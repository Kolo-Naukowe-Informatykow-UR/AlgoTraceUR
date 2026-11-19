# src/environment

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
