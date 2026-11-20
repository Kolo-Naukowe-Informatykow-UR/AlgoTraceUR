# data

Dane projektu w formatach z `schemas/`.

| Folder | Co tam trafi | Kto zapisuje |
|---|---|---|
| `synthetic/` | syntetyczne przebiegi algorytmów wzorcowych do walidacji analizatora | `src/references/` |
| `runs/` | zapisy przebiegów modeli z pilotażu i pełnego badania | `src/runner/` |
| `results/` | wiersze wyników (CSV) i wyniki analizatora | `src/runner/`, `src/analyzer/` |

Zasady:

- zapisów przebiegów się nie zmienia; poprawka to nowy plik z opisem powodu;
- w danych nie ma kluczy API ani danych osobowych;
- zbiór przebiegów ma być publiczny na licencji z sekcji „Licencja”; sposób publikacji dużych plików (repozytorium
  albo wydanie na GitHubie) jest do ustalenia.

## Licencja

Cały folder `data/` (`synthetic/`, `runs/`, `results/`) jest na CC0 1.0 Universal (`CC0-1.0`, tekst prawny:
https://creativecommons.org/publicdomain/zero/1.0/legalcode): autorzy zrzekają się praw autorskich i praw do bazy
danych w zakresie, na jaki pozwala prawo. Zrzeczenie nie obejmuje patentów ani znaków towarowych.

- Atrybucja nie jest wymagana, ale prosimy o cytowanie zbioru w pracach, które z niego korzystają; DOI z Zenodo
  podamy po pierwszym wydaniu zbioru.
- Odpowiedzi w zapisach przebiegów wygenerowały modele językowe; ich dostawców i pełny opis zbioru poda karta zbioru
  przy pierwszym wydaniu.
