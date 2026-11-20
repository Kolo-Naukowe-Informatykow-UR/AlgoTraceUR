# Otwarte pytania o interfejsy

Stan z 20.11.2026. Przy pisaniu specyfikacji programów wyszło jedenaście miejsc, w których protokół
(`docs/protocol/`), kontrakt danych (`schemas/` v2 z przykładami i `check_examples.py`) i
[decyzja 0001](../decisions/0001-stos-technologiczny.md) mówią co innego. Specyfikacje idą za protokołem i opisują
każdą sprawę w swojej sekcji 10 „Do ustalenia”. Poprawka w `schemas/`, protokole albo decyzjach wymaga decyzji
zespołu (np. na pierwszym spotkaniu); po decyzji zmień plik źródłowy, usuń wiersz stąd i z sekcji 10 specyfikacji.

| Nr | Sprawa | Protokół | Kontrakt albo decyzja | Propozycja | Specyfikacja |
|---|---|---|---|---|---|
| 1 | tokeny sortowania | [classification-rules.md](../protocol/classification-rules.md) §3: indeksy `(min, max)` | `check_examples.py` (`selection_sort_tokens`) i przykład `analyzer-result.bubble-sort-n5.json` nie normalizują | poprawić skrypt i przykład według protokołu (na `[4, 6, 3, 1, 2]` odległość bąbelkowe-wybór 13 edycji, 0,7222, zamiast 18, 1,0) | [analyzer.md](../specs/analyzer.md), [references.md](../specs/references.md) |
| 2 | `done` na kroku `max_steps` | [run-settings.md](../protocol/run-settings.md) §8: kolejność `done`, `too_many_errors`, `step_limit` | `check_examples.py`: `step_limit` dokładnie przy `steps == max_steps` | poprawić skrypt według protokołu | [environment.md](../specs/environment.md) |
| 3 | przypomnienia | run-settings.md §4: koniec po drugiej odpowiedzi bez wywołania z rzędu albo czwartej w przebiegu | przykłady: `max_reminders: 1`, pole bez opisu | pole liczy przypomnienia z rzędu; dopisać opis w schemacie | environment.md |
| 4 | skrót promptu | [prompts.md](../protocol/prompts.md) §1: SHA-256 promptu systemowego i opisu zadania | jedno pole `prompt.sha256` bez reguły złożenia | ustalić regułę złożenia (kolejność, separator) i dopisać ją do schematu | environment.md |
| 5 | tekst deklaracji | prompts.md §6: wszystkie odpowiedzi do pierwszej z wywołaniem włącznie | `check_examples.py`: tekst pierwszej tury | poprawić skrypt według protokołu | analyzer.md |
| 6 | Ollama | run-settings.md §1-2: `/api/chat`, `think: false`, `options`; wszystkie wywołania tury wykonuje środowisko | decyzja 0001: `/v1/chat/completions`, adapter wykonuje pierwsze wywołanie, resztę oznacza | nowa decyzja, która zastępuje ten punkt 0001 | [adapters.md](../specs/adapters.md), environment.md |
| 7 | przykład konfiguracji Ollamy | parametry próbkowania niewysyłane (poza `seed` = ziarno instancji) | `experiment-config.pilot-sort.json`: `temperature` 0.8, `top_p` 0.9, `seed` 42, adres `/v1` | poprawić przykład po decyzji z wiersza 6 | adapters.md |
| 8 | ziarno kolejności | [design.md](../protocol/design.md) §4: permutacja przebiegów z `order_seed` „z konfiguracji serii” | `experiment-config.v2`: brak pola, `additionalProperties: false` | opcja `--order-seed`, domyślnie 8 bajtów SHA-256 `series_id`; pole w wersji 2.x | [runner.md](../specs/runner.md) |
| 9 | górny koszt przebiegu | design.md §5: tabela na (model, zadanie, rozmiar) | konfiguracja: jedno `limits.max_cost_per_run` | seria używa tej jednej wartości i wymaga jej przy `budget` | runner.md |
| 10 | miejsce konfiguracji | [experiments/README.md](../../experiments/README.md): podfoldery `pilot/`, `study/` | [schemas/README.md](../../schemas/README.md): `experiments/<series_id>.json` | płasko, nazwa pliku = `series_id` | runner.md |
| 11 | odcinki przy błędzie wstrzykniętym | classification-rules.md §9: etykieta odcinka przed i po błędzie | `analyzer-result.v2`: `segments` tylko dla hybryd, `metrics` tylko liczby | pole na etykiety odcinków w wersji 2.1 | analyzer.md, [analysis.md](../specs/analysis.md) |

Ustalenia architektury, które specyfikacje już przyjęły (zmiana też wymaga decyzji zespołu):

- Środowisko i adaptery łączy `IChatClient` z kluczami `algotrace.*` w `AdditionalProperties` (surowe argumenty,
  powód zakończenia dostawcy, próby, `raw_ref`, rodzaj błędu); nieudane zapytanie to odpowiedź z `FinishReason`
  `error` i `algotrace.error_kind`, bez zdarzenia `model_turn`.
- Analizator importuje publiczne API `algotrace_references` (wyjątek od zasady „programy łączą się tylko plikami”),
  bo reguła hybrydy uruchamia wzorzec od stanu pośredniego; seria woła publiczne API środowiska.
- `schemas/check_examples.py` z przykładami to wykonywalny opis zachowania sortowania; testy akceptacyjne
  specyfikacji liczą liczby jego funkcjami (stąd wiersze 1, 2 i 5 trzeba rozstrzygnąć przed testami).
