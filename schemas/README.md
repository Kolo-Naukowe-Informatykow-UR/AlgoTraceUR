# schemas

Kontrakt danych: formaty plików, przez które łączą się wszystkie moduły. Moduł nie korzysta z kodu innego modułu,
tylko z tych formatów, więc moduły mogą powstać w różnych językach (środowisko, adaptery i seria w C# / .NET, wzorce,
analizator i analiza w Pythonie).

Schematy: JSON Schema 2020-12, wersja główna 2 (pliki `*.v2.schema.json`). Każdy plik ma `$schema` i `$id`
(`https://algotrace.example/schemas/<plik>`; to identyfikator, nie adres w sieci), odwołania między plikami idą do
`common.v2.schema.json`.

| Schemat | Plik danych | Kto zapisuje | Kto czyta | Zawartość |
|---|---|---|---|---|
| `experiment-config.v2.schema.json` | `experiments/<series_id>.json` | zespół | seria (`src/runner/`) | jedna konfiguracja etapu (`pilot` albo `full`) z jednym warunkiem, jednym typem błędu (w warunku `faults`) i jednym wariantem tekstów: modele (dostawca, model, wersja, adres, nazwa zmiennej z kluczem, ustawienia, limity czasu, cena), zadania i rozmiary z limitem kroków, plik instancji, powtórzenia, prompt, limity, błąd wstrzykiwany, ponawianie, budżet, ścieżki wyników |
| `instance.v2.schema.json` | `instances/<series>.jsonl` | generator instancji | środowisko, wzorce, analizator | jedna instancja na linię: `instance_id`, etap, `idx`, zadanie, N, `rep`, ziarno, generator z ziarnami bazowymi, stan początkowy, odpowiedź wzorcowa wyszukiwania, harmonogram błędu, wynik sprawdzeń |
| `run-event.v2.schema.json` | `<runs_dir>/<run_id>.jsonl` | środowisko i seria | analizator, analiza | jedno zdarzenie na linię: `run_start`, `model_turn` (tura modelu), `tool_call` (krok albo wywołanie pominięte), `run_end` |
| `results-row.v2.schema.json` | `results_csv` z konfiguracji | seria | analiza | jeden wiersz CSV na zakończony przebieg (każdą próbę) |
| `analyzer-result.v2.schema.json` | `analysis_file` z konfiguracji | analizator | analiza | cechy i miary, odległości od wzorców, etykieta strategii protokołu, etykieta eksploracyjna, odcinki hybrydy, deklaracja |
| `common.v2.schema.json` | - | - | - | wspólne definicje (stan, zużycie tokenów, cena i koszt, limity, harmonogram błędu, listy zamknięte) |

Przykłady są w `examples/` (nazwa pliku zaczyna się od nazwy schematu: `experiment-config.`, `instances.`, `run.`,
`results.`, `analyzer-result.`), przykłady błędne, które schemat musi odrzucić, w `examples/invalid/`.
Najważniejszy: `examples/run.bubble-sort-n5.jsonl`, sortowanie bąbelkowe tablicy `[4, 6, 3, 1, 2]` z zapowiedzią
algorytmu, 10 porównaniami, 8 zamianami i `done` (19 kroków, 19 tur). `examples/run.api-error-n3.jsonl` to próba 1
przebiegu w warunku `faults`, zakończona `api_error` i zastąpiona (`superseded_by`) próbą 2,
`examples/run.edge-cases-n3.jsonl`: dwa wywołania w jednej turze, błąd walidacji, turę bez wywołania
z przypomnieniem, błąd wstrzyknięty `one_off` w trzecie poprawne wywołanie (harmonogram instancji), ponowienie
zapytania po błędzie API, koniec na limicie kroków i wywołanie pominięte po nim. Ceny, skróty i ziarna w przykładach
są zmyślone; tablica `[4, 6, 3, 1, 2]` to instancja ręczna (`generator: null`), bo nie jest permutacją 1..N.

## Wersja 2 (2026-11-20)

Protokół eksperymentu (`docs/protocol/`, sekcja „Zgodność ze schematami” w jego README) wymagał pól, których v1 nie
miał. Zmiany są niezgodne z v1, więc to nowa wersja główna, a nie wersja `1.1`: `run_id` liczy się teraz także
z `run_attempt`, przybyły pola wymagane, reguły błędów na konfigurację (`fault_rule`, `rule_index`) zastąpił harmonogram
na instancję, limity czasu przeszły z konfiguracji do modelu, a etykiety analizatora są etykietami protokołu. v1 nie
został wydany: pliki nie były w gicie, nie używał ich żaden kod ani zapis danych, więc v2 zastępuje v1 bez czytnika
v1 (decyzja przyjęta w wariancie A). Pliki `*.v1.schema.json` w tym folderze są nieaktualne i do usunięcia;
skrypt sprawdza tylko `*.v2.schema.json`.

| Obszar | v1 | v2 |
|---|---|---|
| ponowienie przebiegu | `run_id` z `{series_id, config_sha256, model_key, instance_id, repetition}`, ponowienie dostałoby ten sam plik | `run_attempt` (od 1) w `run_start` i w kluczu `run_id`; `run_end.superseded_by` = `run_id` próby następnej |
| błąd wstrzykiwany | `faults: {seed, rules}` na konfigurację, `injected_fault.rule_index` | konfiguracja na typ błędu (`faults: {fault_type, fault_length, message}`), harmonogram w wierszu instancji (`fault_schedule: {fault_seed, fault_position}`), kopia w `run_start.faults`, `injected_fault.event_index` 1..`fault_length` |
| reszta tury po końcu | brak w zapisie | `tool_call` z `skipped_reason` (`step_limit`, `too_many_errors`), `step: null`, `result: null`; `counts.skipped_calls` |
| plik instancji | `instance_id`, `task`, `n`, `seed`, `generator`, `state` | także `series`, `idx`, `rep`, `generator.base_seed` i `base_fault_seed`, `initial_state` (zamiast `state`), `target_present`, `answer`, `fault_schedule`, `checks` |
| limity czasu | `limits.timeout_s_per_run` i `retries.request_timeout_s` na konfigurację | `timeouts: {request_timeout_s, run_timeout_s}` w każdym modelu, kopia w `run_start.limits` |
| koszt | tylko `run_end.cost` | `model_turn.cost` każdej tury, `run_end.cost` = suma tur |
| etykiety | `kind`: `known`, `hybrid`, `novel`, `ambiguous`, `not_classified` | `label` i `exploratory_label`: `text` (np. `known:bubble_sort`, `failed:wrong_done:false_absent`), `kind`, `algorithms`, `variant`, `subtype`, `failure_detail`, `margin`, dozwolone rodzaje według rodziny zadań |
| wiersz wyników | - | kolumny `fault_type`, `run_attempt`, `superseded_by`, `fault_fired`, `skipped_calls` |

## Zapis przebiegu

- Kolejność linii: `run_start`, potem dla każdej tury `model_turn` i jej zdarzenia `tool_call` w kolejności z
  odpowiedzi modelu (każde wywołanie z listy tury ma swoje zdarzenie), na końcu `run_end`. Plik bez `run_end` to
  przebieg przerwany.
- `turn` numeruje odpowiedzi modelu od 1, `step` numeruje kroki od 1 (wywołania wykonane, odrzucone przez walidację
  i z błędem wstrzykniętym), `index_in_turn` to pozycja wywołania w turze od 0 (kilka wywołań w turze jest dozwolonych,
  protokół D04).
- Gdy wywołanie kończy przebieg z `step_limit` albo `too_many_errors`, dalsze wywołania tej tury są zapisane jako
  pominięte: `skipped_reason` równe `end_reason`, `step: null`, `executed: false`, `is_error: false`, `result: null`,
  stan bez zmian; nie są krokami (decyzja przyjęta w wariancie A). Wywołania po `done` w tej samej turze dostają błąd
  walidacji `after_done` (protokół prompts.md, sekcja 2) i są krokami.
- `validation_error` (`unknown_tool`, `bad_arguments`, `out_of_range`, `same_index`, `illegal_move`, `after_done`;
  bez błędu „nadmiarowego wywołania”, bo kilka wywołań w turze jest dozwolonych, a `parallel_tool_calls` ma tylko
  wartość `true`) i `injected_fault` wykluczają się; oba znaczą `executed: false`, `is_error: true` i stan bez zmian.
  `validation_detail` podaje szczegół `illegal_move` (`empty_peg`, `larger_on_smaller`, `same_peg`), przy innych
  wywołaniach jest `null`. Błąd API to `attempts` > 1 i `retries` w `model_turn` albo `end_reason: api_error`.
- Błąd wstrzyknięty (warunek `faults`): środowisko liczy poprawne wywołania inne niż `done` (bez odrzuconych przez
  walidację); `fault_position`-te dostaje błąd (`event_index: 1`), przy `persistent` także następne poprawne wywołania
  tego samego narzędzia, razem `fault_length`. Wynik to `message` z konfiguracji. `fault_fired` protokołu to
  `counts.injected_faults > 0` (kolumna `fault_fired` w wynikach).
- `result` to tekst dokładnie taki, jaki środowisko wysłało modelowi (`after_done`: tylko zapis); `state_after` to cały
  stan ukryty po wywołaniu (w wyszukiwaniu może być `null`, bo stan się nie zmienia).
- Zapowiedź algorytmu (protokół D01) jest w `text` pierwszej tury; jej etykieta to wynik analizy (`declaration`
  w wyniku analizatora), nie zapisu.
- `run_end.steps` to liczba kroków (zdarzeń `tool_call` z numerem); `steps` = suma `executed_by_tool` +
  `validation_errors` + `injected_faults`, a `skipped_calls` liczy wywołania pominięte. `step_limit` jest dokładnie
  wtedy, gdy kroków jest `max_steps`. `usage_total` to suma pól tur (`null`, gdy żadna tura pola nie podała).
- Koszt umowny: `model_turn.cost` z `usage` tury i ceny z `run_start` (wzór w opisie `price` w `common`, `null` jak 0),
  `run_end.cost` to suma kosztów tur; bez ceny (model lokalny) koszt jest `null`, a strażnik budżetu liczy go jak 0.
- `input_kind` mówi, na co model odpowiadał (`task`, `tool_results`, `reminder`), więc liczba przypomnień wynika
  z zapisu.

## Identyfikatory i wersje

- Seria, warunek i wariant to trzy osobne pola (protokół `docs/protocol/`): `series` to etap badania (`pilot`,
  `full`), `condition` to warunek (`main`, `faults`), `prompt.prompt_variant` to wariant tekstów (`main` albo grupa
  pilotażu, np. `no_announcement`, `compare_symbols`). Jeden etap ma kilka konfiguracji, każda z własnym `series_id`:
  jedna na warunek, w warunku `faults` jedna na typ błędu (np. `full-main`, `full-faults-one-off`,
  `full-faults-persistent`; decyzja przyjęta w wariancie A), bo `run_id` liczy się z `series_id`, a oba typy błędów idą na
  tych samych instancjach. Schemat konfiguracji pilnuje: w serii `full` i w warunku `faults` tylko wariant `main`;
  `announcement_requested: false` dokładnie w wariancie `no_announcement`; wyniki `compare` jako symbole dokładnie
  w wariancie `compare_symbols`; `faults` dokładnie w warunku `faults`; `one_off` ma `fault_length` 1.
  `prompt.prompt_id` to wersja zestawu tekstów (np. `p1`).
- Powtórzenia: protokół daje każdemu powtórzeniu komórki (zadanie, rozmiar) własną instancję (`rep` 0..9 w pliku
  instancji), więc każdy model przechodzi każdą instancję raz: `repetitions: 1`, `repetition: 1`.
- `config_sha256`: SHA-256 kanonicznego JSON konfiguracji według RFC 8785 (JCS: posortowane klucze, bez spacji,
  liczby w postaci ECMAScript, np. `2.0` jako `2`). Konfiguracji użytej w badaniu się nie zmienia.
- `run_id`: pierwsze 16 znaków hex SHA-256 kanonicznego JSON obiektu `{series_id, config_sha256, model_key,
  instance_id, repetition, run_attempt}`. Ta sama konfiguracja daje te same identyfikatory, więc wznowiona seria pomija
  gotowe przebiegi; zmiana konfiguracji daje nowe.
- Ponowienie całego przebiegu (protokół run-settings.md, sekcja 6): przebieg zakończony `api_error` powtarza się od
  początku jako próba `run_attempt + 1` (nowy `run_id`, nowy plik), najwyżej `max_run_retries` razy; próba po limicie
  dziennym dostawcy (`error.type: daily_limit`) tego limitu nie zużywa. Zastąpiona próba ma w `run_end.superseded_by`
  `run_id` następnej; analiza bierze ostatnią próbę (wiersze z `superseded_by` pustym).
- Plik instancji (protokół design.md, sekcja 3): jeden na etap, linie w kolejności zadanie (sortowanie, Hanoi,
  wyszukiwanie), rozmiar, `rep`; `idx` to numer linii od 0, `seed = base_seed + idx`, `fault_seed = base_fault_seed +
  idx` (oba ziarna bazowe w `generator`, jednakowe w całym pliku, bo plik czyta kilka konfiguracji). Harmonogram błędu
  (`fault_schedule`) jest przy instancjach komórek z błędami i jest wspólny dla obu typów błędów; typ i długość daje
  konfiguracja. `checks` to wynik sprawdzeń generatora (`failed` niepuste = seria nie startuje).
- Każdy rekord ma `schema_version` (`2.x`). Wersja mniejsza dodaje tylko pola opcjonalne, więc każdy rekord 2.x jest
  zgodny z najnowszym schematem 2.x; zmiana niezgodna to nowy plik `*.v3.schema.json` obok starego i czytnik, który
  wybiera schemat po `schema_version`. Od pierwszego zapisu danych w wersji 2 stare zapisy przebiegów muszą dać się dalej
  odczytać.

## Etykiety strategii

`label` wyniku analizatora to etykieta protokołu (`docs/protocol/classification-rules.md`, sekcje 1-2): `text` tak,
jak pisze ją protokół, i te same informacje w polach. Sortowanie: `known` (jeden algorytm w `algorithms`, wariant
w `variant`), `hybrid` (algorytmy odcinków w kolejności), `ambiguous` (algorytmy równie bliskie), `new` (`subtype`
`info_first` albo `other`), `failed`; Hanoi: `optimal`, `optimal_detours`, `other`, `failed`; wyszukiwanie: `known`,
`ambiguous`, `other`, `too_short`, `failed`. `failed` ma `subtype` z `end_reason` (`wrong_done`, `step_limit`,
`errors`, `no_tool_call`, `context`, `infra`), w wyszukiwaniu `failed:wrong_done` ma `failure_detail`
(`false_absent`, `false_present`, `wrong_index`). `exploratory_label` to strategia przebiegu nieudanego z porównania
z prefiksami wzorców (tylko do analiz eksploracyjnych), przy innych przebiegach `null`.

## Pliki

- JSON i JSONL: UTF-8 bez BOM, końce linii LF, w JSONL jedna wartość na linię i LF także po ostatniej. Zapis
  przebiegu dopisuje linię i robi `flush` po każdym zdarzeniu; czytnik pomija tylko uciętą ostatnią linię.
- CSV: RFC 4180, separator `,`, kropka dziesiętna, UTF-8 bez BOM, LF, nagłówek w kolejności `properties` schematu
  `results-row`, `true`/`false`, pusta komórka = `null`; czytać po nazwach kolumn. Wiersz powstaje tylko z zapisu
  przebiegu.
- Czasy: UTC, ISO 8601 z milisekundami i `Z`. Ścieżki: względne od katalogu głównego repozytorium, z `/`.
- Sekrety: klucz API nigdy w pliku, tylko nazwa zmiennej środowiskowej (`api_key_env`); `settings_sent`
  i `provider_options` odrzucają klucze typu `api_key`, `authorization`. Surowe żądania (`<run_id>.raw.jsonl`) to
  format adapterów, bez nagłówków z kluczem.

## Sprawdzanie

```
python -I schemas/check_examples.py
```

Skrypt (sama biblioteka standardowa Pythona) sprawdza, że każdy przykład jest zgodny ze schematem, każdy przykład
błędny odrzucony, plik instancji spójny (`idx`, kolejność, ziarna z ziaren bazowych, `checks`, odpowiedź
wyszukiwania), a przebiegi spójne: odtworzenie na instancji (walidacja wywołań, wyniki `compare`, błąd wstrzyknięty
według harmonogramu instancji, wywołania pominięte, stan po każdym kroku), liczniki `run_end`, koszt każdej tury,
`config_sha256` i `run_id` (z `run_attempt`) według reguły, łańcuch prób (`superseded_by`), wiersze CSV i wynik
analizatora (etykieta i jej tekst) wyprowadzone z zapisu, sortowanie bąbelkowe `[4, 6, 3, 1, 2]` z 10 porównaniami
i 8 zamianami. Gdy jest zainstalowany pakiet `jsonschema`, waliduje nim (`Draft202012Validator`, z kontrolą `format`);
bez niego wbudowanym walidatorem podzbioru słów kluczowych, który przerywa na każdym słowie spoza podzbioru
(`--builtin` wymusza ten drugi). W .NET te same pliki waliduje `JsonSchema.Net` (schematy trzeba zarejestrować po
`$id`).

Do ustalenia później: format wyniku `compare` (`words` albo `symbols`, ustala pilotaż), opisy narzędzi (zestaw
`tool_set` zna środowisko), szczegółowe pola Hanoi i wyszukiwania w zapisie i w miarach analizatora (odtworzenie
w skrypcie obejmuje tylko sortowanie).
