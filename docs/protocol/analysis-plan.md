# Plan analizy wyników

Status: **przed pilotażem** (2026-11-20). Po pilotażu plan uzupełnia się o symulację mocy (sekcja 9)
i zamraża w preregistracji na OSF; analizę wykonuje program `src/analysis/`. Zmiana po zamrożeniu jest
odstępstwem i trafia do raportu.

Decyzje protokołu ([README.md](README.md), sekcja „Zakres”) zastosowane w tym pliku: D01 (deklaracja, pytanie 3), D02 (błędy, pytanie 5), D07 (KPI
analizatora). Reguły etykiet: [classification-rules.md](classification-rules.md); układ i liczby przebiegów:
[design.md](design.md); powody końca: [run-settings.md](run-settings.md), sekcja 8.

## 1. Definicje wspólne

- **Jednostka:** przebieg (jeden model, jedna instancja, jeden warunek, ostatnia próba przebiegu po `api_error`).
- **Sukces (analiza główna):** `end_reason: done_solved`, czyli model sam ogłosił koniec przy poprawnym stanie
  (wyszukiwanie: poprawna odpowiedź). Zadanie wymaga ogłoszenia końca, więc przebieg z posortowaną tablicą bez `done`
  nie jest sukcesem głównym.
- **Sukces (wrażliwość):** `solved: true` na końcu bez względu na `done`.
- **Porażki modelu:** `done_unsolved`, `step_limit`, `too_many_errors`, `no_tool_call`, `context_exceeded` (to także
  porażka: model nie skończył w kontekście, z którym działa w badaniu).
- **Braki danych (nie porażki modelu):** `api_error` po 3 próbach, `time_limit`, `cost_limit`, `interrupted`. Analiza
  główna je pomija (przypadki pełne); liczba braków jest w raporcie na komórkę; wrażliwość liczy je jako porażki.
- **Klaster:** treść instancji. W sortowaniu i wyszukiwaniu każda instancja jest inna (w serii głównej 30 instancji
  sortowania i 30 wyszukiwania), a 10 instancji jednej komórki Hanoi ma tę samą treść ([design.md](design.md)),
  więc Hanoi daje 3 klastry (po jednym na n). Razem 63 klastry, powyżej progu około 30, poniżej którego błędy
  kanapkowe są zaniżone.
- **Rozmiar w modelach:** poziom rozmiaru w zadaniu (mały, średni, duży = 1, 2, 3) jako czynnik, z interakcją
  z zadaniem, bo N sortowania, n Hanoi i N wyszukiwania nie są na jednej skali.
- **Przedział dla proporcji:** dwustronny 95% Wilsona (`proportion_confint(method="wilson")`); Wald nigdy;
  Clopper-Pearson tylko jako sprawdzenie progów KPI.
- **Poziom istotności:** 0,05 dwustronnie w każdej rodzinie hipotez potwierdzających, z poprawką Holma wewnątrz
  rodziny; analizy eksploracyjne z poprawką Benjaminiego-Hochberga (FDR 0,05) w obrębie jednej tabeli.

## 2. Hipotezy potwierdzające (do preregistracji)

| Rodzina | Hipoteza | Test | Poprawka |
|---|---|---|---|
| F1 | H1: skuteczność zależy od modelu | GEE (sekcja 3), test Walda czynnika modelu (6 stopni swobody) | Holm w F1 (4 testy) |
| F1 | H2a-H2c: skuteczność zależy od rozmiaru w sortowaniu, Hanoi i wyszukiwaniu | GEE, test Walda poziomu rozmiaru w każdym zadaniu (2 st. sw.), kierunek z estymat | Holm w F1 |
| F2 | H3: pary modeli różnią się skutecznością | 21 kontrastów par z GEE (efekt modelu uśredniony po zadaniach i rozmiarach) | Holm w F2 (21 testów) |
| F3 | H4: rozkład strategii w udanych przebiegach sortowania zależy od modelu | test permutacyjny statystyki chi-kwadrat, permutacja modeli wewnątrz instancji (10 000 permutacji) | Holm w F3 (2 testy) |
| F3 | H5: rozkład strategii w udanych przebiegach sortowania zależy od N | test permutacyjny, permutacja N wewnątrz modelu | Holm w F3 |
| F4 | H6a, H6b: błąd jednorazowy i błąd trwały obniżają skuteczność | dokładny test McNemara w parach (przebieg z błędem i przebieg tego samego modelu na tej samej instancji w serii głównej) | Holm w F4 (4 testy) |
| F4 | H7a, H7b: po błędzie jednorazowym i trwałym strategia zmienia się częściej niż w tym samym miejscu bez błędu | dokładny test McNemara w parach (zmiana etykiety w przebiegu z błędem i w przebiegu-parze) | Holm w F4 |

Pytania 3 i 4 są opisowe (estymaty z przedziałami, sekcje 5 i 6), bez testu potwierdzającego: nie ma z góry
uzasadnionej wartości, z którą trzeba by je porównać.

## 3. Pytanie 1: skuteczność

- **Opis:** skuteczność na konfigurację (model x zadanie x rozmiar, n = 10) z przedziałem Wilsona, także na model
  x zadanie (n = 30) i na model (n = 90). Pojedyncza konfiguracja służy opisowi, nie porównaniom (przedział szerokości
  około 0,45-0,55).
- **Spójność:** `pass^k` na konfigurację dla k = 3 i 5, estymator nieobciążony `C(c, k) / C(n, k)` (c sukcesów
  z n = 10 powtórzeń), oraz `pass@k` jako granica optymistyczna. Przy nowej instancji w każdym powtórzeniu `pass^k`
  mierzy spójność modelu na rodzinie instancji, nie na jednej instancji.
- **Model główny:** GEE z funkcją logit, rozkład dwumianowy, korelacja wymienna, klaster = treść instancji (sekcja 1),
  błędy kanapkowe; zmienne: model (7 poziomów), zadanie (3), poziom rozmiaru (3), interakcja zadanie x rozmiar.
  Sprawdzenie: regresja logistyczna z tymi samymi zmiennymi i błędami klastrowanymi (`cov_type="cluster"`).
- **Pary modeli (H3):** kontrasty z GEE; obok efekt w skali proporcji: różnica proporcji w parach (te same
  instancje) z przedziałem Newcombe'a dla danych sparowanych i h Cohena `2 arcsin sqrt(p1) - 2 arcsin sqrt(p2)`
  (progi 0,2 / 0,5 / 0,8 tylko orientacyjnie).
- **Separacja** (model z 0% albo 100% skuteczności w jakimś zadaniu, przy którym GEE nie zbiega): regresja
  logistyczna z karą Firtha i przedziały z bootstrapu klastrowego po instancjach (2000 prób); decyzja zapisana
  w raporcie.
- **Eksploracyjnie:** pary modeli w każdym zadaniu i rozmiarze (21 x 9 kontrastów, BH), dostawca jako czynnik zamiast
  modelu, rozumowanie (z / bez) jako czynnik.

## 4. Pytanie 2: algorytm

- **Jednostka:** udany przebieg sortowania serii głównej (`done_solved`); wrażliwość: także `solved: true` bez `done`.
- **Opis:** rozkład etykiet ([classification-rules.md](classification-rules.md): `known` według algorytmu, `hybrid`,
  `ambiguous`, `new:info_first`, `new:other`) na model x N, każdy udział z przedziałem Wilsona (przedziały brzegowe,
  nie łączne); udział wariantów (np. wybór osi); stabilność strategii: odsetek powtórzeń konfiguracji z etykietą
  najczęstszą.
- **Testy (H4, H5):** kategorie z łączną liczebnością poniżej 5 łączy się przed analizą w „inne” (reguła stała, nie
  zależy od wyniku testu). H4: statystyka chi-kwadrat tabeli model x etykieta, rozkład zerowy z permutacji etykiet
  modeli wewnątrz każdej instancji (zachowuje parowanie po instancji). H5: tabela N x etykieta, permutacja wartości N
  wewnątrz modelu (instancje różnych N są różne, więc parowania nie ma).
- **Hanoi i wyszukiwanie:** rozkład etykiet na model x rozmiar z przedziałami Wilsona; testy tylko eksploracyjnie (BH).
- **KPI 2 (D07 A):** odsetek udanych przebiegów sortowania z etykietą `known` albo `hybrid`, z przedziałem Wilsona,
  ogółem, na model i na N; spełniony przy co najmniej 0,90 ([classification-rules.md](classification-rules.md),
  sekcja 11).
- **Kodowanie ręczne:** etykiety ręczne przebiegów `new` i `ambiguous` są analizą eksploracyjną; zgodność koderów
  i zgodność analizatora z próbką 10%: surowa, kappa Cohena z przedziałem, macierz pomyłek.

## 5. Pytanie 3: deklaracja a wykonanie (D01 A)

- **Deklaracja:** surowy tekst z zapisu ([prompts.md](prompts.md), sekcja 6). Kodują ją dwie osoby niezależnie, bez
  śladu wykonania i bez nazwy modelu, na zbiór etykiet z [classification-rules.md](classification-rules.md) plus
  `unspecified` (opis bez rozpoznawalnego algorytmu) i `none` (deklaracja pusta). Zgodność koderów: surowa i kappa
  z przedziałem; rozbieżności rozstrzyga rozmowa.
- **Jednostka:** przebieg udany z etykietą strategii i deklaracją inną niż `none` (sortowanie główne; Hanoi
  i wyszukiwanie osobno).
- **Miary:** zgodność surowa (deklarowany algorytm = rozpoznany; przy hybrydzie zgodność częściowa, gdy deklarowany
  jest algorytmem pierwszego odcinka, raportowana osobno), kappa Cohena z przedziałem (bootstrap klastrowy po
  instancjach), macierz pomyłek deklaracja x wykonanie, zgodność w każdej kategorii; wszystko ogółem i na model
  z przedziałami Wilsona. Kappa ma paradoksy przy niezrównoważonych klasach, więc nigdy bez surowej zgodności.
- **Obok:** odsetek deklaracji `none` i `unspecified` na model; zgodność w przebiegach nieudanych (eksploracyjnie).
- **Wpływ prośby o zapowiedź:** wynik grupy pilotażowej P1 i, jeśli pilotaż ją doda, grupy `no_announcement` pełnego
  badania ([design.md](design.md), sekcja 6): różnica rozkładu etykiet z prośbą i bez, eksploracyjnie.

## 6. Pytanie 4: efektywność

- **Jednostka:** udany przebieg (`done_solved`).
- **Miary sortowania:** porównania wobec `ceil(log2 N!)` (7, 22, 62 dla N = 5, 10, 20) i wobec najbliższego wariantu
  wzorca na tej samej instancji; porównania zbędne (przechodniość na grafie elementów) jako liczba i odsetek; zamiany
  wobec liczby inwersji i wobec `N - liczba cykli`; nadmiar długości wobec najbliższego wzorca.
- **Hanoi:** ruchy / `(2^n - 1)`, cofnięcia; **wyszukiwanie:** odczyty / `ceil(log2(N + 1))`, odczyty zbędne.
- **Estymatory:** mediana i średnia na model x rozmiar; przedział średniej z bootstrapu klastrowego po instancjach
  (2000 prób, percentylowy); bootstrap nie dla proporcji 0/n i n/n (tam Wilson).
- **Eksploracyjnie:** model liniowy `log(miara / granica)` od modelu i rozmiaru z błędami klastrowanymi po instancji,
  pary modeli z BH.

## 7. Pytanie 5: zmiana strategii

- **Z N (H5):** sekcja 4. Obok, na model: czy etykieta najczęstsza zmienia się między N = 5, 10 i 20.
- **Po błędzie wstrzykniętym (H6, H7):** miary z [fault-injection.md](fault-injection.md), sekcja 7, tylko dla
  przebiegów z `fault_fired: true` (wrażliwość dla H6: wszystkie przebiegi warunku, zasada „intention to treat”).
  H6: sukces w przebiegu z błędem i w przebiegu-parze (tabela 2 x 2 par), McNemar dokładny, efekt jako różnica
  proporcji w parach z przedziałem Newcombe'a. H7: zmiana etykiety odcinka przed i po błędzie
  ([classification-rules.md](classification-rules.md), sekcja 9) w przebiegu z błędem i w parze z podziałem w tym samym
  miejscu, McNemar dokładny. Odcinki `too_short` wyłącza się z H7 (liczba w raporcie).
- **Opis:** powrót po błędzie, opóźnienie powrotu, dokładne ponowienie, porzucenie, koszt błędu, w Hanoi utrata stanu,
  na model i podwarunek, z przedziałami Wilsona (proporcje) albo bootstrapu klastrowego (średnie).
- **Po błędzie własnym (eksploracyjnie):** zmiana etykiety odcinka po pierwszym błędzie walidacji w serii głównej,
  wobec przebiegów tego modelu bez błędów.

## 8. Przebiegi ucięte, z błędem API i inne szczególne

| Przypadek | Analiza główna | Wrażliwość |
|---|---|---|
| `step_limit` przy `solved: false` | porażka | wyłączone z analizy |
| `step_limit` przy `solved: true` | porażka (brak `done`) | sukces (definicja `solved`) |
| `context_exceeded` | porażka | wyłączone (zwłaszcza `qwen3:8b` przy sortowaniu N = 20, [run-settings.md](run-settings.md), sekcja 5) |
| `api_error` po 3 próbach, `time_limit`, `cost_limit`, `interrupted` | brak danych, pominięte | porażka |
| przebiegi z ponad połową wywołań w turach wielowywołaniowych | w analizie | pytanie 2 bez nich |
| `bad_arguments` u modeli bez trybu ścisłego | liczone w błędach | porównanie błędów tylko w grupie modeli z tym samym `strict` |

Inne analizy wrażliwości: GLMM z losowym wyrazem wolnym instancji (`BinomialBayesMixedGLM`) zamiast GEE; GEE
z korelacją niezależną; wyniki bez jednego modelu naraz (czy wniosek H1 zależy od jednego modelu).

## 9. Moc przed pełnym badaniem

Po pilotażu analiza (`src/analysis/`) symuluje moc: skuteczności na model i zadanie oraz ICC z pilotażu (przy braku pilotażu
modeli Anthropic i OpenAI: wartości z najbliższego modelu pilotażu, opisane w raporcie), 1000 symulowanych badań
z układem z [design.md](design.md), w każdym GEE z sekcji 3; wynik to moc H1 i średnia moc kontrastów H3 z Holmem
przy 10 i 15 powtórzeniach oraz najmniejszy efekt h wykrywalny z mocą 0,8. Reguła zmiany liczby powtórzeń:
[design.md](design.md), sekcja 6. Przybliżenie z założeniem niezależności (h około 0,58 przy 21 parach) to tylko
górna granica mocy.

## 10. Raport

- Każda liczba z przedziałem i liczebnością; skuteczność z przedziałem Wilsona; testy z wartością p przed i po
  poprawce; efekty w skali proporcji i h.
- Odstępstwa od tego planu (np. separacja, łączenie kategorii, zmiany po pilotażu) w osobnej sekcji raportu.
- Szkielet sekcji metod z listy kontrolnej NeurIPS (punkty 4-8, 16) i ARR (C3, C4); oprogramowanie: Python,
  `statsmodels` (GEE, `proportion_confint`, `confint_proportions_2indep`, `multipletests`, `mcnemar`), `scipy`
  (`bootstrap`, `binomtest`), `scikit-learn` (`confusion_matrix`, `f1_score(average="macro")`, `cohen_kappa_score`),
  wersje przypięte w środowisku analizy (`src/analysis/`).

> [!question] Do weryfikacji
> - Przedział Newcombe'a dla różnicy proporcji sparowanych: `confint_proportions_2indep` jest dla prób niezależnych;
>   wersja sparowana (Newcombe 1998, metoda 10) wymaga własnej funkcji albo innej biblioteki (`src/analysis/`).
> - Czy GEE w `statsmodels` daje kontrasty par z błędami kanapkowymi bez dodatkowego kodu (`t_test` na macierzy
>   kontrastów) i jak zachowuje się przy separacji (sprawdzić na danych z pilotażu).
