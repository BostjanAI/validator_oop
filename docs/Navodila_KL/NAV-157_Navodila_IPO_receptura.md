# Navodila za pripravo recepture za IPO sistem

**Dokument:** NAV-157  
**Naslov:** Navodila za pripravo recepture za IPO sistem  
**Verzija:** 1  
**Datum veljavnosti:** 19. 3. 2026  
**Področje:** Tehnologija / Kromatografija  

---

## KAZALO

1. [Namen, princip in področje uporabe](#1-namen-princip-in-področje-uporabe)
2. [Definicije in okrajšave](#2-definicije-in-okrajšave)
3. [Postopek](#3-postopek)
   - 3.1 [Struktura Excel datoteke](#31-struktura-excel-datoteke)
   - 3.2 [Variante zapisa recepture](#32-variante-zapisa-recepture)
   - 3.3 [List Podatki – parametri recepture](#33-list-podatki--parametri-recepture)
   - 3.4 [Obvezni stolpci](#34-obvezni-stolpci)
   - 3.5 [Številčenje korakov](#35-številčenje-korakov)
   - 3.6 [Tip objekta – dovoljene vrednosti](#36-tip-objekta--dovoljene-vrednosti)
   - 3.7 [Tip podatka – dovoljene vrednosti](#37-tip-podatka--dovoljene-vrednosti)
   - 3.8 [Ključ preverjanja](#38-ključ-preverjanja)
   - 3.9 [Vrednost](#39-vrednost)
   - 3.10 [Labela](#310-labela)
   - 3.11 [Kontrole](#311-kontrole)
   - 3.12 [Vloge operaterjev](#312-vloge-operaterjev)
   - 3.13 [Posebni tipi vrstic](#313-posebni-tipi-vrstic)
   - 3.14 [Excelove formule v poljih Navodilo in Vrednost](#314-excelove-formule-v-poljih-navodilo-in-vrednost)
   - 3.15 [Pravila za ključe kontrole raztopine](#315-pravila-za-ključe-kontrole-raztopine)
   - 3.16 [Korak po korak: dodajanje novega koraka](#316-korak-po-korak-dodajanje-novega-koraka)
   - 3.17 [Validacija recepture](#317-validacija-recepture)
4. [Odgovornosti](#4-odgovornosti)
5. [Dokumentacija](#5-dokumentacija)
6. [Zapisi o spremembah](#6-zapisi-o-spremembah)
7. [Priloge, povezave in reference](#7-priloge-povezave-in-reference)

> **Opomba:** V primeru težav, nerazumevanja ali nepredvidenih dogodkov se posvetujte z nadrejeno osebo.

---

## 1. Namen, princip in področje uporabe

### Namen

Ta dokument opisuje postopek priprave recepture za sistem IPO (Information Processing and Operation). Receptura je strukturirana Excel datoteka, ki sistemu IPO pove, kateri koraki morajo biti izvedeni, kateri podatki se zbirajo, katere kontrole se izvajajo in katera oprema se uporablja pri kromatografskem postopku.

### Princip

Receptura je Excel datoteka s končnico `.xlsm` (Excel z makri). Vsebuje natanko **štiri liste (zavihke)**:

| List | Namen |
|------|--------|
| `Spremembe` | Avtomatski dnevnik sprememb (tega se ne ureja ročno) |
| `Receptura` | Glavni list z vsemi koraki postopka **brez zavihkov** (en neprekinjen seznam) |
| `Receptura_2` | Alternativni list z vsemi koraki postopka **z zavihki** (koraki so ločeni po sklopih/zavihkih) |
| `Podatki` | Parametri za vsako velikost recepture (tehnični parametri) |

> **Pozor:** Lista `Spremembe` se posodablja samodejno z makri. Vanjo nikoli ne pišete ročno.

### Področje uporabe

Ta navodila so namenjena **tehnologom**, ki pripravljajo, vzdržujejo ali posodabljajo recepture za sistem IPO. Navodila pokrivajo oba načina zapisa recepture (z zavihki in brez) ter vse zahtevane stolpce, tipe podatkov, kontrole in pravila za veljavno strukturo.

---

## 2. Definicije in okrajšave

| Izraz / okrajšava | Razlaga |
|-------------------|---------|
| **IPO** | Informacijski sistem za vodenje kromatografskih postopkov |
| **Receptura** | Excel datoteka `.xlsm`, ki opisuje postopek za sistem IPO |
| **Validator** | Orodje (IPO Validator), ki preveri pravilnost strukture recepture |
| **Zavihek** | Ločen sklop korakov v recepturi (prikazuje se kot tab v sistemu IPO) |
| **Tip objekta** | Določa vrsto UI-elementa v sistemu IPO (npr. `edit`, `checkbox`, `spustniseznam`) |
| **Tip podatka** | Opisuje vrsto vsebine, ki se vnaša ali prikazuje (npr. `masa`, `raztopina`, `zaposleni`) |
| **Ključ preverjanja** | Unikatni identifikator koraka za sistem IPO (brez presledkov, šumnikov, posebnih znakov) |
| **Kontrola** | Pravilo preverjanja, ki ga sistem IPO izvaja ob vnosu (npr. `kontrolapraznopolje`, `kontrolainterval`) |
| **HPLC** | Tekočinska kromatografija visoke ločljivosti (oprema) |
| **SST** | Sistemski primernostni test (System Suitability Test) |
| **PM** | Pulzna motnja (tip kromatografskega postopka) |
| **IK** | Izočrtna kromatografija |
| **CV** | Kolumni volumen (Column Volume) |
| **TC** | Testni kromatogram |
| **TK** | Testni komplet |
| **xlsm** | Format Excel datoteke z makri |

---

## 3. Postopek

### 3.1 Struktura Excel datoteke

Datoteka recepture `.xlsm` mora vsebovati **natanko štiri liste** z naslednjimi imeni:

| List | Namen | Urejanje |
|------|--------|----------|
| `Spremembe` | Dnevnik sprememb | Samodejno (makri) – **ne urejati ročno** |
| `Receptura` | Koraki brez zavihkov | Ročno |
| `Receptura_2` | Koraki z zavihki | Ročno |
| `Podatki` | Tehnični parametri recepture | Ročno |

### 3.2 Variante zapisa recepture

Sistem IPO podpira dve varianti zapisa recepture. Izberete **eno ali drugo**, odvisno od tega, ali so koraki v sistemu razdeljeni po zavihkih ali ne.

#### 3.2.1 List `Receptura` – brez zavihkov

V tej varianti **stolpec `Zavihek` ostane prazen** v vseh vrsticah. Koraki tečejo **neprekinjeno od 1 naprej** skozi celoten postopek. V sistemu IPO bo vse prikazano kot en nepretrgan seznam brez ločenih zavihkov.

**Kdaj uporabiti:** Ko je postopek enostaven in ga ne delite v ločene sklope.

**Primer (`Receptura`):**

| Zavihek | šft. Koraka | Navodilo | Tip podatka | Ključ preverjanja | Tip objekta |
|---------|------------|----------|-------------|-------------------|-------------|
| *(prazno)* | 1 | `=INDEX(Podatki!...)` | *(prazno)* | *(prazno)* | naslov |
| *(prazno)* | `=C2+1` | Izpolni vodja | *(prazno)* | *(prazno)* | naslov |
| *(prazno)* | `=C3+1` | Vodja | zaposleni | *(prazno)* | koda |
| *(prazno)* | `=C4+1` | Dodatna navodila | dodatnanavodila | *(prazno)* | edit |
| *(prazno)* | `=C5+1` | *(prazno)* | *(prazno)* | *(prazno)* | crta |

> **Opomba:** V tej varianti se za logično organizacijo korakov v stolpcu `Ključ preverjanja` pogosto dodajajo skupinske kode (npr. `tk_1`, `pm1_1`, `locba_1`). To **ni** isti stolpec kot `Zavihek` – gre za ključ za validacijo, ne za prikaz zavihkov v sistemu IPO.

#### 3.2.2 List `Receptura_2` – z zavihki

V tej varianti so koraki **razdeljeni v ločene zavihke** (sklope). Vsak zavihek ima:
- Svojo **kodo** v stolpcu `Zavihek` (stolpec B)
- Lastno **številčenje korakov od 1 naprej**
- Začetno vrstico tipa `naslov`, ki označuje začetek novega zavihka

V sistemu IPO bo vsak sklop prikazan kot **ločen zavihek** (tab), med katerimi operater preklaplja.

**Kdaj uporabiti:** Ko je postopek razdeljen v jasno ločene sklope (npr. po palicah, po korakih postopka, po dnevih ...).

**Pravila za zavihke:**

*Začetek novega zavihka (prva vrstica sklopa):*

| Stolpec | Vrednost |
|---------|----------|
| `Zavihek` (stolpec B) | **nova koda zavihka** (npr. `monolito1`, `monolito2`) |
| `šft. Koraka` | `1` *(celo število, ne formula – vsak zavihek šteje od 1)* |
| `Navodilo` | Naslov zavihka (npr. „Zavihek za 1. palico") |
| `Tip objekta` | `naslov` |
| Vse kontrole | prazne |

*Naslednje vrstice znotraj istega zavihka:*

| Stolpec | Vrednost |
|---------|----------|
| `Zavihek` (stolpec B) | `=B_prejšnja_vrstica` *(formula, ne ročno vpisana vrednost)* |
| `šft. Koraka` | `=C_prejšnja_vrstica+1` |

**Primer (`Receptura_2`):**

| Zavihek | šft. Koraka | Navodilo | Tip objekta |
|---------|------------|----------|-------------|
| `monolito1` | `1` | Zavihek za 1. palico | naslov |
| `=B38` | `=C38+1` | Koda monolita | edit |
| `=B39` | `=C39+1` | Število odrezanih monolitov | edit |
| `=B40` | `=C40+1` | Končna višina monolitov ustreza | checkbox |
| `=B41` | `=C41+1` | Vizualni pregled monolitov izveden | checkbox |
| `=B42` | `=C42+1` | Monoliti enako obrnjeni | checkbox |
| `=B43` | `=C43+1` | *(prazno)* | crta |
| `=B44` | `=C44+1` | Posebnosti | memo |
| `monolito2` | `1` | Zavihek za 2. palico | naslov |
| `=B46` | `=C46+1` | Koda monolita | edit |

> **Pomembno:** Koda zavihka (npr. `monolito1`) se vpiše **samo enkrat** – v prvi vrstici tega zavihka. Vse naslednje vrstice tega zavihka imajo formulo `=B_prej`. S tem je zagotovljeno, da se koda samodejno prenese.

### 3.3 List `Podatki` – parametri recepture

List `Podatki` vsebuje vrstice za vsako posamezno **velikost recepture** (npr. R-A-4-TES-SDVB, R-A-8-TES-SDVB, R-A-80-TES-SDVB ...). Prva vrstica je glava s stolpci.

**Struktura stolpcev v listu `Podatki`:**

| Stolpec | Opis | Primer |
|---------|------|--------|
| A – `Receptura` | Enolična koda recepture | `R-A-800-TES-SDVB` |
| B – `V monolita (mL)` | Volumen monolita v mL | `800` |
| C – `Vzorec` | Opis vzorca | `0.08 ut% UR v MF1` |
| D – `Pretok (mL/min) PM` | Nominalni pretok za pulzno motnjo | `800` |
| E – `Odstopanje (mL/min)` | Dopustno odstopanje pretoka | `=ROUND(D*0.05,0)` |
| F – `Min. V` | Minimalni dovoljeni pretok | `=D-E-1` |
| G – `Max. V` | Maksimalni dovoljeni pretok | `=D+E+1` |
| H – `Pretok (mL/min) IK` | Pretok za izočrtno kromatografijo | (ali prazno) |
| I – `Odstopanje` | Odstopanje za IK pretok | (ali prazno) |
| J – `Pretok spiranje (mL/min)` | Obseg pretoka za spiranje | `700 - 900` |
| K – `Min. pretok` | Stroga spodnja meja pretoka spiranja | `699` |
| L – `Max. pretok` | Stroga zgornja meja pretoka spiranja | `901` |
| M – `V zanke [mL]` | Volumen zanke v mL | `1` |
| O – `5 CV` | 5-kratni kolumni volumen | `=B*5` |
| P – `Min.` | Minimalen volumen pri 5 CV | `=O-1` |
| S – `10 CV` | 10-kratni kolumni volumen | `=B*10` |
| T – `Min` | Minimalen volumen pri 10 CV | `=S-1` |
| W – `tSST (min)` | Čas za SST test | `0.01 - 0.30` |
| X – `Vr min` | Minimalni retencijski volumen | `680 - 920` |
| Y – `N >` | Minimalno število plošč | `30` |
| Z – `Pretok (mL/min) ETX` | Pretok ekstrakcije | `40` |
| AA–AC – `V, Min., Max.` | Volumen in meje za SST | `719, 8001` |
| AH – `V odpadne` | Volumen odpadne raztopine | `=B/2` |
| AI – `V vzorca mL` | Volumen vzorca v mL | `20` |
| AJ – `Max ε / max lΔp A,C` | Maks. pretok/tlak A,C | `1600 mL/min / ≤ 14 bar` |
| AK – `max lΔp (bar) ≤` | Maks. tlak | `14` |
| AN – `Min Vr` | Min. retencijski volumen (izračunan) | `679` |
| AO – `Max Vr` | Max. retencijski volumen (izračunan) | `921` |
| AP – `Vzorec` | Koda vzorca za lokacijo | `0.08 ut% UR v MF1` |
| AQ – `Ključ 1` | Ključ raztopine vzorca za PM | `0.08mp-UR_2.73mp-NaCl_13.87mp-EtOH-GK` |
| AR – `Vzorec za testni kromatogram` | Opis vzorca za TC | `0.08 ut% UR in 25.76 ut% 2B v MF1` |
| AS – `TC` | Koda tesnilnega kompleta | `TC-GASKET-12` |
| AT – `Ključ1` | Ključ raztopine za TC | `0.08mp-UR_25.76mp-2B_...` |
| AU – `Ključ2` | Drugi ključ za TC | `0.08mp-UR_2.73mp-NaCl_...` |
| AV – `Vinj TK` | Volumen injiciranja za TK | `1 mL` |
| AW – `Pretok TK (mL/min)` | Pretok za testni kromatogram | `40` |
| AX – `Odstopanje (mL/min)` | Odstopanje pretoka TK | `=AW*0.05` |
| AY – `Min. pretok` | Min. pretok TK | `=AW-AX-1` |
| AZ – `Max pretok` | Max. pretok TK | `=AW+AX+1` |
| BQ – `Min tSST` | Spodnja meja časa SST | `0.004` |
| BR – `Max tSST` | Zgornja meja časa SST | `0.305` |
| BS – `Formula (Vr)` | Formula za retencijski volumen | `formula0` ali `formula1` |

> **Opomba:** Vrednosti kot so `Min. pretok` (K), `Max. pretok` (L) itd. se izračunajo po formulah (npr. `=D-E-1`). Vrednosti kot `=ROUND(D*0.05,0)` je treba vnesti kot Excelove formule, ne kot besedilo.

### 3.4 Obvezni stolpci

Vsi spodnji stolpci **morajo biti prisotni** v glavi lista (1. vrstica):

| Stolpec | Ime stolpca | Opis |
|---------|-------------|------|
| A | *(skrit – koda recepture)* | Vsebuje kodo recepture ali je prazna |
| B | `Zavihek` | Koda zavihka (samo v `Receptura_2`); pri `Receptura` vedno prazno |
| C | `šft. Koraka` | Zaporedna številka koraka |
| D | `Navodilo` | Besedilo navodila ali Excelova formula |
| E | `Tip podatka` | Vrsta podatka, ki ga operater vpiše |
| F | `Ključ preverjanja` | Identifikator za validacijo |
| G | `Vrednost` | Privzeta vrednost ali formula |
| H | `Labela` | Enota ali oznaka (npr. `mL/min`, `koda`) |
| I | `Tip objekta` | Vrsta UI-elementa v sistemu IPO |
| J–L | `Kontrola 1`, `Kontrola 1 - par 1`, `Kontrola 1 - par 2` | Prva kontrola in njeni parametri |
| M–O | `Kontrola 2`, `Kontrola 2 - par 1`, `Kontrola 2 - par 2` | Druga kontrola in njeni parametri |
| P–R | `Kontrola 3`, `Kontrola 3 - par 1`, `Kontrola 3 - par 2` | Tretja kontrola in njeni parametri |
| S–U | `Kontrola 4`, `Kontrola 4 - par 1`, `Kontrola 4 - par 2` | Četrta kontrola in njeni parametri |

### 3.5 Številčenje korakov (`šft. Koraka`)

- **Brez zavihkov (`Receptura`):** Koraki se številčijo od 1 naprej **skozi celotno recepturo**. Nikoli se ne začnejo znova.
- **Z zavihki (`Receptura_2`):** Koraki se številčijo od 1 naprej **znotraj vsakega zavihka posebej**. Ko se začne nov zavihek, se številčenje ponastavi na `1`.
- Priporoča se uporaba Excelove formule: `=C_prej+1` (naslednja vrstica dobi vrednost prejšnje +1).
- Vsaka vrstica mora imeti **edinstveno številko** v svojem obsegu – podvojene in manjkajoče vrednosti niso dovoljene.
- Prazne ločilne vrstice (`crta`) **morajo imeti** svojo številko koraka.

### 3.6 Tip objekta – dovoljene vrednosti

`Tip objekta` določa, kateri UI-element bo prikazan operaterju v sistemu IPO.

| Vrednost | Opis | Kdaj uporabiti |
|----------|------|----------------|
| `naslov` | Naslov razdelka (krepko besedilo) | Za označitev začetka nove sekcije ali zavihka |
| `crta` | Vizualni ločnik (vodoravna črta) | Za ločevanje skupin korakov |
| `edit` | Vnosno polje (tekst ali število) | Za vnos izmerkov, kod, imen datotek |
| `spustniseznam` | Spustni seznam (dropdown) | Za izbiro opreme iz liste (HPLC, tehtnica ...) |
| `checkbox` | Polje za kljukico | Za potrjevanje DA/NE dejanj |
| `memo` | Večvrstično besedilno polje | Za poti do baz kromatogramov, daljša besedila |
| `izberidatumcas` | Izbirnik datuma in časa | Za začetke/konce operacij |
| `gumbdatumcas` | Gumb za vnos datuma in časa | Alternativa za izbiro datuma in časa |
| `formula` | Izračunano polje (splošna formula) | Kadar vrednost izhaja iz formule |
| `formula0` | Izračunano polje (brez decimalnih mest) | Za cela števila iz formule |
| `formula1` | Izračunano polje (1 decimalno mesto) | Za decimalna števila iz formule |
| `klictehtnice1` | Direktni klic tehtnice | Za avtomatski odčitek tehtnice |

> **Pozor:** Vrednosti so **občutljive na zapis** – pišite **točno** kot je navedeno (male črke, brez presledkov). `spustni seznam` ni veljavno – pravilno je `spustniseznam`.

### 3.7 Tip podatka – dovoljene vrednosti

`Tip podatka` opisuje **vrsto vsebine**, ki se vnaša ali prikazuje.

| Vrednost | Opis | Potrebna labela |
|----------|------|-----------------|
| `kemikalija` | Kemikalija (vnosna koda) | `koda` |
| `raztopina` | Raztopina (vnosna koda) | `koda` |
| `masa` | Masa/teža ali volumen | enota (npr. `mL`, `g`) |
| `embalaza` | Embalaža | `koda` |
| `zaposleni` | Zaposlen (operater/vodja) | `koda` |
| `monolit` | Monolit (koda sestavka) | `koda` |
| `tehtnica` | Tehtnica (oprema) | `naziv opreme` → `spustniseznam` |
| `termometer` | Termometer (oprema) | `naziv opreme` → `spustniseznam` |
| `kopel` | Vodna kopel (oprema) | `naziv opreme` → `spustniseznam` |
| `pH_meter` | pH meter (oprema) | `naziv opreme` → `spustniseznam` |
| `sušilnik` | Sušilnik (oprema) | `naziv opreme` → `spustniseznam` |
| `vak_sušilnik` | Vakuumski sušilnik (oprema) | `naziv opreme` → `spustniseznam` |
| `merilnik` | Merilnik (oprema) | `naziv opreme` → `spustniseznam` |
| `naprava` | Naprava (oprema) | `naziv opreme` → `spustniseznam` |
| `checkbox` | Polje za kljukico | `DA (kljukica)` ali `DA (kljukica)/NE (prazno)` |
| `datumcaszacetek` | Datum in čas začetka | `datum/čas` |
| `datumcaskonec` | Datum in čas konca | `datum/čas` |
| `datumcas` | Splošni datum in čas | `datum/čas` |
| `naslov` | Naslov sekcije | (prazno) |
| `crta` | Ločnik | (prazno) |
| `memo` | Dolgo besedilo/pot | (prazno) |
| `formula` | Izračunana vrednost | enota |
| `summasa` | Seštevek mas | enota |
| `masakonec` | Masa na koncu | enota |
| `repro` | Reprocesiranje | `koda` |
| `reproodpis` | Odpis pri reprocesiranju | `koda` |
| `monomerna` | Monomerna kolona | (kot oprema) |

> **Opomba:** Vrednosti, ki zahtevajo labelo `koda`, so: `kemikalija`, `zaposleni`, `monolit`, `repro`, `reproodpis`.

### 3.8 Ključ preverjanja (`Ključ preverjanja`)

- Vsak korak, ki zbira podatke, **mora imeti ključ preverjanja** (razen `naslov`, `crta` in `checkbox` brez obveznega vnosa).
- Ključ je **identifikator** tega koraka za sistem IPO.
- **Dovoljeni znaki:** samo `A-Z`, `a-z`, `0-9`, `-`, `_`, `.` – brez presledkov, šumnikov ali posebnih znakov.
- Primeri veljavnih ključev: `pretok_mf1`, `tehtnica_1`, `2.73mp-NaCl_13.87mp-EtOH-GK`, `locba_1`
- **Podvojevanje ključev:** Isti tip podatka ne sme imeti enakih ključev v istem zavihku. Numerično pripono (npr. `GK1`, `GK2`) je treba povečevati.
- Za raztopino se ključ preverjanja ujema z **oznako raztopine** v sistemu IPO.

### 3.9 Vrednost (`Vrednost`)

- Vsebuje privzeto vrednost polja ali Excelovo formulo.
- Za **raztopino ali kemikalijo**: koda raztopine (npr. `2.73mp-NaCl_13.87mp-EtOH-GK`).
- Za **opremo**: koda tipa opreme (npr. `HPLC`, `TEH-KLA`, `TERM`).
- Za **checkbox**: prazno ali `DA`.
- Za **izračunana polja** (`formula0`, `formula1`): Excelova formula, npr.:
  `="=($"&C100&"+"&"$"&C99&")"` – formula, ki se sklicuje na koraka 100 in 99.
- Vrednost je **neobvezna** za `naslov`, `crta`, polja brez privzete vrednosti.

### 3.10 Labela (`Labela`)

Labela je oznaka enote ali tipa prikaza, ki se pokaže operaterju.

| Primer labele | Kdaj |
|---------------|------|
| `koda` | Za kemikalije, raztopine, zaposlene, monolit |
| `naziv opreme` | Za opremo (tehtnica, termometer, HPLC ...) |
| `mL/min` | Za pretoke |
| `bar` | Za tlak |
| `mL` | Za volumne |
| `min` | Za čase v minutah |
| `°C` | Za temperature |
| `DA (kljukica)` | Za checkbox (obvezan DA) |
| `DA (kljukica)/NE (prazno)` | Za checkbox (DA ali NE) |
| `datum/čas` | Za polja z datumom/časom |
| (prazno) | Za `naslov`, `crta`, nekatera `edit` polja |

### 3.11 Kontrole (`Kontrola 1` do `Kontrola 4`)

Vsak korak ima lahko **do 4 kontrole**. Vsaka kontrola ima:
- **ime kontrole** (stolpec `Kontrola N`)
- **parameter 1** (stolpec `Kontrola N - par 1`)
- **parameter 2** (stolpec `Kontrola N - par 2`)

#### 3.11.1 Seznam veljavnih kontrol

| Ime kontrole | Opis | Par 1 | Par 2 |
|-------------|------|-------|-------|
| `kontrolapraznopolje` | Polje ne sme biti prazno | (prazno) | (prazno) |
| `kontrolainterval` | Vrednost mora biti v intervalu [min, max] | spodnja meja | zgornja meja |
| `kontrolacasa` | Trajanje mora biti v intervalu (v sekundah) | min sekunde | max sekunde |
| `aliobkljukan` | Checkbox mora biti označen z določeno vrednostjo | `DA` ali `NE` | (prazno) |
| `aliniobkljukan` | Checkbox ne sme biti označen | `DA` ali `NE` | (prazno) |
| `aliobstajapogoj` | Polje je aktivno samo, če pogoj drži | ključ koraka (npr. `odrez1`) ali celica (npr. `=$F$58`) | `0` ali `1` |
| `aliobstajapogoj_ali` | Pogoj z ALI logiko | referenca | `0` ali `1` |
| `alipravavloga` | Preverja, ali ima operater ustrezno vlogo | ime vloge | (prazno) |
| `alipravavlogakoda` | Preverja vlogo na podlagi kode | ime vloge | (prazno) |
| `kdoizpolni` | Določa, kdo sme izpolniti polje | ime vloge | (prazno) |
| `zaklenipolja` | Zaklene naštete korake, če je polje označeno | seznam korakov (ločenih z vejicami) | (prazno) |
| `aliisto` | Vrednost mora biti enaka vrednosti drugega koraka | referenca na korak (npr. `=C13`) | (prazno) |
| `kontrolaveljavnostiopreme` | Oprema mora biti veljavna (kalibrirana) | tip opreme (npr. `HPLC`, `tehtnica`) | (prazno) |
| `kontrolaustreznostiopreme` | Oprema mora biti primerna za postopek | tip opreme | (prazno) |
| `kontrolaveljavnostiraztopine` | Raztopina mora biti veljavna (v roku) | baza ključa raztopine | (prazno) |
| `kontrolaustreznostiraztopine` | Raztopina mora biti ustrezna | baza ključa raztopine | (prazno) |
| `kontrolaveljavnostimonolita` | Monolit mora biti veljaven | (prazno) | (prazno) |
| `kontrolaustreznostimonolita` | Monolit mora biti ustrezen za serijo | koda tipa(ov), npr. `SES` ali `MOD,SPIR` | (prazno) |
| `kontrolaveljavnostikemikalije` | Kemikalija mora biti veljavna | (prazno) | (prazno) |
| `kontrolaustreznostikemikalije` | Kemikalija mora biti ustrezna | (prazno) | (prazno) |
| `kontrolamase` | Masa mora biti pravilna | (skupaj z `kontrolainterval`) | (prazno) |
| `kontrolaembalaze` | Embalaža mora biti veljavna | (prazno) | (prazno) |
| `kontrolarazlika` | Razlika med vrednostmi mora biti v mejah | (prazno) | (prazno) |

#### 3.11.2 Najpogostejše kombinacije kontrol

**Obvezno vnosno polje (edit):**
```
Kontrola 1: kontrolapraznopolje
```

**Numerična vrednost z mejami:**
```
Kontrola 1: kontrolainterval  |  Par 1: spodnja meja  |  Par 2: zgornja meja
Kontrola 2: kontrolapraznopolje
```

**Raztopina:**
```
Kontrola 1: kontrolaveljavnostiraztopine  |  Par 1: baza_kljuca_raztopine
Kontrola 2: kontrolaustreznostiraztopine  |  Par 1: baza_kljuca_raztopine
Kontrola 3: kontrolapraznopolje
```

**Oprema (HPLC, tehtnica, termometer ...):**
```
Kontrola 1: kontrolaveljavnostiopreme  |  Par 1: HPLC
Kontrola 2: kontrolaustreznostiopreme  |  Par 1: HPLC
Kontrola 3: kontrolapraznopolje
```

**Monolit:**
```
Kontrola 1: kontrolaustreznostimonolita  |  Par 1: MOD,SPIR   (ali koda svojega tipa)
Kontrola 2: kontrolaveljavnostimonolita
Kontrola 3: kontrolapraznopolje
```

**Kemikalija:**
```
Kontrola 1: kontrolaveljavnostikemikalije
Kontrola 2: kontrolaustreznostikemikalije
Kontrola 3: kontrolapraznopolje
```

**Checkbox (obvezan DA):**
```
Kontrola 1: aliobkljukan  |  Par 1: DA
```

**Datum/čas začetek–konec:**
```
Začetek – Kontrola 1: kontrolapraznopolje
Konec   – Kontrola 1: kontrolacasa  |  Par 1: min_sekunde  |  Par 2: max_sekunde
           Kontrola 2: kontrolapraznopolje
```

**Zakleni polja (pogojno zaklepanje):**
```
Checkbox korak – Kontrola 1: zaklenipolja  |  Par 1: 45,46,47,48 (seznam šft. korakov)
```
> Ko je checkbox označen (DA), se našteti koraki zaklenejo. Par 1 je **seznam celih števil**, ločenih z vejicami – brez presledkov.

**Zaklepanje z Excelovo formulo (dinamičen seznam):**
```
Par 1: =C58&","&C60&","&C61&","&C63   (formula, ki zbere številke korakov)
```

**Pogojno polje – aktivno samo pod pogojem:**

*Varianta 1 – referenca na ključ preverjanja (string):*
```
Kontrola 1: aliobstajapogoj  |  Par 1: odrez1  |  Par 2: 1
```
> Korak je obvezen samo, kadar je korak z ključem `odrez1` označen/izpolnjen.

*Varianta 2 – referenca na celico (Excel formula):*
```
Kontrola 1: aliobstajapogoj  |  Par 1: =$F$58  |  Par 2: 1
```
> Korak je obvezen samo, kadar vrednost celice F58 enaka 1.

### 3.12 Vloge operaterjev

V kontrolah `alipravavlogakoda` in `kdoizpolni` se navede ime vloge iz sistema:

| Koda vloge | Opis |
|------------|------|
| `ROLE_HEAD` | Vodja (šef izmene) |
| `ROLE_OPERATOR` | Operater |

### 3.13 Posebni tipi vrstic

#### 3.13.1 Naslov razdelka / začetek zavihka (`naslov`)

```
Zavihek:      nova koda zavihka (pri Receptura_2) ali prazno (pri Receptura)
Navodilo:     Besedilo naslova
Tip podatka:  (prazno)
Tip objekta:  naslov
Vse kontrole: (prazne)
```

#### 3.13.2 Ločnik (`crta`)

```
Zavihek:      =B_prejšnja (ali prazno)
Navodilo:     (prazno)
Tip podatka:  (prazno)
Tip objekta:  crta
Vse kontrole: (prazne)
```

#### 3.13.3 Checkbox

```
Navodilo:    Besedilo potrditve (ali Excelova formula)
Tip podatka: checkbox
Labela:      DA (kljukica)   ALI   DA (kljukica)/NE (prazno)
Tip objekta: checkbox
Kontrola 1:  aliobkljukan  |  Par 1: DA
```

#### 3.13.4 Spustni seznam (oprema)

```
Navodilo:    "HPLC"
Tip podatka: HPLC  (ali tehtnica, termometer ...)
Vrednost:    koda_tipa (npr. HPLC, TEH-KLA, TERM)
Labela:      naziv opreme
Tip objekta: spustniseznam
Kontrola 1:  kontrolaveljavnostiopreme  |  Par 1: HPLC
Kontrola 2:  kontrolaustreznostiopreme  |  Par 1: HPLC
Kontrola 3:  kontrolapraznopolje
```

#### 3.13.5 Datum/čas

```
Tip podatka: datumcaszacetek  ALI  datumcaskonec  ALI  datumcas
Labela:      datum/čas
Tip objekta: izberidatumcas  ALI  gumbdatumcas
```

Za `datumcaskonec` mora biti kontrola časa:
```
Kontrola 1:  kontrolacasa  |  Par 1: min_sek  |  Par 2: max_sek
Kontrola 2:  kontrolapraznopolje
```

#### 3.13.6 Formula

```
Tip podatka: formula  ALI  summasa
Tip objekta: formula0  (za cela števila)  ALI  formula1  (za 1 decimalno mesto)
Vrednost:    Excelova formula z referencami na korake
```

Primer vrednosti formule:
```
="=($"&C113&"-"&"$"&C108&")/($"&C108&"-$"&C89&")"
```
To pomeni, da sistem IPO izračuna `(korak113 - korak108) / (korak108 - korak89)`.

### 3.14 Excelove formule v poljih `Navodilo` in `Vrednost`

Excelove formule se pogosto berejo parametre iz lista `Podatki`. Tipična formula:
```excel
=INDEX(Podatki!$A:$BZ, MATCH($A$2, Podatki!$A:$A, 0), 4)
```
- `$A$2` vsebuje kodo recepture (npr. `R-A-800-TES-SDVB`)
- `MATCH(...)` najde vrstico v `Podatki`
- Četrti argument `4` je stolpec D (pretok)

To omogoča, da se isto navodilo prilagodi za vsako velikost recepture – **ne pisati ročno vrednosti v navodila**.

### 3.15 Pravila za ključe kontrole raztopine

Ko je `Tip podatka` = `raztopina`:
- `Ključ preverjanja` je **unikatna koda** (npr. `2.73mp-NaCl_13.87mp-EtOH-GK1`)
- V kontroli `kontrolaveljavnostiraztopine` je **Par 1 = baza ključa brez numerične pripone** (npr. `2.73mp-NaCl_13.87mp-EtOH-GK`)
- To pomeni: če imate 3 enake raztopine z ključi `GK1`, `GK2`, `GK3` – vse tri imajo isto Par 1 = `GK` (brez številke)

### 3.16 Korak po korak: dodajanje novega koraka

1. **Odločite se za varianto** – ali lista `Receptura` (brez zavihkov) ali `Receptura_2` (z zavihki).
2. **Če z zavihki:** preverite, ali ste v pravilnem zavihku (stolpec B mora imeti pravo kodo ali formulo `=B_prej`).
3. **Nastavite številko koraka** – formula `=C_prejšnja+1`; pri novem zavihku napišite `1`.
4. **Vpišite navodilo** – besedilo ali Excelova formula.
5. **Izberite Tip podatka** – glejte razdelek 3.7.
6. **Določite Ključ preverjanja** – unikaten identifikator brez presledkov.
7. **Vpišite Vrednost** – koda opreme, raztopine ali formula.
8. **Nastavite Labelo** – enota ali oznaka prikaza.
9. **Izberite Tip objekta** – ustreza tipu podatka (glejte razdelek 3.6).
10. **Dodajte kontrole** – glede na tip podatka (glejte razdelek 3.11).
11. **Shranite in zaženite validator** – preverite, da ni napak.

### 3.17 Validacija recepture

Po dokončani pripravi recepture je treba datoteko **validirati z IPO validatorjem**:

1. Odprite aplikacijo IPO Validator.
2. Naložite datoteko `.xlsm`.
3. Preverite poročilo napak.
4. Odpravite vse napake tipa **error** (napake vrste **warning** so opozorila, ne blokirajo).
5. Ponovite validacijo do `"is_valid": true`.

---

## 4. Odgovornosti

| Vloga | Odgovornost |
|-------|-------------|
| **Tehnolog** | Pripravi recepturo v skladu s temi navodili; izvede validacijo z IPO validatorjem; zagotovi, da je receptura brez napak tipa *error* pred oddajo. |
| **Vodja tehnologije** | Pregleda in odobri recepturo pred vnosom v produkcijsko okolje; odgovoren za pravilnost tehničnih parametrov v listu `Podatki`. |
| **Skrbnik sistema IPO** | Vzdržuje IPO Validator; zagotavlja delovanje makrov v predlogi `.xlsm`. |

---

## 5. Dokumentacija

| Dokument | Opis |
|----------|------|
| Receptura `.xlsm` | Datoteka recepture, pripravljena po teh navodilih |
| IPO Validator – poročilo | Izhod validatorja po preverjanju recepture |
| List `Spremembe` v `.xlsm` | Samodejni dnevnik sprememb recepture (generiran z makri) |

---

## 6. Zapisi o spremembah

| Izdaja | Opis spremembe | Datum |
|--------|----------------|-------|
| 1 | Prva izdaja dokumenta | 19. 3. 2026 |

---

## 7. Priloge, povezave in reference

### Priloga A – Tipične napake in kako jih odpraviti

Kode napak so prikazane točno tako, kot se pojavijo v stolpcu **Napaka** v poročilu validatorja.

**Strukturne napake**

| Koda napake | Vzrok | Rešitev |
|-------------|-------|---------|
| `MISSING_COLUMN` | Manjka obvezen stolpec v glavi lista | Preverite, da so vsi obvezni stolpci prisotni in pravilno poimenovani |
| `STEP_NOT_INTEGER` | Vrednost v `šft. Koraka` ni celo število | Preverite, da formula vrača celo število (ne `1.0`, temveč `1`) |
| `STEP_MISSING` | Vrstica nima številke koraka | Dodajte formulo `=C_prej+1` v stolpec `šft. Koraka` |
| `STEP_DUPLICATE` | Dve vrstici imata isto `šft. Koraka` | Preverite formule; pri zavihkih se vsak zavihek začne z `1` |
| `STEP_TAB_NOT_FROM_ONE` | Zavihek v `Receptura_2` se ne začne s korakom 1 | V prvi vrstici zavihka vpišite vrednost `1` (ne formulo) |
| `STEP_GAPS` | Vrzel v zaporedju korakov | Vrstice `crta` morajo imeti svojo številko koraka; preverite zaporedje |

**Napake polj**

| Koda napake | Vzrok | Rešitev |
|-------------|-------|---------|
| `OBJECT_TYPE_EMPTY` | Stolpec `Tip objekta` je prazen | Vpišite ustrezno vrednost (npr. `edit`, `checkbox`, `naslov`) |
| `OBJECT_TYPE_UNKNOWN` | Napačno zapisana vrednost v `Tip objekta` | Preverite črkovanje (npr. `spustniseznam`, ne `spustni seznam`) |
| `OBJECT_TYPE_MISMATCH` | `Tip objekta` ni ustrezen za dani `Tip podatka` | Preverite tabelo ujemanja v razdelku 3.6 |
| `LABEL_MUST_BE_KODA` | Za `zaposleni`/`kemikalija`/`monolit` labela ni `koda` | Nastavite `Labela` = `koda` |
| `LABEL_CHECKBOX_FORMAT` | Napačna vrednost Labele pri checkboxu | Nastavite `DA (kljukica)` ali `DA (kljukica)/NE (prazno)` |
| `KEY_INVALID_FORMAT` | Ključ vsebuje prepovedane znake | Odstranite presledke, šumnike, posebne znake |
| `KEY_REQUIRED` | Manjka ključ pri tipu `kemikalija`/`raztopina`/`masa`/`tehtnica` | Dodajte unikaten ključ preverjanja |
| `FORMULA_SYNTAX` | Formula v `Vrednost` se ne začne z `=` | Vrednost mora biti Excelova formula, ki se začne z `=` |
| `FORMULA_NO_REFERENCE` | Formula ne vsebuje sklica `$N` na korak | Dodajte sklice na korake v obliki `"$"&C113` |
| `FORMULA_INVALID_REFERENCE` | Formula se sklicuje na neobstoječ korak | Preverite `$N` reference – korak mora obstajati |
| `FORMULA_STEP_INVALID_TYPE` | Sklicani korak nima dovoljenega `Tip objekta` | Sklici so dovoljeni le na `edit`, `formula`, `formula0`, `formula1` |
| `COMMA_NOT_ALLOWED` | Vejica kot decimalno ločilo v številki | Zamenjajte vejico s piko (razen v `Navodilo` in `zaklenipolja`) |
| `SPACE_NOT_ALLOWED` | Presledek v vrednosti stolpca | Odstranite presledek (dovoljeno le v `Navodilo` in `Labela`) |
| `UNIT_MISMATCH` | Enota v `Labela` se ne ujema z enoto v `Navodilo` | Uskladite enoti – morata biti enaki |

**Relacijske napake**

| Koda napake | Vzrok | Rešitev |
|-------------|-------|---------|
| `KEY_DUP_CHEM` | Podvojen ključ pri kemikaliji | Vsaka kemikalija mora imeti unikaten ključ (npr. `NaCl1`, `NaCl2`) |
| `KEY_DUP_SOL` | Podvojen ključ pri raztopini | Vsaka raztopina mora imeti unikaten ključ |
| `KEY_DUP_MASS_SECTION` | Isti ključ mase v več razdelkih | Masa z istim ključem je dovoljena le znotraj enega razdelka |
| `PAIR_MASS_WITHOUT_OWNER` | Masa nima ustrezne kemikalije/raztopine | Preverite ujemanje ključev med maso in lastnikom |
| `PAIR_MASS_SECTION_MISMATCH` | Masa je v napačnem razdelku glede na lastnika | Masa mora slediti svoji kemikaliji/raztopini v istem razdelku |
| `PAIR_TIME_WITHOUT_END` | Začetni čas brez ustreznega končnega | Dodajte `datumcaskonec` z enakim ključem |
| `PAIR_TIME_WITHOUT_START` | Končni čas brez ustreznega začetnega | Dodajte `datumcaszacetek` z enakim ključem |
| `KEY_NUM_NOT_FROM_ONE` | Oštevilčenje ključev se ne začne z 1 | Prva raztopina/kemikalija mora imeti ključ s pripono `1` |
| `KEY_NUM_GAP` | Vrzel v oštevilčenju ključev | Zaporedje mora biti neprekinjeno (1, 2, 3 …) |
| `SCALE_VALUE_TOO_HIGH` | Masa previsoka za izbrani razred tehtnice | Za maso ≥ 10 g uporabite `TEH-KLA` |
| `SCALE_VALUE_TOO_LOW` | Masa prenizka za izbrani razred tehtnice | Za maso < 10 g uporabite `TEH-ANA` |

**Napake kontrol**

| Koda napake | Vzrok | Rešitev |
|-------------|-------|---------|
| `CTRL_UNKNOWN` | Napačno ime kontrole | Preverite črkovanje; ime mora biti iz seznama veljavnih kontrol |
| `CTRL_INVALID_CONTEXT` | Kontrola ni dovoljena v tem kontekstu | Preverite, ali je kontrola primerna za ta `Tip podatka`/`Tip objekta` |
| `CTRL_REQUIRED_EMPTY` | Manjka `kontrolapraznopolje` pri vnosnem polju | Dodajte `kontrolapraznopolje` (obvezno za `edit`, `spustniseznam`, `memo` ...) |
| `CTRL_CHECKBOX_EMPTY` | Checkbox ima nedovoljeno `kontrolapraznopolje` | Odstranite `kontrolapraznopolje`; pri checkboxu uporabite `aliobkljukan` |
| `CTRL_EXPECTED_MISSING` | Manjka pričakovana kontrola | Dodajte zahtevano kontrolo (npr. `kontrolaveljavnostiraztopine`) |
| `CTRL_INTERVAL_PARAMS` | Pri `kontrolainterval` manjkajo Par 1 ali Par 2 | Vedno vnesite obe meji (spodnjo in zgornjo) |
| `CTRL_INTERVAL_NOT_NUMBER` | Meja intervala ni numerična vrednost | Preverite, da formula v Par1/Par2 vrača število |
| `CTRL_INTERVAL_RANGE` | Zgornja meja ≤ spodnja meja | Preverite vrstni red – Par2 mora biti večji od Par1 |
| `CTRL_INTERVAL_REQUIRED` | Manjka `kontrolainterval`, čeprav navodilo vsebuje interval | Dodajte `kontrolainterval` s pravilnimi mejami |
| `CTRL_CASA_REQUIRED` | Manjka `kontrolacasa` pri tipu `datumcaskonec` | Dodajte `kontrolacasa` s Par1 = min sekunde, Par2 = max sekunde |
| `CTRL_CASA_MIN` | Manjka minimalni čas pri `kontrolacasa` | Vnesite minimalni čas v sekundah v Par1 |
| `CTRL_ALIOBKLJUKAN_REQUIRED` | Manjka `aliobkljukan` pri checkboxu z `DA (kljukica)` | Dodajte `aliobkljukan` s Par1 = `DA` |
| `CTRL_ALIPRAVAVLOGAKODA_REQUIRED` | Manjka `alipravavlogakoda` pri tipu `zaposleni` | Dodajte `alipravavlogakoda` s Par1 = ime vloge |
| `CTRL_MONOLIT_VALIDITY_REQUIRED` | Manjka `kontrolaveljavnostimonolita` | Dodajte kontrolo veljavnosti monolita |
| `CTRL_MONOLIT_SUITABILITY_REQUIRED` | Manjka `kontrolaustreznostimonolita` | Dodajte kontrolo ustreznosti monolita s Par1 = koda tipa |
| `LOCK_P1_FORMAT` | Par 1 pri `zaklenipolja` ni seznam celih števil | Vnesite npr. `45,46,47` – samo številke, ločene z vejicami |
| `LOCK_P1_STEP_MISSING` | Korak v Par1 pri `zaklenipolja` ne obstaja | Preverite, da navedeni koraki obstajajo v listu |
| `LOCK_P1_WITHOUT_CONDITION` | Korak v Par1 nima `aliobstajapogoj` | Vsak korak v Par1 mora imeti kontrolo `aliobstajapogoj` |
| `SOLUTION_KEY_MISSING` | Kontrola raztopine brez ključa v vrstici | Dodajte ključ preverjanja pri vrstici raztopine |
| `SOLUTION_P1_BASE` | Par1 pri kontroli raztopine ne ustreza bazi ključa | Par1 mora biti ključ brez numerične pripone (npr. `GK`, ne `GK1`) |

### Priloga B – Primeri

#### Primer 1 – Meritev pretoka (brez zavihkov)

| Stolpec | Vrednost |
|---------|----------|
| Zavihek | *(prazno)* |
| šft. Koraka | `=C_prej+1` |
| Navodilo | `="Dejanski pretok MF1 ("&INDEX(Podatki!...,53)&" ± "&INDEX(...)&" mL/min)"` |
| Tip podatka | `dejanski_pretok` |
| Ključ preverjanja | `pretok_s_locba_1` |
| Vrednost | (prazno) |
| Labela | `mL/min` |
| Tip objekta | `edit` |
| Kontrola 1 | `kontrolainterval` |
| Kontrola 1 - par 1 | `=INDEX(Podatki!...,53)-INDEX(Podatki!...,54)-0.1` |
| Kontrola 1 - par 2 | `=INDEX(Podatki!...,53)+INDEX(Podatki!...,54)+0.1` |
| Kontrola 2 | `kontrolapraznopolje` |

#### Primer 2 – Začetek novega zavihka (`Receptura_2`)

| Stolpec | Vrednost |
|---------|----------|
| Zavihek | `monolito1` |
| šft. Koraka | `1` |
| Navodilo | `Zavihek za 1. palico` |
| Tip podatka | (prazno) |
| Ključ preverjanja | (prazno) |
| Vrednost | (prazno) |
| Labela | (prazno) |
| Tip objekta | `naslov` |
| Kontrole | (vse prazne) |

#### Primer 3 – Koda monolita (`Receptura_2`, znotraj zavihka)

| Stolpec | Vrednost |
|---------|----------|
| Zavihek | `=B_prej` |
| šft. Koraka | `=C_prej+1` |
| Navodilo | `Koda monolita` |
| Tip podatka | `monolit` |
| Ključ preverjanja | (prazno) |
| Vrednost | (prazno) |
| Labela | `koda` |
| Tip objekta | `edit` |
| Kontrola 1 | `kontrolaustreznostimonolita` |
| Kontrola 1 - par 1 | `MOD,SPIR` |
| Kontrola 2 | `kontrolaveljavnostimonolita` |
| Kontrola 3 | `kontrolapraznopolje` |

#### Primer 4 – SST checkbox z zaklepanjem (dinamičen seznam)

| Stolpec | Vrednost |
|---------|----------|
| Tip podatka | `checkbox` |
| Labela | `DA (kljukica)/NE (prazno)` |
| Tip objekta | `checkbox` |
| Kontrola 1 | `zaklenipolja` |
| Kontrola 1 - par 1 | `=C58&","&C60&","&C61&","&C63&","&C64&","&C65` |
| Kontrola 2 | (prazno) |

#### Primer 5 – Pogojno polje z ključem (`Receptura_2`)

| Stolpec | Vrednost |
|---------|----------|
| Navodilo | `Končni odrez za ostale kemije: 4.7 - 4.9 mm` |
| Tip podatka | `odrez1` |
| Ključ preverjanja | (prazno) |
| Labela | `mm` |
| Tip objekta | `edit` |
| Kontrola 1 | `aliobstajapogoj` |
| Kontrola 1 - par 1 | `odrez1` |
| Kontrola 1 - par 2 | `1` |
| Kontrola 2 | `kontrolainterval` |
| Kontrola 2 - par 1 | `4.6` |
| Kontrola 2 - par 2 | `5` |
| Kontrola 3 | `kontrolapraznopolje` |

### Reference

- IPO Validator – dokumentacija sistema
- Vzorčne recepture `Receptura.xlsm` (listi `Receptura` in `Receptura_2`)
