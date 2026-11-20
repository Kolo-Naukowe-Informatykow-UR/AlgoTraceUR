# src/references

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/references.md](../../docs/specs/references.md).

Algorytmy wzorcowe, które na tych samych danych co model zapisują każdy krok w formacie zapisu przebiegu, oraz
generator syntetycznych przebiegów do walidacji analizatora.

Co tu trafi:

- **sortowanie** (co najmniej 6 algorytmów, z wariantami: kierunek, wczesne zakończenie, wybór osi): bąbelkowe, przez
  wstawianie, przez wybór, szybkie, scalanie w miejscu i np. koktajlowe albo Shella;
- **wieże Hanoi:** rozwiązanie rekurencyjne;
- **wyszukiwanie:** binarne, liniowe, interpolacyjne;
- **generator syntetycznych przebiegów:** przebiegi wzorców czyste i z zakłóceniami (zbędne porównanie, pominięty
  krok, zmieniona kolejność), powtarzalne z ziarna; wynik w `data/synthetic/`.

Przykład do testów: dla `[4, 6, 3, 1, 2]` sortowanie bąbelkowe robi 10 porównań i 8 zamian, przez wstawianie 10 i 8,
przez wybór 10 i 2 (liczba inwersji to 8).

## Język i narzędzia

Python 3.13, pakiet `algotrace_references` w workspace uv repozytorium. Główne biblioteki:

- biblioteka standardowa: algorytmy wzorcowe i generator bez dodatkowych bibliotek;
- `jsonschema` (`Draft202012Validator`): zgodność zapisów przebiegu ze `schemas/`.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy powstanie kod wzorców. Z katalogu głównego repozytorium:

```
uv sync --locked --all-packages
uv run --locked python -m algotrace_references ...
uv run --locked pytest tests/python/references
```

Syntetyczne przebiegi trafiają do `data/synthetic/`.
