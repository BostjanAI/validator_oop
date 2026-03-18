# Ocena tveganja
## Validator MES receptur

---

## Nadzor nad dokumentom

| Polje | Vrednost |
|---|---|
| **Naslov dokumenta** | Ocena tveganja |
| **Sistem / Aplikacija** | Validator MES receptur (validator_oop) |
| **ID dokumenta** | VAL-RA-001 |
| **Verzija** | 1.0 |
| **Datum** | 2026-02-04 |
| **Pripravil** | ______________________ |
| **Pregledal (QA)** | ______________________ |
| **Odobril** | ______________________ |

---

## 1. Namen

Namen te ocene tveganja je sistematično identificirati, ovrednotiti in dokumentirati tveganja, povezana z uporabo validatorja MES receptur, ter definirati ustrezne kontrole tveganj za zmanjšanje tveganj na sprejemljive ravni.

## 2. Obseg in sistemski kontekst

### 2.1 Opis sistema

Validator MES receptur je offline programsko orodje za validacijo Excel delovnih zvezkov receptur in (opcijsko) preverjanje skladnosti s SOP specifikacijami.

### 2.2 Meje ocene tveganja

**Vključeno v oceno:**
- Delovanje programske opreme Validator (GUI in CLI načini)
- Tveganja za integriteto podatkov (vhodne datoteke, validacijska logika, izhodna poročila)
- Tveganja uporabniške interakcije (nepravilno delovanje, napačna interpretacija rezultatov)
- Validacija skladnosti s SOP (opcijska funkcionalnost)

**Izključeno iz ocene:**
- Delovanje MES sistema in nadzor proizvodne opreme (Validator nima neposrednega vmesnika)
- Sistemi elektronskega podpisa (niso implementirani v validatorju)
- Avtomatizirani poteki odobritev receptur (Validator je samo orodje za podporo odločanju)

### 2.3 Izjava o predvideni uporabi

Validator je **orodje za podporo odločanju**. Rezultati validacije zagotavljajo vhod za pregled in odločanje usposobljenega osebja. Končna odgovornost za odobritev in uvoz recepture v MES ostaja pri določenih lastnikih procesov v skladu z vzpostavljenimi postopki kakovosti.

## 3. Metodologija ocene tveganja

### 3.1 Kvalitativno ocenjevanje tveganja

Ta ocena tveganja uporablja kvalitativno metodo ocenjevanja tveganja z naslednjimi lestvicami:

**S (Resnost / Severity):** Vpliv načina okvare na kakovost izdelka, varnost pacienta ali integriteto podatkov
- 1 = Zanemarljiv vpliv
- 2 = Manjši vpliv (omejen obseg, zlahka popravljen)
- 3 = Zmeren vpliv (potencialen vpliv na kakovost, brez tveganja za varnost pacienta)
- 4 = Resen vpliv (vpliv na kakovost, potencialno tveganje za varnost pacienta)
- 5 = Kritičen vpliv (neposredno tveganje za varnost pacienta ali znaten vpliv na kakovost)

**P (Verjetnost / Probability):** Verjetnost pojava načina okvare
- 1 = Redko (< 0,1% operacij)
- 2 = Malo verjetno (0,1% - 1% operacij)
- 3 = Mogoče (1% - 10% operacij)
- 4 = Verjetno (10% - 50% operacij)
- 5 = Pogosto (> 50% operacij)

**D (Zaznavnost / Detectability):** Sposobnost odkrivanja okvare pred nastankom vpliva
- 1 = Zagotovljeno odkrivanje (avtomatsko odkrivanje z jasnim opozorilom)
- 2 = Visoka verjetnost odkrivanja (odkrivanje verjetno med normalnim pregledom)
- 3 = Zmerna verjetnost odkrivanja (lahko se odkrije med pregledom)
- 4 = Nizka verjetnost odkrivanja (odkrivanje zahteva specifično preverjanje)
- 5 = Malo verjetno odkrivanje (okvaro je težko odkriti pred vplivom)

**RPN (Prioritetna številka tveganja / Risk Priority Number):** \( \text{RPN} = S \times P \times D \)

### 3.2 Kriteriji sprejemljivosti tveganja

Uporabljajo se naslednji pragovi sprejemljivosti tveganja (odvisno od odobritve organizacijske politike):

| Obseg RPN | Raven tveganja | Kriteriji sprejemljivosti |
|---|---|---|
| 1 – 20 | Nizka | Sprejemljivo brez dodatnih kontrol |
| 21 – 40 | Srednja | Sprejemljivo z dokumentirano utemeljitvijo in definiranimi kontrolami tveganja |
| 41 – 125 | Visoka | Zahteva dodatne kontrole tveganja ali modifikacijo sistema/procesa |

### 3.3 Ocena preostanka tveganja

Po implementaciji kontrol tveganja se mora preostanek tveganja ponovno oceniti in dokumentirati v oddelku 6.

## 4. GAMP klasifikacija (informativno)

**GAMP 5 kategorija:** Validator je orodje po meri/konfigurabilno z vgrajeno validacijsko logiko. Na podlagi GAMP 5 smernic je ta sistem klasificiran kot **Kategorija 4** (konfigurirana programska oprema z razširitvami po meri).

**Utemeljitev:** Sistem uporablja standardne knjižnice (`openpyxl`, `python-docx`, `tkinter`) z implementacijami validacijskih pravil po meri, specifičnimi za strukturo MES receptur.

**Pristop validacije:** Proporcionalen pristop validacije, ki sestoji iz URS, FS, ocene tveganja in OQ, s formalnim nadzorom sprememb za modifikacije validacijske logike.

## 5. Identifikacija tveganj in kontrolni ukrepi

### 5.1 Register tveganj

| ID tveganja | Nevarnost / Način okvare | Vzrok | Potencialni vpliv | S | P | D | RPN |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **RA-01** | Lažno negativna ugotovitev: Validator ne odkrije napake v recepturi | Napaka v logiki validacijskega pravila; nepričakovana variacija Excel formata; filtriranje delovnih listov izključi relevantne podatke | Neveljavna receptura nadaljuje v proizvodno uporabo; potencialen vpliv na kakovost šarže, skladnost ali varnost pacienta | 5 | 2 | 4 | 40 |
| **RA-02** | Lažno pozitivna ugotovitev: Validator poroča o napaki v veljavni recepturi | Validacijsko pravilo preveč strogo; nepričakovana variacija formata; napaka v logiki pravila | Nepotrebni popravki; zamude v proizvodnji; izguba virov | 2 | 3 | 2 | 12 |
| **RA-03** | Nepravilna generacija Excel poročila | Napaka v logiki `ReportWriter`; nezdružljiva verzija `openpyxl`; težave z dovoljenji za pisanje datotek | Uporabnik napačno interpretira rezultate; izguba dokazil validacije; nepravilni korektivni ukrepi | 3 | 2 | 3 | 18 |
| **RA-04** | Napaka pri izvajanju med branjem Excel | Poškodovana vhodna datoteka; manjkajoče programske odvisnosti; datoteka zaklenjena z drugim procesom | Validacija se ne more izvesti; zamude v proizvodnji; potrebna ročna verifikacija | 2 | 3 | 1 | 6 |
| **RA-05** | Nepravilna interpretacija formul | Nalaganje formul onemogočeno (`include_formulas=False`); parser formul ne podpira vseh tipov Excel formul | Pravila, odvisna od formul, proizvajajo nepravilne rezultate; potencialna lažno negativna ali lažno pozitivna ugotovitev | 4 | 2 | 4 | 32 |
| **RA-06** | SOP Word dokument napačno parsiran | Nestandardna struktura SOP dokumenta; OCR artefakti; omejitve `python-docx`; težave s kodiranjem | Nepravilne napake skladnosti s SOP; veljavne recepture nepravilno označene; ali neusklajene recepture niso odkrite | 4 | 2 | 4 | 32 |
| **RA-07** | Neprimerna uporaba bypass pravil (`--bypass`) | Uporabnik izključi kritično validacijsko pravilo brez odobritve QA; pomanjkanje dokumentacije bypass | Kritične napake niso odkrite; neveljavna receptura nadaljuje v uporabo | 5 | 2 | 4 | 40 |
| **RA-08** | Apply fixes spremeni nepravilne celice | Nepravilno mapiranje `target_cell`; napačen izračun `proposed_value` v pravilu | Poškodovana kopija recepture; potencialna uporaba nepravilne recepture, če je ročna verifikacija preskočena | 4 | 1 | 3 | 12 |
| **RA-09** | Nezadostna sledljivost rezultatov | Brez centraliziranega beleženja; identiteta uporabnika ni zajeta; poročila niso arhivirana na kontrolirani lokaciji | Težave pri ugotavljanju, kdo je validiral kaj in kdaj; vrzeli v revizijski sledi | 3 | 2 | 4 | 24 |
| **RA-10** | Težave s kodiranjem znakov v izpisu konzole | Konzola Windows brez UTF-8; posebni znaki v podatkih | Izpis konzole neberljiv; zmeda uporabnika; vendar Excel/besedilna poročila ostanejo berljiva | 1 | 3 | 1 | 3 |

### 5.2 Kontrolni ukrepi tveganja

**RA-01: Lažno negativna ugotovitev (RPN 40 – Srednje tveganje)**

**Preventivne kontrole:**
- Formalni nadzor sprememb za modifikacije validacijskih pravil (URS-COM-02)
- Operacijska kvalifikacija s reprezentativnimi testnimi podatki (VAL-OQ-001)
- Periodični pregled validacijskih pravil glede na trenutne formate receptur

**Detektivne kontrole:**
- Ročni pregled vseh receptur je obvezen pred uvozom v MES (proceduralna kontrola)
- Validacijska poročila vključujejo podrobne lokacije napak za verifikacijo
- Neodvisen QA pregled za kritične recepture

**Preostanek tveganja:** Srednje (odvisno od proceduralnih kontrol)

---

**RA-02: Lažno pozitivna ugotovitev (RPN 12 – Nizko tveganje)**

**Preventivne kontrole:**
- Zmogljivost bypass pravil za odobrene izjeme (parameter `--bypass` z odobritvijo QA)
- Formalni proces za prilagajanje pravil na podlagi povratnih informacij uporabnikov

**Detektivne kontrole:**
- Proces upravljanja odstopanj za sistematični pregled lažno pozitivnih ugotovitev
- Testiranje primerjave strogega načina v OQ (OQ-005)

**Preostanek tveganja:** Nizko

---

**RA-03: Nepravilno Excel poročilo (RPN 18 – Nizko tveganje)**

**Preventivne kontrole:**
- OQ testni primer za preverjanje strukture Excel poročila (OQ-003)
- Več možnosti formata poročila (Excel, JSON, besedilo) za redundanco

**Detektivne kontrole:**
- Vizualni pregled strukture poročila med pregledom validacije
- Log datoteka zagotavlja varnostno kopijo dokazil rezultatov validacije

**Preostanek tveganja:** Nizko

---

**RA-04: Napaka pri izvajanju (RPN 6 – Nizko tveganje)**

**Preventivne kontrole:**
- Jasna sporočila o napakah z navodili za korektivne ukrepe
- Preverjanje odvisnosti in navodila za namestitev v SOP
- Nadomestna možnost med GUI in CLI načini

**Detektivne kontrole:**
- Takojšnje obveščanje uporabnika o napakah pri izvajanju
- Log datoteka zajame podrobne informacije o napakah

**Preostanek tveganja:** Nizko

---

**RA-05: Napaka pri interpretaciji formul (RPN 32 – Srednje tveganje)**

**Preventivne kontrole:**
- Privzeta konfiguracija GUI omogoča nalaganje formul (`include_formulas=True`)
- OQ testni primer z validacijo formul (OQ-006)
- Dokumentirana omejitev za nepodprte tipe formul (FS oddelek 7)

**Detektivne kontrole:**
- Ročna verifikacija rezultatov validacije, odvisnih od formul, za kritične recepture
- SOP zahteva uporabniški pregled uporabnosti validacijske logike

**Preostanek tveganja:** Srednje (omiljeno z ročno verifikacijo za kritične primere)

---

**RA-06: Napaka pri parsiranju SOP (RPN 32 – Srednje tveganje)**

**Preventivne kontrole:**
- Validacija SOP je opcijska funkcionalnost
- Proces nalaganja SOP je beležen s podrobnimi informacijami o ekstrakciji
- OQ testni primer z referenčnim SOP dokumentom (OQ-008)
- QA pregled logike mapiranja SOP

**Detektivne kontrole:**
- Neuspeh nalaganja SOP rezultira v jasnem opozorilu; validacija se nadaljuje
- Proces upravljanja odstopanj za neskladja validacije, povezana s SOP

**Preostanek tveganja:** Srednje (omiljeno z opcijsko naravo in ročnim pregledom)

---

**RA-07: Neprimeren bypass pravil (RPN 40 – Srednje tveganje)**

**Preventivne kontrole:**
- SOP omejuje uporabo bypass na vlogo sistemskega skrbnika / naprednega uporabnika (VAL-SOP-USE-001)
- Uporaba bypass mora biti dokumentirana in utemeljena
- Zahtevana odobritev QA za bypass kritičnih pravil

**Detektivne kontrole:**
- OQ vključuje primerjavo osnovne vrednosti z bypass (OQ-004)
- Validacijska poročila dokumentirajo uporabljeno konfiguracijo (vključno z bypass pravili)

**Preostanek tveganja:** Srednje (odvisno od proceduralnih kontrol)

---

**RA-08: Napaka apply fixes (RPN 12 – Nizko tveganje)**

**Preventivne kontrole:**
- Apply fixes deluje samo na kopiji delovnega zvezka (nikoli ne spremeni originala)
- Jasna razlika v imenu datoteke (`_AUTOFIX.xlsx`)
- OQ testni primer preverja integriteto izvorne datoteke (OQ-007)

**Detektivne kontrole:**
- SOP zahteva obvezno ročno verifikacijo izhoda autofix pred uporabo
- Število apliciranih popravkov je beleženo in prikazano

**Preostanek tveganja:** Nizko

---

**RA-09: Nezadostna sledljivost (RPN 24 – Srednje tveganje)**

**Preventivne kontrole:**
- SOP zahteva shranjevanje validacijskih poročil na kontrolirani lokaciji
- Log datoteka `MESValidator.log` zagotavlja zgodovino izvajanja

**Detektivne kontrole:**
- Proceduralna kontrola: SOP definira zahteve za arhiviranje poročil
- Periodični revizije razpoložljivosti in popolnosti validacijskih poročil

**Preostanek tveganja:** Srednje (omiljeno s proceduralnimi kontrolami)

---

**RA-10: Težave s kodiranjem (RPN 3 – Nizko tveganje)**

**Preventivne kontrole:**
- Excel in besedilna poročila so primarni artefakti dokazil (ne izpis konzole)
- CLI uporablja statusna sporočila, varna za ASCII, kjer je primerno

**Detektivne kontrole:**
- Takojšnja vidnost nečitljivega izhoda (uporabnik lahko preklopi na pregled datoteke poročila)

**Preostanek tveganja:** Nizko

---

## 6. Povzetek preostanka tveganja in sklep

### 6.1 Povzetek preostanka tveganj

| Raven tveganja | Število | ID-ji tveganj |
|---|:---:|---|
| Nizka | 5 | RA-02, RA-03, RA-04, RA-08, RA-10 |
| Srednja | 5 | RA-01, RA-05, RA-06, RA-07, RA-09 |
| Visoka | 0 | Brez |

### 6.2 Sklep o sprejemljivosti tveganja

Z implementacijo definiranih kontrol tveganja (kvalifikacija OQ, proceduralne kontrole preko SOP, nadzor sprememb, obvezen ročni pregled) so preostanka tveganja ocenjena kot **sprejemljiva** za predvideno uporabo kot orodje za podporo odločanju.

**Odvisnosti kritičnih kontrol:**
- Validator se uporablja samo kot orodje za podporo odločanju (ne za avtonomne odločitve)
- Usposobljeno osebje pregleduje vse rezultate validacije
- Ohranjen je formalni nadzor sprememb za modifikacije validacijskih pravil
- Ponovno testiranje OQ se izvaja po pomembnih spremembah

### 6.3 Priporočila

Za postavke srednjega tveganja (RA-01, RA-05, RA-06, RA-07, RA-09) so priporočene naslednje okrepljene kontrole:
- QA pregled rezultatov validacije za kritične recepture
- Dokumentacija utemeljitev bypass pravil
- Periodični pregled uspešnosti validacijskih pravil (stopnje lažno pozitivnih/negativnih ugotovitev)
- Hranjenje validacijskih poročil kot kakovostnih zapisov

---

## Podpisi za odobritev

| Vloga | Ime | Podpis | Datum |
|---|---|---|---|
| **Pripravil** | | | |
| **Pregledal (QA)** | | | |
| **Odobril** | | | |

---

**KONEC DOKUMENTA**
