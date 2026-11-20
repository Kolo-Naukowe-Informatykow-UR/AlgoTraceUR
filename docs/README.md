# docs

Dokumentacja projektu, która nie jest kodem ani tekstem badania. Zasady pracy i kolejność czytania:
[AGENTS.md](../AGENTS.md).

| Folder albo plik | Co zawiera |
|---|---|
| [project/overview.md](project/overview.md) | projekt badania: pytania, metoda rozpoznawania algorytmu, miary, zestaw modeli, koszt |
| [project/work-plan.md](project/work-plan.md) | plan prac: kolejność programów, zależności, kryteria „gotowe” |
| [project/open-questions.md](project/open-questions.md) | otwarte sprawy interfejsów (protokół a kontrakt danych), do decyzji zespołu |
| `specs/` | specyfikacje sześciu programów (tabela niżej) |
| [knowledge/provider-apis.md](knowledge/provider-apis.md) | różnice API dostawców modeli, których adapter musi pilnować |
| [protocol/](protocol/README.md) | protokół eksperymentu i plan analizy wyników, ustalone przed zbieraniem danych |
| [decisions/](decisions/README.md) | zapisy decyzji projektu (jedna decyzja na plik) |
| `meetings/` | notatki ze spotkań zespołu i kopie raportów co 2 tygodnie |

## Specyfikacje programów

Każda ma ten sam układ: cel, granice, wejścia i wyjścia, interfejsy, zachowanie, błędy i przypadki brzegowe,
wymagania protokołu, testy akceptacyjne, wiedza techniczna i źródła, sprawy do ustalenia.

| Program | Specyfikacja | Folder |
|---|---|---|
| środowisko | [specs/environment.md](specs/environment.md) | `src/environment/` |
| adaptery dostawców | [specs/adapters.md](specs/adapters.md) | `src/adapters/` |
| seria przebiegów | [specs/runner.md](specs/runner.md) | `src/runner/` |
| algorytmy wzorcowe | [specs/references.md](specs/references.md) | `src/references/` |
| analizator | [specs/analyzer.md](specs/analyzer.md) | `src/analyzer/` |
| analiza wyników | [specs/analysis.md](specs/analysis.md) | `src/analysis/` |

Tu trafia też raport walidacji analizatora, jeśli nie wejdzie do tekstu badania.
