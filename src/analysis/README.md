# src/analysis

Specyfikacja (cel, interfejsy, zachowanie, testy akceptacyjne): [docs/specs/analysis.md](../../docs/specs/analysis.md).

Analiza wyników pełnego badania według planu z `docs/protocol/`: odpowiedzi na pięć pytań badawczych.

Co tu trafi:

- skuteczność według modelu, dostawcy i N z przedziałami ufności;
- rozkład rozpoznanych algorytmów i zgodność deklaracji z wykonaniem;
- efektywność wobec granic teoretycznych i wzorców;
- zmiana strategii z rozmiarem zadania i po błędzie narzędzia;
- skrypty, które generują tabele i wykresy do `paper/figures/` (wykresów nie rysuje się ręcznie).

Wejście: wiersze wyników i wyniki analizatora z `data/results/`.

## Język i narzędzia

Python 3.13, pakiet `algotrace_analysis` w workspace uv repozytorium. Główne biblioteki:

- `pandas` z `pyarrow`: wiersze wyników z CSV i duże analizy w Parquet;
- `statsmodels` i `scipy`: modele i testy statystyczne (metody wybiera plan analizy w `docs/protocol/`);
- `matplotlib`: wykresy do PDF albo PGF.

Decyzja, wersje i odrzucone opcje: [0001 Stos technologiczny modułów](../../docs/decisions/0001-stos-technologiczny.md).

## Budowanie i uruchamianie

Plan: polecenia zadziałają, gdy powstanie kod analizy. Z katalogu głównego repozytorium:

```
uv sync --locked --all-packages
uv run --locked python -m algotrace_analysis ...
uv run --locked pytest tests/python/analysis
```

Tabele i wykresy trafiają do `paper/figures/`.
