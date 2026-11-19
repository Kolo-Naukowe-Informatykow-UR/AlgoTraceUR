# src/runner

Uruchamianie serii eksperymentów: program czyta konfigurację z `experiments/` (dostawca, model, zadanie, N,
ziarno, prompt, ustawienia, limity, ścieżki wyników), uruchamia przebiegi (modele × zadania × N × powtórzenia)
w środowisku i zapisuje zapisy przebiegów oraz wiersze wyników do `data/`.

Wymagania:

- jeden przebieg albo cała seria jednym poleceniem z zapisanej konfiguracji;
- seria w tle, wznawiana po przerwaniu bez powtarzania gotowych przebiegów;
- limit kosztu: seria staje po przekroczeniu ustalonego budżetu.

Powtórzenie przebiegu oznacza uruchomienie tej samej konfiguracji z tym samym ziarnem; odpowiedź modelu może się
różnić, więc źródłem analizy jest zawsze zapis przebiegu.
