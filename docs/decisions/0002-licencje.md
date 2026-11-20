# 0002 Licencje kodu, zbioru przebiegów i tekstu badania

- **Status:** przyjęta, 20.11.2026. Lider zaproponował ją przed pierwszym kodem i przed wkładem innych członków;
  zespół zgodził się na nią na pierwszym spotkaniu 20.11.2026 ([notatka](../meetings/2026-11-20-pierwsze-spotkanie.md)).
  Plik `LICENSE` (niezmieniony tekst Apache-2.0 z `https://www.apache.org/licenses/LICENSE-2.0.txt`) jest w katalogu
  głównym od 20.11.2026, obok `NOTICE` i sekcji „Licencja” w `README.md`.
- **Jak ją zmienić:** nowy plik `NNNN-krotki-opis.md`, który w statusie pisze „zastępuje 0002” i podaje powód. Zmiana
  licencji części, do której wnieśli wkład inni, wymaga zgody wszystkich autorów tego wkładu (art. 9 ustawy o prawie
  autorskim), a kopie już wydane zostają na starej licencji.

## Kontekst

Repozytorium ma trzy rodzaje treści o różnych potrzebach: kod (także kod środowiska bazowego, który trafi do
`src/environment/` po 23.12.2026), zbiór przebiegów modeli, który ma być publiczny i cytowany, oraz tekst badania,
z którego powstanie referat. Licencję wybiera się teraz, bo dziś wszystkie commity ma jeden autor; po wkładzie innych
każda zmiana wymaga zgody wszystkich.

- Prawa autorskie mają autorzy, przy utworze wspólnym wspólnie; koło może prezentować projekt, ale nie jest
  właścicielem praw.
- Zależności z 0001 są na licencjach permisywnych (MIT, BSD-3-Clause, Apache-2.0, PSF; MPL-2.0 ma tylko `hypothesis`
  w testach) i nie wchodzą do repozytorium: NuGet i PyPI pobierają je przy budowaniu.
- Odpowiedzi w przebiegach wygenerowały modele; czy są utworem, jest niepewne.
- Regulamin zarządzania prawami autorskimi UR (uchwała Senatu 108/10/2025) dotyczy utworów, które są przedmiotem
  komercjalizacji. Wynik powstały z pomocą uczelni, także w kole naukowym, ma prawa ustalone umową o tej pomocy,
  a twórca zgłasza dobro intelektualne do UCTT w 14 dni i zachowuje je w tajemnicy do decyzji Rektora. O licencjach
  otwartych regulamin nie mówi. Brzmienie tych przepisów trzeba jeszcze potwierdzić w tekście z BIP UR.

## Decyzja

1. **Kod: Apache License 2.0** (`Apache-2.0`) dla wszystkiego poza `data/` i `paper/`, także `docs/`, `schemas/`
   i `experiments/`: jeden plik `LICENSE` w katalogu głównym i `NOTICE` z nazwą projektu i linią praw autorów.
2. **Zbiór przebiegów: CC0 1.0** (`CC0-1.0`) dla całego `data/`, z prośbą o cytowanie przez DOI (`data/README.md`).
3. **Tekst badania: CC BY 4.0** (`CC-BY-4.0`) dla całego `paper/`, także `figures/` (`paper/README.md`).
4. **Wkład** jest na licencji części, której dotyczy (`README.md`, „Licencja”); kod obejmuje też § 5 Apache-2.0, więc
   projekt nie potrzebuje CLA ani DCO.
5. **Kod środowiska bazowego** wchodzi na tej samej licencji: autor przy imporcie udziela licencji Apache-2.0, a prawa
   zostają przy nim. Przeniesienie praw majątkowych wymagałoby umowy pisemnej (art. 53 ustawy), a bez wyraźnego
   przeniesienia jest licencja (art. 65).

Powody:

- Apache-2.0 jest permisywna jak MIT, a dodaje jawną licencję patentową współtwórców i `NOTICE`, co porządkuje wkład
  wielu członków koła; ten sam warunek mają SDK `Anthropic` i `Google.GenAI`.
- Creative Commons poleca CC0 dla danych naukowych. CC BY obiecywałaby prawa do wyjść modeli, których może nie być,
  a przy łączeniu wielu zbiorów mnoży atrybucje; cytowanie i tak zapewnia DOI.
- CC BY 4.0 to standard tekstów w otwartym dostępie.
- Jedna licencja dla kodu, schematów, konfiguracji i dokumentacji: schematy i konfiguracje czytają programy,
  a prompty z `docs/protocol/` trafiają do konfiguracji.

## Odrzucone

- **MIT dla kodu:** równie dobra i prostsza, ale bez jawnej licencji patentowej i `NOTICE`. Różnica w praktyce jest
  mała, więc to wybór na wypadek, gdy zespół woli najprostszy tekst (inny `LICENSE`, bez `NOTICE`).
- **GPL-3.0 dla kodu:** projektowi badawczemu nic nie daje, a utrudnia ponowne użycie analizatora w projektach
  na licencjach permisywnych.
- **CC BY 4.0 dla zbioru:** bezpieczna, gdyby opiekun koła albo uczelnia chcieli wymogu atrybucji, ale obiecuje prawa
  niepewne przy wyjściach modeli.
- **Tekst bez licencji otwartej:** zamyka ponowne użycie tekstu i rysunków; o prawach do referatu i tak zdecyduje
  miejsce publikacji.
- **`docs/` (albo `docs/` i `schemas/`) na CC BY 4.0:** dwie licencje w części, którą czytają programy.

## Skutki

- Pliki: `LICENSE` (niezmieniony tekst Apache-2.0), `NOTICE`, sekcje „Licencja” w `README.md`, `data/README.md`
  i `paper/README.md`. Bez nagłówków SPDX w plikach i bez plików z licencjami zależności.
- Kto rozpowszechnia kod, dołącza `LICENSE`, zachowuje noty, oznacza zmienione pliki i przenosi treść `NOTICE`
  (Apache-2.0 § 4).
- Binaria `JsonSchema.Net` są na umowie OSMF EULA (kod biblioteki jest na MIT), więc wydania (GitHub, Zenodo) zawierają tylko
  źródła i dane, bez skompilowanych programów.
- Przed upublicznieniem repozytorium albo pierwszym wydaniem: pytanie do opiekuna koła, czy koło dostaje pomoc uczelni
  w rozumieniu regulaminu UR, czy jest umowa o tej pomocy i czy wynik trzeba zgłosić do UCTT.
- Jeśli miejsce publikacji referatu wymaga przeniesienia praw albo innej licencji, poda to `paper/README.md`, a zmiana
  licencji tekstu dostanie nowy zapis.
- Warunki dostawców modeli i karta zbioru powstaną przy pierwszym wydaniu zbioru.
