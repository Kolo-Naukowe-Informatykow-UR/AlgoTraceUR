# docs/protocol

Protokół eksperymentu, ustalony **przed** zbieraniem danych pełnego badania i zmieniany tylko z zapisem zmiany
w sekcji „Historia zmian”.

Status: **przed pilotażem** (wersja z 2026-11-20). Pilotaż może zmienić tylko punkty
wymienione w [design.md](design.md), sekcja 6, według zapisanych tam reguł. Przed preregistracją na OSF i pierwszym
przebiegiem pełnego badania protokół się zamraża; zmiana po zamrożeniu jest odstępstwem i trafia do
raportu.

## Pliki

| Plik | Co zawiera |
|---|---|
| [prompts.md](prompts.md) | teksty dla modeli (po angielsku): prompt systemowy, opisy zadań, prośba o zapowiedź, przypomnienie, schematy narzędzi, komunikaty błędów, warianty pilotażu, słowa zakazane, tłumaczenie polskie |
| [run-settings.md](run-settings.md) | ustawienia 7 modeli, wywołania równoległe, limity kroków, błędów, tokenów, kontekstu i czasu, ponawianie, strażnik budżetu, `end_reason`, konfiguracja przebiegu |
| [fault-injection.md](fault-injection.md) | warunek z błędami narzędzi: typy, harmonogram z ziarnem, komunikat, zapis, miary do pytania 5 |
| [design.md](design.md) | układ: seria główna, warunek z błędami, instancje i ziarna, kolejność, liczby przebiegów, kosztorys, pilotaż i reguły rozstrzygnięcia |
| [classification-rules.md](classification-rules.md) | reguły etykiet strategii, próg odległości, reguła hybrydy, kalibracja i zamrożenie progów, Hanoi, wyszukiwanie, kodowanie ręczne, KPI analizatora |
| [analysis-plan.md](analysis-plan.md) | plan analizy: definicje sukcesu, hipotezy potwierdzające, metody dla pytań 1-5, przebiegi ucięte, wrażliwość, moc |

## Zakres protokołu: gdzie co jest

| Co protokół ustala | Miejsce |
|---|---|
| prompt systemowy | [prompts.md](prompts.md), sekcja 3 |
| opis zadania każdej rodziny, neutralny, bez podpowiedzi algorytmu | [prompts.md](prompts.md), sekcje 1, 5 i 11 |
| co model wie (N, cel; wartości nie) | [prompts.md](prompts.md), sekcja 4 |
| zbieranie deklaracji algorytmu | [prompts.md](prompts.md), sekcja 6; kodowanie: [analysis-plan.md](analysis-plan.md), sekcja 5 |
| ustawienia (temperatura, rozumowanie) | [run-settings.md](run-settings.md), sekcje 1-2; temperatura w pilotażu: [design.md](design.md), sekcja 6 |
| limity kroków | [run-settings.md](run-settings.md), sekcja 3 |
| limity czasu i tokenów | [run-settings.md](run-settings.md), sekcje 2 i 5 |
| warunki zatrzymania | [run-settings.md](run-settings.md), sekcje 4 i 8 |
| wstrzykiwanie błędów | [fault-injection.md](fault-injection.md) |
| wywołania równoległe | [run-settings.md](run-settings.md), sekcja 1; wykonanie: [prompts.md](prompts.md), sekcja 2 |
| rozmiary N | [design.md](design.md), sekcja 1 |
| liczba powtórzeń | [design.md](design.md), sekcja 1; zmiana po pilotażu: sekcja 6 |
| ziarna | [design.md](design.md), sekcje 3-4; błędy: [fault-injection.md](fault-injection.md), sekcja 3 |
| miary z Research design | [analysis-plan.md](analysis-plan.md), sekcje 3-7 |
| przedziały ufności skuteczności | [analysis-plan.md](analysis-plan.md), sekcje 1 i 3 |
| testy porównań modeli | [analysis-plan.md](analysis-plan.md), sekcje 2-3 |
| próg odległości klasyfikatora | [classification-rules.md](classification-rules.md), sekcje 4, 6 i 12 |
| reguła hybrydy | [classification-rules.md](classification-rules.md), sekcja 5 |
| KPI analizatora | [classification-rules.md](classification-rules.md), sekcja 11 |

Decyzje protokołu (wszystkie przyjęte 2026-11-20 w wariancie A, do potwierdzenia przez właściciela projektu): D01 zapowiedź
algorytmu ([prompts.md](prompts.md)), D02 błędy narzędzi ([fault-injection.md](fault-injection.md)), D03 ustawienia
([run-settings.md](run-settings.md)), D04 wywołania równoległe ([run-settings.md](run-settings.md),
[prompts.md](prompts.md)), D05 rozmiary ([design.md](design.md)), D06 próg i hybryda
([classification-rules.md](classification-rules.md)), D07 KPI ([classification-rules.md](classification-rules.md)),
D08 wynik `move` ([prompts.md](prompts.md)), D09 język tekstów ([prompts.md](prompts.md)).

## Czego protokół wymaga od kontraktu danych

Pola ponad wzór zdarzeń `run_start`, `model_turn`, `tool_call`, `run_end`:

- `run_start`: `series` (`pilot`, `full`), `condition` (`main`, `faults`), `prompt_version` (w kontrakcie
  `prompt.prompt_id`), `prompt_variant` (wartości z [prompts.md](prompts.md), sekcja 10), SHA-256 promptu systemowego, opisu zadania
  i definicji narzędzi, `instance_id` i instancja, harmonogram błędu (`fault_seed`, `fault_type` `one_off` / `persistent`, `fault_position`,
  `fault_length`), `run_attempt`, konfiguracja modelu i limity ([run-settings.md](run-settings.md), sekcja 9),
  `strict_tools`, temperatura grupy pilotażowej, gdy ustawiona.
- `model_turn`: numer tury, `attempts` (każda próba zapytania), `stop_reason` dostawcy, widoczny tekst tury (z niego
  deklaracja), treść rozumowania osobno, tokeny (wejście, z cache, zapis cache, wyjście, rozumowanie), koszt umowny,
  czy tura była przypomnieniem.
- `tool_call`: numer tury i pozycja w turze (D04), `validation_error` (`unknown_tool`, `bad_arguments`,
  `out_of_range`, `same_index`, `illegal_move`, `after_done`; bez `extra_call`), `validation_detail` (przy
  `illegal_move`: `empty_peg`, `larger_on_smaller`, `same_peg`), `injected_fault` (`type`, `event_index`), `executed`,
  `skipped_reason` (`step_limit` i pozostałe wywołania tury po końcu przebiegu), wynik taki, jaki dostał model, stan po
  kroku.
- `run_end`: `end_reason` z zamkniętej listy 10 wartości ([run-settings.md](run-settings.md), sekcja 8), `solved`,
  `fault_fired` (w kontrakcie wyprowadzane: `counts.injected_faults > 0`), liczniki błędów walidacji według rodzaju,
  liczba błędów wstrzykniętych, `text_turns`, `reminders`, `superseded_by` przy próbie zastąpionej ponowieniem.
- Plik instancji serii: pola z [design.md](design.md), sekcja 3.
- Etykiety strategii i deklaracji to wynik analizy, nie zapisu przebiegu.

### Zgodność ze schematami w `schemas/`

Stan z 2026-11-20: kontrakt danych w wersji v2 (`schemas/*.v2.schema.json`, zmiana opisana
w `schemas/README.md`; decyzje kontraktu v2 przyjęte w wariancie A), `python -I schemas/check_examples.py` przechodzi.
Nazwy `step_limit`, `interrupted`, `faults` i `one_off` protokół przejął z kontraktu wcześniej. Otwartych rozbieżności
między protokołem a kontraktem nie ma (wcześniejsza lista rozbieżności jest zamknięta). Rozbieżności znalezione później przy pisaniu specyfikacji: [open-questions.md](../project/open-questions.md).

**Uzgodnione w kontrakcie:**

- `end_reason` ma 10 wartości protokołu, z `time_limit`.
- `validation_error` nie ma `extra_call` (D04 A); `parallel_tool_calls` w ustawieniach modelu, w `run_start` i
  w wierszu wyników przyjmuje tylko `true`.
- `condition` (`main`, `faults`), `series` (`pilot`, `full`) i `prompt.prompt_variant` są osobnymi polami
  konfiguracji, `run_start` i wiersza wyników. Schemat konfiguracji pilnuje reguł protokołu: w serii `full` i w
  warunku `faults` tylko wariant `main`; `announcement_requested` jest `false` dokładnie w wariancie
  `no_announcement`; `compare_result_format: symbols` w sortowaniu dokładnie w wariancie `compare_symbols`.
- `validation_detail` (`empty_peg`, `larger_on_smaller`, `same_peg`) jest w `tool_call` i jest wymagane dokładnie przy
  `illegal_move`; `strict_tools` jest w ustawieniach modelu, w `run_start` i w wierszu wyników.
- Komunikaty w przykładach kontraktu są tymi z [prompts.md](prompts.md) (sekcja 9) i
  [fault-injection.md](fault-injection.md) (sekcja 5).
- Ponowienie całego przebiegu ([run-settings.md](run-settings.md), sekcja 6): `run_attempt` jest w `run_start`
  i w kluczu `run_id`, więc każda próba ma nowy `run_id` i własny plik; `run_end.superseded_by` (i kolumna wyników)
  wskazuje `run_id` następnej próby, analiza bierze ostatnią.
- Harmonogram błędu na instancję ([fault-injection.md](fault-injection.md), sekcje 3-6): `fault_schedule`
  (`fault_seed`, `fault_position` = c, liczone w poprawnych wywołaniach innych niż `done`) w wierszu instancji, typ,
  długość (`fault_type`, `fault_length`) i komunikat w konfiguracji, całość w `run_start.faults`; wywołanie z błędem ma
  `injected_fault: {type, event_index}` z `event_index` 1..`fault_length`.
- `skipped_reason` (`step_limit`, `too_many_errors`) w `tool_call` ([run-settings.md](run-settings.md), sekcje 3 i 8):
  wywołanie pominięte nie jest krokiem (`step: null`, `result: null`), więc `steps` = wykonane + błędy walidacji +
  błędy wstrzyknięte i `step_limit` dokładnie przy `max_steps` krokach dalej się zgadzają; licznik
  `counts.skipped_calls`. Po `done` reszta tury dostaje błąd walidacji `after_done` ([prompts.md](prompts.md),
  sekcja 2), więc `skipped_reason` nie ma wartości `done`.
- Plik instancji ([design.md](design.md), sekcja 3): wiersz ma `instance_id`, `series`, `idx`, `task`, `n`, `rep`,
  `seed`, `generator` (nazwa, `version`, ziarna bazowe), `initial_state`, `target_present`, `answer`, `fault_schedule`
  i `checks` (wynik sprawdzeń); `size` protokołu to `n`, `generator_version` to `generator.version`, `target`
  wyszukiwania jest w `initial_state`.
- Limity czasu ([run-settings.md](run-settings.md), sekcja 5): `timeouts` (`request_timeout_s`, `run_timeout_s`)
  w każdym modelu konfiguracji (300 s i 3 h w chmurze, 600 s i 6 h lokalnie) i w `run_start.limits`.
- Koszt umowny każdej tury ([run-settings.md](run-settings.md), sekcja 7): `model_turn.cost`; `run_end.cost` to suma
  tur, a koszt `null` (model lokalny bez ceny) strażnik liczy jak 0.
- Etykiety strategii ([classification-rules.md](classification-rules.md), sekcje 1-2): `label` wyniku analizatora
  ma `text` w zapisie protokołu (np. `known:bubble_sort`, `hybrid:insertion_sort+selection_sort`,
  `failed:wrong_done:false_absent`) i te same informacje w polach `kind`, `algorithms`, `variant`, `subtype`,
  `failure_detail`, z rodzajami dozwolonymi według rodziny zadań; `exploratory_label` to strategia przebiegu
  nieudanego (sekcja 2, ostatni punkt).

**Zmienione w protokole zamiast w kontrakcie:**

- Konfiguracja to jeden plik na serię i warunek albo grupę pilotażu, a w warunku `faults` jeden na typ błędu, każdy
  z własnym `series_id` (np. `full-main`, `full-faults-one-off` i `full-faults-persistent` w serii `full`), bo `run_id`
  liczy się z `series_id`, a przebiegi warunku `faults` mają te same instancje i powtórzenia co seria główna
  ([run-settings.md](run-settings.md), sekcja 9; decyzja kontraktu v2 o konfiguracji na typ błędu).
- `fault_fired` nie jest osobnym polem zapisu, tylko wartością wyprowadzaną z `run_end.counts.injected_faults > 0`
  (w warunku `faults`; kolumna `fault_fired` w wynikach).
- `base_seed` i `base_fault_seed` („w konfiguracji serii” w [design.md](design.md) i
  [fault-injection.md](fault-injection.md)) są w opisie generatora każdego wiersza pliku instancji, bo plik jest jeden
  na etap i czyta go kilka konfiguracji; `fault_type` i `fault_length` są w konfiguracji, a nie przy instancji, bo ten
  sam harmonogram instancji służy obu typom błędów.
- Powtórzenie komórki w protokole to osobna instancja (`rep` 0..9), więc konfiguracja ma `repetitions: 1`, a każdy
  model przechodzi każdą instancję raz.

## Historia zmian

| Data | Zmiana | Powód |
|---|---|---|
| 2026-11-20 | Wersja „przed pilotażem”: sześć plików protokołu, teksty `p1` (decyzje D01-D09 przyjęte w wariancie A). Sprawdzenie słów zakazanych w blokach `text` i `json` [prompts.md](prompts.md): 0 trafień. | Protokół przed pilotażem i preregistracją. |
| 2026-11-20 | Kontrakt danych w `schemas/` dopasowany do protokołu (sekcja „Zgodność ze schematami”); w protokole: konfiguracja na serię i warunek z własnym `series_id` ([run-settings.md](run-settings.md), sekcja 9), `fault_fired` wyprowadzane z liczników. | Domknięcie wersji „przed pilotażem”. |
| 2026-11-20 | Kontrakt danych v2 (`schemas/*.v2.schema.json`): pola z listy rozbieżności protokołu i kontraktu w kontrakcie, sekcja „Zgodność ze schematami” bez otwartych rozbieżności; w protokole: w warunku `faults` konfiguracja na typ błędu ([run-settings.md](run-settings.md), sekcja 9), ziarna bazowe w pliku instancji, `repetitions: 1`. | Kontrakt danych v2 (jego decyzje przyjęte w wariancie A). |
