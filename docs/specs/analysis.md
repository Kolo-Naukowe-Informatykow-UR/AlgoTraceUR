# Specyfikacja: analiza wyników (`src/analysis/`)

Program w Pythonie 3.13, pakiet `algotrace_analysis` w workspace uv repozytorium. Status: kod jeszcze nie istnieje.
Czyta wiersze wyników (CSV od serii, [runner.md](runner.md)) i wyniki analizatora ([analyzer.md](analyzer.md)),
liczy statystykę z [analysis-plan.md](../protocol/analysis-plan.md) i zapisuje tabele oraz wykresy do tekstu badania
(`paper/`). Opis folderu: [src/analysis/README.md](../../src/analysis/README.md).

## 1. Cel

Z plików wyników pełnego badania (i pilotażu) policzyć odpowiedzi na pięć pytań badawczych dokładnie tak, jak opisuje
plan analizy, i wypisać je jako tabele (LaTeX i CSV) oraz wykresy (PDF i PNG), bez ręcznego przepisywania liczb do
tekstu. Każda liczba ma wyjść z przedziałem i liczebnością. Ta sama komenda na tych samych plikach i z tym samym
ziarnem daje te same bajty tabel (wykresy: ta sama treść, sekcja 9).

## 2. Granice

- Nie uruchamia modeli ani środowiska i nie zapisuje przebiegów: robi to seria ([runner.md](runner.md)).
- Nie klasyfikuje strategii i nie liczy odległości od wzorców: etykiety i miary bierze z wyniku analizatora
  ([analyzer.md](analyzer.md)). Wzorce odtwarza [references.md](references.md).
- Nie czyta zapisów przebiegów (`data/runs/`), tylko wiersze wyników i wyniki analizatora. Miary, których w tych
  dwóch źródłach nie ma (np. powrót po błędzie wstrzykniętym z [fault-injection.md](../protocol/fault-injection.md)
  §7), wymagają pól, które doda analizator (sekcja 10).
- Nie koduje ręcznie: etykiety ręczne (deklaracje, strategie `new`) przychodzą z pliku analizatora
  (`declaration.labelled_by`).
- Nie zmienia reguł protokołu: metody, progi i poprawki są z planu analizy; zmiana po zamrożeniu planu to odstępstwo
  zapisane w raporcie, a nie zmiana w kodzie.
- Nie składa tekstu: generuje pliki, które `paper/` włącza (`\input`, `\includegraphics`).

## 3. Wejścia i wyjścia

**Wejścia**

| Wejście | Schemat | Miejsce |
|---|---|---|
| wiersze wyników, jeden na zakończony przebieg (każdą próbę) | [results-row.v2](../../schemas/results-row.v2.schema.json) | `data/results/*.csv` (opis: [data/results/README.md](../../data/results/README.md)) |
| wynik analizatora, jeden obiekt JSON na linię | [analyzer-result.v2](../../schemas/analyzer-result.v2.schema.json) | plik `analysis_file` serii w `data/results/` (nazwa: sekcja 10) |

Format plików: [schemas/README.md](../../schemas/README.md), sekcje „Pliki” i „Identyfikatory i wersje”: CSV RFC 4180,
UTF-8, `true`/`false`, pusta komórka = `null`, czytać po nazwach kolumn. Klucz łączenia: `run_id`.

Pola wierszy wyników, które program czyta: `series_id`, `series`, `condition`, `fault_type`, `model_key`, `provider`,
`task`, `n`, `instance_id`, `repetition`, `run_attempt`, `prompt_variant`, `announcement_requested`, `strict_tools`,
`solved`, `done_called`, `end_reason`, `superseded_by`, `steps`, `executed_calls`, `compare_calls`, `swap_calls`,
`move_calls`, `read_calls`, `done_calls`, `validation_errors`, `injected_faults`, `fault_fired`, `parallel_turns`,
`turns`, `output_tokens`, `cost`, `currency`. Pola wyniku analizatora: `run_id`, `task`, `n`, `instance_id`,
`trace_length`, `metrics` (`compares`, `swaps`, `redundant_compares`, `info_bound_compares`, `inversions`,
`min_swaps`, `moves`, `optimal_moves`, `reads`, `validation_errors`, `recoveries_after_error`,
`longest_error_streak`), `label` (`text`, `kind`, `algorithms`, `variant`, `subtype`, `failure_detail`),
`exploratory_label`, `segments`, `declaration` (`declared_algorithm`, `labelled_by`, `matches_label`).

**Wyjścia** (wszystkie odtwarzalne z wejść; ścieżki to propozycja, katalog zmienia opcja `--out`)

| Wyjście | Format | Miejsce |
|---|---|---|
| tabele do tekstu | `.tex` (`booktabs`, bez `\begin{table}`: obiekt pływający i podpis dodaje tekst) | `paper/figures/tables/` |
| te same tabele jako dane | `.csv` (UTF-8, LF, kropka dziesiętna) | `data/results/analysis/` |
| wykresy | `.pdf` (do tekstu) i `.png` (podgląd) | `paper/figures/` |
| ślad przebiegu analizy | `analysis-manifest.json`: wersje bibliotek, ziarno, skróty plików wejściowych, liczba wierszy, ostrzeżenia | `data/results/analysis/` |

Układ `paper/`: [paper/README.md](../../paper/README.md) (`figures/` na rysunki; liczby w tekście pochodzą ze skryptów).

## 4. Interfejsy

Propozycja układu wewnątrz członka workspace (ostateczny układ ustala pierwszy kod,
[decyzja 0001](../decisions/0001-stos-technologiczny.md)). Typy: `pandas.DataFrame` (pandas 3), wyniki jako małe
`dataclass` z polami `estimate`, `lower`, `upper`, `n`.

```python
# io.py
def load_results(path: Path) -> pd.DataFrame        # CSV -> typy ze schematu
def load_analyzer(path: Path) -> pd.DataFrame       # JSONL -> kolumny płaskie: label_kind, label_text, ...
def validate_results(df: pd.DataFrame) -> list[Problem]
def join_runs(results: pd.DataFrame, analyzer: pd.DataFrame) -> pd.DataFrame  # po run_id
# prepare.py
def last_attempts(df) -> pd.DataFrame               # tylko wiersze z superseded_by == null
def add_outcomes(df) -> pd.DataFrame                # kolumny success_main, success_sens, missing, cluster, size_level
# stats.py
def wilson(k: int, n: int, alpha: float = 0.05) -> Interval
def pass_hat_k(c: int, n: int, k: int) -> float     # C(c,k)/C(n,k)
def holm(p: Sequence[float]) -> np.ndarray          # także benjamini_hochberg(p)
def cohens_h(p1: float, p2: float) -> float
def newcombe_paired(a: int, b: int, c: int, d: int, alpha: float = 0.05) -> Interval
def mcnemar_exact(b: int, c: int) -> float
def cluster_bootstrap_mean(values, clusters, *, n_boot: int = 2000, rng) -> Interval
def permutation_chi2(table_source, *, within: str, n_perm: int = 10_000, rng) -> PermResult
def cohen_kappa(x, y) -> float
def fit_gee(df) -> GeeFit                           # model główny, sekcja 5 krok 6
def pair_contrasts(fit, models) -> pd.DataFrame     # 21 kontrastów z p przed i po Holmie
# questions.py: q1_effectiveness(df), q2_algorithm(df), q3_declaration(df), q4_efficiency(df), q5_change(df)
# report.py
def write_table(df, name, out_dir, *, caption_key) -> None
def make_figures(tables: dict, out_dir: Path, *, textwidth_pt: float = 455.2) -> list[Path]
```

CLI (propozycja), z katalogu głównego repozytorium:

```
uv run --locked python -m algotrace_analysis validate --results data/results --analysis data/results
uv run --locked python -m algotrace_analysis run --results data/results --analysis data/results \
    --out paper/figures --seed 20261120
uv run --locked python -m algotrace_analysis tables | figures    # podzbiory kroku run
```

Kody wyjścia: 0 sukces; 1 błąd walidacji wejścia (wypisana lista `Problem`: plik, wiersz, kolumna, powód);
2 błąd użycia. Ostrzeżenia nie zmieniają kodu wyjścia, lecz trafiają do manifestu.

## 5. Zachowanie krok po kroku

1. **Wczytanie.** `load_results` czyta każdy `data/results/*.csv` po nazwach kolumn, rzutuje typy ze schematu
   (`solved`, `done_called`, `strict_tools`: boolean; `fault_fired`: boolean z brakiem; liczby całkowite z brakiem:
   `Int64`). `load_analyzer` czyta JSONL i spłaszcza `label`, `declaration`, `metrics`.
2. **Walidacja.** Kolumny dokładnie jak w `properties` schematu (brak lub nadmiar = błąd); wartości zamknięte z
   `common.v2` (`end_reason`, `condition`, `series`, `task`, `provider`, `prompt_variant`); `run_id` unikalny;
   `schema_version` zaczyna się od `2.`; spójność: `fault_fired` i `fault_type` puste dokładnie w `condition: main`;
   przy `end_reason: done_solved` pola `solved` i `done_called` równe `true`. Rekordy analizatora: `run_id` istnieje
   w wynikach, `task`, `n`, `instance_id` zgodne z wierszem. Naruszenie = `Problem`; błędy kończą program kodem 1.
3. **Ostatnia próba.** Zostają wiersze z pustym `superseded_by` ([schemas/README.md](../../schemas/README.md),
   „Identyfikatory i wersje”). Liczba odrzuconych prób idzie do raportu.
4. **Zmienne wyniku.** Dla każdego przebiegu ([analysis-plan.md](../protocol/analysis-plan.md) §1 i §8):
   `missing` = `end_reason` w {`api_error`, `time_limit`, `cost_limit`, `interrupted`}; `success_main` =
   `end_reason == done_solved`; `success_sens` = `solved`; wykluczenie z wrażliwości: `end_reason == context_exceeded`
   albo (`step_limit` i `solved == false`); we wrażliwości `missing` liczy się jako porażka. `cluster`: dla sortowania
   i wyszukiwania `(task, n, instance_id)`, dla Hanoi `(task, n)` (10 powtórzeń komórki to ta sama treść,
   [design.md](../protocol/design.md) §3). `size_level` 1, 2, 3 według rosnącego `n` w zadaniu. Seria główna:
   `series == full`, `condition == main`, `prompt_variant == main`; pilotaż i grupy `prompt_variant` osobno, opisowo.
5. **Pytanie 1 ([analysis-plan.md](../protocol/analysis-plan.md) §3).** Skuteczność z przedziałem Wilsona na
   konfigurację (model x zadanie x rozmiar, n = 10), model x zadanie (30) i model (90); `pass^k` dla k = 3 i 5 oraz
   `pass@k` na konfigurację; braki liczone osobno na komórkę.
6. **Model główny i testy potwierdzające (§2 i §3).** GEE (logit, dwumianowy, korelacja wymienna, klaster z kroku 4):
   `success_main ~ C(model_key) + C(task) * size_level`. H1: test Walda czynnika modelu (6 st. sw.); H2a-H2c: test
   Walda poziomu rozmiaru w każdym zadaniu; Holm w rodzinie (4 testy). H3: 21 kontrastów par modeli, Holm w rodzinie
   (21 testów); obok różnica proporcji w parach z przedziałem Newcombe'a i h Cohena. Sprawdzenie: regresja logistyczna
   z błędami klastrowymi. Separacja: sekcja 6.
7. **Pytanie 2 (§4).** Z udanych przebiegów sortowania (`success_main`): rozkład `label.text` na model x N z
   przedziałami Wilsona; stabilność (odsetek powtórzeń z etykietą najczęstszą); kategorie o łącznej liczebności poniżej
   5 łączone w „inne” przed testem. H4 i H5: statystyka chi-kwadrat tabeli i test permutacyjny (10 000 permutacji;
   H4: etykiety modeli permutowane wewnątrz instancji, H5: wartości N wewnątrz modelu), Holm w rodzinie (2 testy).
   KPI 2: odsetek `label.kind` w {`known`, `hybrid`} z Wilsonem, ogółem, na model i na N; próg 0,90 sprawdzany
   na liczbach całkowitych (`10 * k >= 9 * n`). Hanoi i wyszukiwanie: rozkłady z Wilsonem, testy tylko
   eksploracyjne (BH).
8. **Pytanie 3 (§5).** Przebiegi udane z niepustym `declaration.declared_algorithm`: zgodność surowa
   (`declaration.matches_label`), częściowa dla hybrydy (deklarowany = pierwszy w `label.algorithms`), kappa Cohena
   z przedziałem z bootstrapu klastrowego, macierz pomyłek deklaracja x wykonanie, zgodność w kategorii; ogółem i na
   model. Odsetek deklaracji pustych (`declared_algorithm` null) na model.
9. **Pytanie 4 (§6).** Z udanych przebiegów: sortowanie `metrics.compares / info_bound_compares`,
   `swaps / inversions`, `swaps / min_swaps`, `redundant_compares`; Hanoi `moves / optimal_moves`; wyszukiwanie
   `reads` wobec `ceil(log2(N + 1))`. Mediana i średnia na model x rozmiar; przedział średniej z bootstrapu klastrowego
   po klastrze (2000 prób, percentylowy, ziarno z `--seed`). Dla proporcji 0/n i n/n: Wilson, nie bootstrap.
10. **Pytanie 5 (§7).** H5: jak w kroku 7. H6a/H6b: z przebiegów `condition == faults` i `fault_fired == true` oraz
    ich par z serii głównej (ten sam `model_key` i `instance_id`; Hanoi: sekcja 10): tabela 2 x 2, McNemar dokładny,
    różnica proporcji z przedziałem Newcombe'a. H7a/H7b: tak samo na zmianie etykiety odcinka, gdy analizator poda ją
    w wyniku. Holm w rodzinie (4 testy każda). Wrażliwość H6: wszystkie przebiegi warunku.
11. **Wrażliwość (§8).** Powtórzenie kroków 5-6 z `success_sens` i wykluczeniami z kroku 4; GLMM z losowym wyrazem
    wolnym instancji zamiast GEE; GEE z korelacją niezależną; model bez jednego modelu naraz; pytanie 2 bez przebiegów,
    w których ponad połowa wywołań jest w turach z kilkoma wywołaniami (sekcja 10: skąd ta liczba).
12. **Wyjścia.** Tabele (sekcja 3) z każdą liczbą, jej przedziałem i liczebnością; wartości p przed i po poprawce.
    Wykresy: (a) skuteczność model x zadanie z przedziałami Wilsona, (b) skuteczność od rozmiaru na model,
    (c) skumulowany rozkład etykiet na model i N, (d) macierz pomyłek deklaracja x wykonanie, (e) porównania wobec
    granicy `ceil(log2 N!)` z krzywymi wzorcowymi (osie logarytmiczne), (f) skuteczność w parach: seria główna a błąd.
    Rozmiar z `\textwidth` (455,2 pt, do potwierdzenia po pierwszej kompilacji szablonu), czcionka szeryfowa, zapis
    PDF z ustalonymi metadanymi. Na końcu manifest.

## 6. Błędy i przypadki brzegowe

- **Pusta grupa** (n = 0): brak estymaty, komórka `NA` w CSV i „-” w LaTeX; test w tej grupie pominięty z notatką.
  Wilson dla n = 0 nie jest liczony (nie zwraca po cichu przedziału 0-1).
- **0/n i n/n:** Wilson; bootstrap nie (przedział zerowej szerokości). Wald nigdy; Clopper-Pearson tylko dla progów
  walidacji analizatora, która jest w programie [analyzer.md](analyzer.md), nie tutaj.
- **Braki danych:** `api_error` (po wyczerpaniu prób), `time_limit`, `cost_limit`, `interrupted`: pominięte w analizie
  głównej, liczba na komórkę w tabeli braków; we wrażliwości porażki ([analysis-plan.md](../protocol/analysis-plan.md)
  §8). Wiersz `api_error` z niepustym `superseded_by` nie jest brakiem: to zastąpiona próba.
- **Brak rekordu analizatora** dla przebiegu: ostrzeżenie, przebieg wypada z pytań 2-4 (nie z pytania 1).
  Rekord bez wiersza wyników: błąd walidacji.
- **Za mało danych:** kategoria poniżej 5 łączona w „inne” przed testem; po łączeniu mniej niż 2 kategorie lub
  2 wiersze tabeli = test pominięty (wartość `NA`, powód w manifeście); para McNemara bez par niezgodnych (b + c = 0)
  daje p = 1; mniej niż 30 klastrów w modelu: ostrzeżenie o zaniżonych błędach kanapkowych.
- **Separacja** (0% albo 100% skuteczności modelu w zadaniu, GEE nie zbiega albo ostrzega o zbieżności):
  regresja z karą Firtha plus przedziały z bootstrapu klastrowego po instancjach (2000 prób); decyzja zapisana
  w manifeście jako odstępstwo.
- **Puste kolumny:** `fault_fired` puste poza warunkiem `faults`; `cost`, `currency` i tokeny mogą być puste (model
  lokalny): sumy i średnie pomijają braki i podają liczbę uwzględnionych; waluty się nie miesza (różne `currency`
  w grupie = błąd).
- **Kilka serii w katalogu:** wiersze łączy się po `series_id`; ten sam `run_id` w dwóch plikach to błąd.
- **Etykiety `failed:*`** w analizie algorytmu nie występują (tylko przebiegi udane); `exploratory_label` tylko
  w tabelach oznaczonych jako eksploracyjne.

## 7. Wymagania protokołu

- [analysis-plan.md](../protocol/analysis-plan.md) §1: jednostka, definicje sukcesu głównego i wrażliwości, braki,
  klastry, przedział Wilsona (Wald nigdy), alfa 0,05 z Holmem w rodzinie i BH w eksploracji.
- [analysis-plan.md](../protocol/analysis-plan.md) §2: hipotezy H1-H7, ich testy i rodziny poprawek.
- [analysis-plan.md](../protocol/analysis-plan.md) §3: skuteczność, `pass^k`, GEE, Newcombe, h Cohena, separacja.
- [analysis-plan.md](../protocol/analysis-plan.md) §4-5: rozkład strategii, testy permutacyjne, KPI 2 i zgodność
  deklaracji (zgodność surowa zawsze obok kappy).
- [analysis-plan.md](../protocol/analysis-plan.md) §6-7: miary efektywności z bootstrapem klastrowym oraz zmiana
  strategii z N i po błędzie.
- [analysis-plan.md](../protocol/analysis-plan.md) §8-10: przebiegi szczególne i wrażliwość, moc po pilotażu, raport:
  liczba z przedziałem i liczebnością, odstępstwa w osobnej sekcji.
- [classification-rules.md](../protocol/classification-rules.md) §1-2 i §11: znaczenie etykiet i definicja KPI 2.
- [design.md](../protocol/design.md) §1-3: układ (7 modeli, 630 przebiegów serii głównej, 280 z błędami), instancje.
- [run-settings.md](../protocol/run-settings.md) §6 i §8: ponowienie po `api_error` i lista `end_reason`.
- [fault-injection.md](../protocol/fault-injection.md) §7: miary pytania 5 i para przebiegów.

## 8. Testy akceptacyjne

Testy w `tests/python/analysis/` ([tests/README.md](../../tests/README.md)), pytest; dane małe, wyniki policzone
ręcznie i sprawdzone skryptem (tolerancja 0,001 dla liczb rzeczywistych).

- **T1 Wilson, 7 z 10.** Dane: k = 7, n = 10. Działanie: `wilson(7, 10)`. Oczekiwane: estymata 0,700, przedział
  0,397-0,892; dla k = 10, n = 10: 0,722-1,000; dla k = 0, n = 10: 0,000-0,278.
- **T2 Wilson n = 1.** Dane: k = 1, n = 1 oraz k = 0, n = 1. Działanie: `wilson`. Oczekiwane: 0,206-1,000
  oraz 0,000-0,793; `wilson(0, 0)` zgłasza `ValueError` (grupę pustą obsługuje się wyżej jako `NA`).
- **T3 pass^k.** Dane: c = 7 sukcesów z n = 10. Działanie: `pass_hat_k(7, 10, 3)` i `(7, 10, 5)`. Oczekiwane:
  C(7,3)/C(10,3) = 35/120 = 0,292 oraz C(7,5)/C(10,5) = 21/252 = 0,083; `pass_hat_k(2, 10, 3)` = 0,000.
- **T4 Definicje sukcesu i wykluczenia.** Dane: 9 wierszy (ostatnie próby, jeden model, jedno zadanie), pary
  `end_reason`/`solved`: `done_solved`/true, `done_solved`/true, `done_unsolved`/false, `step_limit`/true,
  `step_limit`/false, `context_exceeded`/false, `api_error`/false, `time_limit`/false, `too_many_errors`/false.
  Działanie: `add_outcomes`, potem Wilson analizy głównej i wrażliwości. Oczekiwane: główna n = 7 (bez `api_error`
  i `time_limit`), 2 sukcesy: 0,286, przedział 0,082-0,641, braki 2. Wrażliwość n = 7 (bez wierszy 5 i 6), 3 sukcesy:
  0,429, przedział 0,158-0,750.
- **T5 Plik przykładowy.** Dane: `schemas/examples/results.example.csv`. Działanie: `load_results`, `validate_results`,
  `last_attempts`, `add_outcomes`. Oczekiwane: 3 wiersze wczytane, 0 problemów, 2 ostatnie próby (wiersz
  `bad99684456c9b54` odrzucony, bo ma `superseded_by` = `6e6327bf7da2953e`); `condition == main`: model `qwen3-8b`,
  sortowanie N = 5, 1 z 1 (`done_solved`), przedział 0,206-1,000; `condition == faults`: `claude-haiku-5-5`,
  sortowanie N = 3, 0 z 1 (`step_limit`, `solved` false, `fault_fired` true), przedział 0,000-0,793; braków 0.
- **T6 Połączenie z wynikiem analizatora.** Dane: `results.example.csv` i
  `schemas/examples/analyzer-result.bubble-sort-n5.json` (jeden rekord, `run_id` `2821d1679b18acbf`). Działanie:
  `join_runs`, krok 9. Oczekiwane: 1 przebieg połączony, 2 bez rekordu (ostrzeżenie); etykieta `known:bubble_sort`,
  KPI 2 = 1 z 1 (Wilson 0,206-1,000); `compares / info_bound_compares` = 10/7 = 1,429; `swaps / inversions` = 8/8 =
  1,000; `swaps / min_swaps` = 8/2 = 4,000; `trace_length` 18 = `executed_calls` 19 - `done_calls` 1;
  `matches_label` true.
- **T7 McNemar dokładny.** Dane: 10 par; przebieg z błędem sukces, para porażka: b = 1; przebieg z błędem porażka,
  para sukces: c = 6; obie strony sukces 2, obie porażka 1. Działanie: `mcnemar_exact(1, 6)`; różnica proporcji.
  Oczekiwane: p = 2 * (1 + 7) / 128 = 0,125; skuteczność z błędem 3/10, w parach 8/10, różnica -0,500;
  `mcnemar_exact(0, 6)` = 2/64 = 0,031; `mcnemar_exact(0, 0)` = 1,000.
- **T8 Poprawki Holma i BH.** Dane: p = [0,01; 0,04; 0,03]. Działanie: `holm(p)`, `benjamini_hochberg(p)`.
  Oczekiwane: Holm [0,03; 0,06; 0,06]; BH [0,03; 0,04; 0,04]; kolejność wejścia zachowana.
- **T9 h Cohena.** Dane: p1 = 0,8, p2 = 0,5. Działanie: `cohens_h`. Oczekiwane:
  2 arcsin(sqrt 0,8) - 2 arcsin(sqrt 0,5) = 0,644; `cohens_h(0.3, 0.8)` = -1,055; `cohens_h(0.5, 0.5)` = 0,000.
- **T10 Kappa i zgodność.** Dane: 10 przebiegów, deklaracja `[b,b,b,b,b,b,i,i,i,i]`, wykonanie
  `[b,b,b,b,b,i,i,i,i,b]` (b = `bubble_sort`, i = `insertion_sort`). Działanie: zgodność surowa, `cohen_kappa`,
  macierz pomyłek. Oczekiwane: zgodność 8/10 = 0,800 (Wilson 0,490-0,943); p_e = 0,36 + 0,16 = 0,52; kappa =
  (0,8 - 0,52) / 0,48 = 0,583; macierz (wiersze: deklaracja, kolumny: wykonanie) [[5, 1], [1, 3]].
- **T11 Chi-kwadrat i łączenie kategorii.** Dane: tabela model x etykieta [[8, 2], [2, 8]]; osobno łączne liczebności
  etykiet: `known:bubble_sort` 12, `known:insertion_sort` 4, `new:other` 1. Działanie: statystyka bez poprawki
  Yatesa; reguła łączenia. Oczekiwane: statystyka 7,200 (wszystkie oczekiwane 5, 4 x 9/5); po łączeniu kategorie
  `known:bubble_sort` (12) i „inne” (5); test permutacyjny z `rng` o ziarnie 1 powtórzony dwa razy daje identyczne p,
  a przy tabeli [[5, 5], [5, 5]] statystyka 0 i p = 1,000.
- **T12 Klaster Hanoi i bootstrap.** Dane: 10 wierszy `task == hanoi`, `n == 3`, różne `instance_id`, oraz 3 wiersze
  `sort`, `n == 5`, z różnymi `instance_id`. Działanie: `add_outcomes`; `cluster_bootstrap_mean` na wartościach
  [2, 4, 6, 8] w klastrach [a, a, b, b] z `rng` o ziarnie 7 dwukrotnie. Oczekiwane: Hanoi tworzy 1 klaster,
  sortowanie 3; dwa wywołania dają identyczny przedział, średnia 5,000; przy wartościach stałych [3, 3, 3, 3]
  przedział [3,000; 3,000].
- **T13 Wykresy deterministyczne.** Dane: tabela wejściowa z T4. Działanie: `make_figures` dwa razy do różnych
  katalogów. Oczekiwane: te same nazwy plików `.pdf` i `.png`; pliki PNG identyczne bajt po bajcie, a PDF po
  usunięciu pola daty utworzenia; szerokość rysunku 455,2 / 72,27 = 6,30 cala.
- **T14 Walidacja odrzuca błędne dane.** Dane: kopia `results.example.csv` z `end_reason` zmienionym na `finished`
  w wierszu 2 i z usuniętą kolumną `steps`. Działanie: `validate_results`, CLI `validate`. Oczekiwane: dwa `Problem`
  (wiersz 2, kolumna `end_reason`; brakująca kolumna `steps`), kod wyjścia 1.

## 9. Wiedza techniczna i źródła

**Biblioteki** (wersje z [decyzji 0001](../decisions/0001-stos-technologiczny.md), przypina je `uv.lock`):
`pandas` 3.1.1 z `pyarrow` 26.0.1, `statsmodels` 0.15.0, `scipy` 1.18.1, `matplotlib` 3.11.2; testy `pytest`
9.2.0, `hypothesis` 6.170.16, `syrupy` 7.0.2. Spoza tej listy plan analizy używa `scikit-learn` (`cohen_kappa_score`,
`confusion_matrix`); jest już w analizatorze, dopisanie go do `analysis` zmienia plik blokady (sekcja 10).
`seaborn` i `polars` nie są w decyzji dla analizy: nie używać (seaborn liczy przedziały bootstrapem po wierszach,
nie metodą protokołu).

**Pułapki**

- pandas 3: Copy-on-Write, kolumny tekstowe mają typ `str`; nie przypisywać łańcuchowo (`df[a][b] = x`), używać
  `.loc`. Pusta komórka liczby całkowitej to `Int64`/`NA`, nie `NaN`; `fault_fired` czytać jako `boolean`.
- Przedziały: `statsmodels.stats.proportion.proportion_confint(k, n, method="wilson")`; metoda zawsze jawna (domyślna
  to `normal`, czyli Wald). Clopper-Pearson to `method="beta"`.
- GEE: `statsmodels.formula.api.gee(..., groups=cluster, family=Binomial(), cov_struct=Exchangeable())`; błędy
  kanapkowe są zaniżone poniżej około 30 klastrów (tu 63). Test Walda czynnika: `wald_test_terms`; kontrasty par:
  `t_test` na wektorze uśredniającym wiersze macierzy planu po komórkach zadanie x rozmiar. Przy separacji GEE nie
  zbiega: łapać `ConvergenceWarning`. Zapis `cov_type="cluster"` w `logit(...).fit` sprawdzić na pierwszym modelu.
- Newcombe dla par (metoda 10 z pracy z 1998) nie ma gotowej funkcji: `confint_proportions_2indep` jest dla prób
  niezależnych. Własna funkcja: granice Wilsona obu proporcji i poprawka o korelację z tabeli 2 x 2; sprawdzić ze
  źródłem przed użyciem.
- Bootstrap: `scipy.stats.bootstrap` losuje obserwacje, nie klastry; bootstrap klastrowy (losowanie klastrów ze
  zwracaniem) pisać samemu na `numpy.random.default_rng(seed)`. `BCa` zwraca NaN dla danych stałych, stąd
  percentylowy i Wilson dla 0/n, n/n. Ziarno: jedno z `--seed`, osobny strumień na analizę (`rng.spawn`), zapisane
  w manifeście.
- Testy permutacyjne: stały `rng`; po permutacji liczyć statystykę dokładnie tak jak dla danych;
  p = (1 + liczba statystyk >= obserwowana) / (1 + 10 000). `scipy.stats.chi2_contingency(correction=False)` daje
  statystykę do kontroli.
- `DataFrame.to_latex` wymaga `jinja2`, której decyzja nie wymienia: tabele `.tex` pisać własną małą funkcją
  (`\toprule`, `\midrule`, `\bottomrule`, ucieczka znaków `# $ % & ~ _ ^ \ { }`).
- Wykresy deterministyczne: backend `pdf`/`Agg`; `savefig(..., metadata={"CreationDate": None})` dla PDF,
  `pdf.fonttype = 42`, ustalona czcionka (bez zależności od systemu); stały `figsize` z `textwidth_pt / 72.27`;
  punkty chmur `rasterized=True`. Przedziały rysować samemu (`ax.errorbar`) z własnych wartości Wilsona.
- Kolejność wierszy: sortować po `run_id` przed agregacją, żeby wynik nie zależał od kolejności plików.

**Źródła**

- Brown, Cai, DasGupta 2001 (przedziały dla proporcji): https://projecteuclid.org/euclid.ss/1009213286
- Przegląd przedziałów: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
- statsmodels, przedziały: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html
- statsmodels, GEE: https://www.statsmodels.org/stable/gee.html
- statsmodels, poprawki: https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
- statsmodels, `BinomialBayesMixedGLM`: https://www.statsmodels.org/stable/generated/statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM.html
- scipy, `bootstrap`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- scipy, `chi2_contingency`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html
- Metoda Holma: https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method
- Kappa Cohena: https://en.wikipedia.org/wiki/Cohen%27s_kappa
- Newcombe 1998, różnica proporcji sparowanych (Statistics in Medicine 17, 2635-2650): pobrać przez DOI przed kodem.
- pandas 3.0: https://pandas.pydata.org/docs/whatsnew/v3.0.0.html
- matplotlib, PGF i PDF: https://matplotlib.org/stable/users/explain/text/pgf.html

## 10. Do ustalenia

- **Nazwa pliku wyników analizatora.** Propozycja: `data/results/<series_id>.analysis.jsonl` (tak jak w
  `schemas/examples/experiment-config.faults-sort.json`); program bierze ścieżkę z opcji `--analysis`, domyślnie plik
  o tej nazwie obok CSV.
- **Para przebiegów w H6/H7 dla Hanoi.** Wszystkie 10 powtórzeń komórki ma tę samą treść. Propozycja: para po
  `(model_key, instance_id)` jak w sortowaniu (warunek z błędami idzie na tych samych instancjach co seria główna,
  [fault-injection.md](../protocol/fault-injection.md) §2), a klaster po komórce.
- **Miary pytania 5 spoza wiersza wyników** (powrót po błędzie wstrzykniętym, zmiana etykiety odcinka przed i po
  błędzie). Propozycja: analizator dopisuje je do `metrics` (schemat pozwala na dodatkowe pola liczbowe); do tego
  czasu H7 i opis powrotu pomijane z ostrzeżeniem.
- **Udział wywołań w turach z kilkoma wywołaniami** (wrażliwość, krok 11). Wiersz wyników ma tylko `parallel_turns`
  (liczbę tur), a nie liczbę wywołań w takich turach. Propozycja: analizator dopisuje `metrics.calls_in_parallel_turns`;
  do tego czasu przybliżenie `parallel_turns > turns / 2` z adnotacją w manifeście.
- **Kontrasty H3.** Propozycja: wektor uśredniający po 9 komórkach zadanie x rozmiar, jednakowa waga; zmiana wagi
  na liczebności wymaga zapisu w planie analizy.
- **Kara Firtha** nie jest w statsmodels. Propozycja: własna funkcja (Newton z karą Jeffreysa) sprawdzona na danych
  z pilotażu; w razie kłopotu tylko bootstrap klastrowy z odnotowaniem.
- **`scikit-learn` w `analysis`.** Propozycja: dopisać do członka workspace (jest już w analizatorze) i używać tylko
  `cohen_kappa_score` oraz `confusion_matrix`; alternatywa to własne kilkanaście linii. Zależność wymaga zgody
  człowieka ([AGENTS.md](../../AGENTS.md)).
- **`jinja2`** (wymaga jej `DataFrame.to_latex`). Propozycja: nie dodawać, pisać tabele własną funkcją (sekcja 9).
- **Ziarno domyślne.** Propozycja: 20261120; wartość zapisana w manifeście.
- **Miejsce tabel `.tex`.** Propozycja: `paper/figures/tables/`; jeśli szablon ma mieć osobny `paper/tables/`,
  zmienić domyślne `--out` bez zmiany reszty.
- **Moc po pilotażu** ([analysis-plan.md](../protocol/analysis-plan.md) §9): symulacja GEE. Propozycja: osobne
  polecenie `power` po pilotażu, poza pierwszą wersją.
