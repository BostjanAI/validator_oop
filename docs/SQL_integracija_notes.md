# SQL Integracija — Notes iz pogovora (13. 3. 2026)

## Kontekst

Validator OOP trenutno deluje kot standalone desktop orodje, ki bere `.xlsx` datoteke.
MES sistem podjetja uporablja **MySQL** bazo podatkov (PHP 7+ / Linux / Apache / phpMyAdmin).

Cilj: integracija validatorja z obstoječim MES MySQL sistemom.

---

## Trenutni tok podatkov (brez SQL)

```
.xlsx → ExcelLoader → WorkbookParser → list[dict] → RuleEngine → ValidationReport → .xlsx/.json
```

---

## Možnosti integracije

### Možnost A — SQL kot VIR podatkov (namesto Excel)

Nov `MySQLLoader` razred, ki vrne `list[dict]` — isti format kot `WorkbookParser`.
`RuleEngine` in vsa pravila ostanejo **brez sprememb**.

```
MySQL (recipe data) → MySQLLoader → list[dict] → RuleEngine → ValidationReport
```

### Možnost B — SQL kot CILJ (shranjevanje rezultatov)

`ValidationReport.to_dict()` že vrne serializirano strukturo — primerno za SQL INSERT.
PHP aplikacija nato prikaže rezultate iz MySQL tabele.

### Možnost C — Oboje (priporočeno za produkcijo)

```
MySQL (recipe data) → MySQLLoader → RuleEngine → ValidationReport → MySQL (results)
                                                                   → .xlsx (opcijsko)
```

---

## Kaj je potrebno

### 1. Python driver

```bash
pip install mysql-connector-python
```

### 2. Dostop do MySQL (od MES admina)

- Host (IP naslov strežnika)
- Port (privzeto `3306`)
- Ime baze
- Uporabnik (priporočeno: read-only user)
- Geslo

### 3. Razumeti strukturo MySQL tabel

Ključni korak: ugotoviti katere MySQL tabele in stolpci ustrezajo headerjem, ki jih validator pričakuje:
`št. Koraka`, `Navodilo`, `Tip podatka`, `Tip objekta`, `Labela`, `Koda`, itd.

To se preveri v **phpMyAdmin** ali z `DESCRIBE table_name;`.

---

## Primer MySQLLoader

```python
import mysql.connector

class MySQLLoader:
    def __init__(self, host, port, database, user, password):
        self.conn = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

    def load_recipe(self, recipe_id: int) -> dict[str, list[dict]]:
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM recipe_steps
            WHERE recipe_id = %s
            ORDER BY step_number
        """, (recipe_id,))
        rows = cursor.fetchall()

        # MAPPING: MySQL stolpci → validator header imena
        mapped_rows = []
        for row in rows:
            mapped_rows.append({
                "št. Koraka":  row["step_number"],
                "Navodilo":    row["instruction"],
                "Tip podatka": row["data_type"],
                "Tip objekta": row["object_type"],
                # ... ostali stolpci — treba dopolniti glede na dejansko shemo
            })

        return {"Sheet1": mapped_rows}
```

---

## Tabela za shranjevanje rezultatov v MySQL

```sql
CREATE TABLE validation_results (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id     INT NOT NULL,
    validated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid      TINYINT(1),
    error_count   INT,
    warning_count INT,
    sheet         VARCHAR(100),
    row_index     INT,
    rule_name     VARCHAR(100),
    code          VARCHAR(50),
    severity      VARCHAR(20),
    message       TEXT,
    INDEX (recipe_id),
    INDEX (validated_at)
);
```

---

## Minimalne spremembe v obstoječi kodi

| Datoteka | Sprememba |
|---|---|
| `db/sql_loader.py` | Nov razred `MySQLLoader` |
| `db/sql_report_writer.py` | Nov razred `MySQLReportWriter` |
| `core/config.py` | Dodaj `db_url: str \| None = None` |
| `core/validator_engine.py` | if/else za Excel vs SQL loader |
| `rules/` + `core/rule_engine.py` | **Nobenih sprememb** |

---

## Naslednji koraki

1. Pridobi dostop do MySQL od MES admina (host, port, baza, user, pass)
2. Poglej tabele v phpMyAdmin — najdi tabelo z recipe koraki
3. Primerjaj MySQL stolpce z `REQUIRED_COLUMNS` iz `core/constants.py`
4. Napiši mapping MySQL stolpcev → validator header imen
5. Implementiraj `MySQLLoader`

---

## Arhitekturna prednost

Validator je že SQL-friendly:
- `RuleEngine` in pravila **ne vedo nič o viru podatkov** — delajo samo z `list[dict]`
- `ValidationReport.to_dict()` je že primeren za SQL INSERT
- `ValidatorConfig` se enostavno razširi z DB connection parametri
- `SharedContext` deluje enako z MySQL podatki kot z Excel podatki
