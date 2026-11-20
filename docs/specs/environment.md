# Specyfikacja: środowisko (`src/environment/`)

Biblioteka C# / .NET 10 `AlgoTrace.Environment`. Status: kodu jeszcze nie ma; środowisko bazowe (piaskownica, pętla
tool callingu, wstrzykiwanie błędów) powstaje jako projekt zaliczeniowy lidera i trafia do `src/environment/` po jego
oddaniu (po 23.12.2026). Do tego czasu nikt nie pisze kodu w tym folderze, a ta specyfikacja jest celem, do którego
dostosowuje się przejęty kod, i umową, na której pracują inne programy. Środowisko dostaje przebieg od serii
([runner.md](runner.md)), rozmawia z modelem przez `IChatClient` z adapterów ([adapters.md](adapters.md)) i zapisuje
zapis przebiegu czytany przez analizator ([analyzer.md](analyzer.md)). Folder: [src/environment/README.md](../../src/environment/README.md).

## 1. Cel

Wykonać jeden przebieg: jedno zadanie (sortowanie, Hanoi, wyszukiwanie) na jednej instancji z ukrytym stanem, jedną
rozmowę z modelem, w której model działa wyłącznie przez wywołania narzędzi, i zapisać każde zdarzenie (start, tura
modelu, wywołanie, koniec) w JSONL zgodnym z `schemas/run-event.v2.schema.json`. Środowisko pilnuje tekstów, walidacji,
limitów, warunków zatrzymania i błędów wstrzykiwanych dokładnie według protokołu, tak że ten sam ciąg odpowiedzi modelu
daje zawsze ten sam zapis (poza czasami).

## 2. Granice

- Nie zna dostawców: nie buduje żądań HTTP, nie ponawia zapytań, nie zna kluczy ani ustawień rozumowania. To robią
  adaptery ([adapters.md](adapters.md)); środowisko widzi tylko `IChatClient`.
- Nie czyta konfiguracji eksperymentu, nie wybiera instancji, nie liczy `run_id`, nie pilnuje budżetu serii, nie
  ponawia całych przebiegów i nie zapisuje wierszy CSV: to seria ([runner.md](runner.md)). Seria podaje gotowy opis
  przebiegu (sekcja 4) i strażnika kosztu.
- Nie rozpoznaje algorytmu i nie liczy miar poza licznikami `run_end`: to analizator ([analyzer.md](analyzer.md)).
- Nie zmienia tekstów dla modeli: bierze je dosłownie z [prompts.md](../protocol/prompts.md) (pliki tekstów wskazuje
  konfiguracja), podstawia tylko `{N}`, `{last_index}`, `{n}`, `{target}`.
- Nie kończy przebiegu sam po osiągnięciu stanu docelowego ([prompts.md](../protocol/prompts.md) §4).
- Generator instancji: miejsce do ustalenia (sekcja 10); pętla przebiegu dostaje instancję gotową, z pliku.

## 3. Wejścia i wyjścia

| Kierunek | Co | Format | Miejsce |
|---|---|---|---|
| wejście | instancja (jeden wiersz pliku instancji) | `schemas/instance.v2.schema.json` | `instances/<series>.jsonl`, czyta seria |
| wejście | opis przebiegu od serii: pola `run_start` z konfiguracji, limity, harmonogram błędu, teksty | obiekt `RunSpec` (sekcja 4), zbudowany z `schemas/experiment-config.v2.schema.json` | konfiguracja w `experiments/`, teksty w plikach `prompt.system_file`, `task_files`, `reminder_file` |
| wejście | odpowiedzi modelu | `ChatResponse` przez `IChatClient` (umowa w sekcji 4) | adapter |
| wyjście | zapis przebiegu: `run_start`, potem `model_turn` i jej `tool_call`, na końcu `run_end` | `schemas/run-event.v2.schema.json` | `<runs_dir>/<run_id>.jsonl` (`output.runs_dir` z konfiguracji) |
| wyjście | wynik przebiegu dla serii | obiekt `RunOutcome` (`end_reason`, `solved`, koszt, `error`) | pamięć, seria buduje z zapisu wiersz CSV |

Reguły pliku zapisu (kolejność linii, numeracja `turn` i `step`, wywołania pominięte, liczniki, koszt):
[schemas/README.md](../../schemas/README.md), sekcje „Zapis przebiegu” i „Pliki”. Wzorcowe zapisy:
`schemas/examples/run.bubble-sort-n5.jsonl`, `run.edge-cases-n3.jsonl`, `run.api-error-n3.jsonl`.

## 4. Interfejsy

Propozycja (nazwy typów może zmienić przejęty kod; pola i wartości w zapisie nie mogą się zmienić).

```csharp
namespace AlgoTrace.Environment;

public sealed record RunSpec(
    RunStartHeader Header,          // pola run_start, które zna seria: run_id, run_attempt, series, series_id,
                                    // config_sha256, condition, model_key, provider, model_requested, model_version,
                                    // api_version, settings_sent, parallel_tool_calls, strict_tools, repetition,
                                    // price, runner_version, software
    InstanceRecord Instance,        // wiersz instance.v2 (task, n, seed, initial_state, target, answer, ...)
    PromptTemplates Prompt,         // prompt_id, prompt_variant, language, announcement_requested,
                                    // teksty system / task / reminder przed podstawieniem
    string ToolSet,                 // np. "sort-v1"; definicje narzędzi zna środowisko (sekcja 5, krok 1)
    string? CompareResultFormat,    // "words" | "symbols" | null (rodziny bez compare)
    RunLimits Limits,               // max_steps, max_errors, max_reminders, max_output_tokens_per_turn,
                                    // max_cost_per_run, request_timeout_s, run_timeout_s (run_limits z common.v2)
    FaultPlan? Faults,              // fault_type, fault_length, fault_seed, fault_position, message; null w main
    int? ContextBudgetTokens,       // num_ctx - num_predict modelu lokalnego (np. 18432), inaczej null
    string? RetryRunId);            // run_id próby run_attempt + 1, gdy seria ją wykona po api_error; inaczej null

public interface IRunEventSink { void Write(JsonObject runEvent); }   // jedna linia JSONL + flush
public interface ICostGuard { bool StopAfterTurn(decimal runCostSoFar); }  // run-settings.md §7, daje seria
public interface IClock { DateTimeOffset UtcNow { get; } }               // w testach zegar stały

public sealed class RunLoop
{
    public RunLoop(IClock clock);
    public Task<RunOutcome> RunAsync(RunSpec spec, IChatClient model, IRunEventSink sink,
                                     ICostGuard costGuard, CancellationToken ct);
}

public interface ITaskState                 // SortState, HanoiState, SearchState
{
    CallOutcome Apply(string tool, JsonObject? args);   // wykonanie poprawnego wywołania, wynik dla modelu
    string? Validate(string tool, JsonObject? args, out string? detail); // validation_error albo null
    JsonNode? Snapshot();                    // state_after (wyszukiwanie: null)
    bool IsSolved { get; }
}
```

Granica .NET: środowisko nie odwołuje się do `AlgoTrace.Adapters`, a adaptery do środowiska; seria tworzy adapter
(`IChatClient`) i wywołuje `RunLoop` (interpretacja decyzji 0001: sekcja 10).

**Umowa `IChatClient` ze stroną adapterów** (ta sama w [adapters.md](adapters.md); klucze z prefiksem `algotrace.`
w `AdditionalProperties`, bo wspólny model `Microsoft.Extensions.AI` ich nie ma):

| Zapytanie (środowisko → adapter) | Postać |
|---|---|
| prompt systemowy, opis zadania, przypomnienie | `ChatMessage(ChatRole.System, text)`, `ChatMessage(ChatRole.User, text)` |
| poprzednie odpowiedzi modelu | wiadomości z `ChatResponse.Messages` bez zmian (tekst, `TextReasoningContent`, `FunctionCallContent`): dostawcy wymagają odesłania rozumowania, a stały prefiks daje cache |
| wyniki narzędzi tury | jedna `ChatMessage(ChatRole.Tool, ...)` z `FunctionResultContent(callId, result)` w kolejności wywołań; `result` to napis wysłany modelowi |
| flaga błędu wyniku | `FunctionResultContent.AdditionalProperties["algotrace.is_error"] = true` |
| narzędzia | `options.Tools`: deklaracje bez implementacji z postaci neutralnej ([prompts.md](../protocol/prompts.md) §8) |
| ustawienia | `options.ToolMode = ChatToolMode.Auto`, `options.AllowMultipleToolCalls = true`, `options.MaxOutputTokens`, `options.AdditionalProperties["algotrace.strict_tools"]` |

| Pole `model_turn` | Skąd w `ChatResponse` |
|---|---|
| `text`, `reasoning_text` | połączone `TextContent`, `TextReasoningContent` (`null`, gdy brak) |
| `tool_calls[].id`, `name`, `arguments_raw` | `FunctionCallContent.CallId`, `Name`, `AdditionalProperties["algotrace.arguments_raw"]` (napis argumentów taki, jaki przysłał dostawca) |
| `finish_reason`, `finish_reason_raw` | `FinishReason` (wartości enumu `finish_reason` z `common.v2`), `AdditionalProperties["algotrace.finish_reason_raw"]` |
| `model_returned`, `response_id`, `system_fingerprint` | `ModelId`, `ResponseId`, `AdditionalProperties["algotrace.system_fingerprint"]` |
| `usage` | `Usage`: `InputTokenCount`, `CachedInputTokenCount`, `OutputTokenCount`, `ReasoningTokenCount`, `AdditionalCounts["algotrace.cache_write"]`; brak = `null` |
| `latency_ms`, `attempts`, `retries`, `raw_ref` | `AdditionalProperties["algotrace.latency_ms"]`, `["algotrace.attempts"]`, `["algotrace.retries"]` (lista `{status, error_type, wait_ms}`), `["algotrace.raw_ref"]` |

Nieudane zapytanie (po wszystkich próbach): adapter zwraca `ChatResponse` bez treści z
`FinishReason = new ChatFinishReason("error")` i `AdditionalProperties["algotrace.error_kind"]` (`api_error`,
`daily_limit`, `context_exceeded`, `provider_funds`), `["algotrace.error_type"]` (typ błędu dostawcy, np.
`overloaded_error`; przy limicie dziennym `daily_limit`), `["algotrace.error_message"]`. Taka odpowiedź nie daje
zdarzenia `model_turn`. Jedyny wyjątek, który przechodzi przez granicę, to `OperationCanceledException`.

## 5. Zachowanie krok po kroku

1. **Przygotowanie.** Definicje narzędzi rodziny w postaci neutralnej według `ToolSet` i `prompt_variant`
   ([prompts.md](../protocol/prompts.md) §8 i §10: `para_order` zmienia kolejność, `para_names` nazwy,
   `compare_symbols` i `hanoi_state` opisy). Teksty: podstawienie zmiennych, kodowanie UTF-8, LF, bez końcowego
   znaku nowego wiersza (§1). Skróty: `prompt.sha256` i `tools.sha256` (SHA-256 kanonicznego JSON definicji
   neutralnych: klucze posortowane, bez spacji), `tools.names` w kolejności definicji.
2. **`run_start`.** `Header` plus `ts`, `task`, `n`, `instance_id`, `instance_seed`, `initial_state`, `prompt`,
   `tools`, `limits`, `faults` (konfiguracja + harmonogram instancji; `null` w `condition: main`), `env_version`.
3. **Zapytanie.** Wiadomości: system, opis zadania (`input_kind: task`), dalej historia. Odpowiedź z
   `algotrace.error_kind` kończy przebieg (krok 8). W przeciwnym razie `turn += 1` i zdarzenie `model_turn`
   (`cost` z `usage` i `price`: wzór w `common.v2`, `null` liczony jak 0, bez ceny `null`).
4. **Odpowiedź bez wywołania** (`text_turns += 1`): jeśli to druga taka odpowiedź z rzędu albo czwarta w przebiegu,
   koniec `no_tool_call`; inaczej przypomnienie z [prompts.md](../protocol/prompts.md) §7 jako wiadomość użytkownika
   (`reminders += 1`, następna tura ma `input_kind: reminder`). Licznik „z rzędu” zeruje odpowiedź z wywołaniem.
5. **Wywołania tury po kolei** (kolejność z odpowiedzi, `index_in_turn` od 0; dwa i więcej wywołań = `parallel_turns
   += 1`). Dla każdego:
   - przebieg już zakończony przez `step_limit` albo `too_many_errors` w tej turze → zdarzenie pominięte:
     `step: null`, `executed: false`, `is_error: false`, `result: null`, `skipped_reason` = `end_reason`, stan bez zmian;
   - inaczej `step += 1` i walidacja w kolejności `after_done`, `unknown_tool`, `bad_arguments`, `out_of_range`,
     `same_index`, `illegal_move` ([prompts.md](../protocol/prompts.md) §9; `illegal_move` z `validation_detail`);
     błąd: `executed: false`, `is_error: true`, `result` = komunikat z §9 co do znaku, stan bez zmian, licznik błędów
     z rzędu `+1` (poza `after_done`, po którym przebieg i tak jest zakończony);
   - poprawne wywołanie inne niż `done` w warunku `faults`: licznik poprawnych wywołań `+1`; jeśli trafia w
     `fault_position` (albo jest kolejnym wywołaniem tego samego narzędzia w trwającym błędzie `persistent`) →
     `injected_fault: {type, event_index}`, `result` = `faults.message`, `executed: false`, `is_error: true`, stan bez
     zmian, licznik błędów z rzędu bez zmian ([fault-injection.md](../protocol/fault-injection.md) §3-4);
   - inaczej wykonanie: `executed: true`, `is_error: false`, licznik błędów z rzędu = 0, wynik: `compare` → `less` /
     `greater` (albo `<` / `>` przy `compare_symbols`), `swap` i `move` → `ok` (przy `hanoi_state` ze stanem palików,
     §10 protokołu), `read` → liczba dziesiętnie, `done` → `accepted` (tylko w zapisie);
   - zdarzenie `tool_call` z `state_after` (sortowanie `{array}`, Hanoi `{pegs}`, wyszukiwanie `null`);
   - po zdarzeniu, w tej kolejności: `done` wykonane → koniec `done_solved` albo `done_unsolved` (dalsze wywołania
     tury dostają `after_done` i są krokami); licznik błędów z rzędu = `max_errors` → koniec `too_many_errors`;
     `step == max_steps` → koniec `step_limit` (dalsze wywołania tury pominięte).
6. **Po turze bez końca**: strażnik kosztu (`ICostGuard`, koniec `cost_limit`), czas od `run_start` ≥ `run_timeout_s`
   (koniec `time_limit`), model lokalny: `usage.input + usage.output + 512 > ContextBudgetTokens` (koniec
   `context_exceeded`, [run-settings.md](../protocol/run-settings.md) §5). Inaczej do historii idzie odpowiedź modelu
   i jedna wiadomość z wynikami wszystkich wywołań tury (bez wyniku `after_done`), krok 3.
7. **`solved`** liczy się niezależnie od powodu końca: sortowanie `array` rosnąco, Hanoi `pegs == [[], [], [n, ..., 1]]`,
   wyszukiwanie tylko przy `done(index)` z `index == answer` (`-1`, gdy `target_present: false`).
8. **`run_end`**: `end_reason`, `solved`, `done_called`, `final_state`, `steps`, `turns`, `counts`
   (`executed_by_tool` z `done`, `validation_errors`, `by_validation_error`, `injected_faults`, `skipped_calls`,
   `text_turns`, `reminders`, `parallel_turns`), `usage_total` (suma pól tur, `null` gdy żadna tura pola nie podała),
   `cost` (suma `cost` tur), `duration_ms`, `error` (`{type, message}` przy `api_error`, `context_exceeded`,
   `interrupted`, inaczej `null`), `superseded_by` (`RetryRunId` przy `api_error` poza `provider_funds`, inaczej
   `null`). `CancellationToken` → `end_reason: interrupted`, `error.type: interrupted`.

## 6. Błędy i przypadki brzegowe

- **Argumenty:** `arguments_raw`, które nie są obiektem JSON, dają `arguments: null` i `bad_arguments`. Brak klucza,
  klucz nadmiarowy, wartość niecałkowita (`1.5`, `1.0`, `1e2`, `"1"`, `true`, `null`) → `bad_arguments`. Liczba
  całkowita ujemna albo za duża → `out_of_range` z tą wartością w komunikacie; gdy oba indeksy są poza zakresem,
  komunikat podaje pierwszy (`i`, `from_peg`).
- **`same_index`** dotyczy tylko `compare` i `swap`; `move(p, p)` to `illegal_move` z `same_peg`.
- **Wyszukiwanie:** `done(-1)` jest poprawne; `done(-2)` i `done(N)` to `out_of_range` z komunikatem dla odpowiedzi
  (§9 protokołu); `read` nie zmienia stanu, więc `state_after: null`.
- **Kilka wywołań, w tym `done`:** wywołania przed `done` wykonują się, po `done` dostają `after_done` (komunikat tylko
  w zapisie; model nie dostaje już zapytania).
- **Błąd wstrzyknięty:** nigdy na `done` ani na wywołanie odrzucone przez walidację; przebieg zakończony przed
  `fault_position` ma `injected_faults: 0` (protokół: `fault_fired: false`); błąd `persistent` trafia tylko w to samo
  narzędzie, inne działają.
- **Odpowiedź ucięta** (`finish_reason: length`) bez wywołania dostaje przypomnienie; z wywołaniami: wywołania
  przechodzą zwykłą walidację (często `bad_arguments`).
- **Puste `text`** przed pierwszym wywołaniem to pusta deklaracja, nie błąd ([prompts.md](../protocol/prompts.md) §6).
- **Przerwanie procesu** bez `run_end` zostawia plik bez ostatniej linii: to przebieg przerwany, czytnik pomija uciętą
  linię ([schemas/README.md](../../schemas/README.md), „Pliki”); seria uruchamia go od nowa.
- **Sekrety:** środowisko nie zapisuje nagłówków ani kluczy; `settings_sent` przychodzi od serii i schemat odrzuca klucze
  typu `api_key`.

## 7. Wymagania protokołu

- [prompts.md](../protocol/prompts.md) §1: teksty dosłownie, zmienne tylko cztery, limity nieujawniane, wersja i skróty.
- [prompts.md](../protocol/prompts.md) §2: przebieg rozmowy, kilka wywołań w odpowiedzi wykonywanych po kolei.
- [prompts.md](../protocol/prompts.md) §3, §5-7: prompt systemowy, opisy zadań, zapowiedź, przypomnienie.
- [prompts.md](../protocol/prompts.md) §8-10: definicje narzędzi, wyniki i komunikaty błędów, warianty pilotażu.
- [run-settings.md](../protocol/run-settings.md) §3-5: limity kroków (wzory), błędów z rzędu, przypomnień, kontekstu
  i czasu.
- [run-settings.md](../protocol/run-settings.md) §7-8: strażnik kosztu po każdej odpowiedzi, `end_reason` i pierwszeństwo
  warunków w turze.
- [fault-injection.md](../protocol/fault-injection.md) §3-6: harmonogram, działanie błędu, komunikat, zapis.
- [design.md](../protocol/design.md) §3: instancje i ziarna, plik instancji jako źródło prawdy.
- [schemas/README.md](../../schemas/README.md): reguły zapisu przebiegu, pliki, czasy UTC z milisekundami.

## 8. Testy akceptacyjne

Testy w `tests/dotnet/AlgoTrace.Environment.Tests/` (xUnit v3, FsCheck, Verify), bez sieci: model zastępuje fałszywy
`IChatClient`, który zwraca z góry zapisane odpowiedzi; zegar stały. „Zgodny z przykładem” znaczy: te same linie po
usunięciu `ts`, `latency_ms`, `duration_ms`.

- **T1 Sortowanie bąbelkowe z przykładu.** Dane: instancja `sort-n5-example` (`[4, 6, 3, 1, 2]`) z
  `schemas/examples/instances.example.jsonl`, fałszywy klient odtwarzający tury modelu z
  `schemas/examples/run.bubble-sort-n5.jsonl`. Działanie: `RunAsync`. Oczekiwane: zapis zgodny z przykładem;
  `end_reason: done_solved`, `steps: 19`, `turns: 19`, `executed_by_tool` = `{compare: 10, swap: 8, done: 1}`,
  `final_state.array` = `[1, 2, 3, 4, 6]`.
- **T2 Przypadki brzegowe z przykładu.** Dane: instancja `sort-n3-example` (`[3, 1, 2]`), warunek `faults`,
  `one_off`, `fault_position: 3`, `max_steps: 6`, tury z `schemas/examples/run.edge-cases-n3.jsonl`. Oczekiwane: zapis
  zgodny z przykładem; krok 3 `swap(0, 3)` → `out_of_range`, wynik `Error: position 3 is out of range. Valid positions
  are 0 to 2. The call was not executed.`; tura 3 bez wywołania, tura 4 z `input_kind: reminder`; krok 4 `swap(0, 1)`
  → `injected_fault: {type: one_off, event_index: 1}`; krok 6 kończy `step_limit`, a `swap(1, 2)` w tej samej turze
  ma `step: null`, `skipped_reason: step_limit`; `counts` = `{executed_by_tool: {compare: 3, swap: 1},
  validation_errors: 1, injected_faults: 1, skipped_calls: 1, text_turns: 1, reminders: 1, parallel_turns: 2}`.
- **T3 Błąd API.** Dane: tury z `schemas/examples/run.api-error-n3.jsonl`, druga odpowiedź klienta z
  `algotrace.error_kind: api_error`, `error_type: overloaded_error`, `RetryRunId: 6e6327bf7da2953e`. Oczekiwane:
  jedna tura, `steps: 1`, brak `model_turn` dla tury 2, `end_reason: api_error`, `error.type: overloaded_error`,
  `superseded_by: 6e6327bf7da2953e`. Przy `error_kind: provider_funds`: `superseded_by: null`.
- **T4 Kolejność i teksty walidacji (sortowanie, N = 3, `[3, 1, 2]`).** Dane: jedna tura z wywołaniami `foo {}`,
  `compare {"i":0}`, `compare {"i":1.5,"j":0}`, `compare {"i":true,"j":0}`, `compare {"i":0,"j":3}`,
  `compare {"i":1,"j":1}`, `compare` z `arguments_raw` `{i:0`. Oczekiwane: kolejno `unknown_tool` (`Error: unknown tool
  "foo". Available tools: compare, swap, done. The call was not executed.`), `bad_arguments` (`Error: invalid arguments
  for compare. Expected arguments: i (integer), j (integer). The call was not executed.`) trzy razy, `out_of_range`,
  `same_index`, `bad_arguments` z `arguments: null`; `state_after` za każdym razem `[3, 1, 2]`; `by_validation_error`
  = `{unknown_tool: 1, bad_arguments: 4, out_of_range: 1, same_index: 1}`; licznik błędów z rzędu 7 (bez końca).
- **T5 Hanoi n = 3.** Dane: `move(0, 0)`, `move(1, 2)`, `move(0, 2)`, `move(0, 2)`, `move(0, 3)`, potem ruchy optymalne
  od stanu `[[3, 2], [], [1]]`: `(0, 1)`, `(2, 1)`, `(0, 2)`, `(1, 0)`, `(1, 2)`, `(0, 2)` i `done`. Oczekiwane:
  `illegal_move` z `same_peg`, `illegal_move` z `empty_peg` (`Error: illegal move, peg 1 has no disks. The call was
  not executed.`), `ok` i stan `[[3, 2], [], [1]]`, `illegal_move` z `larger_on_smaller`, `out_of_range` (`Error: peg 3
  does not exist. Valid pegs are 0, 1 and 2. The call was not executed.`); na końcu `pegs` `[[], [], [3, 2, 1]]`,
  `end_reason: done_solved`, `steps: 12`, `executed_by_tool` = `{move: 7, done: 1}`, `validation_errors: 4`
  (limit kroków 21 nieosiągnięty).
- **T6 Wariant `hanoi_state`.** Dane: n = 3, `prompt_variant: hanoi_state`, `move(0, 2)`. Oczekiwane: wynik
  `ok. Peg 0: [3, 2]. Peg 1: []. Peg 2: [1].`; w wariancie `main` ten sam ruch daje `ok`.
- **T7 Wyszukiwanie N = 15.** Dane: `array` `[3, 7, 9, 14, 18, 22, 25, 31, 36, 40, 44, 47, 51, 55, 58]`, `target: 31`,
  `answer: 7`. Działanie: trzy przebiegi: (a) `read(7)`, `done(7)`; (b) `done(-1)`; (c) `done(15)`, `done(7)`.
  Oczekiwane: (a) `read` → `31`, `state_after: null`, `done_solved`, `solved: true`; (b) `done_unsolved`,
  `solved: false`; (c) `out_of_range` z wynikiem `Error: 15 is not a valid answer. Give a position from 0 to 14, or -1.
  The call was not executed.`, potem `done_solved`, `steps: 2`.
- **T8 `done` w środku tury.** Dane: sortowanie `[2, 1, 3]`, jedna tura: `swap(0, 1)`, `done()`, `compare(0, 1)`.
  Oczekiwane: `ok`, `accepted`, potem krok 3 `after_done`, `executed: false`, wynik `Error: the task has already
  ended. The call was not executed.`; `end_reason: done_solved`, `steps: 3`, klient wywołany dokładnie raz.
- **T9 Błędy z rzędu.** Dane: sortowanie N = 5 (`max_steps: 30`, `max_errors: 10`), tury: 3 x `compare(0, 0)`,
  3 x `compare(0, 0)`, 3 x `compare(0, 0)`, potem `compare(0, 0)`, `compare(0, 1)`. Oczekiwane: dziesiąty błąd kończy
  przebieg `too_many_errors` w turze 4; `compare(0, 1)` pominięte (`skipped_reason: too_many_errors`), `steps: 10`.
  Wariant: jedno poprawne wywołanie po piątym błędzie zeruje licznik i przebieg trwa.
- **T10 Przypomnienia.** Dane: (a) odpowiedzi: tekst, tekst; (b) tekst, wywołanie, tekst, wywołanie, tekst,
  wywołanie, tekst. Oczekiwane: (a) `no_tool_call` po turze 2, `reminders: 1`, `text_turns: 2`; (b) `no_tool_call`
  po turze 7, `reminders: 3`, `text_turns: 4`; w obu przypomnienie co do znaku z §7 protokołu.
- **T11 Błąd trwały.** Dane: sortowanie N = 10, `persistent`, `fault_length: 3`, `fault_position: 3`, wywołania
  poprawne: `compare`, `compare`, `compare`, `swap`, `compare(0, 0)` (błąd walidacji), `compare`, `compare`, `compare`.
  Oczekiwane: błąd wstrzyknięty na trzecim `compare` (`event_index: 1`), `swap` wykonane, `compare(0, 0)` z
  `same_index` (poza licznikiem harmonogramu), dwa następne `compare` z `event_index` 2 i 3, ostatnie wykonane;
  `injected_faults: 3`, `validation_errors: 1`.
- **T12 Kontekst modelu lokalnego.** Dane: `ContextBudgetTokens: 18432`, tura 5 z `usage.input` 17900 i `output` 30
  i jednym poprawnym wywołaniem. Oczekiwane: wywołanie wykonane i zapisane, potem `end_reason: context_exceeded`
  (17900 + 30 + 512 = 18442 > 18432), `turns: 5`; przy `input` 17880 (18422) przebieg trwa.
- **T13 Strażnik kosztu i czas.** Dane: `ICostGuard` zwraca `true` po turze 2; osobno zegar przesuwany o 3 h po turze 1
  przy `run_timeout_s: 10800`. Oczekiwane: `cost_limit` po turze 2; `time_limit` po turze 1; w obu `solved` liczone ze
  stanu.
- **T14 Powtarzalność i własności.** Dane: ten sam `RunSpec` i te same odpowiedzi dwa razy; FsCheck: losowe ciągi
  wywołań na losowych permutacjach. Oczekiwane: identyczne bajty zapisu po usunięciu czasów; `swap` zachowuje multizbiór
  wartości, `compare` i każdy błąd nie zmieniają stanu; każdy zapis przechodzi `run-event.v2.schema.json`
  (`JsonSchema.Net`) i `python -I schemas/check_examples.py`, gdy zapis dodać do przykładów.

## 9. Wiedza techniczna i źródła

- **Wzór API:** Gymnasium rozdziela „zadanie skończone” (`terminated`) i „ucięte limitem” (`truncated`); środowisko
  ma to samo rozróżnienie w `end_reason` (`done_*` a limity). τ-bench i τ²-bench zwracają błąd narzędzia jako zwykły
  wynik i liczą go jako krok, z limitem błędów (`max_errors = 10`). Kopiujemy konwencje, nie pakiety: żaden framework
  ewaluacji nie daje środowiska z ukrytą tablicą.
- **Losowość nie przenosi się między wersjami:** NumPy `Generator` obiecuje ten sam strumień tylko w tej samej wersji,
  Python `random.shuffle` może się zmienić między wersjami Pythona, a .NET `System.Random` może zmienić algorytm
  między wersjami .NET. Dlatego źródłem prawdy jest plik instancji, a ziarno i nazwa generatora to metadane.
- **`Microsoft.Extensions.AI`:** bez `UseFunctionInvocation` (decyzja 0001) `GetResponseAsync` zwraca
  `FunctionCallContent` i niczego nie wykonuje; pętlę pisze środowisko. `FunctionCallContent.Arguments` to już
  słownik, więc surowy napis argumentów przychodzi osobno (`algotrace.arguments_raw`), a walidacja działa na nim.
- **`System.Text.Json`:** `JsonElement.TryGetInt64` zwraca `false` dla `1.0`, `1e2` i liczb poza `Int64`, co daje
  `bad_arguments` jak w odtworzeniu w `schemas/check_examples.py` (Python odrzuca `float` i `bool`); `true` ma
  `ValueKind` `True`, nie liczbę. Do zapisu ustalić jawnie `JavaScriptEncoder` i kolejność pól (kolejność `properties`
  schematu), żeby snapshoty Verify były stabilne; JSONL: `\n`, UTF-8 bez BOM, `Flush` po każdej linii.
- **Wzór odtworzenia:** `schemas/check_examples.py` (funkcje walidacji wywołań sortowania, harmonogramu błędu
  i liczników `run_end`) to wykonywalny opis zachowania dla sortowania; testy środowiska mogą porównywać się z nim
  na tych samych przykładach.
- **Narzędzia dla agentów:** Anthropic zaleca proste identyfikatory od 0 i komunikaty błędów, które mówią, co
  poprawić; protokół idzie za tym (§9).
- Źródła: https://gymnasium.farama.org/api/env/, https://github.com/sierra-research/tau2-bench,
  https://numpy.org/doc/stable/reference/random/compatibility.html, https://docs.python.org/3/library/random.html,
  https://learn.microsoft.com/en-us/dotnet/api/system.random,
  https://learn.microsoft.com/en-us/dotnet/ai/microsoft-extensions-ai,
  https://www.anthropic.com/engineering/writing-tools-for-agents, prace o podobnych środowiskach: EARL
  (https://arxiv.org/abs/2510.07581, sortowanie przez compare i swap na ukrytych liczbach), Su i in.
  (https://arxiv.org/abs/2510.15974, Hanoi przez narzędzia), AQA-Bench (https://arxiv.org/abs/2402.09404).

## 10. Do ustalenia

- **`max_reminders`.** Przykłady konfiguracji mają `max_reminders: 1`, a protokół kończy przebieg po drugiej
  odpowiedzi bez wywołania z rzędu albo po czwartej w przebiegu (§4 run-settings). Propozycja: `max_reminders` =
  przypomnienia z rzędu (1), a łączny limit 3 to stała protokołu; zgłosić do opisu pola w schemacie.
- **`done` albo dziesiąty błąd na kroku `max_steps`.** Protokół: pierwszy spełniony warunek w kolejności `done`,
  `too_many_errors`, `step_limit`, więc `done` na ostatnim dozwolonym kroku daje `done_*`. `check_examples.py` wymaga
  `step_limit` dokładnie przy `steps == max_steps`, co ten przypadek odrzuca. Propozycja: za protokołem; zgłoszenie
  poprawki skryptu. To samo dla wywołań `after_done`, które mogą dać `steps > max_steps`.
- **Skrót `prompt.sha256`.** Protokół mówi o SHA-256 promptu systemowego i opisu zadania po podstawieniu, a schemat
  ma jedno pole. Propozycja: SHA-256 napisu `system + "\n\n" + task` (UTF-8); zapisać regułę w `schemas/README.md`.
- **Generator instancji.** `src/environment/README.md` wymienia generator, a przykłady mają generator
  `algotrace-instances-pcg64`. Propozycja: osobne polecenie serii korzystające z kodu środowiska, PCG64 z wektorami
  testowymi i opisanym algorytmem permutacji, żeby Python mógł plik sprawdzić; plik raz wygenerowany jest źródłem
  prawdy.
- **Nazwy narzędzi w `para_names`.** Propozycja: zapis trzyma nazwy takie, jakie model wywołał (`check_pair`), a
  `tools.names` i `tool_set` pozwalają analizatorowi zmapować je na nazwy główne; `executed_by_tool` po nazwach
  wywołanych.
- **Ollama a kilka wywołań.** Decyzja 0001 mówi, że adapter Ollamy wykonuje pierwsze wywołanie i oznacza resztę;
  protokół ([prompts.md](../protocol/prompts.md) §2) każe wykonywać wszystkie po kolei. Specyfikacja idzie za protokołem.
- **Kolejność szczegółów `illegal_move`.** Protokół nie rozstrzyga. Propozycja: `same_peg`, potem `empty_peg`, potem
  `larger_on_smaller`.
- **„Tylko `IChatClient`” w decyzji 0001.** Propozycja: dotyczy połączenia środowiska z adapterami; seria może
  wołać publiczne API środowiska (`RunLoop`, `RunSpec`) i fabrykę adapterów, bo sama je składa.
- **`superseded_by`.** Propozycja: seria podaje `RetryRunId`, gdy po `api_error` wykona próbę następną (nie przy
  `provider_funds` ani po ostatniej dozwolonej próbie); środowisko wpisuje go do `run_end`.
- **Czas przebiegu** sprawdzany tylko po turze: jedno zapytanie trwa najwyżej `request_timeout_s` razy liczba prób,
  więc przebieg może przekroczyć `run_timeout_s` o tyle. Propozycja: tak zostawić (bezpiecznik infrastruktury).
