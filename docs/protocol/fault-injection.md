# Warunek z błędami narzędzi

Status: **przed pilotażem** (2026-11-20). Pilotaż może zmienić przedziały pozycji błędu i długość błędu
trwałego; zmiana z datą i powodem w historii [README](README.md).

Decyzja protokołu ([README.md](README.md), sekcja „Zakres”) zastosowana w tym pliku: D02 A (osobny warunek z błędami na części przebiegów, seria główna bez
błędów, typy jednorazowy i trwały, harmonogram z ziarnem, 1-2 zadania i rozmiary). Służy pytaniu badawczemu 5 (zmiana
strategii po błędzie narzędzia); miary i testy w [analysis-plan.md](analysis-plan.md), liczba przebiegów
i kosztorys w [design.md](design.md).

## 1. Po co osobny warunek

Prace o niezawodności agentów traktują błąd narzędzia jako parametr (typ, intensywność, harmonogram z ziarnem)
i raportują wynik jako spadek względem przebiegów bez błędów (ReliabilityBench, arXiv 2601.06112; Bench2Robust,
arXiv 2608.11977); standardowego odsetka błędów nie ma. Błędy we wszystkich przebiegach mieszałyby się z pytaniami
1-4, więc seria główna (`condition: main`) nie ma żadnych błędów wstrzykniętych, a warunek z błędami ma własne
przebiegi.

## 2. Podwarunki i komórki

| Podwarunek (`condition: faults`, `fault_type`) | Błąd | Komórki zadanie x rozmiar |
|---|---|---|
| `faults:one_off` | jednorazowy: jedno wywołanie się nie udaje | sortowanie N = 10, Hanoi n = 4 |
| `faults:persistent` | trwały: narzędzie nie działa przez k = 3 kolejne poprawne wywołania | sortowanie N = 10, Hanoi n = 4 |

- **Dlaczego te komórki:** sortowanie, bo tylko tam klasyfikator rozróżnia kilka strategii, więc da się zmierzyć
  zmianę strategii po błędzie; N = 10 daje typowo 50-100 wywołań, czyli dość śladu przed błędem i po nim, przy koszcie
  dużo niższym niż N = 20. Hanoi n = 4 (optimum 15 ruchów), bo model śledzi tam stan sam (D08 A), więc błąd sprawdza,
  czy po nieudanym ruchu nie gubi stanu. Wyszukiwanie odpada: przy N = 63 przebieg przez połowienie przedziału ma
  około 6 odczytów, za mało na odcinki przed i po błędzie.
- **Instancje:** te same co w serii głównej dla tych komórek (ten sam plik instancji, te same `instance_id`
  i powtórzenia, [design.md](design.md)). Każdy przebieg z błędem ma więc parę: przebieg tego samego modelu na tej
  samej instancji bez błędu.
- **Jeden błąd na przebieg:** każdy przebieg ma dokładnie jedno zdarzenie błędu (jednorazowe albo trwałe). Drugie
  zdarzenie w tym samym przebiegu mieszałoby skutki obu, a pytanie 5 pyta o reakcję na błąd, nie o kumulację.
  Intensywność opisuje się więc jako „jedno zdarzenie na przebieg”, długość 1 albo 3 wywołania.
- **Ustawienia i limity:** jak w serii głównej ([run-settings.md](run-settings.md)), wariant tekstów `main`
  ([prompts.md](prompts.md)).

Zapis `faults:one_off` i `faults:persistent` w protokole to skrót: `condition: faults` z `fault_type: one_off` albo `persistent` (nazwy jak w kontrakcie danych, `schemas/`).

## 3. Harmonogram z ziarnem

- Liczy się tylko **poprawne wywołania inne niż `done`**: wywołania odrzucone przez walidację dostają swój błąd
  walidacji i nie przesuwają licznika. Błąd trafia w `c`-te poprawne wywołanie.
- Pozycja `c` jest losowana równomiernie z przedziału zależnego od rozmiaru, tak żeby przed błędem był odcinek śladu
  do klasyfikacji, a po nim większość pracy:
  - sortowanie: `c` z `[N, 3N]`, dla N = 10: 10-30;
  - Hanoi: `c` z `[2^(n-2), 2^(n-1)]`, dla n = 4: 4-8.
- Ziarno harmonogramu: `fault_seed = base_fault_seed + idx`, gdzie `idx` to numer instancji w pliku serii, a
  `base_fault_seed` jest w konfiguracji serii i różni się od ziarna bazowego instancji. Generator i jego zapis jak dla
  instancji ([design.md](design.md)): harmonogram losuje się raz przed serią i zapisuje przy instancji
  (`fault_type`, `fault_position` = `c`, `fault_length` = 1 albo 3), więc jest jednakowy dla wszystkich modeli na danej
  instancji i nie zależy od zachowania modelu.
- Jeśli przebieg kończy się przed `c`-tym poprawnym wywołaniem, błąd nie występuje (`fault_fired: false`); taki
  przebieg zostaje w danych i w porównaniu skuteczności, ale nie w miarach powrotu po błędzie
  ([analysis-plan.md](analysis-plan.md)).

## 4. Działanie błędu

- **Jednorazowy (`one_off`):** `c`-te poprawne wywołanie nie jest wykonane i dostaje komunikat błędu; następne
  wywołanie tego samego narzędzia działa normalnie.
- **Trwały (`persistent`):** `c`-te poprawne wywołanie i dwa następne poprawne wywołania **tego samego narzędzia**
  (razem k = 3) nie są wykonane i dostają ten sam komunikat; potem narzędzie działa normalnie. Inne narzędzia działają
  przez cały czas (np. przy nieudanym `compare` działa `swap`). W Hanoi jedynym narzędziem pracy jest `move`, więc
  zawodzą trzy kolejne poprawne ruchy.
- **Stan bez zmian:** wywołanie z błędem wstrzykniętym nie zmienia stanu, jak błąd walidacji.
- **Kilka wywołań w turze (D04 A):** błąd dotyczy tylko wywołań, w które trafia; pozostałe wywołania tej samej tury
  wykonują się normalnie, w kolejności (np. `swap` po nieudanym `compare` w tej samej odpowiedzi się wykona). Przy
  błędzie trwałym kolejne wywołania tego samego narzędzia w tej samej turze wliczają się do k.
- **`done` nigdy nie dostaje błędu wstrzykniętego.**
- **Limity:** wywołanie z błędem wstrzykniętym jest krokiem (liczy się do limitu kroków), ale nie liczy się do limitu
  błędów walidacji z rzędu i go nie zeruje ([run-settings.md](run-settings.md), sekcja 4); nie jest porównaniem, zamianą
  ani ruchem algorytmu.
- Kolejność sprawdzania: najpierw walidacja ([prompts.md](prompts.md), sekcja 9); dopiero poprawne wywołanie może
  dostać błąd wstrzyknięty.

## 5. Komunikat dla modelu

Oba typy dostają ten sam tekst, więc model nie wie z góry, czy błąd minie po jednym wywołaniu:

```text
Error: the tool is temporarily unavailable. The call was not executed.
```

- Flaga błędu jak przy błędzie walidacji (`is_error: true` u Anthropic, sam tekst u pozostałych), więc dla modelu
  wygląda jak zwykła awaria narzędzia (wzór odpowiedzi 503). Komunikat nie mówi „spróbuj ponownie”: to, czy model
  ponowi wywołanie, jest miarą.
- Tekst spełnia zasady neutralności z [prompts.md](prompts.md) (sekcja 11) i jest objęty tym samym sprawdzeniem.

## 6. Zapis: odróżnienie od błędów walidacji

Błąd wstrzyknięty nie jest błędem walidacji, więc w zapisie ma osobne pola (wymaganie dla kontraktu danych, lista
w [README](README.md)):

- `run_start`: `condition` (`main` albo `faults`) i harmonogram (`fault_seed`, `fault_type` `one_off` albo `persistent`,
  `fault_position`, `fault_length`).
- `tool_call` wywołania z błędem: `validation_error: null`, `executed: false`, `injected_fault: {type, event_index}`
  (`event_index` 1..k), wynik dokładnie taki, jaki dostał model.
- `run_end`: `fault_fired`, liczba wywołań z błędem wstrzykniętym osobno od liczników błędów walidacji.

Analiza błędów modelu (miara „Błędy” z research design) liczy tylko `validation_error`; błędy wstrzyknięte są
zmienną warunku, nie błędem modelu.

## 7. Miary do pytania 5

Liczone tylko dla przebiegów z `fault_fired: true`; „para” to przebieg tego samego modelu na tej samej instancji
w serii głównej. Testy i przedziały: [analysis-plan.md](analysis-plan.md).

| Miara | Definicja |
|---|---|
| spadek skuteczności | skuteczność w podwarunku minus skuteczność par z serii głównej (porównanie w parach) |
| powrót po błędzie (`recovered`) | po ostatnim wywołaniu z błędem model wykonał udane wywołanie tego samego narzędzia przed końcem przebiegu |
| opóźnienie powrotu | liczba wywołań i tur od pierwszego wywołania z błędem do pierwszego udanego wywołania tego samego narzędzia |
| dokładne ponowienie | pierwsze udane wywołanie tego narzędzia ma te same argumenty co wywołanie, które dostało błąd |
| porzucenie | po błędzie model wywołuje `done` albo kończy przebieg odpowiedzią bez wywołania, zanim ponowi narzędzie |
| zmiana strategii po błędzie | etykieta klasyfikatora odcinka przed błędem różni się od etykiety odcinka po błędzie (reguły odcinków: [classification-rules.md](classification-rules.md)); wywołania z błędem są poza oboma odcinkami |
| ciągłość wzorca | odległość odcinka po błędzie od kontynuacji wzorca rozpoznanego przed błędem, odtworzonej od stanu w chwili błędu |
| kontrola zmian bez błędu | te same dwie miary w przebiegu-parze, z podziałem w tym samym miejscu (po `c`-tym poprawnym wywołaniu); zmiana strategii przypisana błędowi to różnica między przebiegiem z błędem a parą |
| koszt błędu | dodatkowe wywołania i tokeny względem pary |
| Hanoi: utrata stanu | nielegalne ruchy w pierwszych 5 ruchach po błędzie oraz odległość do celu (liczba krążków poza palikiem 2) w chwili błędu i na końcu, wobec pary |
| wzmianka o błędzie | czy tekst modelu po błędzie wspomina awarię (kodowanie ręczne jak deklaracji, [analysis-plan.md](analysis-plan.md)) |

## 8. Co sprawdza pilotaż

- Czy komunikat jest rozumiany jako awaria narzędzia (a nie błąd argumentów) na 1-2 modelach; czy modele nie kończą
  przebiegu od razu po błędzie częściej niż w kilku procentach przebiegów (wtedy wynik i tak jest danymi, ale warto
  to wiedzieć przed kosztorysem).
- Czy przedziały pozycji `c` dają błąd w środku typowego przebiegu (odsetek `fault_fired: false` poniżej 10%); jeśli
  nie, przedziały zmienia się przed serią główną (historia w [README](README.md)).
