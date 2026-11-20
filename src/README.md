# src

Kod projektu, jeden folder na moduł. Moduły wymieniają dane tylko przez formaty z `schemas/`.

| Moduł | Język | Zadanie | Wejście | Wyjście |
|---|---|---|---|---|
| `environment/` | C# / .NET 10 | zadania z ukrytym stanem i pętla tool callingu | zadanie, N, ziarno, adapter | zapis przebiegu |
| `adapters/` | C# / .NET 10 | wspólny interfejs do modeli różnych dostawców | wiadomości i opis narzędzi | odpowiedź modelu, wywołania narzędzi, tokeny |
| `runner/` | C# / .NET 10 | seria przebiegów z konfiguracji | konfiguracja eksperymentu | zapisy przebiegów, wiersze wyników |
| `references/` | Python 3.13 | algorytmy wzorcowe i syntetyczne przebiegi | dane zadania | zapis przebiegu wzorca |
| `analyzer/` | Python 3.13 | rozpoznanie strategii z zapisu przebiegu | zapis przebiegu, wzorce | wynik analizatora |
| `analysis/` | Python 3.13 | statystyka i wykresy | wyniki, wyniki analizatora | tabele i wykresy do `paper/` |

## Wymagania

- **.NET SDK 10** (dokładna wersja w `global.json`) dla `environment/`, `adapters/` i `runner/`;
- **uv** dla `references/`, `analyzer/` i `analysis/`; Pythona 3.13 uv instaluje sam według `.python-version`;
- **Ollama** tylko do modelu lokalnego (`adapters/README.md`).

Z katalogu głównego repozytorium `dotnet build` i `dotnet test` budują i testują moduły .NET (jedno rozwiązanie
`AlgoTrace.slnx`), a `uv sync --locked --all-packages` i `uv run --locked pytest` moduły Pythona (jeden workspace uv,
pakiety `algotrace_<moduł>`). Dopóki nie ma kodu, polecenia w README modułów są planem; pierwszy kod modułu je
sprawdza i poprawia.

Język, biblioteki, układ plików i odrzucone opcje:
[0001 Stos technologiczny modułów](../docs/decisions/0001-stos-technologiczny.md). Struktura wewnątrz folderu modułu
idzie za zwyczajem jego języka.
