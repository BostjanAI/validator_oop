# Pravila validatorja – pregled in opis

Validator OOP izvaja **42 validacijskih pravil**, razporejenih v 4 module. Vsako pravilo preverja določen vidik Excel recepture (IPO datoteke) in ob kršitvi javi napako ali opozorilo.

---

## Kazalo

1. [Strukturna pravila](#1-strukturna-pravila-structural)
2. [Pravila polj](#2-pravila-polj-field)
3. [Relacijska pravila](#3-relacijska-pravila-relational)
4. [Pravila kontrol](#4-pravila-kontrol-control)

---

## 1. Strukturna pravila (`structural`)

### 1.1 Obvezni stolpci

Preverja, da ima vsak list (zavihek) recepture vse predpisane stolpce (`REQUIRED_COLUMNS`).

| | |
|---|---|
| **Preverja** | Prisotnost vseh obveznih stolpcev v glavi lista |
| **Napaka** | `MANJKA_STOLPEC` – navede ime manjkajočega stolpca |
| **Resnost** | ERROR |

---

### 1.2 Številčenje korakov

Preverja pravilnost vrednosti v stolpcu `št. Koraka`.

| | |
|---|---|
| **Preverja** | Vrednost je celo število; ni duplikatov znotraj zavihka; prvi korak je 1; ni vrzeli v zaporedju; korak ni prazen, če vrstica vsebuje podatke; koraki so v naraščajočem fizičnem vrstnem redu |
| **Napake** | `KORAK_NI_CELO` – vrednost ni celo število |
| | `KORAK_MANJKA` – korak manjka pri vrstici s podatki |
| | `KORAK_PODVOJEN` – podvojena številka koraka |
| | `KORAKI_ZAVIH_NE_1` – zavihek ne začne s korakom 1 |
| | `KORAK_PRESLEDKI` – vrzel v zaporedju (npr. 1, 2, 4 …), preverja se tudi kadar koraki ne začnejo pri 1 |
| | `STEP_OUT_OF_ORDER` – korak se v Excelu pojavi pred višje oštevilčenim korakom (npr. 12, 11, 10) |
| **Opomba** | Duplikati in začetek pri 1 se preverita ločeno po zavihkih; vrstni red se prav tako preverja po zavihkih |

---

## 2. Pravila polj (`field`)

### 2.1 Tip objekta

Preverja, da je vrednost v stolpcu `Tip objekta` veljavna in ne prazna.

| | |
|---|---|
| **Preverja** | Stolpec `Tip objekta` – neprazen, vrednost iz dovoljenega nabora (`ALLOWED_TIP_OBJEKTA`) |
| **Napake** | `TIP_OBJEKTA_PRAZEN` – polje je prazno |
| | `TIP_OBJEKTA_NEZNAN` – vrednost ni v dovoljenem naboru |

---

### 2.2 Združljivost tipa podatka in tipa objekta

Preverja, da je kombinacija `Tip podatka` + `Tip objekta` smiselna glede na predpisano preslikavo.

| | |
|---|---|
| **Preverja** | Če `Tip podatka` ∈ `STANDARD_TIP_PODATKA`, mora biti `Tip objekta` v `DATA_OBJECT_MAPPING[tip]` |
| **Napaka** | `TIP_NE_USREZA` – `Tip objekta` ni ustrezen za dani `Tip podatka` |

---

### 2.2.1 Tip podatka `masa`

Preverja, da je masa zapisana točno kot `masa`, ne kot oštevilčena različica.

| | |
|---|---|
| **Preverja** | `Tip podatka` ne sme biti `masa1`, `masa2`, `masa_1` ipd.; dovoljena je samo vrednost `masa` (številka sodi v `Ključ preverjanja`) |
| **Napaka** | `DATA_TYPE_MASA_INVALID` – oštevilčen tip podatka za maso ni veljaven |
| **Opomba** | Tipi `masakonec` in `summasa` ostanejo veljavni |

---

### 2.2.2 Tip podatka `posebnosti` / `posebnostimon`

Preverja, da tip podatka za posebnosti ustreza stolpcu `Zavihek` v isti vrstici.

| | |
|---|---|
| **Preverja** | Če je v isti vrstici v `Zavihek` vpisano `monolit1`, `monolit2`, …, mora biti tip `posebnostimon`. Sicer mora biti tip `posebnosti`. Velikost črk ni pomembna. |
| **Napake** | `DATA_TYPE_POSEBNOSTI_REQUIRED` – v isti vrstici `Zavihek` ni `monolit1`, `monolit2`, …, `Tip podatka` pa je `posebnostimon` |
| | `DATA_TYPE_POSEBNOSTIMON_REQUIRED` – v isti vrstici je `Zavihek` `monolit1`, `monolit2`, …, `Tip podatka` pa je `posebnosti` |
| **Opomba** | Ostali tipi podatka se ne preverjajo. Zavihek v drugi vrstici ne šteje. Formula, poljubno besedilo, `monolit` brez številke ali vrednost s presledkom niso koda monolita. |

---

### 2.3 Zahteve za Labelo

Preverja pravilno vrednost in enoto v stolpcu `Labela`.

| | |
|---|---|
| **Preverja** | Pri tipih, ki zahtevajo `koda` v Labeli (`LABELA_KODA_TYPES`), mora biti normalizirana vrednost enaka `koda`; enota v `Labela` se mora ujemati z enoto v `Navodilo`, kadar obe vsebujeta številčno vrednost z enoto |
| **Napake** | `LABELA_MORA_KODA` – Labela ni `koda`, čeprav je zahtevana |
| | `ENOTA_NE_USREZA` – enota v Labeli se ne ujema z enoto v Navodilu |

---

### 2.4 Labela pri checkboxu

Preverja dovoljene vrednosti Labele za polja tipa checkbox.

| | |
|---|---|
| **Preverja** | Kadar je `Tip objekta` = `checkbox`, mora biti `Labela` ena izmed dovoljenih vrednosti (`LABELA_CHECKBOX_ALLOWED`) |
| **Napaka** | `LABELA_CHECKBOX_OBLIKA` – Labela ni dovoljena vrednost za checkbox |

---

### 2.5 Vrednost pri spustnem seznamu

Preverja, da je stolpec `Vrednost` zapolnjen pri poljih tipa spustni seznam.

| | |
|---|---|
| **Preverja** | Kadar je `Tip objekta` = `spustniseznam`, mora biti `Vrednost` neprazna (oznaka šifranta, npr. `HPLC`, `tehtnica`). Pri opremi je `Vrednost` obvezna namesto ključa preverjanja. |
| **Napaka** | `SPUSTNISEZNAM_VREDNOST_EMPTY` – vrednost manjka pri spustnem seznamu |

---

### 2.6 Prazni stolpci pri ločniku (`crta`)

Preverja, da vrstice tipa ločnik ne vsebujejo podatkov v drugih stolpcih, številka koraka pa mora biti zapolnjena.

| | |
|---|---|
| **Preverja** | Kadar je `Tip objekta` = `crta`, mora biti `št. Koraka` zapolnjen (tudi okrajšava `št. Kor.`); prazni morajo biti vsi ostali stolpci razen `Tip podatka` in `Tip objekta`; `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, ...) |
| **Napake** | `CRTA_STEP_EMPTY` – manjka številka koraka pri ločniku |
| | `CRTA_COLUMN_NOT_EMPTY` – stolpec vsebuje vrednost, čeprav mora biti prazen pri ločniku |

---

### 2.6.1 Stolpci pri naslovu (`naslov`)

Preverja obvezna polja naslova in da ostali stolpci ostanejo prazni.

| | |
|---|---|
| **Preverja** | Kadar je `Tip objekta` (ali `Tip podatka`) = `naslov`, morata biti zapolnjena `št. Koraka` in `Navodilo`; `Zavihek` sme biti prazen ali koda monolita (`monolit1`, `monolit2`, ...) kot pri `crta`; ostali stolpci morajo biti prazni |
| **Napake** | `NASLOV_STEP_EMPTY` – manjka številka koraka pri naslovu |
| | `NASLOV_NAVODILO_EMPTY` – manjka `Navodilo` pri naslovu |
| | `NASLOV_COLUMN_NOT_EMPTY` – stolpec vsebuje vrednost, čeprav mora biti pri naslovu prazen |

---

### 2.7 Oblika ključa preverjanja

Preverja sintakso in prisotnost vrednosti v stolpcu `Ključ preverjanja`.

| | |
|---|---|
| **Preverja** | Vrednost mora ustrezati vzorcu `KEY_PATTERN`; ključ je obvezen pri `kemikalija`, `raztopina`, `masa` in časovnem paru. Oprema in checkbox ključa ne zahtevata (pri `spustniseznam` je obvezna `Vrednost`). |
| **Napake** | `KEY_INVALID_FORMAT` – oblika ključa ni pravilna (navede prvi napačen znak) |
| | `KEY_REQUIRED` – ključ manjka pri tipu podatka, ki ga zahteva |

---

### 2.8 Sintaksa formule

Preverja pravilno obliko vsebine `Vrednost` pri formulah.

| | |
|---|---|
| **Preverja** | Kadar je `Tip objekta` ∈ {`formula`, `formula0`, `formula1`}: `Vrednost` se mora začeti z `=` in vsebovati `$` (sklici na korake). Zapis `&$` ni dovoljen. |
| **Napake** | `FORMULA_SINTAKSA` – `Vrednost` se ne začne z `=` |
| | `FORMULA_BREZ_SKLICA` – formula ne vsebuje sklica na korak (`$`) |
| | `FORMULA_AMPERSAND_DOLLAR` – formula vsebuje `&$` (sklic zapišite kot `"$"&` in celico, npr. `"$"&C12`) |

---

### 2.9 Prepovedana vejica kot decimalno ločilo

Zaznava nepravilno uporabo vejice namesto pike kot decimalnega ločila.

| | |
|---|---|
| **Preverja** | Vejica kot decimalno ločilo v številčnih vrednostih – razen v stolpcu `Navodilo` in v Param1 pri vrsticah s kontrolama `zaklenipolja` ali `aliobstajapogoj` |
| **Napaka** | `VEJICA_NEDOVOLJENA` – vejica je uporabljena namesto pike |

---

### 2.10 Nedovoljeni presledki

Zaznava presledke v vrednostih celic.

| | |
|---|---|
| **Preverja** | Nobena vrednost (razen `Navodilo`, `Labela`, `Vrednost` in `Ključ preverjanja`) ne sme vsebovati presledkov. Presledek v `Zavihek` ne odpira novega zavihka (ostane samo ta napaka). |
| **Napaka** | `PRESLEDEK_NEDOVOLJEN` |

---

### 2.10.1 Presledki pri razponu v Navodilu

Preverja zapis razponov v stolpcu `Navodilo`.

| | |
|---|---|
| **Preverja** | Pri razponu (število, pomišljaj `–` / `—` ali vezaj `-`, število) mora biti en presledek pred pomišljajem in en za njim: `4000 – 4400`. Ne velja za zapise, ki niso razpon (`7647-14-5`, `2026-01-01`, `SOP-123`). |
| **Napaka** | `NAVODILO_RANGE_DASH_SPACING` – manjka (ali je odveč) presledek pred ali za pomišljajem pri razponu |

---

### 2.11 Veljavnost sklicevanja formule

Preverja, da sklici v formuli kažejo na obstoječe korake.

| | |
|---|---|
| **Preverja** | Vsak `$N` v `Vrednost` formule mora biti N ∈ obstoječih korakov (`shared.existing_steps`) |
| **Napaka** | `FORMULA_NAPACEN_SKLICE` – formula se sklicuje na neobstoječ korak |

---

### 2.12 Tip objekta pri sklicanem koraku

Preverja, da se formula sklicuje le na primerne korake.

| | |
|---|---|
| **Preverja** | Vsak korak, na katerega se formula sklicuje (`$N`), mora imeti `Tip objekta` ∈ {`edit`, `formula`, `formula0`, `formula1`} |
| **Napaka** | `FORMULA_KORAK_EDIT_LABELA` – sklicanemu koraku ni dovoljen tip objekta za sklicevanje |

---

## 3. Relacijska pravila (`relational`)

### 3.1 Podvojeni ključi

Preverja enoličnost ključev preverjanja pri kemikalijah, raztopinah in masah.

| | |
|---|---|
| **Preverja** | Podvojeni ključi za `kemikalija` / `raztopina` znotraj zavihka; masa: isti ključ ne sme biti v več sekcijah; za `masa` z istim baznim ključem: dovoljeno le, če obstaja lastnik (kemikalija/raztopina z istim bazom) v isti sekciji ali pred njo |
| **Napake** | `KEY_DUP_KEM` – podvojen ključ za kemikalijo |
| | `KEY_DUP_RAZT` – podvojen ključ za raztopino |
| | `KLJUC_PODVOJEN_MASA_RAZD` – isti ključ mase v več razdelkih |
| | `KLJUC_PODVOJEN_MASA` – podvojen ključ mase |
| **Opomba** | Ključi za vodo so izvzeti iz preverjanja duplikatov |

---

### 3.2 Lastnik mase

Preverja, da ima vsaka vrstica z maso ustrezno „lastniško" vrstico kemikalije, raztopine ali monomerne.

| | |
|---|---|
| **Preverja** | Vsaka vrstica `masa` (razen vode) mora imeti najbližjo predhodno vrstico `kemikalija`, `raztopina` ali `monomerna` (vključno z oštevilčenimi variantami, npr. `monomerna1`) z ujemajočim baznim ključem na istem zavihku; ključ mase mora biti enak polnemu ključu lastnika |
| **Napake** | `PAR_MASA_BREZ_LASTNIKA` – masa nima ustreznega lastnika |
| | `PAR_MASA_NAPACEN_RAZD` – masa je v napačnem razdelku glede na lastnika |

---

### 3.2.1 Par kemikalija/raztopina in masa

Preverja obratno smer para: vsaka kemikalija ali raztopina mora imeti vrstico `masa` z **enakim** ključem preverjanja. `volumen` z istim ključem ni nadomestilo za maso.

| | |
|---|---|
| **Preverja** | `kemikalija` in `raztopina` na istem zavihku imata vrstico `masa` z enakim ključem; vrstica `volumen` z istim ključem ni dovoljena |
| **Izjema** | Ključ vode (`dH2O`, `dH2O_1`, …): zahtevan je tip `volumen`, ne `masa` |
| **Napake** | `PAIR_CHEM_WITHOUT_MASS` – kemikalija nima vrstice `masa` |
| | `PAIR_SOL_WITHOUT_MASS` – raztopina nima vrstice `masa` |
| | `PAIR_VOLUME_NOT_ALLOWED` – `volumen` z istim ključem kot kemikalija/raztopina |
| | `PAIR_WATER_WITHOUT_VOLUME` – pri ključu dH2O manjka vrstica `volumen` |

---

### 3.3 Par začetek/konec časa

Preverja, da sta vrstici `datumcaszacetek` in `datumcaskonec` vedno v paru.

| | |
|---|---|
| **Preverja** | Vsak ključ `datumcaszacetek` ima ustrezen `datumcaskonec` in obratno; znotraj zavihka in ključa je dovoljena le ena začetna in ena končna vrstica |
| **Napake** | `PAR_CAS_BREZ_KONCA` – začetek brez konca |
| | `PAR_CAS_BREZ_ZACETKA` – konec brez začetka |
| | `KLJUC_PODVOJEN_CAS_PAR` – podvojen ključ pri časovnem paru |

---

### 3.4 Oštevilčenje ključev

Preverja pravilno zaporedno oštevilčenje ključev kemikalij, raztopin in mas.

| | |
|---|---|
| **Preverja** | Pri ključih s številčno pripono (npr. `kem1`, `kem2` …): zaporedje se začne pri 1, brez vrzeli; opozorilo, če obstajata bazni ključ in oštevilčeni ključ hkrati |
| **Napake** | `KLJUC_NUM_NE_1` – oštevilčenje se ne začne pri 1 |
| | `KLJUC_NUM_PRESLEDEK` – vrzel v oštevilčenju ključev |
| | `KLJUC_NUM_PODVOJEN_BASE` – obstaja tako bazni kot oštevilčen ključ (OPOZORILO) |

---

### 3.5 Par tehtnica/masa

Preverja, da tehtnica brez mase ne uporablja kontrole ustreznosti opreme.

| | |
|---|---|
| **Preverja** | Vrstica `tehtnica` brez ujemajoče vrstice `masa` z enakim ključem ne sme imeti kontrole `kontrolaustreznostiopreme` |
| **Napaka** | `KONTROLA_TEHTNICA_BREZ_MASE` |

---

### 3.6 Primernost tehtnice glede na maso

Preverja, da je tehtnica ustrezne razreda glede na vrednost mase.

| | |
|---|---|
| **Preverja** | Vrednost mase iz recepture: če masa ≥ 10 → `TEH-KLA` ali `{TEH-KLA, TEH-ANA}`; če masa < 10 in enota v Labeli ni `kg` → `TEH-ANA` ali `{TEH-KLA, TEH-ANA}` |
| **Napake** | `TEHTNICA_VREDNOST_PREVISOKA` – masa previsoka za izbrani razred tehtnice |
| | `TEHTNICA_VREDNOST_PRENIZKA` – masa prenizka za izbrani razred tehtnice |

---

### 3.7 Par repro/kolicina

Preverja, da ima vsaka vrstica `kolicina` predhodno vrstico `repro` z enakim ključem preverjanja (enako kot par raztopina/masa).

| | |
|---|---|
| **Preverja** | Vsaka vrstica `kolicina` mora imeti najbližjo predhodno vrstico `repro` na istem zavihku; ključ količine mora biti enak ključu tega repro |
| **Napake** | `PAR_KOLICINA_BREZ_LASTNIKA` – kolicina nima predhodnega repro |
| | `PAR_KOLICINA_NAPACEN_KLJUC` – ključ količine se ne ujema s ključem repro |
| **Izjema** | Predhodni `monolit` (tudi `monolit1`, ...) s ključem `paketni` + `kolicina` s ključem `paketnimonolit` ni napaka |

---

## 4. Pravila kontrol (`control`)

### 4.1 Neznana kontrola

Preverja, da so vse kontrole znane.

| | |
|---|---|
| **Preverja** | Vsaka nepraza vrednost v stolpcu Kontrola mora biti normalizirano ime znane kontrole (`ALLOWED_CONTROLS`) |
| **Napaka** | `KONTROLA_NEZNAN` |

---

### 4.1a Rezervirani stolpec Kontrola 1

Preverja, da je stolpec `Kontrola 1` namenjen samo kontrolama `zaklenipolja` in `aliobstajapogoj`.

| | |
|---|---|
| **Pravilo** | `control_column_one_reserved_rule` |
| **Preverja** | V stolpcu `Kontrola 1` sta dovoljeni samo `zaklenipolja` in `aliobstajapogoj` (tudi `aliobstajapogoj_ali`). Vse ostale kontrole morajo biti v `Kontrola 2` ali naprej. Kontrole `zaklenipolja` / `aliobstajapogoj` smejo biti tudi v drugih stolpcih. Neznane kontrole javi pravilo 4.1. |
| **Napaka** | `CTRL_COL1_RESERVED` |

---

### 4.2 Kontekst kontrole

Preverja, ali je kontrola dovoljena glede na tip podatka, tip objekta, Labelo in kontekst opreme.

| | |
|---|---|
| **Preverja** | `aliobkljukan` le pri checkboxu; kontrole opreme pri dropdownu, Labeli `koda` ali tipih/ključih opreme; `aliisto` le pri `kemikalija`/`raztopina`/oprema; `kontrolacasa` le pri `datumcaskonec`; raztopinske kontrole potrebujejo ključ in Param1 (ujemanje Param1 s ključem se ne zahteva) |
| **Napake** | `KONTROLA_NAPACEN_KONTEKST` – kontrola ni dovoljena v tem kontekstu |
| | `RAZTOPINA_*` – napake pri raztopinskih kontrolah |

---

### 4.3 Obvezna prisotnost kontrole praznopoljja

Preverja, da ima vsako vnosno polje kontrolo `kontrolapraznopolje`.

| | |
|---|---|
| **Preverja** | Tipi `edit`, `spustniseznam`, `izberidatumcas`, `gumbdatumcas`, `memo` morajo imeti `kontrolapraznopolje`, razen če so vsi kontrolni reži zasedeni ali je prisotna `zaklenipolja`; tipi `checkbox`, `naslov` in `crta` ne smejo imeti prazno-polje kontrole |
| **Napake** | `KONTROLA_ZAHTEVANO_PRAZNO` – manjka `kontrolapraznopolje` |
| | `KONTROLA_CHECKBOX_PRAZNO` – checkbox ima nedovoljeno kontrolo `kontrolapraznopolje` |
| | `KONTROLA_PRAZNO_NI_DOVOLJENO` – `naslov` ali `crta` ima nedovoljeno kontrolo `kontrolapraznopolje` |
| | `KONTROLA_ZAKLENI_BREZ_PRAZNO` – zaklenjeno polje nima `kontrolapraznopolje` |

---

### 4.4 Pričakovane kontrole (opozorilo)

Opozori, kadar manjkajo pričakovane kontrole glede na kontekst vrstice.

| | |
|---|---|
| **Preverja** | Pričakovane kontrole za kemikalijo, maso (z izjemami), embalažo, opremo, monolit, raztopino glede na `EXPECTED_CONTROLS` |
| **Napaka** | `KONTROLA_PRICAKOVANO_MANJKA` |
| **Resnost** | WARNING |

---

### 4.5 Parametri zaklenipolja

Preverja veljavnost parametrov kontrole `zaklenipolja`.

| | |
|---|---|
| **Preverja** | Param1: brez Excel `#` napak; z vejico ločena cela števila; vsak korak mora obstajati; vsak korak mora imeti `aliobstajapogoj` (razen če je izklopljeno v nastavitvah) |
| **Napake** | `ZAKLENI_PAR1_EXCEL_NAPAKA` – Excel napaka v Param1 |
| | `ZAKLENI_PAR1_FORMAT` – napačna oblika Param1 |
| | `ZAKLENI_P1_KORAK_MANJKA` – korak v Param1 ne obstaja |
| | `ZAKLENI_P1_BREZ_POGOJA` – korak nima `aliobstajapogoj` |

---

### 4.6 Kombinacija parametrov aliobstajapogoj

Preverja ujemanje parov Param1/Param2 pri `aliobstajapogoj`.

| | |
|---|---|
| **Preverja** | Par (Param1 ključ, Param2 vrednost 0/1) mora ustrezati logiki zaklenipolja – ključ v koraku glede na vse ključe zakleni |
| **Napaka** | `ZAKLENI_POGOJ_P1P2` |

---

### 4.6a Param1 pri aliobstajapogoj (ključ zaklenipolja)

Preverja, da je Param1 pri `aliobstajapogoj` skladen z `zaklenipolja`, ki ta korak zaklene, in da ni podvojen med sklopi.

| | |
|---|---|
| **Preverja** | Param1 mora biti ključ preverjanja sklopa `zaklenipolja`, ki ta korak zaklene: ključ vrstice, ki korak navaja v Param1 (npr. `sst_3` s Param2=0), ali parni ključ istega sklopa (npr. `sst_4` s Param2=1). Isti Param1 ne sme biti uporabljen pri dveh različnih sklopih `zaklenipolja` na istem zavihku. Excelove formule v Param1 (`=$F$58`) se preskočijo. |
| **Napake** | `LOCK_CONDITION_P1_LOCK_KEY` – Param1 ni ključ sklopa `zaklenipolja`, ki ta korak zaklene |
| | `LOCK_CONDITION_P1_DUPLICATE` – Param1 je podvojen med različnimi sklopi `zaklenipolja` |

---

### 4.7 Enoličnost ključa pri zaklenipolja

Preverja, da isti ključ nima dveh vrstic `zaklenipolja` v istem zavihku.

| | |
|---|---|
| **Preverja** | Podvojen `Ključ preverjanja` pri vrsticah z `zaklenipolja` znotraj istega zavihka |
| **Napaka** | `ZAKLENI_KLJUC_PODVOJEN` |

---

### 4.8 Vsak pogoj pokrit z zaklenipolja

Preverja, da je vsak `aliobstajapogoj` dejansko naveden v Param1 nekega `zaklenipolja`.

| | |
|---|---|
| **Preverja** | Vsak korak z `aliobstajapogoj` mora biti naveden v Param1 vsaj enega `zaklenipolja` na istem zavihku |
| **Napaka** | `ZAKLENI_P1_MANJKA_ZA_POGOJ` |

---

### 4.9 Checkbox in zaklenipolja

Preverja nedovoljene kombinacije `zaklenipolja` z `aliobkljukan` pri checkboxih.

| | |
|---|---|
| **Preverja** | Checkbox z `zaklenipolja` ne sme imeti `aliobkljukan`; Labela DA/NE ne sme imeti `aliobkljukan` |
| **Napake** | `KONTROLA_ZAKLENI_BREZ_ALIOB` – zaklenjeni checkbox ne sme imeti `aliobkljukan` |
| | `KONTROLA_CHECKBOX_DA_NE_BREZ_ALIOB` – checkbox DA/NE ne sme imeti `aliobkljukan` |
| | `KONTROLA_ZAKLENI_BREZ_PRAZNO` – zaklenjeno polje brez `kontrolapraznopolje` |

---

### 4.10 Parameter aliobkljukan

Preverja parametre kontrole `aliobkljukan`.

| | |
|---|---|
| **Preverja** | Param1 mora biti `da` ali `ne`; mora se ujemati s stanjem checkboxa (`shared.checkbox_states[key]`) |
| **Napake** | `ALIOB_PARAM_DA_NE` – Param1 ni `da` ali `ne` |
| | `CHECKBOX_STANJE` – vrednost Param1 ni skladna s stanjem checkboxa |

---

### 4.11 Parametri intervalnih kontrol

Preverja osnovno veljavnost parametrov pri `kontrolainterval` / `kontrolaintervala`.

| | |
|---|---|
| **Preverja** | Vsaj en parameter mora biti podan; vrednosti morajo biti števila; maksimum mora biti večji od minimuma |
| **Napake** | `KONTROLA_INTERVAL_PARAMETRI` – manjka vsaj en parameter |
| | `KONTROLA_INTERVAL_NI_STEVILO` – vrednost ni število |
| | `KONTROLA_INTERVAL_VRSTA` – max ≤ min |

---

### 4.12 Napredna validacija intervalnih parametrov

Preverja, da se parametri kontrole `kontrolainterval` / `kontrolaintervala` (Param1 = spodnja meja, Param2 = zgornja meja) ujemajo z vrednostjo ali intervalom, zapisanim v stolpcu `Navodilo`. Pravilo prepozna tri oblike zapisa v Navodilu in za vsako določi drugačna pravila za izračun zahtevanih vrednosti Param1 in Param2.

| | |
|---|---|
| **Napake** | `KONTROLA_INTERVAL_CILJ_P1`, `KONTROLA_INTERVAL_CILJ_P2_MIN` – neskladje pri neenačbi |
| | `KONTROLA_INTERVAL_PM_P1`, `KONTROLA_INTERVAL_PM_P2` – neskladje pri ±-toleranci |
| | `KONTROLA_INTERVAL_P1_MEJA` – napačna spodnja meja pri razponu |
| | `KONTROLA_INTERVAL_P2_MEJA` – napačna zgornja meja pri razponu |

#### Splošni pojem: korak (eps)

**Korak** je najmanjša enota natančnosti, ki jo narekuje vrednost v Navodilu. Določi se iz števila decimalnih mest:

| Zapis v Navodilu | Korak (eps) |
|---|---|
| Celo število (npr. `90`) | `1` |
| Ena decimalna mesta (npr. `6.5`) | `0.1` |
| Dve decimalni mesti (npr. `6.50`) | `0.01` |
| Tri decimalna mesta (npr. `3.180`) | `0.001` |

---

#### Oblika 1: Neenačba (`>`, `>=`, `<`, `<=`)

Navodilo vsebuje primerjalni operator in mejo, npr. `> 5`, `≥ 10`, `< 100`.

Označimo mejo kot **xi** in korak kot **eps**.

| Operator | Zahtevani Param1 | Zahtevani Param2 |
|---|---|---|
| `>` (strogo večje) | `= xi` | `≥ xi + eps` |
| `>=` (večje ali enako) | `= xi − eps` | `≥ xi + eps` |
| `<` (strogo manjše) | `≤ xi − eps` | `= xi` |
| `<=` (manjše ali enako) | `≤ xi − eps` | `= xi + eps` |

Logika je simetrična: pri `>` / `>=` je **Param1** določen natančno, Param2 je samo spodnja meja zgornjega dela. Pri `<` / `<=` je **Param2** določen natančno, Param1 je samo zgornja meja spodnjega dela.

**Primeri:**

| Navodilo | eps | Param1 | Param2 |
|---|---|---|---|
| `> 5` | 1 | `= 5` | `≥ 6` |
| `>= 5` ali `≥ 5` | 1 | `= 4` | `≥ 6` |
| `> 5.0` | 0.1 | `= 5.0` | `≥ 5.1` |
| `>= 5.0` | 0.1 | `= 4.9` | `≥ 5.1` |
| `< 100` | 1 | `≤ 99` | `= 100` |
| `<= 100` | 1 | `≤ 99` | `= 101` |
| `< 5.0` | 0.1 | `≤ 4.9` | `= 5.0` |
| `<= 5.0` | 0.1 | `≤ 4.9` | `= 5.1` |

---

#### Oblika 2: Toleranca s ± (npr. `6.50 ± 0.10`)

Navodilo vsebuje ciljno vrednost **xpm** in toleranco **tpm**. Interval je `[xpm − tpm, xpm + tpm]`.

Enotna formula (velja za vse primere, ne glede na velikost ali obliko tolerance):

```
eps  = korak iz decimalnih mest xpm  (npr. 6.50 → 0.01 ; 8.0 → 0.1 ; 20 → 1)

Param1 = (xpm − tpm) − eps
Param2 = (xpm + tpm) + eps
```

| Navodilo | eps | spodnja meja | Param1 | zgornja meja | Param2 |
|---|---|---|---|---|---|
| `6.50 ± 0.10` | `0.01` | `6.40` | `6.39` | `6.60` | `6.61` |
| `5.5 ± 0.1` | `0.1` | `5.4` | `5.3` | `5.6` | `5.7` |
| `8.0 ± 0.4` | `0.1` | `7.6` | `7.5` | `8.4` | `8.5` |
| `3.180 ± 0.032` | `0.001` | `3.148` | `3.147` | `3.212` | `3.213` |
| `14.01 ± 0.14` | `0.01` | `13.87` | `13.86` | `14.15` | `14.16` |
| `20 ± 1` | `1` | `19` | `18` | `21` | `22` |
| `90 ± 2` | `1` | `88` | `87` | `92` | `93` |
| `90.0 ± 2` | `0.1` | `88.0` | `87.9` | `92.0` | `92.1` |

Kanonski Param1/Param2 ostaneta priporočeni vrednosti in jih napiše sporočilo napake (npr. `24.0 ± 0.5` → `23.4` / `24.6`, ne `23.44` / `24.55`). Dodatno je sprejet numerični pas okoli intervala `[xpm − tpm, xpm + tpm]`: od pol koraka minus eno fino mesto pod spodnjo mejo do pol koraka nad zgornjo mejo.

**Primer:** `6.50 ± 0.10` → interval `[6.40, 6.60]`, dovoljeni pas **`[6.34, 6.65]`**. `6.34` in `6.65` sta OK. `6.33` in `6.66` (ter `6.24` / `6.75`) ostaneta napaki. Kanonski `6.39` / `6.61` ostaneta veljavna.

---

#### Oblika 3: Razpon `a–b` (npr. `5–10`)

Navodilo vsebuje spodnjo mejo **a** in zgornjo mejo **b**. Param1 in Param2 se določita tako, da se meja razširi za en korak:

```
Param1 = a − eps
Param2 = b + eps
```

| Navodilo | eps | Param1 | Param2 |
|---|---|---|---|
| `5–10` | 1 ali 0.1 | `4` ali `4.9` | `11` ali `10.1` |
| `45–51` | 1 ali 0.1 | `44` ali `44.9` | `52` ali `51.1` |
| `5.0–10.0` | 0.1 | `4.9` | `10.1` |
| `5.00–10.00` | 0.01 | `4.99` | `10.01` |

Če sta obe meji celi števili, sta pravilni obe branji: kot celo število (`45` → korak `1`) in kot ena decimalna mesta (`45.0` → korak `0.1`). Končna ničla se v navodilu včasih ne prikaže. Če je decimalna mesta zapisano (`5.0–10.0`, `47.5–52.5`), velja samo ta natančnost.

Če je v Navodilu razpon v CV in v oklepaju volumen **na kolono** (`12 - 13 CV ... (48 - 52 mL/kolono)`), je razpon v mL (z enoto) absolutna meja kot pri vsakem drugem razponu: Param1 = `47` ali `47.9`, Param2 = `53` ali `52.1`. Vrednosti, preračunane na večjo kolono (npr. `239` / `261` za 20 mL), so napaka. Pri `1.0 - 1.1 CV (4 - 4.4 mL/kolono)` velja razpon `4 - 4.4 mL` z eno decimalko: Param1 `3.9`, Param2 `4.5`.

Pri razponu ostaneta Param1/Param2 na **istih decimalkah** kot meji: `47.5–52.5` → `47.4` / `52.6`; `0.18–0.22` → `0.17` / `0.23` (ne `0.174`).

Izjema, kadar bi bil `a − eps` enak **0** (`0.01–0.30`): MES prag na eno mesto več.

**Primer:** `0.01–0.30` → dovoljeni pas Param1/Param2 **`[0.004, 0.305]`** (Param1 prag pod meritvijo `0.005`, Param2 prag nad zadnjo meritvijo `0.304`). Param1 `0` in Param2 `0.306` / `0.310` so napake. `0.01–0.60` → zgornja meja Param2 **`0.605`** (ne `0.610`).

---

### 4.13 Parametri kontrole časa

Preverja veljavnost parametrov `kontrolacasa`.

| | |
|---|---|
| **Preverja** | Param1 (min. sekunde) mora biti podan in biti število; Param2, kadar je podan, mora biti število; min ≤ max (opozorilo); ujemanje z vrednostjo v Navodilu (neenačba ali razpon, toleranca ±10 s) |
| **Napake** | `KONTROLA_CAS_MIN` – manjka minimalna vrednost |
| | `KONTROLA_CAS_MIN_NI_STEVILO` – min ni število |
| | `KONTROLA_CAS_MAX_NI_STEVILO` – max ni število |
| | `KONTROLA_CAS_VRSTA` – max < min (OPOZORILO) |
| | `KONTROLA_CAS_P1_NAVODILO` – spodnja meja se ne ujema z Navodilom |
| | `KONTROLA_CAS_P2_NAVODILO` – zgornja meja se ne ujema z Navodilom |

---

### 4.14 Zahtevana kontrola časa

Preverja, da ima vsak `datumcaskonec` kontrolo `kontrolacasa`.

| | |
|---|---|
| **Preverja** | Vrstica s tipom podatka `datumcaskonec` in tipom objekta `edit`/`formula`/`formula0`/`formula1` mora imeti kontrolo `kontrolacasa` |
| **Napaka** | `KONTROLA_CAS_ZAHTEVANA` |

---

### 4.15 Zahtevana intervalna kontrola

Preverja, da je intervalna kontrola prisotna, kadar jo Navodilo nakazuje.

| | |
|---|---|
| **Preverja** | Kadar `Navodilo` vsebuje numeričen interval (razpon / ± / neenačba), `Tip objekta` je `edit`/formula tip, ni `datumcaskonec`, ni checkbox in `Labela` ≠ `koda` → mora biti prisotna `kontrolainterval`, `kontrolaintervala` ali `kontrolarazlika` |
| **Napaka** | `KONTROLA_INTERVAL_ZAHTEVANA` |

---

### 4.16 Zahtevana aliobkljukan pri checkboxu

Preverja, da ima checkbox z Labelo `DA (kljukica)` kontrolo `aliobkljukan`.

| | |
|---|---|
| **Preverja** | `Tip podatka` = checkbox in `Labela` = `DA (kljukica)` zahteva `aliobkljukan`, razen kadar je prisotna `zaklenipolja` |
| **Napaka** | `KONTROLA_ALIOBKLJUKAN_ZAHTEVANA` |

---

### 4.17 Zahtevana kontrola vloge

Preverja, da ima vsaka vrstica `zaposleni` kontrolo `alipravavlogakoda`.

| | |
|---|---|
| **Preverja** | `Tip podatka` = `zaposleni` zahteva kontrolo `alipravavlogakoda` |
| **Napaka** | `KONTROLA_ALIPRAVAVLOGAKODA_ZAHTEVANA` |

---

### 4.18 Zahtevani kontroli za monolit

Preverja, da ima monolit obe predpisani kontroli.

| | |
|---|---|
| **Preverja** | `Tip podatka` z začetkom `monolit` zahteva obe kontroli: veljavnost in ustreznost monolita |
| **Napake** | `KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA` – manjka kontrola veljavnosti |
| | `KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA` – manjka kontrola ustreznosti |

---

### 4.19 Kontrola mase brez vrednosti

Preverja, da masa brez vrednosti nima kontrole mase.

| | |
|---|---|
| **Preverja** | Vrstica `masa` s prazno `Vrednost` ne sme imeti kontrole `kontrolamase` |
| **Napaka** | `KONTROLA_MASA_BREZ_VREDNOSTI` |

---

### 4.20 Kontroli kemikalije in raztopine (par + tip podatka)

Preverja, da sta kontroli veljavnosti in ustreznosti kemikalije oz. raztopine v vrstici vedno obe in da stojita samo na pravem tipu podatka.

| | |
|---|---|
| **Preverja** | Če je v vrstici `kontrolaVeljavnostiKemikalije` ali `kontrolaUstreznostiKemikalije`, morata biti prisotni obe, `Tip podatka` pa mora biti točno `kemikalija`. Enako za `kontrolaVeljavnostiRaztopine` / `kontrolaUstreznostiRaztopine` in `Tip podatka` = `raztopina`. |
| **Napake** | `CTRL_KEMIKALIJA_VALIDITY_REQUIRED` / `CTRL_KEMIKALIJA_SUITABILITY_REQUIRED` – manjka ena od kontrol kemikalije |
| | `CTRL_KEMIKALIJA_TYPE_REQUIRED` – kontroli kemikalije na tipu, ki ni `kemikalija` |
| | `CTRL_RAZTOPINA_VALIDITY_REQUIRED` / `CTRL_RAZTOPINA_SUITABILITY_REQUIRED` – manjka ena od kontrol raztopine |
| | `CTRL_RAZTOPINA_TYPE_REQUIRED` – kontroli raztopine na tipu, ki ni `raztopina` |
| **Parametri** | Kemikalija: `Param1` in `Param2` pri obeh kontrolah morata biti prazna (`CTRL_KEMIKALIJA_PARAM1_NOT_EMPTY`, `CTRL_KEMIKALIJA_PARAM2_NOT_EMPTY`). Raztopina: `Param1` mora biti pri veljavnosti in ustreznosti enak (`CTRL_RAZTOPINA_PARAM1_MISMATCH`), `Param2` pa prazen (`CTRL_RAZTOPINA_PARAM2_NOT_EMPTY`). |
| **Navodilo raztopine** | Stolpec `Navodilo` mora vsebovati točno oznako raztopine, kot je na nalepki: vrednost `Param1` pri `kontrolaUstreznostiRaztopine` (npr. `Koda 1M-NaOH-PL`). Primerja se natančno (velike/male črke); oznaka ne sme biti del daljše oznake (`1M-NaOH` v `1M-NaOH-PL`). Če je `Param1` prazen ali neizračunana formula, se ne preverja (`CTRL_RAZTOPINA_NAVODILO_LABEL`). |
| **Opomba** | Če kontrol ni, pravilo ne javi ničesar (priporočilo za manjkajoče kontrole ostaja opozorilo v `expected_controls_rule`). Različice tipa (`kemikalija1`, `raztopina1`) niso veljavne. |

## Pregled po modulih

| Modul | Št. pravil |
|---|:---:|
| `structural` | 2 |
| `field` | 10 |
| `relational` | 6 |
| `control` | 21 |
| **Skupaj** | **39** |

---

## Resnosti napak

| Resnost | Pomen |
|---|---|
| **ERROR** | Kršitev, ki onemogoča veljavno recepturo |
| **WARNING** | Opozorilo – možna nepravilnost, a ne nujno napaka |
| **INFO** | Informativna beležka |

Privzeta resnost vseh pravil je **ERROR**, razen kjer je v zgornjem opisu izrecno navedeno drugače.

---

*Dokument je bil generiran na podlagi izvorne kode validatorja (različica: CHANGELOG [Unreleased], 23. 3. 2026).*
