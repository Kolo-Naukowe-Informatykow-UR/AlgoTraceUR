# tests

Testy modułów z `src/`. Układ wewnątrz folderu (jeden podfolder na moduł albo testy obok kodu) idzie za zwyczajem
języka wybranego dla modułu.

Testy, które muszą być niezależnie od języka:

- algorytmy wzorcowe dają znane liczby kroków (np. dla `[4, 6, 3, 1, 2]`: bąbelkowe 10 porównań i 8 zamian, przez
  wstawianie 10 i 8, przez wybór 10 i 2);
- pliki zapisywane przez moduły są zgodne ze schematami z `schemas/`;
- analizator rozpoznaje syntetyczne przebiegi wzorców (walidacja z progiem z `docs/protocol/`);
- generator zadań daje te same dane dla tego samego ziarna.

Testy nie wołają płatnych API; modele zastępuje atrapa zgodna z kontraktem danych.
