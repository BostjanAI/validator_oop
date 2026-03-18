# Protokol operacijske kvalifikacije (OQ)
## Validator MES receptur

---

## Nadzor nad dokumentom

| Polje | Vrednost |
|---|---|
| **Naslov dokumenta** | Protokol operacijske kvalifikacije (OQ) |
| **Sistem / Aplikacija** | Validator MES receptur (validator_oop) |
| **ID dokumenta** | VAL-OQ-001 |
| **Verzija** | 1.0 |
| **Datum** | 2026-02-04 |
| **Pripravil** | ______________________ |
| **Izvedel** | ______________________ |
| **Pregledal (QA)** | ______________________ |
| **Odobril** | ______________________ |

---

## 1. Namen

Namen te operacijske kvalifikacije je zagotoviti dokumentirane dokaze, da sistem Validator deluje pravilno v svojem predvidenem operativnem okolju in da kritične funkcije (nalaganje, validacija, poročanje, konfiguracijske možnosti) proizvajajo pričakovane rezultate.

## 2. Obseg

Ta OQ protokol pokriva naslednja funkcionalna področja:

- Izvajanje CLI validacije in preverjanje izhodnih kod
- Generiranje poročil v več formatih (Excel, JSON, besedilo)
- Funkcionalnost bypass pravil in strogega načina
- Validacija skladnosti s SOP z Word dokumenti (opcijsko)
- Funkcionalnost apply fixes (opcijsko)
- Zagon GUI aplikacije in osnovno delovanje (opcijsko)

## 3. Odgovornosti

| Vloga | Odgovornost |
|---|---|
| **Izvajalec OQ** | Izvajanje testnih primerov, zbiranje dokazil (izpisi konzole, generirane datoteke), dokumentiranje rezultatov |
| **QA pregledovalec** | Pregled testnih rezultatov, ocena odstopanj, odobritev/zavrnitev rezultata OQ |
| **Lastnik procesa** | Odobritev zaključka OQ in sproščanje sistema za operativno uporabo |

## 4. Predpogoji in testno okolje

### 4.1 Specifikacija testnega okolja

**Operacijski sistem:**
- Windows 10 ali Windows 11

**Programsko okolje:**
- Python 3.12 (ali enakovredna verzija, kot je določeno v dokumentaciji uporabe)

**Zahtevane odvisnosti:**
- `openpyxl` (obvezno za Excel operacije)

**Opcijske odvisnosti:**
- `python-docx` (zahtevano samo za teste validacije SOP)
- `tkinter` (zahtevano samo za GUI teste; običajno vključeno v standardnih Python distribucijah)

### 4.2 Testni podatki

**Lokacija testnih podatkov:** `validator_oop/samples/`

**Primarne testne datoteke:**
- `receptura_brez_napak.xlsx` (veljavna receptura brez napak)
- `receptura_z_napakami.xlsx` (receptura z znanimi napakami)

**Referenčni izhodi:**
- `receptura_brez_napak_report.json` (pričakovan izhod za veljavno recepturo)
- `receptura_z_napakami_report.json` (pričakovan izhod za neveljavno recepturo)

### 4.3 Izhodni direktorij testov

**Priporočilo:** Ustvarite namenski izhodni direktorij `oq_output\` za preprečitev prepisovanja vzorčnih referenčnih datotek.

**Opomba o izvajanju:**
- Če je delovni direktorij `validator_oop\`, uporabite: `python main.py ...`
- Če je delovni direktorij nadrejen `validator_oop\`, uporabite: `python -m validator_oop ...`

Vsi testni primeri spodaj predpostavljajo izvajanje iz direktorija `validator_oop\`.

## 5. Matrika sledljivosti URS → OQ

| Zahteva URS | Testni primer(i) OQ |
|---|---|
| URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-14 | OQ-001, OQ-002 |
| URS-FR-07, URS-FR-08, URS-FR-09 | OQ-001, OQ-002, OQ-003 |
| URS-FR-10, URS-FR-11 | OQ-004, OQ-005 |
| URS-FR-12 | OQ-006 |
| URS-FR-13 | OQ-007 |
| URS-FR-05 | OQ-008 |
| URS-FR-02 | OQ-009 |
| URS-NFR-07 | Dokazila iz vseh testnih primerov (log datoteke, izpisi konzole) |

## 6. Testni primeri

### Testni primer OQ-001: CLI validacija – veljavna receptura (JSON format)

**Cilj:** Preveriti pravilno nalaganje datoteke in validacijo za recepturo brez napak.

**Sledljivost URS:** URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-08, URS-FR-14

**Vhodna datoteka:** `samples\receptura_brez_napak.xlsx`

**Testni koraki:**

1. Izvedite ukaz:
   ```
   python main.py "samples\receptura_brez_napak.xlsx" --format json
   ```
2. Zajemite celoten izpis konzole
3. Zabeležite izhodno kodo

**Pričakovani rezultati:**

- JSON izhod vsebuje: `"is_valid": true`
- Števila napak: `"counts": {"error": 0, "warning": 0, "info": 0}`
- Izhodna koda: `0`

**Zahteve za dokazila:**
- Izpis konzole (besedilna datoteka ali posnetek zaslona)
- Zabeležena izhodna koda

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-002: CLI validacija – neveljavna receptura (JSON format)

**Cilj:** Preveriti odkrivanje napak in pravilno poročanje kod napak/lokacij.

**Sledljivost URS:** URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-08, URS-FR-14

**Vhodna datoteka:** `samples\receptura_z_napakami.xlsx`

**Testni koraki:**

1. Izvedite ukaz:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json
   ```
2. Zajemite celoten izpis konzole
3. Zabeležite izhodno kodo
4. Primerjajte izhodno strukturo z referenčno datoteko `samples\receptura_z_napakami_report.json`

**Pričakovani rezultati (na podlagi referenčne datoteke):**

- JSON izhod vsebuje: `"is_valid": false`
- Skupno število napak: Minimalno 4 napake z `severity: "error"`
- Prisotne zahtevane kode napak (minimalno ena pojavitev vsake):
  - `TIP_OBJEKTA_UNKNOWN`
  - `CTRL_UNKNOWN`
  - `ZAKLENI_PAR1_FORMAT`
  - `STEP_DUPLICATE`
- Izhodna koda: `1`

**Zahteve za dokazila:**
- Izpis konzole
- Preverjanje izhodne kode
- (Opcijsko) JSON izhod shranjen v datoteko za podrobno primerjavo

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-003: Generiranje Excel poročila

**Cilj:** Preveriti generiranje Excel poročila z zahtevanimi delovnimi listi in strukturo.

**Sledljivost URS:** URS-FR-07, URS-FR-09

**Vhodna datoteka:** `samples\receptura_z_napakami.xlsx`

**Testni koraki:**

1. Ustvarite izhodni direktorij: `oq_output\`
2. Izvedite ukaz:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format excel --output "oq_output\OQ003_report.xlsx"
   ```
3. Odprite generirano datoteko `oq_output\OQ003_report.xlsx` v Microsoft Excel
4. Preverite strukturo in vsebino delovnega lista

**Pričakovani rezultati:**

- Datoteka `oq_output\OQ003_report.xlsx` je ustvarjena
- Delovni list "Povzetek" vsebuje stolpce: List, Vrstica, Stolpec, Napaka, Opis napake
- Delovni list "Število napak" vsebuje stolpce: Koda, Opis, Število
- Delovni list "Povzetek" vsebuje minimalno 4 zapise napak (skladno z OQ-002)
- Avtomatski filter je omogočen na obeh delovnih listih

**Zahteve za dokazila:**
- Kopija generirane Excel datoteke
- (Opcijsko) Posnetek zaslona odprtega poročila, ki prikazuje strukturo delovnega lista

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-004: Funkcionalnost bypass pravil

**Cilj:** Preveriti, da parameter `--bypass` izključi določena pravila iz izvajanja.

**Sledljivost URS:** URS-FR-11

**Vhodna datoteka:** `samples\receptura_z_napakami.xlsx`

**Testni koraki:**

1. Izvedite osnovno validacijo (brez bypass):
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json > oq_output\OQ004_baseline.json
   ```
2. Izvedite validacijo z bypass pravila:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json --bypass step_numbering > oq_output\OQ004_bypass.json
   ```
3. Primerjajte kode napak v obeh izhodih

**Pričakovani rezultati:**

- Osnovni izhod vsebuje kodo napake `STEP_DUPLICATE`
- Bypass izhod NE vsebuje kode napake `STEP_DUPLICATE`
- Druge kode napak ostanejo prisotne v bypass izhodu: `CTRL_UNKNOWN`, `TIP_OBJEKTA_UNKNOWN`, `ZAKLENI_PAR1_FORMAT`
- Izhodna koda za obe izvajanja: `1`

**Zahteve za dokazila:**
- Oba JSON izhoda shranjena v datoteke
- Povzetek primerjave, ki dokumentira prisotnost/odsotnost `STEP_DUPLICATE`

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-005: Strogi način (pretvorba WARNING v ERROR)

**Cilj:** Preveriti, da strogi način pretvori ugotovitve na ravni WARNING v raven ERROR.

**Sledljivost URS:** URS-FR-10

**Predpogoj:** Identificirajte ali pripravite Excel datoteko, ki generira vsaj eno WARNING (npr. koda napake `KEY_NUM_DUPLICATE_ONE` ali `CTRL_EXPECTED_MISSING`). Če vzorčni podatki ne vsebujejo opozoril, se ta testni primer izvede med rutinsko uporabo z ustreznimi testnimi podatki.

**Vhodna datoteka:** `<file_with_warnings.xlsx>` (določi izvajalec)

**Testni koraki:**

1. Izvedite normalno validacijo:
   ```
   python main.py "<file_with_warnings.xlsx>" --format json > oq_output\OQ005_normal.json
   ```
2. Izvedite strogo validacijo:
   ```
   python main.py "<file_with_warnings.xlsx>" --format json --strict > oq_output\OQ005_strict.json
   ```
3. Primerjajte polja `severity` in `counts` v obeh izhodih

**Pričakovani rezultati:**

- Izhod normalnega načina vsebuje ugotovitve z `"severity": "warning"`
- Izhod strogega načina pretvori iste ugotovitve v `"severity": "error"`
- `counts.error` se poveča v izhodu strogega načina
- `counts.warning` se zmanjša na 0 v izhodu strogega načina

**Zahteve za dokazila:**
- Oba JSON izhoda
- Primerjalna tabela, ki prikazuje pretvorbo resnosti

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH  ☐ ODLOŽENO (čakanje na testne podatke)

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-006: Nalaganje in validacija formul

**Cilj:** Preveriti, da sistem lahko naloži formule celic in jih uporabi pri validaciji, kjer je to uporabno.

**Sledljivost URS:** URS-FR-12

**Vhodna datoteka:** Excel receptura, ki vsebuje formule v relevantnih poljih (npr. formule `INDEX/MATCH` v celicah "masa"). Vzorčne datoteke v direktoriju `samples\` vsebujejo reference formul.

**Testni koraki:**

1. Izvedite validacijo z nalaganjem formul:
   ```
   python main.py "<recipe_with_formulas.xlsx>" --format json --include-formulas
   ```
2. Preverite, da se izvajanje zaključi brez napak pri izvajanju
3. Preglejte log datoteko za sporočila o parsiranju formul

**Pričakovani rezultati:**

- Validacija se zaključi uspešno (brez izjem pri izvajanju)
- Izhodna koda: `0` ali `1` (odvisno od rezultata validacije)
- Log datoteka vsebuje sporočila o nalaganju formul (če se uporablja `--verbose`)
- Pravila, odvisna od formul (npr. `TehtnicaVrednostFromFormulaRule`), se izvajajo pravilno

**Zahteve za dokazila:**
- Izpis konzole ali izvleček log datoteke
- Dokumentacija rezultatov validacije, odvisnih od formul

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-007: Apply fixes (ustvarjanje kopije delovnega zvezka)

**Cilj:** Preveriti, da "apply fixes" ustvari popravljeno kopijo brez spreminjanja izvorne datoteke.

**Sledljivost URS:** URS-FR-13, URS-NFR-06

**Vhodna datoteka:** `samples\receptura_z_napakami.xlsx`

**Testni koraki:**

1. Zabeležite MD5 hash ali časovni žig datoteke vhodne datoteke (osnovna vrednost)
2. Izvedite validacijo z apply fixes:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format summary --apply-fixes
   ```
3. Preverite ustvarjanje izhodne datoteke
4. Preverite, da izvorna datoteka ni spremenjena (primerjajte MD5 hash ali časovni žig)

**Pričakovani rezultati:**

- Izhodna datoteka ustvarjena s konvencijo poimenovanja `receptura_z_napakami_AUTOFIX.xlsx`
- Izpis konzole poroča o številu apliciranih popravkov (lahko je 0, če niso predlagani popravki)
- Izvorna datoteka `receptura_z_napakami.xlsx` ostane nespremenjena
- Izhodna koda: `0` ali `1` (na podlagi rezultata validacije)

**Zahteve za dokazila:**
- Izpis konzole, ki prikazuje število popravkov
- Posnetek zaslona ali seznam datotek, ki prikazuje izvirno in `_AUTOFIX.xlsx` datoteke
- Preverjanje, da je časovni žig/hash izvorne datoteke nespremenjen

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-008: Validacija skladnosti s SOP (opcijsko)

**Cilj:** Preveriti validacijo skladnosti s SOP, vključno s parsiranjem delovnega lista "Podatki".

**Sledljivost URS:** URS-FR-05

**Predpogoji:**
- Nameščena knjižnica `python-docx`
- Na voljo SOP Word dokument (`.docx`)

**Testni način:** Priporočen GUI

**Testni koraki:**

1. Zaženite GUI:
   ```
   python main.py
   ```
2. Izberite vhodno datoteko recepture preko gumba "Izberi…"
3. Izberite SOP dokument preko gumba "Izberi SOP…"
4. Kliknite "Zaženi validacijo"
5. Preglejte statusno okno za sporočila o nalaganju in validaciji SOP

**Pričakovani rezultati:**

**Če se SOP naloži uspešno:**
- Statusno okno prikaže: "SOP dokument uspešno naložen"
- Statusno okno prikaže: Število IPO kod, zahteve naložene iz SOP
- Če je odkrita neskladnost: V poročilu se pojavijo kode napak, ki se začnejo s `SOP_` (npr. `SOP_IPO_MISMATCH`)

**Če nalaganje SOP ne uspe:**
- Statusno okno prikaže jasno opozorilno sporočilo
- Validacija se nadaljuje brez preverjanj skladnosti s SOP
- V izhodu ni `SOP_*` kod napak

**Zahteve za dokazila:**
- Posnetek zaslona statusnega okna, ki prikazuje sporočila o nalaganju SOP
- Generirano validacijsko poročilo (če so prisotne SOP napake)
- Izvleček konzolnega loga

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH  ☐ NI IZVEDEN (SOP ni na voljo)

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

### Testni primer OQ-009: Zagon GUI aplikacije (smoke test)

**Cilj:** Preveriti, da se GUI aplikacija zažene in da so osnovne kontrole funkcionalne.

**Sledljivost URS:** URS-FR-02, URS-NFR-01

**Testni koraki:**

1. Zaženite GUI brez parametrov:
   ```
   python main.py
   ```
2. Preverite, da se okno odpre z naslovom "Validator MES Receptur ..."
3. Preverite prisotnost UI kontrol:
   - Gumb "Izberi…" (izbira vhodne datoteke)
   - Gumb "Shrani kot…" (izbira izhodne datoteke)
   - Gumb "Zaženi validacijo" (izvedi validacijo)
   - Statusno besedilno območje
4. Testirajte osnovno interakcijo:
   - Klik "Izberi…" → odpre se dialog za datoteke
   - Klik "Shrani kot…" → odpre se dialog za shranjevanje datotek

**Pričakovani rezultati:**

- GUI okno se odpre brez izjem
- Vse določene UI kontrole so vidne in odzivne
- Dialogi za izbiro datotek delujejo pravilno
- Aplikacijo je mogoče zapreti brez napak

**Zahteve za dokazila:**
- Posnetek zaslona GUI okna, ki prikazuje vse kontrole
- Dokumentacija uspešnih interakcij dialoga

**Rezultat testa:** ☐ USPEH  ☐ NEUSPEH  ☐ NI IZVEDEN (tkinter ni na voljo)

**Izvedel:** ______________________ **Datum:** ____________

**Odstopanja:** _________________________________________________________________

---

## 7. Upravljanje odstopanj

Za vsako odstopanje testnega primera dokumentirajte naslednje:

| Polje | Opis |
|---|---|
| **ID testnega primera** | OQ-XXX |
| **Opis odstopanja** | Podroben opis opazovanega v primerjavi s pričakovanim vedenjem |
| **Ocena vpliva** | Vpliv na zahteve URS (kritičen / večji / manjši) |
| **Osnovni vzrok** | Analiza vzroka odstopanja |
| **Korektivni ukrep** | Referenca CAPA ali opis korektivnega ukrepa |
| **Potreben ponovni test** | Da / Ne |

Uporabite priložen obrazec za dnevnik odstopanj (če je na voljo) ali dokumentirajte v tem razdelku.

---

## 8. Povzetek in sklep OQ

### 8.1 Povzetek izvajanja testov

| Metrika | Vrednost |
|---|---|
| Skupaj testnih primerov | 9 |
| Izvedeni testni primeri | _____ |
| Uspešni testni primeri | _____ |
| Neuspešni testni primeri | _____ |
| Neizveden testni primeri | _____ |
| Identificirana odstopanja | _____ |
| Kritična odstopanja | _____ |

### 8.2 Rezultat OQ

**Splošni rezultat:** ☐ USPEH  ☐ USPEH Z ODSTOPANJI  ☐ NEUSPEH

**Utemeljitev:**

_____________________________________________________________________________

_____________________________________________________________________________

**Dodatni komentarji:**

_____________________________________________________________________________

_____________________________________________________________________________

---

## Podpisi za odobritev

| Vloga | Ime | Podpis | Datum |
|---|---|---|---|
| **Izvedel** | | | |
| **Pregledal (QA)** | | | |
| **Odobril** | | | |

---

**KONEC DOKUMENTA**
