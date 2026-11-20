# Pierwsze spotkanie zespołu (20.11.2026)

- **Kiedy:** piątek 20.11.2026, 16:00, ok. 60 minut; prowadził lider projektu.
- **Rodzaj:** spotkanie zapoznawcze. Lider przedstawił projekt według materiałów spotkania (punkty niżej), a zespół
  zgodził się na wszystko, co w nich było. Notatka powstała z materiałów spotkania: ustalenia to propozycje
  z materiałów, które zespół przyjął bez zmian.
- **Kto był:** lider projektu i członkowie zespołu. Role i osoby przy pierwszych kartach zostały do przydziału
  (sekcja „Kto co robi do kiedy”).

## Co omówiliśmy

1. **O co chodzi w projekcie.** Badamy, jak skutecznie i jakimi algorytmami modele LLM różnych dostawców rozwiązują
   zadania algorytmiczne: sortowanie, wieże Hanoi, wyszukiwanie. Model nie widzi danych: każdy ruch (porównaj,
   zamień, przesuń) to wywołanie narzędzia, a z zapisu ruchów analizator rozpoznaje algorytm (znany, hybrydę albo
   strategię nową). Wynik: publiczny zbiór przebiegów, tekst badania po angielsku i referat na studencką konferencję.
2. **Repozytorium i praca z agentem.** [AGENTS.md](../../AGENTS.md) (start dla każdego i dla jego agenta),
   [docs/project/](../project/overview.md) (opis badania, plan prac, sprawy otwarte),
   [docs/specs/](../README.md) (specyfikacje sześciu programów), [schemas/](../../schemas/README.md) (kontrakt danych
   v2), [docs/protocol/](../protocol/README.md) i [docs/decisions/](../decisions/README.md).
3. **Decyzje do przyjęcia przez zespół** (niżej, „Ustalenia”).
4. **Role i pierwsze karty etapu 2.**
5. **Rytm pracy i formalności.**

KPI projektu i terminy wewnętrzne:

| KPI | Termin wewnętrzny | Termin KPI |
|---|---|---|
| Środowisko z 3 rodzinami zadań i walidacja analizatora ≥ 95% | 22.01.2027 | 31.01.2027 |
| Pełne badanie: min. 500 przebiegów na 6 modelach | 7.05.2027 | 31.05.2027 |
| Publiczny zbiór, tekst badania, zgłoszenie referatu | 4-11.06.2027 | 30.06.2027 |
| Zakończenie w kole (prezentacja wyników) | 16.07.2027 | 30.07.2027 |

## Ustalenia

| Sprawa | Ustalenie |
|---|---|
| Stos technologiczny | Środowisko, adaptery i uruchamianie serii w C# / .NET; wzorce, analizator i analiza wyników w Pythonie (uv); model lokalny przez Ollamę. Zapis [0001](../decisions/0001-stos-technologiczny.md) ma status „przyjęta”. |
| Licencje | Kod (i całe repozytorium poza `data/` i `paper/`) na Apache-2.0, zbiór przebiegów na CC0 1.0, tekst badania na CC BY 4.0. Utwór wspólny: zgoda każdego autora obecnego na spotkaniu; zapis [0002](../decisions/0002-licencje.md) ma status „przyjęta”. |
| Język tekstu | Angielski, streszczenie także po polsku; PDF z LaTeX (`latexmk`) lokalnie i w GitHub Actions. |
| Kontrakt danych v2 | Podstawa etapu 2. Sprawy z [open-questions.md](../project/open-questions.md) rozdzielamy na osoby razem z kartami. |
| Zasady pracy | Gałąź `<program>/<opis>` i PR, bez commitów na `main`; żadnych kluczy API w repozytorium; kod i komentarze po angielsku, dokumentacja po polsku. Do 23.12.2026 kod środowiska (`src/environment/`) pisze tylko lider, reszta pracuje na atrapie z `schemas/examples/`. |
| Dzień raportu | Piątek co 2 tygodnie, pierwszy raport 4.12.2026, potem 18.12.2026, 1.01.2027, 15.01.2027 i dalej co 2 tygodnie. Przerwy i sesje (24.12-3.01, 25.01-21.02) to okresy obniżonej aktywności. |
| Aktywność | Po 7 dniach bez zadań ostrzeżenie, po 14 możliwe usunięcie z zespołu; projekt zamyka się po 14 dniach bez postępu albo bez raportu. |
| Tablica zadań | Karta = cel, „gotowe, gdy”, „zależy od” i lista kroków; karta kodu ma linię „Specyfikacja:” z plikiem w `docs/specs/`. Po spotkaniu lider przeniósł tablicę z Trello do urwisu koła (projekt AlgoTraceUR, klucz `ALGO`): listy tablicy to statusy zadań, kamienie milowe to epiki, kroki to podzadania. |

## Kto co robi do kiedy

| Rola | Pierwsza karta (etap 2, od 5.12.2026) | Kto |
|---|---|---|
| Wzorce i analizator (Python) | Algorytmy wzorcowe sortowania z zapisem kroków i przebiegi syntetyczne | do przydziału |
| Adaptery (C#) | Adaptery: wspólny interfejs i model lokalny (na atrapie środowiska) | do przydziału |
| Analiza wyników (Python) | Skrypty analizy na danych syntetycznych | do przydziału |
| Tekst | Budowanie PDF tekstu, rozdział 1 (problem, cel, powiązane prace) | do przydziału |
| Koordynator promocji | Co najmniej jedna publikacja o projekcie w miesiącu (bez prac technicznych) | do przydziału |

Lider: plik `LICENSE`, zaproszenia do repozytorium koła i do projektu w urwisie dla każdego, pierwszy raport
4.12.2026.

## Otwarte sprawy

- Osoby do ról i pierwszych kart: każdy bierze kartę w urwisie (pole wykonawcy).
- Plik `LICENSE` z niezmienionym tekstem Apache-2.0 i pytanie do opiekuna koła, czy regulamin uczelni czegoś wymaga.
- Dostęp do repozytorium i do projektu w urwisie dla każdego z zespołu.
- Tryb raportów w przerwach i sesjach do uzgodnienia z Przewodniczącym.
- Oświadczenia o własności intelektualnej: 30 dni od przyjęcia do koła (karta z terminem 18.12.2026).
- Sprawy interfejsów z [open-questions.md](../project/open-questions.md).

## Następne spotkanie

Termin ustala lider (materiały spotkania go nie podają); najbliższy punkt kontrolny to pierwszy raport 4.12.2026.
