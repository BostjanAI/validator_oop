# Kratka navodila za pripravo recepture (za nove sodelavce)

**Namenjeno:** novim tehnologom v KL  
**Obseg:** prvi dan dela z Excel recepturo za IPO  
**Podrobnosti:** [NAV-157 – Navodila za pripravo recepture](NAV-157_Navodila_KL_priprava_recepture.md)  
**Validacija:** [NAV-158 – Uporaba validatorja](../Navodila_Validator/NAV-158_Navodila_Validator.md)

---

## 1. Kaj je receptura

Receptura je Excel datoteka **`.xlsm`** (Excel z makri). Vsaka vrstica je en korak postopka, ki ga operater vidi v sistemu IPO: naslov, vnosno polje, spustni seznam, checkbox, datum/čas ali črta.

Pred predajo mora biti datoteka preverjena z **IPO Validatorjem**.

> **Ne začenjajte od nič.** Skopirajte obstoječo recepturo istega tipa (isti postopek, druga velikost), preimenujte datoteko, zamenjajte kodo recepture in nato spreminjajte samo tisto, kar je treba.

---

## 2. Kako začeti

1. Skopirajte vzorčno ali obstoječo recepturo iste kemije/postopka.
2. Odprite `.xlsm` in **omogočite makre**.
3. V listu `Podatki` vnesite vrstico za novo velikost (koda, pretoki, volumni, ključi raztopin).
4. V listu `Receptura` (ali `Receptura_2`) v celico **`$A$2`** vpišite kodo recepture (npr. `R-A-800-TES-SDVB`).
5. Po potrebi dodajte ali uredite korake (glejte razdelek 7).
6. Shranite kot `.xlsm` (makri morajo ostati).
7. Zaženite **IPO Validator** in odpravite napake.

---

## 3. Štirje listi v datoteki

| List | Kaj je | Urejate? |
|------|--------|----------|
| `Spremembe` | Dnevnik sprememb (makro) | **NE** – nikoli ročno, ne brišite |
| `Receptura` | Postopek **brez** zavihkov (en seznam korakov) | DA |
| `Receptura_2` | Postopek **z** zavihki (sklopi, npr. več palic) | DA, če potrebujete zavihke |
| `Podatki` | Parametri po velikosti kolone | DA – **ne brišite stolpcev** |

**Kdaj kateri list:**

- `Receptura` – običajno (tudi GMP). Stolpec `Zavihek` je prazen, koraki tečejo od 1 naprej skozi cel postopek.
- `Receptura_2` – kadar na istem DN testirate več kolon/palic. Vsak zavihek začne korake znova od `1`. Za GMP se praviloma **ne** uporablja.

Na začetku in na koncu lista **ne brišite** standardnih vrstic (`Izpolni vodja`, `Vodja`, `Dodatna navodila`, info o monolitu) – vezane so na IPO.

---

## 4. List `Podatki`

Tu so številke, ki se razlikujejo po velikosti kolone: pretoki, volumni, vzorci, ključi raztopin, tolerance.

- Ena vrstica = ena receptura/velikost.
- Oznaka v stolpcu A (npr. `R-A-4-TES-SDVB`): **R** receptura, **A** pore, **4** velikost, **TES** testiranje, **SD** kemija.
- `Ključ1` / `Ključ2` sta oznaki raztopin iz modula RAZTOPINE.
- **Stolpcev ne brišite**, samo vsebino. Na stolpce so vezane formule `INDEX/MATCH` v recepturi – če zbrišete stolpec, se formule podrejo.

Parametre v navodilih in kontrolah **ne vpisujte na roke**. Berite jih iz `Podatki`:

```
=INDEX(Podatki!$A:$BZ, MATCH($A$2, Podatki!$A:$A, 0), <številka_stolpca>)
```

Te celice obarvajte **sivo**.

---

## 5. Barve v recepturi

| Barva | Pomen |
|-------|--------|
| rumena | naslovna vrstica (`Tip objekta = naslov`) |
| siva | formula `INDEX/MATCH` (bere iz `Podatki`) |
| oranžna | komentar / opomnik za KL – **ne gre v IPO** |

---

## 6. Stolpci – kaj kam spada

Vrednosti v tehničnih stolpcih pišite **z malimi črkami, brez presledkov in brez šumnikov** (`spustniseznam`, ne `spustni seznam`). Izjema: `Navodilo` in `Labela`.

| Stolpec | Ime | Kratko |
|---------|-----|--------|
| A | koda recepture | V `$A$2` je koda, ki jo `INDEX/MATCH` išče v `Podatki`. |
| B | `Zavihek` | Prazen pri `Receptura`. Pri `Receptura_2`: koda samo v prvi vrstici sklopa, naprej `=B_prej`. |
| C | `št. Koraka` | Formula `=C_prej+1`. Tudi vrstica `crta` **mora** imeti številko. Pri novem zavihku vpišite `1` (ne formulo). |
| D | `Navodilo` | Besedilo za operaterja; sledite SOP. Številke po velikosti kolone prek `INDEX/MATCH`. |
| E | `Tip podatka` | Kaj podatek je: `raztopina`, `masa`, `zaposleni`, `monolit`, `checkbox`, `HPLC`, `tehtnica` … |
| F | `Ključ preverjanja` | Identifikator koraka. Brez presledkov in šumnikov. Isti ključ veže par (raztopina–masa, začetek–konec časa). |
| G | `Vrednost` | Šifrant opreme (`HPLC`, `TEH-KLA`), koda raztopine ali formula za izračun. |
| H | `Labela` | Kaj vidi operater levo od polja: `koda`, `naziv opreme`, `mL/min`, `DA (kljukica)`, `datum/čas`. |
| I | `Tip objekta` | UI v IPO: `naslov`, `edit`, `crta`, `spustniseznam`, `checkbox`, `memo`, `formula0`/`formula1`, `izberidatumcas`. |
| J–U | Kontrole 1–4 | Preverjanje vnosa v IPO (interval, prazno polje, veljavnost opreme/raztopine …). |

### Pogoste kombinacije

**Raztopina** – `Tip podatka = raztopina`, `Labela = koda`, `Tip objekta = edit`.  
Kontrole: `kontrolaveljavnostiraztopine` + `kontrolaustreznostiraztopine` (Par 1 = baza ključa **brez** `1`/`2`/`3`) + `kontrolapraznopolje`.  
Takoj za njo pride **masa** z **istim ključem** (`Tip podatka = masa`), da se poraba odšteje od zaloge. Porabo vpišete v mL; masa se izračuna iz gostote.

**Voda** ni `masa` (ni v modulu RAZTOPINE) – uporabite `volumen`.

**Oprema** – `Tip objekta = spustniseznam`, `Vrednost` = oznaka šifranta, `Labela = naziv opreme`.  
Kontrole: `kontrolaveljavnostiopreme` + `kontrolaustreznostiopreme` + `kontrolapraznopolje`.

**Checkbox** – `Labela` natanko `DA (kljukica)` ali `DA (kljukica)/NE (prazno)`.  
Kontrola: `aliobkljukan` / `zaklenipolja`. **Brez** `kontrolapraznopolje`.

**Naslov / črta** – brez kontrol. **Brez** `kontrolapraznopolje`. Črta ima prazno navodilo in svojo številko koraka.

**Vnosno polje** (`edit`, `spustniseznam`, `memo`, datum/čas) – vedno ima `kontrolapraznopolje` (običajno v zadnji prosti reži).

---

## 7. Dodajanje novega koraka

1. Vstavite **celo vrstico** nad mestom, kjer želite nov korak.
2. V `št. Koraka` vpišite `=C_prejšnja+1` (številčenje spodaj se popravi samo).
3. Pri `Receptura_2` v `Zavihek` vpišite `=B_prejšnja`.
4. Izpolnite Navodilo → Tip podatka → Ključ → Vrednost → Labela → Tip objekta → kontrole.
5. Obarvajte celice (rumeno / sivo / oranžno).
6. Shranite in zaženite validator.

---

## 8. Zlata pravila

1. Pišite **točno** kot v seznamu (`spustniseznam`, `kontrolapraznopolje`, `št. Koraka`).
2. Decimalno ločilo je **pika** (`6.5`), ne vejica. Večina vejic v kontrolah pomeni seznam korakov (`45,46,47`).
3. Ključi: samo `A–Z a–z 0–9 - _ .`
4. Raztopine istega tipa oštevilčite `GK1`, `GK2`, `GK3` – od 1 naprej, brez vrzeli. Masa ima **isti** ključ kot raztopina.
5. `kontrolainterval` je **odprt** interval: za SOP `[3.2, 4.2]` vpišite `3.1` in `4.3`. Samo številke, brez enot.
6. `kontrolacasa` je v **sekundah** (npr. 60 min ± 10 s → `3590` / `3610`).
7. Za raztopine v postopku najprej pripravite recepture v modulu **RAZTOPINE**, nato jih vežite s ključem.
8. Po vsaki spremembi zaženite validator.

---

## 9. Validacija pred predajo

1. Odprite IPO Validator → izberite `.xlsm` → **Zaženi validacijo**.
2. V poročilu preglejte vse **ERROR**. **WARNING** preglejte in uredite po presoji.
3. Popravite, shranite, ponovno validirajte.
4. Validator je pomoč – vsako napako še vedno **sami preverite** (nekateri intervali so po SOP širši).

Pogoste prve napake: napačno črkovanje tipa objekta, manjkajoča `kontrolapraznopolje`, `crta` brez številke koraka, presledek v ključu, masa brez raztopine z istim ključem, `Par 1` pri raztopini z `GK1` namesto baze `GK`.

---

## 10. Kam po več

| Vprašanje | Dokument |
|-----------|----------|
| Vsi tipi, kontrole, primeri vrstic | NAV-157 (ta mapa) |
| Kako zagnati validator in kaj pomeni koda napake | NAV-158 |
| Vzorčna datoteka | `Receptura.xlsm` v tej mapi |

Če niste prepričani, vprašajte mentorja **preden** brišete vrstice ali stolpce.
