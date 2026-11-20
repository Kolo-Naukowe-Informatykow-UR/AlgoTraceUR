# Oś czasu projektu

Harmonogram AlgoTrace od 20.11.2026 do 30.07.2027: sześć etapów, terminy KPI z terminami wewnętrznymi i buforami,
piątki raportów oraz kalendarz akademicki UR 2026/2027 jako okresy niższej aktywności. Stan: 20.11.2026. Kolejność
programów i kryteria „gotowe” podaje [work-plan.md](work-plan.md) i on wygrywa, gdy plik się z nim różni; bieżący stan
prac niosą karty zespołu w urwisie (projekt AlgoTraceUR, klucz `ALGO`). Ustalenia z pierwszego spotkania:
[notatka](../meetings/2026-11-20-pierwsze-spotkanie.md).

## 1. Etapy

Do 23.12.2026 kod w `src/environment/` pisze tylko lider (środowisko bazowe pochodzi z projektu zaliczeniowego lidera);
reszta zespołu pracuje na atrapach z `schemas/examples/` i na kontrakcie danych. Etapy zachodzą na siebie, bo programy
są niezależne (zob. [work-plan.md](work-plan.md), sekcja 2).

| Etap | Daty | Cel | Główna praca | Kończy się |
|---|---|---|---|---|
| 1. Start i fundamenty | 20.11-18.12.2026 | zespół działa, decyzje podjęte | dostęp do repozytorium i urwisu, dzień raportu, licencje, stos, kontrakt danych, test modeli lokalnych, LaTeX, algorytmy wzorcowe | raport 18.12.2026 |
| 2. Kod do KPI 1 | 5.12.2026-22.01.2027 | środowisko i walidacja | analizator sortowania, adaptery dostawców, rozdział 1; od 24.12 przeniesienie środowiska do repozytorium koła | walidacja analizatora 22.01.2027 |
| 3. Seria i pilotaż | 23.01-19.03.2027 | seria działa na prawdziwym środowisku | uruchamianie serii, analizator wież Hanoi i wyszukiwania, pilotaż, kosztorys z pomiaru, wybór konferencji | pilotaż 19.03.2027 |
| 4. Pełne badanie | 27.03-7.05.2027 | min. 500 przebiegów na 6 modelach | konfiguracja modeli i budżet, przebiegi w krótkim oknie (ok. 12.04-2.05) | przebiegi 7.05.2027 |
| 5. Analiza, tekst, zbiór, referat | 20.03-11.06.2027 | wyniki gotowe do publikacji | skrypty analizy (najpierw na pilotażu), analiza wyników, pełny tekst, publiczny zbiór, zgłoszenie referatu | referat 11.06.2027 |
| 6. Zakończenie | 19.06-30.07.2027 | projekt zamknięty w kole | prezentacja wyników na spotkaniu koła, raport końcowy | zakończenie 30.07.2027 |

Punkty pośrednie: środowisko w repozytorium koła 15.01.2027, analiza wyników 21.05.2027, tekst i zbiór 4.06.2027,
wybór konferencji 26.02.2027.

## 2. KPI i terminy wewnętrzne

| KPI | Termin KPI | Termin wewnętrzny | Bufor | Uwagi |
|---|---|---|---|---|
| Środowisko z 3 rodzinami zadań; walidacja analizatora co najmniej 95% | 31.01.2027 (nd.) | 22.01.2027 | 9 dni | KPI wypada w sesji zimowej; realnie zamykamy przed końcem zajęć 24.01 |
| Pełne badanie: min. 500 przebiegów na 6 modelach | 31.05.2027 (pn.) | 7.05.2027 | 24 dni | bufor na powtórki; okno przebiegów krótkie przez ciche aktualizacje modeli |
| Publiczny zbiór, tekst badania, zgłoszenie referatu | 30.06.2027 (śr.) | 4-11.06.2027 | 19-26 dni | wszystko przed sesją letnią (14-27.06) |
| Zakończenie w kole (prezentacja wyników) | 30.07.2027 (pt.) | 16.07.2027 | 14 dni | wakacje; tryb pracy uzgodnić z góry |

Raport końcowy: do 30 dni po zakończeniu, czyli najpóźniej 29.08.2027.

## 3. Piątki raportów

Raport co 2 tygodnie w piątek, od 4.12.2026 (ustalenie z pierwszego spotkania). Terminy kart wypadają na te piątki,
żeby każdy raport zamykał karty.

- 2026: 4.12, 18.12.
- 2027, styczeń-luty: 1.01 (przerwa świąteczna, dzień wolny: tryb uzgodniony), 15.01, 29.01 (sesja zimowa), 12.02
  (przerwa międzysemestralna).
- 2027, marzec-maj: 26.02, 12.03, 26.03 (przerwa wielkanocna: tryb uzgodniony), 9.04, 23.04, 7.05, 21.05.
- 2027, czerwiec-lipiec: 4.06, 18.06 (sesja letnia), 2.07 (wakacje), 16.07 (wakacje), 30.07 (zakończenie).

## 4. Kalendarz akademicki UR 2026/2027

Źródło: zarządzenie nr 72/2026 Rektora UR w sprawie organizacji roku akademickiego 2026/2027
([PDF](https://www.ur.edu.pl/files/user_directory/580/Student/Pliki%20do%20pobrania/Regulaminy%20i%20zarz%C4%85dzenia/Organizacja%20roku%20akademickiego%202026-2027.pdf)).
Przerwy i sesje to okresy obniżonej aktywności: reguła 14 dni bez postępu nie obowiązuje, a tryb raportów w tych
okresach uzgadnia się z Przewodniczącym koła.

| Okres | Daty | Co to znaczy dla pracy |
|---|---|---|
| Zajęcia zimowe | 1.10-23.12.2026 i 4-24.01.2027 | normalne tempo; lider oddaje środowisko bazowe do 23.12 |
| Przerwa świąteczna | 24.12.2026-3.01.2027 | niższa aktywność; lider przenosi środowisko do repozytorium; dni wolne 24-26.12, 1.01 |
| Sesja zimowa | 25.01-7.02.2027 | niższa aktywność; KPI 1 zamknięte wcześniej; 6.01 dzień wolny |
| Przerwa międzysemestralna | 8-14.02.2027 | niższa aktywność; seria działa w tle |
| Sesja poprawkowa | 15-21.02.2027 | niższa aktywność; termin serii dopiero 26.02 |
| Semestr letni | 22.02-13.06.2027 | normalne tempo, pilotaż i pełne badanie |
| Przerwa wielkanocna | 25-31.03.2027 | niższa aktywność; dni wolne 28-29.03; start pełnego badania po niej |
| Dni wolne w maju | 1.05, 3.05, 27.05.2027 | bez pracy; piątek 7.05 nadal raportowy |
| Sesja letnia | 14-27.06.2027 | niższa aktywność; referat i zbiór zamknięte przed nią |
| Wakacje | od 28.06.2027 | niższa aktywność; obejmują zakończenie 30.07.2027 i raport końcowy |

Wariant do sprawdzenia: ostatni semestr studiów inżynierskich może mieć sesję wcześniej (4-17.01.2027, poprawka
25-31.01.2027). Gdyby obowiązywał lidera, środowisko trzeba przenieść do 3.01.2027. Listę dni wolnych sprawdzić
w komunikatach UR.

## 5. Jak przesunąć termin

1. Zmień datę najpierw w tym pliku (etap, KPI, piątek raportu) i sprawdź bufor do KPI.
2. Potem zmień termin karty w urwisie (projekt `ALGO`) i zależnych kart.
3. Jeśli zmiana dotyka kolejności programów albo kryteriów „gotowe”, zmień [work-plan.md](work-plan.md) i wpisz decyzję
   zespołu.
4. Przesunięcie, które zjada bufor przed KPI, zgłoś na najbliższym raporcie.
