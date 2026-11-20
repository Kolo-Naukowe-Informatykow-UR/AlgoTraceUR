# Teksty dla modeli: prompt systemowy, opisy zadań i narzędzi

Status: **przed pilotażem**, wersja tekstów `p1` (2026-11-20). Pilotaż może zmienić parafrazy,
format wyniku `compare` i wynik `move`; każda zmiana trafia do historii w [README](README.md) z datą i powodem, a tekst
dostaje nową wersję (`p2`, `p3`...).

Decyzje protokołu ([README.md](README.md), sekcja „Zakres”) zastosowane w tym pliku: D01 (zapowiedź algorytmu), D04 (kilka wywołań w jednej odpowiedzi),
D08 (wynik `move`), D09 (język). Ustawienia modeli i limity: [run-settings.md](run-settings.md); błędy wstrzykiwane:
[fault-injection.md](fault-injection.md).

## 1. Zasady pisania tekstów

- **Język (D09 A):** wszystkie teksty wysyłane do modeli są po angielsku, jednakowe dla wszystkich dostawców; różni się
  tylko opakowanie w format API (sekcja 8). Polskie tłumaczenie (sekcja 12) służy wyłącznie dokumentacji i nigdy nie
  trafia do modelu.
- **Neutralność:** tekst podaje stan początkowy, cel, narzędzia, znaczenie ich wyników i warunek końca. Nie podaje
  nazw algorytmów, nazw łamigłówek, które przywołują gotowe rozwiązanie, ani niczego o efektywności (liczba wywołań,
  „szybko”, „mało ruchów”). Lista słów zakazanych i sprawdzenie: sekcja 11.
- **Limity nie są ujawniane:** model nie dowiaduje się o limicie kroków, błędów, tokenów ani czasu. Limit podany w
  tekście byłby podpowiedzią o efektywności (zachęcałby do oszczędzania wywołań), a limity są ustawione z zapasem dla
  najwolniejszego algorytmu wzorcowego ([run-settings.md](run-settings.md)), więc nie odcinają poprawnych strategii.
- **Bez nazwy łamigłówki Hanoi:** opis podaje paliki, krążki i zasady, ale nie nazwę łamigłówki. Nazwa przywołuje
  zapamiętane rozwiązanie podręcznikowe i jego listę ruchów, a zasady bez nazwy są kompletne. Model może łamigłówkę
  rozpoznać sam; pokaże to jego zapowiedź (D01).
- **Zmienne w szablonach:** tylko `{N}` (rozmiar tablicy), `{last_index}` (`N - 1`), `{n}` (liczba krążków)
  i `{target}` (szukana liczba). Poza podstawieniem tych wartości tekst wysyła się dokładnie tak, jak w bloku
  (z podziałami wierszy, kodowanie UTF-8, końce wierszy LF, bez końcowego znaku nowego wiersza).
- **Opisy narzędzi nie zależą od rozmiaru:** schemat i opis narzędzia mówi „od 0 do N-1, gdzie N podaje zadanie”,
  więc definicje narzędzi są takie same dla wszystkich rozmiarów jednej rodziny, a konkretne wartości są w opisie
  zadania.
- **Wersja i hash:** zapis przebiegu (`run_start`) zawiera `prompt_version` (`p1`), `prompt_variant` (sekcja 10),
  SHA-256 promptu systemowego i opisu zadania po podstawieniu oraz SHA-256 definicji narzędzi w postaci neutralnej
  (sekcja 8) jako kanoniczny JSON (klucze posortowane, bez spacji), zanim adapter zamieni je na format dostawcy.

## 2. Przebieg rozmowy

1. Wiadomość systemowa: prompt systemowy (sekcja 3), wspólny dla trzech rodzin zadań.
2. Pierwsza wiadomość użytkownika: opis zadania danej rodziny (sekcja 5) z podstawionymi wartościami instancji;
   w wersji głównej kończy się zdaniem z prośbą o zapowiedź (sekcja 6).
3. Definicje narzędzi danej rodziny (sekcja 8) w każdym zapytaniu, `tool_choice: auto` (D01: wymuszone narzędzie
   pomija tekst przed wywołaniem; reszta ustawień w [run-settings.md](run-settings.md)).
4. Pętla: odpowiedź modelu, wykonanie wywołań, wyniki narzędzi (sekcja 9) w następnym zapytaniu. Po odpowiedzi bez
   wywołania narzędzia idzie przypomnienie (sekcja 7).
5. Koniec: wywołanie `done`, przypomnienie bez skutku albo limit ([run-settings.md](run-settings.md)). Po `done`
   model nie dostaje już zapytania; wynik `done` (`accepted`) trafia tylko do zapisu.

Kilka wywołań w jednej odpowiedzi (D04 A): środowisko wykonuje je po kolei, w kolejności z odpowiedzi, każde
waliduje osobno i każde dostaje własny wynik; błąd jednego wywołania nie wstrzymuje następnych. Wywołania po `done`
w tej samej odpowiedzi nie są wykonywane (`after_done`). Wszystkie wyniki tury wracają do modelu razem, w tej samej
kolejności. Model dowiaduje się o tej regule z promptu systemowego. Błąd `extra_call` z wcześniejszej propozycji projektu
środowiska nie występuje: D04 A dopuszcza kilka wywołań, więc nie
ma czego odrzucać (specyfikacja środowiska: [environment.md](../specs/environment.md)).

Treść rozumowania (bloki `thinking` Anthropic, podsumowania rozumowania OpenAI i Gemini) adapter odsyła w następnych
zapytaniach tak, jak wymaga dostawca, i zapisuje osobno; nie jest to deklaracja algorytmu (sekcja 6).

## 3. Prompt systemowy

Wersja główna, wspólna dla sortowania, Hanoi i wyszukiwania:

```text
You are working in a task environment that you can access only through the provided tools.
The state of the task is not shown to you. You learn about it only from the task description and from the results of your tool calls.
The task is described in the next message. Carry it out by calling the tools.
If one response contains several tool calls, they are executed one after another, in the order in which they appear.
An invalid tool call is not executed and does not change the state; its result explains what was wrong.
When you consider the task complete, call the tool done. It ends the task, and no further tool calls are possible after it.
```

Zdanie o kolejności wykonania wynika z D04 A: model, który wysyła kilka wywołań naraz, musi wiedzieć, że np.
`swap` po `compare` w tej samej odpowiedzi wykona się bez względu na wynik `compare`. Prompt nie zachęca do łączenia
wywołań ani do ich rozdzielania.

## 4. Co model wie, a czego nie

| Rodzina | Model wie | Model nie wie |
|---|---|---|
| sortowanie | N, pozycje 0..N-1, liczby są różne, cel (rosnąco), znaczenie `less` / `greater` i `ok`, że `done` kończy zadanie | wartości liczb i ich zakres, że to permutacja 1..N, limity |
| Hanoi | n, paliki 0-2, numery krążków 1..n według rozmiaru, stan początkowy (wszystkie na paliku 0), cel (wszystkie na paliku 2), zasady, że `move` zwraca `ok`, że `done` kończy zadanie | stan po ruchach nie jest mu podawany (D08 A), musi go śledzić sam; limity |
| wyszukiwanie | N, pozycje 0..N-1, liczby całkowite różne i rosnące, szukana liczba, że `read` zwraca liczbę z pozycji, że odpowiedź to pozycja albo -1 | wartości i ich zakres, czy liczba jest w tablicy, limity |

Wspólne dla wszystkich: model nie wie, ile wywołań wolno mu wykonać, że przebieg nie kończy się sam po osiągnięciu
celu ani czy `done` zostało przyjęte jako poprawne. Środowisko nie kończy przebiegu po osiągnięciu stanu docelowego
(to byłaby podpowiedź i ucięłoby końcowe sprawdzanie przez model); pole `solved` zapisuje się niezależnie od `done`.

Wartości `equal` w wyniku `compare` nie ma: liczby są różne (permutacje bez powtórzeń, [design.md](design.md)),
a `compare(i, i)` jest błędem `same_index`, więc porównanie dwóch równych liczb nie może się zdarzyć. Wariant
z powtórzeniami nie należy do tego badania.

## 5. Opisy zadań

### Sortowanie

```text
There is a hidden array a of {N} distinct numbers at positions 0 to {last_index}. You cannot see the numbers.

Goal: rearrange the numbers so that they are in increasing order, a[0] < a[1] < ... < a[{last_index}].

Tools:
- compare(i, j) returns "less" if a[i] < a[j] and "greater" if a[i] > a[j].
- swap(i, j) exchanges the numbers at positions i and j and returns "ok".
- done() ends the task.
In compare and swap, i and j are positions from 0 to {last_index}, and i must be different from j.

Before your first tool call, state in one sentence the approach you will use.
```

### Paliki i krążki (Hanoi)

```text
There are three pegs, numbered 0, 1 and 2, and {n} disks of different sizes, numbered from 1 (the smallest) to {n} (the largest).
At the start, all disks are on peg 0, with the largest at the bottom and the smallest at the top. Pegs 1 and 2 are empty.

Goal: get all disks onto peg 2, again with the largest at the bottom and the smallest at the top.

Rules: a move takes the top disk of one peg and puts it on top of another peg. A disk may never be put on a smaller disk.

Tools:
- move(from_peg, to_peg) moves the top disk of peg from_peg onto peg to_peg and returns "ok".
- done() ends the task.
In move, from_peg and to_peg are 0, 1 or 2, and they must be different.

Before your first tool call, state in one sentence the approach you will use.
```

### Wyszukiwanie

```text
There is a hidden array a of {N} distinct integers at positions 0 to {last_index}, in increasing order: a[0] < a[1] < ... < a[{last_index}]. You cannot see the numbers.

Goal: find the position of the number {target} in the array, or determine that {target} is not in the array.

Tools:
- read(index) returns the number at position index, where index is from 0 to {last_index}.
- done(index) ends the task with your answer: the position of {target}, or -1 if {target} is not in the array.

Before your first tool call, state in one sentence the approach you will use.
```

Wyszukiwanie nie podaje zakresu wartości: model może go poznać tylko przez `read` (np. skrajnych pozycji). Zakres,
z którego generator losuje liczby, i udział instancji z liczbą nieobecną ustala [design.md](design.md).

## 6. Zapowiedź algorytmu (D01 A)

Wersja główna kończy każdy opis zadania tym samym zdaniem, jako osobnym akapitem:

```text
Before your first tool call, state in one sentence the approach you will use.
```

- Słowo `approach` zamiast „algorithm”: nie sugeruje, że odpowiedź ma być nazwą algorytmu z podręcznika, a model,
  który taki algorytm wybrał, i tak go nazwie. Prośba o jedno zdanie, a nie o rozumowanie krok po kroku (Anthropic
  odradza to drugie przy narzędziach), przy `tool_choice: auto`.
- **Deklaracja w zapisie:** surowy widoczny tekst wszystkich odpowiedzi modelu od początku do odpowiedzi z pierwszym
  wywołaniem narzędzia włącznie (gdy model najpierw pisze samo zdanie, a narzędzie woła w następnej odpowiedzi po
  przypomnieniu, deklaracją jest tekst obu). Treść rozumowania (sekcja 2) nie jest deklaracją. Brak tekstu przed
  pierwszym wywołaniem to deklaracja pusta (zapisana jako pusty napis), nie błąd i nie powód przypomnienia.
- Etykieta zadeklarowanego algorytmu powstaje dopiero w analizie ([analysis-plan.md](analysis-plan.md)); zapis
  przechowuje tylko surowy tekst.
- **Grupa pilotażowa bez prośby** (`prompt_variant: no_announcement`): ten sam opis zadania bez ostatniego akapitu
  (zdanie i poprzedzający je pusty wiersz usunięte), reszta bez zmian. Deklarację zbiera się tak samo, z tekstu, który
  model napisze z własnej woli. Pilotaż porównuje wybór algorytmu z prośbą i bez niej ([design.md](design.md)).

## 7. Przypomnienie po odpowiedzi bez wywołania

Gdy odpowiedź modelu nie zawiera żadnego wywołania narzędzia (sam tekst albo pusta odpowiedź), środowisko wysyła
jako następną wiadomość użytkownika:

```text
Your last response did not contain a tool call. The task can only be carried out through tool calls. Call a tool to continue, or call done if you consider the task complete.
```

- Po przypomnieniu, jeśli następna odpowiedź też nie ma wywołania, przebieg kończy się z `end_reason: no_tool_call`.
- Odpowiedź bez wywołania nie jest błędem narzędzia: liczy się w `text_turns`, a przypomnienie w `reminders`; nie
  wlicza się do limitu błędów. Łączny limit przypomnień w przebiegu: [run-settings.md](run-settings.md).
- Odpowiedź ucięta limitem tokenów wyjścia bez wywołania też dostaje przypomnienie; jej `stop_reason` dostawcy trafia
  do zapisu.

## 8. Narzędzia: opisy i schematy JSON

Postać neutralna (z niej liczy się hash). Schematy są ścisłe: wszystkie pola wymagane, `additionalProperties: false`,
`strict: true` tam, gdzie API go przyjmuje. Schematy celowo **nie** mają `minimum` / `maximum`: część dostawców nie
obsługuje ich w trybie ścisłym, więc zakres sprawdzałby jeden dostawca, a inny nie; zakres podaje opis, a sprawdza
środowisko (błąd `out_of_range`), jednakowo dla wszystkich modeli.

### Sortowanie

```json
[
  {
    "name": "compare",
    "description": "Compares the numbers at positions i and j of the hidden array. Returns \"less\" if a[i] < a[j] and \"greater\" if a[i] > a[j].",
    "parameters": {
      "type": "object",
      "properties": {
        "i": {"type": "integer", "description": "A position from 0 to N-1, where N is the array size given in the task."},
        "j": {"type": "integer", "description": "A position from 0 to N-1, different from i."}
      },
      "required": ["i", "j"],
      "additionalProperties": false
    },
    "strict": true
  },
  {
    "name": "swap",
    "description": "Exchanges the numbers at positions i and j of the hidden array. Returns \"ok\".",
    "parameters": {
      "type": "object",
      "properties": {
        "i": {"type": "integer", "description": "A position from 0 to N-1, where N is the array size given in the task."},
        "j": {"type": "integer", "description": "A position from 0 to N-1, different from i."}
      },
      "required": ["i", "j"],
      "additionalProperties": false
    },
    "strict": true
  },
  {
    "name": "done",
    "description": "Ends the task. No tool calls are possible after it.",
    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": false},
    "strict": true
  }
]
```

### Hanoi

```json
[
  {
    "name": "move",
    "description": "Moves the top disk of peg from_peg onto peg to_peg. Returns \"ok\". A disk may never be put on a smaller disk.",
    "parameters": {
      "type": "object",
      "properties": {
        "from_peg": {"type": "integer", "description": "The peg to take the top disk from: 0, 1 or 2."},
        "to_peg": {"type": "integer", "description": "The peg to put the disk on: 0, 1 or 2, different from from_peg."}
      },
      "required": ["from_peg", "to_peg"],
      "additionalProperties": false
    },
    "strict": true
  },
  {
    "name": "done",
    "description": "Ends the task. No tool calls are possible after it.",
    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": false},
    "strict": true
  }
]
```

### Wyszukiwanie

```json
[
  {
    "name": "read",
    "description": "Returns the number at position index of the hidden array.",
    "parameters": {
      "type": "object",
      "properties": {
        "index": {"type": "integer", "description": "A position from 0 to N-1, where N is the array size given in the task."}
      },
      "required": ["index"],
      "additionalProperties": false
    },
    "strict": true
  },
  {
    "name": "done",
    "description": "Ends the task with your answer. No tool calls are possible after it.",
    "parameters": {
      "type": "object",
      "properties": {
        "index": {"type": "integer", "description": "The position of the number you were asked to find, or -1 if it is not in the array."}
      },
      "required": ["index"],
      "additionalProperties": false
    },
    "strict": true
  }
]
```

### Zamiana na format dostawcy (adaptery, `src/adapters/`)

| Dostawca | Gdzie trafia postać neutralna | `strict` |
|---|---|---|
| OpenAI (Responses API) | `tools: [{"type": "function", "name", "description", "parameters", "strict"}]` | tak |
| Anthropic | `tools: [{"name", "description", "input_schema", "strict"}]` (`parameters` jako `input_schema`) | tak |
| Google Gemini | `function_declarations` z `name`, `description` i schematem parametrów | brak odpowiednika, pole pominięte |
| Groq (`openai/gpt-oss-120b`) | format Chat Completions zgodny z OpenAI: `{"type": "function", "function": {...}}` | Do weryfikacji |
| Ollama (`qwen3:8b`) | `tools` w formacie zgodnym z OpenAI | brak odpowiednika, pole pominięte |

Adapter zmienia tylko opakowanie: nazwy, opisy i schemat parametrów zostają co do znaku. Tam, gdzie nie ma trybu
ścisłego, błędnie zbudowane argumenty są możliwe i środowisko zwraca `bad_arguments`; liczby błędów `bad_arguments`
porównuje się między modelami tylko opisowo, z tym zastrzeżeniem w zagrożeniach trafności
([analysis-plan.md](analysis-plan.md)). Konfiguracja przebiegu zapisuje, czy `strict` został wysłany.

## 9. Wyniki narzędzi i komunikaty błędów

Wynik udanego wywołania to krótki napis (bez cudzysłowów):

| Narzędzie | Wynik |
|---|---|
| `compare` | `less` albo `greater` |
| `swap` | `ok` |
| `move` | `ok` (D08 A: bez stanu palików) |
| `read` | liczba dziesiętnie, np. `42` |
| `done` | `accepted` (tylko w zapisie, model go nie dostaje) |

Błąd walidacji wraca jako wynik narzędzia z flagą błędu tam, gdzie API ją ma (`is_error: true` u Anthropic), a
u pozostałych dostawców jako sam tekst; tekst jest zawsze ten sam i zaczyna się od `Error:`. Błędne wywołanie nie
zmienia stanu i nie kończy przebiegu (do limitu błędów z [run-settings.md](run-settings.md)); liczy się do limitu
kroków, ale nie do porównań, zamian, ruchów ani odczytów algorytmu.

Kolejność sprawdzania (pierwszy pasujący błąd wygrywa): `after_done`, `unknown_tool`, `bad_arguments`,
`out_of_range`, `same_index`, `illegal_move`. Komunikaty (w nawiasach klamrowych wartości wstawiane przez
środowisko; `{name}` to nazwa z wywołania, `{tools}` to nazwy narzędzi rodziny rozdzielone przecinkami
i spacją, `{expected}` to lista argumentów z typami, np. `i (integer), j (integer)`, a dla `done()` słowo `none`):

```text
unknown_tool:
Error: unknown tool "{name}". Available tools: {tools}. The call was not executed.

bad_arguments:
Error: invalid arguments for {name}. Expected arguments: {expected}. The call was not executed.

out_of_range (compare, swap, read):
Error: position {value} is out of range. Valid positions are 0 to {last_index}. The call was not executed.

out_of_range (move):
Error: peg {value} does not exist. Valid pegs are 0, 1 and 2. The call was not executed.

out_of_range (done in the search task):
Error: {value} is not a valid answer. Give a position from 0 to {last_index}, or -1. The call was not executed.

same_index (compare, swap):
Error: i and j must be different. The call was not executed.

illegal_move, source peg empty:
Error: illegal move, peg {from_peg} has no disks. The call was not executed.

illegal_move, larger disk onto a smaller one:
Error: illegal move, a disk cannot be put on a smaller disk. The call was not executed.

illegal_move, same peg:
Error: illegal move, from_peg and to_peg must be different. The call was not executed.

after_done (recorded only, the model does not receive it):
Error: the task has already ended. The call was not executed.
```

Wiersze z nazwą błędu i dwukropkiem to etykiety dokumentacji; do modelu trafia tylko wiersz zaczynający się od
`Error:`. Przy `illegal_move` zapis ma też szczegół (`empty_peg`, `larger_on_smaller`, `same_peg`) w polu
`validation_detail` (wymaganie dla kontraktu danych, [README](README.md)). `move(p, p)` jest `illegal_move`, a nie
`same_index`, bo `same_index` dotyczy pozycji tablicy. Komunikat błędu Hanoi nie zdradza rozmiarów krążków.

Błędy wstrzykiwane w warunku z błędami narzędzi mają własne komunikaty i własne oznaczenie w zapisie:
[fault-injection.md](fault-injection.md).

## 10. Warianty do pilotażu

Każdy wariant ma własną wartość `prompt_variant` w zapisie; seria główna używa `main`. Zdanie z prośbą o zapowiedź
jest takie samo we wszystkich wariantach poza `no_announcement`, żeby parafraza nie mieszała się z D01. Na których
modelach i zadaniach działa każdy wariant, ustala [design.md](design.md).

| `prompt_variant` | Co się zmienia | Po co |
|---|---|---|
| `main` | nic (sekcje 3-9) | seria główna |
| `no_announcement` | brak akapitu z prośbą o zapowiedź (sekcja 6) | wpływ prośby na wybór algorytmu (D01) |
| `para_order` | kolejność zdań promptu systemowego i opisu sortowania, kolejność narzędzi | wrażliwość na kolejność (Sclar i in.) |
| `para_names` | nazwy narzędzi we wszystkich tekstach i schematach | wrażliwość na nazwy narzędzi |
| `para_wording` | inne słowa przy tej samej treści promptu systemowego i opisu sortowania | wrażliwość na sformułowanie |
| `hanoi_state` | `move` zwraca stan palików (D08: tylko pilotaż) | czy zwrot stanu zmienia skuteczność i strategię |
| `compare_symbols` | `compare` zwraca `<` / `>` zamiast słów | format wyniku `compare` (punkt pilotażu) |

### `para_order`

Prompt systemowy:

```text
The task is described in the next message. Carry it out by calling the provided tools; you can access the task environment only through them.
When you consider the task complete, call the tool done. It ends the task, and no further tool calls are possible after it.
An invalid tool call is not executed and does not change the state; its result explains what was wrong.
If one response contains several tool calls, they are executed one after another, in the order in which they appear.
The state of the task is not shown to you. You learn about it only from the task description and from the results of your tool calls.
```

Opis sortowania (definicje narzędzi w kolejności `done`, `swap`, `compare`):

```text
Goal: rearrange the numbers of a hidden array a so that they are in increasing order, a[0] < a[1] < ... < a[{last_index}].

The array has {N} distinct numbers at positions 0 to {last_index}. You cannot see the numbers.

Tools:
- done() ends the task.
- swap(i, j) exchanges the numbers at positions i and j and returns "ok".
- compare(i, j) returns "less" if a[i] < a[j] and "greater" if a[i] > a[j].
In compare and swap, i and j are positions from 0 to {last_index}, and i must be different from j.

Before your first tool call, state in one sentence the approach you will use.
```

### `para_names`

Zamiana nazw we wszystkich tekstach wariantu `main` (prompt systemowy, opisy zadań, przypomnienie, opisy narzędzi,
komunikaty błędów), nazwy argumentów bez zmian:

| `main` | `para_names` |
|---|---|
| `compare` | `check_pair` |
| `swap` | `exchange` |
| `move` | `move_disk` |
| `read` | `get_value` |
| `done` | `finish` |

Zamienia się całe słowo narzędzia (także w zdaniach „call the tool done” i „call done”); w sortowaniu i wyszukiwaniu
słowo „done” nie występuje w innym znaczeniu, więc zamiana jest jednoznaczna.

### `para_wording`

Prompt systemowy:

```text
You act in an environment that can be used only by means of the tools listed.
You do not see the task state. Everything you know about it comes from the task description and from what your tool calls return.
The next message describes the task. Use the tools to accomplish it.
When a response includes more than one tool call, the calls run one by one, in the order given.
A tool call that is not valid is rejected without any effect on the state, and its result says what the problem was.
Once you regard the task as finished, call done. This closes the task; no tool calls can follow it.
```

Opis sortowania (definicje narzędzi jak w `main`):

```text
A list a with {N} different values is hidden from you; its indices are 0 to {last_index}.

Task: reorder the values into ascending order, so that a[0] < a[1] < ... < a[{last_index}].

Tools:
- compare(i, j) answers "less" when a[i] < a[j] and "greater" when a[i] > a[j].
- swap(i, j) puts the value from index i at index j and the value from index j at index i, and answers "ok".
- done() closes the task.
For compare and swap, i and j are indices between 0 and {last_index}, and they may not be equal.

Before your first tool call, state in one sentence the approach you will use.
```

`para_order` i `para_wording` są napisane dla sortowania, bo pytania 2 i 3 dotyczą głównie sortowania; Hanoi
i wyszukiwanie mają w pilotażu tylko `para_names`.

### `hanoi_state`

W opisie Hanoi zdanie o `move` brzmi:

```text
- move(from_peg, to_peg) moves the top disk of peg from_peg onto peg to_peg and returns "ok" followed by the disks on each peg, listed from bottom to top.
```

Opis narzędzia `move`: `Moves the top disk of peg from_peg onto peg to_peg. Returns "ok" followed by the disks on
each peg, listed from bottom to top. A disk may never be put on a smaller disk.` Wynik, np. po pierwszym ruchu
z paliku 0 na palik 2 przy n = 3:

```text
ok. Peg 0: [3, 2]. Peg 1: []. Peg 2: [1].
```

### `compare_symbols`

W opisie sortowania i w opisie narzędzia `compare` słowa wyniku zamienia się na symbole:

```text
- compare(i, j) returns "<" if a[i] < a[j] and ">" if a[i] > a[j].
```

Opis narzędzia: `Compares the numbers at positions i and j of the hidden array. Returns "<" if a[i] < a[j] and ">"
if a[i] > a[j].` Wynik to `<` albo `>`.

## 11. Słowa zakazane i sprawdzenie neutralności

Bloki tekstów dla modeli (bloki `text` i `json` w tym pliku) nie mogą zawierać trafień wzorca (bez rozróżniania
wielkości liter):

`bubble|insertion|selection|quick|merge|heap|binary|interpolat|linear|recurs|divide|efficient|optimal|minim|fewest|fast`

Lista dodatkowa, sprawdzana tak samo (nazwy łamigłówek, elementy algorytmów i słowa o koszcie):

`hanoi|tower|pivot|partition|bisect|half|middle|sequential|scan|few|least|best|cost|limit|budget|count|step`

Sprawdzenie (Python 3, z katalogu repozytorium; wynik `0 hits` oznacza zgodność):

```python
import re, pathlib
text = pathlib.Path("docs/protocol/prompts.md").read_text(encoding="utf-8")
blocks = re.findall(r"```(?:text|json)\n(.*?)```", text, flags=re.S)
words = ("bubble|insertion|selection|quick|merge|heap|binary|interpolat|linear|recurs|divide|efficient|optimal"
         "|minim|fewest|fast|hanoi|tower|pivot|partition|bisect|half|middle|sequential|scan|few|least|best|cost"
         "|limit|budget|count|step")
hits = [m.group(0) for b in blocks for m in re.finditer(words, b, flags=re.I)]
print(f"{len(hits)} hits", sorted(set(hits)))
```

Ostatni wynik sprawdzenia: sekcja „Historia zmian” w [README](README.md).

## 12. Tłumaczenie polskie (tylko dokumentacja)

Prompt systemowy:

```text
Pracujesz w środowisku zadania, do którego masz dostęp wyłącznie przez udostępnione narzędzia.
Stan zadania nie jest ci pokazywany. Dowiadujesz się o nim tylko z opisu zadania i z wyników swoich wywołań narzędzi.
Zadanie jest opisane w następnej wiadomości. Wykonaj je, wywołując narzędzia.
Jeśli jedna odpowiedź zawiera kilka wywołań narzędzi, są one wykonywane jedno po drugim, w kolejności, w jakiej występują.
Niepoprawne wywołanie narzędzia nie jest wykonywane i nie zmienia stanu; jego wynik wyjaśnia, co było nie tak.
Gdy uznasz zadanie za ukończone, wywołaj narzędzie done. Kończy ono zadanie i po nim nie są możliwe żadne wywołania.
```

Sortowanie:

```text
Istnieje ukryta tablica a złożona z {N} różnych liczb na pozycjach od 0 do {last_index}. Nie widzisz tych liczb.

Cel: przestaw liczby tak, żeby były w kolejności rosnącej, a[0] < a[1] < ... < a[{last_index}].

Narzędzia:
- compare(i, j) zwraca "less", jeśli a[i] < a[j], i "greater", jeśli a[i] > a[j].
- swap(i, j) zamienia liczby na pozycjach i oraz j i zwraca "ok".
- done() kończy zadanie.
W compare i swap i oraz j to pozycje od 0 do {last_index}, a i musi się różnić od j.

Przed pierwszym wywołaniem narzędzia podaj w jednym zdaniu sposób, którego użyjesz.
```

Paliki i krążki:

```text
Są trzy paliki o numerach 0, 1 i 2 oraz {n} krążków różnej wielkości o numerach od 1 (najmniejszy) do {n} (największy).
Na początku wszystkie krążki są na paliku 0, największy na dole, najmniejszy na górze. Paliki 1 i 2 są puste.

Cel: przenieś wszystkie krążki na palik 2, znów największy na dole, najmniejszy na górze.

Zasady: ruch zdejmuje górny krążek z jednego palika i kładzie go na wierzch innego palika. Krążka nie wolno nigdy położyć na mniejszym krążku.

Narzędzia:
- move(from_peg, to_peg) przenosi górny krążek z palika from_peg na palik to_peg i zwraca "ok".
- done() kończy zadanie.
W move from_peg i to_peg to 0, 1 albo 2 i muszą być różne.

Przed pierwszym wywołaniem narzędzia podaj w jednym zdaniu sposób, którego użyjesz.
```

Wyszukiwanie:

```text
Istnieje ukryta tablica a złożona z {N} różnych liczb całkowitych na pozycjach od 0 do {last_index}, w kolejności rosnącej: a[0] < a[1] < ... < a[{last_index}]. Nie widzisz tych liczb.

Cel: znajdź pozycję liczby {target} w tablicy albo ustal, że {target} nie ma w tablicy.

Narzędzia:
- read(index) zwraca liczbę z pozycji index, gdzie index jest od 0 do {last_index}.
- done(index) kończy zadanie twoją odpowiedzią: pozycją liczby {target} albo -1, jeśli {target} nie ma w tablicy.

Przed pierwszym wywołaniem narzędzia podaj w jednym zdaniu sposób, którego użyjesz.
```

Przypomnienie:

```text
Twoja ostatnia odpowiedź nie zawierała wywołania narzędzia. Zadanie można wykonać tylko przez wywołania narzędzi. Wywołaj narzędzie, żeby kontynuować, albo wywołaj done, jeśli uznajesz zadanie za ukończone.
```

## 13. Do weryfikacji

> [!question] Do weryfikacji
> - Czy Groq przyjmuje `strict` w definicji funkcji dla `openai/gpt-oss-120b` i czy Gemini przyjmuje
>   `additionalProperties: false` w schemacie parametrów (adaptery, `src/adapters/`; przy odrzuceniu pole się pomija
>   i zapisuje to w konfiguracji).
> - Czy pusty obiekt `properties` w `done()` przechodzi w trybie ścisłym u każdego dostawcy zestawu A (pierwszy
>   test adapterów).
