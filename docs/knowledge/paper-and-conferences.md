# Tekst badania i konferencje: budowa artykułu, wymagania miejsc zgłoszenia

Plik zbiera, jak jest zbudowany tekst badania i gdzie zostanie zgłoszony, żeby osoby piszące tekst i zgłoszenie
konferencyjne nie potrzebowały innego źródła. **Stan: 20.11.2026** (strony organizatorów czytane 19-20.11.2026; edycje
2027 w większości jeszcze nieogłoszone). Gdy [paper/README.md](../../paper/README.md) mówi coś innego, wygrywa
repozytorium, a ten plik trzeba poprawić.

## 1. Decyzje zespołu (20.11.2026)

- **Język**: tekst po angielsku (`main=english` w `paper/main.tex`), streszczenie także po polsku.
- **Budowanie PDF**: LaTeX z `latexmk`, lokalnie i w GitHub Actions (PDF z CI jest jednakowy dla wszystkich).
  Overleaf w planie darmowym odpada: limit kompilacji 10 s, jeden współpracownik, brak Gita.
- **Konferencja**: ML in PL 2027 (Warszawa, 13-16.10.2027), abstrakt po angielsku z wynikami pełnego badania;
  wewnętrzny termin wysłania **11.06.2027** (KPI projektu: zgłoszenie do 30.06.2027).
- **Zapas**: sekcja AI Kongresu Młodej Nauki (Uniwersytet Gdański), gdy call ML in PL nie jest otwarty do 31.05.2027.
- **Punkt decyzji**: 26.02.2027, wtedy wybór można jeszcze zmienić.
- **Wcześniejszy abstrakt**: dozwolony krótki abstrakt z pilotażu (opcjonalnie).
- **Licencja**: tekst i rysunki w `paper/` na CC BY 4.0, chyba że miejsce publikacji wymaga przeniesienia praw
  (wtedy opisuje to sekcja Licencja w [paper/README.md](../../paper/README.md)).

## 2. Budowa artykułu

Układ to **IMRaD** (wprowadzenie, metody, wyniki, dyskusja) z dodatkami typowymi dla informatyki: prace pokrewne,
osobna sekcja ograniczeń i zagrożeń trafności oraz oświadczenie o dostępności danych i kodu. Tekst w repozytorium
jest pełnym raportem badania; wersja konferencyjna jest krótsza i powstaje z niego osobno.

| Część artykułu | Co ma zawierać | Plik w `paper/sections/` |
|---|---|---|
| Streszczenie (EN i PL) | cel, metoda, główny wynik, wniosek | [00-abstract.tex](../../paper/sections/00-abstract.tex) |
| Wprowadzenie | problem, pytania badawcze, wkład | [01-introduction.tex](../../paper/sections/01-introduction.tex) |
| Prace pokrewne | stan wiedzy, luka | [02-related-work.tex](../../paper/sections/02-related-work.tex) |
| Metoda | zadania, modele, analizator, walidacja analizatora, statystyka | [03-method.tex](../../paper/sections/03-method.tex) |
| Eksperyment i protokół | co, kiedy i jak zebrano; ustawienia dość do powtórki | [04-experiment.tex](../../paper/sections/04-experiment.tex) |
| Wyniki | odpowiedź na każde pytanie badawcze po kolei | [05-results.tex](../../paper/sections/05-results.tex) |
| Dyskusja | interpretacja, porównanie z literaturą | [06-discussion.tex](../../paper/sections/06-discussion.tex) |
| Wnioski | odpowiedzi w skrócie, dalsze prace | [07-conclusion.tex](../../paper/sections/07-conclusion.tex) |
| Dodatek | kontrakt danych, prompty, schematy | [appendix-a-data-contract.tex](../../paper/sections/appendix-a-data-contract.tex) |
| Ograniczenia i zagrożenia trafności | patrz niżej | brak osobnego pliku |
| Dostępność danych i kodu | patrz niżej | brak osobnego pliku |

> **Do sprawdzenia:** dwóch ostatnich części nie ma w `paper/sections/`. Trzeba zdecydować, czy to osobne pliki
> (i dopisać je w `main.tex`), czy podsekcje dyskusji i wniosków.

**Wymagania z ogólnych standardów** (ACM SIGSOFT Empirical Standards, standard ogólny i Benchmarking):

- we wstępie: problem, pytania badawcze i definicje;
- w metodzie: nazwana metoda z uzasadnieniem; opis ustawień wystarczający do niezależnej powtórki; benchmark ma
  uzasadnienie (co mierzy, jakie metryki);
- w wynikach: odpowiedź wprost na pytania, podane i sprawdzone założenia testów, dość powtórzeń, by ocenić
  stabilność; zachować surowe wyniki, nie tylko zagregowane;
- wykresy i język nie mogą wprowadzać w błąd; liczby pochodzą ze skryptów analizy (zasada z `paper/README.md`).

**Ograniczenia i zagrożenia trafności** (podział Wohlina i in., *Experimentation in Software Engineering*, 2012):

- *konstrukcyjna*: czy miary naprawdę mierzą zgodność z algorytmem;
- *wewnętrzna*: czy wynik wynika z warunku, a nie z promptu lub wersji modelu;
- *zewnętrzna*: czy wnioski przenoszą się na inne algorytmy, rozmiary wejścia i modele;
- *wniosków*: poprawność wnioskowania statystycznego.

Pisać o konkretnych zagrożeniach tego badania, od najważniejszego, a nie odhaczać kategorie. Niektóre miejsca
(ACL Rolling Review) wymagają osobnej sekcji Limitations po wnioskach, poza limitem stron; jej brak oznacza
odrzucenie bez recenzji.

**Dostępność danych i kodu**: oświadczenie wskazuje, gdzie są dane i kod (repozytorium archiwalne z DOI, np. Zenodo),
albo dlaczego ich nie ma. W tekście cytuje się DOI konkretnej wersji, na której liczono wyniki. W bibliografii zbiór
jest wpisem `@dataset`, kod `@software`; w katalogu głównym repozytorium leży `CITATION.cff`. Dodać też deklarację
użycia AI przy pisaniu tekstu.

**Bibliografia i język w LaTeX**: `babel` (polski i angielski), `biblatex` z Biberem, jeden plik `references.bib`
(szablony ACL i IEEE używają BibTeX, więc bez pól wyłącznie biblatexowych tam, gdzie to zbędne). Szablony
konferencji (ACL, IEEE, Springer) są obowiązkowe i nie wolno ich zmieniać, więc szablon w `paper/` jest roboczy.

## 3. Wymagania miejsc zgłoszenia

Daty z oznaczeniem [2026] pochodzą z ostatniej edycji i są tylko przybliżeniem.

| Miejsce | Format | Język | Długość | Termin | Koszt | Status |
|---|---|---|---|---|---|---|
| [ML in PL 2027](https://conference.mlinpl.org/2026/next-year) | abstrakt w formularzu, bez szablonu; referat 20+5 min, plakat albo SRW 15+5 min [2026] | angielski | 300-3500 znaków | wewn. 11.06.2027; call nieogłoszony, [2026] 4.05-31.07 | prezentujący bezpłatnie, współautor kupuje bilet (studencki 500 zł [2026]) | **wybrane** |
| [Kongres Młodej Nauki, sekcja AI](https://kongresmlodejnauki.ug.edu.pl/sztuczna-inteligencja/) | abstrakt, bez szablonu | polski lub angielski (sekcja AI po angielsku) | 1/3-3/4 strony A4 | [2026] do 15.06, rejestracja od 14.05 | ok. 350 zł | **zapas** |
| [SITEE 2027](https://sitee.pw.edu.pl/) (PW, 19.05.2027) | artykuł IEEE; ustnie 8+5 min lub plakat A1 | polski lub angielski | 3-4 strony | nieogłoszony; [2026] abstrakty 1.04 | brak informacji | inne (z pilotażem) |
| [POSTER 2027](https://poster2026.sciencesconf.org/) (Praga) | rozszerzony abstrakt lub artykuł, szablony Word i LaTeX | angielski | 2 lub 4 strony | [2026] 14.03 (przedłużone 22.03) | bez opłaty | inne (z pilotażem) |
| [SPSympo2027](https://spsympo.ise.pw.edu.pl/instructions-for-authors) (PW, 28-30.09.2027) | artykuł, szablon IEEE A4 | angielski | do 6 stron | 1.04.2027 | nie podano | inne (temat poboczny) |
| [FedCSIS 2027](https://2027.fedcsis.org/) (Gdynia, 12-15.09.2027) | artykuł lub position paper, styl IEEE | angielski | 4-12 / 4-8 stron [2026] | artykuł 14.05.2027, position paper 11.06.2027 | nieustalony | inne (ryzykowny termin) |
| [Let's MIT IT](https://wmit.pollub.pl/nauka/konf-sem-proj-/international-student-conference-lets-mit-it-13.html) | wystąpienie 5 min, bez szablonu | polski lub angielski | brak | [2026] 30.04 | bezpłatnie | inne (z pilotażem) |
| [ACL 2027 SRW](https://2027.aclweb.org/) | szablon ACL, anonimizacja, Limitations | angielski | 4 lub 8 stron | call nieogłoszony; [2026] 18.03 | wyjazd do Japonii | odrzucone (za wcześnie) |

W 2026 ML in PL przyjmował też zgłoszenia do Student Research Workshop. Inne miejsca (TYGIEL, PP-RAI, EEICT, ICAISC,
SKILL) odpadły przez termin przed pełnym badaniem, język lub zasięg.

## 4. Wybrana konferencja i zapas

**ML in PL 2027** (Warszawa, Centrum Nauki Kopernik, 13-16.10.2027):

- abstrakt 300-3500 znaków po angielsku, z wynikami **pełnego** badania (pełne badanie kończy się 7.05.2027,
  analiza 21.05.2027); zgłoszenie w 2026 szło przez OpenReview;
- brak szablonu, więc w `paper/` nie trzeba przygotowywać osobnego formatu; wystarczy streszczenie oparte na
  wynikach ze skryptów analizy;
- termin własny 11.06.2027, bo call z 2026 kończył się 31.07, czyli po KPI (30.06.2027); KPI wymaga zgłoszenia, nie
  wystąpienia.

**Zapas: Kongres Młodej Nauki, sekcja AI**, gdy call ML in PL nie jest otwarty do 31.05.2027. Zgłoszenia około
15.06, opłata ok. 350 zł, abstrakt bez szablonu. Czasopismo "Progress" dotyczy tylko humanistyki i nauk społecznych,
więc dla AI nie ma publikacji.

**Punkt decyzji 26.02.2027**: potwierdzić wybór albo zmienić go (np. na wcześniejsze wystąpienie z pilotażu w SITEE
albo artykuł na FedCSIS). **Opcjonalny wcześniejszy abstrakt** z pilotażu (wyniki od 20.03.2027) może iść do miejsc
z wcześniejszym terminem; przed 20.03.2027 abstrakt może opisać tylko projekt i metodę.

**Prawa autorskie**: tekst i rysunki z `paper/` są na CC BY 4.0. Abstrakty bez tomu materiałów (ML in PL, Kongres
dla AI) raczej nie wymagają przeniesienia praw. Dla miejsc z tomem (IEEE, Springer) sprawdzić warunki przed wysłaniem.

## 5. Do sprawdzenia później

> **Do sprawdzenia:** do 26.02.2027: czy call ML in PL 2027 jest ogłoszony (terminy, SRW, archiwalność; call z 2026
> nie mówi, czy abstrakty są publikowane).

> **Do sprawdzenia:** kwiecień-maj 2027: Kongres Młodej Nauki 2027 (termin, opłata dla studentów spoza UG).
> Regulamin w §2.5 ogranicza referaty do tematyki nauki i jej organizacji, co nie pasuje do sekcji AI; wyjaśnić
> z organizatorem przed zgłoszeniem.

> **Do sprawdzenia:** ostrzeżenia pierwszej budowy w CI (20.11.2026, zakończona sukcesem, PDF w artefakcie
> `paper-pdf`): `main.log` i `main.blg` nie były jeszcze przejrzane (zob. `paper/README.md`).

> **Do sprawdzenia:** SITEE 2027 (terminy; czy przyjmuje studentów innych uczelni, wymaga promotora jako ostatniego
> autora) i POSTER 2027 (czy przyjmuje studentów I stopnia), jeśli zespół wybierze wcześniejsze wystąpienie.

> **Do sprawdzenia:** SITEE i POSTER przyjmują tylko magistrantów i doktorantów; reszta zespołu może nie spełniać
> tego warunku.

## Źródła

- [paper/README.md](../../paper/README.md): pliki, budowanie, zasady, licencja.
- Oficjalne strony w tabeli w sekcji 3; standardy SIGSOFT: https://github.com/acmsigsoft/EmpiricalStandards;
  ACL Rolling Review: https://aclrollingreview.org/cfp; oświadczenia o dostępności danych:
  https://www.springernature.com/gp/authors/research-data-policy/data-availability-statements.
