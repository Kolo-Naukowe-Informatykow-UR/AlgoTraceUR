# src/references

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
