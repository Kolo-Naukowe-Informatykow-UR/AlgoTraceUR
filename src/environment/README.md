# src/environment

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/environment.md](../../docs/specs/environment.md).

Środowisko testowe:

- **generator zadań z ziarnem:** dane wejściowe sortowania, wież Hanoi i wyszukiwania, powtarzalne z ziarna;
- **piaskownica z ukrytym stanem:** model nie widzi danych, zmienia i odczytuje stan tylko przez narzędzia
  `compare(i, j)`, `swap(i, j)`, `move(from, to)`, `read(index)`; program sprawdza stan końcowy;
- **pętla tool callingu:** walidacja argumentów, czytelny błąd zwracany modelowi, limit kroków i czasu, celowe
  wstrzykiwanie błędów narzędzi;
- **zapis przebiegu:** każde wywołanie i każda odpowiedź modelu w formacie z `schemas/`.

Środowisko bazowe powstaje najpierw jako osobny, indywidualny projekt zaliczeniowy lidera (do 23.12.2026) i trafia
tutaj po jego oddaniu. Do tego czasu zespół nie pisze kodu w tym folderze; adaptery i analizator testuje się na
atrapie zgodnej z kontraktem danych.

## Język i narzędzia

C# / .NET 10 (`net10.0`), biblioteka `AlgoTrace.Environment`. Główne biblioteki:

- `Microsoft.Extensions.AI.Abstractions`: interfejs `IChatClient`, jedyne połączenie z adapterami; pętlę tool callingu
  pisze środowisko, nie biblioteka;
- `System.Text.Json`: zapis przebiegu w JSONL;
- `JsonSchema.Net`: zgodność zapisów ze `schemas/` w testach.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy środowisko bazowe trafi do tego folderu (po 23.12.2026). Z katalogu głównego
repozytorium:

```
dotnet build
dotnet test
```

Testy modułu leżą w `tests/dotnet/AlgoTrace.Environment.Tests/`. Środowiska nie uruchamia się osobno: przebiegi
uruchamia seria z `src/runner/`.
