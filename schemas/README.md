# schemas

Kontrakt danych: formaty plików, przez które łączą się wszystkie moduły. Moduł nie korzysta z kodu innego modułu,
tylko z tych formatów, więc moduły mogą powstać w różnych językach.

Co tu trafi (schematy, np. JSON Schema, każdy z przykładem obok):

| Format | Kto zapisuje | Kto czyta | Zawartość |
|---|---|---|---|
| konfiguracja eksperymentu | zespół (`experiments/`) | uruchamianie serii | dostawca, model i jego wersja, zadanie, N, ziarno, prompt, ustawienia, limity, ścieżki wyników; klucz API tylko jako nazwa zmiennej środowiskowej |
| zapis przebiegu | środowisko | analizator, analiza wyników | jedno zdarzenie na krok: numer kroku i tury, narzędzie, argumenty, wynik, błąd walidacji, tekst modelu, tokeny, czas |
| wiersz wyników | uruchamianie serii | analiza wyników | jeden wiersz na przebieg (CSV): konfiguracja, sukces, liczby wywołań, tokeny, koszt |
| wynik analizatora | analizator | analiza wyników | cechy, miary, odległości od wzorców, przypisana strategia |

Pierwszy przykład do przygotowania: przebieg sortowania bąbelkowego tablicy `[4, 6, 3, 1, 2]` (10 porównań,
8 zamian).

Zmiana formatu to zmiana wersji schematu; stare zapisy przebiegów muszą dać się dalej odczytać.
