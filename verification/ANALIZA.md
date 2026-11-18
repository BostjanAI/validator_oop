# Arhitektura in izbor funkcij

Pregled temelji na izvorni kodi veje `master` pri reviziji `f5fefb8733087923b9c141db10cbfbcf9bb3a743`. Različica iz `core/_version.py` je 1.1.0, gradnja 125. Razvrstitev spodaj je inženirska presoja za izbiro preverjanj. Lastnik procesa določi formalno GMP klasifikacijo tveganja.

## Pot od vhodne datoteke do ugotovitve

| Sklop | Kaj dejansko dela | Posledica za preverjanje |
|---|---|---|
| `main.py`, `ui/`, `run_web.py`, `web/frontend/`, `web/backend/` | CLI, namizne variante in splet pripravijo nastavitve, vire in izvoz. React uporablja spletni API. Namizna pot naloži formule, v spletni shemi je `include_formulas` privzeto izključen. | Enakost funkcij velja za enak vhod in konfiguracijo. Ujemanje poročil med vmesniki potrebuje ločen integracijski test. |
| `excel/excel_loader.py`, `workbook_parser.py`, `recipe_workbook.py` | openpyxl bere shranjene vrednosti in po izbiri še izraze formul. Parser kanonizira glave, praznim pripiše ime in se privzeto ustavi pri prvi prazni vrstici. | Manjkajoča predpomnjena vrednost, prazna vrstica ali kolizija glav lahko spremeni podatke za vsa pravila. Bralnik sam ne izračunava formul. |
| `db/mapping.py`, `sql_loader.py`, `sql_report_writer.py` | Preslikava MES stolpcev in tipov v `LoadedWorkbook`, ločen transakcijski zapis rezultatov. `schema.sql` in `migrate.py` sta namenjena namestitvi. | Formalni pilot začne pri sintetičnih vrsticah. Preizkusi MES uporabljajo dvojnike. Živa baza je izključena. |
| `core/validator_engine.py`, `rule_engine.py`, `shared_context.py`, `rules/base_rule.py`, `rule_registry.py` | Izbor listov, izdelava indeksov po ključu/koraku/zavihku, registracija in izvajanje na ravni vrstice, lista ali zvezka. Konfiguracija nadzoruje preskoke, filtriranje kod in resnost. | Napačen indeks lahko prizadene več pravil. Pilot za oba primerjana commita izdela kontekst z njuno lastno kodo. |
| `utils/helpers.py`, `excel/catalog_loader.py`, `excel/sop_loader.py` | Normalizacija ključev in glav, pretvorbe števil in časa, razčlenjevanje intervalov ter formul, dostop do referenčnih kod in podatkov SOP. | Formalni model vrstičnega pravila sam ne zagotavlja pravilne priprave vhodov iz Excel/Word. |
| `core/error.py`, `core/report.py`, `excel/report_writer.py` | Ugotovitev vsebuje kodo, resnost, lokacijo, sporočilo in morebitni predlog popravka. `ValidationReport.is_valid()` temelji na prisotnosti napak. `WorkbookFixer` je ločena pot zapisovanja. | Pri primerjavi različic je pomembna tudi sprememba ciljne celice ali vsebine predloga popravka. |
| `web/backend/app.py`, `jobs.py`, `db.py`, `history.py`; `utils/logger.py`, `validation_progress.py` | Splet beleži dogodke z uporabnikom v SQLite in ob zaključku arhivira vhod, poročila in JSON. Aktivna opravila so v pomnilniku. Lokalni log in JSON metrik imata drug namen. | Poročilo pilota ima lasten čas, commit, predpostavke in ponovitev. Niti operativni log niti ta JSON nista dokaz podpisa ali nespremenljivosti zapisa. |
| `excel/recipe_diff.py`, `section_compare.py` | `diff_recipes` primerja naložene vrednosti s poravnavo vrstic prek `SequenceMatcher`. `compare_sections` primerja razdelke receptur in njihove korake. | Primerjava receptur ne zajema vseh lastnosti datoteke OOXML. |
| `tests/`, `samples/`, `docs/`, `web/deploy/` | Testi pokrivajo pravila, skupni kontekst, pogona, nalagalnike, kataloge, SOP, DB preslikave ter API, zgodovino in audit. Označen je test živega MySQL. Vzorci vključujejo starejšo skripto, namestitev vsebuje Docker/nginx. | Referenca pilota je commit dejanskega paketa. Uporabljeni so sintetični vhodi, brez uporabe stare vzorčne skripte kot oraklja. |

## Popis vgrajenih pravil

Seznam je iz deklaracij `@register` v modulih, ki jih uvaža `rules/builtin/__init__.py`. V tej reviziji jih je 53. To je število definiranih pravil. Dejanska izvedba je odvisna od vhodnih listov, konfiguracije in razpoložljivih virov. V spodnjih skupinah je skupna končnica imen razredov `Rule`.

| Datoteka pod `rules/builtin/` | Razredi |
|---|---|
| `structural.py` (2) | RequiredColumns, StepNumbering |
| `field.py` (16) | ObjectType, MasaTipPodatka, PosebnostiTipPodatka, DataObjectCompatibility, LabelRequirements, CheckboxLabela, CrtaEmptyColumns, NaslovEmptyColumns, SpustniseznamVrednost, KeyValidation, FormulaSyntax, CommaNumber, NoSpaces, NavodiloRangeDashSpacing, FormulaReference, FormulaStepEditLabela |
| `relational.py` (9) | DuplicateKey, MassOwner, OwnerMassPair, ReproKolicinaOwner, TimePair, TimeOrder, KeyNumbering, TehtnicaMasaPair, TehtnicaVrednostFromFormula |
| `control.py` (23) | UnknownControls, ControlColumnOneReserved, ExcelErrorToken, ControlContext, RequiredControls, ExpectedControls, ZakleniParam, AliObstajaPogojCombination, AliObstajaPogojParam1, ZakleniUniqueKey, ZakleniInverse, ZakleniCheckbox, AliObkljukanParam, KontrolaIntervalParam, KontrolaIntervalAdvanced, KontrolaCasa, DatumCasKonecKontrolaCasaRequired, NavodiloIntervalKontrolaIntervalRequired, CheckboxAliObkljukanRequired, ZaposleniAliPravavlogaKodaRequired, MonolitControlsRequired, ChemicalSolutionControls, MasaKontrolaMaseBrezVrednosti |
| `catalog_code_rule.py`, `podatki_usage_rule.py`, `sop_compliance_rule.py` (po 1) | CatalogCode, PodatkiColumnUsage, SOPCompliance |

## Prednostna lista

Vhod »vrstica« pomeni preslikavo imen stolpcev v vrednosti. Kontekst je `RuleContext` s pripadajočim `SharedContext`. Pri metodah pravil je rezultat zaporedje ugotovitev. Prve tri imajo neposredno sled do NAV-158 in majhno domeno z neodvisno določljivim pričakovanjem. Naslednje so primerne za razširitev po razjasnitvi navedenih odvisnosti.

| Vrstni red in funkcija | Namen, vhod in pričakovani rezultat | Odvisnosti | Tveganje in izvedljivost |
|---|---|---|---|
| 1. `KontrolaIntervalParamRule.evaluate` | Vrstica + kontekst → ugotovitve za manjkajoča, neštevilska ali napačno urejena parametra. | Stolpci kontrol, `coerce_str`, `_parse_number`. | Enaka ali obrnjena meja je lahko sprejeta. Dobra izvedljivost za urejenost in dobesedne vnose. **Pilot.** |
| 2. `OwnerMassPairRule.evaluate_sheet` | Zaporedje vrstic + kontekst + odmik → ugotovitve za kemikalijo/raztopino brez ustrezne mase ter za posebno obravnavo volumna vode. | Indeksi po tipu in zavihku, `is_water_key`. | Napačno povezani količini. Dobra izvedljivost za eno področje ključa z enim lastnikom. **Pilot.** |
| 3. `ZakleniParamRule.evaluate` | Vrstica + kontekst → ugotovitve o zapisu seznama, obstoju in pogojnosti korakov. | Glave Param1, množica korakov, indeks kontrol, izjema za zaklepni checkbox, konfiguracija. | Napačna ciljna skupina korakov. Dobra izvedljivost za omejeno slovnico in določen kontekst. **Pilot.** |
| 4. `KontrolaIntervalAdvancedRule.evaluate` | Navodilo, oznake enot in parametri v vrstici → ugotovitve o kanonskih mejah oziroma dopustnem zaokroževanju. | `_parse_numeric_navodilo`, Decimal, natančnost, izjeme CV in info. | Meja lahko spremeni sprejem recepture. Srednja izvedljivost po ločitvi slovnice in decimalne aritmetike. Najprej uskladiti primere ±, odprtih mej in CV z lastnikom pravil. |
| 5. `MassOwnerRule.evaluate_sheet` | Vrstice in indeksi → skladnost mase s predhodnim lastnikom v ustreznem razdelku. | `_owner_match_base`, npr. posebnost ključev `razt1`/`razt2`, indeksi razdelkov. | Združitev dveh različnih lastnikov. Primerno za omejena zaporedja in permutacije. |
| 6. `TehtnicaVrednostFromFormulaRule.evaluate_sheet` | Vrstice tehtnice/mase in podatki formul → ustreznost izbire tehtnice po dokumentiranem pragu. | Razčlenjevanje INDEX/MATCH, predpomnjene vrednosti. | Napačna razvrstitev mase. Visoka izvedljivost za numerično odločitev, nižja za celotno pot formule. |
| 7. `CatalogCodeRule.evaluate_workbook` | Preslikava listov in referenčni katalogi → odstopanja kod, vključno s kodami različnih velikosti iz lista Podatki. | `match_key`, ekstrakcija Param1, formule, `CatalogData`. | Neznana šifra se ujema z napačnim izdelkom. Najprej sintetični katalog z znanimi kolizijami in manjkajočimi viri. |
| 8. `excel.catalog_loader.match_key` | Niz in `CatalogData` → ujemanje, najdena šifra in način ujemanja. | Normalizacija koncentracij, velikosti črk in pripon instanc. | Izguba pomena številke ali napačna prednost ključa. Dobra izvedljivost na končnem naboru katalogov, po potrditvi pravil za kolizije. |
| 9. `expand_usage_with_podatki_formulas` | Zbirka uporabljenih stolpcev in vrstice s formulami → razširjena uporaba prek odvisnosti na listu Podatki. | `referenced_columns_in_podatki_formula`, obsegi in dinamični sklici. | Spregledan ali napačno prijavljen stolpec. Dobra izvedljivost na majhnih grafih, tudi s cikli. |
| 10. `WorkbookParser._parse_sheet` | Delovni list openpyxl, način branja formul → zaporedje slovarjev pod glavo. | Normalizacija glav, odmik, politika prazne vrstice. | Izpuščene vrstice ali enako poimenovani stolpci. Visoka izvedljivost na sintetičnih knjigah, posebej za XLSX integracijo. |
| 11. `ColumnMapping.map_row` | Preslikava MES vrstice → slovar s kanonskimi glavami, obravnavo NULL in pretvorbo tipov. | Konfiguracija preslikav in `_transform`. | Enaki podatki lahko dajo drugačen rezultat kot Excel. Visoka izvedljivost z lokalnimi slovarji. |
| 12. `RuleEngine.run` | Preslikave listov, glave, opcijske formule in konfiguracija → končne ugotovitve. | Register, filtre in skupni kontekst uporablja za vsako raven pravil. | Preskok pomembnega pravila. Uporabiti majhen sintetičen register in preveriti pokritost posameznih poti. |
| 13. `WorkbookFixer.apply_fixes` | Vhodna in izhodna pot ter predlogi sprememb → zapisana knjiga in število izvedenih popravkov. | openpyxl, datotečni sistem, `target_cell`, `proposed_value`. | Prepis formule ali delna sprememba po napaki. Model sprememb je izvedljiv, zapis, zrušitve in makri zahtevajo integracijo. |
| 14. `diff_recipes` | Dve poti → poročilo `RecipeDiff` o vrsticah, stolpcih in vrednostih. | ExcelLoader, normalizacija nizov, SequenceMatcher. | Nezaznana sprememba formule z enako prikazano vrednostjo. Preveriti povratne primere s sintetičnimi pari datotek. |

## Izbira tehnik

| Tehnika | Kaj pomeni izid v tem projektu | Odločitev |
|---|---|---|
| Tradicionalni testi pytest | Izbrani primeri preverijo pričakovani rezultat, lokacijo ali napako. | Ohranimo obstoječo zbirko ter dodamo mejne in regresijske primere. |
| Hypothesis | Generira konkretne primere in zmanjša najdeni protiprimer. Uspeh velja za izvedeni vzorec. | Izbran za širše pare stotink, ključe in manjkajoče reference. |
| Izčrpna vedenjska primerjava | Dve dejanski implementaciji na vseh elementih navedene končne domene. Primerjamo opazovanja. Obe lahko kršita isto zahtevo. | Ločena procesa in pripeta referenčna revizija, tudi za pomožne funkcije. |
| Z3 na omejeni relaciji | Vhod ter izid dejanskih klicev tvorita končno tabelo. Neodvisne formule opišejo zahtevane ugotovitve. SAT prinese primer, UNSAT izčrpa to tabelo. | Izbran za vsa tri pravila. |
| Z3 za matematičen dokaz | UNSAT za negacijo lastnosti vseh elementov navedenega modela ob navedenih predpostavkah. | Izbran za izvlečeni numerični pogoj in abstrakten enocelični zapis. Noben dokaz ne zajema celotne aplikacije. |
| CrossHair | Simbolično izvaja poti podprte kode Python. Stanje `unknown` ali iztečen čas ne izključita napake. Regex, pretvorbe, slovarji zvezka in openpyxl otežujejo razlago pokritosti. | Kandidat za prihodnje čiste, izolirane funkcije s pogodbami. V pilotu ni meritev CrossHair. |
| Dafny | Omogoča dokaz pogodb in invariant zank na ločeni implementaciji/modelu. Potrebna bi bila dodatna vez z dejanskim Pythonom. | Smiselno za prihodnji splošni algoritem zaporedja transakcij, če analiza tveganj upraviči dokaz indukcije. |

Pri reviziji `f5fefb8` ni bilo modula ali vstopne točke za prenos izbranih sprememb med recepturama (Recipe Sync). Obstoječi primerjalnik in zapisovalnik popravkov sta ločena mehanizma. Pogodba za prihodnji zapis je v [opisu Recipe Sync](SYNC.md).
