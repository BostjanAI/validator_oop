# Navodila za uporabo aplikacije IPO Validator

**Dokument:** NAV-158  
**Naslov:** Navodila za uporabo aplikacije IPO Validator  
**Verzija:** 5  
**Datum veljavnosti:** 1. 9. 2026  
  

---

## KAZALO

1. [Namen, princip in področje uporabe](#1-namen-princip-in-področje-uporabe)
2. [Definicije in okrajšave](#2-definicije-in-okrajšave)
3. [Postopek](#3-postopek)
   - 3.1 [Zagon aplikacije](#31-zagon-aplikacije)
   - 3.2 [Opis vmesnika](#32-opis-vmesnika)
   - 3.3 [Korak po korak: standardna validacija](#33-korak-po-korak-standardna-validacija)
   - 3.4 [Validacija več datotek hkrati](#34-validacija-več-datotek-hkrati)
   - 3.5 [Načina poročila](#35-načina-poročila)
   - 3.6 [Razlaga poročila](#36-razlaga-poročila)
4. [Opis napak in kako jih odpraviti](#4-opis-napak-in-kako-jih-odpraviti)
   - 4.1 [Strukturne napake](#41-strukturne-napake)
   - 4.2 [Napake polj](#42-napake-polj)
   - 4.3 [Relacijske napake](#43-relacijske-napake)
   - 4.4 [Napake kontrol](#44-napake-kontrol)
5. [Odgovornosti](#5-odgovornosti)
6. [Dokumentacija](#6-dokumentacija)
7. [Zapisi o spremembah](#7-zapisi-o-spremembah)
8. [Priloge, povezave in reference](#8-priloge-povezave-in-reference)

> **Opomba:** V primeru težav, nerazumevanja ali nepredvidenih dogodkov se posvetujte z nadrejeno osebo.

---

## 1. Namen, princip in področje uporabe

### Namen

Ta dokument opisuje postopek uporabe aplikacije **IPO Validator** – orodja, ki samodejno preveri pravilnost strukture Excel recepture pred njenim vnosom v sistem IPO. Validator zagotavlja, da so vse zahteve za strukturo, polja, kontrole in ključe izpolnjene, in prepreči vnos napačnih receptur v produkcijsko okolje.

### Princip

Aplikacija prebere Excel datoteko recepture (`.xlsm` ali `.xlsx`), izvede 38 preverjanj po štirih kategorijah pravil in rezultate zapiše v poročilo. Vsaka ugotovljena napaka ali opozorilo je točno locirana (list, vrstica, stolpec) skupaj z razlago vzroka in kodo napake.

**Kategorije preverjanj:**

| Kategorija | Opis |
|------------|------|
| **Strukturna pravila** | Obvezni stolpci, veljavnost in zaporedje številk korakov |
| **Pravila polj** | Vrednosti polj (Tip objekta, Labela, Ključ preverjanja, formule) |
| **Relacijska pravila** | Pari kemikalija/masa, datumi začetek/konec, podvojeni ključi |
| **Pravila kontrol** | Prisotnost in veljavnost vseh kontrol (npr. `kontrolainterval`, `zaklenipolja`) |

Validacija se zaključi z rezultatom:
- **Brez napak** – receptura je strukturno veljavna.
- **Z napakami** – v poročilu so navedene vse kršitve, ki jih je treba odpraviti.

### Področje uporabe

Ta navodila so namenjena **tehnologom**, ki pripravljajo ali posodabljajo recepture za sistem IPO. Navodila opisujejo postopek zagona aplikacije, razlago vmesnika, branje poročila in odpravljanje napak.

---

## 2. Definicije in okrajšave

| Izraz / okrajšava | Razlaga |
|-------------------|---------|
| **IPO** | Informacijski sistem za vodenje kromatografskih postopkov |
| **Receptura** | Excel datoteka `.xlsm`, ki opisuje postopek za sistem IPO |
| **Validator** | Aplikacija IPO Validator za preverjanje pravilnosti recepture |
| **ERROR** | Napaka, ki jo validator označi kot nepravilnost – pripravljalec jo mora preveriti in po presoji odpraviti |
| **WARNING** | Opozorilo – možna nepravilnost, ne blokira, a ga je priporočljivo odpraviti |
| **INFO** | Informativna beležka brez akcije |
| **Ključ preverjanja** | Unikaten identifikator koraka za sistem IPO |
| **Tip objekta** | Vrsta UI-elementa v sistemu IPO (npr. `edit`, `checkbox`) |
| **Tip podatka** | Vrsta vsebine, ki se vnaša (npr. `masa`, `raztopina`) |
| **Kontrola** | Pravilo preverjanja pri vnosu operaterja v sistemu IPO |
| **Poročilo** | Excel datoteka z rezultati validacije (`.xlsx` ali `.txt`) |

---

## 3. Postopek

### 3.1 Zagon aplikacije

Aplikacijo zaženete z dvojnim klikom na datoteko `Validator.exe` (ali `main.py` v razvijalskem okolju).

Po zagonu se odpre okno z naslovom **„Validator IPO Receptur"** s črno glavo in rumenim trakom z imenom organizacije.

> **Opomba:** Ob zagonu se v statusnem polju izpiše različica aplikacije, datum zagona in ime avtorja procesa. To je pričakovano delovanje – aplikacija je pripravljena za delo.

---

### 3.2 Opis vmesnika

Okno aplikacije vsebuje naslednje elemente:

| Element | Opis |
|---------|------|
| **Vhodna Excel datoteka (receptura)** | Polje, v katerem se prikažejo poti do izbranih receptur |
| **Izberi...** | Gumb za izbiro ene ali več receptur (`.xlsx`, `.xlsm`) |
| **Počisti seznam** | Gumb za čiščenje vseh izbranih datotek |
| **Izhodno poročilo (.xlsx ali .txt)** | Polje, kamor vnesete pot in ime poročila |
| **Shrani kot...** | Gumb za izbiro lokacije in formata poročila |
| **Način poročila** | Izbirate med: *Ena skupna datoteka* ali *Ločeno poročilo za vsako datoteko* |
| **Zaženi validacijo** | Zažene validacijo recepture |
| **Primerjaj razdelke med listi** | Primerja razdelke med listoma `Receptura` in `Receptura_2` |
| **Odpri mapo poročila** | Odpre mapo, kjer je shranjeno poročilo |
| **Statusno polje** | Prikazuje potek validacije in sporočila o napakah |

---

### 3.3 Korak po korak: standardna validacija

1. **Odprite aplikacijo** – dvokliknite `Validator.exe`.

2. **Izberite recepturo:**
   - Kliknite gumb **Izberi...** (pri vrstici *Vhodna Excel datoteka*).
   - V pogovornem oknu izberite datoteko recepture (`.xlsx` ali `.xlsm`).
   - Pot do datoteke se prikaže v polju.

3. **Določite izhodno poročilo:**
   - Kliknite gumb **Shrani kot...**.
   - Izberite mapo in vnesite ime datoteke poročila (npr. `porocilo_Receptura_A800.xlsx`).
   - Priporoča se format `.xlsx` (Excel), ki omogoča filtriranje po stolpcih.

4. **Zaženite validacijo:**
   - Kliknite gumb **Zaženi validacijo**.
   - V statusnem polju se sproti prikazuje potek.

5. **Preverite rezultat:**
   - Po končani validaciji se odpre pogovorno okno s povzetkom:
     - `"Brez napak"` – receptura je veljavna.
     - `"Najdene napake: N"` – odprite poročilo in preverite napake.

6. **Odprite poročilo:**
   - Kliknite **Odpri mapo poročila** ali poiščite datoteko poročila ročno.
   - Poročilo odprite v Excelu.

7. **Preglejte napake in po presoji odpravite:**
   - Vsako javljeno napako tipa ERROR preverite (glejte razdelek 4).
   - Če gre za dejansko nepravilnost, jo odpravite in ponovite korake 2–6.
   - Če napaka ne odraža dejanske nepravilnosti (validator jo je javil zgolj na podlagi svojih pravil), je receptura primerna za prenos v proizvodnjo kljub tej napaki.

---

### 3.4 Validacija več datotek hkrati

Aplikacija omogoča validacijo več receptur v enem zagonu:

1. Kliknite **Izberi...** in izberite eno datoteko.
2. Kliknite **Izberi...** znova in izberite naslednjo datoteko – doda se k obstoječemu seznamu.
3. Izberite **Način poročila:**
   - **Ena skupna datoteka** – vse napake iz vseh datotek so v enem poročilu.
   - **Ločeno poročilo za vsako datoteko** – za vsako recepturo se ustvari ločena datoteka poročila (ime: `por_<ime_recepture>.xlsx`) v izbrani mapi.
4. Kliknite **Zaženi validacijo**.

Za brisanje celotnega seznama datotek kliknite **Počisti seznam**.

---

### 3.5 Načina poročila

| Način | Kdaj uporabiti | Izhod |
|-------|----------------|-------|
| **Ena skupna datoteka** | Primerjava napak med recepturami ali pregled ene recepture | En `.xlsx` ali `.txt` z vsemi napakami |
| **Ločeno poročilo za vsako datoteko** | Serijska validacija večih receptur, ko vsaka dobi svoje poročilo | Mapa z datotekami `por_<ime>.xlsx` |

---

### 3.6 Razlaga poročila

Poročilo je Excel datoteka (`.xlsx`) z dvema listoma:

#### List „Povzetek"

Vsebuje glavo in seznam vseh najdenih napak in opozoril. Stolpci:

| Stolpec | Vsebina |
|---------|---------|
| **List** | Ime lista recepture in ime datoteke (npr. `Receptura_A800.xlsx:Receptura`) |
| **Vrstica** | Številka vrstice v Excel datoteki recepture, kjer je napaka |
| **Stolpec** | Ime stolpca, ki vsebuje napako (npr. `Labela`, `Kontrola 1`) |
| **Napaka** | Slovensko ime vrste napake (npr. `Manjka obvezen stolpec`) |
| **Opis napake** | Podroben opis: kaj točno je narobe in (pogosto) kakšna je pravilna vrednost |

Na vrhu lista sta navedeni ime aplikacije in njena različica.

**Brez napak:** V stolpcu Napaka piše `OK`, v stolpcu Opis napake pa `Ni najdenih strukturnih napak.`

#### List „Število napak"

Zbirni pregled: koliko napak posamezne vrste je bilo ugotovljenih. Stolpci: Koda, Opis, Število. Uporaben za hitro oceno, katere napake so najpogostejše.

#### Format `.txt`

Besedilno poročilo z eno vrstico na napako:
```
<datoteka:list> | vrstica <N> | stolpec <S> | <Opis napake> – <Podroben opis>
```

**Resnost napak:**

| Resnost | Pomen |
|---------|-------|
| **ERROR** | Napaka, ki jo validator označi – pripravljalec jo mora preveriti in po presoji odpraviti |
| **WARNING** | Opozorilo – možna nepravilnost, priporočljivo preveriti |
| **INFO** | Informativna beležka |

> **Pomembno:** Poročilo validacije je treba skrbno pregledati. Validator včasih javi napake, ki niso nujno dejanske napake v recepturi – pripravljalec receptur mora vsako javljeno napako (ERROR) individualno preveriti in presoditi, ali gre za dejansko nepravilnost. Če ugotovi, da receptura kljub napaki validatorja ustreza zahtevam, je primerna za prenos v proizvodnjo. Opozorila (WARNING) in informativne beležke (INFO) ne blokirajo, a jih je priporočljivo pregledati.

---

## 4. Opis napak in kako jih odpraviti

Vsaka napaka je opisana z:
- **Kodo** – tehnično oznako (prikazano v poročilu)
- **Opisom** – kaj pomeni napaka
- **Vzrokom** – zakaj se pojavi
- **Rešitvijo** – kako jo odpraviti

---

### 4.1 Strukturne napake

Te napake se nanašajo na osnovno strukturo lista (obvezni stolpci, zaporedje korakov).

---

#### `MISSING_COLUMN` – Manjka obvezen stolpec

**Opis:** V glavi lista manjka vsaj en od obveznih stolpcev.

**Vzrok:** Stolpec je bil izbrisan, preimenovan ali ni prisoten v datoteki.

**Rešitev:** Preverite, da imata lista `Receptura` in `Receptura_2` v prvi vrstici vse obvezne stolpce:

| Obvezni stolpci |
|-----------------|
| `št. Koraka` |
| `Navodilo` |
| `Tip podatka` |
| `Ključ preverjanja` |
| `Vrednost` |
| `Labela` |
| `Tip objekta` |
| `Kontrola 1`, `Kontrola 1 - par 1`, `Kontrola 1 - par 2` |
| `Kontrola 2`, `Kontrola 2 - par 1`, `Kontrola 2 - par 2` |
| `Kontrola 3`, `Kontrola 3 - par 1`, `Kontrola 3 - par 2` |
| `Kontrola 4`, `Kontrola 4 - par 1`, `Kontrola 4 - par 2` |

Preverite črkovanje – stolpec `st. Koraka` (brez strešice) ni veljavno ime.

---

#### `STEP_NOT_INTEGER` – Številka koraka ni celo število

**Opis:** Vrednost v stolpcu `št. Koraka` ni celo število (npr. `1.5`, `abc`).

**Vzrok:** Napačen vnos ali formula, ki vrne decimalno vrednost.

**Rešitev:** Preverite formulo v stolpcu `št. Koraka`. Mora biti `=C_prej+1` (in vrača cela števila). Vrednosti kot `1.0` niso dovoljene – le `1`, `2`, `3` ...

---

#### `STEP_MISSING` – Manjka številka koraka v vrstici

**Opis:** Vrstica ima vsebino (Navodilo ali Tip objekta), a je stolpec `št. Koraka` prazen.

**Vzrok:** Formula za številčenje je bila izbrisana ali ni bila dodana novi vrstici.

**Rešitev:** Dodajte formulo `=C_prej+1` v ustrezno celico stolpca `št. Koraka`. Vsaka vrstica s podatki mora imeti svojo številko koraka – vključno z vrsticami tipa `crta`.

---

#### `STEP_DUPLICATE` – Podvojena številka koraka

**Opis:** Dve ali več vrstic ima isto vrednost v stolpcu `št. Koraka`.

**Vzrok:** Napaka pri kopiranju – vrstica je bila kopirana z enako vrednostjo koraka; ali se pri `Receptura_2` isti zavihek nenamerno ponovi.

**Rešitev:**
- **Pri `Receptura` (brez zavihkov):** Preverite, da koraki tečejo neprekinjeno od 1 naprej brez ponovitev.
- **Pri `Receptura_2` (z zavihki):** Vsak zavihek začne s korakom `1` in naprej – podvojene vrednosti znotraj enega zavihka niso dovoljene.
- Priporoča se uporaba formul `=C_prej+1`, ki samodejno preprečijo podvajanje.

---

#### `STEP_TAB_NOT_FROM_ONE` – Koraki v zavihku se ne začnejo s 1

**Opis:** V listu `Receptura_2` se prvi korak novega zavihka ne začne z vrednostjo `1`.

**Vzrok:** Pri dodajanju novega zavihka je bila kopirana formula iz prejšnjega zavihka namesto vnosa vrednosti `1`.

**Rešitev:** V prvo vrstico vsakega novega zavihka (tipa `naslov`) v stolpec `št. Koraka` vpišite vrednost `1` (ne formulo `=C_prej+1`).

---

#### `STEP_GAPS` – Manjkajo vmesni koraki

**Opis:** V zaporedju korakov obstaja vrzel (npr. koraki so 1, 2, 4 – manjka 3).

**Vzrok:** Vrstica je bila izbrisana brez popravka formul; ali vrstice tipa `crta` nimajo številke koraka.

**Rešitev:**
- Preverite, da nobena vrstica ni bila izbrisana in da je zaporedje neprekinjeno.
- Vrstice tipa `crta` **morajo imeti** svojo številko koraka – niso izvzete.
- Če ste izbrisali vrstico, preverite, da so formule v naslednjih vrsticah pravilno posodobljene.

---

### 4.2 Napake polj

Te napake se nanašajo na vrednosti posameznih polj (stolpcev) v vrsticah recepture.

---

#### `OBJECT_TYPE_EMPTY` – Tip objekta ni določen

**Opis:** Stolpec `Tip objekta` je v vrstici prazen.

**Vzrok:** Manjkajoč vnos v celici.

**Rešitev:** Vsaka vrstica mora imeti izpolnjen `Tip objekta`. Izberite ustrezno vrednost iz dovoljenih:

| Vrednost | Kdaj |
|----------|------|
| `naslov` | Začetek sekcije ali zavihka |
| `crta` | Vizualni ločnik |
| `edit` | Vnosno polje (tekst/število) |
| `checkbox` | Polje za kljukico |
| `spustniseznam` | Spustni seznam opreme |
| `memo` | Večvrstično besedilo |
| `izberidatumcas` | Izbirnik datuma in časa |
| `gumbdatumcas` | Gumb za datum/čas |
| `formula` / `formula0` / `formula1` | Izračunano polje |
| `klictehtnice1` | Direktni klic tehtnice |

---

#### `OBJECT_TYPE_UNKNOWN` – Neznan tip objekta

**Opis:** Vrednost v stolpcu `Tip objekta` ni v seznamu dovoljenih vrednosti.

**Vzrok:** Tipkarska napaka (npr. `spustni seznam` namesto `spustniseznam`; `Edit` namesto `edit`).

**Rešitev:** Vrednosti so **občutljive na zapis** – pišite točno kot je navedeno, male črke, brez presledkov. Preverite črkovanje.

---

#### `DATA_TYPE_MASA_INVALID` – Tip podatka mora biti `masa`

**Opis:** V stolpcu `Tip podatka` je oštevilčena različica mase (npr. `masa1`, `masa2`).

**Vzrok:** Številka je vpisana v tip podatka namesto v `Ključ preverjanja`.

**Rešitev:** V `Tip podatka` vpišite točno `masa`. Različne mase ločite s ključem preverjanja (npr. `NaCl1`, `NaCl2`), ne z `masa1`.

---

#### `DATA_TYPE_POSEBNOSTI_REQUIRED` – Brez `monolitN` v isti vrstici mora biti `posebnosti`

**Opis:** V isti vrstici stolpec `Zavihek` ni `monolit1`, `monolit2`, …, `Tip podatka` pa je `posebnostimon`.

**Vzrok:** `posebnostimon` je vpisano v vrstici, ki nima kode monolita v `Zavihek`. Zavihek v drugi vrstici ne šteje.

**Rešitev:** V tej vrstici v `Tip podatka` vpišite `posebnosti`, ali v isti vrstici v `Zavihek` vpišite `monolit1`, `monolit2`, …

---

#### `DATA_TYPE_POSEBNOSTIMON_REQUIRED` – Ob `monolitN` v isti vrstici mora biti `posebnostimon`

**Opis:** V isti vrstici je v `Zavihek` vpisano `monolit1`, `monolit2`, …, `Tip podatka` pa je `posebnosti`.

**Vzrok:** Ob kodi monolita v isti vrstici je zahtevan tip `posebnostimon`.

**Rešitev:** V `Tip podatka` te vrstice vpišite `posebnostimon`.

---

#### `OBJECT_TYPE_MISMATCH` – Tip objekta ne ustreza tipu podatka

**Opis:** Kombinacija `Tip podatka` in `Tip objekta` ni veljavna.

**Vzrok:** Napačno določen `Tip objekta` glede na vsebino vrstice.

**Rešitev:** Preverite ujemanje:

| Tip podatka | Dovoljeni Tip objekta |
|-------------|----------------------|
| `kemikalija`, `raztopina`, `zaposleni`, `monolit`, `embalaza`, `repro`, `reproodpis`, `monomerna` | `edit` |
| `masa` | `edit`, `klictehtnice1` |
| `tehtnica`, `termometer`, `kopel`, `pH_meter`, `sušilnik`, `vak_sušilnik`, `merilnik`, `naprava`, `avtoklav` | `edit`, `spustniseznam` |
| `datumcas`, `datumcaszacetek`, `datumcaskonec` | `izberidatumcas`, `gumbdatumcas` |
| `checkbox` | `checkbox` |
| `naslov` | `naslov` |
| `crta` | `crta` |
| `memo` | `memo` |
| `formula`, `summasa` | `formula`, `formula0`, `formula1` |

---

#### `LABEL_MUST_BE_KODA` – Labela mora biti 'koda'

**Opis:** Za določene tipe podatka je zahtevana vrednost `koda` v stolpcu `Labela`, a je vrednost drugačna ali prazna.

**Vzrok:** Napačno vpisana Labela.

**Rešitev:** Za naslednje tipe podatka vpišite v stolpec `Labela` vrednost `koda` (male črke):

| Tip podatka, ki zahteva Labela = `koda` |
|-----------------------------------------|
| `kemikalija` |
| `zaposleni` |
| `monolit` |
| `repro` |
| `reproodpis` |

---

#### `LABEL_CHECKBOX_FORMAT` – Napačna oblika Labele pri checkboxu

**Opis:** Pri vrsticah s tipom objekta `checkbox` mora biti Labela ena od dveh dovoljenih vrednosti.

**Vzrok:** Napačna vrednost v stolpcu `Labela`.

**Rešitev:** Vpišite natanko eno od:
- `DA (kljukica)` – checkbox, ki zahteva obvezen DA
- `DA (kljukica)/NE (prazno)` – checkbox, ki dopušča DA ali NE

---

#### `KEY_INVALID_FORMAT` – Nepravilen zapis ključa

**Opis:** Vrednost v stolpcu `Ključ preverjanja` vsebuje nedovoljene znake.

**Vzrok:** Ključ vsebuje presledke, šumnike (č, š, ž) ali posebne znake.

**Rešitev:** Ključ sme vsebovati le:
- Črke `A–Z`, `a–z`
- Številke `0–9`
- Znake `-`, `_`, `.`

**Primeri veljavnih ključev:** `pretok_mf1`, `masa_kem1`, `2.73mp-NaCl_13.87mp-EtOH-GK1`

**Napačni ključi:** `pretok mf1` (presledek), `masa_čas` (šumnik č), `kem#1` (znak #)

---

#### `KEY_REQUIRED` – Manjka ključ preverjanja

**Opis:** Vrstica tipa `kemikalija`, `raztopina`, `masa` ali časovni par nima ključa preverjanja. Oprema in checkbox ključa ne zahtevata.

**Vzrok:** Stolpec `Ključ preverjanja` je pri tej vrstici puščen prazen.

**Rešitev:** Dodajte unikaten ključ preverjanja (glejte format zgoraj). Pri opremi s `Tip objekta = spustniseznam` namesto ključa zapolnite stolpec `Vrednost` (oznaka šifranta).

---

#### `SPUSTNISEZNAM_VREDNOST_EMPTY` – Manjka vrednost pri spustnem seznamu

**Opis:** Vrstica s `Tip objekta = spustniseznam` nima zapolnjenega stolpca `Vrednost`. Pri opremi je ta stolpec obvezen namesto ključa preverjanja.

**Vzrok:** Stolpec `Vrednost` je prazen, čeprav gre za spustni seznam (dropdown šifranta opreme).

**Rešitev:** V stolpec `Vrednost` vpišite oznako šifranta (npr. `HPLC`, `tehtnica`, `TEH-KLA`).

---

#### `CRTA_STEP_EMPTY` – Pri `crta` manjka številka koraka

**Opis:** Vrstica s `Tip objekta = crta` nima zapolnjenega stolpca `št. Koraka`.

**Vzrok:** Ločilna vrstica je brez številke koraka (ali je stolpec pomotoma izpraznjen).

**Rešitev:** V `št. Koraka` vpišite formulo `=C_prej+1` (ali `1` na začetku zavihka). Vrstice tipa `crta` **morajo imeti** številko koraka.

---

#### `CRTA_COLUMN_NOT_EMPTY` – Pri `crta` mora biti stolpec prazen

**Opis:** Vrstica s `Tip objekta = crta` ima zapolnjen stolpec, ki mora biti prazen.

**Vzrok:** V ločilno vrstico so vpisani podatki (npr. `Navodilo`, ključ, kontrole).

**Rešitev:** Pri `crta` pustite prazne vse stolpce razen `št. Koraka` (obvezen), `Tip objekta` in po potrebi `Tip podatka`. `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, …).

---

#### `NASLOV_STEP_EMPTY` – Pri `naslov` manjka številka koraka

**Opis:** Vrstica s `Tip objekta = naslov` nima zapolnjenega stolpca `št. Koraka`.

**Rešitev:** V `št. Koraka` vpišite `1` (nov zavihek) ali formulo `=C_prej+1`.

---

#### `NASLOV_NAVODILO_EMPTY` – Pri `naslov` manjka Navodilo

**Opis:** Vrstica s `Tip objekta = naslov` nima besedila v stolpcu `Navodilo`.

**Rešitev:** V `Navodilo` vpišite naslov razdelka (besedilo, ki ga vidi operater).

---

#### `NASLOV_COLUMN_NOT_EMPTY` – Pri `naslov` mora biti stolpec prazen

**Opis:** Vrstica s `Tip objekta = naslov` ima zapolnjen stolpec, ki mora biti prazen.

**Rešitev:** Pri `naslov` zapolnite samo `št. Koraka` in `Navodilo`. `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, …), enako kot pri `crta`. Ostali stolpci (ključ, vrednost, labela, kontrole) naj bodo prazni.

---

#### `FORMULA_SYNTAX` – Nepravilen zapis formule

**Opis:** Pri vrsticah s tipom objekta `formula`, `formula0` ali `formula1` vsebina stolpca `Vrednost` ni veljavna formula (ne začne se z `=`).

**Vzrok:** Formula je bila vpisana kot besedilo ali pa je prazna.

**Rešitev:** Vrednost mora biti Excelova formula, ki se začne z `=` in vsebuje sklic `$` na korake. Primer:
```
="=($"&C113&"-"&"$"&C108&")/($"&C108&"-$"&C89&")"
```

---

#### `FORMULA_AMPERSAND_DOLLAR` – Formula vsebuje nedovoljen zapis `&$`

**Opis:** Pri vrsticah s tipom objekta `formula`, `formula0` ali `formula1` stolpec `Vrednost` vsebuje zaporedje `&$`.

**Vzrok:** Sklic na korak je zapisan kot `&$…` (npr. `&$12` ali `&$C12`) namesto kot spoj znaka `$` in celice s številko koraka.

**Rešitev:** Sklic zapišite kot `"$"&` in celico s številko koraka, npr. `"$"&C12`. Zapis `&$` odstranite.

---

#### `FORMULA_NO_REFERENCE` – Formula nima sklica na korake

**Opis:** Formula v stolpcu `Vrednost` ne vsebuje znaka `$` (sklica na korak).

**Vzrok:** Formula ne vsebuje referenc na korake (`$N`).

**Rešitev:** Formule morajo vsebovati sklice na številke korakov v obliki `$N` (npr. `$113`). Preverite, da ste vstavili pravilne reference s pomočjo stolpca `C` (npr. `"$"&C113`).

---

#### `FORMULA_INVALID_REFERENCE` – Formula se sklicuje na neobstoječ korak

**Opis:** Formula vsebuje `$N`, kjer N ni veljavna številka koraka v tem listu.

**Vzrok:** Sklicujete se na korak, ki je bil izbrisan ali mu je bila spremenjena številka.

**Rešitev:** Preverite, da se formula sklicuje le na obstoječe korake. Vrednost `N` v `$N` mora biti ena od obstoječih vrednosti v stolpcu `št. Koraka`.

---

#### `FORMULA_STEP_INVALID_TYPE` – Sklicani korak nima ustreznega tipa objekta

**Opis:** Formula se sklicuje na korak, katerega `Tip objekta` ni dovoljen za sklicevanje.

**Vzrok:** Formula kaže na korak tipa `naslov`, `crta`, `checkbox` ali drugega, iz katerega sistem IPO ne more izračunati vrednosti.

**Rešitev:** Formule se smejo sklicevati le na korake s tipom objekta: `edit`, `formula`, `formula0`, `formula1`. Preverite vsak `$N` v formuli in se prepričajte, da ima navedeni korak ustrezen tip.

---

#### `COMMA_NOT_ALLOWED` – Nedovoljena vejica v številu

**Opis:** Numerična vrednost vsebuje vejico namesto pike kot decimalno ločilo (npr. `6,5` namesto `6.5`).

**Vzrok:** Napačen vnos – v slovenskem jezikovnem okolju se vejica pogosto piše kot decimalno ločilo, a sistem IPO zahteva piko.

**Rešitev:** Zamenjajte vejice s pikami v numeričnih vrednostih. Izjema: v stolpcu `Navodilo` so vejice dovoljene; prav tako pri parametrih kontrole `zaklenipolja` (kjer vejica ločuje številke korakov).

---

#### `SPACE_NOT_ALLOWED` – Nedovoljen presledek v vrednosti

**Opis:** Vrednost v enem od stolpcev (razen `Navodilo`, `Labela`, `Vrednost` in `Ključ preverjanja`) vsebuje presledek.

**Vzrok:** Presledek je bil vstavljen med tipkanjem ali pri lepljenju vrednosti iz drugega vira.

**Rešitev:** Odstranite presledek iz vrednosti v navedenem stolpcu. Presledki so dovoljeni v stolpcih `Navodilo`, `Labela`, `Vrednost` in `Ključ preverjanja`.

**Posebej – stolpec `Zavihek`:** Presledek v `Zavihek` **ne odpira novega zavihka**. Validator javi napako v tem stolpcu; pravil `zaklenipolja` in številčenja korakov zaradi tega ne razbije. Popravite celico v `Zavihek`.

---

#### `NAVODILO_RANGE_DASH_SPACING` – Presledki pri razponu v Navodilu

**Opis:** Razpon v stolpcu `Navodilo` nima presledka pred pomišljajem in za njim (npr. `4000–4400` ali `4000-4400`).

**Vzrok:** Razpon je zapisan strnjeno ali z neenakomernimi presledki.

**Rešitev:** Zapišite razpon z enim presledkom pred pomišljajem in enim za njim: `4000 – 4400`. Pravilo ne velja za zapise, ki niso razpon (npr. `7647-14-5`, `2026-01-01`, `SOP-123`).

---

#### `UNIT_MISMATCH` – Enota v Labeli se ne ujema z enoto v Navodilu

**Opis:** Enota, navedena v stolpcu `Labela`, se ne ujema z enoto, ki je navedena v stolpcu `Navodilo`.

**Vzrok:** Neskladnost med besedilom navodila in labelo (npr. Navodilo: `pretok MF1 (800 mL/min)`, Labela: `L/min`).

**Rešitev:** Uskladite enoto v stolpcu `Labela` z enoto iz stolpca `Navodilo`. Obe morata biti enaki (npr. obe `mL/min`).

---

### 4.3 Relacijske napake

Te napake se nanašajo na logične odnose med vrsticami (pari masa/kemikalija, začetek/konec časa, podvojeni ključi).

---

#### `PAIR_MASS_WITHOUT_OWNER` – Masa nima pripadajoče kemikalije ali raztopine

**Opis:** Vrstica `masa` nima ustrezne predhodne vrstice `kemikalija` ali `raztopina` z ujemajočim ključem.

**Vzrok:** Ključ mase se ne ujema z ključem kemikalije/raztopine; ali pa vrstica kemikalije/raztopine manjka.

**Rešitev:** Preverite, da ima vsaka vrstica `masa` neposredno predhodno vrstico `kemikalija` ali `raztopina` z enakim baznim ključem. Primer:
- Kemikalija: ključ `NaCl1`
- Masa: ključ `NaCl1` ✓ (ujemanje)
- Masa: ključ `NaCl2` ✗ (ne ujema se)

---

#### `PAIR_CHEM_WITHOUT_MASS` – Za kemikalijo manjka ustrezna masa

**Opis:** Vrstica `kemikalija` nima vrstice `masa` z enakim ključem preverjanja.

**Vzrok:** Manjka parna vrstica ali je namesto `masa` vpisan `volumen`.

**Rešitev:** Dodajte vrstico z `Tip podatka = masa` in **istim** ključem. `volumen` z istim ključem ni dovoljen (razen pri `dH2O`).

---

#### `PAIR_SOL_WITHOUT_MASS` – Za raztopino manjka ustrezna masa

**Opis:** Vrstica `raztopina` nima vrstice `masa` z enakim ključem preverjanja.

**Vzrok:** Manjka parna vrstica ali je namesto `masa` vpisan `volumen`.

**Rešitev:** Dodajte vrstico z `Tip podatka = masa` in **istim** ključem. Za porabo raztopine ne uporabljajte tipa `volumen`.

---

#### `PAIR_VOLUME_NOT_ALLOWED` – Volumen z istim ključem ni dovoljen

**Opis:** Ob kemikaliji/raztopini obstaja vrstica `volumen` z enakim ključem preverjanja.

**Vzrok:** Poraba je vpisana kot `volumen` namesto `masa`.

**Rešitev:** Spremenite `Tip podatka` v `masa`. Izjema: ključ `dH2O` (takrat je `volumen` pravilen).

---

#### `PAIR_WATER_WITHOUT_VOLUME` – Za dH2O mora biti volumen

**Opis:** Kemikalija/raztopina s ključem vode nima vrstice `volumen`.

**Vzrok:** Pri vodi je vpisan `masa` ali pa parna vrstica manjka.

**Rešitev:** Za `dH2O` uporabite `Tip podatka = volumen` (voda ni v modulu RAZTOPINE).

---

#### `PAIR_MASS_SECTION_MISMATCH` – Ključ mase se ne ujema z raztopino/kemikalijo

**Opis:** Vrstica `masa` je umeščena pred svojo kemikalijo/raztopino ali v napačnem razdelku.

**Vzrok:** Masa je bila premaknjena ali dodana na napačno mesto v recepturi.

**Rešitev:** Masa mora vedno slediti svoji kemikaliji ali raztopini v istem razdelku. Preverite vrstni red vrstic.

---

#### `PAIR_KOLICINA_WITHOUT_OWNER` – Kolicina nima pripadajočega repro

**Opis:** Vrstica `kolicina` nima ustrezne predhodne vrstice `repro` na istem zavihku.

**Vzrok:** Manjka vrstica `repro` nad količino, ali je `repro` na drugem zavihku.

**Rešitev:** Nad vsako vrstico `kolicina` mora biti vrstica `repro` z istim ključem preverjanja.

---

#### `PAIR_KOLICINA_KEY_MISMATCH` – Ključ količine se ne ujema z repro

**Opis:** Vrstica `kolicina` nima enakega ključa preverjanja kot najbližji predhodni `repro` na istem zavihku.

**Vzrok:** Ključ je ostal od kopiranja (npr. `telo_V4` namesto `telo_samec_V4`).

**Rešitev:** Vrstica `kolicina` mora imeti **enak** ključ kot njen `repro`. Primer:
- Repro: ključ `telo_samec_V4`
- Kolicina: ključ `telo_samec_V4` ✓
- Kolicina: ključ `telo_V4` ✗

---

#### `PAIR_TIME_WITHOUT_END` – Začetni čas brez končnega

**Opis:** Vrstica `datumcaszacetek` nima ustrezne vrstice `datumcaskonec` z enakim ključem.

**Vzrok:** Manjka vrstica za vnos končnega časa ali ima napačen ključ.

**Rešitev:** Vsak par začetek/konec mora imeti enak ključ. Dodajte vrstico `datumcaskonec` z istim ključem preverjanja kot `datumcaszacetek`.

---

#### `PAIR_TIME_WITHOUT_START` – Končni čas brez začetnega

**Opis:** Vrstica `datumcaskonec` nima ustrezne vrstice `datumcaszacetek` z enakim ključem.

**Vzrok:** Manjka vrstica za vnos začetnega časa ali ima napačen ključ.

**Rešitev:** Enako kot pri `PAIR_TIME_WITHOUT_END` – zagotovite ujemajoč par.

---

#### `KEY_DUP_CHEM` / `KEY_DUP_SOL` – Podvojen ključ kemikalije ali raztopine

**Opis:** Dve vrstici `kemikalija` ali `raztopina` imata enak ključ preverjanja.

**Vzrok:** Isti ključ je bil kopiran in ni bil spremenjen.

**Rešitev:** Vsaka kemikalija/raztopina mora imeti unikaten ključ. Dodajte numerično pripono (npr. `NaCl1`, `NaCl2`, `NaCl3`). Zaporedje se mora začeti z `1` brez vrzeli.

---

#### `KEY_DUP_MASS_SECTION` – Isti ključ mase v več razdelkih

**Opis:** Ključ mase se pojavlja v več razdelkih recepture, a brez ustreznega lastnika v vsakem od razdelkov.

**Vzrok:** Masa z istim ključem je bila kopirana v nov razdelek brez spremembe ključa.

**Rešitev:** Preverite, da ima vsaka masa unikaten ključ znotraj razdelka, ali da ima vsak razdelek svojega lastnika (kemikalija/raztopina z ustreznim ključem).

---

#### `KEY_DUP_MASS` – Podvojen ključ mase

**Opis:** Dve vrstici `masa` v istem razdelku imata enak ključ preverjanja, pri čemer nimata skupnega lastnika.

**Vzrok:** Isti ključ je bil kopiran in ni bil spremenjen.

**Rešitev:** Vsakemu koraku z maso dodelite unikaten ključ (npr. `NaCl1_masa`, `NaCl2_masa`).

---

#### `KEY_NUM_NOT_FROM_ONE` – Oštevilčenje ključev se ne začne z 1

**Opis:** Ključi iste vrste se začnejo z številko, ki ni `1` (npr. `GK2`, `GK3` brez `GK1`).

**Vzrok:** Vrstica z ključem `GK1` je bila izbrisana.

**Rešitev:** Oštevilčeni ključi morajo začeti pri `1`. Preverite, da je prva raztopina/kemikalija oštevilčena z `1`.

---

#### `KEY_NUM_GAP` – Vrzel v oštevilčenju ključev

**Opis:** V zaporedju oštevilčenih ključev obstaja vrzel (npr. `GK1`, `GK3` – manjka `GK2`).

**Vzrok:** Vmesna vrstica je bila izbrisana.

**Rešitev:** Zaporedje ključev mora biti neprekinjeno (1, 2, 3 ...). Preimenujte ključe ali dodajte manjkajočo vrstico.

---

#### `SCALE_VALUE_TOO_HIGH` / `SCALE_VALUE_TOO_LOW` – Napačna tehtnica

**Opis:** Vrednost mase v recepturi nakazuje, da je bila izbrana tehtnica napačnega razreda.

**Vzrok:**
- `SCALE_VALUE_TOO_HIGH`: masa ≥ 10, a je bila določena analitska tehtnica (`TEH-ANA`) namesto klasične (`TEH-KLA`).
- `SCALE_VALUE_TOO_LOW`: masa < 10, a je bila določena klasična tehtnica (`TEH-KLA`) namesto analitske (`TEH-ANA`).

**Rešitev:** V stolpcu `Vrednost` pri vrstici `tehtnica` nastavite ustrezno kodo:
- **masa ≥ 10 g** → `TEH-KLA` (ali `TEH-KLA, TEH-ANA` za oba razreda)
- **masa < 10 g** → `TEH-ANA` (ali `TEH-KLA, TEH-ANA` za oba razreda)

---

### 4.4 Napake kontrol

Te napake se nanašajo na pravilnost kontrol v stolpcih `Kontrola 1` do `Kontrola 4`.

---

#### `CTRL_UNKNOWN` – Neznano ime kontrole

**Opis:** Vrednost v stolpcu `Kontrola N` ni v seznamu veljavnih kontrol.

**Vzrok:** Tipkarska napaka ali zastarelo ime kontrole.

**Rešitev:** Preverite črkovanje. Veljavna imena kontrol (vse male črke, brez presledkov):

| Ime kontrole | Namen |
|--------------|-------|
| `kontrolapraznopolje` | Polje ne sme biti prazno |
| `kontrolainterval` | Vrednost v intervalu [min, max] |
| `kontrolacasa` | Trajanje v intervalu (sekunde) |
| `aliobkljukan` | Checkbox mora biti označen |
| `aliniobkljukan` | Checkbox ne sme biti označen |
| `aliobstajapogoj` | Polje aktivno pod pogojem |
| `aliobstajapogoj_ali` | Pogoj z ALI logiko |
| `alipravavloga` | Preverja vlogo operaterja |
| `alipravavlogakoda` | Preverja vlogo po kodi |
| `kdoizpolni` | Določa, kdo sme izpolniti |
| `zaklenipolja` | Zaklene seznam korakov |
| `aliisto` | Vrednost mora biti enaka drugemu koraku |
| `kontrolaveljavnostiopreme` | Oprema mora biti veljavna |
| `kontrolaustreznostiopreme` | Oprema mora biti primerna |
| `kontrolaveljavnostiraztopine` | Raztopina mora biti veljavna |
| `kontrolaustreznostiraztopine` | Raztopina mora biti ustrezna |
| `kontrolaveljavnostimonolita` | Monolit mora biti veljaven |
| `kontrolaustreznostimonolita` | Monolit mora biti ustrezen |
| `kontrolaveljavnostikemikalije` | Kemikalija mora biti veljavna |
| `kontrolaustreznostikemikalije` | Kemikalija mora biti ustrezna |
| `kontrolamase` | Masa mora biti pravilna |
| `kontrolaembalaze` | Embalaža mora biti veljavna |
| `kontrolarazlika` | Razlika med vrednostmi v mejah |

---

#### `CTRL_COL1_RESERVED` – Kontrola v rezerviranem stolpcu `Kontrola 1`

**Opis:** Stolpec `Kontrola 1` je rezerviran samo za kontroli `zaklenipolja` in `aliobstajapogoj`.

**Vzrok:** V stolpcu `Kontrola 1` je druga kontrola (npr. `kontrolapraznopolje`, `kontrolainterval`).

**Rešitev:** Premaknite kontrolo (skupaj z njenima `par 1` / `par 2`) v `Kontrola 2` ali naprej.

---

#### `CTRL_INVALID_CONTEXT` – Kontrola ni dovoljena v tem kontekstu

**Opis:** Kontrola je veljavna (obstaja v seznamu), a ni dovoljena za ta tip podatka ali tip objekta.

**Vzrok:** Napačna kombinacija kontrole in tipa vrstice (npr. `kontrolainterval` pri `checkbox`, ali `aliobkljukan` pri `edit`).

**Rešitev:** Preverite, katere kontrole so dovoljene za dani tip podatka in tip objekta. Napačno kontrolo zamenjajte z ustrezno ali jo odstranite.

---

#### `CTRL_REQUIRED_EMPTY` – Manjka kontrola `kontrolapraznopolje`

**Opis:** Vnosno polje (tip `edit`, `spustniseznam`, `izberidatumcas`, `gumbdatumcas`, `memo`) nima kontrole `kontrolapraznopolje`.

**Vzrok:** Kontrola je bila pozabljena ali izbrisana.

**Rešitev:** Dodajte `kontrolapraznopolje` v zadnji prosti kontrolni reži (npr. `Kontrola 2`, `Kontrola 3`). Ta kontrola je obvezna za vse vnosne objekte.

> **Izjema:** Tipi `checkbox`, `naslov` in `crta` **ne smejo** imeti `kontrolapraznopolje` – napaki `CTRL_CHECKBOX_EMPTY` oziroma `CTRL_EMPTY_NOT_ALLOWED`.

---

#### `CTRL_CHECKBOX_EMPTY` – Checkbox ima nedovoljeno kontrolo `kontrolapraznopolje`

**Opis:** Vrstica tipa checkbox ima kontrolo `kontrolapraznopolje`, ki pri checkboxu ni dovoljena.

**Vzrok:** Napačen vnos ali kopiranje iz vrstice z `edit` tipom.

**Rešitev:** Pri checkboxu odstranite `kontrolapraznopolje`. Namesto nje uporabite `aliobkljukan` z Param1 `DA`.

---

#### `CTRL_EMPTY_NOT_ALLOWED` – `naslov` ali `crta` ima nedovoljeno kontrolo `kontrolapraznopolje`

**Opis:** Vrstica tipa `naslov` ali `crta` ima kontrolo `kontrolapraznopolje`, ki tam ni dovoljena.

**Vzrok:** Napačen vnos ali kopiranje iz vrstice z vnosnim poljem.

**Rešitev:** Pri `naslov` in `crta` odstranite `kontrolapraznopolje`. Ti tipi niso vnosna polja.

---

#### `CTRL_EXPECTED_MISSING` – Manjka pričakovana kontrola (WARNING)

**Opis:** Za dani tip vrstice manjka ena ali več pričakovanih kontrol (opozorilo, ne blokira).

**Vzrok:** Za določene tipe (kemikalija, monolit, raztopina, oprema ...) so predpisane specifične kontrole, ki manjkajo.

**Rešitev:** Preverite pričakovano kombinacijo kontrol glede na tip:

| Tip podatka | Pričakovane kontrole |
|-------------|---------------------|
| `kemikalija` | `kontrolaveljavnostikemikalije`, `kontrolaustreznostikemikalije`, `kontrolapraznopolje` |
| `raztopina` | `kontrolaveljavnostiraztopine` (Par1 zapolnjen, ujemanje s ključem se ne zahteva), `kontrolaustreznostiraztopine` (Par1 zapolnjen, ujemanje s ključem se ne zahteva), `kontrolapraznopolje` |
| `monolit` | `kontrolaustreznostimonolita` (Par1: kode tipov), `kontrolaveljavnostimonolita`, `kontrolapraznopolje` |
| `tehtnica`/oprema | `kontrolaveljavnostiopreme` (Par1: tip), `kontrolaustreznostiopreme` (Par1: tip), `kontrolapraznopolje` |
| `checkbox` (DA) | `aliobkljukan` (Par1: `DA`) |
| `zaposleni` | `alipravavlogakoda` (Par1: vloga), `kontrolapraznopolje` |
| `datumcaskonec` | `kontrolacasa` (Par1: min sek, Par2: max sek), `kontrolapraznopolje` |

---

#### `CTRL_INTERVAL_PARAMS` – Kontrola interval brez mej

**Opis:** Kontrola `kontrolainterval` nima vsaj enega od parametrov (Par1 ali Par2).

**Vzrok:** Manjkajoča vrednost v stolpcu `Kontrola N - par 1` ali `Kontrola N - par 2`.

**Rešitev:** Vedno vnesite obe meji:
- `Kontrola N - par 1` = spodnja meja (minimum)
- `Kontrola N - par 2` = zgornja meja (maximum)

Vrednosti sta lahko Excelovi formuli (npr. `=INDEX(Podatki!...)`).

---

#### `CTRL_INTERVAL_NOT_NUMBER` – Meja intervala ni število

**Opis:** Parametri `kontrolainterval` ne vsebuje veljavne numerične vrednosti.

**Vzrok:** Parameter vsebuje besedilo, napačno formulo ali Excelovo napako (npr. `#REF!`).

**Rešitev:** Preverite, da formula v Param1/Param2 vrača numerično vrednost. Preverite sklice na list `Podatki` – ali so pravilni.

---

#### `CTRL_INTERVAL_RANGE` – Maximum je manjši ali enak minimumu

**Opis:** Zgornja meja (Par2) je manjša ali enaka spodnji meji (Par1) pri kontroli `kontrolainterval`.

**Vzrok:** Napačen vrstni red parametrov ali napačne vrednosti v listu `Podatki`.

**Rešitev:** Preverite, da velja `Par2 > Par1`. Zamenjajte vrednosti, če sta bili zamenjani.

---

#### `CTRL_INTERVAL_P1_BOUND` / `CTRL_INTERVAL_P2_BOUND` – Napačna meja intervala

**Opis:** Parametra `kontrolainterval` se ne ujemata z vrednostjo ali intervalom, zapisanim v stolpcu `Navodilo`.

**Vzrok:** Validator primerja Par1/Par2 z mejami, ki izhajajo iz besedila navodila (razpon `a–b`, toleranca `± t` ali neenačba `> x`). Če se ne ujemajo, je to napaka.

**Rešitev:** Preverite, da parametri intervala ustrezajo pravilom:

- **Razpon** (npr. Navodilo: `5–10`, korak eps=1): kanonsko `Par1 = 4`, `Par2 = 11`; pri `47.5–52.5` `Par1 = 47.4`, `Par2 = 52.6`; pri `0.18–0.22` `Par1 = 0.17`, `Par2 = 0.23`; pri `0.01–0.30` (kjer bi bil `a − eps` enak 0) so sprejemljive vrednosti v `[0.004, 0.305]` (`0`, `0.003`, `0.306` in `0.310` so napake).
- **Toleranca ±** (npr. Navodilo: `6.50 ± 0.10`, eps=0.01): kanonsko `Par1 = 6.39`, `Par2 = 6.61`; sprejemljive so tudi vrednosti v `[6.34, 6.65]`. `6.33` in `6.66` sta napaki.
- **Neenačba** (npr. Navodilo: `> 5`): `Par1 = 5`, `Par2 ≥ 6`

---

#### `CTRL_CASA_REQUIRED` – Manjka kontrola časa pri `datumcaskonec`

**Opis:** Vrstica `datumcaskonec` nima kontrole `kontrolacasa`.

**Vzrok:** Kontrola ni bila dodana.

**Rešitev:** Dodajte `kontrolacasa` z:
- `Par1` = minimalni čas trajanja v sekundah
- `Par2` = maksimalni čas trajanja v sekundah

---

#### `CTRL_CASA_MIN` – Manjka minimalna vrednost časa

**Opis:** Kontrola `kontrolacasa` nima Param1 (minimalne vrednosti).

**Vzrok:** Par1 je prazen.

**Rešitev:** Vnesite minimalni čas v sekundah v stolpec `Kontrola N - par 1`.

---

#### `CTRL_INTERVAL_REQUIRED` – Manjka kontrola `kontrolainterval` ali `kontrolarazlika`

**Opis:** Stolpec `Navodilo` vsebuje numeričen interval (razpon, ±, neenačba), a ni ne `kontrolainterval` ne `kontrolarazlika`.

**Vzrok:** Kontrola ni bila dodana, čeprav navodilo zahteva preverjanje vrednosti.

**Rešitev:** Dodajte `kontrolainterval` s pravilnimi mejami (glejte pravila za izračun v razdelku `CTRL_INTERVAL_P1_BOUND`) ali `kontrolarazlika`.

---

#### `CTRL_ALIOBKLJUKAN_REQUIRED` – Manjka `aliobkljukan` pri checkboxu

**Opis:** Vrstica tipa checkbox z Labelo `DA (kljukica)` nima kontrole `aliobkljukan`.

**Vzrok:** Kontrola ni bila dodana.

**Rešitev:** Dodajte `aliobkljukan` s Param1 = `DA`.

---

#### `CTRL_ALIPRAVAVLOGAKODA_REQUIRED` – Manjka kontrola vloge pri `zaposleni`

**Opis:** Vrstica tipa `zaposleni` nima kontrole `alipravavlogakoda`.

**Vzrok:** Kontrola ni bila dodana.

**Rešitev:** Dodajte `alipravavlogakoda` s Param1 = ime vloge:
- `ROLE_HEAD` – za vodje
- `ROLE_OPERATOR` – za operaterje

---

#### `CTRL_MONOLIT_VALIDITY_REQUIRED` / `CTRL_MONOLIT_SUITABILITY_REQUIRED` – Manjka kontrola monolita

**Opis:** Vrstica `monolit` nima ene ali obeh predpisanih kontrol.

**Vzrok:** Kontrola manjka.

**Rešitev:** Vsaka vrstica `monolit` mora imeti:
```
Kontrola 1: kontrolaustreznostimonolita  |  Par1: <koda tipa, npr. MOD,SPIR>
Kontrola 2: kontrolaveljavnostimonolita
Kontrola 3: kontrolapraznopolje
```

---

#### `LOCK_P1_FORMAT` – Napačen format Par1 pri `zaklenipolja`

**Opis:** Param1 pri kontroli `zaklenipolja` ni v pravilnem formatu (seznam celih števil, ločenih z vejicami).

**Vzrok:** Param1 vsebuje besedilo, decimalna števila, presledke ali druge nedovoljene znake.

**Rešitev:** Param1 mora biti seznam celih številk, ločenih z vejicami, brez presledkov. Primer: `45,46,47,48`. Dinamičen seznam z Excelovo formulo: `=C58&","&C60&","&C61`.

---

#### `LOCK_P1_STEP_MISSING` – Korak v Par1 ne obstaja

**Opis:** Param1 pri `zaklenipolja` navaja številko koraka, ki ne obstaja v listu.

**Vzrok:** Korak je bil izbrisan ali je bila spremenjena njegova številka.

**Rešitev:** Preverite vse številke korakov v Param1 in zagotovite, da obstajajo. Pri dinamičnih formulah (npr. `=C58&...`) preverite, da se te celice sklicujejo na veljavne korake.

---

#### `LOCK_P1_WITHOUT_CONDITION` – Korak v Par1 nima `aliobstajapogoj`

**Opis:** Korak, naveden v Param1 pri `zaklenipolja`, nima kontrole `aliobstajapogoj`.

**Vzrok:** Manjka pogoj za zaklepanje koraka.

**Rešitev:** Vsak korak, ki je naveden v Param1 pri `zaklenipolja`, mora imeti kontrolo `aliobstajapogoj` z ustreznim ključem in Param2 = `0` ali `1`.

---

#### `LOCK_CONDITION_P1_LOCK_KEY` – Napačen ključ v Par1 pri `aliobstajapogoj`

**Opis:** Param1 pri kontroli `aliobstajapogoj` ni ključ sklopa `zaklenipolja`, ki ta korak zaklene.

**Vzrok:** Pogosto kopiranje SST (ali podobnega) bloka: v Par1 ostane ključ prejšnjega sklopa (npr. `sst_4`), čeprav ta korak zaklene drug `zaklenipolja` (npr. `sst_9` / `sst_10`).

**Rešitev:** V Par1 vpišite **ključ tistega `zaklenipolja`, ki v Param1 navaja ta korak**, ali **parni ključ istega sklopa**. Primer: `sst_3` s Param2=`0` je enakovreden `sst_4` s Param2=`1`, če sta `sst_3` in `sst_4` par DA/NE.

---

#### `LOCK_CONDITION_P1_DUPLICATE` – Podvojen Par1 pri `aliobstajapogoj`

**Opis:** Isti Param1 pri `aliobstajapogoj` je uporabljen pri dveh različnih sklopih `zaklenipolja` na istem zavihku.

**Vzrok:** Kopiran blok zaklepanja, v katerem Par1 ni bil posodobljen na ključ novega `zaklenipolja`.

**Rešitev:** Vsak sklop `zaklenipolja` naj ima v Par1 pri `aliobstajapogoj` **svoj** ključ. Več vrstic v **istem** sklopu sme imeti enak Param1.

---

#### `SOLUTION_KEY_MISSING` – Kontrola raztopine brez ključa v vrstici

**Opis:** Vrstica z raztopino ima kontrolo `kontrolaveljavnostiraztopine` ali `kontrolaustreznostiraztopine`, a v vrstici manjka ključ preverjanja.

**Vzrok:** Stolpec `Ključ preverjanja` je prazen pri vrstici, ki vsebuje kontrolo raztopine.

**Rešitev:** Dodajte ključ preverjanja (npr. `GK1`) v stolpec `Ključ preverjanja` za to vrstico.

---

#### `CTRL_RAZTOPINA_NAVODILO_LABEL` – Navodilo ne vsebuje točne oznake raztopine

**Opis:** V stolpcu `Navodilo` pri vrstici z `kontrolaustreznostiraztopine` ni točne oznake raztopine, kot jo ima raztopina na nalepki.

**Vzrok:** Oznaka raztopine v `Navodilo` je drugačna od `Param1` pri `kontrolaustreznostiraztopine` (drugačno besedilo, velike/male črke, krajša ali daljša oznaka) ali pa je `Navodilo` prazno. Poljubno besedilo vodi do napak pri delu.

**Rešitev:** V `Navodilo` vpišite natančno oznako iz `Param1` (npr. `Koda 1M-NaOH-PL`).

---

## 5. Odgovornosti

| Vloga | Odgovornost |
|-------|-------------|
| **Tehnolog** | Pripravi recepturo po navodilih NAV-157; izvede validacijo z IPO validatorjem; pregleda vse javljene napake in za vsako presodi, ali gre za dejansko nepravilnost, ki jo je treba odpraviti. |
| **Vodja tehnologije** | Pregleda poročilo validacije; odobri recepturo pred vnosom v produkcijsko okolje. |
| **Skrbnik sistema IPO** | Vzdržuje in posodablja aplikacijo IPO Validator; zagotavlja delovanje v skladu s pravili. |

---

## 6. Dokumentacija

| Dokument | Opis |
|----------|------|
| Receptura `.xlsm` | Datoteka recepture, ki se validira |
| Poročilo validacije `.xlsx` | Izhod validatorja z vsemi napakami in opozorili |
| NAV-157 | Navodila za pripravo recepture za IPO sistem |

---

## 7. Zapisi o spremembah

| Izdaja | Opis spremembe | Datum |
|--------|----------------|-------|
| 1 | Prva izdaja dokumenta | 25. 3. 2026 |
| 2 | Odstranjene vsebine o SOP validaciji (poglavja 3.4, 3.8, 4.5); posodobljene kode napak v razdelku 4.2 na dejanske kode iz izvorne kode (`OBJECT_TYPE_UNKNOWN`, `KEY_INVALID_FORMAT` itd.); dodana napaka `SPACE_NOT_ALLOWED` | 25. 3. 2026 |
| 3 | Posodobljene vse kode napak v razdelkih 4.1, 4.3 in 4.4 iz slovenščine v angleščino (kode iz izvorne kode validatorja); dodane manjkajoče kode: `KEY_DUP_MASS`, `KEY_DUP_MASS_SECTION`, `CTRL_INVALID_CONTEXT`, `SOLUTION_KEY_MISSING` | 25. 3. 2026 |
| 4 | Posodobljeno besedilo o sprejemljivosti recepture: pripravljalec mora vsako napako validatorja individualno preveriti in presoditi; receptura je primerna za prenos v proizvodnjo tudi, če napaka ne odraža dejanske nepravilnosti. Usklajene definicije (razdelek 2), postopek (razdelek 3.3) in odgovornosti (razdelek 5). | 25. 3. 2026 |
| 5 | Odstranjena napaka `SOLUTION_P1_BASE`: Par1 pri kontrolah raztopine se ne preverja več proti ključu preverjanja | 1. 9. 2026 |
| 6 | Dodana napaka `DATA_TYPE_MASA_INVALID`: `Tip podatka` za maso sme biti samo `masa` (`masa1` ni veljaven) | 9. 9. 2026 |
| 7 | Par kemikalija/raztopina–masa: obvezen `masa` z istim ključem; `volumen` z istim ključem ni dovoljen (izjema `dH2O`) | 9. 9. 2026 |

---

## 8. Priloge, povezave in reference

### Priloga A – Hiter pregled najpogostejših napak

| Napaka | Pogost vzrok | Hitra rešitev |
|--------|--------------|---------------|
| `OBJECT_TYPE_UNKNOWN` | Tipkarska napaka v `Tip objekta` | Preverite črkovanje (male črke, brez presledkov) |
| `DATA_TYPE_MASA_INVALID` | `Tip podatka` je `masa1` namesto `masa` | Vpišite točno `masa`; številko dajte v ključ preverjanja |
| `OBJECT_TYPE_MISMATCH` | Napačen `Tip objekta` za ta `Tip podatka` | Glejte tabelo ujemanja v razdelku 4.2 |
| `LABEL_MUST_BE_KODA` | Napačna Labela | Nastavite `Labela = koda` za kemikalija, zaposleni, monolit |
| `KEY_INVALID_FORMAT` | Prepovedani znaki v ključu | Odstranite presledke, šumnike, posebne znake |
| `SPUSTNISEZNAM_VREDNOST_EMPTY` | Prazna `Vrednost` pri `spustniseznam` (npr. oprema) | Vpišite oznako šifranta (npr. `HPLC`, `tehtnica`) |
| `CRTA_STEP_EMPTY` | Ločnik `crta` brez številke koraka | V `št. Koraka` vpišite `=C_prej+1` (ali `1`) |
| `NASLOV_NAVODILO_EMPTY` | Naslov brez besedila | V `Navodilo` vpišite naslov razdelka |
| `COMMA_NOT_ALLOWED` | Vejica kot decimalno ločilo | Zamenjajte vejico s piko v numeričnih vrednostih |
| `SPACE_NOT_ALLOWED` | Presledek v vrednosti stolpca | Odstranite presledek (dovoljeno v `Navodilo`, `Labela`, `Vrednost` in `Ključ preverjanja`) |
| `NAVODILO_RANGE_DASH_SPACING` | Razpon v `Navodilo` brez presledkov ob pomišljaju (`4000–4400`) | Zapišite `4000 – 4400` (presledek pred in za pomišljajem) |
| `FORMULA_INVALID_REFERENCE` | Formula kaže na izbrisan korak | Preverite `$N` reference v formulah |
| `STEP_DUPLICATE` | Kopirana vrstica brez popravka | Preverite formule v stolpcu `št. Koraka` |
| `STEP_GAPS` | Izbrisana vrstica ali `crta` brez koraka | Zagotovite neprekinjeno zaporedje; `crta` mora imeti korak |
| `LOCK_P1_FORMAT` | Napačen Par1 pri `zaklenipolja` | Vnesite samo cela števila, ločena z vejicami: `45,46,47` |
| `LOCK_CONDITION_P1_LOCK_KEY` | Pri `aliobstajapogoj` je napačen ključ (npr. `sst_4` iz drugega sklopa) | V Par1 vpišite ključ sklopa, ki ta korak zaklene (`sst_3`/0 ali parni `sst_4`/1) |
| `LOCK_CONDITION_P1_DUPLICATE` | Isti Par1 pri `aliobstajapogoj` v dveh sklopih zaklepanja | Vsak sklop `zaklenipolja` mora imeti svoj ključ v Par1 |
| `PAIR_MASS_WITHOUT_OWNER` | Masa brez kemikalije/raztopine | Preverite ujemanje ključev med maso in lastnikom |
| `PAIR_CHEM_WITHOUT_MASS` / `PAIR_SOL_WITHOUT_MASS` | Kemikalija/raztopina brez mase | Dodajte vrstico `masa` z istim ključem |
| `PAIR_VOLUME_NOT_ALLOWED` | `volumen` z istim ključem kot raztopina | Spremenite v `masa` (razen `dH2O`) |

---

### Referenca: Navodila za pripravo recepture

Za podrobna navodila o pripravi Excel recepture (struktura listov, tipi podatkov, ključi, kontrole) glejte:

**NAV-157** – *Navodila za pripravo recepture za IPO sistem*

---

*Dokument je bil pripravljen na podlagi aplikacije IPO Validator in navodil NAV-157 za sistem Sartorius BIA Separations.*
