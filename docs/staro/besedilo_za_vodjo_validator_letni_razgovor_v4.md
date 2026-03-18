## Besedilo za vodjo oddelka (za letni razgovor)

**Kaj je "Validator"?**  
Validator je **programsko orodje (Python aplikacija)**, ki sem ga razvil za **avtomatizirano preverjanje kakovosti receptur** v formatu Excel. Deluje tako, da **prebere recepturo, sistematično preveri vse vnaprej definirane zahteve** (strukturne, vsebinske, skladnost s SOPji) in **izdela poročilo z vsemi odkritimi napakami** — vsaka napaka ima točno lokacijo (list, vrstica, stolpec) in opis. Namen orodja je nadomestiti ročni, dolgotrajni in nepopolni pregled receptur ter zmanjšati tveganje napak v nadaljnjem procesu (izdaja, testiranje, proizvodnja).

---

Rad bi izpostavil konkreten rezultat in predlog izboljšave procesa: **avtomatiziran pregled receptur z validatorjem** nam bistveno skrajša čas kontrole in hkrati dvigne kakovost.

Na realnem primeru (poročilo `porocilo_SD.xlsx`) je validator našel **99 napak** v recepturi in jih razvrstil v **15 kategorij** (npr. manjkajoči ali podvojeni ključi, nedoločen tip objekta, neujemanje parametrov kontrol z navodilom – intervali, ±, čas). Poročilo je pripravljeno tako, da ima vsaka napaka **točno lokacijo (list/vrstica/stolpec)** ter opis, dodatno pa še **povzetek po vrstah napak**.

**Prihranek časa:** ročni pregled takšnega obsega je realno **1,5–5 ur** (odvisno od izkušenj in kompleksnosti), ker zahteva sprotno iskanje po Excelu in preverjanje pravil v več kontekstih. Z validatorjem dobimo rezultat v nekaj sekundah, nato pa porabimo čas predvsem za **ciljno popravljanje**, tipično **10–30 minut** na recepturo. To pomeni **približno 1–4 ure prihranka na recepturo**.

**Dodatni merljiv prihranek pri testiranju (MES):** v tabeli `Testiranje_IPO.xlsx` je za 10 receptur zabeležen **čas testiranja/obdelave 15–240 min** (mediana **35 min**, povprečje **56,5 min**; brez enega izstopajočega primera **~36 min**), pri čemer imajo recepture **113–313 korakov** (tipično **~6–22 s/korak**). Ker validator odkrije napake že pred vnosom in izdajo, je **testiranje recepture v testnem okolju našega MES sistema v veliki meri nepotrebno** oziroma se skrči na minimalno potrditveno preverjanje — **prihranek časa je zato še bistveno večji**.

**Ključne koristi za oddelek:**
- **Doslednost**: ista pravila za vse recepture, neodvisno od tega, kdo pregleduje.
- **Popolnost**: sistematično preverjanje pravil, ki jih ročno pogosto spregledamo (npr. zaporedja ključev, skladnost parametrov kontrol z navodilom).
- **Hitrejše popravljanje**: jasna lokacija in tip napake skrajšata čas odprave.
- **Manj potrebe po testiranju v testnem MES okolju**: ker je receptura pregledana z validatorjem in so napake odpravljene še pred vnosom, se izognemo večini testnih iteracij (v praksi je to pogosto **desetine minut do več ur** na recepturo).
- **Manj ponovnega dela in tveganj**: manj napak gre naprej v proces (revizije, izdaja, uporaba).
- **Možnost standardizacije in merjenja**: statistika napak (po kodah) omogoča ciljne izboljšave predlog in usposabljanj.

Moj predlog je, da validator **formalno vključimo v standardni potek** pregleda receptur (npr. kot obvezni korak pred oddajo ali izdajo). S tem dobimo merljiv prihranek časa, boljšo sledljivost in višjo kakovost dokumentacije, kar je pomembno tako operativno kot z vidika skladnosti.
