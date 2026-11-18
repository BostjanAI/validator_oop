# Izvedbeni zapis FV-1, 18. november 2026

**Skupni izid pilota je FAIL.** Našli smo eno ponovljivo razliko med namenskim pravilom za zaklepanje in njegovo dokumentirano diagnostiko. Ločeno preverjanje enakovrednosti za vse tri funkcije je uspelo.

| Podatek | Vrednost |
|---|---|
| Aplikacija | Validator OOP 1.1.0, gradnja 125 |
| Referenčni commit in viri zahtev | `f5fefb8733087923b9c141db10cbfbcf9bb3a743` |
| Preverjeni kandidat in orodje | `5a3d0f4d92218d554b368483f45683737ad670ad` |
| Izvedba formalnega pilota | 18. 11. 2026 ob 09:17:34 UTC, Linux x86-64, CPython 3.12.14 |
| Orodja | Z3 4.15.3 (paket 4.15.3.0), pytest 8.4.2, Hypothesis 6.135.20, openpyxl 3.1.5, Git 2.52.0 |
| Podatki | Sintetične vrstice, simbolične vrednosti in začasne knjige. Obstoječi testi lokalnega API in preslikav uporabljajo svoje testne podatke. |
| Arhiv | [Poročilo JSON](pilot.json), SHA-256 `540871def7e9c4be7e6546f3b6c734defc1bcb7bb61d826507698f28b734bfaa`, [okolje testov](requirements-linux-py312.txt) |

Med navedenima commitoma so se spremenile samo datoteke pod `verification/`. V tem zagonu primerjamo isto produkcijsko vedenje na dveh revizijah. Zmožnost zaznavanja dejanskih sprememb preverja posebej nadzorovan test v začasnem klonu.

| Funkcija oziroma obveznost | Metoda in domena | Rezultat |
|---|---|---|
| `KontrolaIntervalParamRule.evaluate`, EQ/SPEC-interval | Primerjava obeh izvedb ter neodvisna specifikacija v Z3 na 47 parih | PASS / PASS |
| `OwnerMassPairRule.evaluate_sheet`, EQ/SPEC-owner | Enaka postopka na 34 konfiguracijah lastnika, mase in volumna | PASS / PASS |
| `ZakleniParamRule.evaluate`, EQ/SPEC-lock | Enaka postopka na 12 nizih s sintetičnim kontekstom korakov | PASS / FAIL |
| `CTRL_INTERVAL_RANGE` | SMT nad izvlečenim produkcijskim pogojem za vse pare končnih binary64 ob predpogoju uspešne pretvorbe | PASS, UNSAT za negacijo lastnosti |
| `SYNC-FRAME` | SMT nad abstraktnim enoceličnim zapisom z dovoljenjem, zaščito formule in izidom potrditve | PASS, UNSAT za negacijo lastnosti |
| `SYNC-XLSX` | Dejanska sinhronizacija in atomska objava Excelove datoteke | NOT VERIFIED, v pregledani reviziji ni sinhronizatorja |

## Odstopanje FV-1-D01

**Funkcija in vhod.** `ZakleniParamRule.evaluate`, primer `lock/08`. V sintetičnem zvezku je na vrstici 2 checkbox s kontrolo `zaklenipolja`, njegov Param1 je `2, 3`. Oba navedena koraka obstajata in imata kontrolo `aliObstajaPogoj`.

**Pričakovano.** Po NAV-158 §4.4 in navodilih za pripravo recepture ima seznam zapis brez presledkov. Specifikacija pričakuje `LOCK_P1_FORMAT` v stolpcu `Kontrola 1 - par 1`, vrstica 2.

**Opaženo.** Navedena metoda vrne prazno zaporedje, brez izjeme ali opazne spremembe vhodov. Izraz `ZakleniParamRule.INT_LIST_PATTERN` dovoli presledek ob vejici. V obeh commitih je opazovanje enako. Ob vključitvi vseh pravil `NoSpacesRule` na isti celici javi `SPACE_NOT_ALLOWED`. Dokazani vpliv je razlika v namenski diagnostiki. V polnem pogonu ta primer torej že povzroči napako.

**Razvrstitev.** Tehnično reproducirano neskladje implementacije s prepisom zahteve. Odprta ostaja odločitev lastnika pravila, ali naj namensko pravilo vrne `LOCK_P1_FORMAT` ali je splošna koda za presledek sprejemljiva in je treba posodobiti specifikacijo. Pilot ni spremenil sprejemnih meril.

**Ponovitev.** V okolju s preverjanim orodjem zaženi naslednja ukaza. Prvi vrne tudi izvorne vrstice, zahtevane ugotovitve in dejanski izid. Drugi izvede samostojni regresijski test zahteve.

```sh
python -m verification --candidate 5a3d0f4d92218d554b368483f45683737ad670ad --case lock/08
PYTHONPATH=.. python -m pytest -q verification/tests/test_regressions.py
```

## Izvedeni testi

| Izvedba na Linuxu | Rezultat | Omejitve in odstopanja |
|---|---|---|
| Obstoječa zbirka pred izvedbo, izhodišče `f5fefb8` | 685 uspešnih, 2 neuspešna, 3 preskočeni, 1 izločen | `TestStaroFolderDetection.test_detects_staro_in_path` in `test_detects_staro_case_insensitive` obravnavata poti Windows na Linuxu. Trije spletni testi zahtevajo odsotno datoteko `MOD-QA.xlsx`. Izbor `-m 'not mysql'` izloči test živega strežnika. |
| Obstoječa zbirka po izvedbi, koda kandidata `5a3d0f4` | 685 uspešnih, 2 neuspešna, 3 preskočeni, 1 izločen | Isti neuspešni in preskočeni primeri. Ukaz, vhodni obseg in okolje ustrezajo izhodišču. |
| `verification/tests` na kodi kandidata | 28 uspešnih, 1 neuspešen | Odprt regresijski test FV-1-D01 preverja pričakovano ugotovitev. Neuspeh ni označen kot pričakovani preskok ali xfail. |

Parametrizirani primeri preverjajo meje, vrstici lastnika/volumna in reference korakov. Hypothesis generira dodatne pare stotink, ključe in manjkajoče reference v širših domenah. V začasnem klonu je referenčni posnetek ostal pripet med tremi eksperimenti. Enakovreden zapis primerjave je prestal preverjanje v domeni. Spremenjena pomožna pretvorba `"0.5" → "0"` je povzročila FAIL pri primerjavi in specifikaciji. Sprememba `≤` v `<` je dala tudi ponovljiv simbolični protiprimer. Dodatni testi preverjajo opažanje izjem in stranskih učinkov ter izida INCONCLUSIVE in NOT VERIFIED. Podrobnosti ponovitve so v [navodilih](../README.md).

**Status za pregled.** Dokazila so razvojni izpis brez elektronskega podpisa. Za formalno uporabo je odprta potrditev kontroliranega izvoda zahtev, presoja FV-1-D01 ter neodvisen pregled meja modelov. Naslednja kandidata za razširitev sta napredni decimalni interval in preverjanje referenčnih šifer po potrditvi izjem v njunih specifikacijah.
