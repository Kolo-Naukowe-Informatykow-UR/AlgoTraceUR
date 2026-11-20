# tests

Testy akceptacyjne każdego programu (konkretne dane i oczekiwane wyniki) są w sekcji 8 jego specyfikacji: indeks w [docs/README.md](../docs/README.md).

Testy modułów z `src/`, osobno dla każdego języka
([0001 Stos technologiczny modułów](../docs/decisions/0001-stos-technologiczny.md)):

- **.NET** (`environment`, `adapters`, `runner`): `tests/dotnet/AlgoTrace.<Moduł>.Tests/`, xUnit v3 z FsCheck
  i Verify; uruchamia je `dotnet test` z katalogu głównego;
- **Python** (`references`, `analyzer`, `analysis`): `tests/python/<moduł>/`, pytest z hypothesis i syrupy;
  uruchamia je `uv run --locked pytest` z katalogu głównego.

Pliki `*.verified.*` (Verify) i `__snapshots__/` (syrupy) są wzorcami w repozytorium: zmieniony zapis przebiegu
bez ich zmiany to błąd testu.

Testy, które muszą być niezależnie od języka:

- algorytmy wzorcowe dają znane liczby kroków (np. dla `[4, 6, 3, 1, 2]`: bąbelkowe 10 porównań i 8 zamian, przez
  wstawianie 10 i 8, przez wybór 10 i 2);
- pliki zapisywane przez moduły są zgodne ze schematami z `schemas/`;
- analizator rozpoznaje syntetyczne przebiegi wzorców (walidacja z progiem z `docs/protocol/`);
- generator zadań daje te same dane dla tego samego ziarna.

Testy nie wołają płatnych API; modele zastępuje atrapa zgodna z kontraktem danych.
