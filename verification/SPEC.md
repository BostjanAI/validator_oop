# Specifikacije pilota FV-1

Zahteve so prepisane iz dokumenta NAV-158, različica 5, datum veljavnosti 1. 9. 2026, iz revizije `f5fefb8733087923b9c141db10cbfbcf9bb3a743`. Za zapis zaklepnih korakov oba dokumenta predpisujeta enako slovnico. Številčni nabori v pilotu so meje verifikacije na sintetičnih vhodih. Podpisanega izvoda ali zapisa o odobritvi v tej reviziji nismo našli. QA mora pred uporabo za sprostitev primerjati prepis s trenutno veljavnimi odobrenimi pravili. [NAV-158](../docs/Navodila_Validator/NAV-158_Navodila_Validator.md) · [Navodila za pripravo recepture](../docs/NAVODILA_PRIPRAVA_RECEPTURE.md)

**Skupne predpostavke.** En sintetični delovni zvezek `synthetic.xlsx`, list `Pilot`, prva podatkovna vrstica 2. Klicana je navedena metoda na novem primerku pravila s kontekstom, ki ga iz vhodnih vrstic zgradi pripadajoča revizija. Brez obvodov. Stolpci in tip kontrol so znani in pravilno zapisani. Pravilo vrne iterabilno zaporedje ugotovitev. Dokumentirani veljavni primer za to pravilo vrne prazno zaporedje. Vhod s predvideno napako vrne ustrezno kodo, resnost ERROR in lokacijo na danem listu. Invarianta klicnega vmesnika je ohranitev vhodnih vrstic, konteksta in podatkov primerka med vrednotenjem. Izjema je kršitev pogodbe za definirane primere. Razvrstitev ugotovitev in dobesedno besedilo preverjamo pri enakovrednosti.

## SPEC-interval

**Funkcija.** `KontrolaIntervalParamRule.evaluate(row, context)`. Viri so razdelki NAV-158 §4.4 z identifikatorji `CTRL_INTERVAL_PARAMS`, `CTRL_INTERVAL_NOT_NUMBER` in `CTRL_INTERVAL_RANGE`.

**Vhod.** V vrstici 2 je `Kontrola 2 = kontrolainterval`. V stolpcih `Kontrola 2 - par 1` in `Kontrola 2 - par 2` je urejeni par iz množice `{"-1","-0.5","0","0.5","1","","#REF!"}`. Obe permutaciji mešanice prazne celice in Excelove napake sta zunaj domene. Tako dobimo 47 različnih parov. Oblike pokrijejo negativne meje, ničlo, enakost, obrnjeni vrstni red in veljavno povečanje.

**Postpogoji.** Za vsako prazno mejo pričakujemo `CTRL_INTERVAL_PARAMS` na njenem stolpcu. Za vsak `#REF!` pričakujemo `CTRL_INTERVAL_NOT_NUMBER` na njenem stolpcu. Če sta obe meji številski, pričakujemo natanko `CTRL_INTERVAL_RANGE` na drugem stolpcu, kadar `Par2 ≤ Par1`, sicer nič ugotovitev. Primeri vključujejo dve prazni meji in dve Excelovi napaki. Sprememba enot ali proizvodnih toleranc ni del te zahteve.

**Samostojna simbolična obveznost.** Po uspešni pretvorbi obeh mej v končni števili binary64 iz produkcijske metode izvlečemo pogoj pred neposrednim dodajanjem `CTRL_INTERVAL_RANGE`. Z3 preveri možnost `pogoj XOR NOT (Par2 > Par1)` za poljubni končni vrednosti, vključno z obema ničlama, subnormalnimi števili in robovi predstavitve. Model uporablja primerjave IEEE 754. Dokaz je pogojen z dosegljivostjo te veje in pravilnima operandovoma. Sintaksa zunaj podprte podmnožice povzroči `INCONCLUSIVE`.

**Odprto.** Prednost diagnostike pri hkratni prazni in neštevilski meji, obravnava neskončnosti/NaN ali besedil zunaj domene ter manjkajočih predpomnjenih rezultatov formul potrebujejo odločitev lastnika zahtev.

## SPEC-owner

**Funkcija.** `OwnerMassPairRule.evaluate_sheet(rows, context, row_offset=2)`. Viri so NAV-158 §4.3, `PAIR_CHEM_WITHOUT_MASS`, `PAIR_SOL_WITHOUT_MASS`, `PAIR_VOLUME_NOT_ALLOWED` in `PAIR_WATER_WITHOUT_VOLUME`.

**Vhod.** Na enem logičnem zavihku je v vrstici 2 lastnik `kemikalija` ali `raztopina` s ključem `K` ali `dH2O`. V vrstici 3 je prostor za maso, v vrstici 4 za volumen. Vsak prostor je prazen, ima isti ključ kot lastnik ali drug sintetičen ključ `ALT`. Prazen prostor je prazna preslikana vrstica na vhodu metode. Testira se že naloženi list. Izključena sta primera, kjer imata ob vodi hkrati masa in volumen isti ključ. Domena ima 34 stanj.

**Postpogoji.** Za navadni ključ izostanek mase z istim ključem javi `PAIR_CHEM_WITHOUT_MASS` ali `PAIR_SOL_WITHOUT_MASS` na lastniku. Volumen z istim navadnim ključem neodvisno javi `PAIR_VOLUME_NOT_ALLOWED` na vrstici 4. Pri ključu vode je odsotnost ustreznega volumna `PAIR_WATER_WITHOUT_VOLUME` na lastniku. Vsi izpisi kažejo stolpec `Tip podatka`. Vrstica z drugim ključem ne zadosti paru. Testiramo oba tipa lastnika in vse dovoljene kombinacije prisotnosti, tudi obe vrsti odsotni.

**Odprto.** QA naj določi pomen sočasne mase in volumna pri vodi, veljavne vzdevke in pripone vode ter področje parjenja pri več lastnikih, razdelkih in zavihkih. Odsotni ključ obravnava ločeno pravilo. Njegove veljavnosti ta pogodba ne presoja.

## SPEC-lock

**Funkcija.** `ZakleniParamRule.evaluate(row, context)`. Viri so NAV-158 §4.4, `LOCK_P1_FORMAT`, `LOCK_P1_STEP_MISSING`, `LOCK_P1_WITHOUT_CONDITION`, in navodila za pripravo recepture, primer »Checkbox korak«. V njih izrecno piše »brez presledkov«.

**Vhod.** Korak 1 je checkbox s kontrolo `zaklenipolja` v `Kontrola 1`. Koraka 2 in 3 imata `aliObstajaPogoj`. Korak 4 obstaja in nima te kontrole. Koraka 5 ni. Preverjamo neprazne, že izračunane besedilne vrednosti Param1 iz spodnje tabele. Nastavitev zahteva preverjanje pogojev. Posebna izjema za druge zaklepne checkboxe se v teh podatkih ne pojavi.

| Vrednost Param1 | Pričakovane ugotovitve |
|---|---|
| `2`, `3`, `2,3`, `3,2` | Nobena |
| `4`, `2,4` | `LOCK_P1_WITHOUT_CONDITION` |
| `5`, `3,5` | `LOCK_P1_STEP_MISSING` |
| `2, 3`, `2,`, `2.5`, `x` | `LOCK_P1_FORMAT` |

**Postpogoji.** Besedilo v domeni ustreza slovnici `[0-9]+(,[0-9]+)*` ali javi napako formata. Za sintaktično pravilen seznam morajo navedeni koraki obstajati in imeti zahtevani pogoj. Vsi izpisi so na vrstici 2, stolpec `Kontrola 1 - par 1`. Zamenjava vrstnega reda dveh različnih obstoječih pogojnih korakov ohrani veljavnost.

**Odprto.** Prazni nizi, Unicode številke, vodilne ničle, podvojene reference, surova formula namesto njene izračunane vrednosti in skupine na sosednjih zavihkih niso zajeti. Slovnica v modelu se uporabi samo na navedenih 12 nizih. Lastnik procesa naj potrdi, ali je dovoljevanje notranjega presledka zavestna sprememba zahteve.

## EQ-interval, EQ-owner, EQ-lock

Za vsako zgornjo domeno in vsak njen element `i` mora veljati `observe(reference, i) = observe(candidate, i)`. Obe opazovanji izvirata iz samostojnih klicev dejanske kode, vključno s pripadajočim graditeljem konteksta. Primerjamo vsa polja ugotovitev, njihov vrstni red in večkratnost, tip in argumente izjeme ter izpis, zajete dnevnike in spremembe stanja pri klicu. Primerjava uporabi tudi delni izhod, če generator pozneje sproži izjemo.

Ob predpostavki determinističnih klicev izčrpanje potrdi enakost teh opazovanj za točno navedene vhode. Čas izvajanja, identiteta objektov, prehodne spremembe, zunanji V/I, globalno stanje in procesne interakcije ležijo zunaj primerjave. Procesna izolacija je namenjena izbiri pravilne različice zaupanja vredne kode. Pri razširitvi na funkcijo z zunanjimi učinki je treba vpeljati dodatne opazovalce.
