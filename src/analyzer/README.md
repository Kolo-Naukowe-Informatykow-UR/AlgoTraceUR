# src/analyzer

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/analyzer.md](../../docs/specs/analyzer.md).

Analizator przebiegów: z zapisu przebiegu rozpoznaje, jaką strategią model rozwiązał zadanie.

Kroki dla sortowania:

1. **Czy się udało:** stan końcowy posortowany; nieudane przebiegi dostają rodzaj błędu.
2. **Cechy:** odsetek porównań i zamian sąsiadów, stosunek zamian do porównań, struktura przebiegów (kierunek,
   kurczący się zakres), liczba porównań przed pierwszą zamianą.
3. **Miary:** porównania wobec `ceil(log2(N!))` i wobec wzorca; porównania zbędne (wynik wynikał już z wcześniejszych
   przez przechodniość, liczone na grafie relacji elementów); zamiany wobec liczby inwersji i `N - liczba cykli`.
4. **Odległość od wzorców:** każdy wariant algorytmu wzorcowego z `references/` na tych samych danych, odległość ciągów
   operacji (np. znormalizowana edycyjna).
5. **Klasyfikacja:** najbliższy wzorzec poniżej progu → znany algorytm; fragmenty pasujące do różnych wzorców →
   hybryda; brak dopasowania → strategia nowa do analizy ręcznej.

Uwaga: sortowanie bąbelkowe i przez wstawianie robią tyle samo zamian (liczba inwersji), więc odróżnia je kolejność
operacji, nie ich liczba. Dla wież Hanoi i wyszukiwania metoda jest inna (odchylenie od optimum, ciąg odczytywanych
indeksów) i dochodzi później.

Przed badaniem analizator przechodzi walidację na syntetycznych przebiegach z `data/synthetic/`: co najmniej
6 algorytmów, trafność co najmniej 95%. Próg i reguła hybrydy są w `docs/protocol/`.

## Język i narzędzia

Python 3.13, pakiet `algotrace_analyzer` w workspace uv repozytorium. Główne biblioteki:

- `rapidfuzz`: znormalizowana odległość edycyjna na ciągach operacji;
- `scikit-learn`: n-gramy operacji, drugi sposób porównania z wzorcami;
- `jsonschema`: odczyt zapisów przebiegu zgodnych ze `schemas/`;
- `networkx` tylko w testach: sprawdza porównania zbędne, które kod liczy własnym grafem relacji.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy powstanie kod analizatora. Z katalogu głównego repozytorium:

```
uv sync --locked --all-packages
uv run --locked python -m algotrace_analyzer ...
uv run --locked pytest tests/python/analyzer
```
