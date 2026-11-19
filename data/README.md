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
- zbiór przebiegów ma być publiczny; licencja zbioru i sposób publikacji dużych plików (repozytorium albo wydanie na
  GitHubie) są do ustalenia.
