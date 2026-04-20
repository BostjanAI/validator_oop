# Plan izboljšav projekta Validator OOP

## Cilj

Dvigniti zanesljivost validacije, zmanjšati tveganje regresij in poenostaviti vzdrževanje projekta, predvsem v jedru pravil (`control`, `field`, `relational`) in spremljajoči infrastrukturi testov/dokumentacije.

## 1) Stabilizacija repozitorija in delovnega toka (visoka prioriteta)

- Urediti, kaj sodi v git in kaj ne:
  - izločiti `__pycache__/`, lokalne izhode in začasne analitične datoteke iz verzioniranja;
  - potrditi strategijo za `samples/` (katere datoteke ostanejo kot referenčni testni set, katere se odstranijo/arhivirajo).
- Uskladiti strukturo dokumentacije in odstraniti podvojene/eksperimentalne izpise.
- Uvesti enoten “clean workspace” check pred merge (brez generated artefaktov).

Ključne poti:

- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/conftest.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/conftest.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/README.md](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/README.md)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/samples/](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/samples/)

## 2) Testna strategija in pokritost pravil (visoka prioriteta)

- Definirati testno matriko po skupinah pravil:
  - `structural`, `field`, `relational`, `control`, `sop`.
- Pri `control` pravilih uvesti parametrizirane teste za kritične edge-case scenarije (kombinacije `Kontrola-*`, `Par 1/Par 2`, neveljavni tipi, prazne vrednosti).
- Dodati “regression fixtures” za že opažene produkcijske napake in zagotoviti, da ostanejo trajno pokrite.
- Uvesti baseline metrike:
  - minimalna pokritost za kritične module,
  - ločeni hitri testi za PR in širši nightly set.

Ključne poti:

- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/control.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/control.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/test_control_rules.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/test_control_rules.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/conftest.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/tests/conftest.py)

## 3) Refaktor pravil in jasne meje odgovornosti (srednja prioriteta)

- V `rules/builtin/control.py` razbiti monolitna pravila na manjše, testabilne helperje (parse, normalize, validate, error-build).
- Konsolidirati ponavljajočo logiko med `field.py`, `relational.py`, `control.py` v skupne util funkcije (brez podvajanja parserjev in normalizacij).
- Standardizirati obliko napak (`code`, `message`, `column`, `context`) za lažje poročanje in avtomatsko analitiko.

Ključne poti:

- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/control.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/control.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/field.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/field.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/relational.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/rules/builtin/relational.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/utils/helpers.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/utils/helpers.py)

## 4) SharedContext in performance optimizacije (srednja prioriteta)

- Profilirati gradnjo `SharedContext` pri večjih workbookih (veliko vrstic/listov).
- Uvesti cache/predizračune tam, kjer je ponovno računanje pogosto med pravili.
- Dodati benchmark teste za ključne poti validacije, da se ujame degradacija hitrosti.

Ključne poti:

- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/core/shared_context.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/core/shared_context.py)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/core/rule_engine.py](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/core/rule_engine.py)

## 5) Dokumentacija in developer experience (srednja prioriteta)

- Urediti “single source of truth” dokumentov:
  - jasna meja med uporabniškimi navodili in tehnično dokumentacijo.
- Dodati kratka navodila “How to add a rule safely” z obveznim checklistom (test, changelog, sample, expected report).
- Dodati troubleshooting sekcijo za najpogostejše napake validacije in razlago bypass nastavitev.

Ključne poti:

- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/README.md](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/README.md)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/docs/](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/docs/)
- [C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/CHANGELOG.md](C:/Users/boskom/Desktop/Boskom/Cursor projekt/Validator OOP/validator_oop/CHANGELOG.md)

## Predlagan vrstni red izvedbe (4 sprinti)

- Sprint 1: higiena repozitorija + testna matrika + kritični regression testi.
- Sprint 2: refaktor `control` pravil + standardizacija error modela.
- Sprint 3: SharedContext optimizacije + benchmarki.
- Sprint 4: konsolidacija dokumentacije + onboarding/checklisti.

## Merila uspeha

- Manj regresij pri spremembah pravil (merjeno preko regression testov).
- Višja in stabilna pokritost kritičnih modulov pravil.
- Krajši čas analize napake (bolj konsistentna error sporočila in docs).
- Čistejši repo brez generated datotek in manj “šuma” v commitih.
