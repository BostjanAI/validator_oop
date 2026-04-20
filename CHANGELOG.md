# Changelog

Vse pomembne spremembe projekta Validator OOP so dokumentirane v tej datoteki.

Format temelji na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **docs/** `NAV-158_Navodila_Validator.md` – Lektorski pregled: popravljene gramatične napake in neformalni izrazi (večih→več, Sumarni→Zbirni, ni dovoljeno→ni dovoljen, Excel napako→Excelovo napako, imata lista, pri vrstici, obnovljeno kodiranje, popravljena tabela v razdelku 7). *(27. 3. 2026, ~15 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Posodobljeno besedilo o sprejemljivosti recepture (razdelek 3.6, 3.3, 2, 5): pripravljalec mora vsako napako validatorja individualno preveriti in presoditi; receptura je primerna za prenos v proizvodnjo tudi, če napaka ne odraža dejanske nepravilnosti; verzija dokumenta 4. *(25. 3. 2026, ~20 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Vse kode napak v razdelkih 4.1, 4.3 in 4.4 posodobljene iz slovenščine v dejanske angleške kode iz izvorne kode validatorja; dodane manjkajoče kode `KEY_DUP_MASS`, `KEY_DUP_MASS_SECTION`, `CTRL_INVALID_CONTEXT`, `SOLUTION_KEY_MISSING`; verzija dokumenta 3. *(25. 3. 2026, ~45 min)*
- **docs/** `NAV-158_Navodila_Validator.md` – Navodila za uporabo aplikacije IPO Validator: zagon, opis vmesnika, postopek validacije, razlaga poročila, opis vseh napak in rešitev; odstranjene vsebine o SOP validaciji; vse kode napak v 4.1–4.4 posodobljene na dejanske kode iz izvorne kode. *(25. 3. 2026, ~1 h 30 min)*
- **docs/** `NAV-157_Navodila_IPO_receptura.md` – Appendix A razširjen in posodobljen z dejanskimi kodami iz izvorne kode; razdeljeno po modulih (strukturne, polja, relacijske, kontrole) s 30+ kodami namesto starih 9 napačnih. *(25. 3. 2026, ~20 min)*
- **rules/** `pyrightconfig.json` – Dodana konfiguracija za basedpyright (`extraPaths: [".."]`, `venv`), ki odpravlja 4 opozorila o nerazrešenih importih `validator_oop.*` v `control.py` in ostalih modulih. *(23. 3. 2026, ~5 min)*
- **docs/** `PRAVILA_VALIDATORJA.md` – Nov dokument z opisom vseh 39 validacijskih pravil (modul, kaj preverja, kode napak, resnost). *(23. 3. 2026, ~20 min)*
- **docs/** `NAV-157_Navodila_IPO_receptura.md` – Navodila za pripravo recepture za IPO sistem prestrukturirana po predlogi NAV-157 (namen, definicije, postopek, odgovornosti, dokumentacija, zapisi o spremembah, priloge). *(19. 3. 2026, ~30 min)*

### Changed
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
- **rules/** `changelog-tracking` - Pri vsakem vnosu v CHANGELOG se zdaj zahtevata tudi **datum** in ocena porabljenega časa; format *(datum, ~čas)*. *(12. 3. 2025, ~20 min)*
- **rules/** `changelog-tracking` - Pri vsakem vnosu v CHANGELOG se zdaj zahteva tudi ocena porabljenega časa (kot za človeškega programerja), npr. *(datum, ~15 min)*; v pravilo dodan razdelek z navodili za ocenjevanje. *(12. 3. 2025, ~15 min)*

### Fixed
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
