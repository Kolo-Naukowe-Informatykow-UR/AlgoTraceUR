# latexmk w folderze paper/: `latexmk main.tex` buduje build/main.pdf (biber uruchamia się sam).
$pdf_mode = 1;        # 1 = pdfLaTeX; 4 = LuaLaTeX
$out_dir = 'build';
@default_files = ('main.tex');
