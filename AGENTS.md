# AGENTS.md - AlgoTraceUR

Zasady dla każdego, kto pisze kod albo dokumentację w tym repozytorium: dla ludzi i dla agentów kodujących (Claude
Code, Codex, Cursor i inne). Przeczytaj ten plik przed pierwszą zmianą. Wszystko, czego potrzebujesz do pracy, jest
w repozytorium; nie zakładaj wiedzy spoza niego.

## Projekt w skrócie

AlgoTraceUR bada, jakimi algorytmami modele językowe rozwiązują proste zadania (sortowanie, wieże Hanoi,
wyszukiwanie), gdy nie widzą danych i działają tylko przez wywołania narzędzi (`compare`, `swap`, `move`, `read`).
Każde wywołanie trafia do zapisu przebiegu, a analizator porównuje ten zapis z algorytmami wzorcowymi i rozpoznaje
strategię. Projekt składa się z sześciu programów:

| Program | Język | Rola |
|---|---|---|
| `src/environment/` | C# / .NET 10 | zadania z ukrytym stanem, pętla tool callingu, zapis przebiegu |
| `src/adapters/` | C# / .NET 10 | modele różnych dostawców za jednym interfejsem `IChatClient` |
| `src/runner/` | C# / .NET 10 | seria przebiegów z pliku konfiguracji, wznawianie, budżet |
| `src/references/` | Python 3.13 | algorytmy wzorcowe z zapisem kroków, syntetyczne przebiegi |
| `src/analyzer/` | Python 3.13 | cechy, miary, odległość od wzorców, etykieta strategii |
| `src/analysis/` | Python 3.13 | statystyka, tabele i wykresy do tekstu badania |

## Co czytać i w jakiej kolejności

1. [README.md](README.md): cel, pytania badawcze, schemat części, licencje.
2. [docs/README.md](docs/README.md): mapa dokumentacji.
3. [docs/project/overview.md](docs/project/overview.md): projekt badania (metoda, miary, modele, koszt) i
   [docs/project/work-plan.md](docs/project/work-plan.md): kolejność programów, zależności, kryteria „gotowe”.
4. [docs/decisions/0001-stos-technologiczny.md](docs/decisions/0001-stos-technologiczny.md): języki, biblioteki,
   układ repozytorium; [0002](docs/decisions/0002-licencje.md): licencje.
5. [schemas/README.md](schemas/README.md): kontrakt danych v2, jedyne połączenie programów.
6. `docs/specs/<program>.md`: specyfikacja programu, nad którym pracujesz (indeks w [docs/README.md](docs/README.md)),
   i otwarte sprawy jego interfejsów w [docs/project/open-questions.md](docs/project/open-questions.md).
7. Sekcje [docs/protocol/](docs/protocol/README.md), które wskazuje specyfikacja; protokołu nie czytaj w całości,
   jeśli nie musisz.
8. `src/<program>/README.md` i [tests/README.md](tests/README.md): polecenia budowania i testów.

## Zasady

- **Żadnych kluczy API ani sekretów w repozytorium**, także w testach, przykładach i logach. Klucz jest tylko
  w zmiennej środowiskowej (albo w `dotnet user-secrets`); konfiguracja eksperymentu podaje nazwę zmiennej.
  Schemat konfiguracji odrzuca plik z kluczem.
- **Kontrakt danych to jedyne połączenie programów.** Programy wymieniają dane tylko przez pliki zgodne ze
  `schemas/*.v2.schema.json`; programy .NET łączą się jeszcze tylko przez `IChatClient` (decyzja 0001). Program nie
  importuje kodu innego programu i nie czyta jego plików wewnętrznych. Wyjątki: analizator używa publicznego API
  pakietu `algotrace_references`, bo odtwarza wzorce od stanów pośrednich śladu
  ([docs/specs/analyzer.md](docs/specs/analyzer.md)), a seria wywołuje publiczne API środowiska i fabrykę adapterów,
  bo składa przebieg ([docs/specs/environment.md](docs/specs/environment.md)). Każdy zapisany plik danych przechodzi
  walidację ze schematem w testach.
- **Protokół jest ustalony.** Teksty dla modeli bierzesz dosłownie z [prompts.md](docs/protocol/prompts.md),
  ustawienia i limity z [run-settings.md](docs/protocol/run-settings.md), reguły etykiet z
  [classification-rules.md](docs/protocol/classification-rules.md). Kod ich nie poprawia ani nie „ulepsza”.
- **Powtarzalność.** Każda losowość idzie z zapisanego ziarna (generator zadań, harmonogram błędów, syntetyczne
  przebiegi); ten sam plik wejściowy i to samo ziarno dają te same bajty wyjścia (poza znacznikami czasu i
  odpowiedziami modeli). Zapisów w `data/` się nie zmienia: poprawka to nowy plik z opisem powodu.
- **Testy przy każdej zmianie.** Nowy kod ma testy w `tests/` (układ w [tests/README.md](tests/README.md)). Testy
  nie wołają płatnych API ani sieci: modele zastępuje fałszywy `IChatClient` albo atrapa HTTP. Przed PR przechodzą:

  ```
  dotnet build
  dotnet test
  uv sync --locked --all-packages
  uv run --locked pytest
  python -I schemas/check_examples.py
  ```

  Dopóki moduł nie ma kodu, jego polecenia są planem; pierwszy kod modułu je sprawdza i poprawia w jego `README.md`.
- **Zależności** tylko z decyzji 0001; nowa biblioteka wymaga licencji zgodnej z Apache-2.0 (decyzja 0002) i wpisu
  w opisie PR. Wersje przypięte w plikach blokad (`uv.lock`, `Directory.Packages.props`, `global.json`).
- **Gałęzie i PR.** Praca na gałęzi `<program>/<krótki-opis>` (np. `analyzer/zbedne-porownania`), jeden program na
  PR, jeśli się da. Opis PR: co i dlaczego, który punkt specyfikacji realizuje, jak sprawdzono. Scala człowiek po
  przeglądzie.
- **Język.** Dokumentacja w repozytorium po polsku. Kod, identyfikatory, komentarze w kodzie, nazwy plików danych
  i teksty dla modeli po angielsku. Pliki tekstowe w UTF-8 z końcami linii LF.
- **Środowisko bazowe** powstaje jako osobny projekt zaliczeniowy lidera i trafia do `src/environment/` po jego
  oddaniu (po 23.12.2026). Do tego czasu nikt nie pisze kodu w `src/environment/`; adaptery, seria i analizator
  pracują na atrapie zgodnej z kontraktem (zapisy przebiegu z `schemas/examples/` i z `data/synthetic/`).

## Czego agent nie robi sam

Zapytaj człowieka, zanim:

- zrobisz commit albo push na `main`, `push --force`, scalisz PR albo usuniesz gałąź;
- zmienisz `docs/protocol/`, `schemas/` albo `docs/decisions/`: to wymaga decyzji zespołu (nowy plik w
  `docs/decisions/`, wpis w historii zmian protokołu, nowa wersja schematu);
- uruchomisz cokolwiek, co woła płatne API albo serię przebiegów (koszt; budżet ustala konfiguracja i człowiek);
- zmienisz albo usuniesz pliki w `data/` lub konfiguracje użyte w badaniu w `experiments/`;
- dodasz zależność spoza decyzji 0001 albo zmienisz wersję .NET, Pythona lub pliku blokady;
- napiszesz kod w `src/environment/` przed przejęciem środowiska bazowego.

Gdy specyfikacja czegoś nie rozstrzyga, nie zgaduj w ciszy: wybierz najprostsze rozwiązanie zgodne z kontraktem,
opisz je w PR i oznacz jako „do ustalenia”.

## Gdy dokumenty się różnią

Nazwy pól, zdarzeń i wartości: wygrywa `schemas/` (v2). Zachowanie, teksty, ustawienia, progi: wygrywa
`docs/protocol/`. Potem `docs/decisions/`, potem `docs/specs/`, na końcu `src/*/README.md`. Sprzeczność zgłoś w PR
albo w zgłoszeniu (issue), zamiast wybierać po cichu.

W protokole i w `schemas/` zdarzają się numery zadań i krótkie kody decyzji (litera z numerem, czasem z literą
wariantu): to odnośniki do wewnętrznego planu prac lidera. Treść potrzebna do pracy jest w repozytorium, więc je pomijaj i nie dodawaj nowych.
