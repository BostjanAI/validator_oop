# Navodila za pripravo Excel recepture za IPO sistem (KL)

**Dokument:** NAV-157 – praktičen izvod za laboratorij KL
**Naslov:** Navodila za pripravo Excel recepture za sistem IPO
**Namenjeno:** Tehnologi v laboratoriju KL (priprava in vzdrževanje receptur)
**Vir:** NAV-157 v1, Kratka navodila KL IPO, vzorčna `Receptura.xlsm`
**Datum veljavnosti:** 20. 4. 2026

---

## Kazalo

1. [Uvod](#1-uvod)
2. [Struktura recepturne datoteke (štirje listi)](#2-struktura-recepturne-datoteke-štirje-listi)
3. [Dve varianti recepture: `Receptura` vs `Receptura_2`](#3-dve-varianti-recepture-receptura-vs-receptura_2)
4. [List `Podatki` in formule `INDEX/MATCH`](#4-list-podatki-in-formule-indexmatch)
5. [Obvezni stolpci](#5-obvezni-stolpci)
6. [Vrednosti polja `Tip objekta`](#6-vrednosti-polja-tip-objekta)
7. [Vrednosti polja `Tip podatka`](#7-vrednosti-polja-tip-podatka)
8. [Ključ preverjanja](#8-ključ-preverjanja)
9. [Kontrole](#9-kontrole)
10. [Vloge operaterjev (`ROLE_HEAD`, `ROLE_OPERATOR`)](#10-vloge-operaterjev-role_head-role_operator)
11. [Posebni tipi vrstic](#11-posebni-tipi-vrstic)
12. [Korak po korak: dodajanje novega koraka](#12-korak-po-korak-dodajanje-novega-koraka)
13. [Tipične napake in rešitve](#13-tipične-napake-in-rešitve)
14. [Validacija recepture](#14-validacija-recepture)

> **Pozor:** Vse vrednosti v recepturi so **občutljive na zapis** – pišite **točno male črke brez presledkov in brez šumnikov** (npr. `spustniseznam` in ne `spustni seznam` ali `Spustniseznam`). Izjema: stolpca `Navodilo` in `Labela`, kjer so presledki in šumniki dovoljeni.

---

## 1. Uvod

### Namen dokumenta

Dokument opisuje, kako se pripravi Excel receptura (`.xlsm`) za sistem **IPO** (informacijski sistem za vodenje kromatografskih postopkov). Navodila so praktična in pokrivajo vsak stolpec, vsako vrednost ter vsako kontrolo, ki se uporablja pri rednem delu v KL.

### Za koga so navodila

Navodila so namenjena **tehnologom v laboratoriju KL**, ki pripravljajo nove recepture ali posodabljajo obstoječe (testiranje, GMP, razvoj). Navodila predpostavljajo osnovno znanje Excela (vnos formul, `INDEX/MATCH`, reference celic).

### Vloga recepture v sistemu IPO

Receptura je **izvorna definicija postopka** za sistem IPO. Vsak korak v Excelu postane en vnosno polje, spustni seznam, checkbox ali naslov v IPO vmesniku, ki ga operater izpolnjuje. Kontrole v recepturi preprečijo napačne vnose že med delom (npr. vrednost izven intervala, napačna oprema, neveljavna raztopina). Receptura je tako hkrati **navodilo operaterju** in **samodejni kontrolni mehanizem**.

Preden gre receptura v proizvodnjo, mora biti uspešno pregledana z aplikacijo **IPO Validator** (glejte razdelek 14).

---

## 2. Struktura recepturne datoteke (štirje listi)

Vsaka recepturna datoteka ima točno **štiri liste (zavihke)** v tem vrstnem redu:

| List | Namen | Ali se ureja ročno? |
|------|-------|---------------------|
| `Spremembe` | Avtomatski dnevnik sprememb v datoteki (datum, zavihek, celica, stara/nova vrednost, uporabnik). | **NE** – polni ga makro. |
| `Receptura` | Glavni list postopka **brez zavihkov** (en neprekinjen seznam korakov). | DA |
| `Receptura_2` | Alternativni list postopka **z zavihki** (koraki ločeni po sklopih). | DA |
| `Podatki` | Tabela tehničnih parametrov za vsako velikost kolone/recepture (pretoki, volumni, tolerance, vzorci, ključi raztopin ...). | DA |

> **Opomba:** Vzorčna datoteka `Receptura.xlsm` ima lista poimenovana `Brez_zavihkov` in `Z_zavihki` – v delovni recepturi za IPO pa morata biti poimenovana točno `Receptura` in `Receptura_2`.

> **Pozor:** Lista `Spremembe` se **nikoli** ne ureja ročno in se **ne briše** iz datoteke.

**Primer** (iz vzorčne `Receptura.xlsm`, list `Spremembe`):

| Datum in cas | Zavihek | Celica | Stara vrednost | Nova vrednost | Uporabnik |
|---|---|---|---|---|---|
| 9. 3. 2026 13:50:40 | Sheet1 | A1:U1020 | [bulk change] 21420 celic | [bulk change] | Boštjan Komac |

---

## 3. Dve varianti recepture: `Receptura` vs `Receptura_2`

Sistem IPO podpira **dve varianti** zapisa postopka. V datoteki naj bosta prisotni **obe**, vendar KL izpolni aktivno **samo tisto, ki ustreza potrebi**. Druga ostane kot predloga/prazna.

### 3.1 `Receptura` – brez zavihkov

- Stolpec `Zavihek` (B) **ostane prazen v vseh vrsticah**.
- Koraki se številčijo **neprekinjeno od 1 naprej** skozi cel postopek.
- V sistemu IPO bo videti kot en dolg seznam korakov brez delitev.

**Kdaj uporabiti:** testiranje, enostaven postopek brez ločenih sklopov, GMP postopki z eno linijo izvajanja.

### 3.2 `Receptura_2` – z zavihki

- Koraki so razdeljeni v **ločene zavihke** (sklope) – v sistemu IPO bo vsak sklop svoj zavihek, med katerimi operater preklaplja.
- Vsak zavihek ima svojo **kodo** v stolpcu `Zavihek` (npr. `monolito1`, `monolito2`, `MF1`, `MF2`).
- Vsak zavihek **začne z lastnim številčenjem od `1`**.

**Kdaj uporabiti:** več palic/monolitov vzporedno, razdeljeno delo po dnevih, postopki z jasno ločenimi fazami.

> **Pozor:** V GMP postopkih se varianta `Receptura_2` praviloma **ne uporablja**. Za KL testiranja večih kolon na istem DN pa je priporočena.

#### Pravila za zavihke

**Prva vrstica novega zavihka (tipično `naslov`):**

| Stolpec | Vrednost |
|---------|----------|
| `Zavihek` (B) | nova koda zavihka, npr. `monolito1` *(ročna vrednost)* |
| `št. Koraka` (C) | `1` *(ročna vrednost – ne formula)* |
| `Navodilo` (D) | besedilo naslova (npr. *Zavihek za 1. palico*) |
| `Tip objekta` (I) | `naslov` |
| ostali stolpci | prazno |

**Naslednje vrstice znotraj istega zavihka:**

| Stolpec | Vrednost |
|---------|----------|
| `Zavihek` (B) | `=B_prejšnja` *(formula – koda se prenese)* |
| `št. Koraka` (C) | `=C_prejšnja+1` *(formula)* |

> **Pomembno:** Koda zavihka se **ročno vpiše samo v prvo vrstico** zavihka. Vse druge vrstice tega zavihka imajo formulo `=B_prej`.

**Primer** (iz `Receptura_2`, vzorčna datoteka):

| Zavihek | št. Koraka | Navodilo | Tip podatka | Tip objekta |
|---|---|---|---|---|
| `R-1-KO` | `1` | `R-1-KO` | *(prazno)* | `naslov` |
| *(iz formule `=B2`)* | `=C2+1` | Izpolni vodja | *(prazno)* | `naslov` |
| *(iz formule)* | `=C3+1` | Vodja | `zaposleni` | `edit` |
| *(iz formule)* | `=C4+1` | Dodatna navodila | `dodatnanavodila` | `memo` |
| *(iz formule)* | `=C5+1` | *(prazno)* | *(prazno)* | `crta` |

---

## 4. List `Podatki` in formule `INDEX/MATCH`

List `Podatki` je **tabela tehničnih parametrov**, ki se prenašajo v recepturo za vsako velikost kolone posebej.

### 4.1 Struktura

- **1. vrstica:** zaporedne številke stolpcev (1, 2, 3 ...) – uporabljajo se v `MATCH`.
- **2. vrstica:** imena stolpcev – opisi parametrov.
- **Od 3. vrstice naprej:** ena vrstica za vsako recepturo (eno velikost kolone). Prvi stolpec (`Receptura`) vsebuje oznako recepture, ki se uporablja kot ključ.

### 4.2 Stolpci v `Podatki` (najpogostejši)

| Oznaka | Ime stolpca | Opis |
|--------|-------------|------|
| A (1) | `Receptura` | Oznaka/koda recepture (npr. `R-A-800-TES-SDVB`). Ključ za `MATCH`. |
| B (2) | `V monolita (mL)` | Volumen monolita |
| C (3) | `Vzorec` | Opis vzorca |
| D (4) | `Pretok (mL/min) PM` | Nominalni pretok pulzne motnje |
| E (5) | `Odstopanje (mL/min)` | Dopustno odstopanje pretoka |
| F (6) | `Min. V` | Spodnja meja pretoka |
| G (7) | `Max. V` | Zgornja meja pretoka |
| H (8) | `Pretok (mL/min) IK` | Pretok za izokratno kromatografijo |
| J (10) | `Pretok spiranje (mL/min)` | Obseg pretoka za spiranje |
| K–L | `Min./Max. pretok` | Stroge meje pretoka spiranja |
| M (13) | `V zanke [mL]` | Volumen injekcijske zanke |
| O (15) | `5 CV` | 5 × kolumni volumen |
| S (19) | `10 CV` | 10 × kolumni volumen |
| W (23) | `tSST (min)` | Čas testa SST |
| AP (42) | `Vzorec` | Oznaka vzorca za lokacijo |
| AQ (47) | `Ključ 1` | Baza ključa raztopine vzorca (brez numerične pripone) |
| AT (50) | `Ključ1` | Drugi ključ raztopine (za TC) |
| AU (51) | `Ključ2` | Tretji ključ raztopine |
| BQ (69) | `Min tSST` | Spodnja meja časa SST |
| BR (70) | `Max tSST` | Zgornja meja časa SST |
| BS (71) | `Formula (Vr)` | Tip formule za retencijski volumen (`formula`, `formula0`, `formula1`) |

> **Opomba KL:** Ključi raztopin v stolpcih `Ključ 1`, `Ključ1`, `Ključ2` so vezani na oznake raztopin v IPO modulu RAZTOPINE. Prek teh ključev se raztopina v recepturi samodejno poveže s pripravljalnim dokumentom raztopine.

### 4.3 Kako se parametri berejo v recepturo (`INDEX/MATCH`)

V stolpcih `Navodilo`, `Kontrola N - par 1` in `Kontrola N - par 2` se parametri iz lista `Podatki` berejo s formulo `INDEX/MATCH`. Ključ ujemanja je **oznaka recepture**, zapisana v celici `$A$2` glavnega lista.

**Osnovna oblika formule:**

```
=INDEX(Podatki!$A:$BZ, MATCH($A$2, Podatki!$A:$A, 0), <stevilka_stolpca>)
```

- `$A$2` – celica z oznako recepture (fiksna sklica).
- `Podatki!$A:$A` – prvi stolpec `Podatki` (tam je koda recepture).
- `<stevilka_stolpca>` – številka stolpca iz 1. vrstice `Podatki`.

> **Opomba KL:** Teh celic **ne oblikujte ročno z vrednostmi** – vedno uporabite formulo `INDEX/MATCH`. Po dogovoru jih označimo s **sivo barvo ozadja**.

### 4.4 Barvna označitev celic v `Receptura` / `Receptura_2`

| Barva | Pomen |
|-------|-------|
| 🟡 **rumena** | naslovne vrstice (`Tip objekta = naslov`) |
| 🟠 **oranžna** | komentarji, opomniki za KL (niso del IPO izpisa) |
| ⬜ **siva** | celice z `INDEX/MATCH` formulami (samodejno berejo iz `Podatki`) |

### 4.5 Pomembno pri urejanju `Podatki`

> **Pozor:** V listu `Podatki` **ne brišite stolpcev**, le vsebino/vrednosti. Na stolpce so vezane formule v obeh receptura listih – če zbrišete stolpec, se formule `INDEX/MATCH` podrejo.

**Primer** (iz vzorčne datoteke, list `Brez_zavihkov`, vrstica 37):

```
Navodilo:   ="Dejanski φ MF1 ("&INDEX(Podatki!$A:$BZ,MATCH($D$2,Podatki!$A:$A,0),4)&" ± ..."
Kontrola 1: kontrolainterval
Par 1:      =INDEX(Podatki!$A:$BZ,MATCH($A$2,Podatki!$A:$A,0),6)
Par 2:      =INDEX(Podatki!$A:$BZ,MATCH($A$2,Podatki!$A:$A,0),7)
```

Formule pobirajo spodnjo (`Min. V`, stolpec 6) in zgornjo (`Max. V`, stolpec 7) mejo pretoka iz `Podatki` glede na izbrano velikost kolone.

---

## 5. Obvezni stolpci

V prvi vrstici (glavi) listov `Receptura` in `Receptura_2` **morajo biti** naslednji stolpci – natanko s temi imeni (pazi na presledke in šumnike):

| Oznaka stolpca | Ime stolpca | Opis |
|----|-------------|------|
| A  | *(prazno; v vrstici 2 je koda recepture v `$A$2`)* | Ključna celica za `INDEX/MATCH`. |
| B  | `Zavihek` | Koda zavihka (samo v `Receptura_2`). |
| C  | `št. Koraka` | Zaporedna številka koraka (celo število). |
| D  | `Navodilo` | Besedilo navodila (lahko vsebuje formule za sestavljanje nizov). |
| E  | `Tip podatka` | Vrsta vsebine (glej razdelek 7). |
| F  | `Ključ preverjanja` | Identifikator koraka (glej razdelek 8). |
| G  | `Vrednost` | Privzeta vrednost ali referenca na šifrant IPO. |
| H  | `Labela` | Enota ali opisna oznaka. |
| I  | `Tip objekta` | UI-element v IPO (glej razdelek 6). |
| J  | `Kontrola 1` | Ime 1. kontrole. |
| K  | `Kontrola 1 - par 1` | Parameter 1 prve kontrole. |
| L  | `Kontrola 1 - par 2` | Parameter 2 prve kontrole. |
| M–O | `Kontrola 2`, `Kontrola 2 - par 1`, `Kontrola 2 - par 2` | Druga kontrola. |
| P–R | `Kontrola 3`, `Kontrola 3 - par 1`, `Kontrola 3 - par 2` | Tretja kontrola. |
| S–U | `Kontrola 4`, `Kontrola 4 - par 1`, `Kontrola 4 - par 2` | Četrta kontrola. |

> **Pozor:** Stolpec **`št. Koraka`** vsebuje presledek med `št.` in `Koraka` ter šumnik. Zapis `st. Koraka` **ni veljaven** – validator javi napako `MISSING_COLUMN`.

> **Opomba:** Na začetku in na koncu recepture je nekaj vrstic, ki so vezane na IPO sistem (npr. `Izpolni vodja`, `Vodja`, `Dodatna navodila` na vrhu). **Teh vrstic ne brišite**, saj so vezane na druge module v IPO.

**Primer** (vzorčna glava iz `Brez_zavihkov`):

```
(A) | Zavihek | št. Koraka | Navodilo | Tip podatka | Ključ preverjanja |
Vrednost | Labela | Tip objekta |
Kontrola 1 | Kontrola 1 - par 1 | Kontrola 1 - par 2 |
Kontrola 2 | Kontrola 2 - par 1 | Kontrola 2 - par 2 |
Kontrola 3 | Kontrola 3 - par 1 | Kontrola 3 - par 2 |
Kontrola 4 | Kontrola 4 - par 1 | Kontrola 4 - par 2 |
```

---

## 6. Vrednosti polja `Tip objekta`

`Tip objekta` določa **UI-element** v sistemu IPO. Vrednosti pišite z **malimi črkami, brez presledkov**.

| Vrednost | UI-element v IPO | Kdaj uporabiti |
|----------|------------------|----------------|
| `naslov` | krepek naslov sekcije | Začetek nove sekcije ali zavihka; rumena barva v Excelu. |
| `crta` | vodoravna ločna črta | Ločevanje sklopov za preglednost. |
| `edit` | vnosno polje (tekst/število) | Kode, vrednosti, imena datotek, ročni vnosi. |
| `spustniseznam` | dropdown (povezan s šifrantom IPO) | Izbira opreme: HPLC, tehtnica, termometer, filtrirna enota ... |
| `checkbox` | kvadratek za kljukico | Potrjevanje dejanj (DA oz. DA/NE). |
| `memo` | večvrstično polje (brez omejitve znakov) | Poti do baz kromatogramov, daljša besedila, opombe. |
| `izberidatumcas` | koledarček za izbiro datuma in časa | Začetek/konec operacije, čas SST ... |
| `gumbdatumcas` | gumb, ki zapiše trenutni datum/čas | Alternativa `izberidatumcas`. |
| `formula` | izračunano polje (brez zaokroževanja) | Izračuni z vsemi decimalnimi mesti. |
| `formula0` | izračunano polje (zaokroženo na celo število) | Volumni, odčitki v celih številkah. |
| `formula1` | izračunano polje (1 decimalno mesto) | Retencijski volumen, tlak ... |
| `formula2` | izračunano polje (2 decimalni mesti) | pH, koncentracije. |
| `klictehtnice1` | klic tehtnice (avtomatski odčitek) | Samodejni odčitek mase. |

> **Pozor:** `spustni seznam`, `Spustniseznam`, `edit polje` **niso veljavne vrednosti** – validator javi `OBJECT_TYPE_UNKNOWN`. Pišite natanko: `spustniseznam`, `edit`.

**Primer** (iz vzorčne `Brez_zavihkov`):

| št. Koraka | Navodilo | Tip podatka | Tip objekta |
|---|---|---|---|
| 2 | `R-A-800-TES-SDVB` | *(prazno)* | `naslov` |
| 5 | *(prazno)* | *(prazno)* | `crta` |
| 12 | HPLC | `HPLC` | `spustniseznam` |
| 15 | Nastavljen φ (800 mL/min) | `checkbox` | `checkbox` |
| 31 | Baza kromatogramov (pot) | `baza` | `memo` |

---

## 7. Vrednosti polja `Tip podatka`

`Tip podatka` opisuje **vrsto vsebine**, ki se vnaša. Od tipa podatka je odvisna zahtevana vrednost v stolpcu `Labela`.

| Tip podatka | Opis | Zahtevana Labela | Najpogostejši Tip objekta |
|-------------|------|------------------|---------------------------|
| `kemikalija` | Kemikalija (vnos QR kode) | `koda` | `edit` |
| `raztopina` | Raztopina iz modula RAZTOPINE | `koda` | `edit` |
| `masa` | Masa ali volumen porabljene raztopine/kemikalije | enota (`g`, `mL`, `kg`) | `edit`, `klictehtnice1` |
| `monolit` | Monolit (QR koda sestavka) | `koda` | `edit` |
| `zaposleni` | Operater/Vodja (QR koda zaposlenega) | `koda` | `edit` |
| `embalaza` | Embalaža | `koda` | `edit` |
| `repro` / `reproodpis` | Reprocesiranje / odpis | `koda` | `edit` |
| `tehtnica` | Tehtnica | `naziv opreme` | `spustniseznam` |
| `termometer` | Termometer | `naziv opreme` | `spustniseznam` |
| `pH_meter`, `kopel`, `sušilnik`, `vak_sušilnik`, `merilnik`, `naprava` | Ostala oprema | `naziv opreme` | `spustniseznam` |
| `HPLC`, `črpalka`, `volumen`, `tlak`, `dejanski_pretok`, `baza`, `popravek_ohisja`, `popravek_mon`, `dodatnanavodila` | Lastno definirani tipi (besedilni/številčni vnosi) | ustrezna enota ali prazno | `edit`, `memo`, `spustniseznam` |
| `checkbox` | Polje za kljukico | `DA (kljukica)` ali `DA (kljukica)/NE (prazno)` | `checkbox` |
| `datumcaszacetek` | Datum/čas začetka operacije | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `datumcaskonec` | Datum/čas konca operacije | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `datumcas` | Splošni datum/čas | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `formula`, `summasa`, `masakonec` | Izračunane vrednosti | enota | `formula`, `formula0`, `formula1` |
| `naslov` | Naslov sekcije/zavihka | *(prazno)* | `naslov` |
| `crta` | Ločnik | *(prazno)* | `crta` |

> **Pozor – Labela za kodo:** Tipi `kemikalija`, `raztopina`, `monolit`, `zaposleni`, `repro`, `reproodpis` **morajo imeti** `Labela = koda`. Validator javi `LABEL_MUST_BE_KODA`.

> **Pozor – voda:** Ko se uporablja voda, **tip podatka ni `masa`**, ker vode ne vnašamo v modul RAZTOPINE. Uporabite tip `volumen` z enoto `mL` (ali brez tipa, samo `edit`).

> **Opomba:** Pri tipu `masa` **vedno** vnesete porabljeno količino – tudi če jo vpišete v mL, se iz gostote avtomatsko poračuna masa, ki se odšteje od zaloge raztopine.

**Primer** (iz vzorčne `Brez_zavihkov`):

| Navodilo | Tip podatka | Ključ preverjanja | Vrednost | Labela | Tip objekta |
|---|---|---|---|---|---|
| Vodja | `zaposleni` | *(prazno)* | *(prazno)* | `koda` | `edit` |
| Koda sestavljenega monolita | `monolit1` | *(prazno)* | *(prazno)* | `koda` | `edit` |
| HPLC | `HPLC` | `tk_1` | `HPLC` | `naziv opreme` | `spustniseznam` |
| Dejanski φ MF1 (800 ± 40 mL/min) | `dejanski_pretok` | `tk_1` | *(prazno)* | `mL/min` | `edit` |
| Porabljen V 2.73 ut% NaCl ... | `masa` | `2.73mp-NaCl_13.87mp-EtOH-GK3` | *(prazno)* | `mL` | `edit` |

---

## 8. Ključ preverjanja

`Ključ preverjanja` (stolpec F) je **identifikator koraka** za IPO. Uporablja se za:

- povezovanje **para kemikalija/raztopina – masa** (isti ključ označuje isti material),
- povezovanje **para datumcaszacetek – datumcaskonec** (isti ključ označuje isti časovni interval),
- sklicevanje med koraki (`aliobstajapogoj`, `zaklenipolja`).

### 8.1 Pravila formata

**Dovoljeni znaki:** `A–Z`, `a–z`, `0–9`, `-`, `_`, `.`

**Prepovedani:** presledki, šumniki (`č`, `š`, `ž`), posebni znaki (`#`, `@`, `/`, `\`, ...).

| Veljaven ključ | Neveljaven ključ | Razlog |
|----------------|------------------|--------|
| `pretok_mf1` | `pretok mf1` | presledek |
| `masa_kem1` | `masa_čas` | šumnik `č` |
| `2.73mp-NaCl_13.87mp-EtOH-GK1` | `kem#1` | znak `#` |
| `tk_1`, `pm1_1`, `locba_1` | `TK 1` | presledek |

### 8.2 Kdaj je ključ obvezen

| Tip vrstice | Ključ obvezen? |
|-------------|----------------|
| `kemikalija`, `raztopina`, `masa`, `tehtnica` (in ostala oprema), `checkbox` s pogojem, `datumcaszacetek`, `datumcaskonec` | **DA** |
| `naslov`, `crta` | NE |
| `zaposleni` (vodja/operater) | NE (običajno) |

> **Pozor:** Če za `kemikalija`, `raztopina`, `masa` ali `tehtnica` manjka ključ, validator javi `KEY_REQUIRED`.

### 8.3 Podvajanje in oštevilčenje

- **Raztopine in kemikalije istega tipa** se oštevilčijo z numerično pripono (`GK1`, `GK2`, `GK3` ali `NaCl1`, `NaCl2` ...).
- Oštevilčenje se **začne z `1`** in poteka **brez vrzeli**.
- Masa mora imeti **enak ključ kot njena kemikalija/raztopina**, nad katero stoji (par).

| Primer veljavnega zaporedja | Razlaga |
|------------------------------|---------|
| raztopina `GK1`, masa `GK1` | par raztopina–masa |
| raztopina `GK2`, masa `GK2` | drugi par |
| raztopina `GK3`, masa `GK3` | tretji par |

| Primer napačnega zaporedja | Napaka |
|----------------------------|--------|
| raztopina `GK1`, masa `GK2` | `PAIR_MASS_WITHOUT_OWNER` |
| raztopina `GK2` brez `GK1` | `KEY_NUM_NOT_FROM_ONE` |
| raztopina `GK1`, `GK3` (brez `GK2`) | `KEY_NUM_GAP` |

### 8.4 Baza ključa (uporaba v kontrolah)

Pri kontrolah `kontrolaveljavnostiraztopine` in `kontrolaustreznostiraztopine` se v `Par1` vpiše **baza ključa brez numerične pripone**:

| Ključ raztopine (stolpec F) | Baza ključa (Par1 v kontroli) |
|-----------------------------|-------------------------------|
| `2.73mp-NaCl_13.87mp-EtOH-GK1` | `2.73mp-NaCl_13.87mp-EtOH-GK` |
| `GK3` | `GK` |

**Primer** (iz vzorčne `Brez_zavihkov`, vrstica 14):

```
Navodilo:           Raztopina 2.73 ut% NaCl + 13.87 ut% EtOH
Tip podatka:        raztopina
Ključ preverjanja:  2.73mp-NaCl_13.87mp-EtOH-GK1
Labela:             koda
Tip objekta:        edit
Kontrola 2:         kontrolaveljavnostiraztopine
Kontrola 2 - par 1: 2.73mp-NaCl_13.87mp-EtOH-GK   ← baza (brez "1")
```

---

## 9. Kontrole

Vsak korak ima **do 4 kontrole** (stolpci `Kontrola 1`–`Kontrola 4`). Vsaka kontrola ima:

- **ime kontrole** (stolpec `Kontrola N`)
- **parameter 1** (stolpec `Kontrola N - par 1`)
- **parameter 2** (stolpec `Kontrola N - par 2`)

Ime kontrole se piše z **malimi črkami brez presledkov in brez šumnikov**.

### 9.1 Seznam veljavnih kontrol

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolapraznopolje` | Polje ne sme biti prazno (obvezen vnos). | *(prazno)* | *(prazno)* |
| `kontrolainterval` | Številska vrednost mora biti znotraj intervala. Odprti intervali – meje pišemo eksluzivno. | spodnja meja (število ali formula) | zgornja meja |
| `kontrolacasa` | Trajanje (v sekundah) med `datumcaszacetek` in `datumcaskonec`. | min sek | max sek |
| `aliobkljukan` | Checkbox mora biti označen. | `DA` ali `NE` | *(prazno)* |
| `aliniobkljukan` | Checkbox ne sme biti označen. | `DA` ali `NE` | *(prazno)* |
| `aliobstajapogoj` | Polje je aktivno, če pogoj velja. | ključ ali referenca celice (`=$F$58`) | `0` ali `1` |
| `aliobstajapogoj_ali` | Pogoj z ALI logiko. | referenca | `0` ali `1` |
| `alipravavloga` / `alipravavlogakoda` | Preverja vlogo operaterja. | `ROLE_HEAD` ali `ROLE_OPERATOR` | *(prazno)* |
| `kdoizpolni` | Določa, kdo sme izpolniti polje. | `ROLE_HEAD` ali `ROLE_OPERATOR` | *(prazno)* |
| `zaklenipolja` | Zaklene naštete korake, če je polje označeno. | seznam številk korakov ločenih z vejico (npr. `45,46,47`) | *(prazno)* |
| `aliisto` | Vrednost mora biti enaka drugemu koraku. | referenca (npr. `=C13`) | *(prazno)* |
| `kontrolaveljavnostiopreme` | Oprema mora biti veljavna (kalibrirana). | tip opreme (`HPLC`, `tehtnica`, `termometer`, `filter`) | *(prazno)* |
| `kontrolaustreznostiopreme` | Oprema mora biti primerna za postopek. | tip opreme | *(prazno)* |
| `kontrolaveljavnostiraztopine` | Raztopina mora biti v roku. | baza ključa raztopine | *(prazno)* |
| `kontrolaustreznostiraztopine` | Raztopina mora ustrezati kemiji. | baza ključa raztopine | *(prazno)* |
| `kontrolaveljavnostimonolita` | Monolit mora biti veljaven. | *(prazno)* | *(prazno)* |
| `kontrolaustreznostimonolita` | Monolit mora biti pravi tip (npr. sestavljen, ne surov). | koda tipa ali seznam (`SES`, `MOD,SPIR`) | *(prazno)* |
| `kontrolaveljavnostikemikalije` / `kontrolaustreznostikemikalije` | Kemikalija mora biti veljavna/ustrezna. | *(prazno)* | *(prazno)* |
| `kontrolamase` | Masa mora biti v dovoljenih mejah. | (običajno skupaj s `kontrolainterval`) | *(prazno)* |
| `kontrolaembalaze` | Embalaža mora biti veljavna. | *(prazno)* | *(prazno)* |
| `kontrolarazlika` | Razlika med vrednostmi dveh korakov je v mejah. | referenca | meja |
| `kontrolaustreznostilinije`, `kontrolaveljavnostiseta`, `kontrolaustreznostiseta`, `prenosset` | Posebne kontrole za linije/sete. | odvisno | odvisno |

> **Pozor – `kontrolainterval` je odprti interval:** Če SOP zahteva npr. `3.2 ≤ x ≤ 4.2`, potem vpišemo `Par1 = 3.1`, `Par2 = 4.3`. Če SOP piše `> 24 ur`, ne pustite neskončne zgornje meje – izberite realno mejo (npr. `72 ur`, tj. `259200` sekund).

> **Pozor – enote:** V parametre kontrole vpisujete **samo številčne vrednosti brez enot**. Enota je v stolpcu `Labela`.

> **Pozor – decimalno ločilo:** V številkah uporabljajte **piko** (`6.5`), ne vejice (`6,5`). Validator javi `COMMA_NOT_ALLOWED`. Izjema: `zaklenipolja` – kjer vejica ločuje številke korakov.

### 9.2 Najpogostejše kombinacije kontrol po tipu vrstice

**`edit` z obvezno vrednostjo (številka, besedilo):**

```
Kontrola 1: kontrolapraznopolje
```

**Številka z intervalom (npr. pretok, tlak):**

```
Kontrola 1: kontrolainterval | Par1: <spodnja> | Par2: <zgornja>
Kontrola 2: kontrolapraznopolje
```

**Raztopina:**

```
Kontrola 1: kontrolaveljavnostiraztopine | Par1: <baza_ključa>
Kontrola 2: kontrolaustreznostiraztopine | Par1: <baza_ključa>
Kontrola 3: kontrolapraznopolje
```

**Kemikalija:**

```
Kontrola 1: kontrolaveljavnostikemikalije
Kontrola 2: kontrolaustreznostikemikalije
Kontrola 3: kontrolapraznopolje
```

**Monolit:**

```
Kontrola 1: kontrolaustreznostimonolita | Par1: <tip, npr. SES ali MOD,SPIR>
Kontrola 2: kontrolaveljavnostimonolita
Kontrola 3: kontrolapraznopolje
```

**Oprema (HPLC, tehtnica, termometer ...):**

```
Kontrola 1: kontrolaveljavnostiopreme | Par1: <tip opreme>
Kontrola 2: kontrolaustreznostiopreme | Par1: <tip opreme>
Kontrola 3: kontrolapraznopolje
```

**Vodja (zaposleni, `ROLE_HEAD`):**

```
Kontrola 1: alipravavlogakoda | Par1: ROLE_HEAD
Kontrola 2: kdoizpolni         | Par1: ROLE_HEAD
Kontrola 3: kontrolapraznopolje
```

**Operater (zaposleni, `ROLE_OPERATOR`):**

```
Kontrola 1: alipravavlogakoda | Par1: ROLE_OPERATOR
Kontrola 2: kontrolapraznopolje
```

**Checkbox (obvezen DA):**

```
Kontrola 1: aliobkljukan | Par1: DA
```

> **Pozor:** Pri `checkbox` se `kontrolapraznopolje` **ne sme** uporabiti – validator javi `CTRL_CHECKBOX_EMPTY`.

**Checkbox (DA ali NE, z medsebojnim zaklepanjem):**

```
Kontrola 1: zaklenipolja | Par1: 45,46,47,48   (seznam korakov, ki se zaklenejo)
```

**Datum/čas par – začetek:**

```
Kontrola 1: kontrolapraznopolje
```

**Datum/čas par – konec (kontrola trajanja):**

```
Kontrola 1: kontrolacasa | Par1: <min_sekunde> | Par2: <max_sekunde>
Kontrola 2: kontrolapraznopolje
```

> **Opomba:** `kontrolacasa` je odprti interval. Za točen čas 60 s pišete `Par1 = 50`, `Par2 = 70` (tj. 60 ± 10 s).

### 9.3 Obvezna kontrola `kontrolapraznopolje`

Pri **vseh vnosnih tipih objektov** (`edit`, `spustniseznam`, `izberidatumcas`, `gumbdatumcas`, `memo`) je `kontrolapraznopolje` **obvezna** v zadnji razpoložljivi reži. Validator jo zahteva s kodo `CTRL_REQUIRED_EMPTY`.

**Izjeme** – pri teh tipih objekta `kontrolapraznopolje` **NI** potrebna:

- `naslov`
- `crta`
- `checkbox`

**Primer** (iz vzorčne `Brez_zavihkov`, vrstica 4):

```
Navodilo:            Vodja
Tip podatka:         zaposleni
Labela:              koda
Tip objekta:         edit
Kontrola 2:          alipravavlogakoda
Kontrola 2 - par 1:  ROLE_HEAD
Kontrola 3:          kdoizpolni
Kontrola 3 - par 1:  ROLE_HEAD
Kontrola 4:          kontrolapraznopolje
```

---

## 10. Vloge operaterjev (`ROLE_HEAD`, `ROLE_OPERATOR`)

Sistem IPO loči dve vlogi za izpolnjevanje recepture:

| Vloga | Opis | Tipična uporaba |
|-------|------|-----------------|
| `ROLE_HEAD` | Vodja (višja odgovornost) | Potrditve, dodatna navodila, odobritve |
| `ROLE_OPERATOR` | Operater (izvajalec postopka) | Operativni vnosi, odčitki, čas, meritve |

### Vezava vloge na korak

1. **`alipravavlogakoda`** – preveri, da ima oseba, ki skenira QR kodo, zahtevano vlogo.
2. **`kdoizpolni`** – določi, da to polje lahko izpolni **samo oseba s to vlogo** (ostale so zaklenjene).

**Primer – polje, ki ga izpolni vodja:**

```
Tip podatka:         zaposleni
Labela:              koda
Tip objekta:         edit
Kontrola 1:          alipravavlogakoda  | Par1: ROLE_HEAD
Kontrola 2:          kdoizpolni          | Par1: ROLE_HEAD
Kontrola 3:          kontrolapraznopolje
```

**Primer – polje, ki ga izpolni operater (vrstica 7, vzorčna `Brez_zavihkov`):**

```
Tip podatka:         zaposleni
Labela:              koda
Tip objekta:         edit
Kontrola 2:          alipravavlogakoda  | Par1: ROLE_OPERATOR
Kontrola 4:          kontrolapraznopolje
```

---

## 11. Posebni tipi vrstic

### 11.1 `naslov`

- Označuje **začetek sekcije ali zavihka**.
- V Excelu je **rumena vrstica**.
- Ima številko koraka in besedilo naslova, ostalo je prazno.

```
št. Koraka: 11
Navodilo:   Test ustreznosti kromatografskega sistema
Tip objekta: naslov
```

### 11.2 `crta`

- Vizualni **ločnik med sklopi**. V IPO se izpiše kot vodoravna črta.
- **Mora imeti svojo številko koraka.**
- Ostali stolpci so prazni.

```
št. Koraka: 20
Navodilo:   (prazno)
Tip objekta: crta
```

> **Pozor:** Če `crta` nima številke koraka, validator javi `STEP_MISSING` ali `STEP_GAPS`.

### 11.3 `checkbox`

- Polje za kljukico.
- `Labela` mora biti **natanko ena** od dveh vrednosti:
  - `DA (kljukica)` – obvezna kljukica
  - `DA (kljukica)/NE (prazno)` – DA ali NE
- Pri obveznem DA dodajte `aliobkljukan` s `Par1 = DA`.
- **Nikoli** ne dodajajte `kontrolapraznopolje` na checkbox.

```
Navodilo:    Ni puščanja v sistemu
Tip podatka: checkbox
Labela:      DA (kljukica)
Tip objekta: checkbox
Kontrola 2:  aliobkljukan | Par1: DA
```

### 11.4 `spustniseznam`

- Dropdown, povezan s **šifrantom IPO**.
- V stolpec `Vrednost` vpišite oznako šifranta (npr. `HPLC`, `tehtnica`, `TEH-KLA`). To določi, kateri seznam se prikaže operaterju.
- V `Labela` vpišite `naziv opreme`.

```
Navodilo:    HPLC
Tip podatka: HPLC
Vrednost:    HPLC
Labela:      naziv opreme
Tip objekta: spustniseznam
Kontrola 2:  kontrolaveljavnostiopreme  | Par1: HPLC
Kontrola 3:  kontrolaustreznostiopreme | Par1: HPLC
Kontrola 4:  kontrolapraznopolje
```

### 11.5 `izberidatumcas` / `gumbdatumcas` (datum/čas)

- Polje za izbiro datuma in časa (koledarček).
- `Labela` = `datum/čas`.
- Par začetek–konec mora imeti **enak ključ preverjanja** in na koncu dodano `kontrolacasa`.

```
# Začetek
Tip podatka:  datumcaszacetek
Ključ:        locba_1
Labela:       datum/čas
Tip objekta:  izberidatumcas
Kontrola 1:   kontrolapraznopolje

# Konec
Tip podatka:  datumcaskonec
Ključ:        locba_1
Labela:       datum/čas
Tip objekta:  izberidatumcas
Kontrola 1:   kontrolacasa | Par1: 3590 | Par2: 3610   (60 min ± 10 s)
Kontrola 2:   kontrolapraznopolje
```

### 11.6 `formula`, `formula0`, `formula1`, `formula2`

- Izračunano polje v sistemu IPO.
- V stolpec `Vrednost` vpišete **Excelovo formulo kot besedilo**, ki zgradi IPO formulo s `$` pred številkami korakov:

```
="=($"&C113&"-"&"$"&C108&")/($"&C108&"-$"&C89&")"
```

> Ta formula se sklicuje na korake 113, 108 in 89. IPO nato sam izračuna rezultat po tej formuli.

- Formula mora vsebovati **znak `$`** (sklic na korak). Brez tega javi validator `FORMULA_NO_REFERENCE`.
- Sklicujete se lahko samo na korake tipa `edit`, `formula`, `formula0`, `formula1`. Ne na `naslov`, `crta`, `checkbox`.

| Tip | Zaokroževanje |
|-----|---------------|
| `formula` | brez |
| `formula0` | celo število |
| `formula1` | 1 decimalno mesto |
| `formula2` | 2 decimalni mesti |

---

## 12. Korak po korak: dodajanje novega koraka

Spodnja procedura velja za dodajanje vnosnega polja v obstoječo recepturo (list `Receptura` ali `Receptura_2`).

### Koraki

1. **Odpri datoteko** `Receptura.xlsm` (omogoči makre).
2. **Poišči mesto**, kjer se bo dodal nov korak. Izberite vrstico, ki bo **za novo vrstico** (nov korak bo vstavljen **nad** njo).
3. **Desni klik → Insert → Entire row** (ali Ctrl+Shift+=). Excel vstavi prazno vrstico.
4. **Številka koraka (stolpec C):** Vpišite formulo `=C<prejšnja>+1`. V vseh vrsticah **pod** novo vrstico Excel že ima `=C<prev>+1`, zato se številčenje samodejno popravi.
   - Če ste v `Receptura_2` in dodajate korak **znotraj zavihka**, v stolpec B vpišite `=B<prejšnja>` (formula, ne ročno kodo zavihka).
5. **Navodilo (D):** Vpišite besedilo navodila (ali Excelovo formulo za sestavljanje niza z `INDEX/MATCH`). Šumniki in presledki so dovoljeni.
6. **Tip podatka (E):** Izberite ustrezno vrednost iz razdelka 7 (npr. `raztopina`, `masa`, `dejanski_pretok`, `checkbox`).
7. **Ključ preverjanja (F):** Vpišite ključ po pravilih iz razdelka 8 (brez presledkov in šumnikov). Pri masi uporabite **isti ključ** kot pri njeni raztopini/kemikaliji.
8. **Vrednost (G), Labela (H), Tip objekta (I):** Izpolnite po tabeli v razdelku 7 (npr. za opremo: `Vrednost = HPLC`, `Labela = naziv opreme`, `Tip objekta = spustniseznam`).
9. **Kontrole (J–U):** Dodajte ustrezno kombinacijo iz razdelka 9.2. Preverite, da je **`kontrolapraznopolje`** prisotna na vseh vnosnih poljih (razen `checkbox`).
10. **Obarvajte celice:**
    - Rumeno, če je `Tip objekta = naslov`.
    - Sivo, če ste v Navodilu ali Kontrolah uporabili `INDEX/MATCH`.
    - Oranžno za komentarje (ki **ne gredo v IPO**).
11. **Zaženite validator** (razdelek 14). Popravite vse napake `ERROR`. Opozorila `WARNING` pregledajte in uredite po potrebi.

> **Opomba:** Po končanih spremembah shranite datoteko kot `.xlsm` (ohrani makre, ki polnijo list `Spremembe`).

---

## 13. Tipične napake in rešitve

| Napaka | Koda validatorja | Vzrok | Rešitev |
|--------|------------------|-------|---------|
| Stolpec manjka ali preimenovan | `MISSING_COLUMN` | Zbrisan stolpec ali nepravilno ime (npr. `st. Koraka`) | Obnovite točno ime `št. Koraka`, uskladite vse obvezne stolpce (razdelek 5). |
| Manjka številka koraka | `STEP_MISSING` | Brisana formula `=C<prev>+1` ali pozabljeno na `crta` vrstici | Dodajte formulo v stolpec C za vsako vrstico, tudi `crta`. |
| Podvojena številka koraka | `STEP_DUPLICATE` | Kopirana vrstica z enako vrednostjo | Uporabite formulo `=C<prev>+1` namesto statične vrednosti. |
| Vrzel v korakih (npr. 1,2,4) | `STEP_GAPS` | Brisana vrstica ali `crta` brez koraka | Preverite neprekinjenost zaporedja. |
| Koraki v zavihku se ne začnejo z 1 | `STEP_TAB_NOT_FROM_ONE` | V prvi vrstici zavihka v `Receptura_2` je formula namesto `1` | V prvo vrstico vsakega zavihka v stolpec C vpišite **`1`** (ne formulo). |
| Neznan `Tip objekta` | `OBJECT_TYPE_UNKNOWN` | Tipkarska napaka (`spustni seznam`, `Edit`) | Uporabite točen zapis male črke brez presledkov (razdelek 6). |
| Tip objekta ne ustreza tipu podatka | `OBJECT_TYPE_MISMATCH` | Npr. `raztopina` + `spustniseznam` | Uskladite po tabeli v razdelku 7. |
| Napačna `Labela` za kodo | `LABEL_MUST_BE_KODA` | Labela ni `koda` za `kemikalija`, `monolit`, `zaposleni`, `repro`, `reproodpis` | Vpišite `koda` (male črke). |
| Napačna `Labela` pri checkbox | `LABEL_CHECKBOX_FORMAT` | Različna pisava ali presledki | Vpišite natanko `DA (kljukica)` ali `DA (kljukica)/NE (prazno)`. |
| Nedovoljeni znaki v ključu | `KEY_INVALID_FORMAT` | Presledki, šumniki, posebni znaki | Uporabite samo `A–Z a–z 0–9 - _ .` (razdelek 8.1). |
| Manjka ključ pri kemikaliji/masi/raztopini/tehtnici | `KEY_REQUIRED` | Prazna celica v stolpcu F | Dodajte unikatni ključ. |
| Masa brez pripadajoče kemikalije/raztopine | `PAIR_MASS_WITHOUT_OWNER` | Masa nima lastnika z enakim ključem | Dodajte ali popravite kemikalijo/raztopino z istim ključem tik pred maso. |
| Začetek časa brez konca (ali obratno) | `PAIR_TIME_WITHOUT_END` / `PAIR_TIME_WITHOUT_START` | Manjka druga polovica para | Dodajte pripadajočo vrstico z istim ključem. |
| Podvojen ključ raztopine | `KEY_DUP_SOL` | Kopiran ključ | Dodajte numerično pripono (`GK1`, `GK2` ...). |
| Oštevilčenje se ne začne z 1 | `KEY_NUM_NOT_FROM_ONE` | Izbrisana vrstica z `GK1` | Začnite z `1`, neprekinjeno naprej. |
| Vrzel v oštevilčenju | `KEY_NUM_GAP` | Brisan vmesni ključ | Preimenujte ali dodajte manjkajočo vrstico. |
| Vejica kot decimalno ločilo | `COMMA_NOT_ALLOWED` | `6,5` namesto `6.5` | Zamenjajte `,` s `.` (razen pri `zaklenipolja`). |
| Presledek v vrednosti | `SPACE_NOT_ALLOWED` | Presledek v `Tip objekta`, `Ključ`, `Vrednost` ... | Odstranite presledek. Dovoljen le v `Navodilo` in `Labela`. |
| Formula brez `=` | `FORMULA_SYNTAX` | Vpisana kot besedilo | Začnite z `=`, zgradite z `$`. |
| Formula brez sklica | `FORMULA_NO_REFERENCE` | Manjka `$` | Dodajte sklic na številko koraka: `"$"&C113`. |
| Formula se sklicuje na neobstoječ/napačen korak | `FORMULA_INVALID_REFERENCE` / `FORMULA_STEP_INVALID_TYPE` | Izbrisan korak ali sklic na `naslov`/`crta` | Preverite vse `$N` sklice. |
| Napačna tehtnica glede na maso | `SCALE_VALUE_TOO_HIGH` / `SCALE_VALUE_TOO_LOW` | `TEH-ANA` za ≥ 10 g ali `TEH-KLA` za < 10 g | Masa ≥ 10 g → `TEH-KLA`; masa < 10 g → `TEH-ANA`; za oba razreda: `TEH-KLA, TEH-ANA`. |
| Neznana kontrola | `CTRL_UNKNOWN` | Tipkarska napaka | Preverite seznam v razdelku 9.1 (male črke, brez presledkov). |
| Kontrola ni dovoljena v tem kontekstu | `CTRL_INVALID_CONTEXT` | Npr. `kontrolainterval` na `checkbox` | Uporabite ustrezno kontrolo za tip vrstice. |
| Manjka obvezna `kontrolapraznopolje` | `CTRL_REQUIRED_EMPTY` | Vnosno polje brez `kontrolapraznopolje` | Dodajte `kontrolapraznopolje` v zadnji prosti reži. |
| Checkbox ima `kontrolapraznopolje` | `CTRL_CHECKBOX_EMPTY` | Nedovoljena kombinacija | Odstranite `kontrolapraznopolje`, uporabite `aliobkljukan`. |
| `kontrolainterval` brez mej | `CTRL_INTERVAL_PARAMS` | Prazen Par1 ali Par2 | Vpišite obe meji (številka ali formula). |
| `Par1 ≥ Par2` | `CTRL_INTERVAL_RANGE` | Zamenjan vrstni red | `Par2` mora biti strogo večji od `Par1`. |
| Napačne meje glede na Navodilo | `CTRL_INTERVAL_P1_BOUND` / `CTRL_INTERVAL_P2_BOUND` | Razmerje med mejami in `Navodilo` ni pravilno | Razpon `a–b` + eps; toleranca `± t` → `x±(t+eps)`; neenačba `> x` → `Par1 = x`, `Par2 ≥ x+eps`. |
| `zaklenipolja` napačen `Par1` | `LOCK_P1_FORMAT` | Decimalke, presledki, besedilo | Samo cela števila, ločena z vejicami: `45,46,47`. |
| Korak v `zaklenipolja` ne obstaja | `LOCK_P1_STEP_MISSING` | Izbrisan korak | Preverite številke v `Par1`. |
| Raztopina: `Par1` se ne ujema z bazo ključa | `SOLUTION_P1_BASE` | V `Par1` je cel ključ (z `1`) namesto baze | Vpišite bazo brez numerične pripone (npr. `GK` namesto `GK1`). |

> **Opomba:** Poln seznam kod in rešitev je v dokumentu **NAV-158 Navodila za uporabo aplikacije IPO Validator**, razdelek 4.

---

## 14. Validacija recepture

### 14.1 Kdaj validirati

- **Po vsaki spremembi** recepture (dodan/spremenjen/izbrisan korak).
- **Pred predajo** recepture vodji tehnologije.
- **Pred prenosom** v proizvodnjo (GMP).

### 14.2 Zagon aplikacije IPO Validator

1. Dvokliknite `Validator.exe`.
2. Odpre se okno **„Validator IPO Receptur"**.
3. Kliknite **Izberi...** pri vrstici *Vhodna Excel datoteka (receptura)* in izberite svojo recepturo (`.xlsx` ali `.xlsm`).
   - Za več receptur hkrati: ponovno kliknite **Izberi...** za vsako dodatno datoteko.
4. Kliknite **Shrani kot...** in določite, kam se shrani poročilo validacije (npr. `por_Receptura_A800.xlsx`).
5. Izberite **Način poročila**:
   - *Ena skupna datoteka* – vse napake v eni datoteki.
   - *Ločeno poročilo za vsako datoteko* – po en `por_<ime>.xlsx` za vsako recepturo.
6. Kliknite **Zaženi validacijo**.
7. Po končani validaciji se prikaže povzetek:
   - `Brez napak` – receptura je strukturno veljavna.
   - `Najdene napake: N` – odprite poročilo in preverite napake.

### 14.3 Razlaga poročila (`.xlsx`)

Poročilo ima **dva lista**:

**List `Povzetek`** – seznam vseh napak in opozoril:

| Stolpec | Vsebina |
|---------|---------|
| List | Ime lista v recepturi + ime datoteke |
| Vrstica | Vrstica v recepturi, kjer je napaka |
| Stolpec | Ime stolpca z napako (npr. `Labela`, `Kontrola 1`) |
| Napaka | Kratek slovenski opis (npr. *Manjka obvezen stolpec*) |
| Opis napake | Podrobno besedilo napake in predlagana pravilna vrednost |

**List `Število napak`** – tabela: Koda | Opis | Število. Uporabno za hiter pregled najpogostejših napak.

### 14.4 Resnost napak

| Resnost | Pomen | Akcija KL |
|---------|-------|-----------|
| **ERROR** | Napaka, ki jo validator označi kot nepravilnost. | Pripravljalec **MORA** preveriti in po presoji odpraviti. |
| **WARNING** | Opozorilo – možna nepravilnost. | Priporočljivo odpraviti; ne blokira. |
| **INFO** | Informativna beležka. | Le v vednost; akcija ni potrebna. |

> **Pomembno:** Validator včasih javi napake, ki **niso** nujno dejanske napake v recepturi (npr. intervali, ki jih SOP dovoljuje širše). Pripravljalec mora vsako napako tipa ERROR **individualno preveriti** in presoditi, ali gre za dejansko nepravilnost. Če ugotovi, da receptura kljub napaki validatorja ustreza zahtevam, je primerna za prenos v proizvodnjo.

### 14.5 Popravljanje in ponovna validacija

1. V poročilu **filtrirajte po stolpcu Napaka** – najprej odpravite najpogostejše napake.
2. V recepturi poiščite navedeno vrstico in stolpec.
3. Popravite po rešitvah iz razdelka 13 tega dokumenta.
4. Shranite datoteko.
5. Ponovno zaženite validator – korake 3–7 iz razdelka 14.2.
6. Postopek ponavljajte, dokler poročilo ne pokaže `Brez napak` **ali** dokler niso vse preostale napake upravičene (in dokumentirane kot taka).

### 14.6 Primerjava `Receptura` ↔ `Receptura_2`

V validatorju je gumb **Primerjaj razdelke med listi**, ki preveri, ali sta oba lista vsebinsko usklajena (enako število sekcij, enake ključne vrednosti). Uporabno, kadar vzdržujete obe varianti hkrati.

---

> **Zaključni nasvet za KL:** Pri novi recepturi se vedno zgledujte po **obstoječi recepturi istega tipa** (isti postopek, druga velikost). Najprej skopirajte datoteko, preimenujte, zamenjajte kodo recepture v `Podatki` in `$A$2`, nato po potrebi dodajte/odstranite korake. Na koncu **obvezno** zaženite validator.
