# URS – User Requirements Specification (Validator MES Receptur)

## Dokumentni podatki

- **Naziv**: URS – User Requirements Specification (Validator MES Receptur)
- **Sistem / aplikacija**: Validator (`validator_oop`) – validacija MES Excel receptur
- **ID dokumenta**: VAL-URS-001
- **Verzija**: 1.0
- **Datum**: 2026-02-04
- **Pripravil**: ______________________
- **Pregledal (QA)**: ______________________
- **Odobril (Lastnik procesa)**: ______________________

## 1. Namen

Namen dokumenta je definirati uporabniške zahteve (URS) za aplikacijo Validator, ki se uporablja za preverjanje skladnosti in kakovosti podatkov v MES Excel delovnih zvezkih (recepturah) ter za generiranje poročil o najdenih odstopanjih.

## 2. Obseg (Scope)

- **Vključeno**:
  - Validacija Excel receptur (več listov) z vnaprej definiranimi pravili.
  - Grafični uporabniški vmesnik (GUI) in ukazna vrstica (CLI).
  - Generiranje poročil v `.xlsx`, `.txt` in `.json` formatih.
  - Opcijska validacija skladnosti z SOP specifikacijo iz Word dokumenta (`.docx`).
  - Opcijska funkcija “apply fixes” (ustvarjanje kopije z uveljavljenimi popravki).
- **Izključeno**:
  - Neposredno upravljanje/krmiljenje proizvodne opreme ali MES.
  - Avtomatsko nalaganje receptur v MES ali avtomatsko odobravanje receptur.
  - Upravljanje uporabnikov, pravic in elektronskih podpisov v aplikaciji.

## 3. Opisi in definicije

- **Validator**: programsko orodje za preverjanje kakovosti podatkov in pravilnosti strukture MES Excel receptur.
- **Receptura**: Excel delovni zvezek z definiranimi stolpci (npr. *št. Koraka*, *Navodilo*, *Tip podatka* …).
- **Pravilo**: logika validacije, ki generira napake/opozorila (npr. manjkajoč stolpec, podvojeni koraki, kontrola intervala).
- **OQ**: Operational Qualification – dokaz, da sistem deluje pravilno v predvidenem okolju uporabe.
- **SOP**: Standard Operating Procedure – referenčni dokument zahtev, ki se lahko uporabi za dodatno validacijo.

## 4. Ozadje in namen uporabe (Intended Use)

Validator je namenjen **interni** uporabi (QA/Production/Process), kot **podporno orodje** za odkrivanje napak v recepturah pred uporabo v MES/proizvodnji. Rezultati validatorja služijo kot vhod v pregled in odločanje uporabnika; končno odgovornost za odobritev/uvoz recepture ima uporabnik/proces.

## 5. Predpostavke in omejitve

- Uporabnik zagotovi, da so vhodne datoteke pristne in upravljane skladno z internimi pravili (kontrola verzij, arhiviranje).
- Excel datoteke se obravnavajo kot vhodni podatki; Validator jih **privzeto ne spreminja**.
- Funkcija “apply fixes” ustvarja **kopijo** vhodnega dokumenta (ne sme prepisati originala).
- GUI je odvisen od razpoložljivosti `tkinter`; SOP validacija od razpoložljivosti `python-docx`; Excel branje/pisanje od `openpyxl`.

## 6. Uporabniške vloge

- **URS-ROLE-01 Uporabnik (QA/Production)**: izbira datotek, zagon validacije, ogled poročil, interpretacija rezultatov.
- **URS-ROLE-02 Skrbnik / Power user**: konfiguracija zagona (CLI parametri), diagnostika (logi), podpora uporabnikom.

## 7. Uporabniške zahteve

### 7.1 Funkcionalne zahteve

- **URS-FR-01 (Vhodna datoteka)**: Sistem mora omogočiti izbiro in branje Excel delovnega zvezka (`.xlsx`, `.xlsm`, po potrebi `.xls` kjer je podprto).
- **URS-FR-02 (Več datotek v GUI)**: GUI mora omogočiti izbiro ene ali več vhodnih receptur in zagon validacije nad vsemi izbranimi datotekami.
- **URS-FR-03 (Filtriranje listov)**: Sistem mora validirati samo liste, ki vsebujejo relevantne (obvezne) stolpce za recepturo.
- **URS-FR-04 (Validacijska pravila)**: Sistem mora izvesti nabor pravil za:
  - strukturo (obvezni stolpci, številčenje korakov),
  - pravila na nivoju polj (tip objekta/podatka, ključ, formula, enote),
  - relacijska pravila (unikatnost ključev, pari datum/čas, lastništvo mase),
  - kontrole (znane kontrole, kontekst kontrol, parametri intervala/časa, zaklenipolja).
- **URS-FR-05 (SOP – opcijsko)**: Sistem mora (opcijsko) omogočiti nalaganje SOP dokumenta iz Word (`.docx`) in izvesti dodatno validacijo skladnosti.
- **URS-FR-06 (Rezultat)**: Sistem mora prikazati, ali je receptura veljavna (valid) in zagotoviti seznam napak/opozoril z lokacijo (list, vrstica, stolpec) in kodo napake.
- **URS-FR-07 (Poročilo – Excel)**: Sistem mora generirati poročilo v Excel formatu (`.xlsx`) z vsaj:
  - seznamom napak,
  - številom napak po kodah.
- **URS-FR-08 (Poročilo – alternativni formati)**: Sistem mora omogočiti izvoz poročila v `.txt` in `.json`.
- **URS-FR-09 (Izhodne poti)**: Uporabnik mora imeti možnost določiti izhodno pot poročila (CLI parameter ali GUI izbira).
- **URS-FR-10 (Strogi način / strict)**: Sistem mora omogočiti način, kjer se opozorila obravnavajo kot napake.
- **URS-FR-11 (Bypass pravil)**: Sistem mora omogočiti izključitev izbranih pravil (npr. po imenu ali kodi).
- **URS-FR-12 (Formule – opcijsko)**: Sistem mora omogočiti validacijo z upoštevanjem formul (npr. formule v stolpcu “Vrednost”).
- **URS-FR-13 (Apply fixes – opcijsko)**: Sistem mora (opcijsko) ustvariti kopijo delovnega zvezka in uveljaviti predlagane popravke, kjer so definirani.
- **URS-FR-14 (Izhodni status/exit code)**: CLI mora vrniti:
  - `0` ob uspehu (brez ERROR),
  - `1` če so prisotne validacijske napake,
  - `2` ob runtime napaki (npr. neberljiva datoteka).

### 7.2 Nefunkcionalne zahteve

- **URS-NFR-01 (Uporabnost)**: GUI mora omogočiti uporabniku zagon validacije brez poznavanja CLI, z jasnimi sporočili o statusu in rezultatu.
- **URS-NFR-02 (Kompatibilnost OS)**: Sistem mora delovati na Windows okolju (Windows 10/11).
- **URS-NFR-03 (Zanesljivost)**: Sistem mora robustno obravnavati nepravilne/poškodovane datoteke in podati razumljivo sporočilo o napaki.
- **URS-NFR-04 (Izvedba)**: Validacija tipične recepture mora zaključiti v razumnem času (tarča: minute, odvisno od velikosti).
- **URS-NFR-05 (Sledljivost rezultatov)**: Poročilo mora vsebovati dovolj informacij za ponovljiv pregled (koda, opis, lokacija).
- **URS-NFR-06 (Integriteta podatkov)**:
  - Originalna vhodna datoteka se ne sme spreminjati.
  - Če je uporabljen “apply fixes”, mora biti izhod jasno ločen in sledljiv (ime datoteke, lokacija).
- **URS-NFR-07 (Logiranje/diagnostika)**: Sistem mora omogočiti diagnostiko napak (log datoteka ali konzolni izpis), posebej za EXE distribucijo.

### 7.3 Zahteve skladnosti (Compliance / Quality)

> Opomba: Natančna GxP klasifikacija je organizacijska odločitev. Ta URS predvideva uporabo kot podporno orodje za pregled podatkov.

- **URS-COM-01 (Uporaba kot podporno orodje)**: Sistem ne sme samodejno sprejemati proizvodnih odločitev; rezultat mora biti interpretiran s strani usposobljenega uporabnika.
- **URS-COM-02 (Kontrolirana sprememba)**: Spremembe pravil/algoritmov morajo biti upravljane (spremembni zapis, impact assessment, retest po potrebi).
- **URS-COM-03 (Dokazljivost)**: OQ mora omogočiti dokaz, da ključne funkcije delujejo v predvidenem okolju.

## 8. Kriteriji sprejema (Acceptance Criteria)

- Vse zahteve URS-FR in URS-NFR imajo pokritje v FS in OQ (sledljivost).
- OQ testni primeri se izvedejo brez odstopanj ali z ustrezno dokumentiranimi odstopanji (deviations) in ocenjenim vplivom.

## 9. Sledljivost (Traceability)

Sledljivost se vodi v FS (URS → FS) in OQ (URS/FS → OQ testi). Minimalno: vsaka URS-FR ima referenco na FS element in vsaj en OQ testni primer.

## 10. Priloge

- Seznam vzorčnih datotek za OQ: `validator_oop/samples/*`
- Izhodni primeri poročil: `validator_oop/samples/*_VALIDATION_REPORT.xlsx`

