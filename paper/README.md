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

Zespół buduje PDF tak samo lokalnie i w CI: TeX Live 2026 z `latexmk` i `biber` (oba w zestawie TeX Live, razem
z Perlem). Lokalnie w folderze `paper/`:

```
latexmk main.tex
```

Wynik: `build/main.pdf`. Szablon działa z pdfLaTeX (domyślnie) i LuaLaTeX (`$pdf_mode = 4;` w `.latexmkrc` albo
`latexmk -lualatex`); `latexmk -pvc` kompiluje po każdej zmianie, `latexmk -C` czyści `build/`. Użyte pakiety są
w każdej pełnej dystrybucji: `babel` (polski i angielski), `csquotes`, `biblatex`, `geometry`, `microtype`, `amsmath`,
`booktabs`, `tikz`, `listings`, `algorithm` i `algpseudocode`, `hyperref`.

- **TeX Live 2026 na Windows:** instalator sieciowy z https://tug.org/texlive/ (schemat pełny to kilka GB, mniejszy
  wystarczy, jeśli zawiera pakiety z listy); `biber --version` i `latexmk --version` sprawdzają instalację. MiKTeX
  też zadziała, ale wymaga osobnego Perla dla `latexmk`, a CI używa TeX Live. biblatex i biber muszą pochodzić z tej
  samej dystrybucji.
- **CI:** `.github/workflows/paper.yml` (`xu-cheng/latex-action@v4`, pełny TeX Live w kontenerze) buduje PDF przy
  każdej zmianie `paper/` w pushu i w PR; PDF jest w artefakcie `paper-pdf` przebiegu, przy błędzie razem z
  `main.log` i `main.blg`. Bez lokalnego TeX wystarczy PR i artefakt.
- **Edytor:** VS Code z rozszerzeniem LaTeX Workshop (receptura latexmk, skok źródło ↔ PDF) albo TeXstudio. Overleaf
  w planie darmowym nie ma synchronizacji z GitHubem, więc źródłem tekstu zostaje repozytorium.

> Stan (20.11.2026): pierwsza budowa w CI (push na `main` 20.11.2026) zakończyła się sukcesem, PDF jest
> w artefakcie `paper-pdf`; ostrzeżenia z `main.log` i `main.blg` czekają na przegląd, a lokalnie szablonu jeszcze
> nikt nie kompilował.

## Zasady

- Tekst jest po angielsku (`main=english` w `main.tex`, decyzja zespołu z 20.11.2026), streszczenie także po polsku.
  Struktura tekstu i wybrana konferencja: [docs/knowledge/paper-and-conferences.md](../docs/knowledge/paper-and-conferences.md),
  literatura do rozdziału 1: [docs/knowledge/literature.md](../docs/knowledge/literature.md).
- Cytowania przez `\cite{klucz}` z `references.bib`; każda praca sprawdzona w źródle pierwotnym.
- Liczby i wykresy wyników pochodzą ze skryptów analizy, nie są przepisywane ręcznie.
- Miejsca do napisania: `\TODO{...}`.

## Licencja

Tekst badania z folderu `paper/`, także rysunki w `figures/`, jest na CC BY 4.0 (`CC-BY-4.0`, tekst prawny:
https://creativecommons.org/licenses/by/4.0/legalcode): wolno go kopiować, zmieniać i rozpowszechniać pod warunkiem
uznania autorstwa, podania linku do licencji i oznaczenia zmian.

Jeśli miejsce publikacji referatu wymaga przeniesienia praw albo innej licencji, ta sekcja poda, czego to dotyczy.
