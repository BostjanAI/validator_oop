# Navodila za pripravo Excel recepture za IPO sistem (KL)


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

Dokument opisuje, kako se pripravi Excel receptura (`.xlsm`) za sistem **IPO** (Industrijska programska oprema). Navodila so praktična in pokrivajo vsak stolpec, vsako vrednost ter vsako kontrolo, ki se uporablja pri rednem delu v KL.

### Vloga recepture v sistemu IPO

Receptura je **izvorna definicija postopka** za sistem IPO. Vsak korak v Excelu postane en vnosno polje, spustni seznam, checkbox ali naslov v IPO vmesniku, ki ga operater izpolnjuje. Kontrole v recepturi preprečijo napačne vnose že med delom (npr. vrednost izven intervala, napačna oprema, neveljavna raztopina). 

---

## 2. Struktura recepturne datoteke (štirje listi)

Vsaka recepturna datoteka ima točno **štiri liste (zavihke)** v tem vrstnem redu:

| List | Namen | Ali se ureja ročno? |
|------|-------|---------------------|
| `Spremembe` | Avtomatski dnevnik sprememb v datoteki (datum, zavihek, celica, stara/nova vrednost, uporabnik). | **NE** – polni ga makro. |
| `Receptura` | Glavni list postopka **brez zavihkov** (en neprekinjen seznam korakov). | DA |
| `Receptura_2` | Alternativni list postopka **z zavihki** (koraki ločeni po sklopih). | DA |
| `Podatki` | Tabela tehničnih parametrov za vsako velikost kolone/recepture (pretoki, volumni, tolerance, vzorci, ključi raztopin ...). | DA |

> **Pozor:** Lista `Spremembe` se **nikoli** ne ureja ročno in se **ne briše** iz datoteke.


## 3. Dve varianti recepture: `Receptura` vs `Receptura_2`

### 3.1 `Receptura` – brez zavihkov

- Stolpec `Zavihek` (B) **ostane prazen v vseh vrsticah**.
- Koraki se številčijo **neprekinjeno od 1 naprej** skozi cel postopek.
- V sistemu IPO bo videti kot en dolg seznam korakov brez delitev.


### 3.2 `Receptura_2` – z zavihki

- Koraki so razdeljeni v **ločene zavihke** (sklope) – v sistemu IPO bo vsak sklop svoj zavihek, med katerimi operater preklaplja.
- Vsak zavihek ima svojo **kodo** v stolpcu `Zavihek` (npr. `monolit1`, `monolit2`).
- Vsak zavihek **začne z lastnim številčenjem od `1`**.

**Kdaj uporabiti:** več palic/monolitov vzporedno.

## 4. List `Podatki` in formule `INDEX/MATCH`

List `Podatki` je **tabela tehničnih parametrov**, ki se prenašajo v recepturo za vsako velikost kolone posebej.

### 4.1 Struktura

- **1. vrstica:** zaporedne številke stolpcev (1, 2, 3 ...) – uporabljajo se v `MATCH`.
- **2. vrstica:** imena stolpcev – opisi parametrov.
- **Od 3. vrstice naprej:** ena vrstica za vsako recepturo (eno velikost kolone). Prvi stolpec (`Receptura`) vsebuje oznako recepture, ki se uporablja kot ključ.


> **Opomba KL:** Ključi raztopin v stolpcih `Ključ 1`, `Ključ1`, `Ključ2` so vezani na oznake raztopin v IPO modulu RAZTOPINE. Prek teh ključev se raztopina v recepturi samodejno poveže s pripravljalnim dokumentom raztopine.

### 4.2 Primer: pretok iz `Podatki`

Formule pobirajo spodnjo (`Min. V`) in zgornjo (`Max. V`) mejo pretoka iz `Podatki` glede na izbrano velikost kolone.

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

### 4.4 Barvna označitev celic 

| Barva | Pomen |
|-------|-------|
| 🟡 **rumena** | naslovne vrstice (`Tip objekta = naslov`) |
| 🟠 **oranžna** | komentarji, opomniki za KL (niso del IPO izpisa) |
| ⬜ **siva** | celice z `INDEX/MATCH` formulami (samodejno berejo iz `Podatki`) |

### 4.5 Pomembno pri urejanju `Podatki`

> **Pozor:** V listu `Podatki` **ne brišite stolpcev**, le vsebino/vrednosti. Na stolpce so vezane formule v obeh receptura listih – če zbrišete stolpec, se formule `INDEX/MATCH` podrejo.

---

## 5. Obvezni stolpci

V prvi vrstici **morajo biti** naslednji stolpci – natanko s temi imeni (pazi na presledke in šumnike):

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

> **Opomba:** Na začetku in na koncu recepture je nekaj vrstic, ki so vezane na IPO sistem (npr. `Izpolni vodja`, `Vodja`, `Dodatna navodila` na vrhu).
Teh vrstic ne brišite!


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



## 7. Vrednosti polja `Tip podatka`

`Tip podatka` opisuje **vrsto vsebine**, ki se vnaša. Od tipa podatka je odvisna zahtevana vrednost v stolpcu `Labela`.

| Tip podatka | Opis | Zahtevana Labela | Najpogostejši Tip objekta |
|-------------|------|------------------|---------------------------|
| `kemikalija` | Kemikalija (vnos QR kode) | `koda` | `edit` |
| `raztopina` | Raztopina iz modula RAZTOPINE | `koda` | `edit` |
| `masa` | Masa ali volumen porabljene raztopine/kemikalije. **Točno `masa`** – `masa1` ni veljaven tip (številka sodi v `Ključ preverjanja`) | enota (`g`, `mL`, `kg`) | `edit`, `klictehtnice1` |
| `monolit` | Monolit (QR koda sestavka) | `koda` | `edit` |
| `zaposleni` | Operater/Vodja (QR koda zaposlenega) | `koda` | `edit` |
| `embalaza` | Embalaža | `koda` | `edit` |
| `repro` / `reproodpis` | Repro material / odpis | `koda` | `edit` |
| `tehtnica` | Tehtnica | `naziv opreme` | `spustniseznam` |
| `termometer` | Termometer | `naziv opreme` | `spustniseznam` |
| `pH_meter`, `kopel`, `sušilnik`, `vak_sušilnik`, `merilnik`, `naprava`, `avtoklav` | Ostala oprema | `naziv opreme` | `spustniseznam` |
| `HPLC`, `črpalka`, `volumen`, `tlak`, `dejanski_pretok`, `baza`, `popravek_ohisja`, `popravek_mon`, `dodatnanavodila` | Lastno definirani tipi (besedilni/številčni vnosi) | ustrezna enota ali prazno | `edit`, `memo`, `spustniseznam` |
| `checkbox` | Polje za kljukico | `DA (kljukica)` ali `DA (kljukica)/NE (prazno)` | `checkbox` |
| `datumcaszacetek` | Datum/čas začetka operacije | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `datumcaskonec` | Datum/čas konca operacije | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `datumcas` | Splošni datum/čas | `datum/čas` | `izberidatumcas`, `gumbdatumcas` |
| `formula`, `summasa`, `masakonec` | Izračunane vrednosti | enota | `formula`, `formula0`, `formula1` |
| `naslov` | Naslov sekcije/zavihka | *(prazno)* | `naslov` |
| `crta` | Ločnik | *(prazno)* | `crta` |

> **Pozor – voda:** Ko se uporablja voda, **tip podatka ni `masa`**, ker vode ne vnašamo v modul RAZTOPINE. Uporabite tip `volumen` z enoto `mL` in ključem `dH2O`. Pri kemikaliji/raztopini **ni dovoljen** `volumen` z istim ključem – tam mora biti `masa`.

> **Opomba:** Pri tipu `masa` **vedno** vnesete porabljeno količino – tudi če jo vpišete v mL, se iz gostote avtomatsko poračuna masa, ki se odšteje od zaloge raztopine.


## 8. Ključ preverjanja

`Ključ preverjanja` (stolpec F) je **identifikator koraka** za IPO. Uporablja se za:

- povezovanje **para kemikalija/raztopina – masa** (isti ključ označuje isti material),
- povezovanje **para repro – kolicina** (isti ključ označuje isti sestavni del),
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
| `kemikalija`, `raztopina`, `masa`, `datumcaszacetek`, `datumcaskonec` | **DA** |
| oprema (`tehtnica`, `termometer`, `HPLC` …) | **NE** – pri `Tip objekta = spustniseznam` je namesto ključa obvezen stolpec `Vrednost` (oznaka šifranta) |
| `naslov`, `crta`, `checkbox` | NE |
| `zaposleni` (vodja/operater) | NE (običajno) |


### 8.3 Podvajanje in oštevilčenje

- **Raztopine in kemikalije istega tipa** se oštevilčijo s številčno pripono (`GK1`, `GK2`, `GK3` ali `NaCl1`, `NaCl2` ...).
- Oštevilčenje se **začne z `1`** in poteka **brez vrzeli**.
- Masa mora imeti **enak ključ kot njena kemikalija/raztopina**, nad katero stoji (par).
- Kemikalija/raztopina **mora imeti** parno vrstico `masa` z istim ključem. Tip `volumen` z istim ključem **ni dovoljen**.
- **Izjema – voda:** pri ključu `dH2O` je parni tip `volumen`, ne `masa`.
- Kolicina mora imeti **enak ključ kot njen repro**, nad katerim stoji (par).


### 8.4 Parametri kontrol raztopine

Pri kontrolah `kontrolaveljavnostiraztopine` in `kontrolaustreznostiraztopine` mora biti `Par1` zapolnjen. **Ni potrebno**, da se `Par1` ujema s ključem preverjanja (niti z bazo ključa brez številčne pripone).

**Primer**:

```
Navodilo:           Raztopina 20% v/v EtOH
Tip podatka:        raztopina
Ključ preverjanja:  raz1
Labela:             koda
Tip objekta:        edit
Kontrola 2:         kontrolaveljavnostiraztopine
Kontrola 2 - par 1: 20v-EtOH-RR   ← ni treba, da se ujema s ključem raz1
```

---

## 9. Kontrole

Vsak korak ima **do 4 kontrole** (stolpci `Kontrola 1`–`Kontrola 4`). Vsaka kontrola ima:

- **ime kontrole** (stolpec `Kontrola N`)
- **parameter 1** (stolpec `Kontrola N - par 1`)
- **parameter 2** (stolpec `Kontrola N - par 2`)

Ime kontrole se piše z **malimi črkami brez presledkov in brez šumnikov**.

### 9.1 Seznam veljavnih kontrol

Spodaj so **vse dovoljene kontrole** (40 imen). Validator sprejme samo ta imena. Pišite jih z malimi črkami, brez presledkov in brez šumnikov. `kontrolainterval` in `kontrolaintervala` sta ista kontrola (oba zapisa sta dovoljena).

#### Splošne / vnos

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolapraznopolje` | Polje ne sme biti prazno (obvezen vnos). | *(prazno)* | *(prazno)* |
| `kontrolainterval` | Številska vrednost mora biti znotraj intervala. | spodnja meja | zgornja meja |
| `kontrolaintervala` | Enako kot `kontrolainterval` (dovoljen zapis). | spodnja meja | zgornja meja |
| `kontrolacasa` | Trajanje (v sekundah) med `datumcaszacetek` in `datumcaskonec`. | min sek | max sek |
| `kontrolarazlika` | Razlika med vrednostmi dveh korakov je v mejah. | referenca | meja |
| `aliisto` | Vrednost mora biti enaka drugemu koraku. | referenca (npr. `=C13`) | *(prazno)* |
| `kontrolaistizapis` | Vrednost mora biti isti zapis kot pri referenčnem koraku. | referenca | *(prazno)* |

#### Checkbox / pogoji / vloge

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `aliobkljukan` | Checkbox mora biti označen. | `DA` ali `NE` | *(prazno)* |
| `aliniobkljukan` | Checkbox ne sme biti označen. | `DA` ali `NE` | *(prazno)* |
| `aliobstajapogoj` | Polje je aktivno, če pogoj velja. | ključ sklopa `zaklenipolja` (npr. `sst_3` ali parni `sst_4`) ali referenca celice (`=$F$58`) | `0` ali `1` |
| `aliobstajapogoj_ali` | Pogoj z logiko ALI (vsaj eden od navedenih). | ključi ali referenca | `0` ali `1` |
| `zaklenipolja` | Zaklene naštete korake, če je polje označeno. | seznam številk korakov ločenih z vejico (npr. `45,46,47`) | *(prazno)* |
| `kdoizpolni` | Določa, kdo sme izpolniti polje. | `ROLE_HEAD` ali `ROLE_OPERATOR` | *(prazno)* |
| `alipravavloga` | Preverja vlogo operaterja. | `ROLE_HEAD` ali `ROLE_OPERATOR` | *(prazno)* |
| `alipravavlogakoda` | Preverja vlogo operaterja po kodi (QR). | `ROLE_HEAD` ali `ROLE_OPERATOR` | *(prazno)* |

> **Pozor – `aliobstajapogoj` in `zaklenipolja`:** V Par 1 pri `aliobstajapogoj` navedite **ključ sklopa `zaklenipolja`, ki ta korak zaklene**. Dovoljen je ključ vrstice, ki korak navaja v Param1 (npr. `sst_3` s Param2=`0`), ali parni ključ (npr. `sst_4` s Param2=`1`). Istega ključa ne uporabljajte pri dveh različnih sklopih zaklepanja.

#### Kemikalija / masa / embalaža

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolaveljavnostikemikalije` | Kemikalija mora biti veljavna. | *(prazno)* | *(prazno)* |
| `kontrolaustreznostikemikalije` | Kemikalija mora biti ustrezna. | *(prazno)* | *(prazno)* |
| `kontrolamase` | Masa mora biti v dovoljenih mejah (pogosto skupaj z `kontrolainterval`). | *(prazno)* | *(prazno)* |
| `kontrolarazmerjakemikalij` | Preverja razmerje med kemikalijami. | odvisno | odvisno |
| `kontrolaembalaze` | Embalaža mora biti veljavna. | *(prazno)* | *(prazno)* |
| `kontrolaprazneembalaze` | Preverja prazno embalažo. | *(prazno)* | *(prazno)* |

#### Oprema

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolaveljavnostiopreme` | Oprema mora biti veljavna (kalibrirana). | tip opreme (`HPLC`, `tehtnica`, `termometer`, `filter`) | *(prazno)* |
| `kontrolaustreznostiopreme` | Oprema mora biti primerna za postopek. | tip opreme | *(prazno)* |
| `kontrolaustreznostiopremeizmase` | Ustreznost opreme glede na maso (dovoljena tudi na `klictehtnice1`). | tip opreme | *(prazno)* |

#### Monolit / raztopina / repro

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolaveljavnostimonolita` | Monolit mora biti veljaven. | *(prazno)* | *(prazno)* |
| `kontrolaustreznostimonolita` | Monolit mora biti pravi tip (npr. sestavljen). | koda tipa ali seznam (`SES`, `MOD,SPIR`) | *(prazno)* |
| `kontrolaveljavnostiraztopine` | Raztopina mora biti v roku. | parameter kontrole (ni treba, da se ujema s ključem) | *(prazno)* |
| `kontrolaustreznostiraztopine` | Raztopina mora ustrezati šifri raztopine. | parameter kontrole (ni treba, da se ujema s ključem) | *(prazno)* |
| `kontrolaveljavnostirepro` | Repro mora biti veljaven. | šifra repro | *(prazno)* |
| `kontrolaustreznostirepro` | Repro mora biti ustrezen. | šifra repro | *(prazno)* |
| `kontrolaprimernostirepro` | Repro mora biti primeren za postopek. | prazno | *(prazno)* |
| `kontrolaprimernostitelesainpokrova` | Preverja primernost telesa in pokrova. | prazno | *(prazno)* |
| `prenosrepro` | Prenos repro v naslednji korak/postopek. | prazno | prazno |

#### Set / linija / monomer / ostalo

| Ime kontrole | Namen | Par 1 | Par 2 |
|--------------|-------|-------|-------|
| `kontrolaveljavnostiseta` | Set mora biti veljaven. | šifra seta | *(prazno)* |
| `kontrolaustreznostiseta` | Set mora biti ustrezen. | šifra seta | *(prazno)* |
| `prenosset` | Prenos seta v naslednji korak/postopek. | šifra seta | odvisno |
| `kontrolaustreznostilinije` | Linija mora biti ustrezna. | prazno | *(prazno)* |
| `kontrolaveljavnostimonomerne` | Monomerna mora biti veljavna. | oznaka MM | *(prazno)* |
| `kontrolaustreznostimonomerne` | Monomerna mora biti ustrezna. | oznaka MM | *(prazno)* |
| `odpispraznemm` | Odpis prazne merilne mase / prazne MM. | prazno | prazno |

> **Pozor – `kontrolainterval` je odprti interval:** Če SOP zahteva npr. `3.2 ≤ x ≤ 4.2`, potem vpišemo `Par1 = 3.1`, `Par2 = 4.3`. Če SOP piše `> 24 ur`, ne pustite neskončne zgornje meje – izberite realno mejo (npr. `72 ur`, tj. `259200` sekund).

> **Pozor – enote:** V parametre kontrole vpisujete **samo številčne vrednosti brez enot**. Enota je v stolpcu `Labela`.

> **Pozor – decimalno ločilo:** V številkah uporabljajte **piko** (`6.5`), ne vejice (`6,5`). 



## 10. Vloge operaterjev (`ROLE_HEAD`, `ROLE_OPERATOR`)

Sistem IPO loči dve vlogi za izpolnjevanje recepture:

| Vloga | Opis | Tipična uporaba |
|-------|------|-----------------|
| `ROLE_HEAD` | Vodja (višja odgovornost) | Potrditve, dodatna navodila, odobritve |
| `ROLE_OPERATOR` | Operater (izvajalec postopka) | Operativni vnosi, odčitki, čas, meritve |

### Vezava vloge na korak

1. **`alipravavlogakoda`** – preveri, da ima oseba, ki skenira QR kodo, zahtevano vlogo.
2. **`kdoizpolni`** – določi, da to polje lahko izpolni **samo oseba s to vlogo** (ostale so zaklenjene).


## 11. Posebni tipi vrstic

### 11.1 `naslov`

- Označuje **začetek sekcije ali zavihka**.
- V Excelu je **rumena vrstica**.
- **Mora imeti** številko koraka (`št. Koraka`) in besedilo naslova (`Navodilo`); ostalo je prazno.
- `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, …) – enako kot pri `crta`.
- **Nikoli** ne dodajajte `kontrolapraznopolje` na naslov.


### 11.2 `crta`

- Vizualni **ločnik med sklopi**. V IPO se izpiše kot vodoravna črta.
- **Mora imeti svojo številko koraka.**
- `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, …).
- Ostali stolpci so prazni.
- **Nikoli** ne dodajajte `kontrolapraznopolje` na črto.


### 11.3 `checkbox`

- Polje za kljukico.
- `Labela` mora biti **natanko ena** od dveh vrednosti:
  - `DA (kljukica)` – obvezna kljukica
  - `DA (kljukica)/NE (prazno)` – DA ali NE
- Pri obveznem DA dodajte `aliobkljukan` s `Par1 = DA`.
- **Nikoli** ne dodajajte `kontrolapraznopolje` na checkbox.


### 11.4 `spustniseznam`

- Dropdown, povezan s **šifrantom IPO**.
- V stolpec `Vrednost` vpišite oznako šifranta (npr. `HPLC`, `tehtnica`, `TEH-KLA`). To določi, kateri seznam se prikaže operaterju.
- V `Labela` vpišite `naziv opreme`.


### 11.5 `izberidatumcas` / `gumbdatumcas` (datum/čas)

- Polje za izbiro datuma in časa (koledarček).
- `Labela` = `datum/čas`.
- Par začetek–konec mora imeti **enak ključ preverjanja** in na koncu dodano `kontrolacasa`.


### 11.6 `formula`, `formula0`, `formula1`, `formula2`

- Izračunano polje v sistemu IPO.
- V stolpec `Vrednost` vpišete **Excelovo formulo kot besedilo**, ki zgradi IPO formulo s `$` pred številkami korakov:

```
="=($"&C113&"-"&"$"&C108&")/($"&C108&"-$"&C89&")"
```

> Ta formula se sklicuje na korake 113, 108 in 89. IPO nato sam izračuna rezultat po tej formuli.

- Formula mora vsebovati **znak `$`** (sklic na korak). 
- Sklicujete se lahko samo na korake tipa `edit`, `formula`, `formula0`, `formula1`. Ne na `naslov`, `crta`, `checkbox`.

| Tip | Zaokroževanje |
|-----|---------------|
| `formula` | brez |
| `formula0` | celo število |
| `formula1` | 1 decimalno mesto |
| `formula2` | 2 decimalni mesti |


