# Standardni operativni postopek (SOP)
## Uporaba validatorja MES receptur

---

## Nadzor nad dokumentom

| Polje | Vrednost |
|---|---|
| **Naslov dokumenta** | Standardni operativni postopek – Uporaba validatorja |
| **Sistem / Aplikacija** | Validator MES receptur (validator_oop) |
| **ID dokumenta** | VAL-SOP-USE-001 |
| **Verzija** | 1.0 |
| **Datum veljavnosti** | Določi se ob odobritvi |
| **Datum** | 2026-02-04 |
| **Lastnik SOP** | ______________________ |
| **Odobril (QA)** | ______________________ |

---

## 1. Namen

Ta standardni operativni postopek določa standardiziran proces za uporabo validatorja MES receptur za preverjanje Excel datotek receptur in generiranje validacijskih poročil, ki dokumentirajo identificirane napake in opozorila.

## 2. Obseg

Ta SOP velja za vse osebje, odgovorno za pred-validacijo MES receptur (oddelki QA, Proizvodnja, Proces), ki uporablja Validator v Windows okoljih preko GUI ali CLI vmesnikov.

## 3. Odgovornosti

| Vloga | Odgovornost |
|---|---|
| **Končni uporabnik** | Pravilna izbira vhodnih datotek, izvajanje validacije, pregled poročila, začetek korektivnih ukrepov |
| **QA** | Določitev pričakovanj validacije, pregled rezultatov validacije, ko je zahtevano, odobritev uporabe bypass |
| **Sistemski skrbnik** | Podpora pri namestitvi, diagnostika, posodobitve programske opreme, usposabljanje uporabnikov |

## 4. Oprema in predpogoji

### 4.1 Zahtevana oprema in programska oprema

- Operacijski sistem Windows 10 ali Windows 11
- Validator MES receptur (Python okolje ali EXE distribucija)

### 4.2 Programske odvisnosti (samo Python okolje)

| Odvisnost | Status | Namen |
|---|---|---|
| `openpyxl` | Zahtevano | Operacije z Excel datotekami |
| `python-docx` | Opcijsko | Parsiranje SOP Word dokumentov |
| `tkinter` | Opcijsko | Funkcionalnost GUI |

### 4.3 Zahteve za usposabljanje

Uporabniki morajo biti usposobljeni za:
- Uporabo validatorja (GUI ali CLI, kot je primerno)
- Interpretacijo poročil
- Pomene kod napak in korektivne ukrepe
- Postopke eskalacije za nerešene napake

## 5. Postopek – GUI uporaba (priporočeno za večino uporabnikov)

### 5.1 Zagon GUI

**Velja za:** Namestitve Python okolja

**Postopek:**
1. Navigirajte do direktorija `validator_oop\` v raziskovalcu datotek
2. Izvedite: `python main.py` (brez parametrov)
3. Preverite, da se GUI okno odpre z naslovom "Validator MES Receptur ..."

**Če se GUI ne zažene:** Preverite, da je `tkinter` nameščen, ali uporabite CLI postopek (Oddelek 6).

### 5.2 Izbira vhodne datoteke

**Postopek:**
1. Kliknite gumb **"Izberi…"**
2. Navigirajte do lokacije datoteke recepture
3. Izberite eno ali več Excel datotek (format `.xlsx` ali `.xlsm`)
4. Preverite, da se poti datotek pojavijo v polju "Vhodna Excel datoteka"
5. Če je izbranih več datotek, so poti prikazane ločene s podpičji

**Za počiščenje izbire:** Kliknite **"Počisti seznam"**

### 5.3 Konfiguracija izhodnega poročila

**Postopek:**
1. Izberite način poročila z uporabo radio gumbov:
   - **"Ena skupna datoteka"**: Ena datoteka poročila za vse izbrane datoteke
   - **"Ločeno poročilo za vsako datoteko"**: Posamezno poročilo na vhodno datoteko

2. Konfigurirajte izhodno lokacijo:
   - **Za kombinirano poročilo:** Kliknite **"Shrani kot…"**, izberite format `.xlsx` ali `.txt`
   - **Za ločena poročila:** Kliknite **"Shrani kot…"**, izberite izhodni direktorij

### 5.4 Izbira SOP dokumenta (opcijsko)

**Postopek:**
1. Kliknite gumb **"Izberi SOP…"**
2. Izberite SOP Word dokument (format `.docx`)
3. Če nalaganje SOP ne uspe:
   - Sistem prikaže opozorilno sporočilo v statusnem oknu
   - Validacija se nadaljuje brez preverjanj skladnosti s SOP

**Funkcionalnost SOP zahteva knjižnico `python-docx`.**

### 5.5 Izvajanje validacije

**Postopek:**
1. Kliknite gumb **"Zaženi validacijo"**
2. Spremljajte statusno okno za sporočila o napredku
3. Po zaključku preglejte statusno sporočilo:
   - **"OK: brez napak"**: Brez ugotovitev na ravni ERROR (opozorila so lahko prisotna)
   - **"Končano z napakami"**: Odkrite ugotovitve na ravni ERROR; preglejte poročilo

### 5.6 Pregled in dostop do poročila

**Dostop do mape poročila:**
1. Kliknite gumb **"Odpri mapo poročila"**
2. Sistem odpre izhodni direktorij v Windows Raziskovalcu

**Pregled Excel poročil:**
1. Odprite datoteko poročila v Microsoft Excel
2. Preglejte delovni list **"Povzetek"** za podrobnosti napak
3. Preglejte delovni list **"Število napak"** za povzetek napak po kodi

## 6. Postopek – CLI uporaba (vmesnik ukazne vrstice)

### 6.1 Osnovno izvajanje validacije

**Delovni direktorij:** `validator_oop\`

**Sintaksa ukaza:**
```
python main.py "<pot\do\recepture.xlsx>"
```

**Privzeto vedenje:** Generira Excel poročilo z imenom datoteke `<ime_recepture>_VALIDATION_REPORT.xlsx` v istem direktoriju kot vhodna datoteka.

### 6.2 Izbira formata poročila

**Excel poročilo z prilagojeno izhodno potjo:**
```
python main.py "receptura.xlsx" --format excel --output "izhodni_imenik\porocilo.xlsx"
```

**JSON izhod v konzolo:**
```
python main.py "receptura.xlsx" --format json
```

**Besedilno poročilo:**
```
python main.py "receptura.xlsx" --format text --output "porocilo.txt"
```

**Povzetek izhod:**
```
python main.py "receptura.xlsx" --format summary
```

### 6.3 Napredne možnosti

**Strogi način (WARNING → ERROR):**
```
python main.py "receptura.xlsx" --strict --format json
```

**Bypass pravila (zahteva odobritev QA za kritična pravila):**
```
python main.py "receptura.xlsx" --bypass <ime_pravila_ali_koda> --format json
```

Primer (več pravil):
```
python main.py "receptura.xlsx" --bypass step_numbering required_columns --format json
```

**Nalaganje formul:**
```
python main.py "receptura.xlsx" --include-formulas --format json
```

**Apply fixes (ustvari popravljeno kopijo):**
```
python main.py "receptura.xlsx" --apply-fixes --format summary
```

**OPOMBA:** Število apliciranih popravkov je lahko nič, če validacijska pravila ne generirajo predlogov popravkov.

### 6.4 Interpretacija izhodnih kod

| Izhodna koda | Pomen | Ukrep uporabnika |
|---|---|---|
| `0` | Validacija uspešna (brez ugotovitev ERROR) | Nadaljujte s postopkom odobritve recepture |
| `1` | Odkrite validacijske napake | Preglejte poročilo, popravite napake, ponovno validirajte |
| `2` | Napaka pri izvajanju | Preverite log datoteko (`MESValidator.log`), preverite dostopnost datoteke, preverite odvisnosti |

## 7. Interpretacija poročila in korektivni ukrepi

### 7.1 Struktura Excel poročila

**Delovni list "Povzetek":**
- Stolpci: List, Vrstica, Stolpec, Napaka (koda napake), Opis napake
- Vsaka vrstica predstavlja eno validacijsko ugotovitev
- Uporabite avtomatski filter za razvrščanje/filtriranje po listu, kodi napake ali resnosti

**Delovni list "Število napak":**
- Stolpci: Koda, Opis, Število
- Agregiran povzetek po kodi napake
- Uporabite za prioritizacijo korektivnih ukrepov

### 7.2 Pogosti scenariji napak in korektivni ukrepi

| Vzorec kode napake | Verjeten vzrok | Korektivni ukrep |
|---|---|---|
| `MISSING_COLUMN` | Manjkajoč zahtevani stolpec | Dodajte zahtevano glavo stolpca na delovni list |
| `STEP_*` | Težave s številčenjem korakov | Odstranite podvojitve, zapolnite vrzeli, zagotovite začetek številčenja z 1 |
| `CTRL_*`, `ZAKLENI_*` | Težave z definicijo kontrol | Preverite imena kontrol, parametre in kontekst (tip podatka/tip objekta) |
| `SOP_*` | Neskladnost s SOP | Uskladite delovni list "Podatki" z zahtevami SOP ali preverite, da je izbran pravilen SOP dokument |
| `KEY_FORMAT` | Neveljavni znaki ključa | Odstranite neveljavne znake iz "Ključ preverjanja" |
| `OBJ_MISMATCH` | Nezdružljivost tipov | Popravite "Tip objekta", da se ujema z zahtevami "Tip podatka" |

## 8. Diagnostika in odpravljanje težav

### 8.1 Lokacija log datoteke

Validator ustvarja diagnostično log datoteko:
- **Ime datoteke:** `MESValidator.log`
- **Lokacija:** HOME direktorij uporabnika (npr. `C:\Users\<uporabnik>\MESValidator.log`)

**Uporabite log datoteko za:**
- Podrobno diagnostiko napak
- Odpravljanje napak pri izvajanju
- Razhroščevanje težav z EXE distribucijo

### 8.2 Pogosta sporočila o napakah in rešitve

| Sporočilo o napaki | Vzrok | Rešitev |
|---|---|---|
| `openpyxl is required` | Manjkajoča Python knjižnica | Namestite: `pip install openpyxl` |
| `python-docx is required` | Manjkajoča Python knjižnica (validacija SOP) | Namestite: `pip install python-docx` ali onemogočite validacijo SOP |
| `Error: tkinter is required for the GUI` | Manjkajoča GUI knjižnica | Uporabite CLI način ali namestite Python distribucijo s tkinter |
| File not readable / corrupted | Neveljavna Excel datoteka ali zaklenjena datoteka | Preverite, da se datoteka odpre v Excel; preverite, da datoteka ni zaklenjena z drugim procesom |
| Permission denied writing report | Izhodna pot ni zapisljiva | Preverite dovoljenja za pisanje v izhodni direktorij; izberite alternativno lokacijo |

## 9. Nadzor sprememb in periodični pregled

### 9.1 Zahteve nadzora sprememb

Spremembe validatorja, ki vplivajo na validacijsko logiko, pravila ali izhodne formate, morajo biti:
- Dokumentirane v formalnem zapisu sprememb
- Ocenjene glede vpliva na rezultate validacije
- Pregledane in odobrene s strani QA
- Sledijo ponovnemu izvajanju relevantnih OQ testnih primerov

### 9.2 Periodični pregled

Ta SOP se mora pregledati:
- Vsaj letno
- Po pomembnih spremembah sistema
- Po večjih posodobitvah validacijskih pravil
- Ko se spremenijo regulatorne zahteve

## 10. Reference

### 10.1 Povezani dokumenti

- Specifikacija uporabniških zahtev: VAL-URS-001
- Funkcionalna specifikacija: VAL-FS-001
- Protokol operacijske kvalifikacije: VAL-OQ-001
- Ocena tveganja: VAL-RA-001

### 10.2 Podporne informacije

- Lokacija testnih podatkov: `validator_oop/samples/*`
- Referenčna poročila: `validator_oop/samples/*_VALIDATION_REPORT.xlsx`

---

## Podpisi za odobritev

| Vloga | Ime | Podpis | Datum |
|---|---|---|---|
| **Lastnik SOP** | | | |
| **Pregledal (QA)** | | | |
| **Odobril** | | | |

---

**Zgodovina revizij**

| Verzija | Datum | Avtor | Opis sprememb |
|---|---|---|---|
| 1.0 | 2026-02-04 | | Prva izdaja |

---

**KONEC DOKUMENTA**
