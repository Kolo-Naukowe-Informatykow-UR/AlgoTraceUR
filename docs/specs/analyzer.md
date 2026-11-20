# Specyfikacja: analizator przebiegów (`src/analyzer/`)

Program w Pythonie 3.13, pakiet `algotrace_analyzer` w workspace uv repozytorium. Status: kod jeszcze nie istnieje.
Czyta zapisy przebiegów (od środowiska, [environment.md](environment.md)) i odtwarza na tej samej instancji algorytmy
wzorcowe z pakietu `algotrace_references` ([references.md](references.md)); zapisuje wyniki analizatora czytane przez
analizę wyników ([analysis.md](analysis.md)). Reguły klasyfikacji są w protokole i kod ich nie zmienia. Folder:
[src/analyzer/README.md](../../src/analyzer/README.md).

## 1. Cel

Z zapisu jednego przebiegu ustalić, czy model osiągnął cel, jaką strategią (znany algorytm i wariant, hybryda,
strategia niejednoznaczna albo nowa; w Hanoi i wyszukiwaniu etykiety własne) i jak efektywnie (porównania, zamiany,
ruchy, odczyty wobec granic i wzorców), dokładnie według
[classification-rules.md](../protocol/classification-rules.md), i zapisać wynik zgodny ze
`schemas/analyzer-result.v2.schema.json`. Przed pełnym badaniem ten sam program kalibruje progi na przebiegach
syntetycznych i mierzy własną trafność (KPI 1).

## 2. Granice

- Nie uruchamia modeli i nie tworzy przebiegów; przebiegi syntetyczne tworzy [references.md](references.md).
- Nie implementuje algorytmów wzorcowych sam: woła publiczne API `algotrace_references` (jedyny dozwolony import
  między programami, [AGENTS.md](../../AGENTS.md)), bo reguła hybrydy uruchamia wzorzec od stanu pośredniego śladu.
- Nie liczy statystyki między przebiegami (skuteczność modeli, testy, wykresy): to [analysis.md](analysis.md).
- Nie zmienia progów po obejrzeniu przebiegów modeli: wartości zamrożone są w
  [classification-rules.md](../protocol/classification-rules.md) §12 i w pliku kalibracji (sekcja 3).
- Nie koduje ręcznie: etykiety ręczne (deklaracje, strategie `new`) wczytuje z pliku koderów (sekcja 10).

## 3. Wejścia i wyjścia

| Kierunek | Co | Format | Miejsce |
|---|---|---|---|
| wejście | zapis przebiegu (jeden plik na przebieg) | `schemas/run-event.v2.schema.json` | `data/runs/<series_id>/<run_id>.jsonl` (`output.runs_dir`), syntetyczne w `data/synthetic/` |
| wejście | wiersz instancji (dla wyszukiwania: `answer`, `target_present`) | `schemas/instance.v2.schema.json` | `instances/<series>.jsonl` |
| wejście | wzorce | API `algotrace_references` | pakiet w workspace |
| wejście | progi `tau_N`, `lambda`, `m_min`, `tau_H`, `tau_S`, `delta` | plik kalibracji z `calibration_id` (propozycja formatu: sekcja 10) | wartości jak w protokole §12 |
| wejście | kody ręczne deklaracji i strategii `new` (opcjonalnie) | CSV koderów (sekcja 10) | `data/results/` |
| wyjście | wynik analizatora, jeden obiekt na linię, jeden na przebieg (każdą próbę, także zastąpioną) | `schemas/analyzer-result.v2.schema.json` | `output.analysis_file`, np. `data/results/<series_id>.analysis.jsonl` |
| wyjście | raport kalibracji i walidacji (KPI 1) | Markdown + CSV macierzy pomyłek | `docs/` (miejsce w [work-plan.md](../project/work-plan.md)) |

Pola wyniku: `run_id`, `series_id`, `task`, `n`, `instance_id`, `analyzer_version`, `created`, `calibration_id`,
`token_variant` (`full`, `type`, `relative`; analiza główna `full`), `trace_length`, `metrics`, `distances`
(`reference`, `variant`, `distance`, `normalized_distance`, `reference_length`, od najbliższego), `label`
(`text`, `kind`, `algorithms`, `variant`, `subtype`, `failure_detail`, `margin`), `exploratory_label`, `segments`
(`start_step`, `end_step`, `reference`, `variant`, `normalized_distance`), `declaration` (`text`,
`declared_algorithm`, `labelled_by`, `matches_label`). Przykład: `schemas/examples/analyzer-result.bubble-sort-n5.json`.

## 4. Interfejsy

Propozycja modułów (układ ustala pierwszy kod):

```python
# io.py
def read_run(path: Path) -> RunLog                       # run_start, turns, calls, run_end; walidacja schematem
def write_results(results: Iterable[dict], path: Path) -> None   # JSONL, UTF-8, LF, kolejność pól ze schematu
# tokens.py
Token = tuple[str, int, int]                             # ("C"|"S", min(i,j), max(i,j)); Hanoi ("M", from, to)
def sort_tokens(log: RunLog) -> list[Token]               # tylko executed: true, bez done, w kolejności wykonania
def split_at_fault(log: RunLog) -> tuple[list[Token], list[Token], list[int]]  # przed, po, stan w chwili błędu
# measures.py
def info_bound(n: int) -> int                             # ceil(log2 n!)
def inversions(a: list[int]) -> int
def min_swaps(a: list[int]) -> int                        # N - liczba cykli
def redundant_compares(initial: list[int], tokens: list[Token]) -> int
def hanoi_distance_to_goal(pegs: list[list[int]], target: int = 2) -> int
# distance.py
def edit_distance(t: list[Token], r: list[Token]) -> int  # Levenshtein, koszty 1/1/1
def normalized(t, r) -> float                             # d / max(len(t), len(r)); 0.0 dla dwóch pustych
def prefix_normalized(t, r) -> float                      # min_m d(t, r[:m]) / max(len(t), m)
# classify.py
def classify_sort(log, refs, cal) -> dict                 # label, distances, segments, margin
def segment_hybrid(tokens, initial, refs, cal) -> list[Segment] | None
def classify_hanoi(log, cal) -> dict
def classify_search(log, instance, cal) -> dict
def failed_label(log, instance) -> dict                   # failed:<subtype>[:<detail>]
# declaration.py
def declaration_text(log) -> str                          # tekst do pierwszej tury z wywołaniem włącznie
def rule_label(text: str) -> str | None                   # słowa kluczowe -> nazwa wzorca, labelled_by "rule"
# calibrate.py, validate.py: kalibracja (protokół §6) i KPI 1 (§11)
```

CLI (propozycja), z katalogu głównego repozytorium:

```
uv run --locked python -m algotrace_analyzer analyze --runs data/runs/<series_id> \
    --instances instances/full.jsonl --calibration <plik> --out data/results/<series_id>.analysis.jsonl
uv run --locked python -m algotrace_analyzer calibrate --synthetic data/synthetic --seed <ziarno> --out <plik>
uv run --locked python -m algotrace_analyzer validate --synthetic data/synthetic --calibration <plik> --report docs/
```

Kody wyjścia: 0 sukces, 1 błąd danych (zapis niezgodny ze schematem, brak instancji), 2 błąd użycia. Plik z błędem
nie przerywa całej serii: trafia do listy problemów, a reszta jest analizowana.

## 5. Zachowanie krok po kroku

1. **Odczyt.** Zapis waliduje się ze schematem; plik bez `run_end` (przebieg przerwany) się pomija z ostrzeżeniem.
   Zapis przebiegu zastąpionego (`superseded_by` niepuste) też dostaje wynik (analiza wybiera ostatnią próbę).
2. **Sukces czy porażka** ([classification-rules.md](../protocol/classification-rules.md) §2): sortowanie i Hanoi
   dostają strategię przy `solved: true` (także `step_limit` bez `done`), wyszukiwanie tylko przy `done_solved`.
   Inaczej `label.kind: failed` z `subtype` według `end_reason`: `done_unsolved` → `wrong_done`, `step_limit` →
   `step_limit`, `too_many_errors` → `errors`, `no_tool_call` → `no_tool_call`, `context_exceeded` → `context`,
   `api_error`, `time_limit`, `cost_limit`, `interrupted` → `infra`. Wyszukiwanie z `wrong_done`: `failure_detail`
   `false_absent` (odpowiedź -1, liczba jest), `false_present` (pozycja, liczby nie ma), `wrong_index`.
3. **Tokeny** (§3): sortowanie `C(i,j)` i `S(i,j)` z indeksami `(min, max)`, tylko wywołania wykonane, bez `done`;
   błędy walidacji i wstrzyknięte nie są tokenami. `trace_length` = liczba tokenów. Kilka wywołań w turze: tokeny
   w kolejności wykonania, granice tur nie zmieniają odległości (§9).
4. **Miary** (`metrics`): `compares`, `swaps`, `redundant_compares` (relacje na tożsamości elementów, nie pozycjach),
   `info_bound_compares`, `inversions`, `min_swaps`; Hanoi `moves`, `optimal_moves` (`2^n - 1`); wyszukiwanie
   `reads`; wszystkie rodziny `validation_errors`, `recoveries_after_error`, `longest_error_streak`. Miary
   dodatkowe (np. nadmiar długości `len(t) / len(r*)`, odsetek tur z kilkoma wywołaniami, zamiany szkodliwe, inwersje
   w stanie końcowym) jako dodatkowe pola liczbowe `metrics`.
5. **Odległości sortowania.** Każdy algorytm wzorcowy w każdym wariancie odtworzony na `initial_state`; `distance`
   i `normalized_distance` (zaokrąglenie do 4 miejsc tylko w zapisie, porównania na pełnej precyzji), lista od
   najbliższego, remis po nazwie wzorca, potem wariantu. Odległość do algorytmu = minimum po wariantach.
6. **Etykieta sortowania** (§4-5): `A1`, `A2` = dwa najbliższe różne algorytmy. `d_A1 <= tau_N`: `ambiguous:A1|A2`,
   gdy `d_A2 - d_A1 < delta` i `d_A2 <= tau_N`, inaczej `known:A1` z wariantem. `d_A1 > tau_N`: segmentacja
   programowaniem dynamicznym (wzorzec odcinka od stanu po `t[0..j)`, odcinki wcześniejsze w trybie prefiksowym,
   ostatni pełnym wzorcem, kara `lambda` za odcinek, sąsiednie odcinki tego samego algorytmu łączone); hybryda przy
   spełnieniu czterech warunków §5 (`segments` z numerami kroków), inaczej `new` z podtypem `info_first` (co najmniej
   80% porównań przed pierwszą zamianą i zamian nie więcej niż `N - c + 2`) albo `other`. `margin` =
   `normalized_distance` drugiego wzorca minus pierwszego (`null`, gdy jest tylko jeden).
7. **Hanoi** (§7): tokeny `M(from,to)` wykonanych `move`; wzorzec optymalny; `optimal`, gdy ciąg jest równy wzorcowi,
   `optimal_detours`, gdy `d <= tau_H`, inaczej `other`. Cechy opisowe (ruchy ponad optimum, cofnięcia, rytm
   najmniejszego krążka, odległość do celu po każdym ruchu) jako dodatkowe pola `metrics`.
8. **Wyszukiwanie** (§8): sondy `read` z wartościami, przedział `[lo, hi]` po każdej sondzie, przewidywanie każdego
   wzorca z tego samego stanu wiedzy, `dev_P = średnia |p_t - pred_P,t| / N`; `known:P`, `ambiguous:P1|P2`
   (różnica poniżej `delta`), `other` (`dev_P > tau_S`), `too_short` przy co najwyżej 2 sondach.
9. **Przebieg nieudany:** `exploratory_label` w trybie prefiksowym, gdy ma co najmniej `2N` wykonanych operacji
   (Hanoi `2^(n-1)`), inaczej `null` (§2).
10. **Warunek z błędami** (§9): ślad dzieli się na pierwszym wywołaniu z błędem wstrzykniętym; odcinek przed nim
    w trybie prefiksowym od stanu początkowego, odcinek po nim pełnym wzorcem od stanu w chwili błędu; odcinek krótszy
    niż `m_min` to `too_short`; ten sam podział (po `fault_position`-tym poprawnym wywołaniu) w przebiegu-parze
    z serii głównej. Gdzie trafiają etykiety odcinków: sekcja 10.
11. **Deklaracja:** `declaration.text` z zapisu ([prompts.md](../protocol/prompts.md) §6), `declared_algorithm` z kodu
    ręcznego (`labelled_by: manual`) albo z reguły słów kluczowych (`rule`), `null` przy pustym tekście; `matches_label`
    = `declared_algorithm` równy algorytmowi etykiety (`null`, gdy któregoś brak).
12. **Kalibracja i walidacja** (§6, §11): podział instancji syntetycznych 60/40 po `instance_id`, siatki `tau` 0,00-0,50
    co 0,01, `lambda` z {1, 2, 3, 5, 8}, `m_min` z {N, 2N, 4N}, rundy z pominiętym algorytmem, F1 makro, remisy na
    korzyść ostrożności; KPI 1: dolna granica 95% przedziału Wilsona trafności ≥ 0,95 na części testowej.

## 6. Błędy i przypadki brzegowe

- **Pusty ślad** (np. `done` jako pierwsze wywołanie na posortowanej tablicy nie może się zdarzyć, bo instancje nie są
  posortowane; ale ślad z samymi błędami tak): `trace_length: 0`, przebieg i tak ma `failed:*`, bo stan nie jest
  docelowy; odległości z `normalized` = 1,0 do niepustych wzorców.
- **Identyczne ślady dwóch algorytmów** na danej instancji (małe N): `ambiguous`, nie losowy wybór.
- **`step_limit` z `solved: true`:** strategia jak przy sukcesie (etykieta nie jest `failed`), a analiza i tak liczy
  to jako porażkę główną.
- **Tury z kilkoma wywołaniami:** bez zmiany tokenów; odsetek wywołań w takich turach jako miara dodatkowa.
- **Nazwy narzędzi z wariantu `para_names`** (`check_pair`, `exchange`, `move_disk`, `get_value`, `finish`): mapowanie
  na nazwy główne według `tools.tool_set` i `prompt.prompt_variant` przed budową tokenów.
- **Wyszukiwanie z odczytem poza przedziałem albo powtórzonym:** odczyt zbędny w miarach, sonda nadal liczy się do
  `dev_P`.
- **Brak instancji** dla `instance_id` z zapisu: błąd danych dla tego przebiegu.
- **Wersja schematu:** rekord `2.x` czytany najnowszym schematem 2.x; `schema_version` spoza 2.x odrzucany z błędem.

## 7. Wymagania protokołu

- [classification-rules.md](../protocol/classification-rules.md) §1-2: etykiety, przebieg nieudany, opis porażki,
  etykieta eksploracyjna.
- [classification-rules.md](../protocol/classification-rules.md) §3-5: tokeny, odległość, tryb prefiksowy, reguła
  etykiety i reguła hybrydy z czterema warunkami.
- [classification-rules.md](../protocol/classification-rules.md) §6 i §11-12: kalibracja, podział po instancjach,
  KPI 1 i KPI 2, wartości zamrożone.
- [classification-rules.md](../protocol/classification-rules.md) §7-9: Hanoi, wyszukiwanie, tury z kilkoma
  wywołaniami i odcinki przy błędzie wstrzykniętym.
- [classification-rules.md](../protocol/classification-rules.md) §10: kodowanie ręczne (`new`, `ambiguous`, próbka 10%).
- [prompts.md](../protocol/prompts.md) §6: co jest tekstem deklaracji.
- [fault-injection.md](../protocol/fault-injection.md) §7: miary pytania 5, które wymagają odcinków.
- [schemas/README.md](../../schemas/README.md), „Etykiety strategii”: zapis etykiety w polach i w `text`.

## 8. Testy akceptacyjne

Testy w `tests/python/analyzer/` (pytest, hypothesis, syrupy). Liczby niżej policzone skryptem na tych samych
danych. W testach z progami podaje się kalibrację testową: `tau_N = 0,30` dla każdego N, `lambda = 3`, `m_min = 2N`,
`tau_H = 0,30`, `tau_S = 0,10`, `delta = 0,02`. T5-T7 używają rejestru wzorców ograniczonego do wariantów
podstawowych `bubble_sort`, `insertion_sort` i `selection_sort` (jak w `schemas/check_examples.py`), żeby liczby nie
zależały od pozostałych wzorców.

- **T1 Bąbelkowe z przykładu.** Dane: `schemas/examples/run.bubble-sort-n5.jsonl` (`[4, 6, 3, 1, 2]`). Działanie:
  `analyze`. Oczekiwane: `trace_length: 18`, `compares: 10`, `swaps: 8`, `redundant_compares: 0`,
  `info_bound_compares: 7`, `inversions: 8`, `min_swaps: 2`; odległość do `bubble_sort` (wariant podstawowy) 0,
  do `insertion_sort` 8 edycji (0,4444), do `selection_sort` 13 edycji (0,7222, przy indeksach `(min, max)`);
  `label.text: known:bubble_sort`; `declaration.declared_algorithm: bubble_sort`, `matches_label: true`; wynik
  przechodzi `analyzer-result.v2.schema.json`.
- **T2 Tokeny bez błędów (przykład brzegowy).** Dane: `schemas/examples/run.edge-cases-n3.jsonl`. Oczekiwane: tokeny
  `[C(0,1), C(1,2), S(0,1), C(1,2)]` (bez `swap(0, 3)` z `out_of_range`, bez wywołania z błędem wstrzykniętym i bez
  pominiętego), `trace_length: 4`, `validation_errors: 1`; `label.text: failed:step_limit`; `exploratory_label: null`
  (4 operacje < `2N` = 6).
- **T3 Porównania zbędne.** Dane: `[1, 2, 3]`, tokeny `C(0,1)`, `C(1,2)`, `C(0,2)`, `C(0,1)`, `S(0,2)`, `C(0,2)`.
  Oczekiwane: `redundant_compares: 3` (przechodniość, powtórzenie i porównanie tych samych elementów po zamianie);
  wynik zgodny ze sprawdzeniem przez `networkx` na grafie relacji.
- **T4 Granice.** Dane: N = 5, 10, 20 i tablica `[3, 1, 2]`. Oczekiwane: `info_bound` 7, 22, 62; `inversions([3, 1, 2])`
  = 2, `min_swaps([3, 1, 2])` = 2.
- **T5 Strategia `new:info_first`.** Dane: `[4, 6, 3, 1, 2]`, ślad: wszystkie 10 par `C(i,j)` dla `i < j` w porządku
  leksykograficznym, potem `S(0,3)`, `S(1,4)` (stan końcowy `[1, 2, 3, 4, 6]`). Oczekiwane: odległości do wariantów
  podstawowych `selection_sort` 0,6667, `insertion_sort` 0,8333, `bubble_sort` 0,8889, więc żaden wzorzec nie spełnia
  `tau = 0,30`, hybryda odrzucona; 100% porównań przed pierwszą zamianą, 2 zamiany ≤ `N - c + 2` = 4 →
  `label.text: new:info_first`; `redundant_compares: 3`.
- **T6 Zakłócony ślad bąbelkowy.** Dane: ślad bąbelkowy `[4, 6, 3, 1, 2]` z dodatkowym `C(0,1)` po trzecim tokenie
  (19 tokenów). Oczekiwane: odległość do `bubble_sort` 1 edycja (0,0526), do `insertion_sort` 0,3684;
  `known:bubble_sort`; `redundant_compares: 1`.
- **T7 Niejednoznaczność.** Dane: `[2, 1]`, ślad `C(0,1)`, `S(0,1)`. Oczekiwane: bąbelkowe, przez wstawianie i przez
  wybór dają ten sam ślad (odległość 0) → `kind: ambiguous`, wszystkie trzy algorytmy w kolejności nazw (sekcja 10), `margin: 0.0`.
- **T8 Etykiety porażki.** Dane: przebiegi z `end_reason` kolejno `done_unsolved`, `step_limit` (`solved: false`),
  `too_many_errors`, `no_tool_call`, `context_exceeded`, `api_error`, `time_limit`, `cost_limit`, `interrupted`.
  Oczekiwane: `failed:wrong_done`, `failed:step_limit`, `failed:errors`, `failed:no_tool_call`, `failed:context`
  i czterokrotnie `failed:infra`. Wyszukiwanie (`target_present: true`, `answer: 7`): `done(-1)` →
  `failed:wrong_done:false_absent`, `done(3)` → `failed:wrong_done:wrong_index`; przy `target_present: false`
  `done(3)` → `failed:wrong_done:false_present`.
- **T9 Hanoi n = 3.** Dane: ruchy optymalne `(0,2), (0,1), (2,1), (0,2), (1,0), (1,2), (0,2)`; osobno ten sam ciąg
  poprzedzony parą `(0,1), (1,0)`. Oczekiwane: `optimal`, `moves: 7`, `optimal_moves: 7`; drugi: 9 ruchów,
  odległość 2/9 = 0,2222 → `optimal_detours` przy `tau_H = 0,30`, `other` przy `tau_H = 0,20`;
  `hanoi_distance_to_goal([[3], [2, 1], []])` = 4.
- **T10 Wyszukiwanie N = 15.** Dane: `[3, 7, 9, 14, 18, 22, 25, 31, 36, 40, 44, 47, 51, 55, 58]`; (a) `target: 44`,
  sondy 7, 11, 9, 10 i `done(10)`; (b) `target: 31`, sonda 7 i `done(7)`. Oczekiwane: (a) połowienie z dolnym
  środkiem przewiduje dokładnie te sondy (`dev = 0`) → `known:binary_search` (nazwa wzorca jak w
  [references.md](references.md)), `reads: 4` = `ceil(log2 16)`; (b) `too_short`.
- **T11 Deklaracja.** Dane: tekst pierwszej tury z `run.bubble-sort-n5.jsonl`; tekst pusty; tekst `I will compare
  every pair first and then place each number.` bez kodu ręcznego. Oczekiwane: `rule` → `bubble_sort`; pusty →
  `declared_algorithm: null`, `matches_label: null`; trzeci → `null` z regułą słów kluczowych (do kodowania ręcznego).
- **T12 Schemat.** Dane: wyniki T1-T11 i przykłady `schemas/examples/invalid/analyzer-result.*.json`. Oczekiwane:
  każdy wynik przechodzi `Draft202012Validator`; przykłady błędne (`hanoi-label-for-sort`, `known-without-algorithm`)
  są odrzucane przez ten sam kod zapisu (zapis nie może ich wyprodukować).
- **T13 Wzorce czyste rozpoznane.** Dane: przebiegi syntetyczne bez zakłóceń z [references.md](references.md) dla
  każdego algorytmu i wariantu, N = 5, 10, 20, po 5 instancji z ziarnem testu. Oczekiwane: `known` z tym samym
  algorytmem albo `ambiguous`, w którym ten algorytm jest; zero `new`.
- **T14 Hybryda syntetyczna.** Dane: N = 10, ślad przez wstawianie do punktu `0,5 L`, potem przez wybór od stanu w tym
  punkcie (generator z [references.md](references.md), ziarno testu). Oczekiwane: `hybrid:insertion_sort+selection_sort`,
  dwa `segments`, punkt podziału najwyżej N tokenów od prawdziwego.
- **T15 Powtarzalność.** Dane: ten sam katalog przebiegów i plik kalibracji dwa razy. Oczekiwane: identyczne bajty
  wyniku poza `created`.

## 9. Wiedza techniczna i źródła

- **Odległość edycyjna na tokenach:** `rapidfuzz.distance.Levenshtein.distance` przyjmuje sekwencje obiektów
  haszowalnych, ale bezpieczniej zakodować tokeny jako liczby całkowite (słownik token → int) i sprawdzić testem
  przy pierwszym kodzie; normalizacja `d / max(len)` jak `normalized_distance` RapidFuzz. Własne DP (20 linii,
  wzór w `schemas/check_examples.py`, funkcja `edit_distance`) jest wzorcem w testach. Pakiet `Levenshtein` ma
  licencję GPL: nie używać.
- **Tryb prefiksowy** liczy się jednym DP: ostatni wiersz macierzy edycji `t` względem `r` daje `d(t, r[:m])` dla
  wszystkich `m` naraz.
- **DTW nie** dla tokenów: dopasowuje jeden element do wielu bez kary, więc maskuje właśnie porównania zbędne.
- **Porównania zbędne:** przyrostowe domknięcie przechodnie na zbiorach (albo bitsetach) „na pewno większe”
  dla tożsamości elementów; mapa pozycja → tożsamość po każdej zamianie (wzór: `redundant_compares` w
  `schemas/check_examples.py`). `networkx` (`transitive_closure_dag`, `has_path`) tylko w testach.
- **Bąbelkowe a przez wstawianie** wykonują tyle samo zamian (liczba inwersji); różni je kolejność operacji, więc
  rozpoznanie opiera się na odległości ciągów, a nie licznikach.
- **Hanoi:** odległość do celu z dowolnego stanu: dla krążków od największego, jeśli krążek `k` nie stoi na celu,
  dodaj `2^(k-1)` i zmień cel mniejszych na trzeci palik; sprawdzenie BFS po `3^n` stanach (Romik,
  https://arxiv.org/abs/math/0310109).
- **Drugi głos (opcjonalnie):** `CountVectorizer` z własnym analizatorem n-gramów tokenów i kNN albo las losowy
  (scikit-learn); klasyfikator zamknięty nie ma odmowy, więc nie zastępuje reguły z progiem.
- **Podział walidacji po instancjach:** `StratifiedGroupKFold` albo własny podział po `instance_id`, żeby ta sama
  instancja nie była w kalibracji i teście.
- **Literatura:** rozpoznawanie sortowania ze śladu zamian (Perţicaş i in., PPIG 2017; Information and Software
  Technology 126, 2020) i z kodu (Taherkhani, Malmi, JEDM 2013) daje ponad 90% trafności na zamkniętym zbiorze klas;
  kategoria „nowa” i próg odmowy są dodatkiem tego badania. Klucze tych prac są w `paper/references.bib`.
- Źródła: https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html,
  https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html,
  https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html,
  https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_closure_dag.html.

## 10. Do ustalenia

- **Indeksy tokenów w przykładzie.** Protokół (§3) każe zapisywać tokeny z indeksami `(min, max)`. Przykład
  `schemas/examples/analyzer-result.bubble-sort-n5.json` i funkcja `selection_sort_tokens` w
  `schemas/check_examples.py` ich nie normalizują (`compare(j, m)` z `j > m`), więc podają dla `selection_sort`
  18 edycji (1,0) zamiast 13 (0,7222). Propozycja: za protokołem; zgłoszenie poprawki przykładu i skryptu (zmiana
  `schemas/` wymaga decyzji zespołu).
- **Tekst deklaracji.** Protokół (`prompts.md` §6): tekst wszystkich odpowiedzi do pierwszej z wywołaniem włącznie;
  `check_examples.py` porównuje z tekstem pierwszej tury. Propozycja: za protokołem, teksty łączone `"\n"`; w
  przykładach oba sposoby dają to samo.
- **Etykiety odcinków przy błędzie wstrzykniętym** (pytanie 5) nie mają pola w schemacie (`segments` jest dla hybryd,
  `metrics` przyjmuje tylko liczby). Propozycja: wersja mniejsza schematu (2.1) z opcjonalnym polem
  `fault_segments: {before, after}` z etykietą i odległością każdego odcinka; do tego czasu osobny plik obok wyniku.
- **Plik kalibracji.** Schemat go nie opisuje. Propozycja: `src/analyzer/calibration/<calibration_id>.json` z
  wartościami z §12 protokołu, datą i commitem; `calibration_id` w każdym wyniku; przed kalibracją `null`.
- **Plik kodów ręcznych.** Propozycja: `data/results/<series_id>.manual-codes.csv` z kolumnami `run_id`, `field`
  (`declared_algorithm` albo `strategy`), `value`, `coder` (`a`, `b`, `final`); analizator bierze `final`.
- **Reguła słów kluczowych deklaracji** (`labelled_by: rule`). Propozycja: lista wzorców słów na wzorzec (np.
  `bubble` → `bubble_sort`), stosowana tylko gdy pasuje dokładnie jeden wzorzec; reszta do kodowania ręcznego.
- **Remisy odległości.** Propozycja: kolejność po `normalized_distance`, potem nazwa wzorca, potem wariant (jak
  sortuje `check_examples.py`); w `ambiguous` przy remisie wielu algorytmów zapisuje się wszystkie o odległości
  w granicy `delta` od najbliższego (schemat dopuszcza więcej niż dwa).
- **Miara dla wrażliwości z turami z kilkoma wywołaniami.** Propozycja: dodatkowe pole `metrics.calls_in_parallel_turns`
  (z niego analiza wyników liczy próg „ponad połowa wywołań”, [analysis.md](analysis.md)).
