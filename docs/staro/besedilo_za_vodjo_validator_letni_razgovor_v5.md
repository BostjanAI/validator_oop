## Besedilo za vodjo oddelka (za letni razgovor)

### Razvoj validatorja receptur – lastna iniciativa za izboljšanje kakovosti in učinkovitosti

Rad bi izpostavil **konkretno izboljšavo procesa**, ki sem jo razvil na lastno iniciativo: **avtomatiziran pregled receptur z validatorjem**. Prepoznal sem, da je ročni pregled receptur časovno potraten, nepopoln in izpostavljen človeški napaki, zato sem razvil **programsko orodje**, ki sistematično preveri kakovost receptur še pred vnosom v proizvodni proces.

**Kaj je validator?**  
Validator je **Python aplikacija**, ki prebere recepturo (Excel format), jo **sistematično preveri glede na vnaprej definirane zahteve** (strukturne, vsebinske, skladnost s SOPji) in izdela **strukturirano poročilo z vsemi odkritimi napakami** — vsaka napaka je natančno locirana (list, vrstica, stolpec) in kategorizirana. Orodje je zasnovano tako, da **standardizira pregled kakovosti** in **zagotavlja sledljivost** ter **merljivost napak**.

---

### Merljivi rezultati in vpliv na proces

**Kakovost in popolnost:**  
Na realnem primeru (poročilo `porocilo_SD.xlsx`) je validator našel **99 napak v recepturi** in jih razvrstil v **15 kategorij** (npr. manjkajoči ali podvojeni ključi, neujemanje parametrov kontrol z navodilom, nedoločen tip objekta). Poročilo omogoča **ciljno odpravljanje napak** in **analizo vzorcev** (katere napake so najpogostejše, kje so najšibkejše točke).

**Vpliv na čas in učinkovitost:**  
Ročni pregled recepture takšnega obsega zahteva **1,5–5 ur**, ker je potrebno sprotno iskati po dokumentu in preverjati pravila v več kontekstih. Z validatorjem dobimo rezultat v **nekaj sekundah**, nato pa je čas porabljen predvsem za **ciljno popravljanje napak** (tipično **10–30 min**). Prihranek časa je **približno 1–4 ure na recepturo**, kar pri več recepturah pomeni **desetine ur mesečno**.

**Vpliv na testiranje (IPO):**  
Za analizo vpliva na testiranje sem iz **logov testnih aktivnosti** pridobil podatke o trajanju testiranja za 10 različnih receptur in pripravil tabelo `Testiranje_IPO.xlsx`. Ugotovitve kažejo, da čas testiranja/obdelave recepture v testnem IPO okolju znaša **15–240 min** (mediana **35 min**, povprečje **56,5 min**; brez enega izstopajočega primera **~36 min**), pri čemer imajo recepture **113–313 korakov** (tipično **6–22 s/korak**). Ker validator odkrije napake **že v fazi pregleda**, se **večina testnih iteracij odpravlja** ali se skrči na krajše potrditveno preverjanje — **dodatni prihranek časa je zato ~30–60 min na recepturo** (ali več pri kompleksnejših primerih).

---

### Strateške koristi za oddelek

- **Standardizacija in doslednost:** vsa preverjanja potekajo po enakih pravilih, neodvisno od tega, kdo pregleduje recepturo.
- **Popolnost in sledljivost:** sistematično preverjanje pravil, ki jih ročno pogosto spregledamo (zaporedja ključev, skladnost s SOPji, parametri kontrol).
- **Zmanjšanje tveganja:** manj napak gre naprej v proces (testiranje, izdaja, proizvodnja); to zmanjšuje tveganje ponovnega dela, zamud in neskladnosti.
- **Merljivost in izboljšave:** statistika napak po kodih omogoča **ciljne izboljšave predlog, usposabljanj in procesov**. To je osnova za nenehno izboljševanje kakovosti.
- **Učinkovitost:** prihranek časa omogoča **višjo kapaciteto** za kompleksnejše naloge, revizije in podporo proizvodnji.

---

### Predlog za formalizacijo in nadaljnji razvoj

Moj predlog je, da validator **formalno vključimo v standardni potek pregleda receptur** (npr. kot obvezni korak pred oddajo ali izdajo). To zahteva:

1. **Uradno določitev odgovornosti:** kdo je odgovoren za uporabo orodja, vzdrževanje in nadaljnji razvoj.
2. **Vključitev v SOP:** validator postane del dokumentiranega procesa (s tem tudi osnova za skladnost).
3. **Usposabljanje:** potrebno je kratko usposabljanje za uporabnike in QA ekipo.
4. **Razširitev pristopa:** izkušnje z validatorjem lahko prenesemo na druge dokumente/procese (npr. validacija drugih tipov dokumentacije, standardizacija poročil).

**Osebna želja in priložnost:**  
To vidim kot **priložnost za večjo odgovornost** — rad bi prevzel vodilno vlogo pri formalizaciji validatorja, nadaljnjem razvoju orodja in prenosu pristopa na druge procese. Prepričan sem, da lahko ta pristop **trajno dvigne kakovost in učinkovitost** v oddelku, hkrati pa omogoči **merljiv prispevek k skladnosti in kontinuiranemu izboljševanju**.
