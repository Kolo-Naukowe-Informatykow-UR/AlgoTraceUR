# experiments

Zapisane konfiguracje eksperymentów w formacie z `schemas/`. Każdy przebieg ma dać się powtórzyć jednym poleceniem
z konfiguracji z tego folderu.

Planowany podział (podfoldery powstają razem z pierwszą konfiguracją):

- `pilot/`: pilotaż na 1-2 modelach, do sprawdzenia całego łańcucha i kosztu;
- `study/`: pełne badanie według protokołu z `docs/protocol/`.

Konfiguracja nigdy nie zawiera klucza API, tylko nazwę zmiennej środowiskowej. Konfiguracji użytej w badaniu się nie
zmienia: nowa wersja to nowy plik.
