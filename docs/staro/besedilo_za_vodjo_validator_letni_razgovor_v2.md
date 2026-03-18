## Besedilo za vodjo oddelka (za letni razgovor)

Rad bi izpostavil konkreten rezultat in predlog izboljšave procesa: **avtomatiziran pregled receptur z validatorjem** nam bistveno skrajša čas kontrole in hkrati dvigne kakovost.

Na realnem primeru (poročilo `porocilo_SD.xlsx`) je validator našel **99 napak** v recepturi in jih razvrstil v **15 kategorij** (npr. manjkajoči ali podvojeni ključi, nedoločen tip objekta, neujemanje parametrov kontrol z navodilom – intervali, ±, čas). Poročilo je pripravljeno tako, da ima vsaka napaka **točno lokacijo (list/vrstica/stolpec)** ter opis, dodatno pa še **povzetek po vrstah napak**.

**Prihranek časa:** ročni pregled takšnega obsega je realno **1,5–5 ur** (odvisno od izkušenj in kompleksnosti), ker zahteva sprotno iskanje po Excelu in preverjanje pravil v več kontekstih. Z validatorjem dobimo rezultat v nekaj sekundah, nato pa porabimo čas predvsem za **ciljno popravljanje**, tipično **10–30 minut** na recepturo. To pomeni **približno 1–4 ure prihranka na recepturo**. Pri več recepturah se to hitro pozna v **desetinah ur na mesec**, hkrati pa zmanjšamo tveganje, da kakšna napaka uide.

**Ključne koristi za oddelek:**
- **Doslednost**: ista pravila za vse recepture, neodvisno od tega, kdo pregleduje.
- **Popolnost**: sistematično preverjanje pravil, ki jih ročno pogosto spregledamo (npr. zaporedja ključev, skladnost parametrov kontrol z navodilom).
- **Hitrejše popravljanje**: jasna lokacija in tip napake skrajšata čas odprave.
- **Manj potrebe po testiranju v testnem MES okolju**: ker je receptura pregledana z validatorjem in so napake odpravljene še pred vnosom, je testiranje recepture v testnem okolju našega MES sistema praktično nepotrebno, prihranek časa pa je ogromen.
- **Manj ponovnega dela in tveganj**: manj napak gre naprej v proces (revizije, izdaja, uporaba).
- **Možnost standardizacije in merjenja**: statistika napak (po kodah) omogoča ciljne izboljšave predlog in usposabljanj.

Moj predlog je, da validator **formalno vključimo v standardni potek** pregleda receptur (npr. kot obvezni korak pred oddajo ali izdajo). S tem dobimo merljiv prihranek časa, boljšo sledljivost in višjo kakovost dokumentacije, kar je pomembno tako operativno kot z vidika skladnosti.

