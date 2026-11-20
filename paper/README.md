# paper

Tekst badania w LaTeX: raport z wynikami, z którego powstanie też referat na konferencję.

## Pliki

| Plik | Co zawiera |
|---|---|
| `main.tex` | preambuła (pakiety, język, bibliografia), metadane i kolejność rozdziałów |
| `sections/` | rozdziały: streszczenia, wstęp, powiązane prace, metoda, protokół, wyniki, dyskusja, podsumowanie, dodatek |
| `references.bib` | bibliografia (biblatex) |
| `figures/` | rysunki i wykresy |
| `.latexmkrc` | ustawienia budowania |

## Budowanie

Potrzebna dystrybucja TeX (TeX Live albo MiKTeX) z `latexmk` i `biber`; w folderze `paper/`:

```
latexmk main.tex
```

Wynik: `build/main.pdf`. Szablon działa z pdfLaTeX (domyślnie) i LuaLaTeX (`$pdf_mode = 4;` w `.latexmkrc`). Użyte
pakiety są w każdej pełnej dystrybucji: `babel` (polski i angielski), `csquotes`, `biblatex`, `geometry`, `microtype`,
`amsmath`, `booktabs`, `tikz`, `listings`, `algorithm` i `algpseudocode`, `hyperref`.

> Stan (listopad 2026): szablon nie był jeszcze kompilowany, bo przy jego pisaniu nie było pod ręką TeX; pierwsza
> kompilacja może wymagać drobnych poprawek.

## Zasady

- Język główny ustawia jedna opcja w `main.tex` (`main=polish` albo `main=english`); streszczenia są w obu językach.
- Cytowania przez `\cite{klucz}` z `references.bib`; każda praca sprawdzona w źródle pierwotnym.
- Liczby i wykresy wyników pochodzą ze skryptów analizy, nie są przepisywane ręcznie.
- Miejsca do napisania: `\TODO{...}`.

## Licencja

Tekst badania z folderu `paper/`, także rysunki w `figures/`, jest na CC BY 4.0 (`CC-BY-4.0`, tekst prawny:
https://creativecommons.org/licenses/by/4.0/legalcode): wolno go kopiować, zmieniać i rozpowszechniać pod warunkiem
uznania autorstwa, podania linku do licencji i oznaczenia zmian.

Jeśli miejsce publikacji referatu wymaga przeniesienia praw albo innej licencji, ta sekcja poda, czego to dotyczy.
