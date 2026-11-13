# Changelog

Vse pomembne spremembe projekta Validator OOP so dokumentirane v tej datoteki.

Format temelji na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **docs/** `Predstavitev_projekta_Validator.docx` - Predstavitveni Word dokument projekta za vodstvo *(11. 11. 2026, ~45 min)*
- **rules/** `podatki_usage_rule` - Nova napaka `PODATKI_COLUMN_UNUSED`: javi zapolnjene stolpce zavihka `Podatki`, ki se ne uporabljajo v nobeni formuli (`INDEX/MATCH` s številko stolpca, `VLOOKUP`, neposreden sklic) v nobenem drugem zavihku; prazen neuporabljen stolpec (tudi s samo naslovom) ni napaka; potrebuje naložene formule (`include_formulas`), sicer se preskoči *(27. 10. 2026, ~1 h)*
- **field/** `navodilo_range_dash_spacing_rule` - V stolpcu `Navodilo` mora imeti razpon (npr. `4000 – 4400`) en presledek pred pomišljajem (`–`, `—`) ali vezajem (`-`) in en za njim; sicer napaka `NAVODILO_RANGE_DASH_SPACING` (zapisi kot `7647-14-5`, `2026-01-01`, `SOP-123` niso razpon) *(26. 10. 2026, ~1 h)*
- **control/** `control_column_one_reserved_rule` - Stolpec `Kontrola 1` je rezerviran za `zaklenipolja` in `aliObstajaPogoj`; druga kontrola v njem javi `CTRL_COL1_RESERVED` (ostale kontrole morajo biti v `Kontrola 2` ali naprej) *(26. 10. 2026, ~1 h)*

### Changed
- **relational/** `mass_owner_rule` - Ključi `razt1`, `razt2`, `razt_6` se pri iskanju lastnika mase ne krajšajo na `razt`; primerja se celoten ključ s številko. `EtOH1` se še naprej ujema po bazi `EtOH` *(13. 11. 2026, ~45 min)*
- **control/** `chemical_solution_controls_rule` - Pri vrstici z `kontrolaUstreznostiRaztopine` mora `Navodilo` vsebovati točno oznako raztopine iz Param1 (kot na nalepki; razlikuje velike/male črke, oznaka ne sme biti del daljše oznake); sicer napaka `CTRL_RAZTOPINA_NAVODILO_LABEL` *(26. 10. 2026, ~1 h)*
- **field/** `posebnosti_tip_podatka_rule` - `posebnostimon` je zahtevan samo, če je v isti vrstici v `Zavihek` vpisano `monolit1`, `monolit2`, …; zavihek v drugi vrstici ne šteje *(21. 10. 2026, ~45 min)*
- **field/** `posebnosti_tip_podatka_rule` - Zavihek v stolpcu `Zavihek` pomeni samo `monolit1`, `monolit2`, …; formula, poljubno besedilo ali `monolit` brez številke ne pomenijo, da ima receptura zavihke (zato ni več `DATA_TYPE_POSEBNOSTIMON_REQUIRED`) *(16. 10. 2026, ~45 min)*
- **excel/** `ReportWriter` - Poročilo (Excel `Povzetek` in TXT) na vrhu navaja validirano datoteko (`Validirana datoteka` / `Validirane datoteke`); nov parameter `source_files`, podan iz vseh vmesnikov (Tkinter, Qt, CLI, splet) *(13. 10. 2026, ~1 h)*
- **relational/** `repro_kolicina_owner_rule` - Izjema: `monolit` s ključem `paketni` + `kolicina` s ključem `paketnimonolit` ni več napaka `PAIR_KOLICINA_WITHOUT_OWNER` *(13. 10. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Sporočilo ± napake kaže kanonski Param (`24.0 ± 0.5` → Param1 `23.4`, Param2 `24.6`), ne rob pasu (`23.44` / `24.55`); pas ostane veljaven *(13. 10. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` - Razpon `mL/kolono` (npr. `12 - 13 CV (48 - 52 mL/kolono)`) ni absolutna meja: Param2 `261` pri 20 mL koloni je veljaven; sporočilo ne zahteva `53 ali 52.1` *(13. 10. 2026, ~1 h)*
- **relational/** `duplicate_key_rule`, `time_pair_rule` - Isti ključ mase v več razdelkih in ponovljen par `datumcaszacetek`/`datumcaskonec` v več zavihkih sta ena napaka (`v zavihkih 'monolit2', 'monolit3', ...`) *(12. 10. 2026, ~45 min)*
- **relational/** `duplicate_key_rule` - Podvojen ključ kemikalije ali raztopine v več zavihkih je ena napaka (`v zavihkih 'monolit1', 'monolit2', ...`), ne več ločenih sporočil po zavihku *(12. 10. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu iz celih števil (`45 - 51`, `5 - 10`) sta veljavni obe branji: korak `1` (`44` / `52`) in korak `0.1`, kot da bi bilo zapisano `45.0` (`44.9` / `51.1`) *(12. 10. 2026, ~1 h)*
- **field/** `formula_syntax` - Če `Vrednost` pri `formula` / `formula0` / `formula1` vsebuje `&$`, se javi napaka `FORMULA_AMPERSAND_DOLLAR` *(12. 10. 2026, ~30 min)*
- **web/** `app.tsx` - Odstranjena konfiguracija in primerjava razdelkov; v rezultatih ni filtrov in stolpca resnosti; prenos samo Excel poročila; v auditu ni stolpca Rola *(12. 10. 2026, ~45 min)*
- **web/** `app-header` - Črna vrstica brez »d.o.o.«; v rumeni vrstici odstranjen kvadratni znak IPO *(12. 10. 2026, ~15 min)*
- **web/** `app-header` - Glava kot na spletišču Sartorius: črna vrstica »Sartorius BIA Separations d.o.o.«, pod njo rumena vrstica z logotipom in navigacijo *(12. 10. 2026, ~45 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri `≥ 3 CV (120000 - 340000 mL)` se za Param1/Param2 vzame razpon v mL (`119999` / `340001`), ne meja iz števila CV *(1. 10. 2026, ~1 h)*
- **field/** `no_spaces_rule` - Presledek v stolpcu `Ključ preverjanja` ni več napaka `SPACE_NOT_ALLOWED` *(30. 9. 2026, ~20 min)*
- **control/** `navodilo_interval_kontrolainterval_required_rule` - Ob številčnem intervalu v Navodilu zadostuje tudi kontrola `kontrolarazlika` (poleg `kontrolaInterval`) *(30. 9. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri `10 ± 0.1 CV (80 ± 8 mL)` se za Param1/Param2 vzame volumen `80 ± 8 mL`, ne število CV *(30. 9. 2026, ~1 h)*
- **ui/** `input_files` - Ročno izbrana datoteka v mapi `staro` se validira; pri izbiri celotne mape se mapa `staro` še vedno preskoči *(30. 9. 2026, ~30 min)*
- **excel/** `recipe_workbook`, **ui/** `input_files` - Datoteka se preskoči samo, če na nobenem listu ni nobenega stolpca recepture; če manjka en ali več stolpcev, se validira in `required_columns` javi `MISSING_COLUMN` *(29. 9. 2026, ~45 min)*
- **ui/** `input_files` - Pri validaciji celotne mape se mapa `staro` (tudi `Staro`) sploh ne odpre; datoteke v njej se ne pregledujejo *(29. 9. 2026, ~30 min)*
- **rules/** `catalog_code_rule` - Enaka `INDEX/MATCH` → `Podatki` pot tudi za Param1 `kontrolaustreznostirepro` (vse velikosti v tem stolpcu, šifrant repro) *(15. 9. 2026, ~45 min)*
- **rules/** `catalog_code_rule` - Preverjanje šifer raztopin je `WorkbookRule`: iz Param1 `kontrolaustreznostiraztopine` razčleni `INDEX/MATCH`, v zavihku `Podatki` pa preveri vse vrstice tega stolpca (vse velikosti recepture, ne samo trenutni dropdown) *(15. 9. 2026, ~2 h)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.18–0.22` sta Param1/Param2 `0.17` / `0.23` (`a − eps`); MES prag `0.174` velja samo, kadar bi bil `a − eps` enak 0 (`0.01–0.30`) *(10. 9. 2026, ~45 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu z eno decimalko (`47.5–52.5`) sta Param1/Param2 `47.4` / `52.6` (`a − eps` / `b + eps`); extra decimalka (`47.44`) ni več zahtevana niti dovoljena *(10. 9. 2026, ~45 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.01–0.30` je Param2 `0.305` prag nad zadnjo meritvijo `0.304` (simetrično s Param1 `0.004`); `0.306` in `0.310` ostaneta napaki; pri `0.01–0.60` zgornja meja `0.605` *(10. 9. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.01–0.30` / `0.01–0.60` kanonski Param2 `0.310` / `0.610` nista več dovoljena; zgornja meja je `0.304` / `0.604` *(10. 9. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.01–0.30` Param1 `0` / `0.000` ni več veljaven (vse ≤ 0.004 je izven intervala); dovoljen je pas od `0.004` *(10. 9. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.01–0.30` je zgornji Param2 `0.304` (ne `0.305`, ker se 0.305 zaokroži na 0.31); Param1 `0.004` ostane dovoljen *(10. 9. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `0.01–0.30` sta Param1=`0.004` in Param2=`0.305` dovoljena (prag pod/nad 0.005–0.304); napaka od `0.003` / `0.306` *(10. 9. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri razponu `a–b` so dovoljene vrednosti, ki se z half-up zaokrožijo v `[a, b]` (npr. `0.01–0.30`: 0.005–0.304 OK; 0.004 in 0.305 napaka); kanonski `a−eps` / `b+eps` ostaneta veljavna *(10. 9. 2026, ~1 h)*
- **control/** `kontrola_interval_advanced_rule` - Sporočilo ± napake kaže rob pasa (`Param1 mora biti 6.34`, `Param2 mora biti 6.65`), brez kanonske meje in oklepaja »ali v …« *(10. 9. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri ± je dovoljeni pas `[6.34, 6.65]` (ne ves `[6.30, 6.70]`): `6.33` in `6.66` sta napaki, `6.34` in `6.65` ostaneta OK *(10. 9. 2026, ~30 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri ± se zaokrožitveni pas razširi za en korak: vrednosti, ki se zaokrožijo na kanonski Param1/Param2, niso napaka (npr. `6.50 ± 0.10`: 6.34→6.30 in 6.65→6.70 sta OK; 6.24 in 6.75 ostaneta napaki) *(10. 9. 2026, ~45 min)*
- **control/** `kontrola_interval_advanced_rule` - Pri ± toleranci se poleg kanonskih Param1/Param2 sprejmejo vrednosti, ki se z half-up zaokrožijo v `[x−t, x+t]` (npr. `6.50 ± 0.10`: dovoljeno 6.35–6.64; 6.34 in 6.65 ostaneta napaki) *(10. 9. 2026, ~1 h)*
- **rules/** `catalog_code_rule` - Pri `raztopina` se šifra primerja iz Param1 kontrole `kontrolaustreznostiraztopine`, ne iz ključa preverjanja *(1. 9. 2026, ~45 min)*
- **rules/** `catalog_code_rule` - Pri `repro`/`reproodpis` se šifra primerja iz Param1 kontrole `kontrolaustreznostirepro`, ne iz ključa preverjanja *(1. 9. 2026, ~45 min)*
- **docs/** `NAV-158`, `PRAVILA_VALIDATORJA` - Presledek v `Zavihek` ne odpira novega zavihka; ostane napaka `SPACE_NOT_ALLOWED` v tem stolpcu *(1. 9. 2026, ~10 min)*
- **core/** `shared_context` - Vrednost v `Zavihek` s presledkom ne odpira novega zavihka (ostane napaka `SPACE_NOT_ALLOWED` v tem stolpcu, brez lažnih napak pri `zaklenipolja` / številčenju korakov) *(1. 9. 2026, ~45 min)*
- **field/** `no_spaces_rule` - Pri presledku v stolpcu `Zavihek` sporočilo pove, da je treba popraviti to celico in da presledek ne odpira novega zavihka *(1. 9. 2026, ~15 min)*
- **control/** `kontrolaveljavnostiraztopine`, `kontrolaustreznostiraztopine` - Param1 se ne preverja več proti bazi ključa preverjanja (`SOLUTION_P1_BASE` / `SOLUTION_P2_BASE`); ključ in Param1 se smejo razlikovati *(1. 9. 2026, ~30 min)*
- **field/** `naslov_empty_columns_rule` - Pri `naslov` morata biti zapolnjena `št. Koraka` (`NASLOV_STEP_EMPTY`) in `Navodilo` (`NASLOV_NAVODILO_EMPTY`); `Zavihek` prazen ali `monolit1`/`monolit2`/… kot pri `crta` *(31. 8. 2026, ~45 min)*
- **field/** `crta_empty_columns_rule` - Pri `crta` mora biti `št. Koraka` zapolnjen (tudi okrajšava `št. Kor.`; koda `CRTA_STEP_EMPTY`); `Zavihek` prazen ali `monolit1`/`monolit2`/… *(31. 8. 2026, ~45 min)*
- **control/** `aliobstajapogoj_param1_rule` - Skrajšano sporočilo `LOCK_CONDITION_P1_LOCK_KEY` (npr. `Param1 pri 'aliObstajaPogoj' mora biti sst_9 ali sst_10, ne 'sst_4'.`) *(31. 8. 2026, ~15 min)*
- **control/** `aliobstajapogoj_param1_rule` - Param1 sme biti tudi parni ključ istega sklopa `zaklenipolja` (npr. `sst_4` s Param2=1 je enakovreden `sst_3` s Param2=0); koda `LOCK_CONDITION_P1_LOCK_KEY` *(31. 8. 2026, ~1 h)*
- **control/** `aliobstajapogoj_param1_rule` - Ujemanje Param1 ne temelji več na najbližjem `zaklenipolja`, temveč na ključu tiste vrstice `zaklenipolja`, ki ta korak navaja v Param1 (koda `LOCK_CONDITION_P1_LOCK_KEY`); preverba podvojenega Param1 med sklopi ostane *(31. 8. 2026, ~1 h)*
- **field/** `key_validation` - Checkbox (tudi s kontrolo pogoja `aliobstajapogoj`/`zaklenipolja`) ne zahteva več ključa preverjanja *(26. 8. 2026, ~20 min)*
- **field/** `key_validation` - Oprema ne zahteva več ključa preverjanja; pri `Tip objekta = spustniseznam` je namesto ključa obvezen stolpec `Vrednost` (`SPUSTNISEZNAM_VREDNOST_EMPTY`) *(26. 8. 2026, ~45 min)*
- **field/** `naslov_empty_columns_rule` - Stolpec `Zavihek` sme biti pri `naslov` zapolnjen, če vsebuje kodo monolita (`monolit1`, `monolit2`, ...); ostali stolpci ostanejo prazni *(26. 8. 2026, ~20 min)*
- **field/** `crta_empty_columns_rule` - Stolpec `Zavihek` sme biti pri `crta` zapolnjen, če vsebuje kodo monolita (`monolit1`, `monolit2`, ...); ostali stolpci ostanejo prazni *(26. 8. 2026, ~20 min)*
- **field/** `water_not_masa_rule` - Opozorilo `MASS_WATER_SHOULD_BE_VOLUME` le, če je `Tip podatka = masa` in ključ preverjanja dH2O (ne več prek besedila v Navodilu) *(25. 8. 2026, ~20 min)*
- **control/** `expected_controls_rule` - Pri `repro`/`reproodpis` sta pričakovani le `kontrolaveljavnostirepro` in `kontrolaustreznostirepro` (odstranjena napačna zahteva `kontrolaprimernostirepro`) *(25. 8. 2026, ~20 min)*
- **field/** `label_requirements` - Labela `datum/čas` se zahteva le pri `Tip objekta = izberidatumcas` ali `gumbdatumcas`, ne za vse tipe podatka `datumcas`/`datumcaszacetek`/`datumcaskonec` *(25. 8. 2026, ~30 min)*
- **field/** `label_requirements` - Labela `naziv opreme` se zahteva le pri `Tip objekta = spustniseznam`, ne za vse tipe opreme (npr. `črpalka` z `edit` lahko ima drugo Labelo) *(25. 8. 2026, ~30 min)*
- **field/** `crta_empty_columns_rule` - Pravilo se sproži po `Tip objekta = crta`; dovoljena je vrednost le v `št. Koraka` (poleg identifikatorjev tipa); `Zavihek` in ostali stolpci morajo biti prazni *(25. 8. 2026, ~30 min)*
- **control/** `aliisto` - Kontrola je dovoljena tudi pri vseh tipih opreme (npr. `tehtnica`, `termometer`, `kopel`, `avtoklav`), ne samo pri `kemikalija` in `raztopina` *(24. 8. 2026, ~20 min)*
- **control/** `required_controls_rule` - Kontrola `kontrolapraznopolje` je pri tipih objekta `naslov` in `crta` prepovedana enako kot pri `checkbox` (koda `CTRL_EMPTY_NOT_ALLOWED`) *(21. 8. 2026, ~20 min)*
- **docs/** `NAV-157_Navodila_KL_priprava_recepture` - Dopolnjen seznam vseh 40 dovoljenih kontrol (vsaka v svoji vrstici, z namenom in Par 1/Par 2), dodane najpogostejše kombinacije, poglavja 12–14 (dodajanje koraka, tipične napake, validacija) in manjkajoči razdelek 4.2 *(17. 8. 2026, ~3 h)*
- **control/** `zakleni_param_rule` - Preverba `LOCK_P1_WITHOUT_CONDITION` je zdaj privzeto vklopljena: korak v Param1 pri `zaklenipolja` mora imeti `aliObstajaPogoj`, razen če gre za drug checkbox korak z `zaklenipolja`; privzeta vrednost `bypass_zakleni_require_pogoj_for_param1_steps` je `False` *(3. 8. 2026, ~45 min)*

### Fixed
- **rules/** `podatki_usage_rule` - Stolpec v `Podatki` ni več `PODATKI_COLUMN_UNUSED`, če ga prebere formula uporabljenega stolpca (tudi po verigi); npr. `Pretok 1` (AP) z vrednostjo v `Min`/`Max` (`=AP3*0.95-0.1`), ko sta `Min` in `Max` v INDEX/MATCH, sam `Pretok 1` pa ne. Sklic na drug zavihek se ne šteje *(13. 11. 2026, ~1 h)*
- **control/** `kontrola_interval_advanced_rule` - Razpon `mL/kolono` (npr. `12 - 13 CV (48 - 52 mL/kolono)`) je spet absolutna meja: Param2 `53` (ne `261`), pri `1.0 - 1.1 CV (4 - 4.4 mL/kolono)` Param2 `4.5`; odstranjeno preračunavanje na volumen kolone (`primer.xlsx`: 8 vrstic zdaj javi napako kot vzorčna koda); popravljeni testi in `PRAVILA_VALIDATORJA.md` *(15. 10. 2026, ~1 h)*
- **core/** `constants` - Dodan slovenski prevod kode `STEP_OUT_OF_ORDER` (koraki niso v naraščajočem vrstnem redu) *(13. 10. 2026, ~10 min)*

### Added
- **control/** `chemical_solution_controls_rule` - Pri kontrolah kemikalije morata biti Param1 in Param2 prazna (`CTRL_KEMIKALIJA_PARAM1_NOT_EMPTY`, `CTRL_KEMIKALIJA_PARAM2_NOT_EMPTY`); pri kontrolah raztopine mora biti Param1 pri veljavnosti in ustreznosti enak, Param2 pa prazen (`CTRL_RAZTOPINA_PARAM1_MISMATCH`, `CTRL_RAZTOPINA_PARAM2_NOT_EMPTY`) *(19. 10. 2026, ~45 min)*
- **control/** `chemical_solution_controls_rule` - Če je v vrstici ena od kontrol `kontrolaVeljavnostiKemikalije` / `kontrolaUstreznostiKemikalije`, morata biti obe, `Tip podatka` pa točno `kemikalija`; enako za `kontrolaVeljavnostiRaztopine` / `kontrolaUstreznostiRaztopine` in tip `raztopina` (`CTRL_KEMIKALIJA_*_REQUIRED`, `CTRL_RAZTOPINA_*_REQUIRED`, `CTRL_*_TYPE_REQUIRED`); preverjanje tipa je prestavljeno iz `control_context_rule`, ki zdaj za raztopino ne sprejema več `raztopina1` *(19. 10. 2026, ~1 h)*
- **field/** `posebnosti_tip_podatka_rule` - Brez zavihka mora biti Tip podatka `posebnosti`, z zavihkom `posebnostimon` (`DATA_TYPE_POSEBNOSTI_REQUIRED`, `DATA_TYPE_POSEBNOSTIMON_REQUIRED`) *(12. 10. 2026, ~1 h)*
- **relational/** `owner_mass_pair_rule` - `kemikalija`/`raztopina` zahtevata vrstico `masa` z enakim ključem; `volumen` z istim ključem ni dovoljen, razen pri `dH2O` (`PAIR_CHEM_WITHOUT_MASS`, `PAIR_SOL_WITHOUT_MASS`, `PAIR_VOLUME_NOT_ALLOWED`, `PAIR_WATER_WITHOUT_VOLUME`) *(9. 9. 2026, ~1 h 30 min)*
- **field/** `masa_tip_podatka_rule` - Tip podatka za maso sme biti samo `masa`; `masa1` in ostale oštevilčene različice niso veljavne (`DATA_TYPE_MASA_INVALID`) *(9. 9. 2026, ~30 min)*
- **rules/** `catalog_code_rule` - Preverjanje šifer repro materiala proti šifrantu (stolpec `material_sifra`); tipi `repro`/`reproodpis`; CLI `--catalog-repro`, GUI in spletni vmesnik *(1. 9. 2026, ~3 h)*
- **control/** `aliobstajapogoj_param1_rule` - Pri `aliObstajaPogoj` mora biti Param1 eden od ključev najbližjega `zaklenipolja` (koda `LOCK_CONDITION_P1_NEAREST_KEY`); isti Param1 ne sme biti uporabljen pri dveh različnih sklopih `zaklenipolja` (koda `LOCK_CONDITION_P1_DUPLICATE`) *(31. 8. 2026, ~2 h)*
- **control/** `expected_controls_rule` - Pričakovane kontrole za `repro`/`reproodpis`: veljavnost in ustreznost (WARNING `CTRL_EXPECTED_MISSING`) *(25. 8. 2026, ~45 min)*
- **relational/** `time_order_rule` - Korak `datumcaszacetek` mora imeti manjšo številko koraka kot `datumcaskonec` z istim ključem (WARNING `PAIR_TIME_ORDER`) *(25. 8. 2026, ~1 h)*
- **field/** `naslov_empty_columns_rule` - Pri naslovu smejo biti zapolnjena le polji `št. Koraka` in `Navodilo` (koda `NASLOV_COLUMN_NOT_EMPTY`) *(25. 8. 2026, ~1 h)*
- **field/** `water_not_masa_rule` - Opozorilo, če je voda zapisana kot tip `masa` namesto `volumen` (WARNING `MASS_WATER_SHOULD_BE_VOLUME`) *(25. 8. 2026, ~45 min)*
- **field/** `key_validation` - Razširjena obveznost ključa preverjanja: vsa oprema (`is_equipment_tip`), `datumcaszacetek`/`datumcaskonec` in checkbox z `aliobstajapogoj`/`zaklenipolja` (koda `KEY_REQUIRED`) *(25. 8. 2026, ~45 min)*
- **field/** `label_requirements` - Razširjena preverba Labele glede na Tip podatka: `koda` tudi za `raztopina`/`embalaza`, `naziv opreme` za opremo, `datum/čas` za časovne tipe, obvezna enota za `masa` (kode `LABEL_MUST_BE_NAZIV_OPREME`, `LABEL_MUST_BE_DATUM_CAS`, `LABEL_MUST_BE_UNIT`) *(25. 8. 2026, ~1 h)*
- **control/** `kontrolaveljavnostiopreme` - Avtoklav podprt kot tip opreme (`EQUIPMENT_TYPES`, `EXPECTED_CONTROLS`). *(24. 8. 2026, ~20 min)*
- **tests/** `test_equipment_detection` - Dodan unit test za prepoznavo tipa `avtoklav` kot opreme. *(24. 8. 2026, ~20 min)*
- **relational/** `repro_kolicina_owner_rule` - Nova relacijska preverba para `repro`–`kolicina`: vsaka `kolicina` mora imeti najbližji predhodni `repro` na istem zavihku z enakim ključem preverjanja (kodi `PAIR_KOLICINA_WITHOUT_OWNER`, `PAIR_KOLICINA_KEY_MISMATCH`) *(21. 8. 2026, ~1 h)*
- **docs/** `Kratka_navodila_priprava_recepture` - Kratka navodila za nove sodelavce o pripravi IPO receptur (postopek od kopije obstoječe datoteke do validacije, stolpci, zlata pravila) *(17. 8. 2026, ~2 h)*
- **db/** `MES/MySQL integracija – nov paket db/` - Polna implementacija Možnosti C (MySQL kot vir receptur in cilj rezultatov) brez sprememb pravil/engina: `DBConfig` (env/.env, `MES_DB_*`, ločen read-only in write user, opcijski TLS), `ConnectionFactory` (lazy import `mysql-connector-python`, retry, context managerji, jasne slovenske napake brez gesla), `ColumnMapping` (config-driven mapping MES stolpcev → validator glave z JSON override prek `MES_DB_MAPPING_FILE`, validacija proti `REQUIRED_COLUMNS` z `MappingError`, transformacije NULL/trim/cast, validacija SQL identifikatorjev), `MySQLLoader.load_recipe()` vrne `LoadedWorkbook` (isti format kot `ExcelLoader`, podpora več listom prek `sheet_column`, `list_recipes`, `recipe_exists`, `RecipeNotFoundError`), `MySQLReportWriter.save()` zapiše run + findinge transakcijsko (rollback ob napaki, opcijski `replace_existing`, verzija validatorja, arhiviran config) v tabeli `validation_runs`/`validation_findings` (`db/schema.sql`, idempotenten `db/migrate.py`); `requirements-db.txt` (driver ni osnovna odvisnost), `.env.example`, `db/README.md` *(21. 7. 2026, ~6 h)*
- **rules/** `CLI za MES/MySQL vir (main.py)` - Novi argumenti `--db-source`, `--recipe-id`, `--db-save-results`, `--list-recipes`, `--db-mapping` (povratno združljivo, brez `--db-source` je Excel tok nespremenjen); validacija iz baze teče prek `validate_loaded()`, izpis run_id po shranjevanju, jasne slovenske napake in exit code 2 ob manjkajočem driverju/konfiguraciji; stdout/stderr `errors="replace"` za Windows cp1252 konzolo *(21. 7. 2026, ~1 h 30 min)*
- **web/** `MES/MySQL endpointi (/api/db/*)` - `GET /api/db/health` (stanje povezave brez poverilnic), `GET /api/db/recipes?limit=&offset=&q=` (seznam receptur), `POST /api/db/validate` (`{recipe_id, config, save_results}` → job prek obstoječe job/report infrastrukture, samo korak nalaganja je zamenjan z `MySQLLoader`); endpointi skriti za `MES_WEB_ENABLE_DB=1`, ob vklopljeni avtentikaciji `save_results` zahteva vlogo QA/admin; `FileResult.db_run_id` v rezultatih; `JobManager.create_db_job` in `ValidationService.validate_db_recipe` *(21. 7. 2026, ~2 h 30 min)*
- **tests/** `test_db_integration.py`, `test_web_db.py` - 40+ testov brez žive baze: mapping (JSON override, manjkajoče preslikave, transformacije, zaščita SQL identifikatorjev), `DBConfig` (env/.env, geslo ni v repr), `MySQLLoader` z mockanim kurzorjem (parametrizirane poizvedbe, multi-sheet, `RecipeNotFoundError`, validacija recipe_id), `MySQLReportWriter` (transakcija/rollback, `replace_existing`), ekvivalenčni test Excel vs SQL vir → identične napake, web endpointi (skriti brez flaga, validacija prek job infrastrukture); opcijski integracijski test z živo bazo (marker `mysql`, privzeto skipnjen) + `tests/docker-compose.mysql.yml` *(21. 7. 2026, ~2 h 30 min)*
- **docs/** `PROMPT_MES_MYSQL_INTEGRACIJA.md` - Celovit prompt/specifikacija za polno MES/MySQL integracijo (SQL kot vir + cilj): nov paket `db/` (`MySQLLoader` vrne `LoadedWorkbook`, config-driven mapping, `MySQLReportWriter`, DDL, migracije), CLI (`--db-source`, `--recipe-id`, `--db-save-results`, `--list-recipes`), web endpointi (`/api/db/*`), testna strategija z mocki + opcijski Docker MySQL, varnost in deployment; poudarek na ohranitvi obstoječega Excel/CLI/GUI toka in nespremenjenem enginu *(21. 7. 2026, ~30 min)*
- **web/** `faza 2 – avtentikacija (AD/LDAP + role)` - Prijava z AD/LDAP (opcijski paket `ldap3`, bind s predlogo DN/UPN, rola iz članstva v AD skupinah) ali lokalnim fallback uporabnikom (JSON s PBKDF2 hashi oz. `MES_WEB_DEV_USERS` za dev); role tehnolog/QA/admin z omejitvami dostopa (tehnolog vidi samo svoje jobe/zgodovino, audit samo QA/admin); strežniške seje v SQLite + HttpOnly piškotek `mes_session` (podprt tudi Bearer žeton); novi endpointi `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`; prijava je privzeto izklopljena (`MES_WEB_AUTH_ENABLED=0`), zato MVP vedenje in obstoječi testi ostanejo nespremenjeni; nova modula `web/backend/auth.py` in `web/backend/db.py` (stdlib sqlite3, brez novih obveznih odvisnosti) *(21. 7. 2026, ~4 h)*
- **web/** `faza 2 – audit trail` - Revizijska sled v SQLite (kdo, kdaj, kaj, IP): prijave (tudi neuspešne), odjave, zagon/zaključek validacije, prenosi poročil, primerjava razdelkov, diff verzij; endpoint `GET /api/audit` (samo QA/admin) s filtri po uporabniku/dejanju in straničenjem; nov zavihek »Audit« v frontendu *(21. 7. 2026, ~1 h 30 min)*
- **web/** `faza 2 – trajna zgodovina validacij` - Vsaka zaključena validacija se trajno shrani (neodvisno od TTL čiščenja jobov): povzetek v SQLite, celotni rezultati + poročila + vhodne datoteke v `workdir/history/{id}/`; endpointi `GET /api/history`, `GET /api/history/{id}` in prenosi poročil iz zgodovine; retencija prek `MES_WEB_HISTORY_TTL_DAYS`; nov modul `web/backend/history.py` in zavihek »Zgodovina« s podrobnim pogledom (ponovno uporabi tabelo rezultatov) *(21. 7. 2026, ~2 h 30 min)*
- **excel/** `section_compare` - Nov izoliran modul za primerjavo razdelkov med listi iste recepture (razdelki po vrsticah `naslov`, enaka logika kot v `shared_context`, brez posega v engine): primerja število razdelkov, naslove, število korakov in besedila navodil; kode `SECTION_COUNT_MISMATCH`, `SECTION_TITLE_MISMATCH`, `SECTION_STEP_COUNT_MISMATCH`, `SECTION_INSTRUCTION_MISMATCH`; poročilo .xlsx/.txt prek ReportWriter; implementiran dosedanji TODO v vseh treh desktop GUI (classic, themed, qt) ter nov web endpoint `POST /api/section-compare` z zavihkom »Razdelki« *(21. 7. 2026, ~3 h)*
- **excel/** `recipe_diff` - Nov izoliran modul za diff dveh verzij recepture: dodani/odstranjeni listi in stolpci, dodane/odstranjene/spremenjene vrstice (poravnava z `difflib.SequenceMatcher`), pri spremenjenih vrsticah seznam spremenjenih stolpcev (stara → nova vrednost); web endpoint `POST /api/diff` sprejme dve naloženi datoteki ali datoteki iz trajne zgodovine (dva joba); nov zavihek »Diff verzij« z barvno označenimi spremembami *(21. 7. 2026, ~2 h 30 min)*
- **web/** `faza 2 – WebSocket napredek` - Nov endpoint `WS /api/ws/jobs/{id}` pošilja stanje joba v realnem času (ob spremembi); frontend najprej poskusi WebSocket (indikator »⚡ v živo«) in ob neuspehu samodejno preide na dosedanji polling; nginx konfiguracija dopolnjena z `Upgrade`/`Connection` headerji za `/api/ws/` *(21. 7. 2026, ~1 h 30 min)*
- **web/** `faza 2 – HTTPS / AD CS priprava` - Nova dokumentacija `web/deploy/HTTPS_AD_CS.md` (izdaja internega certifikata pri AD CS, namestitev v nginx, obnova, preverjanje); v `nginx.conf` pripravljen popoln 443 blok (TLS 1.2/1.3, varnostni headerji, WebSocket) in HTTP→HTTPS preusmeritev; docker-compose z zakomentiranimi primeri za auth/LDAP/zgodovino ter `MES_WEB_SECURE_COOKIES` *(21. 7. 2026, ~1 h)*
- **web/** `faza 2 – prijavni UI in navigacija` - Frontend (vendoran React, brez build koraka) razširjen s prijavnim oknom (Sartorius tema), navigacijskimi zavihki (Validacija / Zgodovina / Razdelki / Diff verzij / Audit, glede na rolo), uporabniškim čipom z odjavo ter samodejnim prikazom prijave ob poteku seje (401) *(21. 7. 2026, ~3 h)*
- **web/** `test_web_phase2.py` - Testi faze 2 (29 testov): modula `section_compare` in `recipe_diff` (z generiranimi testnimi recepturami), prijava/odjava, napačno geslo + audit vnos, zaščita endpointov (401/403), role (tehnolog brez audita, QA/admin z), lastništvo zgodovine, obstoj zgodovine po TTL čiščenju jobov, prenosi poročil iz zgodovine, API za primerjavo razdelkov in diff (upload + iz zgodovine), WebSocket napredek *(21. 7. 2026, ~2 h)*
- **excel/** `recipe_workbook` - Pomožne funkcije za hitro preverjanje, ali Excel vsebuje list z zahtevanimi IPO stolpci; uporabljeno pri filtriranju vhodnih datotek v GUI *(17. 6. 2026, ~25 min)*
- **field/** `crta_empty_columns_rule` - Pri `Tip podatka = crta` morajo biti prazni vsi stolpci razen `št. Koraka`, `Tip podatka`, `Tip objekta` in `Zavihek`; koda napake `CRTA_COLUMN_NOT_EMPTY`; regresijski testi *(11. 6. 2026, ~25 min)*
- **field/** `spustniseznam_vrednost_rule` - Pri `Tip objekta = spustniseznam` mora biti stolpec `Vrednost` zapolnjen (oznaka šifranta); koda napake `SPUSTNISEZNAM_VREDNOST_EMPTY`; regresijski testi *(11. 6. 2026, ~20 min)*
- **web/** `skupno poročilo (batch)` - Pri validaciji več receptur hkrati se generira skupno poročilo za celoten batch (Excel/JSON/TXT/management, list označen kot `datoteka:list`); nov endpoint `GET /api/jobs/{id}/report/{name}` in razdelek »Skupna poročila« v UI *(10. 6. 2026, ~1 h)*
- **web/** `validacija tipov datotek` - Ob nalaganju se preverjajo končnice (recepture `.xlsx`/`.xlsm`, SOP `.docx`, šifranti `.xlsx`/`.xlsm`); napačen tip vrne HTTP 415; frontend pri drag & drop filtrira nepodprte datoteke *(10. 6. 2026, ~30 min)*
- **web/** `test_web_api.py` - Pytest testi za spletni API: endpointi, validacija uploadov (napačne končnice, neveljaven config), E2E validacija `MOD-QA.xlsx` s prenosom vseh poročil, batch s skupnim poročilom, zaščita pred path traversal (10 testov) *(10. 6. 2026, ~1 h)*

- **docs/** `PROMPT_WEB_APLIKACIJA.md` - Celotna specifikacija/prompt za intranet spletno aplikacijo (arhitektura, API, deployment, MVP, faza 2, testni scenariji) *(5. 6. 2026, ~20 min)*
- **web/** `spletna aplikacija` - Nova spletna plast (UI + API) nad obstoječim `ValidatorEngine` (brez sprememb validacijske logike): FastAPI backend (`web/backend/` — `app.py`, `jobs.py`, `service.py`, `rules_catalog.py`, `schemas.py`, `settings.py`) z endpointi za nalaganje receptur (+ SOP/šifranti), zagonom validacije v ozadju (ThreadPoolExecutor) z napredkom, pregledom rezultatov in prenosom poročil (Excel/JSON/TXT/management/auto-fix); React frontend brez build koraka (vendorani React/ReactDOM/Babel za offline delovanje) z nalaganjem, konfiguracijo, filtri/grupiranjem rezultatov in prenosi; zaganjalnik `run_web.py`, `web/requirements-web.txt`, on-prem deployment (`web/deploy/` — Dockerfile, docker-compose, nginx, `.dockerignore`) za interno omrežje; smoke-test celotnega toka uspešen *(5. 6. 2026, ~6 h)*
- **docs/** `OPIS_PROGRAMA.md` - Tehnični opis programa (arhitektura, design patterns, data flow, module overview) namenjen programerju; dokument v `docs/Dokumentacija/` *(1. 6. 2026, ~30 min)*
- **rules/** `catalog_code_rule` - Novo pravilo za preverjanje šifer raztopin in kemikalij proti zunanjim šifrantom (Izvoz_sifre_razt.xlsx, Izvoz_kem.xlsx); integracija obstoječe skripte `primerjaj_sifre_raztopin.py` v validator kot SheetRule z dependency injection; dodan `excel/catalog_loader.py` modul za nalaganje katalogov, razširjena konfiguracija (`catalog_raztopine_path`, `catalog_kemikalije_path`, `enable_catalog_validation`), dodana GUI polja za izbiro šifrantov *(26. 5. 2026, ~2 h)*

### Changed
- **ui/** `input_files`, `main_window`, `main_window_themed`, `main_window_qt` - Ob zagonu validacije datotek v mapi `staro` se prikaže jasno sporočilo, da je datoteka arhivska in validacija ni bila izvedena (namesto zavajajočega sporočila o manjkajočih stolpcih); ločeno sporočilo ostane za datoteke brez `REQUIRED_COLUMNS` *(3. 8. 2026, ~25 min)*
- **web/** `frontend naslov` - Prikazni naslov spletne aplikacije usklajen z desktop GUI: »MES Excel Validator« → »IPO Excel Validator« (zavihek brskalnika, glava, prijavno okno, logotip IPO); FastAPI naslov v `/docs` *(22. 7. 2026, ~10 min)*
- **core/** `validator_engine` - `validate_loaded()` zdaj RuleEngine-u podaja tudi `all_workbook_data`/`all_workbook_headers` (privzeto iz `LoadedWorkbook`), da SOP compliance pravilo deluje tudi pri SQL viru; povratno združljivo z Excel tokom *(21. 7. 2026, ~20 min)*
- **docs/** `SQL_integracija_notes.md` - Zapiski nadgrajeni v dokumentacijo implementirane integracije (env/mapping/DDL/CLI/web/testiranje, seznam za potrditev z MES adminom); `README.md` dobil razdelek »MES/MySQL vir«; `.gitignore` dopolnjen z `.env` *(21. 7. 2026, ~45 min)*
- **core/** `constants` - Dodana prevoda kod `SECTION_COUNT_MISMATCH` in `SECTION_TITLE_MISMATCH` za primerjavo razdelkov (aditivno, brez posega v pravila) *(21. 7. 2026, ~10 min)*
- **ui/** `main_window`, `main_window_themed`, `main_window_qt` - Gumb »Primerjaj razdelke med listi« zdaj dejansko izvede primerjavo (nov modul `excel/section_compare.py`) in zapiše poročilo .xlsx/.txt; prej samo sporočilo »še ni implementirano« *(21. 7. 2026, ~45 min)*
- **web/** `jobs.py` - Job dobi lastnika (prijavljen uporabnik) in `on_complete` hook za trajno zgodovino/audit ob zaključku *(21. 7. 2026, ~30 min)*
- **web/** `README.md` - Dokumentacija faze 2: novi endpointi, role in pravice, lokalni uporabniki, zgodovina/audit, razširjena tabela okoljskih spremenljivk, HTTPS napotki *(21. 7. 2026, ~40 min)*
- **ui/** `input_files` - Datoteke iz podmape `staro` (tudi zapis `Staro`) se zdaj vedno preskočijo pred validacijo, tudi pri ročno izbranih datotekah *(17. 6. 2026, ~15 min)*
- **ui/** `input_files`, `main_window`, `main_window_themed`, `main_window_qt` - Pri izboru in skeniranju map so podprte tudi datoteke `.xlsm` (poleg `.xlsx` in `.xls`), zato se recepture v makro datotekah ne preskočijo več *(17. 6. 2026, ~10 min)*
- **excel/** `recipe_workbook` - Filter receptur v GUI je zaostren: datoteka se validira samo, če ima vsaj en list z vsemi zahtevanimi stolpci (`REQUIRED_COLUMNS`), ne več samo z delnim ujemanjem *(17. 6. 2026, ~20 min)*
- **ui/** `main_window`, `main_window_themed`, `main_window_qt` - Pri izboru mape in ob zagonu validacije se preskočijo Excel datoteke brez zahtevanih stolpcev recepture (`REQUIRED_COLUMNS`); validirajo se le datoteke z vsaj enim listom, ki vsebuje IPO stolpce *(17. 6. 2026, ~40 min)*
- **ui/** `main_window`, `main_window_themed`, `main_window_qt` - Dodan gumb za izbor mape z recepturami; iz izbrane mape se samodejno dodajo vse Excel datoteke (`.xlsx`, `.xls`) in preskočijo vse datoteke v mapi `staro`; enako velja tudi za ročno vnesene poti map *(17. 6. 2026, ~45 min)*
- **.gitignore** - Dodana `venv/` in `.venv/`; obstoječi `__pycache__/` odstranjen iz git sledenja (`git rm --cached`) *(11. 6. 2026, ~5 min)*
- **core/** `REQUIRED_COLUMNS` - Dodanih 12 stolpcev kontrol (`Kontrola 1`–`Kontrola 4` s parametroma `par 1`/`par 2`) v skladu z IPO strukturo recepture *(11. 6. 2026, ~10 min)*
- **web/** `frontend redesign` - Sartorius črno-rumena tema (header `#000000`, akcent `#FFE600`, ozadje `#f5f5f5` — usklajeno s PyQt6 GUI); novi filtri po listu in kodi napake, razvrščanje po stolpcih tabele, graf napak po kodah (top 12, brez zunanjih knjižnic), kliklive ploščice povzetka kot filtri, strni/razširi vse skupine, gumb »Nova validacija«, slovenski statusi datotek, ohranitev konfiguracije v localStorage, gumb »Počisti filtre« *(10. 6. 2026, ~2 h 30 min)*
- **field/** `data_object_compatibility` - Dodano eksplicitno pravilo: pri tipu podatka `masa` tip objekta ne sme biti `formula`, `formula0` ali `formula1`; dodani regresijski testi za vse tri variante *(27. 5. 2026, ~20 min)*
- **excel/** `report_writer` - Poročilo vsebuje blok o preverjanju šifrantov na listu Povzetek in nov list Šifranti; prevod kode `CATALOG_CODE_MISMATCH` *(26. 5. 2026, ~45 min)*
- **ui/** `main_window`, `main_window_themed` - Skupna naloga šifrantov, status po validaciji, povzetek v poročilu; classic GUI ima polja za šifrante kot themed *(26. 5. 2026, ~40 min)*
- **core/** `validator_engine` - Metapodatki `catalog_validation` v ValidationReport po validaciji *(26. 5. 2026, ~20 min)*
- **rules/** `main.py` - CLI `--catalog-raztopine` / `--catalog-kemikalije`; uvoz `catalog_code_rule` za PyInstaller *(26. 5. 2026, ~15 min)*

### Removed
- **docs/** `samples`, `scripts` - Odstranjeni zastareli vzorci poročil, stara dokumentacija in pomožni skripti *(11. 11. 2026, ~30 min)*
- **ui/** `main_window`, `main_window_themed`, `main_window_qt` - Iz desktop GUI odstranjeno SOP preverjanje: polje za izbiro SOP datoteke (Word), gumb »Zaženi validacijo s SOP«, `_pick_sop`, `_run_validation_with_sop` ter vsi parametri `sop_data`; SOP pravilo ostane v jedru (CLI, splet) *(15. 10. 2026, ~30 min)*
- **field/** `water_not_masa_rule` - Odstranjeno opozorilo `MASS_WATER_SHOULD_BE_VOLUME` (ključ dH2O s tipom `masa` ni več napaka) *(22. 9. 2026, ~15 min)*
- **control/** `zaklenipolja_param1_odvecni_koraki_rule` - Odstranjeno preverjanje odvečnih korakov v Param1 pri `zaklenipolja` (koda `LOCK_P1_EXTRA_STEPS`) *(26. 8. 2026, ~20 min)*
- **excel/** `management_report` - Odstranjen modul poročila za vodstvo (.md) ter gumb v GUI (classic, themed, qt) in generiranje v spletnem API-ju *(11. 6. 2026, ~20 min)*

### Fixed
- **utils/** `validation_progress` - Čas validacije v `validation_progress.json` je lokalni (npr. `09:28+02:00`), ne več UTC (`07:28+00:00`); popravljen tudi zapis 793 *(29. 9. 2026, ~10 min)*
- **utils/** `base_key_no_trailing_number` / `catalog_code_rule` - Instanca na koncu črkovne šifre kemikalije (`EtOH1`, `NaCl2`) se ujema s šifrantom brez številke (`EtOH`, `NaCl`); `H2SO4` ostane nespremenjen *(3. 9. 2026, ~25 min)*
- **control/** `kontrola_interval_advanced_rule` - Navodilo v slogu `≥ 10 - 11 CV (≥ 4000 - 4400 mL)` se obravnava kot razpon (Par 2 = zgornja meja + korak), ne kot odprta neenačba `≥` brez zgornje meje *(20. 8. 2026, ~45 min)*
- **excel/** `catalog_loader` - Pri branju glave kataloga se preskočijo celice brez indeksa stolpca (`cell.column is None`), da odpravimo napako tipa basedpyright *(21. 7. 2026, ~10 min)*
- **utils/** `base_key_no_trailing_number` / `strip_instance_suffix` - Oštevilčenje instance na koncu ključa (npr. `-GK1`, `-GK10` → `-GK`) se odstrani brez poseganja v kemijsko formulo (`pH5.0`, `H2SO4`); enaka logika v šifrantu in kontroli Par1 *(27. 5. 2026, ~40 min)*
- **rules/** `catalog_code_rule` - Ena napaka `CATALOG_CODE_MISMATCH` na bazo ključa (npr. `…-GK`), ne ločeno za vsako instanco `GK1`…`GK10` *(27. 5. 2026, ~20 min)*
- **relational/** `mass_owner_rule` - Ujemanje mase z lastnikom pri iskanju para normalizira vodilni decimalni del ključa (npr. `0.30...` -> `0.3...`), zato se pri različnih zapisih iste baze pravilno sproži napaka neujemanja ključev (`PAIR_MASS_SECTION_MISMATCH`) *(27. 5. 2026, ~35 min)*
- **relational/** `key_numbering_rule` - Oštevilčenje ključev (`KEY_NUM_NOT_FROM_ONE`, `KEY_NUM_GAP`) velja le za pripono `_N` (npr. `KEY_1`); ključi s številkami v imenu brez podčrtaja (npr. `H2SO4`) ne sprožijo več lažne napake *(25. 5. 2026, ~25 min)*
- **field/** `no_spaces_rule` - Stolpec `Vrednost` izključen iz preverjanja presledkov (`SPACE_NOT_ALLOWED`); presledki v `Vrednost` so dovoljeni kot v `Navodilo` in `Labela` *(25. 5. 2026, ~10 min)*
- **field/** `no_spaces_rule` - `SPACE_NOT_ALLOWED` samo za presledek v **vmesnosti** vrednosti; robni presledki (npr. v `Vrednost`) ne sprožijo več napake; rob pri `Ključ preverjanja` obravnava `key_validation` *(25. 5. 2026, ~20 min)*
- **field/** `key_validation` - Presledek v `Ključ preverjanja` na začetku ali koncu se zazna iz surove vrednosti celice (brez strip); sporočilo `KEY_INVALID_FORMAT` z besedilom o robnem presledku; presledek v sredini ključa ostane pri `no_spaces_rule` (`SPACE_NOT_ALLOWED`) *(25. 5. 2026, ~25 min)*

### Added
- **excel/** `management_report` – Nov modul `management_report.py`: generira Markdown poročilo za vodstvo iz rezultatov validacije (skupno število napak, tabela po listih, tabela po kodah, podrobnosti za vsako kodo z lokacijami); dodan gumb "Pripravi poročilo o validaciji" v vse tri GUI variante (classic, themed, qt) — po kliku se odpre dialog za shranjevanje `.md` datoteke in ponudi odpiranje datoteke. *(21. 4. 2026, ~45 min)*
- **excel/** `report_writer` – Dodan nov list `Po listih` z grupirano vsoto napak po imenu lista recepture in vrstico `SKUPAJ`; stolpec datuma v `Povzetek` razširjen z uro validacije (`Datum in ura`, format `dd. mm. YYYY HH:MM`); odstranjen stolpec `Delež (%)` iz lista `Število napak`. *(21. 4. 2026, ~20 min)*
- **docs/** `NAv.md` (zunanji dokument) – Posodobitev navodil za tehnologe v skladu s trenutnim projektom: popravek `šft. Koraka` → `št. Koraka` (10 pojavitev), dodana `Tip podatka` vrednosti `merilnik` in `naprava`, dodanih 18 manjkajočih kontrol v tabelo veljavnih kontrol (`kontrolaintervala`, `kontrolarazmerjakemikalij`, `kontrolaprazneembalaze`, `kontrolaustreznostiopremeizmase`, `kontrolaveljavnostirepro`, `kontrolaustreznostirepro`, `kontrolaprimernostirepro`, `kontrolaprimernostitelesainpokrova`, `prenosrepro`, `prenosset`, `kontrolaistizapis`, `kontrolaustreznostimonomerne`, `kontrolaveljavnostimonomerne`, `kontrolaustreznostiseta`, `kontrolaveljavnostiseta`, `kontrolaustreznostilinije`, `odpispraznemm`), popravljene napačne kode napak (`TIP_OBJEKTA_UNKNOWN` → `OBJECT_TYPE_UNKNOWN`, `LABELA_KODA` → `LABEL_MUST_BE_KODA`, `KEY_FORMAT` → `KEY_INVALID_FORMAT`, `ZAKLENI_PAR1_FORMAT` → `LOCK_P1_FORMAT`), verzija dokumenta 1.1 → 1.2. *(20. 4. 2026, ~30 min)*
- **docs/** `ARHITEKTURA_PROJEKTA.md` – Pregled in dopolnitev arhitekturne dokumentacije: dodani `__main__.py`, 7 novih testnih datotek (`test_engines.py`, `test_validator.py`, `test_rules.py`, `test_shared_context.py`, `test_excel_loader.py`, `test_sop_compliance_rule.py`, `test_control_rule_matrix.py`), nova skripta `check_clean_workspace.py`, mapa `analytics_out/`, posodobljeno število pravil (control: 18→21, skupaj 40), posodobljene velikosti datotek (`control.py` 2042 vrstic, `sop_compliance_rule.py` 1550 vrstic), formalizirani `__init__.py` javni API moduli, posodobljene vrzeli v testiranju. *(20. 4. 2026, ~30 min)*
- **docs/** `Navodila_KL/NAV-157_Navodila_KL_priprava_recepture.md` – Nova celovita navodila za KL tehnologe za pripravo Excel recepture za IPO sistem (14 tematskih sklopov: struktura listov, dve varianti `Receptura`/`Receptura_2`, list `Podatki` z `INDEX/MATCH`, obvezni stolpci, vrednosti `Tip objekta`/`Tip podatka`, ključ preverjanja, kontrole s kombinacijami, vloge `ROLE_HEAD`/`ROLE_OPERATOR`, posebni tipi vrstic, korak po korak, tabela napak z rešitvami, validacija); pripravljeno na podlagi NAV-157 v1, Kratka navodila KL IPO in vzorčne `Receptura.xlsm`. *(20. 4. 2026, ~2 h)*
- **docs/** `NAV-158_Navodila_Validator.md` – Lektorski pregled: popravljene gramatične napake in neformalni izrazi (večih→več, Sumarni→Zbirni, ni dovoljeno→ni dovoljen, Excel napako→Excelovo napako, imata lista, pri vrstici, obnovljeno kodiranje, popravljena tabela v razdelku 7). *(27. 3. 2026, ~15 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Posodobljeno besedilo o sprejemljivosti recepture (razdelek 3.6, 3.3, 2, 5): pripravljalec mora vsako napako validatorja individualno preveriti in presoditi; receptura je primerna za prenos v proizvodnjo tudi, če napaka ne odraža dejanske nepravilnosti; verzija dokumenta 4. *(25. 3. 2026, ~20 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Vse kode napak v razdelkih 4.1, 4.3 in 4.4 posodobljene iz slovenščine v dejanske angleške kode iz izvorne kode validatorja; dodane manjkajoče kode `KEY_DUP_MASS`, `KEY_DUP_MASS_SECTION`, `CTRL_INVALID_CONTEXT`, `SOLUTION_KEY_MISSING`; verzija dokumenta 3. *(25. 3. 2026, ~45 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Navodila za uporabo aplikacije IPO Validator: zagon, opis vmesnika, postopek validacije, razlaga poročila, opis vseh napak in rešitev; odstranjene vsebine o SOP validaciji; vse kode napak v 4.1–4.4 posodobljene na dejanske kode iz izvorne kode. *(25. 3. 2026, ~1 h 30 min)*
- **docs/** `NAV-157_Navodila_IPO_receptura.md` – Appendix A razširjen in posodobljen z dejanskimi kodami iz izvorne kode; razdeljeno po modulih (strukturne, polja, relacijske, kontrole) s 30+ kodami namesto starih 9 napačnih. *(25. 3. 2026, ~20 min)*
- **rules/** `pyrightconfig.json` – Dodana konfiguracija za basedpyright (`extraPaths: [".."]`, `venv`), ki odpravlja 4 opozorila o nerazrešenih importih `validator_oop.*` v `control.py` in ostalih modulih. *(23. 3. 2026, ~5 min)*
- **docs/** `PRAVILA_VALIDATORJA.md` – Nov dokument z opisom vseh 39 validacijskih pravil (modul, kaj preverja, kode napak, resnost). *(23. 3. 2026, ~20 min)*
- **docs/** `NAV-157_Navodila_IPO_receptura.md` – Navodila za pripravo recepture za IPO sistem prestrukturirana po predlogi NAV-157 (namen, definicije, postopek, odgovornosti, dokumentacija, zapisi o spremembah, priloge). *(19. 3. 2026, ~30 min)*

### Changed
- **rules/** `formula_step_edit_labela_rule` – Formula se lahko sklicuje tudi na korake s Tip objekta `klictehtnice1` (poleg `edit`, `formula`, `formula0`, `formula1`); posodobljena konstanta `FORMULA_REF_ALLOWED_OBJECT_TYPES` in sporočilo `FORMULA_STEP_INVALID_TYPE`. *(22. 5. 2026, ~15 min)*
- **structural/** `step_numbering` – Dodano preverjanje napačnega fizičnega vrstnega reda korakov (`STEP_OUT_OF_ORDER`): kadar korak N nastopi za korakom M kjer je N < M, se javi napaka za vsak tak korak posebej; popravljeno preverjanje vrzeli (`STEP_GAPS`), ki sedaj deluje tudi kadar koraki ne začnejo pri 1 (prej se je preskočilo); dodani 4 novi testi. *(24. 4. 2026, ~30 min)*
- **excel/** `report_writer.py` - Na list `Povzetek` v Excel poročilu dodan stolpec `Datum`, ki v vsaki vrstici izpiše datum generiranja poročila. *(16. 4. 2026, ~20 min)*
- **core/** `shared_context.py`, `rule_engine.py` - Gradnja `SharedContext` je združena v en prehod čez vrstice, številke kontrolnih stolpcev so predizračunane v kontekstu, `RuleEngine` pa pri workbook pravilih ponovno uporabi že zgrajen kontekst prvega lista; dodani ciljani testi za cache/reuse. *(9. 4. 2026, ~1 h)*
- **control/** `ExpectedControlsRule` - Priporočene kontrole za kemikalije, mase, opremo, monolite in raztopine so razdeljene v manjše helperje; dodani testi za `masa` izjeme in bolj natančno sporočilo za opremo. *(9. 4. 2026, ~45 min)*
- **control/** `ControlContextRule` - Monolitna validacija konteksta kontrol je razbita v manjše helper metode za opremo, kemikalije, raztopine, `aliIsto` in `kontrolaCasa`; dodani ciljani testi za manj pokrite veje. *(9. 4. 2026, ~1 h)*
- **control/** `control.py` - Parsanje števil in numeričnih navodil (`interval`, `±`, neenačbe) je izločeno v skupne helperje, zato je `KontrolaIntervalAdvancedRule` manj monoliten; dodani regresijski testi za več podprtih oblik `Navodilo`. *(9. 4. 2026, ~45 min)*
- **rules/** `Sprint 1 higiena in control test matrix` - Dodani `.gitignore`, skripta `scripts/check_clean_workspace.py`, pytest markerji ter ločena matrika/regresijski testi za kritične `control` scenarije; v `control.py` so intervalne kontrole konsolidirane v skupni helper. *(9. 4. 2026, ~1 h 30 min)*
- **core/** `constants.py`, `scripts/export_rules_to_docx.py` - Na seznam dovoljenih kontrol dodana nova kontrola `kontrolaustreznostilinije`. *(9. 4. 2026, ~10 min)*
- **core/** `constants.py`, `scripts/export_rules_to_docx.py` - Na seznam dovoljenih kontrol dodane nove kontrole `prenosset`, `kontrolaustreznostiseta` in `kontrolaveljavnostiseta`. *(9. 4. 2026, ~15 min)*
- **core/** `main.py` - Tipi parametrov funkcij `format_report_text` in `format_report_summary` posodobljeni iz `dict` v `Mapping[str, Any]`, da basedpyright ne javlja neujemanja z `report.to_dict()` (`MutableMapping`). *(31. 3. 2026, ~10 min)*
- **rules/** `pyrightconfig.json`, `validator_oop/__init__.py` - Dodan paketni `__init__.py` v korenu projekta, da Pylance pravilno razreši absolutne importe `validator_oop.*` in odpravi `reportMissingImports` v `main.py`. *(31. 3. 2026, ~10 min)*
- **control/** `excel_error_token_rule` - Dodano robustno globalno preverjanje Excel napak (`EXCEL_ERROR_TOKENS`) v stolpcu `Vrednost` ter v vseh `Kontrola N - par 1/2` ne glede na uporabljeno kontrolo; ob zaznavi se javi koda `EXCEL_ERROR_TOKEN`. *(27. 3. 2026, ~35 min)*
- **core/** `constants.py`, **rules/** `control.py`, `field.py`, `structural.py`, `relational.py`, `sop_compliance_rule.py`, **tests/** – Vse kode napak preimenovane iz slovenščine v angleščino (~80 kod; npr. `KONTROLA_NEZNAN` → `CTRL_UNKNOWN`, `MANJKA_STOLPEC` → `MISSING_COLUMN`, `KLJUC_NAPAKEN_FORMAT` → `KEY_INVALID_FORMAT`). Slovenski prevodi za končnega uporabnika ostajajo nespremenjeni v `CODE_TRANSLATIONS`. Vse testne datoteke posodobljene. *(25. 3. 2026, ~1 h)*
- **control/** `expected_controls_rule` - Pri tipu `tehtnica` se `kontrolaustreznostiopreme` pričakuje le, če obstaja `masa` z enakim ključem preverjanja in nepraznim stolpcem `Vrednost`. *(24. 3. 2026, ~45 min)*
- **field/** `no_spaces_rule` – Stolpec `Labela` ni več del pregleda presledkov (presledki dovoljeni v celoti, kot pri `Navodilo`). *(24. 3. 2026, ~15 min)*
- **core/** `SharedContextBuilder`, **field/** `comma_number_rule`, `no_spaces_rule` – Stolpec `column_0` (prazen naslov v prvem stolpcu Excela) ni več del validacije; izključen iz `SharedContext.columns` in iz pregleda stolpcev pri poljih. *(23. 3. 2026, ~15 min)*
- **control/** `kontrola_interval_advanced_rule` – Popravljena logika za operatorja `<` in `<=`: Param2 mora biti `= xi` (za `<`) oz. `= xi + eps` (za `<=`), ne `> xi + eps`. *(23. 3. 2026, ~20 min)*
- **control/** `kontrola_interval_advanced_rule` – Logika za izračun Param1/Param2 pri ± toleranci poenostavljena na Možnost A: `Param1 = (xpm − tpm) − eps(xpm)`, `Param2 = (xpm + tpm) + eps(xpm)`, kjer je eps korak iz decimalnih mest xpm. Odstranjene vejitve na potenca-10 / decimalna / cela toleranca. *(23. 3. 2026, ~1 h)*
- **control/** `control_context_rule` – Kontrola `aliIsto` je dovoljena samo pri tipu podatka `raztopina` ali `kemikalija` (vključno s številčno pripono, npr. `raztopina1`). *(23. 3. 2026, ~25 min)*
- **control/** `navodilo_interval_kontrolainterval_required_rule` - Zahteva po kontroli `kontrolaInterval` ob številčnem intervalu v Navodilu ne velja pri korakih s Tip objekta `checkbox` niti pri korakih z Labela `koda`. *(17. 3. 2026, ~20 min)*
- **field/** `no_spaces_rule` – V Labela dodana izjema za vrednost 'naziv opreme' (presledki dovoljeni). *(17. 3. 2026, ~5 min)*
- **field/** `no_spaces_rule` – V stolpcu Labela so pri vrednostih 'DA (kljukica)' in 'DA (kljukica)/NE (prazno)' presledki dovoljeni. *(17. 3. 2026, ~15 min)*
- **rules/** `formula_step_edit_labela_rule` - Pravilo za formule preverja samo, da so vsi sklici v `Vrednost` na korake s Tip objekta `edit`, `formula`, `formula0` ali `formula1`; zahteva po vsaj enem `edit` koraku je odstranjena. *(13. 3. 2026, ~20 min)*
- **rules/** `formula_step_edit_labela_rule` - Formula se lahko sklicuje tudi na korake s Tip objekta `formula`, `formula0` in `formula1`, ne le na `edit`. *(13. 3. 2026, ~30 min)*
- **rules/** `changelog-tracking` - Ocena časa v vnosih zdaj pomeni **celoten čas** (od ugotovitve/analize do končane implementacije in testiranja); posodobljena navodila in primeri v pravilu. *(12. 3. 2026, ~20 min)*
- **docs/** `CHANGELOG.md` - Vsi obstoječi vnosi posodobljeni na ocene celotnega časa (analiza + implementacija + testiranje); kontrolaInterval, nova pravila in večji popravki zdaj ~1 h, zmerni ~45 min. *(12. 3. 2026, ~30 min)*
- **rules/** `changelog-tracking` - Datumi v vnosih morajo biti delovni dan (pon–pet); sobota in nedelja nista dovoljeni; vsi vnosi z 15. 2. 2026 razdeljeni na različne delovne dni. *(12. 3. 2026, ~15 min)*
- **rules/** `changelog-tracking` - Pri vsakem vnosu v CHANGELOG se zdaj zahtevata tudi **datum** in ocena porabljenega časa; format *(datum, ~čas)*. *(12. 3. 2026, ~20 min)*
- **rules/** `changelog-tracking` - Pri vsakem vnosu v CHANGELOG se zdaj zahteva tudi ocena porabljenega časa (kot za človeškega programerja), npr. *(datum, ~15 min)*; v pravilo dodan razdelek z navodili za ocenjevanje. *(12. 3. 2026, ~15 min)*

### Fixed
- **core/** `main_window_themed` – V `ttk` postavitvi odstranjen `**pad` razpakiran slovar in uporabljen ekspliciten `padx/pady`, da basedpyright ne javlja napačnih tipov pri `pack()`. *(22. 5. 2026, ~10 min)*
- **relational/** `mass_owner_rule`, `duplicate_key_rule` – Lastnik mase vključuje tudi tip `monomerna` in oštevilčene variante (`monomerna1`, `monomerna2`, …); odpravljen lažni `PAIR_MASS_WITHOUT_OWNER` (npr. ključ SMM1). *(22. 5. 2026, ~25 min)*
- **control/** `kontrola_interval_param_rule` – `kontrolaInterval` vedno zahteva oba parametra (Par1 in Par2); prazen Par1 ali Par2 sproži `CTRL_INTERVAL_PARAMS` ne glede na vsebino stolpca `Navodilo` (interval v navodilu ni pogoj za uporabo kontrole). *(22. 5. 2026, ~20 min)*
- **control/** `control_context_rule` – `kontrolaustreznostiopremeizmase` je dovoljena tudi na Tip objekta `klictehtnice1` (npr. Labela `g` pri masi), ne le na spustnem seznamu ali polju `koda`. *(22. 5. 2026, ~15 min)*
- **control/** `_decimal_eq` – Lažno pozitivna napaka pri Param1 z vrednostjo enako pričakovani (npr. "3.34 = 3.34"): ko Excel formula vrne float z mikroskopsko napako plavajoče vejice (npr. `3.340000000001`), ga openpyxl prebere z dodatno natančnostjo, medtem ko `fmt()` prikaže zaokroženo vrednost "3.34". Dodana toleranca `< 1e-9` kot fallback v `_decimal_eq`, ki popravi lažno pozitivno ne da bi ogrozila zaznavo dejanskih napak (najmanjši korak je ≥ 0.01); dodana 2 regresijska testa za navodilo `≥ 5 MVS (≥ 3.35 L)` in FP šum. *(24. 4. 2026, ~45 min)*
- **control/** `kontrola_interval_advanced_rule` – Popravljena napaka plavajoče vejice pri primerjavi parametrov intervala: `eq_with_decimals` (ki temelji na `round()` in daje napačne rezultate za vrednosti kot 4.95 → `round(4.95,1)=5.0`) nadomeščena z `_decimal_eq`, ki primerja surovi niz iz Excel celice z formatiranim pričakovanim nizom prek `Decimal`; popravljeno za vse tri veje (razpon, ±, neenačbe) in oba parametra (Param1, Param2). *(22. 4. 2026, ~1 h)*
- **control/** `ExpectedControlsRule` - Oprema zdaj zahteva `kontrolaveljavnostiopreme` samo pri `Tip objekta = spustniseznam` ali kadar je `Labela = koda`; dodani regresijski testi za oba dovoljena konteksta in izjemo. *(16. 4. 2026, ~30 min)*
- **utils/** `parse_navodilo_inequality`, `derive_decimal_step_from_text` - Normaliziran zapis decimal s presledkom (npr. `2 .0`), zato `kontrolaInterval` pri navodilih `<=` pravilno izračuna Param2 (npr. `≤ 2 .0` → `2.1`, ne `3.0`). *(26. 3. 2026, ~30 min)*
- **control/** `kontrolaInterval` – Pri `±` toleranci `eps` zdaj temelji na decimalkah tolerance `t` (ne na decimalkah sredine `x`). Primer: `8 ± 0.4` pravilno zahteva `Param1=7.5` in `Param2=8.5`. *(25. 3. 2026, ~45 min)*
- **control/** `aliobstajapogoj_combo_rule`, novo `zaklenipolja_param1_odvecni_koraki_rule` – Napaka pri napačnih korakih v Param1 zaklenipolja se zdaj poroča na vrstici zaklenipolja z opozorilom „Pri zaklenipolja v Param1 so odvečni koraki: …“ namesto na vrstici z aliObstajaPogoj. *(17. 3. 2026, ~45 min)*
- **control/** `checkbox_aliobkljukan_required_rule`, `zakleni_checkbox_rule` - Pri checkboxu je `aliObkljukan` znova dovoljen in obvezen tudi skupaj s kontrolo `aliObstajaPogoj`; izjema ostaneta samo `Labela = DA (kljukica)/NE (prazno)` in kontrola `zaklenipolja`. *(13. 3. 2026, ~45 min)*
- **relational/** `time_pair_rule` - Isti exact ključ pri `datumcaszacetek/datumcaskonec` se znova javlja kot napaka znotraj istega zavihka; `crpanje` in `crpanje1` ostaneta različna ključa. *(13. 3. 2026, ~30 min)*
- **relational/** `time_pair_rule` - Pravilo za `datumcaszacetek/datumcaskonec` ne javlja več napake za "podvojen par"; preverja samo, da za vsak ključ obstaja ustrezen začetni in končni čas. *(13. 3. 2026, ~30 min)*
- **relational/** `duplicate_key_rule`, `time_pair_rule` - Časovni ključi `datumcaszacetek/datumcaskonec` se zdaj preverjajo samo v `time_pair_rule` z exact ujemanjem; `crpanje` in `crpanje1` nista več napačno obravnavana kot podvojen ključ. *(13. 3. 2026, ~45 min)*
- **relational/** `tehtnica_vrednost_rule` - Napaka za `masa < 10` se javi samo, če ima povezana vrstica `masa` v `Labela` enoto `g`; pri enoti `kg` se ne javi. *(13. 3. 2026, ~30 min)*

### Added
- **core/** `constants` - Naprava dodana med priznano opremo (EQUIPMENT_TIP_PODATKA, EQUIPMENT_KEYWORDS, STANDARD_TIP_PODATKA, DATA_OBJECT_MAPPING). *(18. 3. 2026, ~15 min)*
- **control/** `kontrolaveljavnostiopreme` - Naprava podprta kot tip opreme (EQUIPMENT_TYPES, EXPECTED_CONTROLS). *(18. 3. 2026, ~10 min)*
- **tests/** `test_equipment_detection` - Dodan unit test za prepoznavo tipa `naprava` kot opreme. *(18. 3. 2026, ~5 min)*
- **docs/** `NAVODILA_PRIPRAVA_RECEPTURE.md` - Naprava dodana med primere opreme (spustni seznam). *(18. 3. 2026, ~5 min)*
- **scripts/** `analytics_report.py` - Skripta za avtomatsko analitiko (časovne serije napak/opozoril ter trendi po kodah iz Excel poročil) z izvozom CSV in opcijskimi grafi. *(18. 3. 2026, ~1 h)*
- **core/** `_version.py` - Verzija se v git repozitoriju avtomatsko dopolnjuje s kratkim commit hashom (VERSION_UI, VERSION_REPORT); brez gita ostane statična verzija. *(18. 3. 2026, ~45 min)*
- **excel/** `report_writer.py` - Na list Povzetek v Excel poročilu dodana vrstica z verzijo aplikacije (Validator IPO Receptur, VERSION_REPORT). *(18. 3. 2026, ~15 min)*
- **core/** `constants` - Merilnik dodan med priznano opremo (EQUIPMENT_TIP_PODATKA, EQUIPMENT_KEYWORDS, STANDARD_TIP_PODATKA, DATA_OBJECT_MAPPING). *(17. 3. 2026, ~15 min)*
- **field/** `no_spaces_rule` – V vseh stolpcih in vrsticah preveri prisotnost presledkov; če ga najde, javi napako. Izjema: vrstice v stolpcu Navodilo. *(17. 3. 2026, ~30 min)*
- **tests/** `TestNoSpacesRule` – Unit testi za pravilo `no_spaces_rule` (brez presledkov, presledek v stolpcu, izjema Navodilo, začetni/končni presledek, prazne celice, več stolpcev s presledki). *(17. 3. 2026, ~15 min)*
- **control/** `masa_kontrolamase_brez_vrednosti_rule` – Pri tipu podatka 'masa' kontrola 'kontrolaMase' ni dovoljena, če je stolpec 'Vrednost' prazen. *(16. 3. 2026, ~30 min)*
- **rules/** `formula_contains_edit_step_rule` - Za tip objekta `formula`, `formula0` in `formula1` preveri, da je v enačbi v stolpcu `Vrednost` vključen vsaj en korak s Tip objekta `edit`. *(13. 3. 2026, ~45 min)*
- **field/** `checkbox_labela_rule` – Za tip objekta 'checkbox' preverjanje, da je Labela 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'. *(11. 3. 2026, ~45 min)*
- **control/** `monolit_controls_required_rule` – Za tip podatka 'monolit' (monolit1, monolit2, …) sta obvezni kontrole 'kontrolaVeljavnostiMonolita' in 'kontrolaUstreznostiMonolita'; ob manjkanju se javita napaki. *(10. 3. 2026, ~1 h)*
- **control/** `checkbox_aliobkljukan_required_rule` – Za tip podatka 'checkbox' je obvezna kontrola 'aliObkljukan'; ob manjkanju se javi napaka. *(9. 3. 2026, ~45 min)*
- **control/** `zaposleni_alipravavlogakoda_required_rule` – Za tip podatka 'zaposleni' je obvezna kontrola 'aliPravavlogaKoda'; ob manjkanju se javi napaka. *(6. 3. 2026, ~45 min)*
- **docs/** – Navodila za tehnologe za pripravo recepture za IPO sistem (`docs/NAVODILA_PRIPRAVA_RECEPTURE.md`) – posodobljena z razlago obeh variant (z zavihki / brez zavihkov) in preimenovanim sistemom iz MES v IPO; nastala z analizo vzorčnih listov `Receptura` in `Receptura_2` v datoteki `Receptura.xlsm`. *(5. 3. 2026, ~1 h)*
- **ui/** – Gumb "Zaženi validacijo s SOP" in polje za izbiro SOP datoteke (Word .docx) v GUI (main_window.py, main_window_themed.py); validacija s SOP znova na voljo. *(4. 3. 2026, ~1 h)*
- **rules/** `formula_step_edit_labela_rule` – Za tip podatka formula/formula0/formula1 preverjanje, da imajo koraki, na katere se formula sklicuje (v stolpcu Vrednost), Tip objekta 'edit'. *(3. 3. 2026, ~1 h)*
- **docs/** – Povzetek kriterijev obrazca za napredovanje (PRA-28 Priloga 2) v `docs/Obrazec_za_napredovanje_kriteriji.md` s povezavami na delo Validator OOP za izpolnjevanje obrazca. *(2. 3. 2026, ~1 h)*
- **docs/** – Poročilo o vrednosti – v `docs/Porocilo_o_vrednosti_Validator.md` dodan prihranek ob izogibanju popravkom po prenosu v MES (ukinitev stare verzije, popravek, ponovni pregled in odobritev, ponovni prenos). *(27. 2. 2026, ~45 min)*
- **docs/** – Poročilo o vrednosti (Value Report) – `docs/Porocilo_o_vrednosti_Validator.md` s konkretnimi številkami za vodstvo: časovni prihranek (prej/potem), zmanjševanje tveganja, avtonomija procesa. *(26. 2. 2026, ~1 h)*
- **docs/** - Poročilo o vrednosti programa (Business Case) – `docs/Business_Case_Validator_OOP.md` z utemeljitvijo vrednosti, koristi, stroškov in priporočili. *(25. 2. 2026, ~1 h)*

### Changed
- **core/** `constants.py` – Vse kode napak preimenovane v slovenščino (npr. MISSING_COLUMN → MANJKA_STOLPEC, CTRL_UNKNOWN → KONTROLA_NEZNAN, SOP_IPO_MISMATCH → SOP_IPO_NE_USREZA); CODE_TRANSLATIONS zdaj uporablja samo slovenske identifikatorje. *(24. 2. 2026, ~2 h)*
- **control/** `zakleni_checkbox_rule` – Koda napake preimenovana iz `CTRL_LABELA_DA_NE_NO_CHECK` v `CTRL_CHECKBOX_DA_NE_NO_ALIOB`; sporočilo: "Pri checkboxu z 'DA (kljukica)/NE (prazno)' ni dovoljena kontrola 'aliObkljukan'." *(23. 2. 2026, ~15 min)*
- **rules/** `formula_step_edit_labela_rule` – Sporočilo napake: "Korak $n, na katerega se formula sklicuje, ni pravilen!" *(20. 2. 2026, ~20 min)*
- **rules/** `formula_step_edit_labela_rule` – Preverja samo, da imajo sklicani koraki Tip objekta 'edit'; zahteva po Labela '°C' je odpravljena. *(19. 2. 2026, ~30 min)*
- **control/** `required_controls_rule` - Napaka "Manjka kontrola 'kontrolaPraznoPolje' pri vnosnem polju" se ne javi več, če so vse kontrolne kolone (npr. vse 4) že zasedene. *(18. 2. 2026, ~45 min)*
- **ui/** `main_window*.py` - Verzija v naslovu okna zdaj prikazuje `v1.1.0 (b124)`, v poročilih pa polno verzijo z datumom. Dodana `VERSION_UI` in `VERSION_REPORT`. *(20. 2. 2026, ~1 h)*
- **core/** `constants.py` - VERSION se zdaj uvozi iz `_version.py` namesto hardcoded vrednosti. Na voljo so tudi `__version__`, `__version_full__`, `BUILD`, `BUILD_DATE`. *(20. 2. 2026, ~45 min)*
- **rules/** `changelog-tracking` - Uveden nov format vnosov z modulom: `**modul/** \`pravilo\` - opis`. Moduli: control/, relational/, core/, utils/, excel/, rules/. *(20. 2. 2026, ~30 min)*
- **rules/** `changelog-tracking` - Pravilo izrecno zahteva, da se pri posodobitvi CHANGELOG vedno samo DODA nov vnos; prejšnji vnosi se ne smejo brisati ali zamenjevati, da se beležijo vse spremembe. *(17. 2. 2026, ~25 min)*
- **control/** `datumcaskonec_kontrolacasa_required_rule` - Za vse vrstice s tipom podatka `datumcasKonec` je zdaj obvezna kontrola `kontrolaCasa`; ob manjkajoči kontroli se javi napaka. *(10. 3. 2026, ~1 h)*
- **control/** `navodilo_interval_kontrolainterval_required_rule` - Če `Navodilo` vsebuje številčni interval (npr. "≥ 4 h", "3 - 6", "57.5 ± 3.0"), je obvezna kontrola `kontrolaInterval`; ob manjkajoči kontroli se javi napaka. *(10. 3. 2026, ~1 h)*
- **control/** `navodilo_interval_kontrolainterval_required_rule` - Pri tipu podatka `datumcaskonec` se kontrola `kontrolaInterval` ne zahteva niti ob številčnem intervalu v Navodilu (časovni interval pokriva `kontrolaCasa`). *(16. 2. 2026, ~30 min)*
- **control/** `datumcaskonec_kontrolacasa_required_rule`, `navodilo_interval_kontrolainterval_required_rule` - Zahteva po kontrolah `kontrolaCasa` oziroma `kontrolaInterval` ob številčnem intervalu velja samo, če je Tip objekta `edit`, `formula`, `formula0` ali `formula1`. *(13. 2. 2026, ~45 min)*
- **control/** `checkbox_aliobkljukan_required_rule` - Za checkbox z kontrolo `zaklenipolja` se kontrola `aliObkljukan` ne zahteva. *(12. 2. 2026, ~25 min)*
- **control/** `checkbox_aliobkljukan_required_rule`, `zakleni_checkbox_rule` - Pri tipu checkbox: aliObkljukan je obvezna le, če ni kontrole zaklenipolja; če je zaklenipolja, aliObkljukan ne sme biti. Opis in sporočila napak posodobljena; pravilo zakleni_checkbox_rule omejeno na vrstice s tipom podatka checkbox. *(11. 2. 2026, ~1 h)*
- **control/** `checkbox_aliobkljukan_required_rule` - aliObkljukan je obvezna samo pri Labela 'DA (kljukica)'; pri Labela 'DA (kljukica)/NE (prazno)' ali pri zaklenipolja/aliObstajaPogoj ne sme biti. *(10. 2. 2026, ~45 min)*
- **control/** `zakleni_checkbox_rule` - Pri checkboxu z 'DA (kljukica)/NE (prazno)' ali pri prisotnosti zaklenipolja/aliObstajaPogoj kontrola aliObkljukan ne sme biti; dodana prepoved pri aliObstajaPogoj in nova koda CTRL_CHECKBOX_DA_NE_NO_ALIOB, CTRL_ALIOB_NO_CHECK. *(9. 2. 2026, ~45 min)*
- **control/** `navodilo_interval_kontrolainterval_required_rule` - Sporočilo napake in opis kode `KONTROLA_INTERVAL_ZAHTEVANA` skrajšana na "Manjka kontrola 'kontrolaInterval'". *(16. 3. 2026, ~15 min)*

### Added
- **scripts/** `export_rules_to_docx` - Skripta za izvoz vseh pravil validatorja v Word dokument (Pravila_validatorja.docx). *(6. 2. 2026, ~1 h)*
- **core/** `constants` - Vak_sušilnik dodan med priznano opremo (EQUIPMENT_TIP_PODATKA, EQUIPMENT_KEYWORDS, STANDARD_TIP_PODATKA, DATA_OBJECT_MAPPING). *(5. 2. 2026, ~15 min)*
- **control/** `kontrolaveljavnostiopreme` - Vak_sušilnik podprt kot tip opreme (EQUIPMENT_TYPES, EXPECTED_CONTROLS). *(4. 2. 2026, ~15 min)*
- **core/** `constants` - Sušilnik dodan med priznano opremo (EQUIPMENT_TIP_PODATKA, EQUIPMENT_KEYWORDS, STANDARD_TIP_PODATKA, DATA_OBJECT_MAPPING). *(5. 2. 2026, ~15 min)*
- **control/** `kontrolaveljavnostiopreme` - Sušilnik podprt kot tip opreme (EQUIPMENT_TYPES, EXPECTED_CONTROLS). *(4. 2. 2026, ~15 min)*
- **rules/** `sop_compliance_rule` - Eksplicitno pravilo za konsistentnost pretokov v Podatki: Min. pretok mora biti (spodnja meja Pretok spiranje) − 1, Max. pretok (zgornja meja) + 1 za vsako vrstico; kodi napak `PODATKI_FLOW_MIN_MISMATCH`, `PODATKI_FLOW_MAX_MISMATCH`. *(3. 2. 2026, ~1 h)*
- **core/** `requirements.txt` - Nova datoteka z odvisnostmi projekta (openpyxl, PyQt6, pytest). *(20. 2. 2026, ~20 min)*
- **core/** `_version.py` - Nova datoteka z verzijo kot edini vir resnice. Vsebuje semantic version (MAJOR.MINOR.PATCH), build number in datum. *(20. 2. 2026, ~45 min)*
- **scripts/** `bump_version.py` - Skripta za avtomatsko verziranje: `--patch`, `--minor`, `--major`, `--release`. Samodejno posodobi build number in datum. *(20. 2. 2026, ~1 h)*
- **core/** `validation_progress.json` - Vsaka validacija v zapisu vsebuje zaporedno številko validacije (`zaporedna_stevilka`). Datoteka se privzeto shranjuje v mapo projekta (ne več v `~/.validator_oop/`). *(2. 2. 2026, ~45 min)*

### Changed
- **control/** `kontrolaveljavnostiraztopine`, `kontrolaustreznostiraztopine` - Dovoljeno samo polje z Labela='koda' (ni več dovoljen spustni seznam). *(27. 2. 2026, ~45 min)*
- **control/** `kontrolaveljavnostikemikalije`, `kontrolaustreznostikemikalije` - Dovoljeno samo polje z Labela='koda' (ni več dovoljen spustni seznam). *(27. 2. 2026, ~45 min)*
- **relational/** `duplicate_key_rule` - Isti ključ pri tipu 'masa' ne sme nastopati v več razdelkih; dovoljeno je samo znotraj istega razdelka. Če isti ključ nastopa v več razdelkih, se poroča napaka KEY_DUP_MASA_SECTIONS. *(26. 2. 2026, ~1 h)*
- **relational/** `duplicate_key_rule` - Za bazo ključa voda (dH2O, H2O) se ne poroča podvojen ključ za tip 'masa'; več mas vode (npr. dH2O_1, dH2O_2) je dovoljeno brez vrstice kemikalija/raztopina. *(25. 2. 2026, ~45 min)*
- **relational/** `duplicate_key_rule` - Pri preverjanju podvojenih ključev za tip 'masa' se za lastnika (kemikalija/raztopina) šteje vrstica v istem razdelku ali v kateremkoli prejšnjem razdelku. Kemikalija z isto bazo ključa (npr. EtOH) je lahko tudi več razdelkov pred maso, če vmes ni druge kemikalije/raztopine z isto bazo. *(12. 2. 2026, 14:30, ~1 h)*
- **control/** `kontrolacasa` - Kontrola se pri tipu podatka `datumcaskonec` zdaj zahteva samo, če je v Navodilu naveden časovni interval (npr. "≥ 4 h", "2 h - 2 h 15 min"). Brez intervala (npr. "Konec inkubacije") se kontrola ne zahteva. *(11. 2. 2026, 10:15, ~1 h)*

### Fixed
- **rules/** `sop_compliance_rule` – Kodi napak usklajeni s CODE_TRANSLATIONS: `SOP_SAMPLE_NOT_ALLOWED` → `SOP_VZOREC_NEDOVOLJEN`, `SOP_D_TOO_LOW` → `SOP_D_PRENIZEK`. *(24. 2. 2026, ~20 min)*
- **control/** `kontrolaInterval` - Param2 pri ± zdaj uporablja korak iz zadnje neničelne decimale tolerance (npr. 0.14 → +0.01, 0.20 → +0.1, 0.032 → +0.001), zato je 14.160 veljaven za 14.01 +/- 0.14. *(23. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Pri visoki resoluciji brez "zero-tail" tolerance (npr. 3.180 ± 0.032) je Param2 zdaj naslednji merilni korak nad zgornjo mejo (3.213), ne več 3.222. *(20. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Za tolerance z visoko resolucijo (step_pm < 0.01, npr. 14.010 ± 0.140): Param1 = xpm − (tpm + 0.01), Param2 = xpm + (tpm + 0.01). Logika za 8.0 ± 0.4 in 6.50 ± 0.10 ostane nespremenjena. *(19. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Pri decimalni toleranci ± (tudi potenca 10) Param2 mora biti naslednja vrednost nad zgornjo mejo (right_req + tolerance), ne enaka right_req. Npr. 5.5 ± 0.1 → zgornja meja 5.6, Param2 mora biti 5.7; 5.7 v recepturi je zdaj veljavno. *(18. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Pri tolerance, ki niso potenca 10 (npr. 2.00 ± 0.20), Param2 je naslednja vrednost nad right_req (2.30), ne 2.20; vrednost 2.30 v recepturi je zdaj veljavna. *(17. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Param2 pri ± je zgornja dovoljena meja (right_req); veljavno le, če vrednost zaokroži na right_req. 7.10 ± 0.1: 7.24 → veljavno, 7.25 → neveljavno; 14.010 ± 0.140: 14.160 → neveljavno. *(16. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Param2 pri ± notaciji mora biti naslednja višja vrednost nad zgornjo dovoljeno mejo (right_req), ne enaka right_req. Npr. 2.00 ± 0.20 → zgornja meja 2.20, Param2 mora biti 2.30 (prag za sprožitev napake). *(13. 2. 2026, ~1 h)*
- **control/** `kontrolaInterval` - Popravljena validacija Param2 za tolerance, ki niso potenca 10 (npr. 0.140). Vrednost se zdaj preveri s tolerančnim razponom (±tpm/4) namesto zaokroževanja na večkratnik tolerance, kar je bilo napačno. *(20. 2. 2026, ~1 h)*
- **relational/** `tehtnica_vrednost_rule` - Pri masi >= 10 je dovoljena tudi kombinacija `TEH-KLA, TEH-ANA` (ne javi več napake). *(11. 2. 2026, 09:45, ~45 min)*
- **relational/** `time_pair_rule` - Pravilo za podvojene ključe `datumcaszacetek/datumcaskonec` zdaj preverja podvojenost samo znotraj istega zavihka. Isti ključ na različnih zavihkih ni več napaka. *(11. 2. 2026, 11:00, ~45 min)*
- **control/** `zaklenipolja_unique_key_rule` - Pravilo za podvojene ključe pri kontroli `zaklenipolja` zdaj preverja podvojenost samo znotraj istega zavihka. Isti ključ na različnih zavihkih ni več napaka. *(11. 2. 2026, 11:00, ~45 min)*
- **control/** `zakleni_inverse_rule` - Napaka za korake z `aliObstajaPogoj`, ki niso navedeni v Param1 pri `zaklenipolja`, se zdaj poroča za vsak zavihek posebej. *(16. 2. 2026, 12:00, ~1 h)*

---

## [1.0.0] - 2026-02-11

### Added
- Začetna verzija Validator OOP
- Validacijska pravila za:
  - Kontrole (kontrolaCasa, kontrolaMase, kontrolaIntervala, itd.)
  - Kemikalije, raztopine, monolite
  - Opremo (tehtnica, termometer, kopel, pH meter)
  - Embalažo
  - Relacijska pravila (podvojeni ključi, manjkajoči pari)
  - SOP skladnost
- Qt grafični vmesnik
- Podpora za Excel (.xlsx) datoteke
- Sistem za beleženje napak in opozoril

---

## Kako uporabljati ta changelog

### Kategorije sprememb:
- **Added** - nove funkcionalnosti
- **Changed** - spremembe obstoječih funkcionalnosti  
- **Deprecated** - funkcionalnosti, ki bodo odstranjene
- **Removed** - odstranjene funkcionalnosti
- **Fixed** - popravki napak
- **Security** - varnostni popravki

### Format datuma in časa:
- Pri vsaki spremembi navedite datum in čas v obliki: *(dan. mesec. leto, ura:minuta)*, npr. *(12. 2. 2026, 14:30)*.

### Primer vnosa:
```markdown
## [1.1.0] - 2026-02-15

### Added
- Novo pravilo za validacijo XYZ *(12. 2. 2026, 09:00)*

### Fixed
- Popravljen bug pri preverjanju mase *(13. 2. 2026, 10:30)*
```
