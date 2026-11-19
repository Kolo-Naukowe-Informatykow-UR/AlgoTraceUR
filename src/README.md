# src

Kod projektu, jeden folder na moduł. Moduły wymieniają dane tylko przez formaty z `schemas/`.

| Moduł | Zadanie | Wejście | Wyjście |
|---|---|---|---|
| `environment/` | zadania z ukrytym stanem i pętla tool callingu | zadanie, N, ziarno, adapter | zapis przebiegu |
| `adapters/` | wspólny interfejs do modeli różnych dostawców | wiadomości i opis narzędzi | odpowiedź modelu, wywołania narzędzi, tokeny |
| `runner/` | seria przebiegów z konfiguracji | konfiguracja eksperymentu | zapisy przebiegów, wiersze wyników |
| `references/` | algorytmy wzorcowe i syntetyczne przebiegi | dane zadania | zapis przebiegu wzorca |
| `analyzer/` | rozpoznanie strategii z zapisu przebiegu | zapis przebiegu, wzorce | wynik analizatora |
| `analysis/` | statystyka i wykresy | wyniki, wyniki analizatora | tabele i wykresy do `paper/` |

Język i biblioteki każdego modułu są jeszcze otwarte; po decyzji README modułu mówi, w jakim jest języku, jak go
zbudować i uruchomić, a struktura wewnątrz folderu idzie za zwyczajem wybranego języka.
