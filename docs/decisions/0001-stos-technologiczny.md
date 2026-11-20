# 0001 Stos technologiczny modułów

- **Status:** przyjęta robocza, 20.11.2026. Lider przyjął ją, zanim zespół zaczął kod, żeby pierwsze zadania nie
  czekały; zespół może ją zmienić, np. na pierwszym spotkaniu.
- **Jak ją zmienić:** nowy plik `NNNN-krotki-opis.md`, który w statusie pisze „zastępuje 0001” i podaje powód. Ten plik
  dostaje wtedy status „zastąpiona przez NNNN” i poza tym się nie zmienia. Nowszą wersję tej samej biblioteki
  wprowadza plik blokady, bez nowego zapisu; inna biblioteka, inny język albo inny serwer modeli lokalnych wymaga
  nowego zapisu.

## Kontekst

Trzeba było ustalić, w jakim języku powstaje każdy z sześciu modułów z `src/README.md`, jakimi bibliotekami adaptery
rozmawiają z modelami i czym uruchamiamy model lokalny, zanim zespół napisze pierwszy kod (wzorce, adaptery,
analizator).

- **Środowisko bazowe** (generator zadań, piaskownica, pętla tool callingu, zapis przebiegu) powstaje w C# / .NET jako
  osobny projekt zaliczeniowy lidera i trafia do `src/environment/` po jego oddaniu (do 23.12.2026). Przepisanie go na
  inny język kosztowałoby czas zespołu.
- **Pętla tool callingu musi być naszym kodem.** Każde wywołanie narzędzia i każda odpowiedź modelu trafia do zapisu
  przebiegu z polami dostawcy (powód zakończenia, tokeny, surowa odpowiedź). Biblioteka, która sama wykonuje narzędzia
  albo tłumaczy odpowiedzi na wspólny format z utratą pól, zafałszowałaby dane badania.
- **Analizator i analiza wyników** potrzebują odległości edycyjnej ciągów, modeli statystycznych i wykresów do tekstu
  badania. Te narzędzia są najlepiej opisane i najczęściej używane w Pythonie.
- **Moduły łączą się tylko plikami z `schemas/`:** JSON Schema 2020-12 z numerem wersji, zapis przebiegu w JSONL
  (zdarzenia `run_start`, `model_turn`, `tool_call`, `run_end`), wyniki w CSV, duże analizy w Parquet. Dzięki temu
  można mieszać języki bez wywołań między nimi.
- **Model lokalny:** badanie wymaga co najmniej jednego. Potrzebny jest serwer z tool callingiem i API podobnym do
  chmurowych, który działa na zwykłym laptopie z Windows.
- Umiejętności zespołu nie są jeszcze znane.

## Decyzja

1. **Dwa języki.** C# / .NET 10 dla `environment`, `adapters` i `runner`; Python dla `references`, `analyzer`
   i `analysis`. Między językami tylko pliki z `schemas/`.
2. **Modele przez `IChatClient`** z `Microsoft.Extensions.AI`, nad oficjalnymi SDK dostawców, **bez
   `UseFunctionInvocation`**: adapter zwraca odpowiedź z żądanymi wywołaniami, a środowisko samo je wykonuje
   i zapisuje. W .NET środowisko, adaptery i seria łączą się tym interfejsem i niczym więcej.
3. **Model lokalny przez Ollamę** i jej API zgodne z OpenAI (`http://localhost:11434/v1`), obsługiwane tym samym
   adapterem co OpenAI.

### Moduły

Wersje to stan rejestrów z 19.11.2026. Przypinają je pliki blokady przy pierwszym kodzie każdego modułu; wtedy
sprawdza się je ponownie.

| Moduł | Język | Główne biblioteki | Budowanie |
|---|---|---|---|
| `environment/` | C#, `net10.0`, biblioteka | `Microsoft.Extensions.AI.Abstractions` 11.0.0 (`IChatClient`), `System.Text.Json` (JSONL), `JsonSchema.Net` 9.7.0 | `dotnet`, .NET SDK 10.0.401 |
| `adapters/` | C#, `net10.0`, biblioteka | `Microsoft.Extensions.AI` 11.0.0 z `Microsoft.Extensions.AI.OpenAI`; SDK `OpenAI` 2.15.0, `Anthropic` 13.10.0, `Google.GenAI` 2.2.0; `Microsoft.Extensions.Http.Resilience` 11.0.0 (`Polly.Core` 8.9.1) | `dotnet` |
| `runner/` | C#, `net10.0`, aplikacja konsolowa | `System.Threading.RateLimiting` 11.0.0, `JsonSchema.Net` 9.7.0 (konfiguracja), `System.Text.Json` | `dotnet` |
| `references/` | Python 3.13 | biblioteka standardowa (algorytmy bez bibliotek), `jsonschema` 4.26.0 (`Draft202012Validator`) | uv |
| `analyzer/` | Python 3.13 | `rapidfuzz` 3.14.6 (odległość edycyjna na ciągach operacji), `scikit-learn` 1.9.1 (n-gramy, drugi sposób porównania), `jsonschema` 4.26.0 | uv |
| `analysis/` | Python 3.13 | `pandas` 3.1.1 z `pyarrow` 26.0.1 (Parquet), `statsmodels` 0.15.0, `scipy` 1.18.1, `matplotlib` 3.11.2 (PDF albo PGF do `paper/figures/`) | uv |
| testy .NET | C# | `xunit.v3` 4.0.3, `FsCheck.Xunit.v3` 3.6.0, `Verify.XunitV3` 33.7.0, `WireMock.Net` 2.31.0, fałszywy `IChatClient` zamiast API | `dotnet test` |
| testy Pythona | Python 3.13 | `pytest` 9.2.0, `hypothesis` 6.170.16, `syrupy` 7.0.2; `networkx` 3.7 tylko do sprawdzania porównań zbędnych | `uv run pytest` |

`polars` 2.1.0 albo `duckdb` 2.0.0 dochodzą w `analysis/` tylko wtedy, gdy `pandas` nie wystarczy na duże pliki
Parquet. Metody statystyczne wybiera plan analizy w `docs/protocol/`, nie ten zapis.

### Adaptery i zapis odpowiedzi

- Pola dostawcy, których nie ma we wspólnym modelu, przechodzą przez `RawRepresentation` (odpowiedź)
  i `RawRepresentationFactory` (żądanie).
- `ChatResponse` nie niesie nagłówków HTTP, więc surowe żądania i odpowiedzi zapisujemy na poziomie transportu
  (własny `HttpClient` z handlerem albo polityka `System.ClientModel`).
- Ponawianie w SDK jest wyłączone; ponawiamy i pilnujemy tempa sami (`Microsoft.Extensions.Http.Resilience`,
  `System.Threading.RateLimiting`), żeby każda próba trafiła do zapisu.
- Mistral i inne serwery zgodne z OpenAI przez klienta `OpenAI` z własnym adresem bazowym; trzeba to sprawdzić przy
  pierwszym adapterze.

### Model lokalny

- Ollama (najnowsza wersja 0.40.16 z 09.11.2026), endpoint `/v1/chat/completions`.
- Ollama ignoruje tam `tool_choice` i nie ma przełącznika wywołań równoległych: adapter liczy wywołania w odpowiedzi,
  wykonuje pierwsze, a resztę oznacza w zapisie przebiegu.
- Domyślne okno 4096 tokenów nie da się zmienić przez `/v1`: ustawiamy `OLLAMA_CONTEXT_LENGTH` albo `num_ctx`
  w Modelfile, co najmniej 20K.
- Wersja modelu w zapisie przebiegu to `digest` z `/api/tags`; parametry próbkowania zawsze jawnie; w seriach bez
  strumieniowania.
- Zmiana serwera to inny adres bazowy w konfiguracji. Pilotaż modeli lokalnych potwierdza ten wybór albo go zmienia
  (nowym zapisem).

### Narzędzia i powtarzalność

- **.NET:** `global.json` z pełną wersją SDK (10.0.401) i `rollForward: disable`, bo pakiety dodawane niejawnie przez
  SDK zmieniają się z jego wersją; Central Package Management (`Directory.Packages.props`); `packages.lock.json`
  (`RestorePackagesWithLockFile`), w CI `dotnet restore --locked-mode`.
- **Python:** uv; `.python-version` z 3.13, `requires-python = ">=3.12"` (`networkx` 3.7 wymaga 3.12); `uv.lock`
  w repozytorium, `uv sync --locked` i `uv run --locked`; aktualizacja tylko przez `uv lock --upgrade`. uv sam
  instaluje wersję Pythona z `.python-version`.
- **Sekrety:** klucze API tylko w zmiennych środowiskowych (`.env` poza repozytorium albo `dotnet user-secrets`);
  w konfiguracji eksperymentu tylko nazwa zmiennej.

### Układ repozytorium

- **.NET:** jedno rozwiązanie `AlgoTrace.slnx` w katalogu głównym; projekty
  `src/environment/AlgoTrace.Environment.csproj` (biblioteka), `src/adapters/AlgoTrace.Adapters.csproj` (biblioteka),
  `src/runner/AlgoTrace.Runner.csproj` (aplikacja konsolowa); testy w `tests/dotnet/AlgoTrace.<Moduł>.Tests/`;
  w katalogu głównym `global.json`, `Directory.Build.props` i `Directory.Packages.props`. Projekty środowiska
  przychodzą z projektu zaliczeniowego i ten układ dostosowuje się do nich przy imporcie.
- **Python:** jeden workspace uv w katalogu głównym (`pyproject.toml` z `[tool.uv.workspace]`, jeden `uv.lock`,
  `.python-version`); członkowie `src/references`, `src/analyzer` i `src/analysis`, każdy z własnym `pyproject.toml`
  i pakietem `algotrace_<moduł>` (unikalne nazwy importu zamiast ogólnych, jak `analysis`); testy
  w `tests/python/<moduł>/`. Układ plików wewnątrz członka ustala pierwszy kod modułu.
- Dlaczego tak: z katalogu głównego jedno polecenie na język buduje i testuje wszystko (`dotnet build`,
  `dotnet test`, `uv sync --locked --all-packages`, `uv run --locked pytest`), każdy język ma jeden plik blokady, a testy zostają w `tests/`
  obok testów niezależnych od języka.

## Odrzucone

Język (pytanie 1):

- **Wszystko w C# / .NET:** brak dojrzałych odpowiedników `statsmodels`, `scipy` i wykresów matplotlib do PDF albo
  PGF, a metody analizy są opisane z narzędziami Pythona.
- **Wszystko w Pythonie:** SDK dostawców są tu najlepiej opisane, a seria mogłaby użyć gotowego szkieletu Inspect AI,
  ale środowisko bazowe w C# trzeba by przepisać po 23.12.2026. Zostaje zapasem, gdyby zespół znał tylko Pythona.
- **Decyzja zespołu na pierwszym spotkaniu:** wstrzymuje pierwszy kod; zespół i tak może zmienić ten zapis.

Biblioteki do modeli:

- **LiteLLM, any-llm, aisuite, pydantic-ai:** tłumaczą odpowiedzi na format Chat Completions, zniekształcają powód
  zakończenia (`pause_turn` → `length`, `MALFORMED_FUNCTION_CALL` → `stop`) i gubią pola dostawców.
- **Microsoft Agent Framework 1.28.0, Semantic Kernel 1.82.0:** własna, ukryta pętla wywołań narzędzi.
- **Inspect AI jako szkielet serii:** Python, a środowisko, pętla i analizator i tak byłyby nasze.
- **Vercel AI SDK:** trzeci język, a przekazywanie pól dostawców nie jest sprawdzone.
- **`Mistral.SDK`:** społecznościowy, ostatnie wydanie 10.2025; Mistral przez klienta `OpenAI`.
- **`NJsonSchema` 11.6.2:** nie obsługuje w pełni JSON Schema 2020-12. Zostaje zapasem, gdyby zmieniła się umowa
  binariów `JsonSchema.Net` (kod MIT, binaria na umowie OSMF: opłata tylko dla działalności zarobkowej od 10 000 USD
  przychodu rocznie, projekt studencki nie płaci); drugim zapasem jest walidacja tylko w Pythonie.

Serwer modeli lokalnych (pytanie 2):

- **LM Studio:** nie opisuje, jak traktuje `tool_choice`, a przy nierozpoznanym szablonie modelu oddaje wynik
  narzędzia jako wiadomość roli `user`.
- **vLLM:** daje najwięcej gwarancji (`tool_choice: required`, `strict`), ale wymaga GPU pod Linuksem; na Windows
  tylko przez WSL.
- **llama.cpp `llama-server`:** obsługuje `tool_choice: required`, wymaga `--jinja`. Zostaje zapasem dla modelu, który
  w Ollamie gubi wywołania.

## Skutki

- Na każdym komputerze, który uruchamia całość, potrzebne są .NET SDK 10 i uv; Ollama tylko do modelu lokalnego.
- Dwa zestawy testów; w CI dwa zadania (`actions/setup-dotnet@v6` z `global-json-file`, `astral-sh/setup-uv@v10`),
  na publicznym repozytorium bez opłat. Workflow powstaje osobno.
- Te same przykłady z `schemas/` są walidowane po obu stronach (`JsonSchema.Net` i `jsonschema`), żeby oba języki
  rozumiały format tak samo.
- Limit kroków (liczony z kosztu najwolniejszego wzorca), instancja i ziarno przechodzą między wzorcami (Python)
  a środowiskiem (C#) tylko przez konfigurację eksperymentu i zapis przebiegu. Czy analizator importuje pakiet
  wzorców, czy czyta ich przebiegi z plików, rozstrzyga projekt analizatora.
- Do 23.12.2026 adaptery i analizator testuje się na atrapie środowiska i na fałszywym `IChatClient`, bez płatnych
  API.
- `run_start` każdego przebiegu zapisuje wersje SDK i języka oraz skróty plików blokady.
- README każdego modułu w `src/` mówi, w jakim jest języku i jak go zbudować, uruchomić i przetestować; `.gitignore`
  ma wpisy .NET i Pythona, a pliki blokady i wersji są w repozytorium.
- Ryzyko: jeśli zespół zna tylko Pythona, adaptery i seria w C# są progiem wejścia; wtedy nowy zapis (np. wszystko
  w Pythonie).
- Do sprawdzenia przy pierwszym kodzie: czy klient `OpenAI` dla .NET z adresem Ollamy daje wywołania narzędzi
  w `IChatClient`; czy wszystkie wybrane pakiety Pythona mają koła dla 3.13 (pierwszy `uv lock`).
