# Specyfikacja: adaptery dostawców (`src/adapters/`)

C# / .NET 10 (`net10.0`), biblioteka `AlgoTrace.Adapters`. Status: kod jeszcze nie istnieje. Każdy adapter to
`IChatClient` z `Microsoft.Extensions.AI` bez `UseFunctionInvocation`, nad oficjalnym SDK dostawcy, z własnym
ponawianiem i zapisem surowych żądań. Łączy się ze środowiskiem ([environment.md](environment.md)) tylko przez
`IChatClient` (sekcja 4) i z serią ([runner.md](runner.md)), która tworzy adaptery z konfiguracji. Opis folderu:
[src/adapters/README.md](../../src/adapters/README.md).

## 1. Cel

Jednakowy dla wszystkich dostawców sposób zadania modelowi pytania: wiadomości i narzędzia (postać neutralna,
[prompts.md](../protocol/prompts.md) §8) wchodzą, `ChatResponse` z wywołaniami, tokenami, powodem zakończenia i liczbą
prób wychodzi. Adapter zmienia opakowanie (format API), nie treść, i zapisuje to, co dostawca odesłał, bez poprawiania.

## 2. Granice

- Nie wykonuje ani nie waliduje narzędzi, nie odrzuca wywołań nadmiarowych (wszystkie wywołania tury wykonuje po
  kolei środowisko, [run-settings.md](../protocol/run-settings.md) §1) i nie reaguje na turę bez wywołania.
- Nie parsuje wywołań zapisanych tekstem (Ollama): zwraca `content` jako tekst.
- Nie liczy kosztu ani budżetu, nie pilnuje tempa (RPM) i nie powtarza przebiegów: to seria ([runner.md](runner.md)).
  Adapter ponawia tylko pojedyncze zapytanie.
- Nie wykrywa cichego obcinania kontekstu Ollamy: robi to środowisko z `usage` i `num_ctx`.
- Nie czyta plików konfiguracji ani promptów i nie zapisuje przebiegu `<run_id>.jsonl` (tylko plik surowy).

## 3. Wejścia i wyjścia

**Wejście.** (1) Pozycja `models[]` z [experiment-config.v2.schema.json](../../schemas/experiment-config.v2.schema.json)
(`provider`, `model`, `model_version`, `api`, `settings`, `timeouts`, `local`, `price`; plik
`experiments/<series_id>.json`) oraz `retries` i `output.save_raw` tej konfiguracji. (2) Zapytania `GetResponseAsync`
(sekcja 4). Klucz API adapter czyta ze zmiennej o nazwie z `api.api_key_env`; w żadnym pliku klucza nie ma.

**Wyjście.**
- `ChatResponse` według umowy (sekcja 4); środowisko zapisuje z niego `model_turn`
  ([run-event.v2.schema.json](../../schemas/run-event.v2.schema.json)) w `data/runs/<series_id>/<run_id>.jsonl`
  (`output.runs_dir`).
- Plik surowy `<runs_dir>/<run_id>.raw.jsonl` (gdy `save_raw: true`), jedna linia JSON na zapytanie (format własny):
  `{"n":3,"ts":"...","method":"POST","url":"...","request":{...},"attempts":[{"status":529,"headers":{...},
  "body":...,"duration_ms":210,"wait_ms":2000},...]}`; `n` to numer zapytania od 1 (równy numerowi tury), ostatnia
  pozycja `attempts` jest odpowiedzią końcową. Przed zapisem znikają nagłówki `authorization`, `x-api-key`,
  `x-goog-api-key`, `api-key`, `cookie`, `proxy-authorization` i parametr adresu `key`.

## 4. Interfejsy

### 4.1 Umowa `IChatClient` ze środowiskiem

Środowisko i adaptery łączą się tylko `IChatClient`, więc wszystko, czego nie ma we wspólnym modelu, idzie w
`AdditionalProperties` pod kluczami z prefiksem `algotrace.`. Środowisko nie zna dostawcy: ustawienia dostawcy
(rozumowanie, `num_ctx`, `seed` Ollamy, wersja API, klucz) adapter dostaje przy tworzeniu z konfiguracji modelu, nie w
każdym zapytaniu. Ta sama umowa jest w [environment.md](environment.md).

**Zapytanie (środowisko → adapter): `GetResponseAsync(messages, options, ct)`**

| Element | Postać |
|---|---|
| prompt systemowy | `ChatMessage(ChatRole.System, text)` |
| opis zadania, przypomnienie | `ChatMessage(ChatRole.User, text)` |
| poprzednie odpowiedzi modelu | wiadomości z `ChatResponse.Messages` bez zmian (tekst, `TextReasoningContent`, `FunctionCallContent`), bo dostawcy wymagają odesłania rozumowania i stały prefiks daje cache |
| wyniki narzędzi tury | jedna `ChatMessage(ChatRole.Tool, ...)` z `FunctionResultContent(callId, result)` w kolejności wywołań; `result` to napis wysłany modelowi |
| flaga błędu wyniku | `FunctionResultContent.AdditionalProperties["algotrace.is_error"] = true` (Anthropic: `is_error`; inni: sam tekst) |
| narzędzia | `options.Tools`: deklaracje z postaci neutralnej (`prompts.md` §8: nazwa, opis, schemat parametrów co do znaku), bez implementacji (`AIFunctionDeclaration`) |
| `tool_choice` | `options.ToolMode = ChatToolMode.Auto` |
| wywołania równoległe | `options.AllowMultipleToolCalls = true` |
| limit odpowiedzi | `options.MaxOutputTokens` = `max_output_tokens` modelu |
| `strict` | `options.AdditionalProperties["algotrace.strict_tools"]` (bool z konfiguracji); adapter wysyła `strict` tylko tam, gdzie API go ma |

**Odpowiedź (adapter → środowisko): `ChatResponse`**

| Pole zapisu (`model_turn`) | Skąd |
|---|---|
| `text` | połączone `TextContent` odpowiedzi (`null`, gdy brak) |
| `reasoning_text` | `TextReasoningContent` (`null`, gdy brak) |
| `tool_calls[].id`, `name` | `FunctionCallContent.CallId`, `Name` |
| `tool_calls[].arguments_raw` | `FunctionCallContent.AdditionalProperties["algotrace.arguments_raw"]`: napis argumentów dokładnie taki, jaki przysłał dostawca (Gemini i Ollama dają obiekt: adapter serializuje go bez zmiany kolejności) |
| `finish_reason` | `ChatResponse.FinishReason` zmapowany na `tool_call`, `stop`, `length`, `content_filter`, `pause`, `error`, `other` (wartości spoza `ChatFinishReason` jako `new ChatFinishReason("pause")` itd.) |
| `finish_reason_raw` | `AdditionalProperties["algotrace.finish_reason_raw"]` |
| `model_returned`, `response_id` | `ChatResponse.ModelId`, `ResponseId` |
| `system_fingerprint` | `AdditionalProperties["algotrace.system_fingerprint"]` (OpenAI, gdy jest) |
| `usage` | `ChatResponse.Usage`: `InputTokenCount`, `CachedInputTokenCount`, `OutputTokenCount`, `ReasoningTokenCount`; `cache_write` z `Usage.AdditionalCounts["algotrace.cache_write"]`; brak = `null` |
| `latency_ms` | `AdditionalProperties["algotrace.latency_ms"]` (czas udanej próby) |
| `attempts`, `retries` | `AdditionalProperties["algotrace.attempts"]` (int, od 1), `["algotrace.retries"]` (lista `{status, error_type, wait_ms}` nieudanych prób) |
| `raw_ref` | `AdditionalProperties["algotrace.raw_ref"]`: odnośnik do linii w `<run_id>.raw.jsonl` albo `null` (gdy `save_raw: false`) |

**Niepowodzenie zapytania.** Adapter nie rzuca wyjątku po wyczerpaniu prób (wyjątek gubiłby próby): zwraca
`ChatResponse` bez treści z `FinishReason = new ChatFinishReason("error")` i `AdditionalProperties`:

- `algotrace.error_kind`: `api_error` (6 nieudanych prób albo błąd nieponawiany), `daily_limit` (limit dzienny),
  `context_exceeded` (dostawca odrzucił długość kontekstu), `provider_funds` (brak środków / limit wydatków);
- `algotrace.error_type`: typ błędu dostawcy (np. `overloaded_error` przy HTTP 529), przy limicie dziennym dokładnie
  `daily_limit`;
- `algotrace.error_message`: krótki opis bez sekretów (np. `6 attempts of the request for turn 2 failed with HTTP 529`);
  plus `attempts`, `retries` jak wyżej.

Nieudane zapytanie nie daje zdarzenia `model_turn` (wzór: `schemas/examples/run.api-error-n3.jsonl`, gdzie po turze 1
jest od razu `run_end`). Środowisko kończy przebieg: `context_exceeded` → `end_reason: context_exceeded`, pozostałe →
`api_error`; `run_end.error = {type: <error_type>, message: <error_message>}`; seria decyduje o ponowieniu
(`daily_limit` nie zużywa `max_run_retries`, `provider_funds` zatrzymuje kolejkę dostawcy). Anulowanie
(`CancellationToken`) to jedyny wyjątek, który przechodzi przez granicę (`OperationCanceledException` →
`end_reason: interrupted`).

### 4.2 Uzupełnienia umowy od strony adaptera (propozycja)

1. Adapter powstaje na jeden przebieg (`HttpClient` jest wspólny dla dostawcy), bo `raw_ref` zależy od `run_id`, a
   `seed` Ollamy od instancji.
2. `tool_call` też tworzy `new ChatFinishReason("tool_call")`: standardowe `ChatFinishReason.ToolCalls` ma wartość
   `tool_calls`, a środowisko porównuje napisy ze schematem.
3. `algotrace.retries` przy niepowodzeniu ma wszystkie nieudane próby, także ostatnią (`wait_ms: 0`); przy sukcesie
   `attempts - 1` wpisów.
4. `algotrace.raw_ref` = `<run_id>.raw.jsonl#<n>`, `n` to numer zapytania w kliencie (równy numerowi tury). Zapytanie
   nieudane też dostaje linię pliku surowego.
5. Środowisko odsyła obiekty `ChatMessage` z `ChatResponse.Messages` tak, jak je dostało (nie odtwarza ich z JSON-u):
   adaptery trzymają w `RawRepresentation` elementy dostawcy (bloki `thinking`, elementy `reasoning`, części z
   `thoughtSignature`).
6. Dla `run_start` klient daje: `JsonObject SettingsSent` (parametry dokładnie jak wysłane, nazwy dostawcy, bez narzędzi,
   wiadomości i sekretów), `bool StrictToolsSent` i `Task<LocalServerInfo?> ProbeAsync(ct)` (Ollama: pola jak
   `software.local_server` oraz `digest` modelu do porównania z `model_version`).
7. `options.ToolMode` `RequireAny` i `None` jest mapowany na odpowiedniki dostawcy (konfiguracja dopuszcza `required`,
   `none`); protokół używa tylko `Auto`.

### 4.3 Fabryka i klasy (propozycja sygnatur)

```csharp
public sealed record AdapterRunContext(string RunId, string? RawLogPath, long? Seed); // RawLogPath null = save_raw false
public sealed record AdapterRetryOptions(int MaxApiRetries, double InitialBackoffS, double MaxBackoffS);

public static class AdapterFactory
{
    public static ProviderChatClient Create(ModelEntry model, AdapterRetryOptions retry, AdapterRunContext run,
        AdapterTestHooks? hooks = null);   // hooks: innerHandler, getEnv, delay, jitter (testy)
}
public abstract class ProviderChatClient : IChatClient
{
    public JsonObject SettingsSent { get; }
    public bool StrictToolsSent { get; }
    public virtual Task<LocalServerInfo?> ProbeAsync(CancellationToken ct) => Task.FromResult<LocalServerInfo?>(null);
}
```

`ModelEntry` to rekord z polami `models[]` konfiguracji. `Seed` z kontekstu (ziarno instancji) zastępuje
`settings.seed` tylko w Ollamie. Jedna klasa na rodzinę API; `provider` ze [schematu](../../schemas/common.v2.schema.json)
wybiera klasę:

| `provider` | Klasa | API, domyślny adres | SDK |
|---|---|---|---|
| `anthropic` | `AnthropicClient` | Messages, `https://api.anthropic.com`, `anthropic-version` = `api.api_version` | `Anthropic` |
| `openai` | `OpenAiResponsesClient` | Responses, `store: false` | `OpenAI` |
| `gcp.gen_ai` | `GeminiClient` | `generateContent` | `Google.GenAI` |
| `groq`, `mistral_ai`, `openai_compatible` | `ChatCompletionsClient` | Chat Completions (`https://api.groq.com/openai/v1`, `https://api.mistral.ai/v1` albo `api.base_url`) | `OpenAI`, własny adres |
| `ollama` | `OllamaClient` | `POST /api/chat` | `HttpClient` + `System.Text.Json` |

Ustawienia (`settings`, `null` = nie wysyłać) trafiają do żądania: limit odpowiedzi jako `max_tokens` (Anthropic,
Mistral), `max_output_tokens` (OpenAI), `generationConfig.maxOutputTokens` (Gemini), `max_completion_tokens` (Groq),
`options.num_predict` (Ollama); `reasoning` według [run-settings.md](../protocol/run-settings.md) §2 (Anthropic
`thinking` + `output_config.effort`, OpenAI `reasoning.effort`, Gemini `thinkingConfig.thinkingLevel`, Chat
`reasoning_effort`, Ollama `think` = `false` przy `mode: none`); `parallel_tool_calls: true` tylko OpenAI i Chat;
`provider_options` dosłownie do ciała; `temperature`, `top_p`, `seed` tylko gdy nie są `null` (Ollama: `options.seed`).
`SettingsSent` powstaje z tego samego obiektu, który trafia do żądania.

### 4.4 Mapowanie powodu zakończenia

`finish_reason_raw` to wartość dostawcy bez zmian. Wywołania poznaje się po ich obecności w odpowiedzi.

| Rodzina | Wartość dostawcy → `finish_reason` |
|---|---|
| Anthropic | `tool_use` → `tool_call`; `end_turn`, `stop_sequence` → `stop`; `max_tokens`, `model_context_window_exceeded` → `length`; `pause_turn` → `pause`; `refusal` → `content_filter`; inne → `other` |
| OpenAI Responses | `completed` z `function_call` → `tool_call`; `completed` bez wywołań → `stop`; `incomplete`/`max_output_tokens` → `length`; `incomplete`/`content_filter` albo element `refusal` → `content_filter`; `failed` → `error`; inne → `other` |
| Gemini | `STOP` z częścią `functionCall` → `tool_call`; `STOP` → `stop`; `MAX_TOKENS` → `length`; `SAFETY`, `RECITATION`, `BLOCKLIST`, `PROHIBITED_CONTENT`, `SPII` → `content_filter`; `MALFORMED_FUNCTION_CALL`, `UNEXPECTED_TOOL_CALL`, `TOO_MANY_TOOL_CALLS`, `MISSING_THOUGHT_SIGNATURE`, `MALFORMED_RESPONSE` → `error`; inne → `other` |
| Chat Completions | `tool_calls` albo `stop` z niepustym `tool_calls` → `tool_call`; `stop` → `stop`; `length`, `model_length` → `length`; `content_filter` → `content_filter`; `error` → `error`; inne → `other` |
| Ollama | niepuste `message.tool_calls` → `tool_call`; `stop` → `stop`; `length` → `length`; inne (`load`) → `other` |

### 4.5 Mapowanie zużycia tokenów

`input` zawiera `cached_input` (`usage` w [common.v2.schema.json](../../schemas/common.v2.schema.json)); brak pola u
dostawcy to `null`. Pola dostawców: [provider-apis.md](../knowledge/provider-apis.md) §7.

| Rodzina | `input` | `cached_input` | `cache_write` | `output` | `reasoning` |
|---|---|---|---|---|---|
| Anthropic | `input_tokens` + `cache_read_input_tokens` + `cache_creation_input_tokens` | `cache_read_input_tokens` | `cache_creation_input_tokens` | `output_tokens` | `output_tokens_details.thinking_tokens` |
| OpenAI | `input_tokens` | `input_tokens_details.cached_tokens` | `null` | `output_tokens` | `output_tokens_details.reasoning_tokens` |
| Chat Completions | `prompt_tokens` | `prompt_tokens_details.cached_tokens` | `null` | `completion_tokens` | `completion_tokens_details.reasoning_tokens` |
| Gemini | `promptTokenCount` | `cachedContentTokenCount` | `null` | `candidatesTokenCount` + `thoughtsTokenCount` | `thoughtsTokenCount` |
| Ollama | `prompt_eval_count` | `null` | `null` | `eval_count` | `null` |

## 5. Zachowanie krok po kroku

Jedno `GetResponseAsync` (numer zapytania `n` rośnie o 1):

1. **Budowa żądania z postaci neutralnej.** System: pole systemowe API (Anthropic `system`, Gemini
   `systemInstruction`, reszta pierwsza wiadomość). Sąsiednie wiadomości tej samej roli Anthropic i Gemini łączy w
   jedną. Wywołania i rozumowanie poprzednich tur odtwarza z `RawRepresentation`, a gdy go brak, z pól (`ProtectedData`
   niesie `signature`, `encrypted_content`, `thoughtSignature`). Wyniki narzędzi: Anthropic jedna wiadomość `user` z
   `tool_result` na początku (z `is_error`) i bez tekstu po nich; Gemini jeden `Content` z `functionResponse` (`name`
   z wywołania o tym `callId`); OpenAI `function_call_output`; Chat i Ollama wiadomości `tool`. Narzędzia: schemat
   co do znaku (Gemini `parametersJsonSchema`), `strict` tylko gdy API go ma i `algotrace.strict_tools` jest `true`
   ([provider-apis.md](../knowledge/provider-apis.md) §2). Ustawienia: 4.3.
2. **Wysłanie.** SDK (ponawianie wyłączone) albo `HttpClient` Ollamy przez `RecordingHandler`, który zapisuje ciało,
   stan i nagłówki każdej próby. Limit próby: `timeouts.request_timeout_s`; czas liczy zegar monotoniczny.
3. **Ponawianie** ([run-settings.md](../protocol/run-settings.md) §6): najwyżej `max_api_retries + 1` prób (6).
   Ponawiane: przekroczenie czasu (`status: null`, `error_type: timeout`), błąd sieci (`network_error`), HTTP 408, 409,
   429, 500, 502, 503, 504, 529. Czekanie po `k`-tej nieudanej próbie: `max(Retry-After, backoff_k)`,
   `backoff_k = min(max_backoff_s, initial_backoff_s * 2^(k-1)) * (1 + 0,25 * u)`, `u` z `[0,1)` (w testach 0);
   `Retry-After` to sekundy albo data HTTP. Wpis `{status, error_type, wait_ms}` na każdą nieudaną próbę;
   `error_type` to typ z ciała błędu dostawcy (`error.type`, `error.code`, `error.status`), a bez niego `http_<status>`.
4. **Mapowanie odpowiedzi:** tekst, rozumowanie, wywołania (`arguments_raw` z surowego ciała przez
   `JsonElement.GetRawText()`, nie z obiektu SDK), `finish_reason`, `usage`, `ModelId`, `ResponseId`,
   `system_fingerprint`, `latency_ms`, `attempts`, `retries`. Gdy dostawca nie nadaje identyfikatora wywołania (Gemini,
   Ollama): `call_<n>_<indeks>`.
5. **Zapis surowy** (gdy `RawLogPath` nie jest `null`): linia dopisana i zapisana na dysk przed zwrotem; `raw_ref` =
   `<run_id>.raw.jsonl#<n>`.
6. **Zwrot:** `ChatResponse` albo niepowodzenie (sekcja 6). Anulowanie w dowolnym miejscu (także w czasie czekania)
   przerywa `OperationCanceledException`.

## 6. Błędy i przypadki brzegowe

- **Ponawiane:** jak w kroku 3. Po 6 nieudanych próbach: `error_kind: api_error`, `error_type` ostatniego błędu,
  `error_message` `6 attempts of the request for turn <n> failed with HTTP <status>` (sieć, czas: `... with <error_type>`).
- **Nieponawiane:** 400 (poza kontekstem i środkami), 401, 403, 404, 422 oraz każdy inny kod (413, 501): jedna próba,
  `error_kind: api_error`.
- **Limit dzienny:** 429 z `Retry-After` powyżej 600 s albo z komunikatem o limicie dziennym ("per day", "daily", "RPD",
  "TPD"): bez czekania i dalszych prób, `error_kind` i `error_type` `daily_limit`.
- **Kontekst:** 400 z markerem długości (Anthropic "prompt is too long", OpenAI i Groq `context_length_exceeded`, Gemini o
  liczbie tokenów wejścia, Mistral "too large for model") → `context_exceeded`, bez ponowienia. Markery są w jednej
  tabeli w kodzie.
- **Brak środków:** 402, OpenAI 429 `insufficient_quota`, Anthropic 429 o limicie wydatków, 400 o saldzie →
  `provider_funds`, bez ponowienia.
- **Odpowiedź bez wywołań:** zwykły sukces (`finish_reason: stop`, `tool_calls` puste); to zdarzenie przebiegu.
- **Argumenty niebędące JSON-em** (obcięte, puste): `arguments_raw` bez zmian; adapter nie naprawia, walidacja jest po
  stronie środowiska (`bad_arguments`).
- **Ucięta odpowiedź:** `finish_reason: length`, wywołania zostają, jak przyszły; bez ponowienia z większym limitem.
- **Kilka wywołań w turze:** wszystkie w kolejności odpowiedzi. **Odpowiedź 200 bez treści:** `text: null`.
- **Brak klucza** w zmiennej środowiskowej: `InvalidOperationException` przy tworzeniu adaptera, z nazwą zmiennej.

## 7. Wymagania protokołu

- Ustawienia modeli zestawu A i to, co adapter wysyła: [run-settings.md](../protocol/run-settings.md) §2.
- Brak parametrów próbkowania (poza `seed` Ollamy), `tool_choice: auto`, wywołania równoległe nigdy nie wyłączane:
  [run-settings.md](../protocol/run-settings.md) §1.
- Ponawianie, `Retry-After`, 6 prób, limit dzienny, brak środków: [run-settings.md](../protocol/run-settings.md) §6.
- Limit czasu próby i kontekst Ollamy: [run-settings.md](../protocol/run-settings.md) §5.
- Narzędzia zmieniają tylko opakowanie, `strict` zapisany w `run_start`: [prompts.md](../protocol/prompts.md) §8.
- Flaga błędu wyniku tylko tam, gdzie API ją ma: [prompts.md](../protocol/prompts.md) §9; rozumowanie odsyłane i
  zapisywane osobno: [prompts.md](../protocol/prompts.md) §2.
- Pola `model_turn`, `settings_sent`, `retries`, `raw_ref`: [run-event.v2.schema.json](../../schemas/run-event.v2.schema.json);
  `provider`, `finish_reason`, `usage`: [common.v2.schema.json](../../schemas/common.v2.schema.json).
- Klucz tylko ze zmiennej środowiskowej; `IChatClient` bez `UseFunctionInvocation`: [0001](../decisions/0001-stos-technologiczny.md).

## 8. Testy akceptacyjne

Na atrapie HTTP (`WireMock.Net`, `server.Url` jako `api.base_url`), z wstrzykniętym czekaniem (zapis czasów bez
usypiania) i rozrzutem 0; klucz `sk-test-SECRET-123` w zmiennej `TEST_KEY`. Bez sieci i bez płatnych API. Pozycje modeli
jak w `schemas/examples/experiment-config.pilot-sort.json`.

- **T1 Dwa wywołania Anthropic.** Dane: `claude-haiku-5-5`; `POST /v1/messages` daje 200, `stop_reason: "tool_use"`,
  bloki `tool_use`: `toolu_1` `compare` `{"i":0,"j":1}` i `toolu_2` `swap` `{"i":0,"j":1}`. Działanie:
  `GetResponseAsync`. Oczekiwane: dwa `FunctionCallContent` (`toolu_1`, `toolu_2`), `algotrace.arguments_raw`
  `{"i":0,"j":1}` w obu, `finish_reason` `tool_call`, `finish_reason_raw` `tool_use`, `attempts` 1.
- **T2 Ponowienia po 529.** Dane: Anthropic, `initial_backoff_s: 2`, `max_backoff_s: 120`; kolejno 529
  (`overloaded_error`), 529, 200. Oczekiwane: `attempts` 3, `retries` `[{529,"overloaded_error",2000},
  {529,"overloaded_error",4000}]` (`status`, `error_type`, `wait_ms`), zapisane czekania 2000 i 4000 ms, 3 żądania.
- **T3 Sześć razy 503.** Dane: Gemini, `max_api_retries: 5`, zawsze 503 `UNAVAILABLE`. Oczekiwane: `error_kind`
  `api_error`, `error_type` `UNAVAILABLE`, `attempts` 6, `retries` z 6 wpisami (ostatni `wait_ms` 0), `error_message`
  `6 attempts of the request for turn 1 failed with HTTP 503`, `FinishReason` `error`, 6 żądań.
- **T4 Limit dzienny.** Dane: Groq, odpowiedź 429 z `Retry-After: 900`. Oczekiwane: `error_kind` i `error_type`
  `daily_limit`, `attempts` 1, 1 żądanie, brak czekania.
- **T5 Kontekst.** Dane: Anthropic, 400 `invalid_request_error`, komunikat `prompt is too long: 250000 tokens >
  200000 maximum`. Oczekiwane: `error_kind` `context_exceeded`, `attempts` 1, 1 żądanie.
- **T6 `strict`.** Dane: narzędzia `compare` i `done`, `algotrace.strict_tools` `true`; raz OpenAI (`POST
  /v1/responses`), raz Gemini. Oczekiwane: ciało OpenAI ma `tools[0].strict` `true` i `parallel_tool_calls` `true`,
  `StrictToolsSent` `true`; ciało Gemini nie zawiera napisu `strict`, `StrictToolsSent` `false`; schemat parametrów w
  obu żądaniach równy wejściu co do znaku.
- **T7 Brak klucza w zapisach.** Dane: Anthropic, `RawLogPath` w katalogu tymczasowym, 200 z `usage`
  `{input_tokens:20, cache_read_input_tokens:1760, cache_creation_input_tokens:120, output_tokens:25}`. Oczekiwane:
  `SettingsSent` równe `{"max_tokens":2048,"tool_choice":{"type":"auto"}}`; ani `SettingsSent`, ani plik surowy nie
  zawierają `sk-test-SECRET-123` ani `x-api-key`; plik ma 1 linię z `n: 1`, `raw_ref` `<run_id>.raw.jsonl#1`;
  `input` 1900, `cached_input` 1760, `cache_write` 120, `output` 25, `reasoning` `null`.
- **T8 Ollama.** Dane: `qwen3:8b`, `settings.seed` 42, `Seed` kontekstu 4242, `num_ctx` 20480, `max_output_tokens`
  2048, `base_url` `<atrapa>/v1`; odpowiedź z `message.tool_calls[0].function` `{name:"compare",
  arguments:{"j":1,"i":0}}`, `prompt_eval_count` 1880, `eval_count` 25. Oczekiwane: żądanie `POST /api/chat` z
  `"stream":false`, `"think":false`, `options` `{"num_ctx":20480,"num_predict":2048,"seed":4242}` i bez `temperature`;
  `arguments_raw` `{"j":1,"i":0}`; `input` 1880, `output` 25.
- **T9 Odesłanie rozumowania i błędu (Anthropic).** Dane: `claude-sonnet-5-5`; odpowiedź 1: `thinking` z `signature`
  `sig-abc`, `redacted_thinking` z `data` `red-1`, `tool_use` `toolu_1`; zapytanie 2 z historią i
  `FunctionResultContent("toolu_1","Error: ...")` z `algotrace.is_error` `true`. Oczekiwane: żądanie 1 ma `thinking`
  `{"type":"adaptive"}` i `output_config` `{"effort":"low"}`; w żądaniu 2 wiadomość `assistant` ma bloki w kolejności
  `thinking` (`sig-abc`), `redacted_thinking` (`red-1`), `tool_use`, a następna `user` zaczyna się od `tool_result` z
  `is_error: true` i nie ma tekstu po nim.
- **T10 Gemini: podpis, identyfikator, tokeny.** Dane: `gemini-4-hydrogen`; 200 z częścią `{"functionCall":{"name":
  "compare","args":{"j":1,"i":0}},"thoughtSignature":"ts-1"}` (bez `id`), `finishReason` `STOP`, `usageMetadata`
  `{promptTokenCount:100, candidatesTokenCount:10, thoughtsTokenCount:30}`. Oczekiwane: `arguments_raw`
  `{"j":1,"i":0}`, niepusty wygenerowany `CallId`, `finish_reason` `tool_call`, `finish_reason_raw` `STOP`, `output` 40,
  `reasoning` 30; ciało żądania ma `thinkingLevel` `low`; zapytanie 2 odsyła część z `thoughtSignature` `ts-1` i
  jeden `Content` z `functionResponse` (`name` `compare`).
- **T11 Chat Completions: urwane argumenty.** Dane: Groq `openai/gpt-oss-120b`; 200, `finish_reason` `length`,
  `tool_calls[0].function.arguments` `"{\"i\":0,"`. Oczekiwane: `arguments_raw` `{"i":0,` bez zmian, `finish_reason`
  `length`, brak wyjątku; ciało żądania ma `reasoning_effort` `low`, `parallel_tool_calls` `true`,
  `max_completion_tokens` 8192.
- **T12 Timeout.** Dane: `request_timeout_s: 1`, atrapa odpowiada po 3 s, potem 200. Oczekiwane: `attempts` 2,
  `retries` `[{status:null, error_type:"timeout", wait_ms:2000}]`.

## 9. Wiedza techniczna i źródła

Różnice API dostawców zestawu A (format narzędzi, `strict`, rozumowanie i jego odsyłanie, powody zakończenia, tokeny i
cache, błędy, nagłówki limitów, Ollama) opisuje [provider-apis.md](../knowledge/provider-apis.md) z adresami
dokumentacji dostawców; nie powtarzamy ich tu. Dla kodu w C#:

- Pakiety i wersje: [0001](../decisions/0001-stos-technologiczny.md). `AllowMultipleToolCalls` nie musi być honorowane
  przez SDK; adapter Anthropic nie wysyła `disable_parallel_tool_use` wcale (protokół: pole niewysyłane), więc
  test sprawdza, że ciała żądania go nie mają.
- `ChatResponse` nie niesie nagłówków HTTP: `RecordingHandler` (`DelegatingHandler`) wpinamy w `HttpClient` przekazany
  SDK (OpenAI: `HttpClientPipelineTransport` w opcjach; Anthropic i Google: własny `HttpClient`). Czy każde SDK to
  przyjmuje i jak wyłączyć jego ponawianie, sprawdź przy pierwszym adapterze.
- Pętla ponawiania jest nasza, bo musi wypełnić `retries`; `Microsoft.Extensions.Http.Resilience` może dać potok
  `HttpClient`, ale wpisy prób i `Retry-After` zapisuje adapter.
- Pola dostawcy spoza wspólnego modelu: `ChatOptions.RawRepresentationFactory` (żądanie) i `RawRepresentation` (odpowiedź).
- Źródła: `https://learn.microsoft.com/en-us/dotnet/ai/microsoft-extensions-ai`, `https://github.com/dotnet/extensions`,
  `https://github.com/openai/openai-dotnet`, `https://github.com/anthropics/anthropic-sdk-csharp`,
  `https://github.com/googleapis/dotnet-genai`, `https://docs.ollama.com/api/openai-compatibility`.

## 10. Do ustalenia

- **Ollama: API i wywołania.** Decyzja [0001](../decisions/0001-stos-technologiczny.md) mówi o `/v1/chat/completions` i
  o tym, że adapter wykonuje pierwsze wywołanie, a resztę oznacza; protokół
  ([run-settings.md](../protocol/run-settings.md) §1-2, [prompts.md](../protocol/prompts.md) §2) wymaga `/api/chat` z
  `think: false` i `options`, a wszystkie wywołania tury wykonuje środowisko. Spec idzie za protokołem. Propozycja:
  poprawić 0001 nowym zapisem; do tego czasu adapter obcina końcówkę `/v1` z `api.base_url`.
- **Przykład konfiguracji Ollamy** (`experiment-config.pilot-sort.json`) ma `temperature` 0.8, `top_p` 0.9, `seed` 42
  i `/v1`, a protokół ich nie wysyła (poza `seed` = ziarno instancji). Propozycja: adapter wysyła każde pole
  niebędące `null`, konfiguracje serii mają tu `null`; przykład poprawia właściciel schematów.
- **Źródło `seed` Ollamy.** Schemat ma tylko stały `settings.seed`. Propozycja: `AdapterRunContext.Seed` go zastępuje,
  a `settings_sent` pokazuje wartość faktyczną.
- **`model_context_window_exceeded` (Anthropic)** jako odpowiedź 200. Propozycja: `finish_reason` `length`.
- **Gemini `MALFORMED_FUNCTION_CALL` i pokrewne.** Propozycja: `error` w `model_turn` (surowa wartość w
  `finish_reason_raw`), traktowane przez środowisko jak turę bez wywołania.
- **`output` Gemini** jako `candidatesTokenCount + thoughtsTokenCount`. Propozycja: tak, po potwierdzeniu na pierwszej
  prawdziwej odpowiedzi.
- **Schemat parametrów Gemini** przez `parametersJsonSchema`. Propozycja: tak; gdy `Google.GenAI` go nie ma, wysłać
  `parameters` bez `additionalProperties` i zapisać to w `settings_sent`.
- **Markery błędów kontekstu i środków** opierają się na komunikatach dostawców. Propozycja: jedna tabela w kodzie,
  uzupełniana po pilotażu; nieznany 400 to `api_error`.
- **`strict` dla Groq** ([prompts.md](../protocol/prompts.md) §8: "Do weryfikacji"). Propozycja: `strict_tools: false`
  w konfiguracji Groq, dopóki pilotaż nie potwierdzi obsługi.
- **Odsyłanie `reasoning` OpenAI** przy `store: false` (nazwa `include`, rola `id`). Propozycja: pierwszy test z
  prawdziwym kluczem w pilotażu; do tego czasu atrapy używają odpowiedzi bez rozumowania.
