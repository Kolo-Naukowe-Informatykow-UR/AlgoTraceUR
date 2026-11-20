#!/usr/bin/env python3
"""Check the AlgoTrace data contract (major version 2).

- every schema schemas/*.v2.schema.json is a JSON Schema 2020-12 document with its $id;
- every example in schemas/examples/ is valid against its schema, every file in schemas/examples/invalid/ is rejected;
- the example instances are consistent: idx, order, seeds from the base seeds, checks, search answer;
- the example runs are consistent: replay on the instance (validation, compare results, injected fault by the
  schedule of the instance, calls skipped after the end, state after every step), counts of run_end, cost of every
  turn, run_id (with run_attempt) and config_sha256 by the rule, the chain of attempts (superseded_by), results rows
  and analyzer results (labels) derived from the run logs, the bubble-sort run of [4, 6, 3, 1, 2] gives 10
  comparisons and 8 swaps.

Standard library only. When the jsonschema package (4.18 or newer, with referencing) is installed it validates
with Draft202012Validator; otherwise a built-in validator of the keyword subset these schemas use, which stops on
any keyword outside the subset instead of ignoring it.

Usage: python schemas/check_examples.py [--builtin]
Exit code 0 = all checks passed, 1 = a check failed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE / "examples"
INVALID = EXAMPLES / "invalid"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
# file name prefix of an example -> schema name
PREFIXES = {
    "experiment-config": "experiment-config",
    "instances": "instance",
    "run": "run-event",
    "results": "results-row",
    "analyzer-result": "analyzer-result",
}

# ---------------------------------------------------------------- canonical JSON (RFC 8785) and identifiers


def _jcs_number(v: float | int) -> str:
    if isinstance(v, bool):
        raise TypeError("bool is not a number")
    if isinstance(v, int):
        return str(v)
    if not math.isfinite(v):
        raise ValueError("NaN and Infinity are not JSON")
    if v == 0:
        return "0"
    sign = "-" if v < 0 else ""
    mantissa, _, exp = repr(abs(v)).partition("e")
    whole, _, frac = mantissa.partition(".")
    digits = (whole + frac).lstrip("0")
    point = len(whole.lstrip("0")) if whole.strip("0") else -(len(frac) - len(frac.lstrip("0")))
    n = point + (int(exp) if exp else 0)  # value = 0.digits * 10**n
    digits = digits.rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        out = digits + "0" * (n - k)
    elif 0 < n <= 21:
        out = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        out = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        out = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e > 0 else "-") + str(abs(e))
    return sign + out


def canonical_json(value) -> str:
    """RFC 8785 (JCS): sorted keys (UTF-16 code units), no whitespace, ECMAScript number form."""
    if value is None or isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return _jcs_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=lambda s: s.encode("utf-16-be"))
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canonical_json(value[k]) for k in keys) + "}"
    raise TypeError(f"not JSON: {type(value).__name__}")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_sha256(config: dict) -> str:
    return sha256_hex(canonical_json(config))


def make_run_id(series_id: str, config_hash: str, model_key: str, instance_id: str, repetition: int,
                run_attempt: int) -> str:
    key = {
        "series_id": series_id,
        "config_sha256": config_hash,
        "model_key": model_key,
        "instance_id": instance_id,
        "repetition": repetition,
        "run_attempt": run_attempt,
    }
    return sha256_hex(canonical_json(key))[:16]


# ---------------------------------------------------------------- validators

ANNOTATIONS = {"$schema", "$id", "$comment", "$defs", "title", "description", "examples", "default", "deprecated",
               "readOnly", "writeOnly", "format"}
SUPPORTED = ANNOTATIONS | {"$ref", "type", "enum", "const", "minimum", "maximum", "exclusiveMinimum",
                           "exclusiveMaximum", "minLength", "maxLength", "pattern", "items", "minItems", "maxItems",
                           "uniqueItems", "properties", "required", "additionalProperties", "propertyNames",
                           "minProperties", "allOf", "anyOf", "oneOf", "not", "if", "then", "else"}


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _json_eq(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) and _is_number(b):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_eq(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def _is_type(x, t: str) -> bool:
    return {
        "null": x is None,
        "boolean": isinstance(x, bool),
        "integer": _is_number(x) and float(x).is_integer(),
        "number": _is_number(x),
        "string": isinstance(x, str),
        "array": isinstance(x, list),
        "object": isinstance(x, dict),
    }[t]


class SubsetValidator:
    """Validator of the JSON Schema 2020-12 keywords used by the AlgoTrace schemas. Unknown keyword = error."""

    name = "built-in subset validator (jsonschema not installed)"

    def __init__(self, schemas_by_id: dict[str, dict]):
        self.docs = schemas_by_id
        for sid, doc in schemas_by_id.items():
            self._check_keywords(doc, sid)

    def _check_keywords(self, sch, where):
        if isinstance(sch, bool):
            return
        if not isinstance(sch, dict):
            raise ValueError(f"{where}: schema must be an object or a boolean")
        for k, v in sch.items():
            if k not in SUPPORTED:
                raise ValueError(f"{where}: keyword {k!r} is outside the built-in subset; install jsonschema")
            if k in ("properties", "$defs"):
                for name, sub in v.items():
                    self._check_keywords(sub, f"{where}/{k}/{name}")
            elif k in ("allOf", "anyOf", "oneOf"):
                for i, sub in enumerate(v):
                    self._check_keywords(sub, f"{where}/{k}/{i}")
            elif k in ("items", "additionalProperties", "propertyNames", "not", "if", "then", "else"):
                self._check_keywords(v, f"{where}/{k}")

    def _resolve(self, ref: str, base: str):
        uri, _, fragment = ref.partition("#")
        doc_id = urljoin(base, uri) if uri else base
        node = self.docs[doc_id]
        for part in [p for p in fragment.split("/") if p]:
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return node, doc_id

    def errors(self, instance, schema_id: str) -> list[str]:
        out: list[str] = []
        self._v(instance, self.docs[schema_id], schema_id, "", out)
        return out

    def _valid(self, inst, sch, base) -> bool:
        tmp: list[str] = []
        self._v(inst, sch, base, "", tmp)
        return not tmp

    def _v(self, inst, sch, base, path, out):  # noqa: C901 - one keyword per branch
        if sch is True:
            return
        if sch is False:
            out.append(f"{path or '/'}: not allowed")
            return
        at = path or "/"
        if "$ref" in sch:
            target, tbase = self._resolve(sch["$ref"], base)
            self._v(inst, target, tbase, path, out)
        if "type" in sch:
            types = sch["type"] if isinstance(sch["type"], list) else [sch["type"]]
            if not any(_is_type(inst, t) for t in types):
                out.append(f"{at}: {json.dumps(inst)[:60]} is not of type {types}")
        if "enum" in sch and not any(_json_eq(inst, e) for e in sch["enum"]):
            out.append(f"{at}: {json.dumps(inst)[:60]} is not one of {sch['enum']}")
        if "const" in sch and not _json_eq(inst, sch["const"]):
            out.append(f"{at}: {json.dumps(inst)[:60]} is not {json.dumps(sch['const'])}")
        if _is_number(inst):
            if "minimum" in sch and inst < sch["minimum"]:
                out.append(f"{at}: {inst} < minimum {sch['minimum']}")
            if "maximum" in sch and inst > sch["maximum"]:
                out.append(f"{at}: {inst} > maximum {sch['maximum']}")
            if "exclusiveMinimum" in sch and inst <= sch["exclusiveMinimum"]:
                out.append(f"{at}: {inst} <= exclusiveMinimum {sch['exclusiveMinimum']}")
            if "exclusiveMaximum" in sch and inst >= sch["exclusiveMaximum"]:
                out.append(f"{at}: {inst} >= exclusiveMaximum {sch['exclusiveMaximum']}")
        if isinstance(inst, str):
            if "minLength" in sch and len(inst) < sch["minLength"]:
                out.append(f"{at}: shorter than {sch['minLength']}")
            if "maxLength" in sch and len(inst) > sch["maxLength"]:
                out.append(f"{at}: longer than {sch['maxLength']}")
            if "pattern" in sch and not re.search(sch["pattern"], inst):
                out.append(f"{at}: {inst!r} does not match {sch['pattern']}")
        if isinstance(inst, list):
            if "items" in sch:
                for i, x in enumerate(inst):
                    self._v(x, sch["items"], base, f"{path}/{i}", out)
            if "minItems" in sch and len(inst) < sch["minItems"]:
                out.append(f"{at}: fewer than {sch['minItems']} items")
            if "maxItems" in sch and len(inst) > sch["maxItems"]:
                out.append(f"{at}: more than {sch['maxItems']} items")
            if sch.get("uniqueItems") and any(_json_eq(inst[i], inst[j])
                                              for i in range(len(inst)) for j in range(i + 1, len(inst))):
                out.append(f"{at}: items are not unique")
        if isinstance(inst, dict):
            props = sch.get("properties", {})
            for k, sub in props.items():
                if k in inst:
                    self._v(inst[k], sub, base, f"{path}/{k}", out)
            for k in sch.get("required", []):
                if k not in inst:
                    out.append(f"{at}: {k!r} is a required property")
            if "additionalProperties" in sch:
                for k in inst:
                    if k not in props:
                        if sch["additionalProperties"] is False:
                            out.append(f"{at}: additional property {k!r} is not allowed")
                        else:
                            self._v(inst[k], sch["additionalProperties"], base, f"{path}/{k}", out)
            if "propertyNames" in sch:
                for k in inst:
                    self._v(k, sch["propertyNames"], base, f"{path}/<name {k}>", out)
            if "minProperties" in sch and len(inst) < sch["minProperties"]:
                out.append(f"{at}: fewer than {sch['minProperties']} properties")
        for sub in sch.get("allOf", []):
            self._v(inst, sub, base, path, out)
        if "anyOf" in sch and not any(self._valid(inst, s, base) for s in sch["anyOf"]):
            out.append(f"{at}: matches none of anyOf")
        if "oneOf" in sch:
            branch_errors = []
            for s in sch["oneOf"]:
                tmp: list[str] = []
                self._v(inst, s, base, path, tmp)
                branch_errors.append(tmp)
            hits = [i for i, errs in enumerate(branch_errors) if not errs]
            if not hits:  # report the closest branch, e.g. the event type the record claims to be
                closest = min(branch_errors, key=len)
                out.append(f"{at}: matches none of oneOf; closest branch: {'; '.join(closest[:3])}")
            elif len(hits) > 1:
                out.append(f"{at}: must match exactly one of oneOf, matches {hits}")
        if "not" in sch and self._valid(inst, sch["not"], base):
            out.append(f"{at}: must not match the 'not' schema")
        if "if" in sch:
            branch = "then" if self._valid(inst, sch["if"], base) else "else"
            if branch in sch:
                self._v(inst, sch[branch], base, path, out)


class LibraryValidator:
    name = "jsonschema {} (Draft202012Validator, format checks on)"

    def __init__(self, schemas_by_id: dict[str, dict]):
        import jsonschema
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource

        self.name = self.name.format(getattr(jsonschema, "__version__", "?"))
        registry = Registry().with_resources(
            [(sid, Resource.from_contents(doc)) for sid, doc in schemas_by_id.items()])
        self.validators = {}
        for sid, doc in schemas_by_id.items():
            Draft202012Validator.check_schema(doc)
            self.validators[sid] = Draft202012Validator(doc, registry=registry, format_checker=FormatChecker())

    def errors(self, instance, schema_id: str) -> list[str]:
        return ["/" + "/".join(map(str, e.absolute_path)) + ": " + e.message
                for e in self.validators[schema_id].iter_errors(instance)]


# ---------------------------------------------------------------- reading files


def load_schemas() -> tuple[dict[str, dict], dict[str, str]]:
    by_id, id_of_name = {}, {}
    for path in sorted(HERE.glob("*.v2.schema.json")):
        doc = json.loads(read_text(path))
        name = path.name.split(".")[0]
        if doc.get("$schema") != DIALECT:
            raise ValueError(f"{path.name}: $schema must be {DIALECT}")
        if not str(doc.get("$id", "")).endswith("/" + path.name):
            raise ValueError(f"{path.name}: $id must end with /{path.name}")
        by_id[doc["$id"]] = doc
        id_of_name[name] = doc["$id"]
    return by_id, id_of_name


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{path.name}: UTF-8 with BOM")
    if b"\r" in data:
        raise ValueError(f"{path.name}: CR in line endings (LF only)")
    if data and not data.endswith(b"\n"):
        raise ValueError(f"{path.name}: last line without LF")
    return data.decode("utf-8")


def read_records(path: Path) -> list:
    text = read_text(path)
    if path.suffix == ".json":
        return [json.loads(text)]
    if path.suffix == ".jsonl":
        lines = text.split("\n")[:-1]
        if any(not line.strip() for line in lines):
            raise ValueError(f"{path.name}: empty line in JSONL")
        return [json.loads(line) for line in lines]
    if path.suffix == ".csv":
        return read_csv(text)
    raise ValueError(f"{path.name}: unknown extension")


_ROW_SCHEMA: dict = {}


def _column_types(name: str) -> list[str]:
    return _types_of(_ROW_SCHEMA["properties"][name])


def _types_of(sch: dict) -> list[str]:
    """JSON types a column may hold: from type, the $ref into common, the branches of oneOf, or enum values."""
    if "type" in sch:
        return sch["type"] if isinstance(sch["type"], list) else [sch["type"]]
    if "$ref" in sch:
        return _types_of(_COMMON["$defs"][sch["$ref"].split("/")[-1]])
    if "oneOf" in sch:
        return [t for branch in sch["oneOf"] for t in _types_of(branch)]
    return ["null" if v is None else "string" for v in sch.get("enum", ["x"])]


_COMMON: dict = {}


def read_csv(text: str) -> list[dict]:
    rows = list(csv.reader(text.splitlines(), strict=True))
    header, body = rows[0], rows[1:]
    expected = list(_ROW_SCHEMA["properties"])
    if header != expected:
        raise ValueError(f"CSV header differs from results-row properties: {header} != {expected}")
    out = []
    for cells in body:
        if len(cells) != len(header):
            raise ValueError("CSV row with a different number of fields")
        row = {}
        for name, cell in zip(header, cells):
            types = _column_types(name)
            if cell == "":
                row[name] = None
            elif "boolean" in types:
                row[name] = {"true": True, "false": False}.get(cell, cell)
            elif "integer" in types and re.fullmatch(r"-?[0-9]+", cell):
                row[name] = int(cell)
            elif "number" in types:
                row[name] = float(cell)
            else:
                row[name] = cell
        out.append(row)
    return out


def schema_for(path: Path) -> str:
    prefix = path.name.split(".")[0]
    if prefix not in PREFIXES:
        raise ValueError(f"{path.name}: unknown prefix (expected one of {sorted(PREFIXES)})")
    return PREFIXES[prefix]


# ---------------------------------------------------------------- domain: sorting replay, references, measures

WORDS = {"less": "less", "greater": "greater", "equal": "equal"}
SYMBOLS = {"less": "<", "greater": ">", "equal": "="}


def compare_word(a: list[int], i: int, j: int, fmt: str | None) -> str:
    key = "less" if a[i] < a[j] else "greater" if a[i] > a[j] else "equal"
    return (SYMBOLS if fmt == "symbols" else WORDS)[key]


def bubble_sort_tokens(array: list[int]) -> list[tuple]:
    a, tokens = list(array), []
    for p in range(len(a) - 1):
        for j in range(len(a) - 1 - p):
            tokens.append(("compare", j, j + 1))
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                tokens.append(("swap", j, j + 1))
    return tokens


def insertion_sort_tokens(array: list[int]) -> list[tuple]:
    a, tokens = list(array), []
    for i in range(1, len(a)):
        j = i
        while j > 0:
            tokens.append(("compare", j - 1, j))
            if a[j - 1] <= a[j]:
                break
            a[j - 1], a[j] = a[j], a[j - 1]
            tokens.append(("swap", j - 1, j))
            j -= 1
    return tokens


def selection_sort_tokens(array: list[int]) -> list[tuple]:
    a, tokens = list(array), []
    for i in range(len(a) - 1):
        m = i
        for j in range(i + 1, len(a)):
            tokens.append(("compare", j, m))
            if a[j] < a[m]:
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
            tokens.append(("swap", i, m))
    return tokens


REFERENCES = {
    ("bubble_sort", "standard"): bubble_sort_tokens,
    ("insertion_sort", "standard"): insertion_sort_tokens,
    ("selection_sort", "standard"): selection_sort_tokens,
}


def edit_distance(a: list, b: list) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def inversions(a: list[int]) -> int:
    return sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j])


def min_swaps(a: list[int]) -> int:
    target = {v: k for k, v in enumerate(sorted(a))}
    seen, cycles = set(), 0
    for i in range(len(a)):
        if i not in seen:
            cycles += 1
            while i not in seen:
                seen.add(i)
                i = target[a[i]]
    return len(a) - cycles


def redundant_compares(array: list[int], tokens: list[tuple]) -> int:
    """Comparisons whose result already followed by transitivity (relations kept on element identities)."""
    ident = list(range(len(array)))  # position -> element id
    above = [set() for _ in array]  # above[x] = ids known to be greater than x
    a = list(array)
    count = 0
    for op, i, j in tokens:
        if op == "swap":
            ident[i], ident[j] = ident[j], ident[i]
            a[i], a[j] = a[j], a[i]
            continue
        x, y = ident[i], ident[j]
        if y in above[x] or x in above[y]:
            count += 1
            continue
        lo, hi = (x, y) if a[i] < a[j] else (y, x)
        lower = {lo} | {v for v in range(len(a)) if lo in above[v]}
        higher = {hi} | above[hi]
        for v in lower:
            above[v] |= higher
    return count


# ---------------------------------------------------------------- run log checks


def ms(ts: str) -> int:
    return round(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000)


def op_tokens(events: list[dict]) -> list[tuple]:
    return [(e["tool"], e["arguments"]["i"], e["arguments"]["j"]) for e in events
            if e["event"] == "tool_call" and e["executed"] and e["tool"] in ("compare", "swap")]


def sum_usage(turns: list[dict]) -> dict:
    total = {}
    for k in ("input", "cached_input", "cache_write", "output", "reasoning"):
        vals = [t["usage"][k] for t in turns if t["usage"][k] is not None]
        total[k] = sum(vals) if vals else None
    return total


def cost_of(usage: dict, price: dict | None) -> float | None:
    """Nominal cost by the formula of price in common (a null count as 0); None without a price."""
    if price is None:
        return None
    u = {k: v or 0 for k, v in usage.items()}
    return ((u["input"] - u["cached_input"]) * price["input_per_mtok"]
            + u["cached_input"] * price["cached_input_per_mtok"]
            + u["cache_write"] * price["cache_write_per_mtok"]
            + u["output"] * price["output_per_mtok"]) / 1e6


def check_cost(name: str, what: str, cost: dict | None, amount: float | None, price: dict | None, fail) -> None:
    if amount is None:
        if cost is not None:
            fail(f"{name}: {what} has a cost without a price")
    elif cost is None or abs(cost["amount"] - amount) > 1e-9 or cost["currency"] != price["currency"]:
        fail(f"{name}: {what} cost should be {amount} {price['currency']}")


SORT_ARGS = {"compare": ("i", "j"), "swap": ("i", "j"), "done": ()}


def expected_validation(call: dict, n: int, names: list[str], done: bool) -> str | None:
    """Validation of a sorting call in the order of protocol prompts.md, section 9 (illegal_move is Hanoi only)."""
    if done:
        return "after_done"
    if call["tool"] not in names:
        return "unknown_tool"
    args = call["arguments"]
    want = SORT_ARGS.get(call["tool"], ())
    if args is None or set(args) != set(want) or any(type(args[k]) is not int for k in want):
        return "bad_arguments"
    if any(not 0 <= args[k] < n for k in want):
        return "out_of_range"
    if want and args["i"] == args["j"]:
        return "same_index"
    return None


def check_run(name: str, events: list[dict], configs: dict, instances: dict, fail) -> None:  # noqa: C901
    start, end = events[0], events[-1]
    if start["event"] != "run_start" or end["event"] != "run_end":
        return fail(f"{name}: first line must be run_start and last run_end")
    if sum(e["event"] in ("run_start", "run_end") for e in events) != 2:
        fail(f"{name}: exactly one run_start and one run_end")
    if any(e["run_id"] != start["run_id"] for e in events):
        fail(f"{name}: run_id differs between lines")
    times = [ms(e["ts"]) for e in events]
    if times != sorted(times):
        fail(f"{name}: ts is not in order")

    cfg = configs.get(start["series_id"])
    if cfg is None:
        return fail(f"{name}: no example configuration for series {start['series_id']}")
    if start["config_sha256"] != config_sha256(cfg):
        fail(f"{name}: config_sha256 is not the canonical hash of the configuration")
    cell = (start["series_id"], start["config_sha256"], start["model_key"], start["instance_id"], start["repetition"])
    rid = make_run_id(*cell, start["run_attempt"])
    if start["run_id"] != rid:
        fail(f"{name}: run_id {start['run_id']} is not {rid} by the rule")
    model = next((m for m in cfg["models"] if m["model_key"] == start["model_key"]), None)
    task = next((t for t in cfg["tasks"] if t["task"] == start["task"]), None)
    size = task and next((s for s in task["sizes"] if s["n"] == start["n"]), None)
    inst = instances.get(start["instance_id"])
    if model is None or task is None or size is None or inst is None:
        return fail(f"{name}: model, task, size or instance is not in the configuration and the instance file")
    faults = None
    if cfg["faults"] is not None:
        sched = inst["fault_schedule"]
        if sched is None:
            return fail(f"{name}: condition faults on an instance without fault_schedule")
        faults = {**cfg["faults"], **sched}
    expected = {
        "series": cfg["series"], "condition": cfg["condition"], "provider": model["provider"],
        "model_requested": model["model"], "model_version": model["model_version"],
        "api_version": model["api"]["api_version"], "parallel_tool_calls": model["settings"]["parallel_tool_calls"],
        "strict_tools": model["settings"]["strict_tools"], "faults": faults, "price": model["price"],
        "limits": {"max_steps": size["max_steps"], **cfg["limits"], **model["timeouts"]},
    }
    for k, v in expected.items():
        if not _json_eq(start[k], v):
            fail(f"{name}: run_start.{k} differs from the configuration and the instance")
    if start["repetition"] > cfg["repetitions"]:
        fail(f"{name}: repetition above repetitions")
    p = start["prompt"]
    if (p["prompt_id"], p["prompt_variant"], p["language"], p["announcement_requested"]) != (
            cfg["prompt"]["prompt_id"], cfg["prompt"]["prompt_variant"], cfg["prompt"]["language"],
            cfg["prompt"]["announcement_requested"]):
        fail(f"{name}: prompt differs from the configuration")
    if (start["tools"]["tool_set"], start["tools"]["compare_result_format"]) != (
            task["tool_set"], task["compare_result_format"]):
        fail(f"{name}: tools differ from the configuration")
    if not _json_eq(inst["initial_state"], start["initial_state"]) or inst["n"] != start["n"] \
            or inst["seed"] != start["instance_seed"] or inst["task"] != start["task"] \
            or inst["series"] != cfg["series"]:
        fail(f"{name}: initial_state, n, seed, task or series differs from the instance file")
    sup = end["superseded_by"]
    if sup is not None and sup != make_run_id(*cell, start["run_attempt"] + 1):
        fail(f"{name}: superseded_by is not the run_id of attempt {start['run_attempt'] + 1}")

    # turns, steps and skipped calls
    turns = [e for e in events if e["event"] == "model_turn"]
    calls = [e for e in events if e["event"] == "tool_call"]
    steps = [c for c in calls if c["step"] is not None]
    skipped = [c for c in calls if c["step"] is None]
    if [t["turn"] for t in turns] != list(range(1, len(turns) + 1)):
        fail(f"{name}: turns are not numbered 1..T")
    if [c["step"] for c in steps] != list(range(1, len(steps) + 1)):
        fail(f"{name}: steps are not numbered 1..S")
    if skipped and (calls[-len(skipped):] != skipped or any(c["turn"] != turns[-1]["turn"] for c in skipped)
                    or any(c["skipped_reason"] != end["end_reason"] for c in skipped)):
        fail(f"{name}: skipped calls must close the last turn with skipped_reason = end_reason")
    by_turn = {t["turn"]: t for t in turns}
    seen_turn = 0
    for e in events[1:-1]:
        if e["event"] == "model_turn":
            seen_turn = e["turn"]
        elif e["turn"] != seen_turn:
            fail(f"{name}: call {e['call_id']} is not right after its model_turn")
    for c in calls:
        listed = by_turn[c["turn"]]["tool_calls"]
        entry = listed[c["index_in_turn"]] if c["index_in_turn"] < len(listed) else None
        if entry is None or (entry["id"], entry["name"], entry["index_in_turn"]) != (
                c["call_id"], c["tool"], c["index_in_turn"]):
            fail(f"{name}: call {c['call_id']} does not match the call listed in its turn")
        elif c["arguments"] is not None and json.loads(entry["arguments_raw"]) != c["arguments"]:
            fail(f"{name}: call {c['call_id']} arguments differ from arguments_raw")
    for t in turns:
        if len(t["tool_calls"]) != sum(c["turn"] == t["turn"] for c in calls):
            fail(f"{name}: turn {t['turn']} lists calls without tool_call events")
    for prev, t in zip([None] + turns, turns):
        want = "task" if prev is None else "reminder" if not prev["tool_calls"] else "tool_results"
        if t["input_kind"] != want:
            fail(f"{name}: turn {t['turn']} input_kind should be {want}")

    # replay on the hidden state (sorting): validation, injected fault by the schedule, results, state
    state = list(start["initial_state"]["array"])
    fmt = start["tools"]["compare_result_format"]
    names = start["tools"]["names"]
    done = False
    valid_calls, fault_tool, fault_left, fault_index = 0, None, 0, 0
    for c in calls:
        label = f"call {c['call_id']}"
        if c["step"] is None:
            if c["state_after"] != {"array": state}:
                fail(f"{name}: {label} skipped but state_after differs from the replay")
            continue
        verror = expected_validation(c, len(state), names, done)
        if c["validation_error"] != verror:
            fail(f"{name}: {label} validation_error {c['validation_error']!r}, replay gives {verror!r}")
        fault = None
        if verror is None and faults is not None and c["tool"] != "done":
            valid_calls += 1
            if fault_tool is None and valid_calls == faults["fault_position"]:
                fault_tool, fault_left, fault_index = c["tool"], faults["fault_length"] - 1, 1
                fault = {"type": faults["fault_type"], "event_index": 1}
            elif fault_left > 0 and c["tool"] == fault_tool:
                fault_left, fault_index = fault_left - 1, fault_index + 1
                fault = {"type": faults["fault_type"], "event_index": fault_index}
        if c["injected_fault"] != fault:
            fail(f"{name}: {label} injected_fault {c['injected_fault']}, schedule gives {fault}")
        elif fault is not None and c["result"] != faults["message"]:
            fail(f"{name}: {label} result of an injected fault differs from the message")
        if c["executed"] != (verror is None and fault is None):
            fail(f"{name}: {label} executed differs from the replay")
        if c["executed"]:
            if c["tool"] == "compare":
                want = compare_word(state, c["arguments"]["i"], c["arguments"]["j"], fmt)
            elif c["tool"] == "swap":
                i, j = c["arguments"]["i"], c["arguments"]["j"]
                state[i], state[j] = state[j], state[i]
                want = "ok"
            else:
                want, done = "accepted", True
            if c["result"] != want:
                fail(f"{name}: {label} result {c['result']!r}, replay gives {want!r}")
        if c["state_after"] != {"array": state}:
            fail(f"{name}: {label} state_after differs from the replay")

    solved = state == sorted(state)
    if end["final_state"] != {"array": state}:
        fail(f"{name}: final_state differs from the replay")
    if end["solved"] != solved or end["done_called"] != done:
        fail(f"{name}: solved or done_called differs from the replay")
    if done and end["end_reason"] != ("done_solved" if solved else "done_unsolved"):
        fail(f"{name}: end_reason should be done_solved or done_unsolved")
    if (end["end_reason"] == "step_limit") != (len(steps) == start["limits"]["max_steps"]):
        fail(f"{name}: step_limit exactly at max_steps steps")

    # counts, usage, cost, duration
    by_tool: dict[str, int] = {}
    by_error: dict[str, int] = {}
    for c in steps:
        if c["executed"]:
            by_tool[c["tool"]] = by_tool.get(c["tool"], 0) + 1
        if c["validation_error"]:
            by_error[c["validation_error"]] = by_error.get(c["validation_error"], 0) + 1
    counts = {
        "executed_by_tool": by_tool,
        "validation_errors": sum(by_error.values()),
        "by_validation_error": by_error,
        "injected_faults": sum(c["injected_fault"] is not None for c in steps),
        "skipped_calls": len(skipped),
        "text_turns": sum(not t["tool_calls"] for t in turns),
        "reminders": sum(t["input_kind"] == "reminder" for t in turns),
        "parallel_turns": sum(len(t["tool_calls"]) > 1 for t in turns),
    }
    if not _json_eq(end["counts"], counts):
        fail(f"{name}: run_end.counts {end['counts']} != derived {counts}")
    if (end["steps"], end["turns"]) != (len(steps), len(turns)):
        fail(f"{name}: run_end steps or turns differ from the log")
    usage = sum_usage(turns)
    if end["usage_total"] != usage:
        fail(f"{name}: usage_total differs from the sum of turns")
    price = start["price"]
    total = None if price is None else 0.0
    for t in turns:
        amount = cost_of(t["usage"], price)
        check_cost(name, f"turn {t['turn']}", t["cost"], amount, price, fail)
        if amount is not None:
            total += amount
    check_cost(name, "run_end", end["cost"], total, price, fail)
    if end["duration_ms"] != ms(end["ts"]) - ms(start["ts"]):
        fail(f"{name}: duration_ms differs from the timestamps")


def derive_row(events: list[dict]) -> dict:
    start, end = events[0], events[-1]
    turns = [e for e in events if e["event"] == "model_turn"]
    tools = end["counts"]["executed_by_tool"]
    u = end["usage_total"]
    faults = start["faults"]
    return {
        "schema_version": start["schema_version"], "series_id": start["series_id"], "series": start["series"],
        "run_id": start["run_id"], "condition": start["condition"],
        "fault_type": faults["fault_type"] if faults else None, "model_key": start["model_key"],
        "provider": start["provider"], "model_requested": start["model_requested"],
        "model_version": start["model_version"],
        "model_returned": turns[-1]["model_returned"] if turns else None, "task": start["task"], "n": start["n"],
        "instance_id": start["instance_id"], "repetition": start["repetition"], "run_attempt": start["run_attempt"],
        "prompt_id": start["prompt"]["prompt_id"], "prompt_variant": start["prompt"]["prompt_variant"],
        "announcement_requested": start["prompt"]["announcement_requested"],
        "tool_set": start["tools"]["tool_set"], "parallel_tool_calls": start["parallel_tool_calls"],
        "strict_tools": start["strict_tools"],
        "solved": end["solved"], "done_called": end["done_called"], "end_reason": end["end_reason"],
        "superseded_by": end["superseded_by"],
        "steps": end["steps"], "turns": end["turns"], "executed_calls": sum(tools.values()),
        "compare_calls": tools.get("compare", 0), "swap_calls": tools.get("swap", 0),
        "move_calls": tools.get("move", 0), "read_calls": tools.get("read", 0), "done_calls": tools.get("done", 0),
        "validation_errors": end["counts"]["validation_errors"], "injected_faults": end["counts"]["injected_faults"],
        "fault_fired": end["counts"]["injected_faults"] > 0 if faults else None,
        "skipped_calls": end["counts"]["skipped_calls"],
        "text_turns": end["counts"]["text_turns"], "reminders": end["counts"]["reminders"],
        "parallel_turns": end["counts"]["parallel_turns"], "input_tokens": u["input"],
        "cached_input_tokens": u["cached_input"], "cache_write_tokens": u["cache_write"],
        "output_tokens": u["output"], "reasoning_tokens": u["reasoning"],
        "cost": end["cost"]["amount"] if end["cost"] else None,
        "currency": end["cost"]["currency"] if end["cost"] else None, "duration_ms": end["duration_ms"],
        "started_at": start["ts"], "ended_at": end["ts"], "env_version": start["env_version"],
        "config_sha256": start["config_sha256"],
    }


def derive_analysis(events: list[dict]) -> dict:
    """The parts of an analyzer result that follow from the log alone (sorting, full tokens)."""
    start = events[0]
    array = start["initial_state"]["array"]
    tokens = op_tokens(events)
    distances = []
    for (ref, variant), fn in REFERENCES.items():
        r = fn(array)
        d = edit_distance(tokens, r)
        distances.append({"reference": ref, "variant": variant, "distance": d,
                          "normalized_distance": round(d / max(len(tokens), len(r), 1), 4),
                          "reference_length": len(r)})
    distances.sort(key=lambda x: (x["normalized_distance"], x["reference"]))
    turns = [e for e in events if e["event"] == "model_turn"]
    return {
        "trace_length": len(tokens),
        "metrics": {
            "compares": sum(t[0] == "compare" for t in tokens), "swaps": sum(t[0] == "swap" for t in tokens),
            "redundant_compares": redundant_compares(array, tokens),
            "info_bound_compares": math.ceil(math.log2(math.factorial(len(array)))),
            "inversions": inversions(array), "min_swaps": min_swaps(array),
        },
        "distances": distances,
        "first_text": turns[0]["text"] if turns else None,
    }


FAILED_SUBTYPE = {"done_unsolved": "wrong_done", "step_limit": "step_limit", "too_many_errors": "errors",
                  "no_tool_call": "no_tool_call", "context_exceeded": "context", "api_error": "infra",
                  "time_limit": "infra", "cost_limit": "infra", "interrupted": "infra"}


def label_text(label: dict) -> str:
    """The label as the protocol writes it (classification-rules.md, section 1)."""
    kind, algs = label["kind"], label["algorithms"]
    if kind == "known":
        return "known:" + algs[0]
    if kind == "hybrid":
        return "hybrid:" + "+".join(algs)
    if kind == "ambiguous":
        return "ambiguous:" + "|".join(algs)
    if kind in ("new", "failed"):
        return kind + ":" + label["subtype"] + (":" + label["failure_detail"] if label["failure_detail"] else "")
    return kind


# ---------------------------------------------------------------- instances


TASK_ORDER = {"sort": 0, "hanoi": 1, "search": 2}


def instance_checks(inst: dict) -> tuple[list[str], list[str]]:
    """Checks of protocol design.md, section 3: (checked, failed)."""
    st, n = inst["initial_state"], inst["n"]
    if inst["task"] == "sort":
        res = {"permutation": sorted(st["array"]) == list(range(1, n + 1)),
               "not_sorted": st["array"] != sorted(st["array"])}
    elif inst["task"] == "hanoi":
        res = {"hanoi_start": st["pegs"] == [list(range(n, 0, -1)), [], []]}
    else:
        a = st["array"]
        answer = a.index(st["target"]) if st["target"] in a else -1
        res = {"strictly_increasing": all(x < y for x, y in zip(a, a[1:])),
               "target_present": inst["target_present"] == (st["target"] in a),
               "answer": inst["answer"] == answer}
    return list(res), [k for k, ok in res.items() if not ok]


def check_instance_file(name: str, recs: list[dict], fail) -> None:
    keys = [(TASK_ORDER[r["task"]], r["n"], r["rep"]) for r in recs]
    if keys != sorted(keys):
        fail(f"{name}: lines are not in the order task, n, rep")
    if len({r["series"] for r in recs}) > 1:
        fail(f"{name}: one file holds instances of one series")
    gens = {json.dumps(r["generator"], sort_keys=True) for r in recs if r["generator"] is not None}
    if len(gens) > 1:
        fail(f"{name}: generated lines with different generators or base seeds")
    for idx, inst in enumerate(recs):
        iid = inst["instance_id"]
        st = inst["initial_state"]
        size = len(st["array"]) if "array" in st else sum(len(p) for p in st["pegs"])
        if size != inst["n"]:
            fail(f"instance {iid}: n differs from the state")
        if inst["idx"] != idx:
            fail(f"instance {iid}: idx {inst['idx']} is not its line number {idx}")
        gen, sched = inst["generator"], inst["fault_schedule"]
        if gen is not None:
            if inst["seed"] != gen["base_seed"] + idx:
                fail(f"instance {iid}: seed is not base_seed + idx")
            checked, failed = instance_checks(inst)
            if (inst["checks"]["checked"], inst["checks"]["failed"]) != (checked, failed):
                fail(f"instance {iid}: checks should be checked {checked}, failed {failed}")
            if sched is not None and (gen["base_fault_seed"] is None
                                      or sched["fault_seed"] != gen["base_fault_seed"] + idx):
                fail(f"instance {iid}: fault_seed is not base_fault_seed + idx")
        elif sched is not None:
            fail(f"instance {iid}: a fault schedule needs a generated instance")
        if inst["task"] == "search" and instance_checks(inst)[1]:
            fail(f"instance {iid}: target_present or answer differs from the array")


# ---------------------------------------------------------------- main


def main(argv: list[str]) -> int:  # noqa: C901
    problems: list[str] = []
    fail = problems.append
    by_id, id_of = load_schemas()
    _ROW_SCHEMA.update(by_id[id_of["results-row"]])
    _COMMON.update(by_id[id_of["common"]])
    validator = None
    if "--builtin" not in argv:
        try:
            validator = LibraryValidator(by_id)
        except ImportError:
            validator = None
    validator = validator or SubsetValidator(by_id)
    print(f"validator: {validator.name}")
    print(f"schemas: {', '.join(sorted(id_of))}")

    records: dict[str, list] = {}
    for path in sorted(p for p in EXAMPLES.iterdir() if p.is_file()):
        recs = read_records(path)
        records[path.name] = recs
        sid = id_of[schema_for(path)]
        for i, rec in enumerate(recs, 1):
            for err in validator.errors(rec, sid):
                fail(f"{path.name} record {i}: {err}")
        print(f"example  {path.name}: {len(recs)} record(s) checked against {schema_for(path)}")
    for path in sorted(p for p in INVALID.iterdir() if p.is_file()):
        recs = read_records(path)
        sid = id_of[schema_for(path)]
        errs = [e for rec in recs for e in validator.errors(rec, sid)]
        if not errs:
            fail(f"invalid/{path.name}: accepted, but must be rejected")
        print(f"invalid  {path.name}: " + (f"rejected ({errs[0][:110]})" if errs else "ACCEPTED"))
    if problems:  # the consistency checks below assume records that follow their schemas
        return report(problems)

    configs = {r["series_id"]: r for n, recs in records.items() if n.startswith("experiment-config.") for r in recs}
    instances = {r["instance_id"]: r for n, recs in records.items() if n.startswith("instances.") for r in recs}
    if len(instances) != sum(len(v) for n, v in records.items() if n.startswith("instances.")):
        fail("instance_id is not unique")
    for n, recs in records.items():
        if n.startswith("instances."):
            check_instance_file(n, recs, fail)
    runs = {}
    for n, recs in records.items():
        if n.startswith("run."):
            check_run(n, recs, configs, instances, fail)
            runs[recs[0]["run_id"]] = recs

    for rid, evs in runs.items():  # chain of attempts
        sup = evs[-1]["superseded_by"]
        nxt = runs.get(sup) if sup else None
        if nxt is not None:
            a, b = evs[0], nxt[0]
            if [a[k] for k in ("series_id", "model_key", "instance_id", "repetition")] != [
                    b[k] for k in ("series_id", "model_key", "instance_id", "repetition")] \
                    or b["run_attempt"] != a["run_attempt"] + 1 or ms(b["ts"]) < ms(evs[-1]["ts"]):
                fail(f"run {rid}: superseded_by does not lead to the next attempt of the same run")
        print(f"run {rid}: attempt {evs[0]['run_attempt']}, end {evs[-1]['end_reason']}, superseded_by {sup}")

    bubble = [evs for evs in runs.values() if evs[0]["initial_state"].get("array") == [4, 6, 3, 1, 2]]
    if not bubble:
        fail("no example run on [4, 6, 3, 1, 2]")
    for evs in bubble:
        tokens = op_tokens(evs)
        c, s = sum(t[0] == "compare" for t in tokens), sum(t[0] == "swap" for t in tokens)
        final = evs[-1]["final_state"]["array"]
        print(f"bubble sort [4, 6, 3, 1, 2]: {c} comparisons, {s} swaps, final {final}, "
              f"same as reference: {tokens == bubble_sort_tokens([4, 6, 3, 1, 2])}")
        if (c, s, final) != (10, 8, [1, 2, 3, 4, 6]) or tokens != bubble_sort_tokens([4, 6, 3, 1, 2]):
            fail("bubble-sort example: expected the reference trace with 10 comparisons and 8 swaps")

    for n, recs in records.items():
        if n.startswith("results."):
            if {row["run_id"] for row in recs} != set(runs):
                fail(f"{n}: one row per example run")
            for row in recs:
                evs = runs.get(row["run_id"])
                if evs is None:
                    continue
                want = derive_row(evs)
                diff = [k for k in want if not (_json_eq(row[k], want[k]) or (
                    _is_number(row[k]) and _is_number(want[k]) and abs(row[k] - want[k]) < 1e-9))]
                if diff:
                    fail(f"{n}: row {row['run_id']} differs from its run log in {diff}")
        if n.startswith("analyzer-result."):
            for res in recs:
                evs = runs.get(res["run_id"])
                if evs is None:
                    fail(f"{n}: result for unknown run {res['run_id']}")
                    continue
                want = derive_analysis(evs)
                for k in ("series_id", "task", "n", "instance_id"):
                    if res[k] != evs[0][k]:
                        fail(f"{n}: {k} differs from the run")
                if res["trace_length"] != want["trace_length"]:
                    fail(f"{n}: trace_length differs from the run log")
                for k, v in want["metrics"].items():
                    if res["metrics"].get(k) != v:
                        fail(f"{n}: metrics.{k} = {res['metrics'].get(k)}, derived {v}")
                if res["token_variant"] == "full" and res["distances"] != want["distances"]:
                    fail(f"{n}: distances differ from the references replayed on the instance")
                d, label, end = res["distances"], res["label"], evs[-1]
                for lab in (label, res["exploratory_label"]):
                    if lab is not None and lab["text"] != label_text(lab):
                        fail(f"{n}: label text {lab['text']!r} should be {label_text(lab)!r}")
                strategy = end["solved"] and (evs[0]["task"] != "search" or end["end_reason"] == "done_solved")
                if strategy == (label["kind"] == "failed"):
                    fail(f"{n}: a run that reached the goal gets a strategy, another one failed:<type>")
                if label["kind"] == "failed" and label["subtype"] != FAILED_SUBTYPE.get(end["end_reason"]):
                    fail(f"{n}: failed subtype should follow end_reason {end['end_reason']}")
                if label["kind"] == "known" and label["algorithms"] != [d[0]["reference"]]:
                    fail(f"{n}: a known label must name the closest reference")
                margin = round(d[1]["normalized_distance"] - d[0]["normalized_distance"], 4) if len(d) > 1 else None
                if label["margin"] != margin:
                    fail(f"{n}: margin should be {margin}")
                if res["declaration"]["text"] != want["first_text"]:
                    fail(f"{n}: declaration text differs from the first model_turn")
    return report(problems)


def report(problems: list[str]) -> int:
    if problems:
        print(f"\nFAILED: {len(problems)} problem(s)")
        for p in problems:
            print(f"- {p}")
        return 1
    print("\nOK: all examples valid, invalid examples rejected, instances and runs consistent")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, KeyError, json.JSONDecodeError, csv.Error) as exc:
        print(f"\nFAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
