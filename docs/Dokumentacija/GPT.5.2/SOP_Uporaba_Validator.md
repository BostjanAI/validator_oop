# SOP – Uporaba Validatorja (Validator MES Receptur)

## Dokumentni podatki

- **Naziv**: SOP – Uporaba Validatorja (Validator MES Receptur)
- **ID dokumenta**: VAL-SOP-USE-001
- **Verzija**: 1.0
- **Datum**: 2026-02-04
- **Velja od**: ____________
- **Lastnik SOP**: ______________________
- **Odobril (QA)**: ______________________

## 1. Namen

Ta SOP opisuje standardni postopek uporabe Validatorja za preverjanje MES Excel receptur in pripravo poročil o napakah/opozorilih.

## 2. Področje uporabe

Velja za vse uporabnike, ki izvajajo predhodno kontrolo MES receptur (QA/Production/Process) v okolju Windows, z uporabo GUI ali CLI.

## 3. Odgovornosti

- **Uporabnik**: pravilna izbira vhodnih datotek, zagon validacije, pregled poročila, ukrepanje glede popravkov.
- **QA**: definira pričakovanja uporabe in pregleda rezultate, kadar je to zahtevano.
- **Skrbnik**: nudi podporo pri namestitvi, diagnostiki in posodobitvah.

## 4. Oprema in predpogoji

- Windows 10/11
- Validator (Python ali EXE distribucija)
- Odvisnosti (če uporabljate Python):
  - `openpyxl` (obvezno)
  - `python-docx` (opcijsko; za SOP `.docx`)
  - `tkinter` (opcijsko; za GUI)

## 5. Postopek – GUI (priporočeno za večino uporabnikov)

### 5.1 Zagon GUI

- Če imate Python okolje:
  - zaženite `python main.py` brez parametrov (znotraj mape `validator_oop`).

Če GUI ne deluje (npr. `tkinter` manjka), uporabite CLI (poglavje 6).

### 5.2 Izbira vhodnih datotek

1. Kliknite **Izberi…** in izberite eno ali več Excel receptur.
2. Preverite, da se poti prikažejo v polju za vhodne datoteke.
3. Po potrebi uporabite **Počisti seznam**.

### 5.3 Izbira izhodnega poročila

1. Izberite način poročila:
   - **Ena skupna datoteka**: eno poročilo za vse izbrane datoteke.
   - **Ločeno poročilo za vsako datoteko**: poročilo na datoteko v izbrani mapi.
2. Kliknite **Shrani kot…** (ali izberite mapo) in nastavite izhod:
   - `.xlsx` ali `.txt`

### 5.4 (Opcijsko) SOP dokument

1. Kliknite **Izberi SOP…** in izberite SOP Word dokument (`.docx`).
2. Če se SOP ne more naložiti, Validator izpiše opozorilo in nadaljuje validacijo brez SOP preverjanja.

### 5.5 Zagon validacije

1. Kliknite **Zaženi validacijo**.
2. Spremljajte status v spodnjem oknu (log).
3. Po zaključku:
   - Če je “OK: brez napak”, je receptura brez ERROR napak (opozorila so lahko prisotna).
   - Če je “Končano z napakami”, pregledajte poročilo in popravite recepturo.

### 5.6 Odprtje mape poročila

Kliknite **Odpri mapo poročila** za hiter dostop do izhodnih datotek.

## 6. Postopek – CLI (ukazna vrstica)

### 6.1 Osnovni zagon

V mapi `validator_oop`:

- Validacija in privzeto Excel poročilo:
  - `python main.py "pot\do\recepture.xlsx"`

### 6.2 Formati poročila

- Excel poročilo:
  - `python main.py "receptura.xlsx" --format excel --output "porocilo.xlsx"`
- JSON izpis v konzolo:
  - `python main.py "receptura.xlsx" --format json`
- TXT poročilo:
  - `python main.py "receptura.xlsx" --format text --output "porocilo.txt"`
- Kratek povzetek:
  - `python main.py "receptura.xlsx" --format summary`

### 6.3 Strict način in bypass

- Strict (WARNING → ERROR):
  - `python main.py "receptura.xlsx" --strict --format json`
- Bypass pravila (po imenu ali kodi):
  - `python main.py "receptura.xlsx" --bypass step_numbering required_columns --format json`

### 6.4 Formule

- Vključitev formul:
  - `python main.py "receptura.xlsx" --include-formulas --format json`

### 6.5 Apply fixes (kopija)

- Uveljavitev popravkov v kopijo:
  - `python main.py "receptura.xlsx" --apply-fixes --format summary`

> Opomba: število popravkov je lahko 0, odvisno od tega, ali so pravila generirala “proposed fixes”.

### 6.6 Izhodne kode (exit codes)

- `0`: brez ERROR napak
- `1`: najdene validacijske napake (ERROR)
- `2`: runtime napaka (npr. datoteka ni berljiva, manjkajo odvisnosti)

## 7. Interpretacija poročila

### 7.1 Excel poročilo

- **List `Povzetek`**:
  - vsebuje lokacijo (List/Vrstica/Stolpec) + kodo napake + opis.
- **List `Število napak`**:
  - agregat po kodah napak (uporabno za prioritizacijo).

### 7.2 Najpogostejši scenariji ukrepanja

- **Manjkajo obvezni stolpci** (`MISSING_COLUMN`): popravite headerje/stolpce v listu recepture.
- **Koraki** (`STEP_*`): odstranite duplikate, zapolnite manjkajoče korake, zagotovite začetek z 1.
- **Kontrole** (`CTRL_*`, `ZAKLENI_*`): preverite pravilnost imen kontrol in parametrov ter kontekst (tip podatka/objekta).
- **SOP napake** (`SOP_*`): uskladite `Podatki` in/ali recepturo s SOP zahtevami ali preverite, ali je izbran pravilen SOP dokument.

## 8. Diagnostika in reševanje težav

### 8.1 Log datoteka

Validator ustvarja log datoteko:

- `MESValidator.log` v uporabnikovem HOME profilu (npr. `C:\Users\<uporabnik>\MESValidator.log`)

Uporabite jo za diagnostiko (posebej pri EXE).

### 8.2 Pogoste napake

- **`openpyxl is required`**: manjkajoča Python knjižnica za Excel (namestitev v okolju).
- **`python-docx is required`**: manjkajoča knjižnica za SOP `.docx` (če uporabljate SOP validacijo).
- **GUI se ne zažene**: `tkinter` ni nameščen → uporabite CLI ali namestite okolje z `tkinter`.
- **Neberljiva Excel datoteka / poškodovan dokument**: preverite, ali se datoteka odpira v Excelu in ni zaklenjena/poškodovana.

## 9. Kontrola sprememb in periodični pregled

- Spremembe validatorja (pravila, izhodi, logika) morajo biti dokumentirane (change record) in ocenjene glede vpliva na proces.
- Po pomembnih spremembah se izvede vsaj ponovna izvedba OQ relevantnih testov (re-test).

## 10. Priloge

- OQ protokol: `VAL-OQ-001`
- URS/FS: `VAL-URS-001`, `VAL-FS-001`

