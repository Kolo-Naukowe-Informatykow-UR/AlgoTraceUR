# API dostawców: różnice, których adapter musi pilnować

Stan dokumentacji dostawców: **19.11.2026** (ten dzień sprawdzono; nazwy modeli i pól mogą się zmienić do
konfiguracji pilotażu w styczniu 2027, wtedy sprawdź ponownie). Plik zbiera fakty potrzebne do napisania adapterów
([adapters.md](../specs/adapters.md), sekcja 9); ustawienia modeli zestawu A i reguły ponawiania ustala protokół
([run-settings.md](../protocol/run-settings.md)), a gdy plik i protokół się różnią, wygrywa protokół. Punkty
oznaczone **Do sprawdzenia** nie były potwierdzone w dokumentacji; sprawdź je pierwszym prawdziwym wywołaniem
i popraw ten plik.

## 1. Adresy dokumentacji

- Anthropic: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools`, `.../parallel-tool-use`,
  `.../strict-tool-use`, `https://platform.claude.com/docs/en/build-with-claude/thinking`,
  `.../build-with-claude/prompt-caching`, `https://platform.claude.com/docs/en/api/errors`,
  `.../api/rate-limits`, `.../api/migration-2026-10-21`.
- OpenAI: `https://developers.openai.com/api/docs/guides/function-calling`, `.../guides/reasoning`,
  `.../guides/prompt-caching`, `.../guides/structured-outputs`, `.../guides/rate-limits`, `.../guides/error-codes`,
  `.../guides/migrate-to-responses`, `.../guides/latest-model`. Dopisek `.md` do adresu daje całą stronę.
- Gemini: `https://aistudio.google.com/docs/function-calling.md?generate-content=true` (oraz `thought-signatures`,
  `thinking`, `caching`, `api-errors`, `rate-limits` pod `aistudio.google.com/docs/`),
  `https://aistudio.google.com/api-reference/generate-content`. Strony domyślnie opisują nowe Interactions API;
  wariant `generateContent` (camelCase) otwiera dopisek `?generate-content=true`.
- Mistral: `https://docs.mistral.ai/capabilities/function_calling`, `https://docs.mistral.ai/api/endpoint/chat`,
  `https://docs.mistral.ai/openapi.yaml` (pełny schemat; strony opisowe pomijają np. `strict`),
  `https://docs.mistral.ai/capabilities/reasoning`.
- Ollama: `https://docs.ollama.com/api/openai-compatibility`, `https://docs.ollama.com/capabilities/tool-calling`,
  `https://docs.ollama.com/api/tags`; zgłoszenie o ignorowaniu `tool_choice`:
  `https://github.com/ollama/ollama/issues/17921`.

## 2. Format narzędzi i `strict`

| API | Opis narzędzia | `strict` |
|---|---|---|
| OpenAI Responses | płaski: `{"type":"function","name","description","parameters","strict"}` | tak; wymaga `additionalProperties: false` i wszystkich pól w `required` (schematy AlgoTrace to spełniają) |
| Chat Completions (Groq, Mistral) | zagnieżdżony: `{"type":"function","function":{"name","description","parameters","strict"}}` | Mistral ma pole w schemacie bez opisu semantyki; Groq: **Do sprawdzenia** |
| Anthropic Messages | `{"name","description","input_schema","strict"}` | tak (gramatyka); pierwsze żądanie z nowym schematem jest wolniejsze (kompilacja, cache do 24 h) |
| Gemini `generateContent` | `tools[].functionDeclarations[]` z `name`, `description` i `parameters` (podzbiór OpenAPI) albo `parametersJsonSchema` (JSON Schema); obu naraz nie wolno | brak; pole pominąć |
| Ollama `/api/chat` | `tools` jak w Chat Completions | brak; pole pominąć |

- Schematy narzędzi AlgoTrace nie mają `minimum` ani `maximum` ([prompts.md](../protocol/prompts.md) §8), bo Anthropic
  ich w trybie `strict` nie przyjmuje, a Gemini ich nie obsługuje. Zakres sprawdza środowisko.
- Gemini `parameters` pomija pola spoza podzbioru OpenAPI (m.in. `additionalProperties`), więc schemat nie dojdzie
  do modelu co do znaku; `parametersJsonSchema` niesie go w całości. **Do sprawdzenia**: czy `Google.GenAI` dla .NET
  udostępnia `parametersJsonSchema`.
- Anthropic: nazwa narzędzia musi pasować do `^[a-zA-Z0-9_-]{1,128}$`. Narzędzi serwerowych (web search itp.) nie
  podajemy.

## 3. Wywołania równoległe i `tool_choice`

Protokół dopuszcza kilka wywołań w turze i wysyła `tool_choice: auto` ([run-settings.md](../protocol/run-settings.md)
§1), więc adapter niczego nie wyłącza. Co jednak potrafią dostawcy:

- OpenAI i Chat Completions: `parallel_tool_calls` domyślnie `true`; protokół wysyła je jawnie (OpenAI, Groq).
- Anthropic: kilka bloków `tool_use` w jednej odpowiedzi jest domyślnie dozwolone; `disable_parallel_tool_use` nie
  wysyłamy. Na Opus 5.5, Sonnet 5.5, Fable i Mythos 5.1+ `tool_choice` `any` i `tool` dają HTTP 400, `auto` jest
  przyjmowane; model może zakończyć turę samym tekstem (`end_turn`).
- Gemini: nie ma przełącznika; kilka `functionCall` w jednej odpowiedzi jest możliwe. Tryby `AUTO`, `ANY`, `NONE`,
  `VALIDATED`; `auto` protokołu to `AUTO`.
- Ollama: `tool_choice` w trybie `/v1` jest ignorowany bez błędu; w `/api/chat` pola nie ma. Model może zapisać
  wywołanie tekstem w `content` (zgłoszone na wszystkich czterech popularnych serwerach lokalnych, zwykle przy
  modelach Qwen); szablon modelu decyduje o formacie, a błąd parsera daje pusty `content` i brak `tool_calls`
  przy `eval_count` > 0. Adapter tego nie naprawia: zwraca to, co przyszło (tura bez wywołania).

## 4. Wyniki narzędzi, identyfikatory i argumenty

| API | Wywołanie w odpowiedzi | Wynik w następnym żądaniu |
|---|---|---|
| OpenAI Responses | element `function_call` (`call_id`, `name`, `arguments` jako string JSON) | element `{"type":"function_call_output","call_id","output"}` |
| Chat Completions | `message.tool_calls[]` (`id`, `function.name`, `function.arguments` jako string) | wiadomość `{"role":"tool","tool_call_id","content"}` (Mistral dodaje `name`) |
| Anthropic | blok `tool_use` (`id`, `name`, `input` jako obiekt) | w jednej wiadomości `user` bloki `tool_result` (`tool_use_id`, `content`, `is_error`), po jednym na każde `tool_use` |
| Gemini | część `functionCall` (`id`?, `name`, `args` jako obiekt) | wszystkie `functionResponse` tury w jednym `Content` (`id`, `name`, `response` jako obiekt) |
| Ollama `/api/chat` | `message.tool_calls[].function` (`name`, `arguments` jako obiekt) | wiadomość `{"role":"tool","tool_name","content"}` |

- Anthropic: `tool_result` muszą stać na początku wiadomości `user`, bez wiadomości pomiędzy, a tekst dopisany po nich
  bywa przyczyną pustej odpowiedzi `end_turn`. Brak wyniku dla któregoś `tool_use` daje HTTP 400.
- Gemini: `id` wywołania jest opcjonalne w odpowiedzi (**Do sprawdzenia**, czy zawsze jest); `functionResponse`
  wymaga `name` zgodnego z wywołaniem (inaczej HTTP 400), flagi błędu nie ma, więc błąd idzie jako treść
  (`{"error": ...}`). Rola `Content` z wynikami: dokumentacja `generateContent` podaje `user`, README SDK Pythona
  `tool` (**Do sprawdzenia**).
- Ollama: gdy odpowiedź nie niesie identyfikatora wywołania, adapter nadaje własny (`call_<numer zapytania>_<indeks>`);
  **Do sprawdzenia** dla 0.40.x.
- Flaga błędu wyniku jest tylko u Anthropic (`is_error`); reszta dostaje sam tekst zaczynający się od `Error:`
  ([prompts.md](../protocol/prompts.md) §9).
- Argumenty obiektowe (Anthropic, Gemini, Ollama) zapisuje się z zachowaniem kolejności pól i bez przeformatowania;
  napis (OpenAI, Chat Completions) przekazuje się bez zmian, także gdy nie jest poprawnym JSON-em.

## 5. Rozumowanie i odsyłanie jego bloków

Poziom rozumowania zestawu A: [run-settings.md](../protocol/run-settings.md) §2. Pola zależą od dostawcy:

- Anthropic: `thinking: {"type":"adaptive"}` + `output_config: {"effort": ...}`; modele od 4.7 odrzucają
  `{"type":"enabled","budget_tokens":N}`. Haiku 5.5 bez `thinking` nie rozumuje; Sonnet 5.5 nie przyjmuje
  `{"type":"disabled"}` (jest `between_tools`). Domyślnie `display` bloków to `omitted`.
- OpenAI Responses: `reasoning: {"effort": "none"|"low"|...}`; część modeli odrzuca `none` (HTTP 400). Podsumowania
  tylko z `reasoning.summary`.
- Gemini: `generationConfig.thinkingConfig.thinkingLevel` (`minimal`, `low`, `medium`, `high`; zależnie od modelu)
  albo `thinkingBudget` (seria 2.5); oba naraz dają HTTP 400. Na Gemini 4 myślenia nie wyłączysz.
- Chat Completions: `reasoning_effort` (Groq dla `openai/gpt-oss-120b`, Mistral).
- Ollama: `think: false` w `/api/chat` wyłącza myślenie; `message.thinking` pojawia się tylko przy włączonym.

**Odsyłanie bez zmian** (historia jest tylko dopisywana; zmiana wcześniejszej wiadomości psuje prefiks i cache):

- Anthropic: wszystkie bloki `thinking` (z `signature`) i `redacted_thinking` z tury asystenta, w tej samej kolejności,
  przed `tool_use`. Filtr tylko po `type == "thinking"` gubi `redacted_thinking`. Zmiana `system`, `tools` albo
  wcześniejszych wiadomości przy blokach myślenia daje HTTP 400.
- OpenAI Responses: elementy `reasoning` razem z `function_call`; przy `store: false` trzeba poprosić o
  `include: ["reasoning.encrypted_content"]`, a element niesie wtedy `encrypted_content`. Historia po stronie klienta,
  `store: false`. **Do sprawdzenia**: nazwa `include` i czy `id` elementu jest wymagane przy odsyłaniu.
- Gemini 3 i 4: `thoughtSignature` na pierwszej części `functionCall` (przy wywołaniach równoległych tylko na
  pierwszej); brak podpisu w bieżącej turze to HTTP 400 (`MISSING_THOUGHT_SIGNATURE`). Odsyłać całe części modelu.
- Mistral: wiadomość asystenta z chunkami `thinking` w całości; `content` może być listą, nie napisem.
- W `Microsoft.Extensions.AI` te dane niesie `TextReasoningContent.ProtectedData` (podpis, `encrypted_content`,
  `thoughtSignature`); do `reasoning_text` w zapisie idzie tylko jawny tekst.

## 6. Powody zakończenia

| API | Pole i wartości |
|---|---|
| Anthropic | `stop_reason`: `end_turn`, `tool_use`, `max_tokens`, `stop_sequence`, `pause_turn`, `refusal`, `model_context_window_exceeded` |
| OpenAI Responses | `status` (`completed`, `incomplete`, `failed`) + `incomplete_details.reason` (`max_output_tokens`, `content_filter`); wywołania poznaje się po elementach `function_call` w `output`, osobnego powodu `tool_calls` nie ma |
| Chat Completions | `choices[].finish_reason`: `stop`, `length`, `tool_calls`, `content_filter`; Mistral dodatkowo `model_length`, `error` |
| Gemini | `candidates[].finishReason`: `STOP`, `MAX_TOKENS`, `SAFETY` i inne filtry, `MALFORMED_FUNCTION_CALL`, `UNEXPECTED_TOOL_CALL`, `TOO_MANY_TOOL_CALLS`, `MISSING_THOUGHT_SIGNATURE`, `MALFORMED_RESPONSE`; wywołania poznaje się po częściach `functionCall` (powód to nadal `STOP`) |
| Ollama | `done_reason`: `stop`, `length`, `load`; wywołania w `message.tool_calls` |

Mapowanie na wartości `finish_reason` schematu: [adapters.md](../specs/adapters.md) §4. Biblioteki tłumaczące na
Chat Completions (LiteLLM i podobne) zniekształcają te wartości (np. `pause_turn` na `length`,
`MALFORMED_FUNCTION_CALL` na `stop`), dlatego adaptery czytają odpowiedź dostawcy bezpośrednio. Ucięta odpowiedź
(`max_tokens`, `length`) może mieć niepełny blok narzędzia; nie naprawia się go.

## 7. Tokeny i pamięć podręczna

| API | wejście | z cache | zapis cache | wyjście | rozumowanie |
|---|---|---|---|---|---|
| Anthropic | `input_tokens` **bez** cache | `cache_read_input_tokens` | `cache_creation_input_tokens` | `output_tokens` | `output_tokens_details.thinking_tokens` (w wyjściu) |
| OpenAI Responses | `input_tokens` (z cache) | `input_tokens_details.cached_tokens` | `cache_write_tokens` (nowe, GPT-5.6+) | `output_tokens` | `output_tokens_details.reasoning_tokens` (w wyjściu) |
| Chat Completions | `prompt_tokens` | `prompt_tokens_details.cached_tokens` (gdy jest) | brak | `completion_tokens` | `completion_tokens_details.reasoning_tokens` (gdy jest) |
| Gemini | `promptTokenCount` (z cache) | `cachedContentTokenCount` | brak | `candidatesTokenCount` **bez** myśli | `thoughtsTokenCount` (osobno, rozliczane jak wyjście) |
| Ollama | `prompt_eval_count` | brak | brak | `eval_count` | brak |

- Anthropic: wejście razem to suma trzech pól; cache wymaga `cache_control` (AlgoTrace go nie wysyła, więc zapis i
  odczyt będą zwykle 0 albo `null`, chyba że `provider_options` konfiguracji coś doda). Minimum prefiksu to 512
  tokenów (modele 5.x); krótszy prompt nie daje błędu, tylko braku cache.
- OpenAI: cache automatyczny od 1024 tokenów, kroki po 128; `prompt_cache_key` poprawia trafienia.
- Gemini: cache niejawny od 2048 albo 4096 tokenów; na Gemini 4 poprzednie żądanie jest w pełni z cache tylko wtedy,
  gdy nowe dopisuje co najmniej 2050 tokenów, więc w pętli AlgoTrace zniżka bywa niewielka.
- Mistral: `prompt_cache_key`, bloki po 64 tokeny; `cached_tokens` jest na stronie o cache, a w `openapi.yaml` go
  nie ma, więc parser musi tolerować brak pola.
- Pole brakujące w odpowiedzi to `null`, nie 0 (`usage` w [common.v2.schema.json](../../schemas/common.v2.schema.json)).

## 8. Błędy, nagłówki i limity

| API | Typowe błędy | Nagłówki |
|---|---|---|
| Anthropic | 400 `invalid_request_error`, 401, 402 `billing_error`, 403, 404, 413 `request_too_large`, 429 `rate_limit_error`, 500 `api_error`, 504, 529 `overloaded_error` | `request-id`, `retry-after`, `anthropic-ratelimit-{requests,tokens,input-tokens,output-tokens}-{limit,remaining,reset}` |
| OpenAI | 400, 401, 403, 404, 409, 422, 429 (limit tempa albo brak kredytów), 500, 503 | `x-request-id`, `x-ratelimit-*`, `Retry-After` (minimum) |
| Gemini | 400 `INVALID_ARGUMENT`, 402, 403 `PERMISSION_DENIED`, 404, 429 `RESOURCE_EXHAUSTED`, 500 `INTERNAL`, 503 `UNAVAILABLE`, 504 `DEADLINE_EXCEEDED` | brak opisanych; limity RPM, TPM i RPD są na projekt, RPD zeruje się o północy czasu pacyficznego |
| Mistral | 400 (także przekroczenie okna), 429, 5xx | `X-RateLimit-Remaining`; `Retry-After` **Do sprawdzenia** |
| Ollama | błąd połączenia, 400, 404 (brak modelu), 5xx | brak |

- Anthropic 429 bez `retry-after` bywa limitem wydatków (ponawianie nie pomaga); brak kredytów bywa zgłaszany jako
  400 z komunikatem o saldzie (**Do sprawdzenia**). OpenAI 429 z kodem `insufficient_quota` to brak środków.
- Przekroczenie kontekstu to 400 z komunikatem (Anthropic "prompt is too long", OpenAI kod `context_length_exceeded`,
  Gemini `INVALID_ARGUMENT` o liczbie tokenów wejścia). Ollama tego błędu nie daje: po cichu ucina początek rozmowy,
  co środowisko wykrywa z `prompt_eval_count` ([run-settings.md](../protocol/run-settings.md) §5).
- Ponawianie w SDK jest domyślnie włączone: `openai` i `anthropic` 2 próby (połączenie, 408, 409, 429, >=500),
  `OpenAI` .NET 3 próby (**Do sprawdzenia**), `Google.GenAI` opcjonalne (`HttpRetryOptions`). Wyłącz wszystkie i
  ponawiaj we własnej pętli; listę kodów, czekanie i limity prób ustala protokół
  ([run-settings.md](../protocol/run-settings.md) §6), nie dostawca.
- Wersja modelu: OpenAI zwraca `model` (snapshot z datą, jeśli wysłano alias) i `service_tier`; Anthropic `model` (od
  generacji 4.6 identyfikator bez daty jest przypięty); Gemini `modelVersion`; Mistral i Groq odsyłają alias z żądania;
  w Ollamie `model` to nazwa, a skrót treści (`digest`) jest w `/api/tags`.

## 9. Próbkowanie

Protokół nie wysyła `temperature`, `top_p`, `top_k` do dostawców chmurowych ([run-settings.md](../protocol/run-settings.md)
§1): Anthropic odpowiada na nie HTTP 400 (od `anthropic-version: 2026-10-21` na każdym modelu), Gemini 4 i 3.6+ je
ignorują, OpenAI z rozumowaniem je odrzuca. Parametru `seed` nie ma w Anthropic ani w Responses. Wartość `null`
w `settings` konfiguracji znaczy "nie wysyłać" i adapter trzyma się tego bez wyjątków.

## 10. Ollama

- Używamy natywnego `POST /api/chat` z `"stream": false`, nie `/v1`: tylko tam działają `options.num_ctx` (w `/v1`
  okna nie ustawisz, domyślne bywa 4096) i `think`. Adres bazowy konfiguracji bywa podany z `/v1`; adapter go obcina.
- Żądanie: `model`, `messages`, `tools`, `stream`, `think`, `options` (`num_ctx`, `num_predict`, `seed`, opcjonalnie
  `temperature` itd. tylko gdy konfiguracja je podaje), `keep_alive` (model zostaje w pamięci domyślnie 5 minut).
- Odpowiedź: `message` (`content`, `thinking`, `tool_calls`), `done_reason`, `prompt_eval_count`, `eval_count`,
  czasy w nanosekundach.
- Wersja serwera: `GET /api/version`; skrót i kwantyzacja modelu: `/api/tags` (`digest`, `details.quantization_level`);
  opcje z pliku Modelfile: `POST /api/show`. Alias z `ollama cp` nie zmienia skrótu.
- Wynik narzędzia: wiadomość `role: "tool"` z `tool_name`. Argumenty wywołania są obiektem.
