# src/adapters

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/adapters.md](../../docs/specs/adapters.md).

Adaptery dostawców modeli za jednym wspólnym interfejsem: środowisko wysyła wiadomości i opis narzędzi, adapter
zwraca odpowiedź modelu i żądane wywołania narzędzi, niezależnie od API dostawcy.

Co tu trafi:

- adapter na każdego dostawcę (co najmniej 3) i co najmniej 1 dla modelu uruchamianego lokalnie;
- ten sam opis narzędzi i ten sam prompt dla wszystkich dostawców;
- zapis tokenów, wersji modelu, czasu i błędów API (do zapisu przebiegu);
- obsługa limitów zapytań: ponowienie z przerwą;
- klucze API tylko ze zmiennych środowiskowych.

Różnice między dostawcami, których adapter nie ukryje, opisujemy w `docs/`. Lista dostawców i modeli jest jeszcze
otwarta.

## Język i narzędzia

C# / .NET 10 (`net10.0`), biblioteka `AlgoTrace.Adapters`. Każdy adapter to `IChatClient` z `Microsoft.Extensions.AI`
**bez** `UseFunctionInvocation`: zwraca żądane wywołania, a wykonuje je środowisko. Główne biblioteki:

- oficjalne SDK `OpenAI`, `Anthropic` i `Google.GenAI`; Mistral i Ollama przez klienta `OpenAI` z własnym adresem
  bazowym;
- `Microsoft.Extensions.Http.Resilience`: własne ponawianie z przerwą (ponawianie w SDK wyłączone, żeby każda próba
  trafiła do zapisu); surowe HTTP zapisuje własny handler `HttpClient`.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy powstanie kod adapterów. Z katalogu głównego repozytorium:

```
dotnet build
dotnet test
```

Testy (`tests/dotnet/AlgoTrace.Adapters.Tests/`) używają fałszywego `IChatClient` i atrapy HTTP (`WireMock.Net`),
bez płatnych API. Klucze API tylko w zmiennych środowiskowych (np. `OPENAI_API_KEY`) albo w `dotnet user-secrets`;
konfiguracja eksperymentu podaje tylko nazwę zmiennej.

Model lokalny działa w Ollamie (aplikacja albo `ollama serve`), adres `http://localhost:11434/v1`:

```
ollama pull <tag modelu>
```

Domyślne okno 4096 tokenów nie da się zmienić przez `/v1`, więc przed startem serwera ustaw zmienną
`OLLAMA_CONTEXT_LENGTH` (co najmniej 20480) albo `num_ctx` w Modelfile.
