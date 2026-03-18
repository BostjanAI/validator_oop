# Ocena Vrednosti projekta Validator OOP – Opus 4.6

## 1. Obseg projekta (pregled)

| Kategorija | Število datotek | Število vrstic kode |
|---|---|---|
| Jedro (core) | 7 modulov | ~1.200 vrstic |
| Excel I/O | 4 moduli | ~1.450 vrstic |
| Ogrodje pravil (rules framework) | 2 modula | ~540 vrstic |
| Vgrajena pravila (builtin rules) | 5 modulov | ~4.230 vrstic |
| Grafični vmesnik (GUI) | 3 moduli | ~1.250 vrstic |
| Pomožne funkcije (utils) | 3 moduli | ~1.200 vrstic |
| CLI vmesnik | 1 modul | ~380 vrstic |
| **Produkcijska koda skupaj** | **~33 modulov** | **~10.250+ vrstic** |
| Testi | 11 modulov | ~2.780 vrstic |
| Dokumentacija | 20+ datotek (MD, DOCX) | N/A |
| **Celoten projekt** | **~65+ datotek** | **~13.000+ vrstic** |

---

## 2. Podrobna ocena ur po modulih

### A) Arhitektura in načrtovanje (pred kodiranjem)

| Aktivnost | Ocena ur |
|---|---|
| Analiza domene MES (razumevanje receptur, kontrol, korakov) | 10-14 |
| Načrtovanje OOP arhitekture (engine, pravila, registry) | 8-12 |
| Načrtovanje vzorcev (Strategy, Registry, DI) | 6-8 |
| **Skupaj** | **24-34 ur** |

### B) Jedro sistema (`core/`)

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `validator_engine.py` - orkestrator | 215 | Srednja | 4-6 |
| `rule_engine.py` - izvajanje pravil | 299 | Visoka | 8-12 |
| `shared_context.py` - predračunani podatki | 301 | Visoka | 10-14 |
| `constants.py` - regex vzorci, prevodi | 388 | Srednja | 8-12 |
| `config.py` - konfiguracija | 149 | Srednja | 3-4 |
| `report.py` - poročilo | 87 | Nizka | 2-3 |
| `error.py` - tipi napak | 63 | Nizka | 1-2 |
| **Skupaj** | **~1.200** | | **36-53 ur** |

### C) Excel I/O sloj (`excel/`)

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `sop_loader.py` - parser Word SOP dokumentov | 741 | Zelo visoka | 18-26 |
| `excel_loader.py` - nalaganje Excel datotek | 207 | Srednja | 4-6 |
| `report_writer.py` - generiranje poročil (Excel/JSON/TXT) | 283 | Srednja | 6-8 |
| `workbook_parser.py` - parsanje delovnih zvezkov | 219 | Srednja | 6-8 |
| **Skupaj** | **~1.450** | | **34-48 ur** |

### D) Ogrodje pravil (`rules/`)

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `base_rule.py` - abstraktna hierarhija (RowRule, SheetRule, WorkbookRule) | 347 | Visoka | 8-12 |
| `rule_registry.py` - registracija z dependency injection | 142 | Srednja | 4-6 |
| **Skupaj** | **~540** | | **12-18 ur** |

### E) Vgrajena validacijska pravila (`rules/builtin/`) — NAJKOMPLEKSNEJŠI DEL

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `sop_compliance_rule.py` - 25+ metod, preverjanje skladnosti s SOP | 1.458 | Zelo visoka | 40-56 |
| `control.py` - 14 razredov, validacija MES kontrol | 1.531 | Zelo visoka | 40-56 |
| `relational.py` - 6 razredov, medvrstična validacija | 655 | Visoka | 16-22 |
| `field.py` - 7 razredov, validacija polj | 377 | Srednja | 10-14 |
| `structural.py` - strukturna validacija | 210 | Srednja | 5-7 |
| **Skupaj** | **~4.230** | | **111-155 ur** |

### F) Grafični vmesnik (`ui/`)

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `main_window.py` - klasični GUI (Tkinter) | 604 | Visoka | 12-16 |
| `main_window_themed.py` - tematski GUI (Sartorius stil) | 557 | Visoka | 10-14 |
| `run_validator.py` - zagonski skript | 64 | Nizka | 2-3 |
| **Skupaj** | **~1.250** | | **24-33 ur** |

### G) Pomožne funkcije (`utils/`)

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `helpers.py` - 35+ funkcij, parsanje časov, intervalov, formul | 1.018 | Zelo visoka | 22-30 |
| `file_paths.py` - iskanje datotek | 94 | Nizka | 2-3 |
| `logger.py` - konfiguracija logiranja | 89 | Nizka | 2-3 |
| **Skupaj** | **~1.200** | | **26-36 ur** |

### H) CLI vmesnik

| Modul | Vrstice | Kompleksnost | Ocena ur |
|---|---|---|---|
| `main.py` - argumenti, formatiranje | 380 | Srednja | 6-8 |

### I) Testiranje

| Aktivnost | Vrstice | Ocena ur |
|---|---|---|
| 11 testnih modulov (`conftest.py`, `test_*.py`) | ~2.780 | 32-44 |
| Integracijsko testiranje in odpravljanje napak | - | 16-24 |
| **Skupaj** | **~2.780** | **48-68 ur** |

### J) Dokumentacija

| Aktivnost | Obseg | Ocena ur |
|---|---|---|
| URS (uporabniške zahteve) - EN + SL | 2 verziji | 8-12 |
| FS (funkcionalna specifikacija) - EN + SL | 2 verziji | 8-12 |
| OQ (operacijska kvalifikacija) - EN + SL | 2 verziji | 8-12 |
| Risk Assessment - EN + SL | 2 verziji | 6-10 |
| SOP Uporaba Validator - EN + SL | 2 verziji | 6-8 |
| QA Review Summary | 1 verzija | 3-4 |
| Skripta za konverzijo MD -> DOCX | 334 vrstic | 4-6 |
| **Skupaj** | **20+ dokumentov** | **43-64 ur** |

---

## 3. Skupna ocena ur

| Sklop | Min. ure | Max. ure |
|---|---|---|
| A) Arhitektura in načrtovanje | 24 | 34 |
| B) Jedro sistema | 36 | 53 |
| C) Excel I/O sloj | 34 | 48 |
| D) Ogrodje pravil | 12 | 18 |
| E) Vgrajena pravila | 111 | 155 |
| F) Grafični vmesnik | 24 | 33 |
| G) Pomožne funkcije | 26 | 36 |
| H) CLI vmesnik | 6 | 8 |
| I) Testiranje | 48 | 68 |
| J) Dokumentacija | 43 | 64 |
| **Razvoj skupaj** | **364** | **517** |
| Projektno vodenje (~15%) | 55 | 78 |
| **SKUPAJ** | **419** | **595** |

**Srednja ocena: ~500 ur**

---

## 4. Finančna ocena

| Urna postavka | Min. cena (419 ur) | Srednja cena (~500 ur) | Max. cena (595 ur) |
|---|---|---|---|
| **40 EUR/uro** (junior/mid) | **16.760 EUR** | **20.000 EUR** | **23.800 EUR** |
| **60 EUR/uro** (senior) | **25.140 EUR** | **30.000 EUR** | **35.700 EUR** |
| **80 EUR/uro** (specialist) | **33.520 EUR** | **40.000 EUR** | **47.600 EUR** |
| **100 EUR/uro** (agencija) | **41.900 EUR** | **50.000 EUR** | **59.500 EUR** |

---

## 5. Utemeljitev ocene

Zakaj je ta projekt vreden toliko:

1. **Domensko znanje MES** — razvijalec mora razumeti MES recepture, kontrole (zaklenipolja, aliObstajaPogoj, kontrolaInterval, kontrolaCasa...), SOP dokumente in farmacevtsko validacijo. To ni trivialno znanje.

2. **Kompleksna poslovna logika** — sam modul `control.py` ima 14 razredov in 1.531 vrstic zelo specifične validacijske logike. Skupaj s `sop_compliance_rule.py` (1.458 vrstic) predstavljata skoraj 3.000 vrstic izjemno specializirane kode.

3. **Parser za Word SOP dokumente** — `sop_loader.py` (741 vrstic) parsira strukturirane Word dokumente, kar zahteva razumevanje formatov `.docx` in kompleksno ekstrakcijo podatkov.

4. **Matematično parsanje** — `helpers.py` (1.018 vrstic) vsebuje 35+ funkcij za parsanje časovnih intervalov, numeričnih razponov, formul, enot in decimalnih mest.

5. **OOP arhitektura z design patterns** — Registry pattern, Strategy pattern, Dependency Injection, Abstract Base Classes — profesionalno zasnovana in razširljiva arhitektura.

6. **Dvojni GUI** — dve popolni verziji grafičnega vmesnika (klasična + tematska).

7. **Celovito testiranje** — 11 testnih modulov z ~2.780 vrsticami testov.

8. **Formalna dokumentacija** — URS, FS, OQ, Risk Assessment, SOP v dveh jezikih — kar je zahteva GMP/farmacevtskih standardov.

---

## Končna ocena

> **Realistična tržna vrednost razvoja aplikacije Validator OOP pri zunanjih razvijalcih:**
>
> | Scenarij | Cena |
> |---|---|
> | Minimalna ocena (40 EUR/uro) | **~17.000 EUR** |
> | Realistična ocena (50-60 EUR/uro) | **~25.000 - 30.000 EUR** |
> | Tržna cena agencije (80-100 EUR/uro) | **~40.000 - 50.000 EUR** |

Upoštevati je treba, da bi zunanji razvijalec potreboval tudi čas za razumevanje domene MES in farmacevtskih zahtev (GMP), kar bi čas razvoja podaljšalo za dodatnih 10-20%. Brez domenskega znanja bi bil projekt za zunanjega razvijalca **realistično vreden 25.000 - 35.000 EUR**.
