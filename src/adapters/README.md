# src/adapters

Adaptery dostawców modeli za jednym wspólnym interfejsem: środowisko wysyła wiadomości i opis narzędzi, adapter
zwraca odpowiedź modelu i żądane wywołania narzędzi, niezależnie od API dostawcy.

Co tu trafi:

- adapter na każdego dostawcę (co najmniej 3) i co najmniej 1 dla modelu uruchamianego lokalnie;
- ten sam opis narzędzi i ten sam prompt dla wszystkich dostawców;
- zapis tokenów, wersji modelu, czasu i błędów API (do zapisu przebiegu);
- obsługa limitów zapytań: ponowienie z przerwą;
- klucze API tylko ze zmiennych środowiskowych.

Różnice między dostawcami, których adapter nie ukryje, opisujemy w `docs/`. Lista dostawców i modeli jest jeszcze
otwarta.
