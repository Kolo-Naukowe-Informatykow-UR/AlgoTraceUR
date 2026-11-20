# Ustawienia modeli, limity i warunki zatrzymania

Status: **przed pilotażem** (2026-11-20). Pilotaż może zmienić limity i `max_tokens`; zmiana z datą
i powodem w historii [README](README.md).

Decyzje protokołu ([README.md](README.md), sekcja „Zakres”) zastosowane w tym pliku: D03 (ustawienia, temperatura), D04 (wywołania równoległe), D05
(rozmiary). Teksty dla modeli: [prompts.md](prompts.md); układ badania i kosztorys: [design.md](design.md).

## 1. Zasady

- **Jeden stały tryb na model (D03 A):** w serii głównej i w warunku z błędami każdy model ma jeden poziom
  rozumowania: wyłączone tam, gdzie się da, najniższy dostępny tam, gdzie rozumowania nie da się wyłączyć (reguła
  wyboru zestawu A, [overview.md](../project/overview.md)). Poziom rozumowania zmienia liczbę i długość wywołań, więc nie zmienia się w trakcie
  badania.
- **Parametry próbkowania niewysyłane (D03 A):** `temperature`, `top_p`, `top_k` i `seed` nie są wysyłane do żadnego
  dostawcy chmurowego (Anthropic odrzuca je błędem 400, Gemini je ignoruje, OpenAI z rozumowaniem je odrzuca), więc
  obowiązują wartości domyślne dostawcy. Wyjątek: Ollama dostaje `seed` (sekcja 2), bo tam ziarno daje powtarzalny
  tekst, a nie zmienia rozkładu. Temperatura jako zmienna jest tylko w grupie pilotażowej ([design.md](design.md)).
- **`tool_choice: auto` (D01, D03):** wymuszone narzędzie pomija tekst przed wywołaniem (brak zapowiedzi) i u części
  modeli z rozumowaniem jest odrzucane.
- **Wywołania równoległe dozwolone (D04 A):** żaden adapter nie wyłącza wywołań równoległych
  (`disable_parallel_tool_use` Anthropic i `parallel_tool_calls: false` OpenAI nie są wysyłane; OpenAI i Groq dostają
  jawnie `parallel_tool_calls: true`), bo Gemini i Ollama nie mają przełącznika i wyłączenie dałoby różne warunki
  u dostawców. Wykonanie po kolei według [prompts.md](prompts.md), sekcja 2.
- **Limity jednakowe dla modeli:** limity kroków, błędów i przypomnień zależą tylko od zadania i rozmiaru. Model ich
  nie zna ([prompts.md](prompts.md), sekcja 1).

## 2. Ustawienia modeli zestawu A

| Model (`model` w zapytaniu) | Dostawca, API | Rozumowanie | Co wysyła adapter | `max_tokens` |
|---|---|---|---|---|
| `claude-sonnet-5-5` | Anthropic Messages, `anthropic-version` z konfiguracji | zawsze włączone, najniższy poziom | `thinking: {type: "adaptive"}`, `output_config: {effort: "low"}` | 8192 |
| `claude-haiku-5-5` | Anthropic Messages | wyłączone | bez `thinking`, bez `effort` (domyślny poziom Haiku 5.5 nie włącza rozumowania) | 2048 |
| `gpt-6.1-terra` | OpenAI Responses API | wyłączone | `reasoning: {effort: "none"}` | 2048 |
| `gpt-6-luna` | OpenAI Responses API | wyłączone | `reasoning: {effort: "none"}` | 2048 |
| `gemini-4-hydrogen` | Gemini API | zawsze włączone, najniższy poziom | `thinking_level: "low"` (`minimal` nieobsługiwane) | 8192 |
| `openai/gpt-oss-120b` | Groq, Chat Completions zgodne z OpenAI | niski poziom | `reasoning_effort: "low"` | 8192 |
| `qwen3:8b` | Ollama `/api/chat`, lokalnie | wyłączone | `think: false`, `options: {num_ctx: 20480, num_predict: 2048, seed: <ziarno przebiegu>}` | 2048 |

- `max_tokens` (u Gemini `max_output_tokens`, u Ollama `num_predict`) to limit jednej odpowiedzi. Modele
  z rozumowaniem mają 8192, bo tokeny rozumowania wliczają się do limitu; bez rozumowania 2048, bo odpowiedź to krótki
  tekst i wywołania. Odpowiedź ucięta limitem (`stop_reason` `max_tokens` / `length`) jest zapisana; gdy w pilotażu
  więcej niż 1% odpowiedzi jakiegoś modelu jest uciętych, limit tego modelu podwaja się przed serią główną (zmiana
  w historii [README](README.md)).
- Ollama: opcje modelu, których adapter nie wysyła (np. temperatura z pliku `Modelfile`), czyta się z `/api/show`
  i zapisuje w konfiguracji przebiegu; digest modelu przypina test modeli lokalnych przed pilotażem.
- Ziarno Ollama: `seed` = ziarno instancji przebiegu ([design.md](design.md)), więc powtórzenie przebiegu daje ten
  sam tekst przy tej samej wersji Ollama i tym samym sprzęcie.
- Gemini i Groq na planie darmowym w pilotażu: ustawienia te same co na płatnym; plan zapisuje się w konfiguracji.

> [!question] Do weryfikacji
> Dokładne nazwy pól i poziomów rozumowania zestawu A w dokumentacji z dnia konfiguracji pilotażu (styczeń 2027):
> `output_config.effort: "low"` dla Sonnet 5.5, brak rozumowania Haiku 5.5 przy poziomie domyślnym, `thinking_level`
> Gemini 4, `reasoning_effort` Groq dla gpt-oss-120b. Zmiana nazwy pola nie zmienia reguły z sekcji 1.

## 3. Limity kroków

Krok to każde wywołanie narzędzia, wykonane albo odrzucone przez walidację, łącznie z `done`. Limit liczy wywołania,
nie tury (przy D04 A jedna tura może mieć kilka wywołań). Wzory (D05 A, rozmiary z [design.md](design.md)):

- **Sortowanie:** `ceil(1,5 * N(N-1))`. `N(N-1)` to liczba wywołań sortowania bąbelkowego w najgorszym przypadku
  (`N(N-1)/2` porównań i tyle samo zamian), najwolniejszego algorytmu wzorcowego; limit z granicy informacyjnej
  `ceil(log2 N!)` odciąłby algorytmy O(N^2), które badanie chce rozpoznać. Współczynnik 1,5 daje zapas na porównania
  zbędne i błędy przy koszcie, który rośnie z kwadratem liczby kroków (dla losowej permutacji typowy przebieg
  bąbelkowy ma około `0,75 * N(N-1)` wywołań, więc limit to około dwa razy więcej).
- **Hanoi:** `3 * (2^n - 1)`: trzy razy optimum. Kroki Hanoi są tanie (małe n), a większy zapas pozwala wrócić po
  nielegalnych ruchach (pytanie 5).
- **Wyszukiwanie:** `N + 16`: wyszukiwanie liniowe w najgorszym przypadku (`N` odczytów i `done`) mieści się z zapasem
  15 wywołań, czyli około dwa do czterech razy więcej niż najgorszy przypadek wyszukiwania przez połowienie
  przedziału (`ceil(log2(N + 1))` = 4, 6, 8).

| Zadanie | Rozmiar | Wzorzec najgorszy (wywołania) | Limit kroków |
|---|---|---|---|
| sortowanie | N = 5 | 20 | 30 |
| sortowanie | N = 10 | 90 | 135 |
| sortowanie | N = 20 | 380 | 570 |
| Hanoi | n = 3 | 7 (optimum) | 21 |
| Hanoi | n = 4 | 15 | 45 |
| Hanoi | n = 5 | 31 | 93 |
| wyszukiwanie | N = 15 | 16 (liniowe + `done`) | 31 |
| wyszukiwanie | N = 63 | 64 | 79 |
| wyszukiwanie | N = 255 | 256 | 271 |

Gdy pilotaż zmieni rozmiar (D05: „ostatecznie po pilotażu”), limit liczy się z tego samego wzoru.

Po osiągnięciu limitu środowisko kończy przebieg z `step_limit` zaraz po wywołaniu, które go wyczerpało; dalsze
wywołania tej samej tury są zapisane jako niewykonane (`executed: false`, `skipped_reason: step_limit`). Przebieg
ucięty limitem zostaje w danych z pełnym ciągiem operacji.

## 4. Limit błędów i przypomnień

- **Błędy z rzędu:** 10 kolejnych błędów walidacji (w kolejności wywołań, także przez granice tur) kończy przebieg
  z `too_many_errors`; każde poprawne wywołanie zeruje licznik. Wzór z τ²-bench (`max_errors = 10`) w wersji „z rzędu”,
  bo łączną liczbę błędów ogranicza już limit kroków, a celem jest przerwanie modelu, który powtarza ten sam błąd.
  Błędy wstrzyknięte ([fault-injection.md](fault-injection.md)) nie liczą się do tego licznika i go nie zerują.
- **Przypomnienia:** po każdej odpowiedzi bez wywołania jedno przypomnienie ([prompts.md](prompts.md), sekcja 7). Dwie
  takie odpowiedzi z rzędu albo czwarta w przebiegu (po trzech przypomnieniach) kończą przebieg z `no_tool_call`.
  Odpowiedzi bez wywołania nie są krokami.

## 5. Tokeny, kontekst i czas

- **Odpowiedź:** `max_tokens` z sekcji 2.
- **Kontekst:** przebieg kończy się z `context_exceeded`, gdy dostawca odrzuca zapytanie z powodu długości kontekstu
  (błąd nieponawiany). Ollama nie zwraca takiego błędu, tylko po cichu ucina początek rozmowy, więc pętla sama kończy
  przebieg z `context_exceeded`, gdy liczba tokenów wejścia ostatniego zapytania (`prompt_eval_count`) plus tokeny
  ostatniej odpowiedzi plus 512 przekracza `num_ctx - num_predict` (20480 - 2048 = 18432).
- **Zapytanie:** limit czasu jednej próby 300 s w chmurze, 600 s lokalnie; przekroczenie to błąd ponawiany
  (sekcja 6).
- **Przebieg:** 3 h w chmurze, 6 h lokalnie, liczone bez przerw harmonogramu na limit dzienny dostawcy (sekcja 6);
  przekroczenie kończy przebieg z `time_limit`. To bezpiecznik infrastruktury, a nie miara modelu; czas przebiegu jest
  w analizie tylko miarą pomocniczą.
- **Koszt przebiegu:** strażnik w sekcji 7.

> [!warning] Ryzyko: kontekst Qwen3 8B
> Przy `num_ctx` 20480 i około 60-100 tokenach na krok (wywołanie, wynik, krótki tekst) Qwen3 8B zmieści około
> 180-300 kroków, a sortowanie N = 20 ma limit 570. Przebiegi `qwen3:8b` z `context_exceeded` przy N = 20 są możliwe
> i analizuje się je osobno ([analysis-plan.md](analysis-plan.md)). Pilotaż mierzy tokeny na krok; jeśli sprzęt
> pozwala, `num_ctx` rośnie do 32768 (natywny kontekst Qwen3 8B) przed serią główną (po teście modeli lokalnych, zmiana w historii).

## 6. Ponawianie błędów API

**W zapytaniu** (we własnej pętli adaptera, każda próba zapisana w `attempts` zdarzenia `model_turn`; wbudowane
ponawianie SDK i HTTP wyłączone, bo nie zapisuje prób):

- Ponawiane: przekroczenie czasu próby, błąd sieci, HTTP 408, 409, 429, 500, 502, 503, 504, 529 (Anthropic
  „overloaded”).
- Czekanie: `max(Retry-After, backoff)`, backoff wykładniczy z losowym rozrzutem: 2 s, potem razy 2, najwyżej 120 s,
  rozrzut do 25%. Najwyżej 6 prób na zapytanie.
- Nieponawiane: 400 (poza długością kontekstu, która daje `context_exceeded`), 401, 403, 404, 422; brak środków albo
  limit wydatków u dostawcy kończy serię u tego dostawcy (nie przebieg z ponowieniem).
- Limit dzienny (429 z `Retry-After` powyżej 10 minut albo komunikatem dostawcy o limicie dziennym, np. plan darmowy):
  harmonogram wstrzymuje serię u tego dostawcy do odnowienia limitu; przebieg w toku kończy się z `api_error`
  i powtarza się po przerwie bez zużycia ponowienia całego przebiegu.

**Całego przebiegu:** przebieg zakończony `api_error` (6 nieudanych prób jednego zapytania) powtarza się od początku
na tej samej instancji i z tym samym ziarnem, z nowym `run_id` i kolejnym numerem próby przebiegu (`run_attempt`),
najwyżej 2 razy (3 próby łącznie). Wszystkie próby zostają w danych; analiza bierze ostatnią, a nieudane mają
`superseded_by`. Gdy wszystkie 3 próby kończą się `api_error`, komórka ma brak danych, raportowany w analizie
([analysis-plan.md](analysis-plan.md)); nie dokłada się innej instancji.

## 7. Strażnik budżetu

- **Koszt umowny:** koszt każdej odpowiedzi liczy się z tokenów (wejście, wejście z cache, zapis cache, wyjście
  z rozumowaniem) i z cennika płatnego planu w konfiguracji (z datą i źródłem), także dla Gemini i Groq na planie
  darmowym, żeby strażnik działał jednakowo; model lokalny ma koszt 0.
- **Przed startem przebiegu:** `wydane_seria + górny_koszt_przebiegu > budżet_serii` → przebieg nie startuje, seria
  stoi do decyzji właściciela. `górny_koszt_przebiegu` to koszt przebiegu, który dochodzi do limitu kroków (wzór
  i tabela w [design.md](design.md)).
- **Po każdej odpowiedzi:** `wydane_seria >= budżet_serii` albo `koszt_przebiegu >= 1,5 * górny_koszt_przebiegu` →
  koniec przebiegu z `cost_limit`, zapis tego, co jest. Drugi warunek łapie przebieg, który zużywa dużo więcej tokenów
  na krok, niż zakłada wzór (np. bardzo długie rozumowanie).
- **Współbieżność:** przy kilku przebiegach w locie limit miękki = `budżet_serii - liczba_w_locie *
  górny_koszt_przebiegu`.
- `budżet_serii` ustala właściciel przed pilotażem i przed pełnym badaniem na podstawie
  kosztorysu z [design.md](design.md); wartość trafia do konfiguracji serii.

## 8. Warunki zatrzymania i `end_reason`

Zamknięta lista (w schemacie zapisu jako `enum`, `schemas/`):

| `end_reason` | Kiedy |
|---|---|
| `done_solved` | model wywołał `done`, stan końcowy jest docelowy (wyszukiwanie: odpowiedź poprawna) |
| `done_unsolved` | model wywołał `done` przy stanie niedocelowym (wyszukiwanie: odpowiedź błędna) |
| `step_limit` | wyczerpany limit kroków (sekcja 3) |
| `too_many_errors` | 10 błędów walidacji z rzędu (sekcja 4) |
| `no_tool_call` | odpowiedź bez wywołania po przypomnieniu albo czwarta w przebiegu (sekcja 4) |
| `context_exceeded` | przekroczony kontekst (sekcja 5) |
| `time_limit` | przekroczony czas przebiegu (sekcja 5) |
| `cost_limit` | strażnik budżetu (sekcja 7) |
| `api_error` | 6 nieudanych prób jednego zapytania albo limit dzienny w toku (sekcja 6) |
| `interrupted` | przerwanie ręczne przez prowadzącego |

- Pierwszeństwo w jednej turze: wywołania przetwarza się po kolei; pierwszy spełniony warunek spośród `done`,
  `too_many_errors` i `step_limit` kończy przebieg, a reszta tury jest niewykonana (`skipped_reason`). Po turze
  sprawdza się `cost_limit` i `time_limit`.
- `solved` (stan docelowy osiągnięty) zapisuje się niezależnie od powodu końca: przebieg z `step_limit` może mieć
  `solved: true`, gdy model posortował tablicę, ale nie wywołał `done`. W wyszukiwaniu `solved` jest tylko przy
  `done_solved`. Która z tych definicji jest sukcesem w analizie: [analysis-plan.md](analysis-plan.md).
- Środowisko nie kończy przebiegu samo po osiągnięciu stanu docelowego ([prompts.md](prompts.md), sekcja 4).

## 9. Konfiguracja przebiegu

Konfiguracja (jeden plik na serię i warunek albo grupę pilotażu, w warunku `faults` jeden na typ błędu, każdy
z własnym `series_id`, np. `full-main`, `full-faults-one-off` i `full-faults-persistent` w serii `full`; wersjonowany
w repozytorium; format: `schemas/experiment-config.v2.schema.json`) i jej kopia
w `run_start` każdego przebiegu zawierają:

- model: dostawcę, `model` wysłany w zapytaniu, wersję (snapshot albo digest), wersję API (`anthropic-version`,
  wersja Responses API, wersja Gemini API), poziom rozumowania i dokładne pola, które go ustawiają, `max_tokens`,
  `tool_choice`, regułę wywołań równoległych (`parallel_tool_calls: true`) i to, czy wysłano `strict` (`strict_tools`);
- z odpowiedzi: `system_fingerprint` (OpenAI, gdy jest), identyfikator modelu zwrócony przez dostawcę;
- lokalnie: `seed`, `num_ctx`, `num_predict`, opcje z `/api/show`, wersję Ollama, sprzęt (GPU, VRAM, sterownik);
- limity: kroków (wzór i wartość), błędów z rzędu, przypomnień, czasu zapytania i przebiegu, `budżet_serii`,
  współczynnik strażnika, ponawianie (liczba prób, backoff);
- teksty: `prompt_version`, `prompt_variant`, hashe z [prompts.md](prompts.md); warunek (`main`, `faults`) i parametry
  błędów wstrzykiwanych ([fault-injection.md](fault-injection.md));
- cennik (wersja, data, źródło), datę i godzinę startu (UTC), wersję kodu (commit) i `env_version`.

Przykład jednej pozycji (szkic; nazwy pól ustala kontrakt danych):

```yaml
- provider: anthropic
  model: claude-sonnet-5-5
  version: claude-sonnet-5-5
  api_version: "<anthropic-version z dnia konfiguracji>"
  reasoning: {thinking: adaptive, effort: low}
  max_tokens: 8192
  tool_choice: auto
  parallel_tool_calls: true
  strict_tools: true
  sampling: provider_default
```
