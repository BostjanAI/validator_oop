# Poročilo o vrednosti – MES Validator OOP

**Dokument:** Poročilo o vrednosti (Value Report)  
**Sistem:** MES Recipe Validator (validator_oop)  
**Verzija:** 1.0  
**Datum:** 26. februar 2026  

**Namembniki:** Vodstvo, odločevalci – brez predhodnega poznavanja procesa validacije receptur.

---

## Povzetek v številkah

| Kazalnik | Prej (brez Validatorja) | Potem (z Validatorjem) |
|----------|-------------------------|-------------------------|
| Čas pregleda ene recepture | **25–45 minut** ročno | **&lt; 1 minuta** (validacija v sekundah) |
| Prihranek na recepturo | — | **~25–40 minut** visoko kvalificiranega dela |
| Letni prihranek (npr. 150 receptur) | — | **~60–100 ur** |
| Dodatni prihranek | Če napaka uide v MES: cikel popravka (ukinitev stare, popravek, ponovni pregled, ponovni prenos) = več ur na incident | **Ni popravkov po prenosu** – napake se odpravi pred prenosom |
| Tveganje napake v recepturi | Prisotno (človeška napaka) | **Znižano na nič** (sistemsko preverjanje) |
| Odvisnost procesa | Od posameznika in njegove rutine | **Standardiziran proces**, neodvisen od osebe |

---

## 1. Časovni prihranek

### Prej (brez orodja)

- Ročni pregled recepture traja **X minut** (tipično **25–45 min** odvisno od kompleksnosti in števila listov).
- Pregledovalec mora ročno preveriti: strukturo, formate, relacije med polji, kontrole (čas, masa, intervali, zaklenipolja), skladnost s SOP.
- Rezultat je odvisen od pozornosti in rutine posameznika; doslednost med pregledovalci se razlikuje.

### Potem (z Validatorjem)

- Validator izvede celotno validacijo v **Y sekundah** (tipično **15–60 sekund** odvisno od velikosti datoteke).
- Pregledovalec prejme **poročilo z natančnimi lokacijami napak** (list, vrstica, stolpec, koda napake) in se osredotoči le na odločanje in popravke, ne na ročno iskanje.

### Na letni ravni

| Parameter | Primer (prilagodite svojim številkam) |
|-----------|--------------------------------------|
| Število receptur na leto | **150** |
| Povprečen čas ročnega pregleda (X) | **30 minut** |
| Čas validacije z Validatorjem (Y) | **30 sekund** |
| **Prihranek na recepturo** | 30 min − 0,5 min ≈ **29,5 minut** |
| **Letni prihranek ur** | 150 × 29,5 min = **4.425 min** ≈ **74 ure** visoko kvalificiranega dela |

**Če je vaše število receptur drugačno:**  
- 100 receptur/leto → pribl. **50 ur** prihranka  
- 200 receptur/leto → pribl. **100 ur** prihranka  

*Vrednost ene ure visoko kvalificiranega dela (QA/proizvodnja) lahko uporabite za izračun denarnega prihranka.*

### Dodatni prihranek: izogibanje popravkom po prenosu v MES

Če se napaka **ne odkrije pred prenosom recepture v MES**, ampak šele ko je receptura že v uporabi, se porabi veliko dodatnega časa:

- **Ukinitev stare verzije** recepture v MES sistemu  
- **Popravek recepture** (iskanje vzroka, sprememba, dokumentiranje)  
- **Ponoven pregled in odobritev** nove verzije (QA, proizvodnja)  
- **Ponoven prenos** v MES sistem  

Ta cikel za eno recepturo lahko stane **več ur** (koordinacija, formalni pregledi, prenos). Validator, ki napake ugotovi **pred** odobritvijo in prenosom, to dodatno porabo časa **odstrani**: napake se popravijo v Excelu, šele nato gre receptura skozi odobritev in prenos enkrat. Pri vsaki napaki, ki bi sicer ušla v MES, se tako prihrani celoten cikel popravka po prenosu.

---

## 2. Zmanjševanje tveganja

### Prej (brez orodja)

- **Ena napaka v recepturi** lahko povzroči:
  - **Reklamacijo** (napačna količina, napačen korak, neskladnost s SOP).
  - **Zastoj v proizvodnji** (ob odkritju napake ob uvodu v MES ali med izvajanjem).
  - **Dodatne popravke in revizije** (čas, stroški, porast tveganja za GMP neskladnost).
- Tveganje je odvisno od človeške pozornosti in je težko popolnoma izključiti.

### Potem (z Validatorjem)

- Validator **sistemsko preveri 30+ pravil** na vsaki recepturi (struktura, polja, relacije, kontrole, po želji SOP).
- Napake so **ugotovljene pred odobritvijo** in vnosom v MES.
- **Tveganje, da napaka v recepturi uide v proizvodnjo, se z uporabo orodja zniža na nič** (v obsegu pravil, ki jih Validator preverja). Končna odgovornost za odobritev ostaja pri pooblaščenem osebju; orodje služi kot dosledna varnostna mreža.

---

## 3. Avtonomija in standardizacija

### Prej (brez orodja)

- Proces je **odvisen od posameznika**: kdo kako dolgo gleda, kaj preveri, kako dosledno.
- Pri zamenjavi ljudi ali odsotnosti se **rutina in kakovost pregleda lahko spremenita**.
- Težko je dokazati, da so bile vse recepture preverjene na enak način (revizije, validacija).

### Potem (z Validatorjem)

- **Proces ni več odvisen od posameznika** – vsi uporabniki uporabljajo isto orodje in ista pravila.
- **Standardiziran način preverjanja**: enaka pravila za vse recepture, dokumentirana sledljivost (poročila, logi).
- S tem orodjem je **validacija receptur postopek**, ne izjema; kakovost pregleda je enakomerna ne glede na osebo.

---

## 4. Kazalniki za vodstvo (povzetek)

| Korist | Številka / sporočilo |
|--------|----------------------|
| **Časovni prihranek** | Ročni pregled: **X min** (npr. 30 min). Validator: **Y sek** (npr. 30 s). Na letni ravni: **Z prihranjenih ur** (npr. 74 ur pri 150 recepturah). **Dodatno:** če napaka uide v MES, je treba ukiniti staro verzijo, popraviti, ponovno pregledati in odobriti ter ponovno prenesti – Validator to odpravi, ker napake ugotovi pred prenosom. |
| **Zmanjševanje tveganja** | Ena napaka v recepturi → reklamacija ali zastoj. Validator to tveganje zniža na **nič** (v obsegu preverjenih pravil). |
| **Avtonomija** | Proces ni več odvisen od posameznika; preverjanje je **standardizirano** in enako za vse. |

---

## 5. Priporočilo

Validator OOP prikaže vrednost v **konkretnih številkah**: prihranek časa (prej X min, potem Y s, letno Z ur), znižanje tveganja na nič v obsegu pravil in standardiziran proces neodvisen od posameznika. Priporočilo ostaja: ohraniti in nadalje razvijati orodje kot strateško naložbo v kakovost in učinkovitost MES receptur.

---

*Številke X, Y, Z v tem dokumentu lahko prilagodite dejanskim podatkom vašega obsega receptur in merjenim časom pregledov.*
