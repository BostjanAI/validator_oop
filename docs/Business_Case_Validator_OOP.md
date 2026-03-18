# Poslovni primer (Business Case)  
## MES Excel Validator – Validator OOP

**Dokument:** Poslovni primer / Poročilo o vrednosti programa  
**Sistem:** MES Recipe Validator (validator_oop)  
**Verzija dokumenta:** 1.0  
**Datum:** 26. februar 2026  

---

## Povzetek za odločevalce

**Validator OOP** je specializirano orodje za validacijo Excel receptur v okviru MES (Manufacturing Execution System) v farmacevtski proizvodnji. Zmanjšuje tveganje napak v recepturah pred uvajanjem v proizvodnjo, pospešuje pregled s strani QA in proizvodnje ter podpira skladnost s standardi (GMP, GAMP5).

**Ključna sporočila:**
- **Problem:** Ročno preverjanje receptur je zamudno, napake se pogosto odkrijejo pozno.
- **Rešitev:** Avtomatizirana validacija proti 30+ pravilom (struktura, formati, relacije, kontrole, SOP).
- **Vrednost:** Prihranki pri času pregledov, manj napak v proizvodnji, dokumentirana sledljivost za validacijo.
- **Naložba:** Tržna vrednost razvoja ocenjena na **25.000–55.000 EUR** (odvisno od postavke in obsega dokumentacije).
- **Priporočilo:** Ohranjanje in nadaljnji razvoj validatorja kot strateške naložbe v kakovost in učinkovitost MES receptur.

---

## 1. Poslovna ozadje in problem

### 1.1 Kontekst

Recepture za MES so strukturirane Excel delovne zvezke z več listi, koraki, kontrolami (čas, masa, intervali, zaklenipolja itd.), kemikalijami, opremo in skladnostjo s SOP. Napake v recepturah (napačni formati, manjkajoči pari podatkov, napačne kontrole) lahko vodijo do:
- zaviranja proizvodnje ob odkritju napak v zadnjem trenutku,
- dodatnih pregledov in popravkov s strani QA in proizvodnje,
- tveganja za neskladnost s GMP, če napaka uide v proizvodnjo.

### 1.2 Opis problema

- **Ročno preverjanje** je zamudno in podvrženo človeški napaki.
- **Zahtevnost receptur** (številna pravila, relacije med polji, SOP) otežuje dosledno preverjanje brez orodja.
- **Sledljivost** za validacijo in revizije zahteva jasno dokumentirane rezultate preverjanj.

---

## 2. Rešitev: Validator OOP

### 2.1 Kaj sistem naredi

Validator OOP:
- naloži Excel recepturo (`.xlsx` / `.xlsm`),
- preveri samo liste z zahtevanimi stolpci (filtriranje listov),
- izvede **30+ validacijskih pravil** (struktura, polja, relacije, kontrole, po želji SOP),
- ustvari **poročila** (Excel, JSON, besedilo) z natančno lokacijo napak (list, vrstica, stolpec) in kodo napake,
- omogoča **CLI** (ukazna vrstica) in **GUI** (grafični vmesnik) ter opcijsko **aplikacijo popravkov** v kopijo datoteke.

Sistem je namenjen **podpori odločanja**: končno odobritev recepture in uvoz v MES opravijo po ustanovljenih postopkih pooblaščeni uslužbenci.

### 2.2 Ključne zmogljivosti

| Kategorija | Vsebina |
|------------|--------|
| **Struktura** | Zahtevani stolpci, oštevilčenje korakov |
| **Polja** | Tipi podatkov, formati ključev, formule, enote |
| **Relacije** | Enoličnost ključev, pari datum/čas, lastništvo mas, tehtnica itd. |
| **Kontrole** | Intervali, čas, masa, zaklenipolja, pogoji, oprema |
| **SOP** | Opcijsko preverjanje skladnosti z Word SOP dokumentom |
| **Izhodi** | Excel/JSON/TXT poročila, opcijsko ustvarjanje popravljene kopije |

### 2.3 Arhitektura in kakovost

- **OOP arhitektura:** ValidatorEngine, RuleEngine, Registry pravil, Row/Sheet/Workbook pravila.
- **Razširljivost:** Nova pravila z registracijo, brez spreminjanja jedra.
- **Testiranje:** 11 testnih modulov, pribl. 2.780 vrstic testov.
- **Dokumentacija:** URS, FS, OQ, Risk Assessment, SOP uporabe (tudi v dveh jezikih), kar ustreza zahtevam validacije v farmaciji.

---

## 3. Koristi (vrednost programa)

### 3.1 Kvalitativne koristi

- **Manj napak v recepturah** pred odobritvijo – sistemsko preverjanje proti fiksni množici pravil.
- **Hitrejši pregled** – QA in proizvodnja dobita strukturirano poročilo z lokacijami in kodami napak.
- **Sledljivost** – poročila in logi podpirajo revizije in dokazovanje, da so recepture preverjane na enak način.
- **Skladnost** – podpora GMP/GAMP5 z dokumentacijo (URS, FS, OQ) in nadzorom sprememb pravil.
- **Enotnost** – vsi uporabniki uporabljajo ista pravila, kar zmanjšuje neskladja med pregledovalci.

### 3.2 Kvantitativne koristi (orientacijsko)

- **Čas pregleda:** Če validacija zmanjša čas ročnega pregleda za npr. 30–50 % na recepturo, se pri večjem številu receptur letno prihrani znaten število ur.
- **Manj popravkov v zadnji fazi:** Manj odkritij napak ob uvodu v MES ali v proizvodnji pomeni manj prekinitev in manj ur za popravke.
- **Manj tveganja:** Zmanjšanje tveganja za napako v proizvodnji (kakovost, GMP) je težko natančno v denarju, vendar je pomemben del vrednosti.

### 3.3 Spremljanje napredka

Validator zapisuje rezultate validacij v **validation_progress.json** (število pregledanih datotek, napake, opozorila), kar omogoča spremljanje napredka validacije receptur in števila zaznanih napak skozi čas.

---

## 4. Stroški in naložba

### 4.1 Tržna vrednost razvoja (zamenjave)

Na podlagi obstoječih ocen projekta (obseg kode, dokumentacija, domenska kompleksnost):

| Scenarij | Ocena ur | Urna postavka | Ocenjena vrednost |
|----------|----------|----------------|-------------------|
| Minimalno (junior/mid) | 419–595 | 40 EUR/h | 17.000 – 24.000 EUR |
| Realistično (senior) | 419–595 | 60 EUR/h | 25.000 – 36.000 EUR |
| Z dokumentacijo in validacijo | + analiza, validacija, OQ | - | **35.000 – 55.000 EUR** |
| Agencija (specialist/agencija) | 419–595 | 80–100 EUR/h | 40.000 – 60.000 EUR |

**Obseg projekta:** pribl. 10.250+ vrstic produkcijske kode, 2.780 vrstic testov, 30+ modulov, 20+ dokumentov (URS, FS, OQ, Risk Assessment, SOP). Domenska kompleksnost (MES recepture, kontrole, SOP) poveča vrednost, ker zunanji izvajalec brez znanja domene potrebuje dodatni čas za razumevanje.

### 4.2 Vzdrževanje in nadaljnji razvoj

- Dopolnitve pravil, podpora novim tipom opreme in novim zahtevam iz proizvodnje/SOP so pričakovane. Ocena: redna manjša vložka (npr. 5–15 % letne “naložbe” v razvoj).
- Brez lastnega orodja bi bilo treba plačevati zunanje storitve za vsako večjo spremembo pravil ali integracijo.

---

## 5. Tveganja in ublažitev

| Tveganje | Vpliv | Ublažitev |
|----------|--------|------------|
| Spremembe formatov receptur (MES/Excel) | Srednji | Ohranjanje modularne arhitekture, posodobitve pravil in konstant (npr. `core/constants.py`). |
| Rast števila pravil in kompleksnosti | Srednji | Registry in testi omogočajo varno dodajanje pravil; dokumentacija sprememb v CHANGELOG. |
| Odvisnost od ključnih razvijalcev | Srednji | Dokumentacija (URS, FS, OQ, README, komentarji), struktura projekta in testi olajšujejo prevzem. |
| Klasifikacija GxP in odgovornost | Organizacija odloča | URS jasno opredeljuje validator kot orodje za podporo odločanja; končna odobritev pri pooblaščenih osebah. |

---

## 6. Primerjica z alternativami

| Možnost | Prednosti | Slabosti |
|---------|-----------|----------|
| **Ohranitev in razvoj Validator OOP** | Popolnoma prilagojen MES, sledljivost, dokumentacija, nadzor nad pravilami | Zahteva vzdrževanje in domensko znanje v hiši |
| **Ročno preverjanje** | Brez stroškov orodja | Zamudno, neskladno, več tveganja za napake |
| **Naročilo zunanjega razvoja** | Možno dobiti “na naročilo” | Visoki stroški (35.000–55.000 EUR+), dolg onboarding v domeno, manjši nadzor |
| **Generično validacijsko orodje** | Hitrejši začetek | Verjetno ne pokriva MES kontrol, zaklenipolja, SOP; omejena sledljivost za GMP |

---

## 7. Priporočilo

**Priporočilo:** Validator OOP obravnavati kot **strateško naložbo** v kakovost in učinkovitost obdelave MES receptur. Koristi vključujejo hitrejši in bolj dosleden pregled, manj napak pred proizvodnjo, sledljivost za validacijo in skladnost s priporočili GMP/GAMP5.

- **Obstoječi sistem:** Ohraniti v uporabi, redno posodabljati pravila in dokumentacijo ob spremembah procesov in SOP.
- **Nadaljnji razvoj:** Načrtovati glede na prioritete (nove kontrole, nove tipi opreme, izboljšave poročil ali integracije).
- **Vrednost:** Tržna vrednost razvoja (replacement cost) je ocenjena na **25.000–55.000 EUR**; s tem projektom je organizacija to vrednost že “vložila” in izognila neposrednim plačilom zunanjim izvajalcem ter skrajšala čas do uporabne rešitve.

---

## 8. Viri in reference

- **README.md** – pregled funkcionalnosti, arhitekture in uporabe.
- **CHANGELOG.md** – zgodovina sprememb pravil in modulov.
- **docs/Dokumentacija/EN/** – URS, FS, OQ, Risk Assessment, SOP (EN).
- **docs/Dokumentacija/SL/** – ista dokumentacija v slovenščini.
- **docs/Ocena_vrednosti_projekta_Validator_OOP_Opus4.6.md** – podrobna ocena ur in finančna ocena.
- **docs/ocena_vrednosti_validatorja_za_letni_razgovor.md** – sklep o vrednosti 35.000–55.000 EUR (replacement cost).

---

*Dokument pripravljen za interne odločitve glede vrednosti in nadaljnjega razvoja programa Validator OOP (MES Excel Validator).*
