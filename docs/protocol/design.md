# Układ badania: warunki, instancje, powtórzenia, pilotaż

Status: **przed pilotażem** (2026-11-20). Punkty odroczone do pilotażu są tylko w sekcji 6, każdy z regułą
rozstrzygnięcia; zmiany po pilotażu z datą i powodem w historii [README](README.md).

Decyzje protokołu ([README.md](README.md), sekcja „Zakres”) zastosowane w tym pliku: D01 (grupa bez prośby o zapowiedź), D02 (warunek z błędami), D03
(temperatura tylko w pilotażu), D05 (rozmiary), D08 (Hanoi ze stanem tylko w pilotażu). Ustawienia i limity:
[run-settings.md](run-settings.md); teksty i warianty: [prompts.md](prompts.md); błędy:
[fault-injection.md](fault-injection.md).

## 1. Seria główna

- **Modele:** zestaw A, 7 modeli ([run-settings.md](run-settings.md), sekcja 2), 4 dostawców chmurowych i jeden
  lokalny.
- **Zadania i rozmiary (D05 A):** sortowanie N = 5, 10, 20; Hanoi n = 3, 4, 5; wyszukiwanie N = 15, 63, 255.
- **Powtórzenia:** 10 na konfigurację (model, zadanie, rozmiar), minimum z karty projektu.
- **Liczba przebiegów:** 7 x 3 x 3 x 10 = **630** (KPI: co najmniej 500), 90 na model, 21 par modeli. Plan statystyczny
  liczył 6 modeli (540 przebiegów, 15 par); przy 7 modelach i 21 porównaniach z poprawką Bonferroniego najmniejszy
  efekt wykrywalny z mocą 0,8 przy 90 przebiegach na model to h około 0,58 (przy 15 parach 0,56, przy jednym porównaniu
  0,42), w przybliżeniu niezależności, więc to górna granica mocy.
- **Warunek i warianty:** `condition: main`, `prompt_variant: main`, bez błędów wstrzykniętych.

## 2. Warunek z błędami (D02 A)

`faults:one_off` i `faults:persistent` na sortowaniu N = 10 i Hanoi n = 4, 10 powtórzeń, wszystkie 7 modeli,
te same instancje co seria główna w tych komórkach: 7 x 2 x 2 x 10 = **280** przebiegów. Szczegóły:
[fault-injection.md](fault-injection.md).

## 3. Instancje i ziarna

- **Te same instancje dla wszystkich modeli:** porównania modeli są w parach (ta sama instancja, inny model), co
  zmniejsza wariancję bez dodatkowych przebiegów.
- **Nowa instancja w każdym powtórzeniu:** powtórzenie `r` (0..9) komórki ma własną instancję, co obniża korelację
  powtórzeń (ICC). Wyjątek z natury zadania: Hanoi ma jeden stan początkowy (wszystkie krążki na paliku 0), więc
  10 instancji jednej komórki Hanoi ma tę samą treść, różne `instance_id`, a powtórzenia mierzą tylko niedeterminizm
  modelu; analiza klastruje je po komórce ([analysis-plan.md](analysis-plan.md)).
- **Jeden plik instancji na serię:** `instances/<series>.jsonl`, generowany raz przed serią, wersjonowany
  w repozytorium; ten sam plik czytają środowisko, algorytmy wzorcowe i analizator. Serie: `pilot` i `full`
  (seria główna i warunek z błędami współdzielą plik `full`). Pilotaż ma inne ziarno bazowe niż pełne badanie, więc
  ustawień nie dopasowuje się na instancjach pełnego badania.
- **Ziarno instancji:** `seed = base_seed + idx`, gdzie `idx` to numer wiersza w pliku serii (0, 1, 2...), a
  `base_seed` jest w konfiguracji serii, wybrany i zapisany przed generowaniem. Kolejność wierszy: zadanie
  (sortowanie, Hanoi, wyszukiwanie), rozmiar rosnąco, powtórzenie rosnąco; seria `full` ma 90 wierszy.
- **Generator:** niezależny od języka opis: generator losowy z jawnym algorytmem i ziarnem, np. Python
  `numpy.random.Generator(PCG64(seed))`, albo własny PRNG (SplitMix64 lub PCG32) z wektorami testowymi, jeśli instancje
  mają powstawać w dwóch językach (stos: [decyzja 0001](../decisions/0001-stos-technologiczny.md)). Plik instancji jest źródłem prawdy; nazwa i wersja
  generatora są metadanymi każdego wiersza.
- **Treść instancji:**
  - sortowanie: losowa permutacja 1..N (bez powtórzeń); permutację już posortowaną odrzuca się i losuje ponownie
    z tego samego generatora;
  - Hanoi: n i stan początkowy (wszystkie krążki na paliku 0);
  - wyszukiwanie: N różnych liczb całkowitych wylosowanych z `1..4N` i posortowanych rosnąco; w każdej komórce
    dokładnie 5 z 10 instancji ma liczbę szukaną w tablicy (które, losuje generator); obecna: wartość z losowej pozycji;
    nieobecna: losowa liczba całkowita z przedziału `(a[0], a[N-1])`, której nie ma w tablicy, więc nieobecności nie
    widać po odczycie skrajnych pozycji.
- **Sprawdzenie rozwiązywalności i poprawności** (generator zapisuje wynik w wierszu, a seria nie startuje, gdy
  któreś nie przechodzi): permutacja ma wszystkie wartości 1..N i nie jest posortowana; Hanoi n zgodne z komórką;
  wyszukiwanie: tablica ściśle rosnąca, `target_present` zgodne z treścią, odpowiedź wzorcowa (pozycja albo -1)
  zapisana.
- **Pola wiersza:** `instance_id`, `series`, `task`, `size`, `rep`, `idx`, `seed`, `generator`, `generator_version`,
  `initial_state`, przy wyszukiwaniu `target`, `target_present`, `answer`, przy komórkach z błędami harmonogram
  (`fault_seed`, `fault_position`, [fault-injection.md](fault-injection.md)), wynik sprawdzeń.

## 4. Kolejność przebiegów

- Każdy dostawca ma własną kolejkę (limity zapytań i równoległość: [run-settings.md](run-settings.md)).
- Kolejność przebiegów w kolejce to losowa permutacja z ziarnem `order_seed` z konfiguracji serii, wspólna dla
  wszystkich warunków danego dostawcy (seria główna i warunek z błędami przemieszane), żeby pora dnia, zmiany po
  stronie dostawcy i zmęczenie limitów nie układały się z zadaniem, rozmiarem albo warunkiem.
- Kolejność ramowa: pilotaż (najpierw przebiegi próbne P0, sekcja 6), zmiany protokołu po pilotażu, preregistracja na
  OSF co najmniej 3 dni przed pierwszym przebiegiem pełnego badania (48 h na zatwierdzenie), pełne badanie do
  31.05.2027. Modele Anthropic i OpenAI wchodzą dopiero do pełnego badania (konta płatne).
- Przebieg powtórzony po `api_error` ([run-settings.md](run-settings.md), sekcja 6) idzie na koniec kolejki.

## 5. Liczba przebiegów i górny kosztorys

**Wzór:** koszt przebiegu z cache przy `n` turach to w przybliżeniu `a * n + b * n^2` (wejście rośnie z kwadratem
liczby tur, bo każde zapytanie niesie całą rozmowę). `a` i `b` każdego modelu dopasowano do dwóch kosztów z notatki
o koszcie przebiegu (80 i 200 kroków z cache, ceny płatne z 2026-11-19, prompt 500 tokenów, 80 tokenów na krok, 540
tokenów wyjścia na krok z rozumowaniem). **Górny koszt przebiegu** to ten wzór przy `n` równym limitowi kroków
(jedno wywołanie na turę, czyli najgorszy przypadek przy D04 A); ten sam wzór daje `górny_koszt_przebiegu` strażnika
budżetu ([run-settings.md](run-settings.md), sekcja 7). Po pilotażu `a` i `b` liczy się na nowo z pomiarów (tokeny
promptu, na krok, rozumowania, trafienia cache) i tabela się zmienia (historia w [README](README.md)).

Górny koszt jednego przebiegu (USD, koszt umowny, także dla planów darmowych):

| Model | sort 5 | sort 10 | sort 20 | Hanoi 3 | Hanoi 4 | Hanoi 5 | wysz. 15 | wysz. 63 | wysz. 255 |
|---|---|---|---|---|---|---|---|---|---|
| `claude-sonnet-5-5` | 0,17 | 0,84 | 4,47 | 0,12 | 0,26 | 0,56 | 0,18 | 0,47 | 1,82 |
| `claude-haiku-5-5` | 0,00 | 0,01 | 0,12 | 0,00 | 0,00 | 0,01 | 0,00 | 0,00 | 0,03 |
| `gpt-6.1-terra` | 0,01 | 0,08 | 0,87 | 0,01 | 0,02 | 0,05 | 0,01 | 0,04 | 0,24 |
| `gpt-6-luna` | 0,00 | 0,01 | 0,10 | 0,00 | 0,00 | 0,01 | 0,00 | 0,01 | 0,03 |
| `gemini-4-hydrogen` | 0,22 | 1,03 | 4,97 | 0,15 | 0,33 | 0,70 | 0,23 | 0,59 | 2,16 |
| `openai/gpt-oss-120b` | 0,01 | 0,10 | 1,11 | 0,01 | 0,02 | 0,06 | 0,02 | 0,05 | 0,31 |
| `qwen3:8b` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Kosztorys warunków (górny: każdy przebieg do limitu kroków; typowy: sortowanie `0,75 * N(N-1)` wywołań, Hanoi
1,2 x optimum, wyszukiwanie `2 * ceil(log2(N + 1))` odczytów; oba w USD po cenach płatnych):

| Warunek | Przebiegi | Górny | Typowy |
|---|---|---|---|
| seria główna (`main`) | 630 | 227 | 75 |
| błędy (`faults:one_off`, `faults:persistent`) | 280 | 54 | 25 |
| możliwe dodatki po pilotażu (sekcja 6): `no_announcement`, parafraza, każdy 7 modeli x sortowanie N = 10 x 10 | 70 + 70 | 21 + 21 | około 7 + 7 |
| **pełne badanie razem** | 910 (do 1050) | **281 (do 323)** | **100 (do 114)** |
| pilotaż (sekcja 6) | 277 | modele pilotażu na planach darmowych i lokalnie: 0 USD rzeczywiście | - |

- Najdroższe komórki to sortowanie N = 20 i wyszukiwanie N = 255 u `claude-sonnet-5-5` i `gemini-4-hydrogen`: razem
  około 60% górnego kosztu serii głównej (134 z 227 USD).
- `budżet_serii` w konfiguracji ustala właściciel z tej tabeli ([run-settings.md](run-settings.md), sekcja 7);
  rekomendacja: górny koszt pełnego badania plus 20% zapasu na powtórzenia po `api_error`, czyli około 340-390 USD.

> [!question] Do weryfikacji
> Wzór kosztu zakłada 80 tokenów na krok i 540 tokenów wyjścia na krok z rozumowaniem; Anthropic zostawia bloki
> rozumowania w kontekście, więc dla `claude-sonnet-5-5` przyrost na krok może być większy. Pomiar w pilotażu
> zastępuje te założenia.

## 6. Pilotaż: grupy i reguły rozstrzygnięcia

Modele pilotażu: `gemini-4-hydrogen` (Gemini Free), `openai/gpt-oss-120b` (Groq Free), `qwen3:8b` (lokalnie), bo
konta płatne powstają dopiero przed pełnym badaniem. Instancje z serii `pilot` (inne ziarno bazowe). Pilotaż nie
wchodzi do analizy potwierdzającej i w preregistracji jest deklarowany jako dane już obserwowane.

| Grupa | Co | Modele | Komórki, powtórzenia | Przebiegi |
|---|---|---|---|---|
| P0 próba | wszystkie komórki, wariant `main`: adaptery, limity, tokeny na krok, cache, ucięcia | 3 | 9 x 1 | 27 |
| P1 zapowiedź (D01) | `main` i `no_announcement` | Gemini, Qwen | sortowanie N = 10, 10 | 40 |
| P2 parafrazy | `para_order`, `para_names`, `para_wording` (wobec `main` z P1) | Gemini, Qwen | sortowanie N = 10, 10 | 60 |
| P2 parafrazy | `main` i `para_names` | Gemini, Qwen | Hanoi n = 4, wyszukiwanie N = 63, po 5 | 40 |
| P3 temperatura (D03) | temperatura 0 wobec domyślnej | Qwen (domyślna z P1), gpt-oss | sortowanie N = 10, 10 | 30 |
| P4 Hanoi ze stanem (D08) | `main` i `hanoi_state` | Gemini, Qwen | Hanoi n = 4, 10 | 40 |
| P5 format `compare` | `compare_symbols` (wobec `main` z P1) | Gemini, Qwen | sortowanie N = 10, 10 | 20 |
| P6 błędy (D02) | `faults:one_off`, `faults:persistent` | Gemini | sortowanie N = 10, Hanoi n = 4, po 5 | 20 |
| **razem** | | | | **277** |

Gdy darmowe limity dzienne nie pozwalają zmieścić pilotażu w terminie, grupy P1-P6 schodzą do 5 powtórzeń, reguły
niżej zostają te same. Temperatura w P3 tylko w modelach, które ją przyjmują: `qwen3:8b` na pewno, `gpt-oss-120b`
na Groq do sprawdzenia w P0 (gdy Groq jej nie przyjmuje albo ignoruje, P3 ma tylko Qwen).

**Miary porównania wariantów** (wariant X wobec `main`, ten sam model, te same instancje, w parach po instancji):
różnica skuteczności oraz zgodność etykiet, czyli odsetek instancji, na których klasyfikator
([classification-rules.md](classification-rules.md)) daje tę samą etykietę strategii w obu przebiegach. Wariant jest
**istotny**, gdy u któregoś modelu różnica skuteczności wynosi co najmniej 30 punktów procentowych albo zgodność
etykiet jest poniżej 70%. To reguły decyzyjne pilotażu, nie testy: przy 10 parach test nie ma mocy.

| Punkt odroczony | Reguła rozstrzygnięcia |
|---|---|
| prośba o zapowiedź (P1, D01) | D01 A zostaje (bez prośby pytanie 3 nie ma danych). Gdy `no_announcement` jest istotny, pełne badanie dodaje `no_announcement` na sortowaniu N = 10 dla 7 modeli (70 przebiegów), a efekt prośby trafia do wyników i zagrożeń trafności; gdy nie, tylko opis w metodach. |
| parafrazy (P2) | Gdy któraś parafraza jest istotna, pełne badanie dodaje tę z największą różnicą na sortowaniu N = 10 dla 7 modeli (70 przebiegów) i raportuje zakres wyników; gdy nie, tylko `main` i opis w metodach. |
| temperatura (P3, D03) | D03 A zostaje (temperatury nie da się ustawić jednakowo u dostawców). Wynik P3 idzie do zagrożeń trafności. |
| stan w Hanoi (P4, D08) | D08 A zostaje, chyba że w `main` skuteczność Hanoi n = 4 jest poniżej 10% u obu modeli, a w `hanoi_state` co najmniej 30 punktów wyższa (efekt podłogi: zadanie nie różnicuje modeli). Wtedy zmiana D08 to nowa decyzja właściciela, nie zmiana automatyczna. |
| format `compare` (P5) | Słowa zostają, chyba że `compare_symbols` daje u obu modeli co najmniej 20 punktów wyższą skuteczność; wtedy symbole stają się wariantem `main` (nowa wersja tekstów `p2`). |
| rozmiary (D05) | Zostają, jeśli walidacja analizatora osiąga KPI na sortowaniu N = 20; gdy nie osiąga przy N = 5, rozpoznanie przy N = 5 jest w analizie eksploracyjne, a rozmiar zostaje dla pytania 1. Gdy górny koszt pełnego badania po pomiarach z P0 przekracza budżet, sortowanie N = 20 zmienia się na N = 16 (limit z tego samego wzoru). |
| limity kroków | Gdy w P0-P2 ponad 5% przebiegów jednej komórki kończy się `step_limit`, a ślad jeszcze postępuje (w ostatnich 20 wywołaniach nie powtarza się ta sama para argumentów), współczynnik tej rodziny rośnie o 0,5 (sortowanie 2,0, Hanoi 3,5, wyszukiwanie `N + 32`). |
| `max_tokens` i kontekst | Według [run-settings.md](run-settings.md) (ponad 1% uciętych odpowiedzi: podwojenie; `num_ctx` Qwen do 32768, jeśli sprzęt pozwala). |
| pozycje błędów (P6) | Według [fault-injection.md](fault-injection.md), sekcja 8 (`fault_fired: false` poniżej 10%). |
| liczba powtórzeń | Symulacja mocy z ICC i skutecznością z pilotażu ([analysis-plan.md](analysis-plan.md)): 10 zostaje, chyba że najmniejszy wykrywalny efekt analizy potwierdzającej przekracza h = 0,6 i budżet pozwala na 15 powtórzeń; wtedy 15 we wszystkich komórkach serii głównej. |

Po pilotażu wszystkie wyniki tej tabeli i zmiany protokołu trafiają do historii w [README](README.md) przed
preregistracją; potem protokół jest zamrożony.
