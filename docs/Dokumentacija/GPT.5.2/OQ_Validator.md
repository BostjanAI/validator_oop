# OQ – Operational Qualification Protocol (Validator MES Receptur)

## Dokumentni podatki

- **Naziv**: OQ – Operational Qualification Protocol (Validator MES Receptur)
- **Sistem / aplikacija**: Validator (`validator_oop`)
- **ID dokumenta**: VAL-OQ-001
- **Verzija**: 1.0
- **Datum**: 2026-02-04
- **Pripravil**: ______________________
- **Izvedel**: ______________________
- **Pregledal (QA)**: ______________________
- **Odobril**: ______________________

## 1. Namen

Namen OQ je dokazati, da Validator deluje pravilno v predvidenem okolju uporabe in da ključne funkcije (nalaganje, validacija, poročanje, konfiguracijske možnosti) dosegajo pričakovane rezultate.

## 2. Obseg

Ta OQ pokriva:

- CLI validacijo in izhodne kode.
- Generiranje poročil (Excel, JSON, TXT).
- Bypass pravil in strict način.
- (Opcijsko) SOP validacijo z `.docx`.
- (Opcijsko) “apply fixes”.
- (Opcijsko) GUI zagon in osnovni potek.

## 3. Odgovornosti

- **Izvajalec OQ**: izvede teste, zbere dokazila (izpisi, datoteke).
- **QA**: pregleda rezultate, odobri odstopanja/deviations.
- **Lastnik procesa**: odobri zaključek OQ.

## 4. Predpogoji in testno okolje

### 4.1 Okolje

- **OS**: Windows 10/11
- **Python**: priporočeno 3.12 (ali ekvivalentno, skladno z distribucijo)
- **Odvisnosti**:
  - obvezno: `openpyxl`
  - opcijsko: `python-docx` (SOP validacija)
  - opcijsko: `tkinter` (GUI)

### 4.2 Testni podatki (vzorci)

Vključeni vzorci v repozitoriju:

- `samples\receptura_brez_napak.xlsx`
- `samples\receptura_z_napakami.xlsx`
- pričakovani JSON referenci:
  - `samples\receptura_brez_napak_report.json`
  - `samples\receptura_z_napakami_report.json`

### 4.3 Priporočilo za izhodne datoteke

Za OQ uporabljajte ločeno mapo za izhod (npr. `.\oq_output\`), da se izognete prepisovanju vzorcev.

## 5. Sledljivost URS → OQ (povzetek)

| URS | OQ testni primer(i) |
|---|---|
| URS-FR-01/03/04/06/14 | OQ-001, OQ-002 |
| URS-FR-07/08/09 | OQ-001, OQ-002, OQ-003 |
| URS-FR-10/11 | OQ-004, OQ-005 |
| URS-FR-12 | OQ-006 |
| URS-FR-13 | OQ-007 |
| URS-FR-05 | OQ-008 (opcijsko) |
| URS-NFR-07 | dokazila log/izpisi v vseh testih |

## 6. Testni primeri

> Opomba o zagonu:
> - Če ste v mapi `validator_oop\`, za CLI lahko uporabite `python main.py ...`
> - Če ste v mapi **nad** `validator_oop\`, lahko uporabite `python -m validator_oop ...`
>
> Spodaj je uporabljen pristop `python main.py` (znotraj `validator_oop\`).

### OQ-001 – CLI validacija: receptura brez napak (JSON)

- **Namen**: dokaz pravilnega branja in validacije; pričakovano *valid* brez napak.
- **Vhod**: `samples\receptura_brez_napak.xlsx`
- **Koraki**:
  1. Zaženite:
     - `python main.py "samples\receptura_brez_napak.xlsx" --format json`
  2. Zabeležite izpis v konzoli (kopija v dokazila).
- **Pričakovani rezultat**:
  - JSON vsebuje `"is_valid": true`
  - `"counts": {"error": 0, "warning": 0, "info": 0}`
  - proces se zaključi z **exit code 0**
- **Dokazila**:
  - priložen konzolni izpis (tekst ali posnetek zaslona).

### OQ-002 – CLI validacija: receptura z napakami (JSON) + preverba pričakovane vsebine

- **Namen**: dokaz detekcije napak in pravilnega označevanja lokacije/kod.
- **Vhod**: `samples\receptura_z_napakami.xlsx`
- **Koraki**:
  1. Zaženite:
     - `python main.py "samples\receptura_z_napakami.xlsx" --format json`
  2. Primerjajte povzetek s referenco `samples\receptura_z_napakami_report.json`.
- **Pričakovani rezultat** (na osnovi referenčnega JSON):
  - `"is_valid": false`
  - skupaj **4** napake (ERROR)
  - prisotne kode (vsaj po ena):
    - `TIP_OBJEKTA_UNKNOWN`
    - `CTRL_UNKNOWN`
    - `ZAKLENI_PAR1_FORMAT`
    - `STEP_DUPLICATE`
  - proces se zaključi z **exit code 1**
- **Dokazila**:
  - konzolni izpis,
  - (opcijsko) shranjen JSON izhod v datoteko.

### OQ-003 – Generiranje Excel poročila (`.xlsx`)

- **Namen**: dokaz generiranja poročila v Excelu z dvema listoma.
- **Vhod**: `samples\receptura_z_napakami.xlsx`
- **Koraki**:
  1. Ustvarite mapo `oq_output` (ročno ali v Explorerju).
  2. Zaženite:
     - `python main.py "samples\receptura_z_napakami.xlsx" --format excel --output "oq_output\OQ003_report.xlsx"`
  3. Odprite `oq_output\OQ003_report.xlsx`.
- **Pričakovani rezultat**:
  - datoteka se ustvari,
  - list `Povzetek` vsebuje stolpce: *List, Vrstica, Stolpec, Napaka, Opis napake*,
  - list `Število napak` vsebuje agregat po kodah,
  - poročilo vsebuje vsaj 4 zapise napak (skladno z OQ-002).
- **Dokazila**:
  - kopija generirane datoteke v evidence mapo OQ,
  - (opcijsko) posnetek zaslona odprtega poročila.

### OQ-004 – Bypass pravila (izključitev enega pravila)

- **Namen**: dokaz, da `--bypass` izključi pravilo po imenu.
- **Vhod**: `samples\receptura_z_napakami.xlsx`
- **Koraki**:
  1. Zaženite brez bypass (baseline):
     - `python main.py "samples\receptura_z_napakami.xlsx" --format json`
  2. Zaženite z bypass:
     - `python main.py "samples\receptura_z_napakami.xlsx" --format json --bypass step_numbering`
- **Pričakovani rezultat**:
  - baseline vsebuje kodo `STEP_DUPLICATE`,
  - v bypass zagonu se `STEP_DUPLICATE` ne pojavi,
  - ostale napake (npr. `CTRL_UNKNOWN`, `TIP_OBJEKTA_UNKNOWN`, `ZAKLENI_PAR1_FORMAT`) ostanejo.
- **Dokazila**:
  - oba JSON izpisa (ali shranjeni v datoteki).

### OQ-005 – Strict mode (WARNING → ERROR)

- **Namen**: dokaz, da strict način dvigne opozorila na nivo ERROR.
- **Opomba**: vzorčna datoteka z opozorilom (npr. `KEY_NUM_DUPLICATE_ONE`) morda ni priložena; če ni, pripravite kontrolno datoteko.
- **Vhod**: Excel receptura, ki generira vsaj eno WARNING v normalnem načinu.
- **Koraki**:
  1. Zaženite normalno:
     - `python main.py "<pot-do-datoteke.xlsx>" --format json`
  2. Zaženite strict:
     - `python main.py "<pot-do-datoteke.xlsx>" --format json --strict`
- **Pričakovani rezultat**:
  - v strict izhodu so prej WARNING postale `severity: "error"` in `counts.error` se poveča.
- **Dokazila**:
  - oba izpisa.

### OQ-006 – Vključitev formul (`--include-formulas`)

- **Namen**: dokaz, da sistem lahko naloži formule in jih uporabi pri validaciji, kjer je to relevantno.
- **Vhod**: Excel receptura z formulami v relevantnih poljih (npr. `INDEX/MATCH` v “masa”).
- **Koraki**:
  1. Zaženite:
     - `python main.py "<pot-do-datoteke.xlsx>" --format json --include-formulas`
- **Pričakovani rezultat**:
  - validacija se izvede brez runtime napake,
  - če pravila uporabljajo formule, se rezultati ujemajo s pričakovanji (dokumentirajte).
- **Dokazila**:
  - izpis/log.

### OQ-007 – Apply fixes (ustvarjanje kopije)

- **Namen**: dokaz, da “apply fixes” ustvari kopijo in ne spreminja originala.
- **Vhod**: poljubna receptura (npr. `samples\receptura_z_napakami.xlsx`)
- **Koraki**:
  1. Zaženite:
     - `python main.py "samples\receptura_z_napakami.xlsx" --format summary --apply-fixes`
  2. Preverite, ali se v mapi vzorca pojavi datoteka `*_AUTOFIX.xlsx` (ali uporabite `--output` mapo po internem dogovoru).
- **Pričakovani rezultat**:
  - ustvari se kopija z `_AUTOFIX.xlsx`,
  - izpis vključuje število uveljavljenih popravkov (`N` je lahko 0).
- **Dokazila**:
  - posnetek zaslona/izpis + kopija datoteke.

### OQ-008 – SOP validacija (opcijsko, če je SOP `.docx` na voljo)

- **Namen**: dokaz SOP skladnosti validacije, vključno z branjem zavihka `Podatki`.
- **Predpogoj**: nameščen `python-docx`, SOP dokument `.docx`.
- **Koraki (GUI priporočeno)**:
  1. Zaženite GUI (brez parametrov): `python main.py`
  2. Izberite recepturo in SOP dokument.
  3. Zaženite validacijo in zabeležite SOP povzetek v status oknu.
- **Pričakovani rezultat**:
  - SOP se naloži ali pa sistem jasno javi napako in nadaljuje brez SOP (če dokument ni berljiv),
  - v primeru neskladnosti se pojavijo kode `SOP_*` (npr. `SOP_IPO_MISMATCH`).
- **Dokazila**:
  - posnetek zaslona status okna,
  - (opcijsko) generirano poročilo z `SOP_*` napakami.

### OQ-009 – GUI zagon (osnovni smoke test)

- **Namen**: dokaz, da GUI aplikacija teče in omogoča osnovno izbiro datotek.
- **Koraki**:
  1. Zaženite `python main.py` brez parametrov.
  2. Preverite, da se odpre okno “Validator MES Receptur …”.
  3. Preverite gumbe “Izberi…”, “Shrani kot…”, “Zaženi validacijo”.
- **Pričakovani rezultat**:
  - GUI se odpre brez napake,
  - osnovne akcije delujejo (izbira datotek, začetek validacije).
- **Dokazila**:
  - posnetek zaslona okna.

## 7. Odstopanja (Deviations)

V primeru odstopanj zabeležite:

- ID testa
- opis odstopanja
- vpliv na URS
- korektivni ukrep (CAPA) / ponovitev testa

## 8. Zaključek OQ

- **Rezultat OQ**: PASS / PASS with deviations / FAIL
- **Opombe**: ___________________________________________

Podpisi:

- Izvedel: ______________________ Datum: ____________
- QA pregled: ____________________ Datum: ____________
- Odobril: _______________________ Datum: ____________

