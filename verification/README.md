# Razvojno preverjanje kritičnih pravil

Pilot preverja urejenost mej intervala, pare masa/volumen ter parametre zaklepanja. Cilj je odkriti spremembo vedenja ob refaktoriranju in neskladje med funkcijo in dokumentirano zahtevo. Za vsako odločitev je priložen ponovljiv zapis. Paket se zažene ločeno od aplikacije.

| Dokument | Vsebina |
|---|---|
| [Arhitektura in tveganja](ANALIZA.md) | Popis pravil, kritične funkcije, odvisnosti, izbira tehnik in prednostni vrstni red |
| [Specifikacije](SPEC.md) | Viri, predpogoji, invariante, izhod, robni primeri, neveljavni vhodi in odprta vprašanja |
| [Vmesnik Recipe Sync](SYNC.md) | Pogodba dovoljenih sprememb, formule, objava, dokaz modela in meje preizkusov XLSX |
| [Izvedbeni zapis](evidence/README.md) | Dejanski rezultati, protiprimer, preizkusi pred/po spremembi in odprta presoja |

## Namestitev in zagon

Uporabi Git in CPython 3.12. Za ukaze pytest naj bo mapa projekta poimenovana `validator_oop`, da obstoječi testi uvozijo pravilen paket. Ukaze zaženi iz korena polnega klona. Če je klon plitek in pripeti commit manjka, zgodovino pridobi z `git fetch --unshallow origin`.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r verification/requirements.txt
python -m verification --candidate HEAD --output verification/out/pilot.json
```

Ta namestitev zadošča za pilot in njegove teste. Za ponovitev izvedbenega zapisa, skupaj s spletnimi testi, v čistem okolju uporabi `python -m pip install -r verification/evidence/requirements-linux-py312.txt`. Izvedbeni zapis navaja verzijo Pythona, orodij in izbrano platformo.

```sh
export PYTHONPATH=..
export HYPOTHESIS_STORAGE_DIRECTORY=verification/out/hypothesis
python -m pytest -q -ra -m 'not mysql' tests
python -m pytest -q -ra verification/tests
python -m verification.interval_guard --candidate HEAD
python -m verification --candidate HEAD --case lock/08
```

V PowerShellu uporabi `.venv\Scripts\Activate.ps1`, `$env:PYTHONPATH = ".."` in `$env:HYPOTHESIS_STORAGE_DIRECTORY = "verification/out/hypothesis"`. Test, označen z `mysql`, zahteva živo bazo in je izločen iz tega protokola. Datoteka z rezultati mora imeti novo ime. Brez `--output` se JSON izpiše na standardni izhod. Koda procesa je 0 za PASS, 1 za FAIL, 2 za nedokončano preverjanje oziroma napako pri izvedbi. Reprodukcija z `--case` poda izid samo za navedeni primer.

## Postopek za spremembo kode

1. V ločeni veji shrani predlagano spremembo v commit, vključno s pomožnimi funkcijami. Kandidata izberi z `--candidate <SHA>`. Orodje bere **commitirane** datoteke. Če želiš ponoviti staro poročilo, uporabi tudi isto revizijo orodja in isto okolje.
2. Referenca je polni SHA v `cases.BASELINE`. Orodje vzame Pythonove datoteke iz obeh Git objektov in požene po en izoliran proces na revizijo. Oba procesa dobita iste sintetične vrstice. Referenčno pravilo pri tem uporablja tudi zgodovinske različice parserjev, konstant in izdelave konteksta. Za izvajanje se predpostavlja zaupanja vredna projektna koda.
3. Preveri dve ločeni obveznosti. `EQ-*` preveri ujemanje opazovanj. `SPEC-*` z Z3 poišče protiprimer neodvisni pogodbi na tabeli dejanskih izidov. Dodatna obveznost `CTRL_INTERVAL_RANGE` prevede podprti pogoj, izvlečen iz AST kandidata, in ga simbolično preveri nad končnimi števili binary64. Pri neprepoznani obliki zahteva ročni pregled.
4. Za vsak protiprimer poročilo vsebuje funkcijo, zahtevo, vhod, pričakovani in dejanski izid ter ukaz za ponovitev. Preveri izvor zahteve, preslikavo vrstice v kontekst in kako ugotovitev uporabniku prikaže celotni pogon. Sprememba vedenja je lahko namerna. Napačen orakelj, nejasna zahteva in odstopanje implementacije zahtevajo različne odločitve.
5. Po potrditvi neskladja s specifikacijo dodaj zapis `regression_case` iz poročila v `regressions.json`. Pytest za vsak zapis sam ustvari zahtevo preverjajoč regresijski test. V pilotu je prvi zapis že vključen. Test pade, dokler izvajanje ne doseže pričakovanega izida. Odločitev o spremembi validacijskega pravila ali specifikacije pripada lastniku procesa in QA.
6. Ponovno izvedi obstoječo zbirko, pilot in ustrezne integracijske teste. Zabeleži odstopanja, odobrene spremembe vedenja, verziji izhodišča in kandidata ter nepreverjene domene. Sprememba pripete reference je posebna pregledljiva odločitev.

## Branje poročila za QA

| Izid | Razlaga |
|---|---|
| PASS | Podana obveznost je uspela z navedeno metodo in domeno. Pri izčrpni tabeli velja izid za vse elemente te tabele. Dokaz modela je vezan na predpostavke in semantiko modela. |
| FAIL | Obstaja ponovljiva razlika ali kršitev pogodbe. Enakost z izhodiščem in neuspeh proti zahtevi se lahko pojavita istočasno. |
| INCONCLUSIVE | Obstajajo nedokončana analiza, časovna omejitev ali nepodprta oblika dokazne obveznosti. Pri že najdenem protiprimeru ostane rezultat FAIL in zabeleži se morebitna omejitev nadaljnjega iskanja. |
| NOT VERIFIED | Manjka preverljiv vhod ali izvedba. Primer je odsotna revizija ali bodoči sinhronizator receptur. |

JSON vsebuje polna SHA aplikacije in izhodišča, verzijo in gradnjo aplikacije, revizijo in odtise izvajalne kode orodja, čas UTC, platformo, verzije orodij, pogoje in rezultate po identifikatorju. Vrh `result` se nanaša na izbrani obseg. Pri polnem zagonu vključuje tudi model `SYNC-FRAME`. Ločeni informativni vnos `SYNC-XLSX` je zunaj izračuna tega izida. Izpis testov, njihove verzije in statusi so spremljevalni dokazi. Uspešni enotski ali generativni testi sami ne dokazujejo enakovrednosti.

Za nadzorovan zapis arhiviraj JSON, rezultate testov, uporabljeno okolje, kontrolirane verzije zahtev, reviziji izvorne kode in dokumentirano obravnavo vsake razlike. Zapiši izvajalca, neodvisnega pregledovalca, odločitev lastnika zahteve in odobritev po obstoječem SOP. Orodje ustvarja razvojne dokaze. Elektronski podpisi, kvalifikacija orodja, rok hrambe in odločitev o izdaji sodijo v obstoječi sistem kakovosti.
