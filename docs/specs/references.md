# Specyfikacja: algorytmy wzorcowe i generator przebiegów syntetycznych (`src/references/`)

Program w Pythonie 3.13, pakiet `algotrace_references` (uv), tylko biblioteka standardowa i `jsonschema`. Status: kod jeszcze nie istnieje. Łączy się z analizatorem ([analyzer.md](analyzer.md)): przez pliki w `data/synthetic/`
i przez import jako biblioteki. Skrót: [src/references/README.md](../../src/references/README.md).

## 1. Cel

1. **Algorytmy wzorcowe**: sortowanie (6 algorytmów z wariantami), Hanoi, wyszukiwanie (5 wzorców); działają na ukrytym stanie tylko
   przez `compare`, `swap`, `move`, `read`, `done` i zapisują każdy krok ([classification-rules.md](../protocol/classification-rules.md) §3, §7, §8).
2. **Generator przebiegów syntetycznych** (czystych, z zakłóceniami, hybryd) w `data/synthetic/`: na nich analizator kalibruje progi (§6
   protokołu) i jest walidowany (§11), więc każdy przebieg ma zapisaną prawdziwą etykietę.

## 2. Granice

- Nie liczy cech, odległości, progów ani etykiet analizy ([analyzer.md](analyzer.md)); nie woła modeli; nie uruchamia serii
  (`src/runner/`) ani środowiska (`src/environment/`).
- Nie dzieli instancji na część kalibracyjną i testową (robi to analizator po `instance_id`) i nie generuje pliku instancji serii
  `pilot` ani `full` (środowisko); własne instancje syntetyczne: tylko `make-instances` (§10 pkt 2).

## 3. Wejścia i wyjścia

| Plik | Schemat | Miejsce | Rola |
|---|---|---|---|
| instancja albo jawna tablica | [instance.v2.schema.json](../../schemas/instance.v2.schema.json) | `instances/<series>.jsonl`, przykład [instances.example.jsonl](../../schemas/examples/instances.example.jsonl) | wejście |
| `set.json` | brak (§5.6) | `data/synthetic/<set_id>/` | wejście generatora |
| zapis przebiegu | [run-event.v2.schema.json](../../schemas/run-event.v2.schema.json) | `data/synthetic/<set_id>/<run_id>.jsonl` | wyjście, układ jak w [schemas/README.md](../../schemas/README.md) „Zapis przebiegu” |
| `manifest.jsonl` | brak (§10 pkt 3) | `data/synthetic/<set_id>/` | wyjście: wiersz na przebieg |

Jawna tablica (np. `[4, 6, 3, 1, 2]`) staje się instancją ręczną (`generator: null`). Pliki: UTF-8 bez BOM, LF. Wiersz manifestu:
`run_id`, `file`, `instance_id`, `task`, `n`, `algorithm`, `variant`, `perturbation` (`{kind, percent, seed, applied}` lub `null`), `seed`,
`truth` (tekst etykiety protokołu: `known:bubble_sort`, `hybrid:A+B`, `optimal`, `optimal_detours`, `other`, `too_short`), `segments`
(hybryda: `{algorithm, variant, from, to}`, `[from, to)` w operacjach bez `done`; inaczej `null`).

## 4. Interfejsy

Propozycja (układ plików ustala pierwszy kod).

```python
Op = tuple[str, dict[str, int], str]            # (tool, args, result)
def run_pattern(algorithm_id, variant, state: dict, knowledge: dict | None = None) -> PatternResult
    # PatternResult: tokens, ops (ostatnie done), final_state
def run_reference(algorithm_id, variant, instance: dict) -> Trace   # run_pattern na initial_state + opakowanie
def perturb(trace, perturbation: Perturbation, seed: int) -> tuple[Trace, int]   # (ślad, applied)
def hybrid(instance, first: tuple[str, str], second: tuple[str, str], seed: int) -> Trace
def synthesize(trace, perturbation | None, seed: int, ctx: SetContext) -> SyntheticRun  # zdarzenia v2 + wiersz manifestu
REGISTRY: dict[(algorithm_id, variant), AlgorithmInfo]   # task, kolejność wytwarzania
```

`Trace`: `algorithm_id`, `variant`, `instance`, `ops`, `segments`. `Perturbation(kind, percent)`, `percent` całkowite.

**Dla analizatora** (importuje pakiet jako bibliotekę, bo reguła hybrydy [classification-rules.md](../protocol/classification-rules.md) §5
uruchamia wzorzec od stanu pośredniego): `run_pattern` przyjmuje DOWOLNY stan początkowy w postaci `common.v2` (`sort_state`,
`hanoi_state`, `search_state`): sortowanie to tablica dowolnych różnych liczb (długość >= 2, nie tylko permutacja 1..N); Hanoi to
dowolny legalny stan palików, cel zawsze palik 2; wyszukiwanie to tablica rosnąca i `target`, a `knowledge` (`{indeks: wartość}`) to
odczyty już znane, których wzorzec nie powtarza. Tokeny: sortowanie `("compare" | "swap", min(i, j), max(i, j))` (§3 protokołu), Hanoi
`("move", from_peg, to_peg)`, wyszukiwanie `("read", index)`; `ops` zachowuje argumenty jak w wywołaniu. Funkcja nie dotyka plików.
Identyfikatory `^[a-z][a-z0-9_]*$` (lista w §5.2-5.4). Błędy (podklasy `ValueError`): `InstanceError`, `UnknownAlgorithm`, `UnknownVariant`,
`UnsupportedPerturbation`, `IllegalOperation`.

CLI: `uv run --locked python -m algotrace_references <polecenie>`: `list`; `run <id> [--variant V] (--array 4,6,3,1,2 | --instances F --instance-id ID)`;
`synthesize --set set.json --instances F --out data/synthetic/<set_id>`; `make-instances --out F --base-seed S --per-cell K` (propozycja);
`validate <katalog>`. Kod wyjścia: 0, 2 błędne wejście, 1 błąd wewnętrzny.

## 5. Zachowanie krok po kroku

### 5.1 Zasady wspólne

- Stan ma tylko atrapa środowiska; ona sprawdza zakres, `i != j` i legalność ruchu ([prompts.md](../protocol/prompts.md) §9);
  naruszenie to `IllegalOperation` (błąd programu).
- Wyniki: `compare(i, j)` `less` gdy `a[i] < a[j]`, inaczej `greater`; `swap`, `move` `ok`; `read` wartość dziesiętnie;
  `done` `accepted`. Każdy ślad kończy jedno `done` (wyszukiwanie: `done(index)` z odpowiedzią). Brak wywołań odrzuconych i
  błędów wstrzykniętych. `swap(p, p)` nie występuje (algorytm sprawdza `p != q`).

### 5.2 Sortowanie (rosnąco)

| Id | Warianty | Definicja |
|---|---|---|
| `bubble_sort` | `standard`, `early_exit`, `reverse`, `reverse_early_exit` | `standard`: `p = 0..N-2`, `j = 0..N-2-p`: `compare(j, j+1)`, `greater` daje `swap(j, j+1)` (jak `bubble_sort_tokens` w [check_examples.py](../../schemas/check_examples.py)); `early_exit`: koniec po przejściu bez zamiany; `reverse`: `j = N-1` w dół do `p+1`, `compare(j-1, j)`, `swap(j-1, j)` |
| `insertion_sort` | `standard`, `right_to_left` | `standard`: `i = 1..N-1`, `j = i`; póki `j > 0`: `compare(j-1, j)`, `less` kończy, `greater` daje `swap(j-1, j)`, `j -= 1`. `right_to_left`: `i = N-2` w dół do 0; póki `j < N-1`: `compare(j, j+1)`, `greater` daje `swap(j, j+1)`, `j += 1` |
| `selection_sort` | `standard`, `max` | `standard`: `i = 0..N-2`, `m = i`, `j = i+1..N-1`: `compare(j, m)`, `less` daje `m = j`; potem `swap(i, m)` gdy `m != i`. `max`: `i = N-1` w dół do 1, `m = 0`, `j = 1..i`: `compare(j, m)`, `greater` daje `m = j`; `swap(m, i)` gdy `m != i` |
| `quicksort` | `last`, `first`, `middle`, `median_of_3` | oś: ostatni, pierwszy, środkowy `(lo+hi)//2` albo mediana z trzech. Podział Lomuta: gdy oś `p != hi` `swap(p, hi)`; `i = lo`; `j = lo..hi-1`: `compare(j, hi)`, `less`: `swap(i, j)` gdy `i != j`, `i += 1`; na końcu `swap(i, hi)` gdy `i != hi`; rekurencja lewa `[lo, i-1]`, potem prawa |
| `merge_sort` | `top_down`, `bottom_up` | scalanie w miejscu: `merge(lo, mid, hi)`: `i = lo`, `j = mid`; póki `i < j` i `j < hi`: `compare(i, j)`; `less`: `i += 1`; `greater`: `swap(k-1, k)` dla `k = j` w dół do `i+1`, potem `i += 1`, `j += 1`. `top_down`: `mid = (lo+hi)//2`, lewa, prawa, `merge`. `bottom_up`: `w = 1, 2, 4, ... < N`, `lo = 0, 2w, ...` z `lo < N-w`: `merge(lo, lo+w, min(lo+2w, N))` |
| `cocktail_sort` | `standard`, `backward_first` | `lo = 0`, `hi = N-1`; w prawo (`j = lo..hi-1`, `compare(j, j+1)`, `swap` gdy `greater`), `hi -= 1`; w lewo (`j = hi` w dół do `lo+1`, `compare(j-1, j)`, `swap(j-1, j)`), `lo += 1`; na przemian póki `lo < hi`, koniec po przejściu bez zamiany; `backward_first` zaczyna w lewo |

Mediana z trzech (`hi - lo >= 2`, krócej oś to `hi`): `mid = (lo+hi)//2`, `r1 = compare(lo, mid)`, `r2 = compare(mid, hi)`;
`less/less` lub `greater/greater`: `mid`; `less/greater`: `compare(lo, hi)`, `less` daje `hi`, inaczej `lo`;
`greater/less`: `compare(lo, hi)`, `less` daje `lo`, inaczej `hi`. Te porównania są operacjami śladu.

### 5.3 Hanoi

Id `recursive_hanoi`, warianty `standard` i `iterative`, ten sam ciąg `2^n - 1` ruchów na palik 2 ([classification-rules.md](../protocol/classification-rules.md) §7).
`standard`: `solve(k, a, b, c)`: `solve(k-1, a, c, b)`, `move(a, b)`, `solve(k-1, c, b, a)`, start `solve(n, 0, 2, 1)`.
`iterative`: najmniejszy krążek rusza cyklicznie `0→2→1→0` (n nieparzyste) albo `0→1→2→0` (parzyste), między jego ruchami jedyny
legalny ruch bez niego. Od stanu pośredniego `standard` idzie od największego krążka: stoi na celu - cel mniejszych bez zmian; nie - mniejsze na trzeci palik,
krążek na cel, mniejsze na cel. Narzędzie `move(from_peg, to_peg)`.

### 5.4 Wyszukiwanie

`done(index)` to pozycja albo `-1`, równa `answer` instancji; indeks czyta się najwyżej raz.

| Id | Warianty | Definicja (`[lo, hi]` startuje `[0, N-1]`) |
|---|---|---|
| `binary_search` | `lower_mid`, `upper_mid` | sonda `(lo+hi)//2` albo `(lo+hi+1)//2`; mniejsza `lo = s+1`, większa `hi = s-1`; pusty przedział: `-1` |
| `linear_search` | `left`, `right` | `0, 1, ...` do równej (wynik), większej od celu albo końca (`-1`); `right`: `N-1, N-2, ...`, koniec przy równej albo mniejszej |
| `interpolation_search` | `standard` | `read(lo)`, `read(hi)` (cel poza zakresem: `-1`); potem `pos = lo + (target - a[lo]) * (hi - lo) // (a[hi] - a[lo])`, `read(pos)`; mniejsza `lo = pos+1`, większa `hi = pos-1` |
| `jump_search` | `standard` | krok `isqrt(N)`; sondy `s-1, 2s-1, ...` (do `N-1`) do wartości `>= target`; potem liniowo od początku bloku, `>` daje `-1` |
| `exponential_search` | `standard` | sondy `1, 2, 4, ...` (do `N-1`) do wartości `>= target`; potem połowienie w `[b//2, sonda]` |

### 5.5 Zakłócenia

`Perturbation(kind, percent)` zmienia listę operacji bez `done`; atrapa odtwarza ją i liczy wyniki od nowa. Liczba zakłóceń
`m = 0` dla `percent = 0`, inaczej `max(1, (percent * L + 50) // 100)` (`L` to liczba operacji). Losowanie: `SplitMix64(seed)`
w kolejności z tabeli; `applied` to liczba faktycznie zastosowanych zakłóceń.

| Rodzina | `kind` | Jedno zakłócenie |
|---|---|---|
| sortowanie | `insert_compare` | `e = compares[below(len(compares))]`; `pos = e + 1 + below(len(lista) - e)`; wstaw kopię `compare` z `e`, przy `below(2) == 1` z `(j, i)` |
| sortowanie | `skip_compare` | usuń `compares[below(len(compares))]`; `swap` nigdy nie jest pomijany (stan końcowy posortowany) |
| sortowanie | `reorder` | kandydaci `p`: operacje `p` i `p+1` nie są obie `swap`; zamień `p = cands[below(len(cands))]` z `p+1` |
| sortowanie | `mixed` | `below(3)`: 0 `insert_compare`, 1 `skip_compare`, 2 `reorder` |
| Hanoi | `detour` | `pos = below(len(moves) + 1)`; wybierz `below(len(legal))` z legalnych ruchów po `pos` ruchach (`from`, potem `to` rosnąco); wstaw ruch i jego odwrotność |
| wyszukiwanie | `extra_reads` | `pos = below(len(reads) + 1)`, `index = below(N)`; wstaw `read(index)` |
| wyszukiwanie | `shift_probe` | `p = below(len(reads))`, `d = +1` gdy `below(2) == 1`, inaczej `-1`; `index += d`, poza `[0, N-1]` `index -= d` |

Klasa „inna strategia” dla Hanoi, id `random_walk`: legalne błądzenie od startu, ruch na palik 2 ma wagę 3, inne 1, natychmiastowe
cofnięcie pomijane, gdy jest inny ruch; `below(suma wag)`; limit `100 * (2^n - 1)` ruchów, potem nowa próba (do 20). `truth: other`.

**Hybryda** `hybrid(instance, (A, vA), (B, vB), seed)`, `A != B`: `L` to liczba operacji czystego śladu A; `lo = (L+3)//4`,
`hi = (3*L)//4`, `k = lo + below(hi - lo + 1)`. Ślad: pierwsze `k` operacji A, potem pełny przebieg B od stanu po nich, `done`.
Podział może paść między `compare` a `swap`. `truth`: `hybrid:A+B`.

### 5.6 Zbiór i zapis przebiegu

`set.json` (propozycja): `set_id`, `base_seed`, `ts_base`, `percents` (np. `[0, 5, 10]`), `kinds` (domyślnie `["mixed"]`), `hybrids_per_instance`,
`algorithms`, `instances`; same liczby całkowite; `config_sha256` to SHA-256 jego kanonicznego JSON (RFC 8785). Kolejność: instancje z pliku;
algorytmy i warianty z rejestru; `percent` rosnąco, `kind`; hybrydy na końcu. Przebieg `j` (od 0) ma `seed = base_seed + j`.

Zdarzenia jak w [run.bubble-sort-n5.jsonl](../../schemas/examples/run.bubble-sort-n5.jsonl) (jedna tura na krok). `run_start`:
`series`, `instance_id`, `instance_seed`, `task`, `n`, `initial_state` z instancji; `series_id` `synthetic-<set_id>`; `condition` `main`;
`faults`, `price` `null`; `model_key` `ref-<id>-<wariant>` z `_` na `-`; `provider` `openai_compatible`; `model_requested`
`reference:<id>:<wariant>`; `repetition` od 1 dla pary (`model_key`, `instance_id`); `run_id` jak w [schemas/README.md](../../schemas/README.md)
„Identyfikatory i wersje”; `prompt` `synthetic`/`main`/`en`, `sha256` pustego napisu; `tools.tool_set` `sort-v1`, `hanoi-v1`, `search-v1`,
`compare_result_format` `words` (sortowanie) lub `null`, `sha256` listy `names`; `limits.max_steps` ze wzoru
[run-settings.md](../protocol/run-settings.md) §3, podniesiony do kroków + 1; pozostałe pola stałe (`parallel_tool_calls` `true`,
`software.runtime` `Python 3.13`, reszta `null`). `model_turn`: `text` i `usage` `null`, `call_id` `call_<krok:03d>_0`, `arguments_raw` bez
spacji. `tool_call.state_after`: pełny stan (wyszukiwanie `null`). `run_end`: `done_solved`, `steps` = `turns` = operacje z `done`.
Czas zdarzenia `k` to `ts_base + k ms` (nie zegar), więc to samo ziarno daje te same bajty.

`SplitMix64` ([Steele, Lea, Flood 2014](https://doi.org/10.1145/2660193.2660195)): `x += 0x9E3779B97F4A7C15`, `z = x`,
`z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9`, `z = (z ^ (z >> 27)) * 0x94D049BB133111EB` (mod 2^64), wynik `z ^ (z >> 31)`;
`below(n) = next() % n`. Moduł `random` nie jest używany.

## 6. Błędy i przypadki brzegowe

- Sortowanie: długość < 2 albo powtórzenia to `InstanceError` (`sort_state`); tablica już posortowana jest poprawna (T5).
- Wyszukiwanie `N = 1`: jeden odczyt (`too_short`, także gdy ślad ma najwyżej 2 odczyty). `answer` niezgodne z wzorcem: `InstanceError`.
- Wariant spoza algorytmu: `UnknownVariant`; algorytm obcy rodzinie instancji: `InstanceError`; `hybrid` z `A == B` lub `hi < lo`: `InstanceError`.
- Zakłócenie obce rodzinie (`detour` dla sortowania): `UnsupportedPerturbation`. Brak kandydatów: `applied < m`.
- Zakłócenie nie daje nielegalnego wywołania (indeksy w zakresie, `i != j`, ruch legalny); złamanie mimo to to `IllegalOperation`.

## 7. Wymagania protokołu

- Wzorce i warianty: [classification-rules.md](../protocol/classification-rules.md) §3 (sortowanie), §7 (Hanoi), §8 (wyszukiwanie); dane kalibracyjne §6, KPI §11.
- Instancje i ziarna: [design.md](../protocol/design.md) §3; narzędzia: [prompts.md](../protocol/prompts.md) §8-9; limity kroków:
  [run-settings.md](../protocol/run-settings.md) §3; stos: [0001](../decisions/0001-stos-technologiczny.md).

## 8. Testy akceptacyjne

Liczby sprawdzone skryptem. Testy w `tests/python/references/`.

- **T1 Liczby kroków.** Dane: `[4, 6, 3, 1, 2]`, wariant domyślny. Oczekiwane (porównania / zamiany):
  `bubble_sort` 10 / 8, `insertion_sort` 10 / 8, `selection_sort` 10 / 2, `quicksort` (`last`) 7 / 2, `merge_sort` 7 / 8,
  `cocktail_sort` 10 / 8; koniec `done`, tablica `[1, 2, 3, 4, 6]`.
- **T2 Warianty.** Ta sama tablica: `quicksort` `first` 6 / 6, `middle` 6 / 6, `median_of_3` 8 / 6; `merge_sort` `bottom_up` 6 / 8.
- **T3 Początek bąbelkowego.** Pierwsze 5 operacji: `compare(0,1)` `less`, `compare(1,2)` `greater`, `swap(1,2)` `ok`, `compare(2,3)` `greater`, `swap(2,3)` `ok`; razem 19 z `done`.
- **T4 Zgodność z przykładem.** Dane: [run.bubble-sort-n5.jsonl](../../schemas/examples/run.bubble-sort-n5.jsonl), instancja `sort-n5-example`.
  Działanie: `synthesize` czystego `bubble_sort` `standard`. Oczekiwane: 40 linii; `tool`, `arguments`, `result`, `state_after` 19 zdarzeń
  `tool_call` jak w przykładzie; `run_end.steps` 19, `duration_ms` 39; każda linia przechodzi `Draft202012Validator`.
- **T5 Wczesne zakończenie, tablica posortowana.** Dane: `[2, 1, 3, 4, 5]` i `[1, 2, 3, 4, 5]`. Oczekiwane: pierwsza `bubble_sort` `standard` 10 / 1,
  `early_exit` 7 / 1; druga `standard` 10 / 0, `early_exit` 4 / 0, `insertion_sort` 4 / 0, `merge_sort` 5 / 0, `cocktail_sort` 4 / 0.
- **T6 Zamiany = inwersje.** Dane: `[7, 9, 10, 8, 6, 4, 1, 5, 2, 3]` (36 inwersji). Oczekiwane (porównania / zamiany): `bubble_sort` 45 / 36,
  `insertion_sort` 42 / 36, `selection_sort` 45 / 6, `quicksort` `last` 28 / 6. Wszystkie permutacje N = 2..7 (5912) kończą posortowane w każdym wariancie.
- **T7 Hanoi.** Dane: `hanoi-n3-example` z [instances.example.jsonl](../../schemas/examples/instances.example.jsonl). Oczekiwane ruchy:
  `(0,2) (0,1) (2,1) (0,2) (1,0) (1,2) (0,2)`, razem 7 + `done`; stan końcowy trzy paliki: puste, puste, `[3,2,1]`; `iterative` ten sam ciąg dla n = 3, 4, 5.
- **T8 Wyszukiwanie, cel obecny.** Dane: `search-n15-example` (tablica `[2,5,7,11,13,17,19,23,29,31,37,41,43,47,53]`, cel 23, `answer` 7).
  Oczekiwane indeksy `read`: `binary_search` `lower_mid` `[7]` (`truth: too_short`), `linear_search` `left` `[0..7]`, `right`
  `[14,13,12,11,10,9,8,7]`, `interpolation_search` `[0,14,5,6,7]`, `jump_search` `[2,5,8,6,7]`, `exponential_search` `[1,2,4,8,6,7]`;
  koniec `done(7)`.
- **T9 Cel nieobecny.** Dane: ta sama tablica, cel 24, `answer` -1. Oczekiwane: `binary_search` (oba warianty) `[7,11,9,8]`, `linear_search`
  `left` `[0..8]`, `right` `[14..7]`, `interpolation_search` `[0,14,6,7,8]`, `jump_search` `[2,5,8,6,7]`, `exponential_search` `[1,2,4,8,6,7]`;
  `done(-1)`. Dla `[10,20,30,40]`, cel 10: `lower_mid` `[1,0]`, `upper_mid` `[2,1,0]`.
- **T10 SplitMix64.** Oczekiwane: `SplitMix64(0)`, trzy `next()`: `0xE220A8397B1DCDAF`, `0x6E789E6AA1B965F4`, `0x06C45D188009454F`;
  `SplitMix64(1).below(10)` pięć razy: `5, 9, 0, 5, 1`; `SplitMix64(4).below(5)` sześć razy: `3, 4, 2, 2, 1, 0`.
- **T11 Zakłócenia sortowania.** Dane: ślad bąbelkowego `[4, 6, 3, 1, 2]` (18 operacji), `seed` 7. Oczekiwane: `insert_compare` 5%: `m` = 1, 19 operacji,
  dodatkowe `compare(0,1)` `less` na końcu; 10%: `m` = 2, 20 operacji; `skip_compare` 5%: 17 operacji (9 `compare`, 8 `swap`), po `swap(2,3)` od razu
  `swap(0,1)`; `reorder` 5%: 18 operacji, pierwsze dwie to `compare(1,2)` `greater`, `compare(0,1)` `less`. Każdy daje `[1, 2, 3, 4, 6]`.
- **T12 Hybryda.** Dane: `[4, 6, 3, 1, 2]`, A = `bubble_sort`, B = `selection_sort` (`standard`), `seed` 3. Oczekiwane: `L` = 18, `k` = 5, stan
  w podziale `[4, 3, 1, 6, 2]`, B daje 14 operacji, razem 19 (13 `compare`, 6 `swap`); `segments` `[{bubble_sort, standard, 0, 5},
  {selection_sort, standard, 5, 19}]`; `run_pattern` selection od `{"array": [4,3,1,6,2]}` daje te same 14 operacji.
- **T13 Hanoi z objazdem.** Dane: `hanoi-n3-example`, `detour`, 10%, `seed` 5. Oczekiwane: 9 ruchów `(0,2) (0,1) (2,0) (0,2) (2,1) (0,2) (1,0) (1,2) (0,2)`,
  `truth` `optimal_detours`. `random_walk` (n = 3, 4, 5) kończy w stanie celu, `truth` `other`.
- **T14 Powtarzalność.** Dane: ten sam `set.json` i plik instancji. Działanie: dwa razy `synthesize`. Oczekiwane: równe SHA-256 plików i manifestu;
  po zmianie `base_seed` zmieniają się `seed` i `run_id`.
- **T15 Normalizacja tokenów.** Dane: `[4, 6, 3, 1, 2]`. Oczekiwane: w tokenach `i <= j`; odległość edycyjna tokenów `bubble_sort` i
  `selection_sort` to 13 (bez normalizacji 18).
- **T16 Błędy.** Oczekiwane: `run_reference("selection_sort", "early_exit", ...)` rzuca `UnknownVariant`; tablica `[5]` `InstanceError`; `hybrid` z A
  równym B `InstanceError`; `detour` dla sortowania `UnsupportedPerturbation`; CLI kończy z kodem 2.

## 9. Wiedza techniczna i źródła

- Wzór sprawdzania: `python -I schemas/check_examples.py` (funkcje `bubble_sort_tokens` itd., `canonical_json` wg RFC 8785).
- `jsonschema` 4.x: `Draft202012Validator` z `FormatChecker`; schematy odwołują się po `$id`, więc rejestr `referencing` (jak `LibraryValidator` w `check_examples.py`).
- JSONL: `json.dumps(obj, separators=(",", ":"), ensure_ascii=False)` i `\n`; plik otwierać z `newline="\n"` i `encoding="utf-8"`
 . Kolejność kluczy jak w przykładach.
- Pułapki: bąbelkowe i przez wstawianie robią tyle zamian, ile inwersji (8 w przykładzie), różni je kolejność; `early_exit` i `standard`
  mogą dać identyczny ślad, więc analizator może mieć `ambiguous`.
- Hanoi: optimum `2^n - 1` (Romik, https://arxiv.org/abs/math/0310109). SplitMix64: https://doi.org/10.1145/2660193.2660195. Wyszukiwanie interpolacyjne, skokowe, wykładnicze: Wikipedia (Interpolation search, Jump search,
  Exponential search). JSON Schema: https://json-schema.org/draft/2020-12; kanonizacja: https://www.rfc-editor.org/rfc/rfc8785.

## 10. Do ustalenia

1. Oznaczenie przebiegu syntetycznego: schemat nie ma takiego pola. Propozycja: `provider: openai_compatible`, `series_id: synthetic-<set_id>`, prawdę trzyma manifest.
2. Instancje syntetyczne (inne ziarno niż pilotaż i pełne badanie). Propozycja: `make-instances` w tym pakiecie (SplitMix64, zasady
   [design.md](../protocol/design.md) §3, `series: pilot`, odrębne `generator.name`), 20 instancji na komórkę.
3. Schemat manifestu. Propozycja: `schemas/synthetic-manifest.v2.schema.json` dopisany przez lidera; do tego czasu opis z §3.
4. Nazwy wzorców wyszukiwania i wariantów Hanoi: schemat podaje tylko `binary_search`, `linear_search`, `recursive_hanoi`; propozycja: §5.3-5.4.
5. `text` pierwszej tury: `null`; `tools.sha256`, `prompt.sha256` zastępcze; `state_after` w wyszukiwaniu `null` (propozycja).
6. Publikacja: w repozytorium mały zbiór `smoke-n5`, reszta lokalnie z `set.json` ([data/README.md](../../data/README.md)); plik N = 20 ma
   rząd 0,5 MB (szacunek). `random_walk`: waga 3 dla ruchu na palik 2.
7. Rozbieżność skryptu z protokołem: `selection_sort_tokens` w [check_examples.py](../../schemas/check_examples.py) zapisuje `("compare", j, m)`
   z `j > m` bez normalizacji, a protokół ([classification-rules.md](../protocol/classification-rules.md) §3) każe `(min, max)`; na
   `[4, 6, 3, 1, 2]` odległość bąbelkowe-wybór to 13 z normalizacją i 18 bez. Propozycja: normalizacja w `run_pattern`; poprawić skrypt.
8. Notatka źródłowa lidera a repo (wygrywa repo): szósty algorytm to koktajlowy (notatka dopuszcza też Shella); wyszukiwanie ma 5 wzorców
    (skokowe i wykładnicze oprócz trzech z README modułu); oś quicksorta ma 4 warianty.
