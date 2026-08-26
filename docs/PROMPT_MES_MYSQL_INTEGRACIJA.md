# Naloga: Polna MES / MySQL integracija za Validator OOP

**Datum:** julij 2026
**Jezik:** slovenščina za uporabniška sporočila, angleščina za docstringe (kot obstoječa koda)
**Obseg:** večurno / večdnevno delo — implementiraj celoten SQL sloj (vir + cilj), CLI, web integracijo, teste in dokumentacijo. Ne ustavi se pri skeletonu.

---

## 0. Kontekst (OBVEZNO PREBERI PRED KODO)

Projekt **validator_oop** je OOP validacijski engine za farmacevtske MES/IPO recepture. Trenutno bere `.xlsx/.xlsm`. Podjetje ima MES v **MySQL** (PHP 7+ / Linux / Apache / phpMyAdmin).

**Ključna arhitekturna ugotovitev — engine je že SQL-friendly:**
- `RuleEngine.run(values, ...)` in vsa pravila delajo samo z `list[dict]` (`{header: value}`) — **ne vedo nič o viru podatkov**.
- `ValidationReport.to_dict()` že vrne serializirano strukturo, primerno za SQL INSERT.
- `ValidatorConfig` je dataclass, ki ga je enostavno razširiti.
- `SharedContext` deluje enako za SQL kot za Excel podatke.

**Obstoječi tok:**
```
.xlsx → ExcelLoader → WorkbookParser → LoadedWorkbook(values: dict[sheet, list[dict]]) → ValidatorEngine → RuleEngine → ValidationReport → .xlsx/.json
```

**Ključne datoteke, ki jih moraš prebrati pred začetkom:**
- `docs/SQL_integracija_notes.md` — obstoječi načrt (Možnost A/B/C, primer `MySQLLoader`, DDL, mapping)
- `core/validator_engine.py` — `ValidatorEngine.validate()` in `validate_loaded()`
- `excel/excel_loader.py` — `ExcelLoader` in dataclass `LoadedWorkbook` (cilj: SQL loader mora vrniti enakovreden objekt)
- `excel/workbook_parser.py` — kako nastane `list[dict]`
- `core/config.py` — `ValidatorConfig` (from_dict/to_dict)
- `core/report.py` — `ValidationReport.to_dict()`
- `core/error.py` — `ValidationError.to_dict()` (polja: rule, code, severity, message, sheet, workbook, row, col, payload)
- `core/constants.py` — `REQUIRED_COLUMNS` (ciljne glave za mapping)
- `main.py` — CLI vzorec sestavljanja engina
- `web/backend/service.py`, `web/backend/app.py` — web integracijska točka

### Stroga pravila
1. **NE piši validacijske logike na novo** in **NE spreminjaj** `rules/`, `core/rule_engine.py`, `core/shared_context.py`.
2. Spremembe v `core/validator_engine.py` in `core/config.py` so dovoljene **samo** minimalno in **povratno združljivo** (obstoječi Excel tok, CLI in GUI morajo delovati nespremenjeno).
3. Novi SQL sloj gre v **nov paket** `db/` (glej §2). Excel sloj ostane nedotaknjen.
4. MySQL driver je **opcijska odvisnost** — uvoz naj bo lazy; brez nameščenega driverja mora ostalo delovati (kot openpyxl vzorec v `excel_loader.py`).
5. Nobenih skrivnosti/gesel v kodi ali gitu. Poverilnice samo prek env / config datoteke izven verzioniranja.
6. Vsaka sprememba kode → posodobi `CHANGELOG.md` pod `[Unreleased]` (slovensko, datum delovni dan, ocena časa; samo DODAJ vnose).
7. Ohrani obstoječe teste zelene; dodaj nove.

---

## 1. Cilj

Omogočiti validacijo receptur **neposredno iz MySQL** in shranjevanje rezultatov **nazaj v MySQL**, ob polni ohranitvi obstoječega Excel toka.

Implementiraj **Možnost C** iz zapiskov (oboje):
```
MySQL (recipe data) → MySQLLoader → LoadedWorkbook → RuleEngine → ValidationReport → MySQL (results)
                                                                                    → .xlsx/.json (opcijsko)
```

Podpri tri načine uporabe:
- **CLI**: `python -m validator_oop --db-source --recipe-id 12345`
- **Programsko**: `MySQLLoader(...).load_recipe(id)` → engine
- **Web**: nov endpoint za validacijo po `recipe_id` iz baze (glej §7)

---

## 2. Arhitektura in struktura

Nov paket, ločen od Excel sloja:

```
db/
  __init__.py
  connection.py        # ConnectionFactory / pool, context manager, lazy import driverja
  config.py            # DBConfig dataclass + branje iz env
  mapping.py           # MES stolpci → validator glave (REQUIRED_COLUMNS); config-driven
  sql_loader.py        # MySQLLoader → vrne LoadedWorkbook (isti format kot ExcelLoader)
  sql_report_writer.py # MySQLReportWriter → zapiše ValidationReport v MySQL
  schema.sql           # DDL za results tabele (idempotenten CREATE TABLE IF NOT EXISTS)
  migrate.py           # ustvari/preveri results tabele
  errors.py            # DBConnectionError, RecipeNotFoundError, MappingError
```

### 2.1 Ključna zasnova: `MySQLLoader` vrne `LoadedWorkbook`

Da engine ostane nedotaknjen, `MySQLLoader.load_recipe()` **NE** vrača samo dicta — sestavi in vrne `LoadedWorkbook` (iz `excel/excel_loader.py`) z:
- `values: {sheet_name: list[dict]}` (npr. `{"Receptura": [...]}` ali več listov, če MES loči variante)
- `headers: {sheet_name: list[str]}` (glave = ciljne validator glave)
- `source_path = None` ali psevdo-pot npr. `Path(f"mysql://recipe/{recipe_id}")` za poimenovanje v poročilih
- `row_offset` = smiselna baza za prikaz vrstic (dokumentiraj; npr. 2 ali dejanski `step_number`)
- `sheet_names` urejeno

Nato validacija teče prek obstoječega engina:
```python
loaded = MySQLLoader(db_cfg, mapping).load_recipe(recipe_id)
report = validator.validate_loaded(loaded)
```

**Dovoljena minimalna sprememba:** `ValidatorEngine.validate_loaded()` trenutno RuleEngine-u ne poda `all_workbook_data` / `all_workbook_headers` (ki ju `validate()` poda za SOP compliance pravilo). Če želiš SOP podporo tudi za SQL vir, dodaj ta dva parametra v `validate_loaded()` **povratno združljivo** (privzeto iz `loaded.values` / `loaded.headers`), z dodanim testom. Če SOP za SQL ni v obsegu, to eksplicitno dokumentiraj in pusti `validate_loaded()` pri miru.

### 2.2 Mapping sloj (config-driven, NE hardcoded)

MES shema ni znana vnaprej. Mapping mora biti **konfigurabilen**, ne zašit v kodo:
- `db/mapping.py` definira privzet mapping MES stolpec → validator glava (iz `REQUIRED_COLUMNS`).
- Mapping se lahko prepiše prek JSON datoteke (`MES_DB_MAPPING_FILE`) — brez spreminjanja kode ob spremembi sheme.
- Validiraj mapping ob zagonu: če manjka preslikava za katero od `REQUIRED_COLUMNS`, javi jasno `MappingError` s seznamom manjkajočih.
- Podpri transformacije vrednosti (npr. NULL→"", trim, cast števila v string kot pričakuje validator).

Ciljne glave (iz `core/constants.py` `REQUIRED_COLUMNS`):
`št. Koraka, Navodilo, Tip podatka, Ključ preverjanja, Vrednost, Labela, Tip objekta, Kontrola 1..4 (+ par 1/par 2)`.

---

## 3. Povezava in konfiguracija

### 3.1 `DBConfig` (env-driven)

| Env | Privzeto | Opis |
|---|---|---|
| `MES_DB_HOST` | — | host MySQL |
| `MES_DB_PORT` | `3306` | port |
| `MES_DB_NAME` | — | ime baze |
| `MES_DB_USER` | — | uporabnik (priporočeno **read-only** za vir) |
| `MES_DB_PASSWORD` | — | geslo (nikoli v git) |
| `MES_DB_RESULTS_USER` | = `MES_DB_USER` | ločen uporabnik z write pravico za results (opcijsko) |
| `MES_DB_RESULTS_PASSWORD` | — | geslo za results usera |
| `MES_DB_MAPPING_FILE` | — | pot do JSON mappinga (opcijsko) |
| `MES_DB_CHARSET` | `utf8mb4` | charset |
| `MES_DB_CONNECT_TIMEOUT` | `10` | timeout (s) |
| `MES_DB_SSL_CA` | — | pot do CA za TLS (opcijsko) |

- Podpri tudi `.env` datoteko (izven gita; dodaj `.env` v `.gitignore`, priloži `.env.example`).
- **Ločena principa najmanjših pravic:** branje receptur = read-only user; pisanje rezultatov = ločen write user (če je nastavljen).

### 3.2 `connection.py`
- Lazy import `mysql.connector` (ali `pymysql` — izberi eno, dokumentiraj; `mysql-connector-python` je v zapiskih).
- Context manager za povezavo/kurzor, ki zagotovi zapiranje.
- Enostaven retry (npr. 2 poskusa) na prehodne napake.
- Jasna `DBConnectionError` z nasvetom (host/port/geslo/firewall), brez izpisa gesla.
- Parametrizirane poizvedbe **povsod** (brez f-string SQL — zaščita pred SQL injection).

---

## 4. Branje receptur — `MySQLLoader`

Zahteve:
- `load_recipe(recipe_id) -> LoadedWorkbook`
- `list_recipes(limit, offset, filter) -> list[RecipeMeta]` (id, ime, verzija, datum) — za web/CLI izbiro
- `recipe_exists(recipe_id) -> bool`
- Uredi korake po `step_number` (ORDER BY).
- Uporabi mapping sloj; NULL → primerne privzete vrednosti.
- Če recept ne obstaja → `RecipeNotFoundError`.
- Poizvedba naj bo v mappingu/configu nastavljiva (ime tabele, stolpec recipe_id, order-by), ker MES shema ni znana. Privzeto uporabi vzorec iz zapiskov, a naj bo override možen.
- Podpri več listov, če MES loči variante recepture (npr. `Receptura` / `Receptura_2`); sicer en list.

> Pred implementacijo poizvedb: če dejanska MES shema ni na voljo, implementiraj proti **konfigurabilni shemi** in dodaj privzeti profil, ki ustreza primeru v `docs/SQL_integracija_notes.md`. Jasno označi mesta, kjer je treba potrditi realno shemo (`# TODO(shema): potrditi z MES adminom`).

---

## 5. Shranjevanje rezultatov — `MySQLReportWriter`

### 5.1 DDL (`db/schema.sql`)
Dve tabeli (glava + postavke), idempotentno:

```sql
CREATE TABLE IF NOT EXISTS validation_runs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id     INT NOT NULL,
    recipe_name   VARCHAR(255),
    validated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid      TINYINT(1) NOT NULL,
    error_count   INT NOT NULL DEFAULT 0,
    warning_count INT NOT NULL DEFAULT 0,
    info_count    INT NOT NULL DEFAULT 0,
    validator_version VARCHAR(50),
    config_json   JSON NULL,
    INDEX (recipe_id),
    INDEX (validated_at)
);

CREATE TABLE IF NOT EXISTS validation_findings (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    run_id     INT NOT NULL,
    sheet      VARCHAR(255),
    row_index  INT NULL,
    col        VARCHAR(255) NULL,
    rule_name  VARCHAR(255),
    code       VARCHAR(100),
    severity   VARCHAR(20),
    message    TEXT,
    payload_json JSON NULL,
    INDEX (run_id),
    INDEX (code),
    CONSTRAINT fk_run FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
);
```
(Prilagodi tipom, a ohrani to obliko. Naj bo `migrate.py` sposoben ustvariti tabele.)

### 5.2 `MySQLReportWriter`
- `save(report: ValidationReport, *, recipe_id, recipe_name=None, config=None) -> int` (vrne `run_id`)
- Uporabi `report.to_dict()` in `error.to_dict()` — brez podvajanja logike.
- **Transakcija**: run + findings v enem commitu; rollback ob napaki.
- **Idempotenca**: možnost `replace_existing` (izbriši prejšnje findinge za isti run) ali vedno nov run z novim timestampom (privzeto: nov run). Dokumentiraj.
- Verzija validatorja iz `core/_version.py`.

---

## 6. CLI integracija (`main.py`)

Dodaj argumente (povratno združljivo — obstoječi `workbook` pozicijski ostane):
```
--db-source                validiraj iz MySQL namesto Excel
--recipe-id INT            id recepture v MES
--db-save-results          shrani ValidationReport v MySQL
--list-recipes             izpiši recepture iz baze (id, ime, datum)
--db-mapping PATH          pot do mapping JSON (override env)
```
Vedenje:
- `--db-source --recipe-id 123` → `MySQLLoader` → `validate_loaded` → poročilo na stdout/JSON (kot Excel tok).
- `+ --db-save-results` → še zapis v MySQL, izpiši `run_id`.
- Brez `--db-source` = obstoječi Excel tok, popolnoma nespremenjen.
- Manjkajoč driver / config → jasna slovenska napaka, exit code ≠ 0.

Za PyInstaller: poskrbi, da so `db.*` moduli uvoženi kjer je potrebno (kot obstoječi vzorec za catalog_code_rule v `main.py`).

---

## 7. Web integracija (nadgradnja `web/`)

Brez rušenja obstoječega upload toka. Dodaj:
- `GET  /api/db/health` — preveri povezavo na MES bazo (brez gesla v odgovoru)
- `GET  /api/db/recipes?limit=&offset=&q=` — seznam receptur iz baze
- `POST /api/db/validate` — body `{recipe_id, config, save_results: bool}` → zažene obstoječi background job (kot upload), samo vir je SQL; vrne `job_id`
- Rezultati/prenosi tečejo skozi **obstoječo** job/report infrastrukturo (`jobs.py`, `service.py`) — SQL vir samo zamenja loader korak.
- Env `MES_WEB_ENABLE_DB` (privzeto `0`) — funkcija skrita, dokler ni konfigurirana baza.
- Če je pozneje prisoten auth (Web Faza 2), `save_results` in DB validacijo zaščiti z vlogo.

---

## 8. Testi (obvezno, brez žive baze v CI)

Ne zahtevaj prave MySQL za `pytest`. Tri plasti:

1. **Unit — mapping**: MES vrstica → validator glave; manjkajoč mapping → `MappingError`; transformacije (NULL, trim, cast).
2. **Unit — loader z mockom**: mockan kurzor vrne fiktivne vrstice → `MySQLLoader` vrne pravilen `LoadedWorkbook`; nato `RuleEngine`/`ValidatorEngine` vrne pričakovane napake. Uporabi obstoječe vzorce iz `tests/`.
3. **Unit — report writer z mockom**: preveri, da se sestavijo pravilni parametrizirani INSERT-i iz `report.to_dict()` (brez prave baze).
4. **Ekvivalenčni test**: ista receptura kot Excel IN kot SQL (iste vrstice) → **identičen** seznam napak (dokaz, da SQL vir ne spremeni rezultatov).
5. **Opcijski integracijski test** (marker `@pytest.mark.mysql`, privzeto skip): če je nastavljen `MES_DB_HOST`/testna baza (npr. Docker MySQL), poženi pravi round-trip. Dodaj `docker-compose` primer za testno MySQL v `db/` ali `tests/`.
6. **Regression**: obstoječi Excel/CLI/web testi ostanejo zeleni.

Za mock uporabi `unittest.mock` (brez nove težke odvisnosti).

---

## 9. Varnost

- Parametrizirane poizvedbe povsod (SQL injection).
- Read-only user za branje; ločen write user za results (least privilege).
- Poverilnice samo iz env/`.env` (v `.gitignore`); `.env.example` brez pravih vrednosti.
- Ne logiraj gesel ali connection stringa z geslom.
- Opcijski TLS (`MES_DB_SSL_CA`).
- Validiraj/omeji `recipe_id` (integer) pred poizvedbo.

---

## 10. Odvisnosti in deployment

- Dodaj `mysql-connector-python` (ali `pymysql`) v **ločen** `requirements-db.txt` (ne v osnovni `requirements.txt`), da desktop namestitev ostane lahka.
- Lazy import: brez driverja Excel/CLI/GUI delujejo naprej.
- Dokumentiraj Docker/on-prem: aplikacija in MES baza sta v internem omrežju (brez javnega dostopa).

---

## 11. Dokumentacija (obvezno)

- Posodobi `docs/SQL_integracija_notes.md` → iz "notes" v dejansko dokumentacijo (kako nastaviti env, mapping, zagon CLI/web, DDL, testiranje).
- Dodaj razdelek v `README.md` (CLI primeri za `--db-source`).
- `CHANGELOG.md` — vnosi po kategorijah (Added: db sloj, CLI, web endpointi; Changed: validate_loaded, config).
- `.env.example` + kratek `db/README.md` (mapping profil, kako potrditi MES shemo).

---

## 12. Koraki implementacije (točno v tem vrstnem redu)

1. **Pregled** obstoječih datotek iz §0; naredi kratek plan v odgovoru.
2. `db/config.py` + `db/errors.py` + `db/connection.py` (z lazy importom in mockabilnim vmesnikom).
3. `db/mapping.py` (+ privzeti profil + JSON override + validacija proti `REQUIRED_COLUMNS`).
4. `db/sql_loader.py` → `MySQLLoader.load_recipe()` vrne `LoadedWorkbook`; `list_recipes`, `recipe_exists`.
5. Ekvivalenčni test (Excel vs SQL) — dokaži nevtralnost vira.
6. `db/schema.sql` + `db/migrate.py` + `db/sql_report_writer.py`.
7. Minimalna, povratno združljiva razširitev `core/config.py` (DB parametri prek `extra` ali novih polj) in po potrebi `validate_loaded()`.
8. CLI (`main.py`) argumenti + izpisi.
9. Web endpointi (`web/backend/`), skriti za `MES_WEB_ENABLE_DB`.
10. Vsi testi (unit + mock + ekvivalenca + opcijski docker mysql).
11. Dokumentacija + `CHANGELOG.md`.

Po vsakem večjem sklopu naj bodo testi zeleni. Ne skači na web pred delujočim CLI + loader.

---

## 13. Merila sprejemljivosti (Definition of Done)

- [ ] `MySQLLoader.load_recipe(id)` vrne `LoadedWorkbook`, ki ga engine validira brez sprememb pravil.
- [ ] Ekvivalenčni test: ista receptura (Excel vs SQL) → identične napake.
- [ ] `MySQLReportWriter.save()` zapiše run + findings v transakciji; vrne `run_id`.
- [ ] CLI: `--db-source --recipe-id --db-save-results --list-recipes` delujejo; brez `--db-source` je Excel tok nespremenjen.
- [ ] Web: `/api/db/recipes`, `/api/db/validate` delujeta prek obstoječe job infrastrukture (za `MES_WEB_ENABLE_DB=1`).
- [ ] Mapping je config-driven; manjkajoč mapping da jasno napako.
- [ ] Brez nameščenega MySQL driverja: Excel/CLI/GUI/web upload delujejo naprej.
- [ ] `pytest` zelen brez žive baze; integracijski test skipnjen brez `MES_DB_HOST`.
- [ ] Nobenih poverilnic v gitu; `.env.example` prisoten.
- [ ] `CHANGELOG.md`, `docs/SQL_integracija_notes.md`, `README.md` posodobljeni.

---

## 14. Česa NE delaj

- Ne spreminjaj pravil (`rules/`), `rule_engine.py`, `shared_context.py`.
- Ne dodajaj ORM v `core/` — DB logika samo v `db/` (in tanka nitka v web plasti).
- Ne zašij MES sheme/mappinga v kodo — vse konfigurabilno.
- Ne rušij Excel/CLI/GUI/web upload tokov.
- Ne uvajaj MySQL driverja kot obvezne osnovne odvisnosti.
- Ne commitaj `.env`, gesel, dumpov baze.

---

## 15. Začetek

1. Preberi datoteke iz §0 (zlasti `SQL_integracija_notes.md`, `excel_loader.py` `LoadedWorkbook`, `validator_engine.py`).
2. Napiši kratek plan (koraki 1–11) v odgovoru.
3. Implementiraj po vrstnem redu iz §12.
4. Na koncu: povzetek, kako nastaviti env + mapping, kako pognati CLI in teste, seznam novih endpointov in kaj je treba potrditi z MES adminom (realna shema tabel).

Začni zdaj.
