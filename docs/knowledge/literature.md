# Stan literatury: prace powiązane z AlgoTrace

Plik służy do pisania rozdziału 1 tekstu (problem, cel, prace powiązane) i do uzasadniania decyzji projektowych.
Stan literatury: 20.11.2026. Tam, gdzie repozytorium już coś rozstrzyga, wygrywa repozytorium: zob.
[paper/README.md](../../paper/README.md) i [paper/references.bib](../../paper/references.bib) (113 wpisów). W
nawiasach przy pracach jest klucz do użycia jako `\cite{klucz}`.

## Luka badawcza

Nie znaleziono pracy, która łączy cztery cechy AlgoTrace: gotowe modele różnych dostawców, zwykły tool calling,
ukryty stan zadania i automatyczne rozpoznanie algorytmu z zapisu wywołań. Benchmarki tool callingu oceniają
poprawność wywołań, stan końcowy, wynik albo efektywność trajektorii, ale nie pytają, jakim algorytmem model doszedł
do wyniku. Deklaracja modelu nie jest wiernym opisem jego działania, a nikt nie porównuje nazwanego algorytmu z
rozpoznanym. Twierdzenie o nowości formułować z datą i zakresem przeszukania, nie jako "pierwsza praca".

> **Do sprawdzenia:** wyniki "nie znaleziono" dotyczą przeszukanego zakresu: indeksy cytowań z 2026 roku są niepełne,
> Google Scholar nie był używany automatycznie, a DBLP blokuje klientów automatycznych.

## Spór wokół pracy Apple i narzędzia

- Shojaee i in. (`\cite{shojaee2025illusion}`, NeurIPS 2025): łamigłówki (m.in. wieże Hanoi) pokazują załamanie
  modeli rozumujących. Autorzy odrzucają narzędzia, bo "tell us nothing" o rozumieniu, i oceniają tylko poprawność,
  nie optymalność. AlgoTrace: ruch jest osobnym wywołaniem, narzędzie jest interfejsem, a nie solverem.
- Lawsen (`\cite{lawsen2025comment}`): załamanie wynika z limitu długości odpowiedzi i nierozwiązywalnych instancji.
  Ruch jako osobne wywołanie omija ten limit.
- Song i in. (`\cite{song2025thinking}`): narzędzia (kod, pseudokod, notatnik) realizowane w prompcie, nie przez
  parametr narzędzi w API; ocena tylko poprawności kroków. Teza abstraktu jest mocniejsza niż tabele.
- Khan i in. (`\cite{khan2025comment}`), Dellibarda Varela i in. (`\cite{varela2025rethinking}`), Utsho i in.
  (`\cite{utsho2026empirical}`): kolejne odpowiedzi; porażki w Hanoi nie wynikają tylko z limitu odpowiedzi.
- Su i in. (`\cite{su2025limits}`): wieże Hanoi jako wywołania `move_disk`; dostęp do środowiska nie usuwa załamania.
  Najbliższa praca z tego nurtu, ale stan jest jawny, zadanie jedno, a algorytmu się nie rozpoznaje.
- Inne: `\cite{pereira2026transformers}` (interpretowalność), `\cite{meyerson2025solving}` (Hanoi przez rozkład na
  mikroagentów), `\cite{schepanowski2025limits}` i `\cite{cheng2026verifiable}` (układanki w odpowiedzi tekstowej;
  Cheng i Ling rozkładają efektywność planu na niezawodność, koordynację i oszczędność akcji wobec optimum).

## Najbliższe prace: ukryty stan i operacje

- EARL (`\cite{yue2025earl}`): sortowanie ukrytych liczb przez `compare` i `swap`, ale model Qwen2.5 jest trenowany,
  a powstały algorytm opisano ręcznie. Cytować jako preprint. To najbliższe zadanie, wyraźnie inna metoda.
- Dyad (`\cite{zhan2026dyad}`): jedyna praca cytująca EARL, trenowany koder akcji, nie badanie gotowych modeli.
- ZebraArena (`\cite{zhao2026zebraarena}`): informacja tylko przez wywołania, liczba wywołań wobec teoretycznego
  minimum. Precedens miary efektywności; zagadka logiczna, bez algorytmów wzorcowych.
- Agentic automata learning (`\cite{menaged2026agents}`): odkrycie ukrytego DFA; ślad modelu porównany ze śladami
  L* i TTT. Modele wymieniają L* jako właściwą metodę, ale nie wykonują jej wiernie. Bez klasyfikacji algorytmu.
- FuncBenchGen (`\cite{maekawa2026towards}`), MazeEval (`\cite{einarsson2025mazeeval}`), AQA-Bench
  (`\cite{yang2025aqabench}`), OdysseyArena (`\cite{xu2026odysseyarena}`), ScrambleToolBench
  (`\cite{toh2026scrambletoolbench}`), AgentCE-Bench (`\cite{yang2026agentcebench}`): ukryty graf, labirynt albo
  środowisko; mierzą sukces lub efektywność, nie algorytm. AQA-Bench narzuca algorytm z góry.
- SortBench (`\cite{herbold2025sortbench}`) i Verbalized Algorithms (`\cite{lall2025verbalized}`): sortowanie tekstem
  albo LLM jako wyrocznia porównań w danym algorytmie. CLRS (`\cite{velickovic2022clrs}`) i CLRS-Text
  (`\cite{markeeva2024clrstext}`): ślad algorytmu jest etykietą do nauki, a AlgoTrace rozpoznaje algorytm ze śladu.

## Benchmarki tool callingu

- BFCL (`\cite{patil2025berkeley}`): składnia wywołań, potem stan backendu; każda droga do stanu jest przyjęta.
- tau-bench i tau2-bench (`\cite{yao2024taubench}`, `\cite{barres2025tau2bench}`): stan bazy po rozmowie, spójność
  powtórzeń.
- ToolSandbox (`\cite{lu2025toolsandbox}`): stan świata, kamienie milowe i "miny" na trajektorii.
- AgentBench i AgentBoard (`\cite{liu2024agentbench}`, `\cite{ma2024agentboard}`), API-Bank, T-Eval, NESTFUL
  (`\cite{li2023apibank}`, `\cite{chen2024teval}`, `\cite{basu2024nestful}`), ToolLLM i StableToolBench
  (`\cite{qin2024toolllm}`, `\cite{guo2024stabletoolbench}`): poprawność wywołań, jeden ciąg wzorcowy lub odsetek
  rozwiązanych.
- Benchmarki MCP (`\cite{wang2026mcpbench}`, `\cite{wu2026mcpmark}`, `\cite{luo2025mcpuniverse}`,
  `\cite{fan2025mcptoolbench}`, `\cite{mo2026livemcpbench}`, `\cite{guo2025mcpagentbench}`,
  `\cite{li2026toolathlon}`): stan po zadaniu, wynik, ocena LLM; zadanie jawne, bez oceny strategii.
- Jakość trajektorii (`\cite{kim2026beyond}`, `\cite{he2026trajectbench}`, `\cite{zhu2026redundant}`,
  `\cite{fan2026agentprocessbench}`, `\cite{jang2026odysseys}`, `\cite{mazaheri2026agentatlas}`): zbędne wywołania,
  kolejność, poprawność kroku; bez rozpoznania algorytmu.
- CostBench (`\cite{liu2025costbench}`): ciąg wywołań jako plan o minimalnym koszcie, przy kosztach znanych agentowi.
- Agent-Diff (`\cite{pysklo2026agentdiff}`): świadomie nie dopasowuje śladu, bo to kruche wobec równoważnych
  strategii. AlgoTrace odpowiada wieloma wariantami wzorców, progiem i kategorią "strategia nowa".

## Rozpoznawanie algorytmu z zapisu działań

- Perţicaş, Indurkhya i in. (`\cite{perticas2017finding}`, `\cite{perticas2020neural}`): pięć algorytmów sortowania
  rozpoznanych siecią neuronową z obrazów migawek tablicy (ponad 90 %). Zamknięty zbiór klas bez odmowy, same zamiany
  bez porównań.
- Taherkhani i Malmi (`\cite{taherkhani2013beacon}`, `\cite{taherkhani2012automatic}`): klasyfikacja algorytmów z
  kodu programów studentów (drzewo C4.5, 97 %); analiza statyczna, nie śladu.
- Plan recognition as planning (`\cite{ramirez2009plan}`, `\cite{ramirez2010probabilistic}`): cel z obserwowanych
  akcji przez koszt planu. Analogia do odległości od wzorca, ale tam szuka się celu, a u nas algorytmu.
- Process mining (`\cite{berti2024rethinking}`, `\cite{berti2024pm4pyllm}`, `\cite{dorsch2025compass}`) oraz
  weryfikacja śladów (`\cite{elkoussy2026agentltl}`, `\cite{yagubyan2026consistent}`, `\cite{shu2026resolve}`): rama
  logu zdarzeń, reguły nad śladami agenta, odległość ciągów wywołań.
- Wieże Hanoi: Simon (`\cite{simon1975functional}`, strategie rozwiązywania) i Romik (`\cite{romik2006shortest}`,
  najkrótsze drogi w grafie stanów, użyte w odległości od celu).
- Luki: brak prac o podziale śladu agenta na fazy, o liczeniu porównań zbędnych przez przechodniość i o klasyfikatorze
  z odmową dla śladów modeli językowych.

## Deklaracja a wykonanie

- Wierność rozumowania: Turpin i in. (`\cite{turpin2023language}`), Lanham i in. (`\cite{lanham2023measuring}`),
  Chen i in. (`\cite{chen2025reasoning}`): wyjaśnienia modelu pomijają czynniki, które naprawdę wpłynęły na odpowiedź.
- Plan a działania agenta: Oota i in. (`\cite{oota2026llm}`): Plan+ReAct zachowuje zadeklarowaną strukturę tylko w
  22-45 % trajektorii. Liu i in. (`\cite{liu2026plan}`): zły plan szkodzi bardziej niż brak planu. Dong i in.
  (`\cite{dong2025say}`) i Li i in. (`\cite{li2026consistent}`): luki wykonania i rozumowania, sprzeczne stwierdzenia.
- Nikt nie porównuje nazwanego algorytmu z zapowiedzi z algorytmem rozpoznanym z ciągu operacji. Schemat kodowania
  (zgodna, niezgodna, brak deklaracji, deklaracja niejednoznaczna) to propozycja, nie gotowy standard.

> **Do sprawdzenia:** metodę porównania deklaracji z trajektorią u Oota i in. oraz Liu i in. czytano tylko w
> abstraktach lub częściowo; Simona (1975) tylko ze źródeł wtórnych; pełne teksty Perţicaş i Taherkhaniego nie były
> czytane w całości. Agentic automata learning to zgłoszenie na ICLR 2027 w recenzji (stan 20.11.2026), a miejsce
> publikacji NESTFUL i Dellibarda Varela i in. nie jest ustalone: przed oddaniem tekstu sprawdzić wersje. W pracy Song
> i in. kolumna "Thinking" w tabeli 1 ma "Yes" także dla modelu, który tekst nazywa niemyślącym: sprawdzić w PDF.

## Co z tego wynika dla rozdziału 1

- Problem: ocena tool callingu nie mówi, jaką strategią model działa; spór wokół pracy Apple dotyczy m.in. tego, czy
  porażka to limit odpowiedzi, czy brak rozumowania. Ruch jako osobne wywołanie i ukryty stan zdejmują oba zarzuty.
- Cel: rozpoznać algorytm gotowego modelu z zapisu wywołań i porównać go z zapowiedzią modelu.
- Nowość: różnica wobec EARL (trening kontra gotowe modele, ręczny opis kontra automatyczne rozpoznanie), ZebraArena
  (zagadka bez algorytmów), automata learning (dwie własności, bez klasyfikacji) i Su i in. (stan jawny).
- Miary mają precedensy: liczba wywołań wobec optimum (ZebraArena), porównanie ze śladem klasycznego algorytmu
  (automata learning), liczba porównań i zamian wobec optimum (EARL), efektywność planu (Cheng i Ling).
- Dane powiązane z narzędziem: narzędzie jest tylko interfejsem ruchu, więc odpowiada na argument Shojaee i in., że
  narzędzia rozwiązujące zadanie nic nie mówią o rozumieniu.
- Zapowiedź modelu jest osobną zmienną i trzeba ją porównać z rozpoznanym zachowaniem (Turpin, Oota).
- Przy cytowaniu preprintów (EARL, Song, Lawsen) oznaczać status; nie podawać wersji opublikowanej bez potwierdzenia.

## Jak dodać pozycję do references.bib

1. Dane zbierać ze źródeł pierwotnych, nie z pamięci. Strona abs arXiv (`https://arxiv.org/abs/<id>`): tytuł, pełni
   autorzy z diakrytykami, data v1, pole Comments (często miejsce publikacji). Crossref (`api.crossref.org/works/<DOI>`):
   tom, strony i autorzy wersji opublikowanej; Crossref myli imiona, więc porównać je z arXiv. Semantic Scholar
   (`paper/batch`): miejsce publikacji i klucz DBLP. OpenReview: decyzja konferencji. DBLP i strony AAAI blokują
   klientów automatycznych; wtedy Crossref albo strona otwarta ręcznie.
2. Sprawdzić: numer arXiv na stronie abs (numer z pamięci bywa błędny), czy wersja opublikowana jest potwierdzona (pole
   Comments, DOI wydawcy, strona konferencji, DBLP lub OpenReview); inaczej zostaje preprint.
3. Typ: wersja opublikowana jako `@inproceedings` lub `@article` z DOI; preprint jako `@misc` z `eprint`,
   `archivePrefix = {arXiv}`, `primaryClass` i `url`. Klucz `nazwiskoRokSłowo`, rok wersji opublikowanej albo v1.
4. Zapis: diakrytyki jako polecenia LaTeX (`{\'e}`, `{\v{s}}`), w tytułach klamry wokół skrótowców i nazw własnych
   (`{LLM}`, `{Hanoi}`), podwójne nazwiska w klamrach, bez znaku `@` w komentarzach poza wpisami.
5. Nie wymyślać danych: brakującego tomu, stron, DOI ani decyzji konferencji nie zgadywać; pole zostaje puste, a
   wątpliwość trafia do notatki. Po dodaniu wpisu sprawdzić, że klucz jest unikalny i plik się parsuje.

> **Do sprawdzenia:** szablon zbudował się w CI z Biberem 20.11.2026, ale na prawdziwym tekście z cytowaniami
> jeszcze nie: czy wszystkie wpisy składają się bez ostrzeżeń.
