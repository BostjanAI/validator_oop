-- Rezultati validacije Validator OOP (MES MySQL integracija).
-- Idempotentno: CREATE TABLE IF NOT EXISTS – varno za ponovni zagon.
-- Zagon: python -m validator_oop.db.migrate  (ali ročno prek phpMyAdmin)

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
