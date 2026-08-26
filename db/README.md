# db/ — MES/MySQL integracija

Opcijski sloj za validacijo receptur neposredno iz MES MySQL baze in
shranjevanje rezultatov nazaj v bazo. Excel/CLI/GUI/web upload tok deluje
brez tega sloja nespremenjeno (MySQL driver je lazy import).

Polna dokumentacija: `docs/SQL_integracija_notes.md`.

## Hitri začetek

```bash
pip install -r requirements-db.txt      # mysql-connector-python
copy .env.example .env                  # vpiši poverilnice (NIKOLI v git)
python -m validator_oop.db.migrate      # ustvari tabeli za rezultate
python -m validator_oop --list-recipes
python -m validator_oop --db-source --recipe-id 123 --db-save-results
```

## Struktura

| Datoteka | Vloga |
|---|---|
| `config.py` | `DBConfig` – povezava iz env / `.env` (`MES_DB_*`) |
| `connection.py` | `ConnectionFactory` – lazy import driverja, retry, context managerji |
| `mapping.py` | `ColumnMapping` – MES stolpci → validator glave (JSON override) |
| `sql_loader.py` | `MySQLLoader.load_recipe()` → `LoadedWorkbook` (isti format kot Excel) |
| `sql_report_writer.py` | `MySQLReportWriter.save()` → `validation_runs` + `validation_findings` |
| `schema.sql` | Idempotenten DDL za results tabele |
| `migrate.py` | Ustvari/preveri results tabele (`python -m validator_oop.db.migrate`) |
| `errors.py` | `DBConnectionError`, `RecipeNotFoundError`, `MappingError`, … |

## Mapping profil

Privzeti profil pričakuje tabelo `recipe_steps` s stolpci `recipe_id`,
`step_number`, `instruction`, `data_type`, `check_key`, `value`, `label`,
`object_type`, `control1`, `control1_par1`, … `control4_par2` ter meta tabelo
`recipes` (`id`, `name`, `version`, `created_at`).

**TODO(shema):** privzeti profil je vzorčen — realna imena tabel/stolpcev je
treba potrditi z MES adminom (phpMyAdmin / `DESCRIBE tabela;`) in razlike
zapisati v JSON mapping datoteko (env `MES_DB_MAPPING_FILE` ali CLI
`--db-mapping`), primer:

```json
{
    "columns": {
        "št. Koraka": "zap_st",
        "Navodilo": "opis"
    },
    "transforms": {
        "null_default": "",
        "trim": true,
        "casts": {"št. Koraka": "str"}
    },
    "source": {
        "steps_table": "ipo_koraki",
        "recipe_id_column": "receptura_id",
        "order_by_column": "zap_st",
        "sheet_column": null,
        "default_sheet_name": "Receptura",
        "recipes_table": "recepture",
        "recipes_id_column": "id",
        "recipes_name_column": "naziv",
        "recipes_version_column": "verzija",
        "recipes_date_column": "datum"
    }
}
```

Karkoli v JSON-u izpustiš, ostane na privzeti vrednosti. Če za katero od
`REQUIRED_COLUMNS` ni preslikave, dobiš jasno napako `MappingError` s
seznamom manjkajočih.

## Varnost

- Vse poizvedbe so parametrizirane; `recipe_id` se validira kot integer.
- Imena tabel/stolpcev iz mapping datoteke se preverijo (samo varni identifikatorji).
- Least privilege: `MES_DB_USER` naj bo read-only, `MES_DB_RESULTS_USER`
  ločen write user samo za `validation_runs`/`validation_findings`.
- Poverilnice samo v env / `.env` (v `.gitignore`); gesla se ne logirajo.
- Opcijski TLS prek `MES_DB_SSL_CA`.

## Testi

```bash
pytest tests/test_db_integration.py tests/test_web_db.py   # brez žive baze (mocki)
docker compose -f tests/docker-compose.mysql.yml up -d      # opcijska testna baza
pytest -m mysql                                             # integracijski round-trip
```
