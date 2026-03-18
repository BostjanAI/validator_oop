# Navodila za pripravo recepture za IPO sistem

**Dokument:** Navodila za tehnologe  
**Datum:** 9. 3. 2026  
**Verzija:** 1.1

---

## 1. Uvod

Receptura za IPO sistem je Excel datoteka s končnico `.xlsm` (Excel z makri). Vsebuje natanko **štiri liste (zavihke)**:

| List | Namen |
|------|--------|
| `Spremembe` | Avtomatski dnevnik sprememb (tega se ne ureja ročno) |
| `Receptura` | Glavni list z vsemi koraki postopka **brez zavihkov** (en neprekinjen seznam) |
| `Receptura_2` | Alternativni list z vsemi koraki postopka **z zavihki** (koraki so ločeni po sklopih/zavihkih) |
| `Podatki` | Parametri za vsako velikost recepture (tehnični parametri) |

> **Pozor:** Lista `Spremembe` se posodablja samodejno z makri. Vanjo nikoli ne pišete ročno.

---

## 2. Dve vrsti recepturnih listov: z zavihki in brez

Sistem IPO podpira dve varianti zapisa recepture. Izberete **eno ali drugo**, odvisno od tega, ali so koraki v sistemu razdeljeni po zavihkih (ločenih sklopih) ali ne.

---

### 2.1 List `Receptura` – brez zavihkov

V tej varianti **stolpec `Zavihek` ostane prazen** v vseh vrsticah. Koraki tečejo **neprekinjeno od 1 naprej** skozi celoten postopek. V sistemu IPO bo vse prikazano kot en nepretrgani seznam brez ločenih zavihkov.

**Kdaj uporabiti:** Ko je postopek enostaven in ga ne delite v ločene sklope.

**Primer (iz `Receptura`):**

| Zavihek | šft. Koraka | Navodilo | Tip podatka | Ključ preverjanja | ... |
|---------|------------|----------|-------------|-------------------|-----|
| *(prazno)* | 1 | `=INDEX(Podatki!...)` | *(prazno)* | *(prazno)* | naslov |
| *(prazno)* | `=C2+1` | Izpolni vodja | *(prazno)* | *(prazno)* | naslov |
| *(prazno)* | `=C3+1` | Vodja | zaposleni | *(prazno)* | koda |
| *(prazno)* | `=C4+1` | Dodatna navodila | dodatnanavodila | *(prazno)* | edit |
| *(prazno)* | `=C5+1` | *(prazno)* | *(prazno)* | *(prazno)* | crta |
| ... | ... | ... | ... | ... | ... |
| *(prazno)* | `=C12+1` | HPLC | HPLC | `tk_1` | spustniseznam |
| *(prazno)* | `=C13+1` | HPLC črpalka | črpalka | `tk_1` | edit |

> **Opomba:** V tej varianti se za logično organizacijo korakov v stolpcu `Ključ preverjanja` pogosto dodajajo skupinske kode (npr. `tk_1`, `pm1_1`, `locba_1`). To **ni** isti stolpec kot `Zavihek` – gre za ključ za validacijo, ne za prikaz zavihkov v sistemu IPO.

---

### 2.2 List `Receptura_2` – z zavihki

V tej varianti so koraki **razdeljeni v ločene zavihke** (sklope). Vsak zavihek ima:
- Svojo **kodo** v stolpcu `Zavihek` (stolpec B)
- Lastno **številčenje korakov od 1 naprej**
- Začetno vrstico tipa `naslov`, ki označuje začetek novega zavihka

V sistemu IPO bo vsak sklop prikazan kot **ločen zavihek** (tab), med katerimi operater preklaplja.

**Kdaj uporabiti:** Ko je postopek razdeljen v jasno ločene sklope (npr. po palicah, po korakih postopka, po dnevih ...).

#### Pravila za zavihke

**Začetek novega zavihka (prva vrstica sklopa):**
- `Zavihek` (stolpec B) = **nova koda zavihka** (npr. `monolito1`, `monolito2`)
- `šft. Koraka` = `1` *(celo število, ne formula – vsak zavihek šteje od 1)*
- `Navodilo` = Naslov zavihka (npr. "Zavihek za 1. palico")
- `Tip objekta` = `naslov`
- Vse kontrole: prazne

**Naslednje vrstice znotraj istega zavihka:**
- `Zavihek` (stolpec B) = `=B_prejšnja_vrstica` *(formula, ne ročno vpisana vrednost)*
- `šft. Koraka` = `=C_prejšnja_vrstica+1`

**Primer (iz `Receptura_2`):**

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
| ... | ... | ... | ... |

> **Pomembno:** Koda zavihka (npr. `monolito1`) se vpiše **samo enkrat** – v prvi vrstici tega zavihka. Vse naslednje vrstice tega zavihka imajo formulo `=B_prej`. S tem je zagotovljeno, da se koda samodejno prenese.

---

## 3. List `Podatki` – parametri recepture

List `Podatki` vsebuje vrstice za vsako posamezno **velikost recepture** (npr. R-A-4-TES-SDVB, R-A-8-TES-SDVB, R-A-80-TES-SDVB ...). Prva vrstica je glava s stolpci.

### Struktura stolpcev v listu `Podatki`

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
| AJ – `Max ε (mL/min) / max lΔp (bar) A,C` | Maks. pretok/tlak A,C | `1600 mL/min / ≤ 14 bar` |
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

---

## 4. Obvezni stolpci (oba lista)

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

---

## 5. Številčenje korakov (`šft. Koraka`)

- **Brez zavihkov (`Receptura`):** Koraki se številčijo od 1 naprej **skozi celotno recepturo**. Nikoli se ne začnejo znova.
- **Z zavihki (`Receptura_2`):** Koraki se številčijo od 1 naprej **znotraj vsakega zavihka posebej**. Ko se začne nov zavihek, se številčenje ponastavi na `1`.
- Priporoča se uporaba Excelove formule: `=C_prej+1` (naslednja vrstica dobi vrednost prejšnje +1).
- Vsaka vrstica mora imeti edinstveno številko v svojem obsegu – **podvojene in manjkajoče vrednosti niso dovoljene**.
- Prazne ločilne vrstice (`crta`) **morajo imeti** svojo številko koraka.

---

## 6. Tip objekta (`Tip objekta`) – dovoljene vrednosti

`Tip objekta` določa, kateri UI-element bo prikazan operaterju v sistemu IPO.

| Vrednost | Opis | Kdaj uporabiti |
|----------|------|----------------|
| `naslov` | Naslov razdelka (bold besedilo) | Za označitev začetka nove sekcije ali zavihka |
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

---

## 7. Tip podatka (`Tip podatka`) – dovoljene vrednosti

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

---

## 8. Ključ preverjanja (`Ključ preverjanja`)

- Vsak korak, ki zbira podatke, **mora imeti ključ preverjanja** (razen `naslov`, `crta` in `checkbox` brez obveznega vnosa).
- Ključ je **identifikator** tega koraka za sistem IPO.
- **Dovoljeni znaki:** samo `A-Z`, `a-z`, `0-9`, `-`, `_`, `.` – brez presledkov, šumnikov ali posebnih znakov.
- Primeri veljavnih ključev: `pretok_mf1`, `tehtnica_1`, `2.73mp-NaCl_13.87mp-EtOH-GK`, `locba_1`
- **Podvojevanje ključev:** Isti tip podatka (raztopina, kemikalija, masa ...) ne sme imeti enakih ključev v istem zavihku. Numerično pripono (npr. `GK1`, `GK2`) je treba povečevati.
- Za raztopino se ključ preverjanja ujema z **oznako raztopine** v sistemu IPO.

---

## 9. Vrednost (`Vrednost`)

- Vsebuje privzeto vrednost polja ali Excelovo formulo.
- Za **raztopino ali kemikalijo**: koda raztopine (npr. `2.73mp-NaCl_13.87mp-EtOH-GK`).
- Za **opremo**: koda tipa opreme (npr. `HPLC`, `TEH-KLA`, `TERM`).
- Za **checkbox**: prazno ali `DA`.
- Za **izračunana polja** (`formula0`, `formula1`): Excelova formula, npr.:
  `="=($"&C100&"+"&"$"&C99&")"` – formula, ki se sklicuje na koraka 100 in 99.
- Vrednost je **neobvezna** za `naslov`, `crta`, polja brez privzete vrednosti.

---

## 10. Labela (`Labela`)

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

---

## 11. Kontrole (`Kontrola 1` do `Kontrola 4`)

Vsak korak ima lahko **do 4 kontrole**. Vsaka kontrola ima:
- **ime kontrole** (stolpec `Kontrola N`)
- **parameter 1** (stolpec `Kontrola N - par 1`)
- **parameter 2** (stolpec `Kontrola N - par 2`)

### 11.1 Seznam veljavnih kontrol

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

### 11.2 Najpogostejše kombinacije kontrol

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

---

## 12. Vloge operaterjev

V kontrolah `alipravavlogakoda` in `kdoizpolni` se navede ime vloge iz sistema:

| Koda vloge | Opis |
|------------|------|
| `ROLE_HEAD` | Vodja (šef izmene) |
| `ROLE_OPERATOR` | Operater |

---

## 13. Posebni tipi vrstic

### 13.1 Naslov razdelka / začetek zavihka (`naslov`)

```
Zavihek:     nova koda zavihka (pri Receptura_2) ali prazno (pri Receptura)
Navodilo:    Besedilo naslova
Tip podatka: (prazno)
Tip objekta: naslov
Vse kontrole: (prazne)
```

### 13.2 Ločnik (`crta`)

```
Zavihek:     =B_prejšnja (ali prazno)
Navodilo:    (prazno)
Tip podatka: (prazno)
Tip objekta: crta
Vse kontrole: (prazne)
```

### 13.3 Checkbox

```
Navodilo:    Besedilo potrditve (ali Excelova formula)
Tip podatka: checkbox
Labela:      DA (kljukica)   ALI   DA (kljukica)/NE (prazno)
Tip objekta: checkbox
Kontrola 1:  aliobkljukan  |  Par 1: DA
```

### 13.4 Spustni seznam (oprema)

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

### 13.5 Datum/čas

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

### 13.6 Formula

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

---

## 14. Excelove formule v poljih `Navodilo` in `Vrednost`

Excelove formule se pogosto berejo parametre iz lista `Podatki`. Tipična formula:
```excel
=INDEX(Podatki!$A:$BZ, MATCH($A$2, Podatki!$A:$A, 0), 4)
```
- `$A$2` vsebuje kodo recepture (npr. `R-A-800-TES-SDVB`)
- `MATCH(...)` najde vrstico v `Podatki`
- Četrti argument `4` je stolpec D (pretok)

To omogoča, da se isto navodilo prilagodi za vsako velikost recepture – **ne pisati ročno vrednosti v navodila**.

---

## 15. Pravila za ključe kontrole raztopine

Ko je `Tip podatka` = `raztopina`:
- `Ključ preverjanja` je **unikatna koda** (npr. `2.73mp-NaCl_13.87mp-EtOH-GK1`)
- V kontroli `kontrolaveljavnostiraztopine` je **Par 1 = baza ključa brez numerične pripone** (npr. `2.73mp-NaCl_13.87mp-EtOH-GK`)
- To pomeni: če imate 3 enake raztopine z ključi `GK1`, `GK2`, `GK3` – vse tri imajo isto Par 1 = `GK` (brez številke)

---

## 16. Tipične napake in kako jih odpraviti

| Napaka | Vzrok | Rešitev |
|--------|-------|---------|
| `TIP_OBJEKTA_UNKNOWN` | Napačno zapisana vrednost v `Tip objekta` | Preverite črkovanje (npr. `spustniseznam` ne `spustni seznam`) |
| `CTRL_UNKNOWN` | Napačno ime kontrole | Preverite, ali je kontrola v seznamu veljavnih kontrol |
| `STEP_DUPLICATE` | Dve vrstici imata isto `šft. Koraka` | Preverite formule (pri recepturi z zavihki se vsak zavihek začne z 1) |
| `STEP_GAPS` | Manjkajoči koraki v zaporedju | Vrstice z `crta` morajo imeti svojo številko koraka |
| `CTRL_INTERVAL_PARAMS` | Pri `kontrolainterval` manjkajo Par 1 ali Par 2 | Vedno vnesite obe meji |
| `CTRL_EXPECTED_MISSING` | Za raztopino manjka validacijska kontrola | Dodajte `kontrolaveljavnostiraztopine` in `kontrolaustreznostiraztopine` |
| `LABELA_KODA` | Za `zaposleni`/`kemikalija`/`monolit` labela ni `koda` | Nastavite `Labela` = `koda` |
| `KEY_FORMAT` | Ključ vsebuje prepovedane znake | Odstranite presledke, šumnike, posebne znake |
| `ZAKLENI_PAR1_FORMAT` | Par 1 pri `zaklenipolja` ni seznam celih števil | Vnesite npr. `45,46,47` – samo številke, ločene z vejicami |

---

## 17. Korak po korak: dodajanje novega koraka

1. **Odločite se za varianto** – ali lista `Receptura` (brez zavihkov) ali `Receptura_2` (z zavihki).
2. **Če z zavihki:** preverite, ali ste v pravilnem zavihku (stolpec B mora imeti pravo kodo ali formulo `=B_prej`).
3. **Nastavite številko koraka** – formula `=C_prejšnja+1`; pri novem zavihku napišite `1`.
4. **Vpišite navodilo** – besedilo ali Excelova formula.
5. **Izberite Tip podatka** – glejte razdelek 7.
6. **Določite Ključ preverjanja** – unikaten identifikator brez presledkov.
7. **Vpišite Vrednost** – koda opreme, raztopine ali formula.
8. **Nastavite Labelo** – enota ali oznaka prikaza.
9. **Izberite Tip objekta** – ustreza tipu podatka (glejte razdelek 6).
10. **Dodajte kontrole** – glede na tip podatka (glejte razdelek 11).
11. **Shranite in zaženite validator** – preverite, da ni napak.

---

## 18. Primeri

### Primer A – meritev pretoka (brez zavihkov)

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

---

### Primer B – začetek novega zavihka (Receptura_2)

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

---

### Primer C – koda monolita (Receptura_2, znotraj zavihka)

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

---

### Primer D – SST checkbox z zaklepanjem (dinamičen seznam)

| Stolpec | Vrednost |
|---------|----------|
| Tip podatka | `checkbox` |
| Labela | `DA (kljukica)/NE (prazno)` |
| Tip objekta | `checkbox` |
| Kontrola 1 | `zaklenipolja` |
| Kontrola 1 - par 1 | `=C58&","&C60&","&C61&","&C63&","&C64&","&C65` |
| Kontrola 2 | (prazno) |

---

### Primer E – pogojno polje z ključem (Receptura_2)

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

---

## 19. Validacija recepture

Po dokončani pripravi recepture je treba datoteko **validirati z IPO validatorjem**:

1. Odprite aplikacijo IPO Validator.
2. Naložite datoteko `.xlsm`.
3. Preverite poročilo napak.
4. Odpravite vse napake tipa **error** (napake vrste **warning** so opozorila, ne blokirajo).
5. Ponovite validacijo do `"is_valid": true`.

---

*Navodila so bila pripravljena na podlagi analize vzorčnih receptur `Receptura.xlsm` (listi `Receptura` in `Receptura_2`).*
