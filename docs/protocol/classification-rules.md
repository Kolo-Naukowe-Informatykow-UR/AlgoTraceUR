# Reguły klasyfikacji strategii

Status: **przed pilotażem** (2026-11-20). Reguły są stałe; wartości progów kalibruje się na przebiegach
syntetycznych przed pełnym badaniem i zamraża w sekcji 12 (D06 A). Zmiana reguły po zamrożeniu jest odstępstwem od
preregistracji i trafia do historii w [README](README.md) i do raportu.

Decyzje protokołu ([README.md](README.md), sekcja „Zakres”) zastosowane w tym pliku: D06 A (progi kalibrowane na syntetycznych, zamrożone; reguła hybrydy),
D07 A (definicje KPI analizatora), D04 A (tury z kilkoma wywołaniami). Implementacja: `src/analyzer/` (najpierw sortowanie,
potem Hanoi i wyszukiwanie), walidacja analizatora, algorytmy wzorcowe w `src/references/`.

## 1. Etykiety

| Rodzina | Etykiety |
|---|---|
| sortowanie | `known:<algorytm>` (z wariantem jako informacją dodatkową), `hybrid:<A>+<B>[+...]` (w kolejności odcinków), `ambiguous:<A>\|<B>`, `new` (z podtypem `new:info_first` albo `new:other`), `failed:<typ>` |
| Hanoi | `optimal`, `optimal_detours`, `other`, `failed:<typ>` |
| wyszukiwanie | `known:<wzorzec>`, `ambiguous:<A>\|<B>`, `other`, `too_short`, `failed:<typ>` |

Etykieta strategii dotyczy przebiegu z osiągniętym stanem docelowym; przebieg nieudany dostaje typ porażki
(sekcja 2), a etykietę strategii tylko eksploracyjnie (sekcja 2, ostatni punkt).

## 2. Przebieg nieudany i rodzaj błędu

- **Sortowanie i Hanoi:** przebieg jest klasyfikowany jako strategia, gdy stan końcowy jest docelowy (`solved: true`,
  także przy `step_limit` bez `done`); inaczej dostaje `failed:<typ>` według `end_reason`
  ([run-settings.md](run-settings.md), sekcja 8): `failed:wrong_done` (`done_unsolved`), `failed:step_limit`,
  `failed:errors` (`too_many_errors`), `failed:no_tool_call`, `failed:context`, a `failed:infra` dla `api_error`,
  `time_limit`, `cost_limit` i `interrupted` (to nie porażka modelu, [analysis-plan.md](analysis-plan.md)).
- **Wyszukiwanie:** strategia dla `done_solved`; `failed:wrong_done` z podtypem `false_absent` (odpowiedź -1, liczba
  jest w tablicy), `false_present` (pozycja, liczby nie ma) albo `wrong_index` (zła pozycja); pozostałe jak wyżej.
- **Opis porażki (wszystkie rodziny):** liczniki błędów walidacji według rodzaju, najdłuższa seria błędów, a w
  sortowaniu dodatkowo zamiany szkodliwe (zamiana, która zwiększa liczbę inwersji, czyli błędne odczytanie wyniku
  `compare` albo zgadywanie) i liczba inwersji w stanie końcowym; w Hanoi odległość do celu w stanie końcowym
  (sekcja 7).
- **Strategia przebiegu nieudanego (eksploracyjnie):** gdy przebieg ma co najmniej `2N` wykonanych operacji
  (Hanoi: `2^(n-1)`), ślad porównuje się z prefiksami wzorców tej samej długości (tryb prefiksowy, sekcja 3); wynik
  idzie tylko do analiz eksploracyjnych.

## 3. Tokeny i odległość (sortowanie)

- **Tokeny:** tylko wywołania wykonane (`executed: true`) poza `done`, w kolejności wykonania: `C(i,j)` dla
  `compare` i `S(i,j)` dla `swap`, z indeksami w porządku `(min, max)`, bo `compare(j, i)` niesie tę samą informację co
  `compare(i, j)`, a zamiana jest symetryczna. Błędy walidacji i błędy wstrzyknięte nie są tokenami (nie zmieniają
  stanu); liczy się je osobno.
- **Wzorce na tej samej instancji:** każdy algorytm wzorcowy w każdym wariancie uruchamia się na instancji przebiegu
  (`src/references/`): bąbelkowe, przez wstawianie, przez wybór, szybkie, scalanie w miejscu, koktajlowe (co najmniej te 6,
  KPI); warianty: kierunek, wczesne zakończenie, wybór osi (pierwsza, ostatnia, środkowa, mediana z trzech).
- **Odległość:** `d(t, r) = Levenshtein(t, r) / max(len(t), len(r))` na listach tokenów (wstawienie, usunięcie,
  podstawienie po 1). Odległość do algorytmu to minimum po jego wariantach; wariant z tym minimum jest zapisany obok
  etykiety.
- **Nadmiar długości:** `len(t) / len(r*)` dla najbliższego wariantu, raportowany osobno, bo duża liczba porównań
  zbędnych zaniża podobieństwo strukturalne.
- **Tryb prefiksowy** (przebiegi nieudane, odcinki hybryd, odcinek przed błędem wstrzykniętym): odległość od
  najlepiej pasującego prefiksu wzorca, `min_m Levenshtein(t, r[0..m]) / max(len(t), m)`.

## 4. Klasyfikacja przebiegu udanego (sortowanie)

Dla progu `tau_N` (osobny dla każdego rozmiaru N, sekcja 6) i marginesu `delta = 0,02`:

1. Policz `d_A` dla każdego algorytmu A; niech `A1` ma najmniejszą odległość, a `A2` drugą najmniejszą (inny algorytm).
2. Jeśli `d_A1 <= tau_N`:
   - gdy `d_A2 - d_A1 < delta` i także `d_A2 <= tau_N`, etykieta `ambiguous:A1|A2` (na tej instancji wzorce są prawie
     nie do odróżnienia, np. identyczne ślady dwóch algorytmów);
   - inaczej `known:A1`.
3. Jeśli `d_A1 > tau_N`: reguła hybrydy (sekcja 5); gdy hybryda nie spełnia warunków, etykieta `new`.
4. Podtyp `new`: `new:info_first`, gdy co najmniej 80% porównań przebiegu jest przed pierwszą zamianą i liczba zamian
   nie przekracza `N - c + 2` (`c` to liczba cykli permutacji początkowej; `N - c` to minimum zamian dowolnych par),
   czyli model najpierw ustala kolejność, a potem ją stosuje (hipoteza z research design); inaczej `new:other`.

`delta = 0,02` (dwie edycje na 100 tokenów) jest ustalone z góry, a nie kalibrowane: poniżej tej różnicy decyduje
szum zakłóceń (jedno-dwa porównania zbędne w śladzie długości 100). Odsetek etykiet `ambiguous` raportuje się
w walidacji i w wynikach.

## 5. Reguła hybrydy (D06 A)

Dla śladu `t` długości `L`, którego żaden pojedynczy wzorzec nie spełnia progu:

- **Segmentacja programowaniem dynamicznym:** `best[0] = 0`,
  `best[k] = min_{j < k, A} ( best[j] + (k - j) * d_A(t[j..k] | stan_j) + lambda )`, gdzie `stan_j` to tablica po
  wykonaniu `t[0..j)`, a `d_A(t[j..k] | stan_j)` to odległość odcinka od wzorca A uruchomionego od `stan_j`: dla
  ostatniego odcinka (`k = L`) od pełnego śladu wzorca (do posortowania), dla wcześniejszych w trybie prefiksowym
  (sekcja 3). Odległość ważona długością odcinka sumuje się do „liczby edycji”, a `lambda` (kara zmiany, w tokenach)
  dodaje się za każdy odcinek. Sąsiednie odcinki tego samego algorytmu łączy się.
- **Hybryda**, gdy wszystkie warunki są spełnione:
  1. co najmniej 2 odcinki różnych algorytmów;
  2. każdy odcinek ma `d_A <= tau_N`;
  3. każdy odcinek ma co najmniej `m_min` tokenów;
  4. koszt segmentacji `best[L]` jest mniejszy niż koszt najlepszego pojedynczego wzorca `L * d_A1 + lambda`.
- Etykieta `hybrid:A+B[+...]` w kolejności odcinków; punkty podziału są zapisane (do pytania 5 i do opisu
  przypadków).
- Gdy któryś warunek nie jest spełniony: `new` (z podtypem z sekcji 4).

## 6. Kalibracja progów (D06 A)

**Dane:** przebiegi syntetyczne z generatora w `src/references/` na instancjach z własnym ziarnem bazowym (nigdy instancje
pilotażu ani pełnego badania): każdy algorytm i wariant, N = 5, 10, 20, ślady czyste i z zakłóceniami (wstawione
porównanie zbędne, pominięty krok, zamieniona kolejność sąsiednich operacji; poziom zakłóceń 0, 5% i 10% tokenów),
oraz hybrydy sklejone w znanym punkcie (algorytm A do punktu podziału, potem B od stanu w tym punkcie; punkt losowany
z `[0,25 L, 0,75 L]`). Ziarna zakłóceń i punktów podziału są w zapisie śladu.

**Podział po instancjach:** część kalibracyjna (60% instancji) i część testowa (40%); żadna instancja nie jest
w obu częściach (`StratifiedGroupKFold` albo podział po `instance_id`). Część testowa służy tylko KPI (sekcja 11).

**Krok 1, próg `tau_N`** (osobno dla każdego N, tylko ślady pojedynczych algorytmów):

- Siatka `tau` od 0,00 do 0,50 co 0,01.
- Dla każdego algorytmu L z zestawu: ślady L klasyfikuje się zestawem wzorców bez L (L „pominięty”, więc jego ślady
  powinny dostać `new`), a ślady pozostałych algorytmów pełnym zestawem; wyniki 6 rund się sumuje.
- Miarą jest F1 makro po 7 klasach (6 algorytmów i `new`); `ambiguous` liczy się jako błąd. Wybrany `tau_N` ma
  największe F1 makro; przy remisie mniejszy (ostrożniej wobec przypisania).

**Krok 2, `lambda` i `m_min`** (przy zamrożonym `tau_N`, ślady pojedyncze i hybrydy z części kalibracyjnej):

- Siatka `lambda` z {1, 2, 3, 5, 8} tokenów, `m_min` z {N, 2N, 4N} tokenów.
- Miarą jest F1 makro po klasach: każdy algorytm, `hybrid` i `new` (ślady pominiętego algorytmu jak w kroku 1).
  Hybryda jest trafiona, gdy zgadzają się algorytmy i ich kolejność, a punkt podziału leży najwyżej N tokenów od
  prawdziwego. Wybór: największe F1 makro, przy remisie większe `lambda` i większe `m_min` (ostrożniej wobec hybryd).

**Hanoi i wyszukiwanie:** ta sama procedura z własnymi progami (sekcje 7 i 8).

**Zamrożenie:** wartości trafiają do sekcji 12 z datą, wersją analizatora (commit) i odnośnikiem do raportu walidacji
analizatora, przed preregistracją i przed pierwszym przebiegiem pełnego badania. Progi nie zmieniają
się po obejrzeniu przebiegów modeli; ślady pilotażu służą tylko do sprawdzenia, czy reguły dają się zastosować
(odsetek `new` i `ambiguous`), nie do strojenia wartości.

## 7. Hanoi

- **Tokeny:** `M(from,to)` dla wykonanych `move`, w kolejności.
- **Wzorzec:** jedyne optymalne rozwiązanie z pozycji startowej (`2^n - 1` ruchów; rozwiązanie rekurencyjne i iteracyjne
  „najmniejszy krążek co drugi ruch w stałym kierunku” dają ten sam ciąg).
- **Etykiety przebiegu udanego:** `optimal`, gdy ciąg równa się wzorcowi; `optimal_detours`, gdy
  `d(t, wzorzec) <= tau_H` (wzorzec z objazdami: kilka ruchów zbędnych albo cofniętych); `other`, gdy `d > tau_H`.
- **Kalibracja `tau_H`** (jedna wartość dla n = 3, 4, 5): klasy „wzorzec z zakłóceniami” (optymalny ciąg ze wstawionymi
  parami ruch-cofnięcie i objazdami, 5% i 10% ruchów) i „inna strategia” (losowe legalne błądzenie z odchyleniem
  w stronę celu, które dochodzi do celu), siatka i F1 makro jak w sekcji 6.
- **Cechy opisowe:** ruchy ponad optimum, cofnięcia (ruch odwrotny do poprzedniego), czy najmniejszy krążek rusza się
  co drugi ruch w stałym kierunku, odległość do celu po każdym ruchu (algorytm z notatki o rozpoznawaniu: od
  największego krążka, `2^(k-1)` za każdy krążek poza bieżącym celem) i liczba ruchów, które ją zwiększają.

## 8. Wyszukiwanie

- **Sondy:** wykonane `read(index)` w kolejności, z odczytanymi wartościami. Po każdej sondzie odtwarza się przedział
  `[lo, hi]` pozycji, na których szukana liczba jeszcze może być.
- **Wzorce (w każdym kroku przewidywana sonda z tego samego stanu wiedzy, co model):** połowienie przedziału z dolnym
  środkiem `floor((lo + hi) / 2)` i z górnym środkiem, interpolacja `lo + (target - a[lo]) * (hi - lo) / (a[hi] - a[lo])`
  (z wartości już znanych; przed pierwszymi odczytami skrajnych pozycji ich przewidywaniem jest odczyt skrajnej
  pozycji), liniowe od lewej i od prawej, skokowe (krok `floor(sqrt(N))`, potem liniowo), wykładnicze (1, 2, 4, ...,
  potem połowienie).
- **Odchylenie:** `dev_P = średnia po sondach |p_t - pred_P,t| / N`. Etykieta `known:P` dla najmniejszego `dev_P`, gdy
  `dev_P <= tau_S`; `ambiguous:P1|P2`, gdy różnica dwóch najmniejszych jest poniżej `delta = 0,02`; `other`, gdy
  `dev_P > tau_S`.
- **`too_short`:** przebieg z co najwyżej 2 sondami (np. trafienie w pierwszej sondzie) nie ma etykiety strategii;
  liczba takich przebiegów jest raportowana.
- **Kalibracja `tau_S`** (jedna wartość dla trzech N): sondy wzorców z zakłóceniami (dodatkowe losowe odczyty 5%
  i 10%, przesunięcie sondy o 1), pominięcie wzorca jak w sekcji 6, F1 makro.
- **Miary opisowe:** liczba odczytów wobec `ceil(log2(N + 1))`, odczyty zbędne (indeks poza przedziałem `[lo, hi]`
  albo odczyt powtórzony).

## 9. Tury z kilkoma wywołaniami i odcinki przed błędem i po nim

- **Kilka wywołań w turze (D04 A):** tokeny idą w kolejności wykonania (kolejność z odpowiedzi); granice tur nie
  zmieniają odległości. Numer tury i pozycja w turze są zapisane osobno i służą jako cechy opisowe: odsetek tur
  z kilkoma wywołaniami, średnia liczba wywołań w turze, odsetek porównań wysłanych w jednej turze bez zamian (model nie
  zna wtedy wyników przed wysłaniem kolejnych). Przebiegi, w których ponad połowa wywołań jest w turach wielowywołaniowych,
  raportuje się w analizie wrażliwości osobno ([analysis-plan.md](analysis-plan.md)), bo kolejność porównań w jednej
  turze nie niesie informacji, a liczy się do odległości.
- **Odcinki przy błędzie wstrzykniętym** ([fault-injection.md](fault-injection.md)): ślad dzieli się w miejscu
  pierwszego wywołania z błędem; odcinek przed błędem klasyfikuje się w trybie prefiksowym od stanu początkowego,
  odcinek po błędzie od stanu w chwili błędu do końca (pełny wzorzec), oba progami `tau_N` i regułą z sekcji 4 (bez
  reguły hybrydy wewnątrz odcinka). Odcinek krótszy niż `m_min` dostaje `too_short`. Ten sam podział stosuje się
  w przebiegu-parze z serii głównej.

## 10. Strategia nowa i kodowanie ręczne

- Kodują dwie osoby z zespołu niezależnie, bez nazwy modelu i bez tekstu deklaracji (żeby deklaracja nie sugerowała
  etykiety), na podstawie śladu, stanów i cech opisowych.
- Kodowane są: wszystkie przebiegi `new` i `ambiguous` oraz losowa próbka 10% przebiegów `known` i `hybrid` (ziarno
  próbki w zapisie analizy) jako kontrola przeniesienia progów z danych syntetycznych na ślady modeli.
- Księga kodów: algorytmy wzorcowe, hybryda (z algorytmami i przybliżonym punktem zmiany), `info_first`, inna strategia
  z krótkim opisem, „niejasne”. Zgodność koderów: surowa i kappa Cohena z przedziałem, macierz pomyłek; rozbieżności
  rozstrzyga rozmowa, a etykieta po rozmowie jest ostateczną etykietą ręczną.
- Zgodność analizatora z kodowaniem ręcznym na próbce 10% raportuje się (surowa, kappa); etykieta analizatora zostaje
  etykietą analizy głównej, a etykiety ręczne `new` są analizą eksploracyjną ([analysis-plan.md](analysis-plan.md)).

## 11. KPI analizatora (D07 A)

- **KPI 1, trafność co najmniej 95%:** na części testowej przebiegów syntetycznych (sekcja 6) ze śladami pojedynczych
  algorytmów, czystymi i z zakłóceniami, wszystkie 6 algorytmów i N = 5, 10, 20, co najmniej 40 śladów testowych na
  algorytm (razem co najmniej 240). Trafność to odsetek śladów, w których rozpoznany algorytm jest algorytmem, który
  ślad wygenerował; `ambiguous`, `new` i `hybrid` liczą się jako błąd. KPI jest spełniony, gdy **dolna granica
  dwustronnego 95% przedziału Wilsona** trafności jest co najmniej 0,95 (przy 240 śladach wystarcza to przy najwyżej
  5 błędach). Raport: trafność z przedziałem Wilsona i Cloppera-Pearsona, macierz pomyłek, F1 na klasę i F1 makro,
  osobno dla każdego N; hybrydy i algorytmy pominięte raportuje się obok, poza KPI.
- **KPI 2, przypisanie strategii dla co najmniej 90% udanych przebiegów sortowania:** mianownik to przebiegi
  sortowania serii głównej z `end_reason: done_solved` (wszystkie modele i N), licznik to te z etykietą `known` albo
  `hybrid` (bez `new` i `ambiguous`). KPI jest spełniony, gdy ten odsetek wynosi co najmniej 0,90; raportuje się go
  z dwustronnym 95% przedziałem Wilsona, ogółem, na model i na N.

## 12. Wartości zamrożone

Wypełnia się w walidacji analizatora przed pełnym badaniem; do tego czasu wartości są puste.

| Parametr | Wartość | Data | Wersja analizatora | Raport walidacji |
|---|---|---|---|---|
| `tau_5`, `tau_10`, `tau_20` | | | | |
| `lambda`, `m_min` | | | | |
| `tau_H` | | | | |
| `tau_S` | | | | |
| `delta` | 0,02 (z góry, sekcja 4) | 2026-11-20 | - | - |
