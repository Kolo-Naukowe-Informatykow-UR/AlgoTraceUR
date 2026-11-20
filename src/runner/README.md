# src/runner

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/runner.md](../../docs/specs/runner.md).

Uruchamianie serii eksperymentów: program czyta konfigurację z `experiments/` (dostawca, model, zadanie, N,
ziarno, prompt, ustawienia, limity, ścieżki wyników), uruchamia przebiegi (modele × zadania × N × powtórzenia)
w środowisku i zapisuje zapisy przebiegów oraz wiersze wyników do `data/`.

Wymagania:

- jeden przebieg albo cała seria jednym poleceniem z zapisanej konfiguracji;
- seria w tle, wznawiana po przerwaniu bez powtarzania gotowych przebiegów;
- limit kosztu: seria staje po przekroczeniu ustalonego budżetu.

Powtórzenie przebiegu oznacza uruchomienie tej samej konfiguracji z tym samym ziarnem; odpowiedź modelu może się
różnić, więc źródłem analizy jest zawsze zapis przebiegu.

## Język i narzędzia

C# / .NET 10 (`net10.0`), aplikacja konsolowa `AlgoTrace.Runner`; środowisko i adaptery łączy przez `IChatClient`.
Główne biblioteki:

- `System.Text.Json` i `JsonSchema.Net`: konfiguracja z `experiments/` sprawdzana ze schematem przed startem serii;
- `System.Threading.RateLimiting`: tempo zapytań do dostawców.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy powstanie kod serii (po środowisku i adapterach). Z katalogu głównego repozytorium:

```
dotnet build
dotnet run --project src/runner -- experiments/<konfiguracja>
dotnet test
```

Testy modułu leżą w `tests/dotnet/AlgoTrace.Runner.Tests/`. Klucze API tylko w zmiennych środowiskowych; model
lokalny wymaga działającej Ollamy (`src/adapters/README.md`).
