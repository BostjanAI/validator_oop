# Specifikacija uporabniških zahtev (URS)
## Validator MES receptur

---

## Nadzor nad dokumentom

| Polje | Vrednost |
|---|---|
| **Naslov dokumenta** | Specifikacija uporabniških zahtev (URS) |
| **Sistem / Aplikacija** | Validator MES receptur (validator_oop) |
| **ID dokumenta** | VAL-URS-001 |
| **Verzija** | 1.0 |
| **Datum** | 2026-02-04 |
| **Pripravil** | ______________________ |
| **Pregledal (QA)** | ______________________ |
| **Odobril (Lastnik procesa)** | ______________________ |

---

## 1. Namen

Ta dokument določa specifikacijo uporabniških zahtev (URS) za aplikacijo Validator MES receptur. Sistem preverja skladnost in kakovost podatkov v MES Excel delovnih zvezkih (recepturah) ter generira validacijska poročila, ki identificirajo odstopanja od opredeljenih standardov kakovosti.

## 2. Obseg

### 2.1 Vključeno

- Validacija Excel delovnih zvezkov receptur (več listov) proti vnaprej definiranim naborom pravil
- Grafični uporabniški vmesnik (GUI) in vmesnik ukazne vrstice (CLI)
- Generiranje poročil v formatih Excel (`.xlsx`), besedilo (`.txt`) in JSON (`.json`)
- Opcijska validacija skladnosti s SOP specifikacijami iz Word dokumentov (`.docx`)
- Opcijska funkcija "apply fixes" (ustvarja popravljeno kopijo vhodnega delovnega zvezka)

### 2.2 Izključeno

- Neposredna kontrola ali vmesnik s proizvodno opremo ali MES sistemi
- Avtomatski uvoz receptur v MES ali avtomatski poteki odobritev receptur
- Upravljanje uporabnikov, nadzor dostopa ali funkcionalnost elektronskega podpisa znotraj aplikacije

## 3. Definicije in kratice

| Izraz | Definicija |
|---|---|
| **Validator** | Programsko orodje za preverjanje kakovosti podatkov in strukturne pravilnosti MES Excel receptur |
| **Receptura** | Excel delovni zvezek, ki vsebuje strukturirane procesne podatke z definiranimi stolpci (npr. Št. koraka, Navodilo, Tip podatka itd.) |
| **Pravilo** | Validacijska logika, ki generira napake ali opozorila (npr. manjkajoč stolpec, podvojeni koraki, kontrola intervala) |
| **OQ** | Operational Qualification (Operacijska kvalifikacija) – dokaz, da sistem deluje pravilno v predvidenem operativnem okolju |
| **SOP** | Standard Operating Procedure (Standardni operativni postopek) – referenčni dokument, ki vsebuje zahteve za dodatno validacijo |
| **MES** | Manufacturing Execution System (Sistem za vodenje proizvodnje) |

## 4. Predvidena uporaba

Validator je namenjen **interni uporabi** s strani osebja QA, proizvodnje in procesov kot **orodje za podporo odločanju** pri identificiranju napak v recepturah pred uporabo v MES ali proizvodnih okoljih. Rezultati validacije služijo kot vhod v postopke pregleda in odločanja uporabnika. Končna odgovornost za odobritev in uvoz recepture ostaja pri usposobljenem osebju v skladu z vzpostavljenimi postopki.

## 5. Predpostavke in omejitve

- Vhodne datoteke se upravljajo v skladu z internimi postopki nadzora nad dokumenti (nadzor verzij, arhiviranje, nadzor dostopa)
- Excel datoteke se obravnavajo kot vhodni podatki samo za branje. Validator ne sme spreminjati vhodnih datotek, razen če se eksplicitno uporablja funkcija "apply fixes"
- Funkcija "apply fixes" ustvari novo kopijo delovnega zvezka z razločljivim imenom datoteke. Izvorna vhodna datoteka se ne sme prepisati
- Funkcionalnost GUI zahteva razpoložljivost knjižnice `tkinter`
- Validacija SOP zahteva razpoložljivost knjižnice `python-docx`
- Operacije branja/pisanja Excel zahtevajo razpoložljivost knjižnice `openpyxl`

## 6. Uporabniške vloge

| ID vloge | Naziv vloge | Odgovornosti |
|---|---|---|
| **URS-ROLE-01** | Končni uporabnik (QA/Proizvodnja) | Izbira datotek, izvajanje validacije, pregled poročil, interpretacija rezultatov, začetek korektivnih ukrepov |
| **URS-ROLE-02** | Sistemski skrbnik / Napredni uporabnik | Upravljanje konfiguracije (CLI parametri), diagnostika (pregled logov), podpora uporabnikom, odobravanje bypass funkcij |

## 7. Uporabniške zahteve

### 7.1 Funkcionalne zahteve

| ID zahteve | Naslov | Opis |
|---|---|---|
| **URS-FR-01** | Podpora za vhodne Excel datoteke | Sistem mora podpirati izbiro in nalaganje Excel delovnih zvezkov v formatih `.xlsx` in `.xlsm` (podpora `.xls` je opcijska, kjer je tehnično izvedljivo) |
| **URS-FR-02** | Obdelava več datotek (GUI) | GUI mora podpirati izbiro ene ali več vhodnih datotek receptur in paketno izvajanje validacije |
| **URS-FR-03** | Filtriranje listov | Sistem mora validirati samo delovne liste, ki vsebujejo zahtevane stolpce receptur, kot so določeni v konfiguraciji sistema |
| **URS-FR-04** | Izvajanje validacijskih pravil | Sistem mora izvesti validacijska pravila, ki pokrivajo:<br>• Strukturne zahteve (obvezni stolpci, številčenje korakov)<br>• Zahteve na ravni polj (tip objekta, tip podatka, format ključa, formule, enote)<br>• Relacijske zahteve (unikatnost ključev, pari datum/čas, lastništvo mase)<br>• Zahteve kontrol (imena kontrol, kontekst kontrol, parametri intervala/časa, logika zaklenipolja) |
| **URS-FR-05** | Skladnost s SOP (opcijsko) | Sistem mora podpirati opcijsko nalaganje SOP specifikacijskih dokumentov iz Word formata (`.docx`) in izvajati dodatno validacijo skladnosti s SOP zahtevami |
| **URS-FR-06** | Prikaz rezultatov validacije | Sistem mora prikazati status validacije (veljavno/neveljavno) in zagotoviti seznam napak in opozoril z lokacijo (list, vrstica, stolpec) in kodo napake |
| **URS-FR-07** | Generiranje Excel poročil | Sistem mora generirati validacijska poročila v Excel formatu (`.xlsx`), ki vsebujejo minimalno:<br>• Seznam napak z lokacijami in opisi<br>• Povzetek števila napak po kodi napake |
| **URS-FR-08** | Alternativni formati poročil | Sistem mora podpirati izvoz poročil v formatih besedilo (`.txt`) in JSON (`.json`) |
| **URS-FR-09** | Konfiguracija izhodne poti | Uporabniki morajo imeti možnost določitve izhodnih poti datotek poročil preko CLI parametrov ali GUI dialogov za izbiro datotek |
| **URS-FR-10** | Strogi način | Sistem mora zagotoviti strogi validacijski način, ki obravnava opozorila kot napake |
| **URS-FR-11** | Možnost bypass pravil | Sistem mora podpirati izključitev izbranih validacijskih pravil po imenu ali kodi napake |
| **URS-FR-12** | Podpora za formule (opcijsko) | Sistem mora podpirati opcijsko validacijo z vrednotenjem formul celic (npr. formule v stolpcu "Vrednost") |
| **URS-FR-13** | Apply fixes (opcijsko) | Sistem mora zagotoviti opcijsko funkcionalnost za ustvarjanje spremenjene kopije vhodnega delovnega zvezka z apliciranimi predlaganimi popravki, kjer jih definirajo validacijska pravila |
| **URS-FR-14** | CLI izhodne kode | CLI mora vrniti standardizirane izhodne kode:<br>• `0` = validacija uspešna (brez ugotovitev na ravni ERROR)<br>• `1` = odkrite validacijske napake<br>• `2` = napaka pri izvajanju (datoteka ni berljiva, manjkajoče odvisnosti itd.) |

### 7.2 Nefunkcionalne zahteve

| ID zahteve | Naslov | Opis |
|---|---|---|
| **URS-NFR-01** | Uporabnost | GUI mora omogočiti uporabnikom izvajanje validacije brez znanja CLI, z jasnimi statusnimi sporočili in rezultati |
| **URS-NFR-02** | Združljivost z OS | Sistem mora delovati v Windows okoljih (Windows 10 in Windows 11) |
| **URS-NFR-03** | Obravnava napak | Sistem mora gracilno obravnavati neveljavne ali poškodovane vhodne datoteke ter zagotoviti jasna sporočila o napakah |
| **URS-NFR-04** | Zmogljivost | Validacija tipičnih delovnih zvezkov receptur se mora zaključiti v sprejemljivem časovnem okviru (cilj: minute, odvisno od velikosti in kompleksnosti datoteke) |
| **URS-NFR-05** | Sledljivost rezultatov | Validacijska poročila morajo vsebovati zadostne informacije za omogočanje ponovljivega pregleda (koda napake, opis, natančna lokacija) |
| **URS-NFR-06** | Integriteta podatkov | <br>• Izvorne vhodne datoteke ne smejo biti spremenjene z validacijskimi operacijami<br>• Ko se uporablja "apply fixes", mora biti izhod jasno razločen od vhoda preko imena datoteke in lokacije |
| **URS-NFR-07** | Diagnostika in beleženje | Sistem mora zagotoviti diagnostične zmogljivosti preko log datotek ali izpisa v konzolo, posebej za samostojne izvedljive distribucije |

### 7.3 Zahteve skladnosti in kakovosti

**OPOMBA:** Končna GxP klasifikacija je organizacijska odločitev. Ta URS predpostavlja uporabo kot orodje za podporo odločanju pri pregledu podatkov.

| ID zahteve | Naslov | Opis |
|---|---|---|
| **URS-COM-01** | Funkcija podpore odločanju | Sistem ne sme sprejemati avtonomnih proizvodnih odločitev. Rezultate validacije morajo interpretirati usposobljeni kadri. Končna avtoriteta odobritve ostaja pri določenih lastnikih procesov |
| **URS-COM-02** | Nadzor sprememb | Spremembe validacijskih pravil ali algoritmov morajo biti upravljane preko formalnih postopkov nadzora sprememb, vključno z dokumentacijo sprememb, oceno vpliva in ponovnim testiranjem po potrebi |
| **URS-COM-03** | Dokazilo kvalifikacije | Operacijska kvalifikacija mora zagotoviti dokumentirane dokaze, da kritične funkcije delujejo pravilno v predvidenem operativnem okolju |

## 8. Kriteriji sprejemljivosti

- Vse zahteve URS-FR in URS-NFR morajo imeti dokumentirano sledljivost do FS specifikacij in OQ testnih primerov
- OQ testni primeri se morajo izvesti brez odstopanj ali z odstopanji dokumentiranimi, ocenjenimi glede vpliva in odobrenimi s strani QA

## 9. Sledljivost

Sledljivost se vzdržuje preko:
- URS → FS mapiranje (dokumentirano v FS oddelek 4)
- URS/FS → OQ mapiranje (dokumentirano v OQ oddelek 5)

**Minimalna zahteva sledljivosti:** Vsaka URS-FR mora referencirati vsaj en FS specifikacijski element in vsaj en OQ testni primer.

## 10. Reference in priloge

### 10.1 Povezani dokumenti

- Funkcionalna specifikacija: VAL-FS-001
- Protokol operacijske kvalifikacije: VAL-OQ-001
- Ocena tveganja: VAL-RA-001
- Uporabniški SOP: VAL-SOP-USE-001

### 10.2 Lokacija testnih podatkov

- Vzorčne datoteke za OQ: `validator_oop/samples/*`
- Referenčni izhodi poročil: `validator_oop/samples/*_VALIDATION_REPORT.xlsx`

---

## Podpisi za odobritev

| Vloga | Ime | Podpis | Datum |
|---|---|---|---|
| **Pripravil** | | | |
| **Pregledal (QA)** | | | |
| **Odobril (Lastnik procesa)** | | | |

---

**KONEC DOKUMENTA**
