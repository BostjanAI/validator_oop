# MES/MySQL integracija — dokumentacija

> Prvotni zapiski (13. 3. 2026) so nadgrajeni v dokumentacijo implementiranega
> sloja `db/` (julij 2026). Implementirana je **Možnost C**: MySQL kot vir
> receptur IN kot cilj za rezultate validacije.

## Arhitektura

```
MySQL (recipe data) → MySQLLoader → LoadedWorkbook → ValidatorEngine/RuleEngine
                                                            │
                                                            ▼
                                                     ValidationReport
                                                       │         │
                                              MySQL (results)  .xlsx/.json (opcijsko)
```

Ključno: `MySQLLoader.load_recipe()` vrne **isti objekt kot `ExcelLoader`**
(`LoadedWorkbook`), zato pravila (`rules/`), `RuleEngine` in `SharedContext`
ostajajo popolnoma nespremenjeni. Validacija teče prek obstoječega
`ValidatorEngine.validate_loaded()`.

- `row_offset = 2`: prvi korak recepture se v poročilih izpiše kot "vrstica 2",
  enako kot pri Excel viru z glavo v vrstici 1 (konsistentne lokacije napak).
- SOP compliance deluje tudi za SQL vir: `validate_loaded()` zdaj podaja
  `all_workbook_data`/`all_workbook_headers` (privzeto iz `LoadedWorkbook`,
  povratno združljivo).

## Namestitev

MySQL driver je **opcijska** odvisnost (lazy import) — brez njega Excel/CLI/
GUI/web upload delujejo naprej.

```bash
pip install -r requirements-db.txt   # mysql-connector-python
```

## Konfiguracija (env / .env)

Poverilnice samo prek okoljskih spremenljivk ali `.env` datoteke
(`.env` je v `.gitignore`; predloga je `.env.example`).

| Env | Privzeto | Opis |
|---|---|---|
| `MES_DB_HOST` | — | host MySQL strežnika (obvezno) |
| `MES_DB_PORT` | `3306` | port |
| `MES_DB_NAME` | — | ime baze (obvezno) |
| `MES_DB_USER` | — | uporabnik za branje (priporočeno **read-only**) |
| `MES_DB_PASSWORD` | — | geslo (nikoli v git, se ne logira) |
| `MES_DB_RESULTS_USER` | = `MES_DB_USER` | ločen write user za rezultate (opcijsko) |
| `MES_DB_RESULTS_PASSWORD` | — | geslo za results userja |
| `MES_DB_MAPPING_FILE` | — | pot do JSON mapping datoteke (opcijsko) |
| `MES_DB_CHARSET` | `utf8mb4` | charset |
| `MES_DB_CONNECT_TIMEOUT` | `10` | timeout povezave (s) |
| `MES_DB_SSL_CA` | — | CA certifikat za TLS (opcijsko) |
| `MES_WEB_ENABLE_DB` | `0` | `1` = vklopi web endpointe `/api/db/*` |

## Mapping MES stolpcev → validator glave

Realna MES shema **ni zašita v kodo**. Privzeti profil (tabela `recipe_steps`,
stolpci `step_number`, `instruction`, …) se lahko v celoti prepiše prek JSON
datoteke — glej `db/README.md` za format in primer. Manjkajoča preslikava za
katero od `REQUIRED_COLUMNS` javi `MappingError` s seznamom manjkajočih.

Transformacije vrednosti: `NULL → ""` (nastavljivo), trim nizov (privzeto
vklopljen), opcijski cast na `str`/`int`/`float` po stolpcu.

**TODO(shema):** privzeti profil potrdi z MES adminom (phpMyAdmin,
`DESCRIBE tabela;`) in razlike zapiši v mapping JSON.

## Rezultati v MySQL

DDL: `db/schema.sql` (idempotenten). Ustvarjanje/preverba:

```bash
python -m validator_oop.db.migrate
```

Tabeli:

- `validation_runs` — glava zagona (recipe_id, is_valid, števci po resnosti,
  verzija validatorja, arhiviran config JSON, timestamp),
- `validation_findings` — posamezne napake (sheet, row_index, col, rule_name,
  code, severity, message, payload JSON), FK na run z `ON DELETE CASCADE`.

`MySQLReportWriter.save(report, recipe_id=…)` zapiše run + findinge v **eni
transakciji** (rollback ob napaki) in vrne `run_id`. Privzeto vsak `save()`
ustvari **nov run** (ohranja se celotna zgodovina validacij); z
`replace_existing=True` se prejšnji runi za isto recepturo prej izbrišejo.

## Uporaba

### CLI

```bash
python -m validator_oop --list-recipes                          # seznam receptur
python -m validator_oop --db-source --recipe-id 123             # validacija iz baze
python -m validator_oop --db-source --recipe-id 123 --db-save-results   # + zapis v MySQL
python -m validator_oop --db-source --recipe-id 123 --format json -o porocilo.json
python -m validator_oop --db-source --recipe-id 123 --db-mapping mapping.json
```

Brez `--db-source` je Excel tok popolnoma nespremenjen. Manjkajoč driver ali
konfiguracija vrneta jasno slovensko napako in exit code 2.

### Programsko

```python
from validator_oop.db import DBConfig, MySQLLoader, MySQLReportWriter, load_mapping

db_cfg = DBConfig.from_env()
loader = MySQLLoader(db_cfg, load_mapping(db_cfg.mapping_file))

loaded = loader.load_recipe(123)          # LoadedWorkbook
report = validator.validate_loaded(loaded)

run_id = MySQLReportWriter(db_cfg).save(report, recipe_id=123)
```

### Web (`MES_WEB_ENABLE_DB=1`)

| Endpoint | Opis |
|---|---|
| `GET /api/db/health` | stanje povezave na MES bazo (brez poverilnic v odgovoru) |
| `GET /api/db/recipes?limit=&offset=&q=` | seznam receptur iz baze |
| `POST /api/db/validate` | body `{recipe_id, config, save_results}` → `job_id` (202) |

Validacija teče skozi **obstoječo** job/report infrastrukturo (`jobs.py`,
`service.py`) — zamenjan je samo korak nalaganja. Rezultati in prenosi
poročil so na voljo prek obstoječih `/api/jobs/*` endpointov. Ob vklopljeni
avtentikaciji (Web Faza 2) `save_results` zahteva vlogo QA/admin.

Opombe za DB vir: SOP/šifranti in auto-fix niso podprti (ni izvorne Excel
datoteke).

## Varnost

- Parametrizirane poizvedbe povsod; `recipe_id` validiran kot integer.
- Imena tabel/stolpcev iz mapping datoteke se validirajo (samo `[A-Za-z0-9_]`).
- Least privilege: read-only user za branje, ločen write user za rezultate.
- Gesla se ne logirajo in niso v repr/odgovorih API-ja.
- Opcijski TLS (`MES_DB_SSL_CA`).
- Aplikacija in MES baza naj bosta v internem omrežju (brez javnega dostopa);
  pri Docker deploymentu MySQL port ne sme biti izpostavljen navzven.

## Testiranje

```bash
pytest tests/test_db_integration.py tests/test_web_db.py    # mocki, brez žive baze
```

Opcijski integracijski test z živo bazo (marker `mysql`, privzeto preskočen):

```bash
docker compose -f tests/docker-compose.mysql.yml up -d
$env:MES_DB_HOST="127.0.0.1"; $env:MES_DB_PORT="33061"
$env:MES_DB_NAME="mes_test"; $env:MES_DB_USER="mes_test"; $env:MES_DB_PASSWORD="mes_test_pw"
pytest -m mysql
```

Ekvivalenčni test (`TestExcelSqlEquivalence`) dokazuje, da ista receptura kot
Excel in kot SQL vir vrne **identičen** seznam napak.

## Kaj je treba potrditi z MES adminom

1. Dostop: host, port, ime baze, read-only user + geslo (in po želji ločen
   write user za rezultate).
2. Realno shemo tabel s koraki receptur (`DESCRIBE`), da se pripravi JSON
   mapping (imena tabel/stolpcev, order-by, meta tabela receptur).
3. Ali MES loči variante recepture (→ `source.sheet_column` v mappingu).
4. Dovoljenje za tabeli `validation_runs`/`validation_findings` (migrate).
