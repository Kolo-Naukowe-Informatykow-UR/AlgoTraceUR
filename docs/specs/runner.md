# Specyfikacja: seria przebiegów (`src/runner/`)

Aplikacja konsolowa C# / .NET 10 `AlgoTrace.Runner`. Status: kodu jeszcze nie ma. Seria czyta konfigurację z
`experiments/`, planuje przebiegi, tworzy adapter ([adapters.md](adapters.md)) i wywołuje pętlę środowiska
([environment.md](environment.md)), a z zapisów przebiegów buduje wiersze CSV dla analizy ([analysis.md](analysis.md)).
Do przejęcia środowiska (po 23.12.2026) działa atrapa `RunLoop`. Folder: [src/runner/README.md](../../src/runner/README.md).

## 1. Cel

Wykonać serię bez pracy ręcznej: z konfiguracji (albo kilku konfiguracji tego samego etapu) wyznaczyć przebiegi
(modele x instancje x powtórzenia), uruchomić je w kolejności z ziarna, pilnować budżetu, tempa i kolejek dostawców,
ponawiać przebiegi po `api_error`, wznowić przerwaną serię bez powtarzania gotowych przebiegów i zapisać wyniki w CSV.
Każdy wiersz powstaje z zapisu przebiegu.

## 2. Granice

- Nie wykonuje przebiegu i nie tworzy zdarzeń `model_turn`, `tool_call`: to środowisko. Seria tylko zapisuje linie,
  które dostaje przez `IRunEventSink`.
- Nie buduje żądań HTTP i nie ponawia pojedynczych zapytań: to adaptery. Nie generuje instancji (plik z `instances/`
  jest źródłem prawdy, [environment.md](environment.md) sekcja 10) i nie klasyfikuje strategii ([analyzer.md](analyzer.md)).
- Agent kodujący nie uruchamia `run` na płatnym API sam ([AGENTS.md](../../AGENTS.md)).

## 3. Wejścia i wyjścia

| Kierunek | Co | Format | Miejsce |
|---|---|---|---|
| wejście | konfiguracja | [experiment-config.v2.schema.json](../../schemas/experiment-config.v2.schema.json) | `experiments/<series_id>.json` |
| wejście | instancje | [instance.v2.schema.json](../../schemas/instance.v2.schema.json), JSONL | `tasks[].instances_file`, np. `instances/full.jsonl` |
| wejście | teksty dla modeli | UTF-8, LF | `prompt.system_file`, `task_files`, `reminder_file` (`experiments/prompts/<prompt_id>/`) |
| wejście | klucze API | zmienne środowiskowe o nazwach z `models[].api.api_key_env` | proces, nigdy plik |
| wejście | granice dostawców (propozycja) | `{"<provider>": {"max_concurrent_runs": 1, "requests_per_minute": 30}}` | `experiments/provider-limits.json` |
| wyjście | zapis przebiegu | [run-event.v2.schema.json](../../schemas/run-event.v2.schema.json) | `<runs_dir>/<run_id>.jsonl` (w trakcie `.jsonl.partial`) |
| wyjście | zapis surowy (`save_raw`) | format adapterów | `<runs_dir>/<run_id>.raw.jsonl`, pisze adapter |
| wyjście | wyniki | [results-row.v2.schema.json](../../schemas/results-row.v2.schema.json), CSV | `output.results_csv` |
| wyjście | przebiegi przerwane | kopie do diagnozy | `<runs_dir>/interrupted/` |

Stan wznowienia to zawartość `runs_dir` (sekcja 5, krok 3), bez osobnego pliku; wyjątek to blokada
`<runs_dir>/.runner.lock` (`FileShare.None`). `analysis_file` należy do analizatora.

## 4. Interfejsy

Propozycja; nazwy typów zmienia kod, pola zapisu i wartości nie. Polecenia: `dotnet run --project src/runner --
<polecenie> <konfiguracja>... [opcje]`.

| Polecenie | Działanie |
|---|---|
| `validate` | krok 1 (bez sieci i kluczy; `--check-keys` dodaje zmienne) |
| `plan` | walidacja i lista przebiegów w kolejności kolejek: `run_id`, dostawca, model, instancja, próba, stan (`done`, `pending`, `interrupted`), suma górnych kosztów |
| `run` | walidacja, klucze, plan, potwierdzenie (`--yes` pomija; bez niego trzeba wpisać `series_id`, gdy model ma cenę), wykonanie, CSV |
| `rows` | odbudowuje `results_csv` z zapisów, bez modeli |

Opcje: `--order-seed <ulong>`, `--provider-limits <plik>`, `--yes`, `--max-runs <n>`. Kilka konfiguracji jednego etapu
(np. `full-main`, `full-faults-one-off`) daje wspólną kolejkę dostawcy ([design.md](../protocol/design.md) §4).
Kody wyjścia: 0 komplet, 1 błąd konfiguracji lub środowiska, 2 budżet, 3 kolejka dostawcy zatrzymana, 130 przerwanie.

```csharp
namespace AlgoTrace.Runner;

public sealed record PlannedRun(string RunId, int RunAttempt, ConfigRef Config, ModelEntry Model,
    InstanceRecord Instance, int Repetition, decimal UpperCost);
public sealed record SeriesPlan(IReadOnlyList<PlannedRun> Cells,   // próba 1 każdej komórki, kolejność kanoniczna
    IReadOnlyDictionary<string, IReadOnlyList<PlannedRun>> ProviderQueues);

public static class RunIds   // RFC 8785; ta sama reguła co make_run_id w schemas/check_examples.py
{
    public static string ConfigSha256(JsonElement config);
    public static string RunId(string seriesId, string configSha256, string modelKey, string instanceId,
                               int repetition, int runAttempt);                     // 16 znaków hex
}
public interface IOrderShuffler { IReadOnlyList<T> Shuffle<T>(IReadOnlyList<T> items, ulong orderSeed); }  // SplitMix64

public sealed class BudgetGuard        // jeden na konfigurację z budget != null
{
    public BudgetGuard(decimal budget, decimal upperCostPerRun, decimal alreadySpent);
    public bool TryReserve(string runId);                 // przed startem
    public ICostGuard ForRun(string runId);               // StopAfterTurn(runCostSoFar) dla środowiska
    public void Commit(string runId, decimal finalCost);
}
public sealed class ProviderQueue      // kolejka, SemaphoreSlim, pacer, zatrzymanie
{
    public Task RunAsync(Func<PlannedRun, CancellationToken, Task<RunResult>> execute, CancellationToken ct);
    public void Stop(string reason);                      // provider_funds
    public void PauseUntil(DateTimeOffset utc);           // daily_limit
}
public interface IRequestPacer { ValueTask WaitAsync(CancellationToken ct); }   // TokenBucketRateLimiter albo atrapa
public sealed class PacedChatClient : DelegatingChatClient   // pacer przed każdym zapytaniem
{ public string? LastErrorKind { get; } }                    // ostatnie algotrace.error_kind
public static class ResultsWriter { public static CsvRow Derive(IReadOnlyList<JsonObject> events); }  // jak derive_row
```

Seria wywołuje publiczne API środowiska (`RunLoop`, `RunSpec`, `IRunEventSink`, `ICostGuard`, `IClock`) i
`AdapterFactory.Create(ModelEntry, AdapterRetryOptions, AdapterRunContext)` (interpretacja decyzji
[0001](../decisions/0001-stos-technologiczny.md) z [environment.md](environment.md) sekcja 10).

**`run_id`:** pierwsze 16 znaków hex SHA-256 kanonicznego JSON (RFC 8785) obiektu `{series_id, config_sha256,
model_key, instance_id, repetition, run_attempt}` ([schemas/README.md](../../schemas/README.md), „Identyfikatory i
wersje”). `config_sha256` to SHA-256 kanonicznego JSON całego pliku konfiguracji, z `description` i `created`.

## 5. Zachowanie krok po kroku

1. **Walidacja (przed przebiegami).** (a) JSON: UTF-8 bez BOM, LF, bez zdublowanych kluczy. (b) Schemat konfiguracji
   (`JsonSchema.Net`, `format` sprawdzany); komunikat ma miejsce i regułę, nigdy wartości z `api_key*`. (c) Spójność:
   nazwa pliku = `series_id`; `model_key`, `task`, `n` bez powtórzeń; wpis w `prompt.task_files` dla każdego zadania;
   pliki istnieją; `api_key_env` niepuste poza `ollama` i `openai_compatible`; `local` niepuste dla
   `ollama`; waluta `budget` = waluta cen; `budget` niepuste wymaga niepustego `limits.max_cost_per_run`. (d) Instancje:
   schemat, `idx` = numer linii od 0, `series` zgodne, kolejność zadanie, `n`, `rep`; **niepuste
   `checks.failed` w którymkolwiek wierszu zatrzymuje serię** ([design.md](../protocol/design.md) §3); każdy wpis
   `sizes` ma instancję; w `faults` każda wybrana instancja ma `fault_schedule`. (e) Wypisać wszystkie błędy, kod 1.
2. **Plan.** Wiersze instancji z `task` i `n` z `sizes`, w kolejności pliku. Komórka = (model, instancja,
   `repetition` 1..`repetitions`), próba 1; policzyć `config_sha256` i `run_id`. Kolejka dostawcy = komórki tego
   dostawcy w kolejności kanonicznej (konfiguracje w kolejności argumentów) przemieszane przez `IOrderShuffler` z
   `order_seed` (SplitMix64, Fisher-Yates od końca, `j = NextU64() % (i + 1)`), to samo ziarno dla każdego dostawcy.
   Powtórka po `api_error` idzie na koniec kolejki.
3. **Stan komórek (wznowienie).** Dla prób 1, 2, ...: (i) `<run_id>.jsonl` z ostatnią linią `run_end` = gotowy, z
   wyjątkiem `end_reason: interrupted` (idź do iv); (ii) gotowy `api_error` z niepustym `superseded_by` = czeka
   próba z tego `run_id`; (iii) każdy inny gotowy, także `api_error` z `superseded_by: null`, zamyka komórkę;
   (iv) `.jsonl.partial` albo plik bez `run_end` to przebieg przerwany ([environment.md](environment.md) sekcja 6):
   **nie jest nową próbą** (`run_attempt` liczy tylko ponowienia po `api_error`), plik z `.raw.jsonl` trafia do
   `interrupted/<run_id>.<UTC>.jsonl`, przebieg rusza od nowa pod tym samym `run_id`. Ucięta ostatnia linia jest pomijana.
4. **Wydane.** `alreadySpent` = suma po plikach komórek (także `interrupted/`): `run_end.cost`, bez niego suma `cost`
   zdarzeń `model_turn`.
5. **Budżet przed startem** ([run-settings.md](../protocol/run-settings.md) §7). `górny_koszt` =
   `limits.max_cost_per_run`. `TryReserve` (pod blokadą) pozwala startować, gdy `wydane + (w_locie + 1) * górny_koszt
   <= budżet`, gdzie `wydane` to koszt przebiegów zakończonych, a przebieg w locie rezerwuje górny koszt (limit
   miękki). Odmowa zatrzymuje serię, kod 2.
   `budget: null` wyłącza strażnika.
6. **Budżet po turze.** `StopAfterTurn(runCostSoFar)` = `true`, gdy `wydane_zakończone + koszty przebiegów w locie
   (ten: runCostSoFar) >= budżet` albo `runCostSoFar >= 1,5 * max_cost_per_run` (null wyłącza ten warunek);
   środowisko kończy `cost_limit`. Brak ceny = koszt 0. `Commit` po każdym przebiegu (także błędnym i przerwanym).
7. **Przebieg** (`ProviderQueue`, do `max_concurrent_runs` naraz). (a) `RunSpec`: `Header` (pola z komentarza w
   [environment.md](environment.md) sekcja 4; `model_requested` = `model`; `software`: `git_commit`, `git_dirty`,
   `runtime`, `os`, `lock_sha256`, `local_server`); `Instance`; `Prompt` z plików;
   `ToolSet`; `CompareResultFormat`; `Limits` (`max_steps` z `n`, `limits`, `timeouts`); `Faults` = `faults` +
   `fault_schedule` instancji (w `main` `null`); `ContextBudgetTokens` = `local.context_length -
   settings.max_output_tokens` dla modelu lokalnego (20480 - 2048 = 18432), inaczej `null`; `RetryRunId` z kroku 8.
   (b) `AdapterFactory.Create(model, new AdapterRetryOptions(max_api_retries, initial_backoff_s, max_backoff_s), new
   AdapterRunContext(run_id, rawPath albo null, instance.seed))`. (c) `Header.settings_sent` = `SettingsSent`,
   `strict_tools` = `StrictToolsSent`; model lokalny: `ProbeAsync` daje `software.local_server`, digest różny od
   `model_version` odrzuca przebieg. (d) Klient w `PacedChatClient`. (e) Sink pisze `.jsonl.partial` (linia + LF +
   `Flush`), po `RunAsync` `fsync` i `File.Move` na `<run_id>.jsonl`. (f) `RunLoop.RunAsync`.
8. **Ponowienie** ([run-settings.md](../protocol/run-settings.md) §6). `zużyte_przed(a)` = liczba wcześniejszych prób
   komórki zakończonych `api_error` innym niż `daily_limit`. `RetryRunId(a)` = `run_id` próby `a + 1`, gdy
   `zużyte_przed(a) < max_run_retries`, inaczej `null`. Po `api_error` z `error.type` ≠ `daily_limit` i
   `LastErrorKind` ≠ `provider_funds`: gdy `RetryRunId` niepuste, próba `a + 1` idzie na koniec kolejki, inaczej komórka
   zamknięta (brak danych). Po `daily_limit`: próba `a + 1` bez zużycia, `PauseUntil(następna 00:00 UTC)` (inni
   dostawcy pracują).
9. **`provider_funds`:** kolejka dostawcy staje (nowe nie startują, trwające kończą się), nieudany przebieg ma
   `superseded_by: null` i zostaje w danych; kod 3 po zakończeniu pozostałych kolejek.
10. **CSV.** Po każdym zamkniętym przebiegu: wiersz do pamięci, cały plik do pliku tymczasowego w tym samym folderze,
    `fsync`, `File.Move(overwrite: true)`. Pola jak `derive_row` w [check_examples.py](../../schemas/check_examples.py)
    (m.in. `model_returned` z ostatniego `model_turn`, `fault_fired` = `injected_faults > 0` tylko w `faults`,
    tokeny z `usage_total`, `cost` z `run_end.cost`). Format: [schemas/README.md](../../schemas/README.md),
    „Pliki”. Wiersz dla każdej próby, nie dla `interrupted`; kolejność: komórki kanonicznie, potem próby.
11. **Koniec.** Ostatni zapis CSV i raport (gotowe, `api_error`, koszt).

## 6. Błędy i przypadki brzegowe

- **Ctrl+C:** pierwszy sygnał anuluje token; środowisko zapisuje `run_end` `interrupted`, seria przenosi plik do
  `interrupted/` (bez wiersza), czeka na resztę, kod 130. Drugi sygnał kończy proces, zostawia `.partial`.
- **Konfiguracja z kluczem** (`api_key`, sekret zamiast nazwy): odrzucona przez schemat, bez wartości w komunikacie.
- **Brak klucza** (zmienna z `api_key_env` pusta) u modelu z przebiegami do wykonania: wypisać wszystkie nazwy, kod 1,
  zero przebiegów. Wartości zmiennych nie trafiają do komunikatów.
- **Plik instancji z niepustym `checks.failed`:** seria nie startuje, lista `instance_id` i sprawdzeń.
- **Zmieniona konfiguracja:** każda zmiana pliku (także `description`) zmienia `config_sha256`, więc `run_id`; stare
  zapisy nie są wznawiane ani nadpisywane, `plan` pokazuje wszystko jako `pending`, z ostrzeżeniem o zapisach z innym
  skrótem w `runs_dir`.
- **Drugi proces na `runs_dir`:** brak blokady, kod 1.

## 7. Wymagania protokołu

- [run-settings.md](../protocol/run-settings.md) §6: powtórka przebiegu po `api_error` (najwyżej 2, nowy `run_id`,
  `run_attempt`, `superseded_by`), `daily_limit` bez zużycia, brak środków kończy dostawcę.
- [run-settings.md](../protocol/run-settings.md) §7: strażnik budżetu: przed startem, po odpowiedzi, współbieżność.
- [run-settings.md](../protocol/run-settings.md) §8-9: `end_reason` z listy zamkniętej; konfiguracja i jej kopia.
- [design.md](../protocol/design.md) §3: plik instancji źródłem prawdy, `checks` zatrzymują serię.
- [design.md](../protocol/design.md) §4: kolejka na dostawcę, permutacja z `order_seed`, powtórka na końcu.
- [fault-injection.md](../protocol/fault-injection.md) §2-3: harmonogram z instancji, typ i długość z konfiguracji.
- [schemas/README.md](../../schemas/README.md): `config_sha256`, `run_id`, pliki (UTF-8, LF, UTC), wiersz tylko z zapisu.

## 8. Testy akceptacyjne

Testy w `tests/dotnet/AlgoTrace.Runner.Tests/` (xUnit v3), bez sieci: fałszywy `IChatClient`, atrapa `RunLoop`
odtwarzająca zapisy z `schemas/examples/`, atrapa pacera, stały zegar, katalog tymczasowy z kopią przykładów i
pustymi plikami w `experiments/prompts/p1/`. Wartości policzone przez `config_sha256`, `make_run_id` i
`derive_row` z `schemas/check_examples.py`.

- **T1 Skrót konfiguracji.** Dane: `experiment-config.pilot-sort.json`, `experiment-config.faults-sort.json`.
  Działanie: `RunIds.ConfigSha256`. Oczekiwane: `4795084a6fb8174236733e1a6e649337b0a98ce875bd3fa55592fa261219829a` i
  `a75735d18158450e0738679f1b7cce46f68320e4d477bb986640f5b3f50eed6b` (jak `config_sha256` w `results.example.csv`).
- **T2 RFC 8785.** Dane: pilot-sort. Działanie: (a) `2.0` zapisane jako `2`, inna kolejność kluczy, spacje; (b)
  `max_cost_per_run` = `2.5`; (c) `description` + spacja. Oczekiwane: (a) skrót z T1; (b)
  `19d9c20d6858e824fe86e48fdd302448649238870e9a0eae322e86295141f3a6`, `run_id` pierwszej komórki `ff6056100b4a1d7b`;
  (c) `273e639a088e45de073551ae72bb4dca1fa50d940bbd4a750e840e2bde859a16`, `run_id` `b038ef480250199e`.
- **T3 `run_id` i plan.** Dane: faults-sort (`claude-haiku-5-5`, `sort-n3-example`, `repetition` 1); pilot-sort.
  Działanie: `RunIds.RunId` dla prób 1-4, `plan` pilot-sort. Oczekiwane: `bad99684456c9b54`, `6e6327bf7da2953e`,
  `1ea8b8b75b3e49b3`, `cfb62beb46a07e5a`; pilot-sort ma 2 przebiegi (`sort-n3-example` nie ma w `sizes`):
  `qwen3-8b` `2821d1679b18acbf`, `claude-haiku-5-5` `aaa9069f9ec4b9ec`, po jednym w kolejkach `ollama` i `anthropic`.
- **T4 Odrzucone konfiguracje.** Dane: 6 plików `schemas/examples/invalid/experiment-config.*.json`. Działanie:
  `validate`. Oczekiwane: kod 1, zero klientów i plików w `runs_dir`; miejsce błędu: `api-key-in-file`
  `/models/1/api` (nadmiarowe `api_key`), `full-with-pilot-variant` `/prompt/prompt_variant`,
  `key-instead-of-env-name` `/models/1/api/api_key_env`, `main-with-faults` `/faults`,
  `no-announcement-with-request` `/prompt/announcement_requested`, `one-off-length-3` `/faults`; wyjście nie zawiera
  `do-not-put-keys-here` ani `my-secret-key-value`.
- **T5 Kolejność z `order_seed`.** Dane: SplitMix64 z ziarnem 0 daje `0xe220a8397b1dcdaf`, `0x6e789e6aa1b965f4`,
  `0x6c45d188009454f`. Działanie: `Shuffle([1..5])` z ziarnem 20261120 i 20261121, każde dwa razy. Oczekiwane:
  `[4, 3, 1, 2, 5]` i `[1, 2, 3, 4, 5]`, powtórzenie identyczne; `[1..10]` z 20261120: `[4, 2, 9, 1, 7, 8, 6, 3, 10, 5]`;
  domyślne ziarno `example-pilot-sort` (8 pierwszych bajtów SHA-256 `series_id`, big-endian) = `8650289694782333944`.
- **T6 Wznowienie po 3 z 5.** Dane: pilot-sort, w którym zmienione są tylko `series_id` (`t-resume`), `budget`
  (`null`), `models` (sam wpis `qwen3-8b`) i `tasks[0].sizes` (`[{"n": 5, "max_steps": 30}]`); reszta pliku bez zmian.
  `config_sha256` `3abe1d9d0bcff8f7277aef4179f75d84e8a6e99131a571c111cabfd40d5b433b`. Plik `instances_file` w kopii
  zastąpiony 5 instancjami sortowania `n` 5 o `instance_id` `sort-n5-r0`..`sort-n5-r4`; `run_id` r0..r4:
  `124d725782558691`, `8d086f53909243c8`, `ffa026d0c765c12a`, `eeb1e04c38416430`, `1dc7e33d9db1d8d0`; gotowe
  `.jsonl` (z `run_end`) dla r0-r2. Działanie: `run --yes`. Oczekiwane: adapter tworzony 2 razy (r3, r4), pliki r0-r2
  bez zmian, CSV 5 wierszy. Wariant: dodatkowo `eeb1e04c38416430.jsonl.partial` → plik do `interrupted/`, r3 rusza
  pod tym samym `run_id` (`run_attempt` 1, nie 2), bez wiersza dla przerwanego.
- **T7 Ponowienie po `api_error`.** Dane: faults-sort; klient: próba 1 `api_error` `overloaded_error`, próba 2 jak
  `run.edge-cases-n3.jsonl`. Działanie: `run --yes`. Oczekiwane: `RetryRunId` próby 1 = `6e6327bf7da2953e`, próby 2 =
  `1ea8b8b75b3e49b3`; `bad99684456c9b54.jsonl` ma `superseded_by` `6e6327bf7da2953e`; CSV 2 wiersze jak w
  `results.example.csv`. Wariant: próba 1 `daily_limit`, próby 2-4 `api_error` → 4 pliki (id z T3), `RetryRunId`
  próby 4 = `null`, brak próby 5, `PauseUntil` raz.
- **T8 `provider_funds`.** Dane: 3 przebiegi `anthropic`, 2 `ollama`; pierwszy `anthropic` kończy `api_error` z
  `algotrace.error_kind` `provider_funds`. Oczekiwane: pozostałe dwa `anthropic` nie startują, oba `ollama` się
  kończą, `superseded_by: null`, kod 3, CSV 3 wiersze.
- **T9 Budżet.** Dane: budżet 20,0 USD, `max_cost_per_run` 2,0 (pilot-sort). Działanie: `TryReserve`, `StopAfterTurn`.
  Oczekiwane: wydane 17,5, 0 w locie → start (19,5); 18,5 → odmowa (20,5); 15,9 i 1 w locie → start (15,9 + 2 * 2,0
  = 19,9); 16,1 i 1 w locie → odmowa (20,1); po turze: koszt przebiegu 2,99 →
  `false`, 3,00 → `true` (`1,5 * 2,0`); wydane 19,0 i koszt przebiegu 1,0 → `true`. `Commit(0.00345)` zwiększa
  wydane o dokładnie 0,00345 (`decimal`).
- **T10 Wiersz CSV z zapisu.** Dane: `run.bubble-sort-n5.jsonl`, `run.api-error-n3.jsonl`, `run.edge-cases-n3.jsonl`.
  Działanie: `ResultsWriter.Derive`, zapis CSV. Oczekiwane: wiersze bajt w bajt równe wierszom `results.example.csv`;
  bubble-sort: `solved` true, `steps` 19, `input_tokens` 29545, `output_tokens` 586, `duration_ms` 17871, `cost` i
  `fault_fired` puste; `bad99684456c9b54`: `end_reason` `api_error`, `superseded_by` `6e6327bf7da2953e`, `cost`
  `0.00345`, `fault_fired` `false`.
- **T11 Przerwanie.** Dane: 2 przebiegi, token anulowany w trakcie pierwszego. Oczekiwane: `run_end` `interrupted`,
  plik w `interrupted/`, brak wiersza, kod 130, drugi przebieg nie startuje.
- **T12 Brak klucza i `checks.failed`.** Dane: (a) pilot-sort, `ANTHROPIC_API_KEY` nieustawiona; (b) wiersz instancji z
  `"checks": {"checked": ["permutation", "not_sorted"], "failed": ["not_sorted"]}`. Oczekiwane: (a) kod 1, komunikat
  z `ANTHROPIC_API_KEY`, zero przebiegów także dla `ollama`; (b) kod 1, komunikat z `instance_id` i `not_sorted`.

## 9. Wiedza techniczna i źródła

- **RFC 8785 w .NET.** `System.Text.Json` nie ma trybu kanonicznego, więc własny pisarz: klucze sortowane
  `string.CompareOrdinal` (jednostki UTF-16, nie porównanie kulturowe), bez spacji; ucieczki tylko `"`, `\\`, `\b \t
  \n \f \r` i `\u00xx` (małe litery) dla pozostałych znaków < 0x20, bez ucieczki znaków nie-ASCII i `/` (domyślny
  `JavaScriptEncoder` ucieka więcej). Liczby w postaci ECMAScript: `2.0` daje `2`, `1e21` daje `1e+21`; cyfry z
  `double.ToString("R", InvariantCulture)` przeformatować jak `_jcs_number` w skrypcie. Skrót z drzewa JSON, nie z tekstu.
- **Koszty:** `GetDecimal()` i `InvariantCulture`; `double` daje `1E-05` i błędy sum.
- **Tempo i równoległość.** `System.Threading.RateLimiting.TokenBucketRateLimiter`: `TokenLimit = 1`,
  `TokensPerPeriod = 1`, `ReplenishmentPeriod = 60 s / requests_per_minute`, `AutoReplenishment = true`, duży
  `QueueLimit`; `await limiter.AcquireAsync(1, ct)` i `lease.IsAcquired`. Równoległość przebiegów to osobny
  ogranicznik (`SemaphoreSlim` albo `Channel<T>`). Ponowienia adaptera omijają pacer.
- **Zapis atomowy:** plik tymczasowy w tym samym folderze, `Flush(true)`, `File.Move(..., overwrite: true)`; na
  Windows ponowić zmianę nazwy, gdy plik trzyma antywirus. Czasy z `IClock`, UTC, `yyyy-MM-ddTHH:mm:ss.fffZ`.
- **`JsonSchema.Net`:** schematy rejestrować po `$id`, włączyć asercję `format`. Zdublowane klucze `System.Text.Json`
  domyślnie przyjmuje (sprawdzić `JsonDocumentOptions.AllowDuplicateProperties` w .NET 10).
- Źródła: https://www.rfc-editor.org/rfc/rfc8785, https://www.rfc-editor.org/rfc/rfc4180,
  https://prng.di.unimi.it/splitmix64.c (zamiast `System.Random`, którego algorytm może się zmienić),
  https://learn.microsoft.com/en-us/dotnet/api/system.threading.ratelimiting.tokenbucketratelimiter,
  https://docs.json-everything.net/schema/basics/, https://learn.microsoft.com/en-us/dotnet/api/system.io.file.move.

## 10. Do ustalenia

- **`order_seed`** nie ma pola w schemacie (`additionalProperties: false`), a [design.md](../protocol/design.md) §4
  mówi o ziarnie „z konfiguracji”. Propozycja: `--order-seed`, a bez niego ziarno z `series_id` (T5); zgłosić pole
  opcjonalne w wersji 2.x.
- **Miejsce konfiguracji.** [experiments/README.md](../../experiments/README.md) mówi o podfolderach `pilot/` i
  `study/`, a [schemas/README.md](../../schemas/README.md) o `experiments/<series_id>.json`. Propozycja: płasko, nazwa
  pliku = `series_id`; seria przyjmuje każdą ścieżkę.
- **Tempo i równoległość** nie mają pól w konfiguracji. Propozycja: `experiments/provider-limits.json` (domyślnie 1
  przebieg naraz, bez RPM; wartości z `docs/knowledge/provider-apis.md` przed pilotażem).
- **Górny koszt przebiegu:** [design.md](../protocol/design.md) §5 ma tabelę na (model, zadanie, rozmiar), konfiguracja
  jedno `limits.max_cost_per_run`. Propozycja: ta jedna wartość, wymagana przy `budget` niepustym.
- **`limits.max_output_tokens_per_turn`** jest jedno na serię, a modele mają 2048 i 8192; `run_start.limits` kopiuje
  konfigurację. Propozycja: ostrzeżenie przy różnicy; rozstrzyga protokół.
- **`superseded_by` po `daily_limit` na ostatniej próbie:** `RetryRunId` jest `null` po wyczerpaniu
  `max_run_retries`, a `daily_limit` nie zużywa ponowienia, więc kolejnej próby nie da się wskazać z góry.
  Propozycja: dodatkowe pole `RunSpec` (`RetryRunIdAfterDailyLimit`) w [environment.md](environment.md).
- **`provider_funds`** nie jest w `RunOutcome` ani w `run_end.error`. Propozycja: seria czyta `algotrace.error_kind` w
  `PacedChatClient`; po wznowieniu taka komórka jest zamknięta, ręczna powtórka przez przeniesienie pliku.
- **Pauza po `daily_limit`** do 00:00 UTC to założenie (dostawcy odnawiają limity o różnych porach). Propozycja: po
  pauzie próba, kolejna odmowa wydłuża pauzę o godzinę.
- **Końcowy LF plików tekstów:** [prompts.md](../protocol/prompts.md) §1 wyklucza końcowy znak nowego wiersza.
  Propozycja: seria odcina jeden LF (albo robi to środowisko).
- **Typy:** `ICostGuard` nie zna przebiegu; `LocalServerInfo` bez pól (propozycja: jak
  `software.local_server` plus `digest`); `lock_sha256` = SHA-256 złączonych bajtów `global.json`,
  `Directory.Packages.props`, `packages.lock.json`.
- **Wiele konfiguracji w kolejce:** osobny `BudgetGuard` na `series_id`.
