# Naloga: Spletna aplikacija MES Excel Validator (intranet / on-premise)

**Datum specifikacije:** junij 2026  
**Ciljno okolje:** samo službeno notranje omrežje (intranet), brez javnega dostopa z interneta  
**Jezik vmesnika:** slovenščina

---

## 1. Kontekst

Obstaja delujoč Python projekt **validator_oop** — validacijski engine za farmacevtske MES recepture (IPO) v Excel formatu (.xlsx/.xlsm). Projekt je čist OOP z ~40 pluggable pravili in trenutno ima desktop GUI (Tkinter/PyQt6) ter CLI.

**NE piši validacijske logike na novo.** Obstoječi engine mora ostati jedro sistema. Spletna aplikacija je nova plast (UI + API) nad obstoječim `ValidatorEngine`.

### Ključna dokumentacija v repozitoriju

- `docs/Dokumentacija/OPIS_PROGRAMA.md` — tehnični opis, podatkovni tok, API razredov
- `docs/Dokumentacija/ARHITEKTURA_PROJEKTA.md` — arhitektura modulov
- `docs/PRAVILA_VALIDATORJA.md` — poslovna pravila
- `core/validator_engine.py`, `core/config.py`, `core/report.py`, `core/error.py`
- `excel/report_writer.py`, `excel/management_report.py`, `excel/catalog_loader.py`
- `ui/main_window_qt.py` — referenca za obstoječe funkcionalnosti desktop GUI
- `web/README.md` — obstoječa spletna plast (če že obstaja)

### Obstoječe stanje (če `web/` že obstaja)

Preveri mapo `web/` pred začetkom. Če je MVP že implementiran, **ne prepisuj od začetka** — razširi, popravi ali pripravi za produkcijski intranet deployment. Obstoječa struktura:

```
web/
├── backend/          FastAPI (app.py, service.py, jobs.py, schemas.py, settings.py)
├── frontend/         React (vendoran, brez npm build koraka)
├── deploy/           Docker Compose + nginx (on-prem)
├── requirements-web.txt
└── README.md
```

---

## 2. Cilj

Zgraditi (ali dokončati) **intranet spletno aplikacijo**, ki uporabnikom (tehnologi, QA) na službenem omrežju omogoča:

1. Nalaganje ene ali več Excel receptur prek brskalnika
2. Izbiranje opcijskih vhodnih datotek (SOP .docx, šifranti kemikalij/raztopin)
3. Konfiguracijo validacije (strict mode, bypass, formule, zaklenipolja zastavice, itd.)
4. Zagon validacije z vizualnim napredkom
5. Pregled rezultatov v brskalniku (filtri, skupine po listu/kodi/resnosti)
6. Prenos poročil (Excel, JSON, TXT, management report, opcijsko auto-fix)
7. (Faza 2) Primerjava razdelkov med listi, AD avtentikacija, audit trail

---

## 3. Deployment — SAMO notranje omrežje (intranet)

> **Web aplikacija ≠ javni internet.** Aplikacija mora biti dostopna izključno znotraj službenega omrežja.

### Zahteve

- Aplikacija **NE sme** biti dostopna z javnega interneta
- Zagon na notranjem Windows ali Linux strežniku v podjetju
- Dostop samo iz službenega LAN ali prek obstoječega VPN
- **Brez obvezne povezave** na zunanje storitve (brez SaaS, brez cloud API, brez CDN)
- Frontend mora delovati **offline** — React in odvisnosti vendorane lokalno (brez npm/CDN v produkciji)
- Šifranti (kemikalije, raztopine) in SOP datoteke — lokalno na strežniku ali network share (`:ro` volume)
- HTTPS z notranjim certifikatom (AD CS) ali HTTP znotraj zaščitenega omrežja
- Docker Compose + nginx reverse proxy — vse on-premise

### Omrežna shema

```
[Računalnik tehnologa]  ──►  [Službeni intranet / LAN / VPN]
                                    │
                                    ▼
                         [Notranji strežnik]
                         ├── nginx (port 8080/443)
                         ├── FastAPI backend (port 8000, internal)
                         ├── React frontend (serviran iz FastAPI)
                         └── validator_oop engine (Python import)
```

Primer dostopa: `http://mes-validator.lokalna.domena` ali `http://10.x.x.x:8080`

### Varnostni ukrepi

| Ukrep | Opis |
|-------|------|
| Firewall | Odprt port samo znotraj podjetja (npr. 8080/443 za `10.0.0.0/8`) |
| Brez public IP | Strežnik nima javnega naslova ali je za NAT-om |
| AD avtentikacija | (Faza 2) Windows Authentication / LDAP |
| Temp cleanup | Avtomatsko brisanje naloženih Excel datotek po X urah (`MES_WEB_JOB_TTL_MIN`) |
| Upload limit | Maks. velikost datoteke (privzeto 50 MB, `MES_WEB_MAX_UPLOAD_MB`) |
| MIME validacija | Preverjanje tipov datotek ob uploadu |
| Audit log | (Faza 2) Kdo je kdaj validiral katero datoteko |

---

## 4. Arhitektura — zahtevana ločitev

```
┌─────────────────────────────────────────┐
│  Frontend (React, vendoran lokalno)      │
│  — upload, nastavitve, prikaz napak     │
└──────────────────┬──────────────────────┘
                   │ HTTP / JSON + multipart (samo intranet)
                   ▼
┌─────────────────────────────────────────┐
│  FastAPI backend (web/backend/)          │
│  — thin wrapper okoli ValidatorEngine    │
│  — job queue (ThreadPoolExecutor)        │
│  — temp file storage                     │
└──────────────────┬──────────────────────┘
                   │ direkten Python import
                   ▼
┌─────────────────────────────────────────┐
│  validator_oop (obstoječi paket)        │
│  ValidatorEngine → RuleEngine → Rules     │
└─────────────────────────────────────────┘
```

### Backend zahteve

- Uporabi **FastAPI**
- Direktno importaj obstoječe module:

```python
from validator_oop.core import ValidatorEngine, ValidatorConfig, RuleEngine
from validator_oop.excel import ExcelLoader
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.excel.management_report import write_management_report
from validator_oop.rules.builtin import register_all
```

- Ob zagonu pokliči `register_all()` (obvezno!)
- **Ne spreminjaj** `core/`, `rules/`, `excel/` logike razen če je nujno za API integracijo
- Struktura v `web/backend/`:
  - `app.py` — REST endpointi + serviranje frontenda
  - `schemas.py` — Pydantic modeli (request/response)
  - `service.py` — orkestracija klica `ValidatorEngine.validate()`
  - `jobs.py` — background jobi + napredek
  - `settings.py` — okoljske spremenljivke
  - `rules_catalog.py` — seznam pravil za UI konfiguracijo

### Frontend zahteve

- React (vendoran v `web/frontend/static/vendor/`, brez npm build koraka v produkciji)
- Responsive layout (desktop-first)
- Vizualna identiteta: **Sartorius črno-rumena tema** (kot PyQt6 GUI):
  - Header: `#000000`
  - Akcent: `#FFE600`
  - Ozadje: `#f5f5f5`
  - Font: Segoe UI / sans-serif
- Jezik vmesnika: **slovenščina**

---

## 5. Funkcionalne zahteve (MVP)

### 5.1 Nalaganje datotek

- Drag & drop ali file picker za:
  - **Receptura(e)**: `.xlsx`, `.xlsm` (več datotek hkrati)
  - **SOP** (opcijsko): `.docx`
  - **Šifrant raztopin** (opcijsko): `.xlsx`
  - **Šifrant kemikalij** (opcijsko): `.xlsx`
- Prikaz seznama naloženih datotek z možnostjo odstranitve
- Maks. velikost: konfigurabilno (privzeto 50 MB)

### 5.2 Nastavitve validacije

Preslikaj obstoječi `ValidatorConfig` in CLI argumente:

| Nastavitev | Tip | Privzeto |
|------------|-----|----------|
| `strict_mode` | bool | false |
| `include_formulas` | bool | false |
| `bypass_rules` | string[] | [] |
| `bypass_codes` | string[] | [] |
| `enable_sop_validation` | bool | true |
| `enable_catalog_validation` | bool | true |
| `bypass_zakleni_require_empty_for_checkbox` | bool | true |
| `bypass_zakleni_require_pogoj_for_param1_steps` | bool | true |
| `bypass_zakleni_inverse_pogoj_requirement` | bool | false |
| `apply_fixes` | bool | false |
| Način poročila | enum | `combined` / `per_file` |

### 5.3 Zagon validacije

- Gumb „Zaženi validacijo"
- Progress indikator (loading → processing → done)
- Za več datotek: napredek po datoteki (npr. 2/5)
- Validacija v ozadju (background job) — ne blokiraj HTTP zahtevka

### 5.4 Prikaz rezultatov

Tabela napak s stolpci:

- Resnost (ERROR / WARNING / INFO) — barvno kodirano
- Koda napake
- List (sheet)
- Vrstica
- Stolpec
- Sporočilo

Filtri:

- Po resnosti
- Po listu
- Po kodi napake
- Po datoteki (batch)
- Iskanje po besedilu sporočila

Grupiranje:

- Po listu
- Po kodi
- Po resnosti
- Po datoteki

Povzetek na vrhu:

- Število errors / warnings / info
- Status: VALID / INVALID
- (Opcijsko) graf po kodah napak

### 5.5 Izvoz poročil

- Prenos Excel poročila (`.xlsx` — lista „Napake" + „Povzetek")
- Prenos JSON
- Prenos TXT (human-readable)
- Poročilo za vodstvo (`write_management_report` → `.md`)
- (Opcijsko) Auto-fix kopija (`WorkbookFixer`)

---

## 6. API endpointi

```
GET    /api/health                                    — health check
GET    /api/rules                                     — seznam pravil + kod napak
POST   /api/validate                                  — upload + validacija → job_id
GET    /api/jobs/{job_id}                             — status/napredek joba
GET    /api/jobs/{job_id}/results                     — JSON rezultati validacije
GET    /api/jobs/{job_id}/files/{idx}/report/{name}   — prenos poročila (excel|json|txt|management|autofix)
```

### Response model za napako

```json
{
  "rule": "zaklenipolja",
  "code": "CTRL_ZAKLENI",
  "code_label": "Zakleni polja",
  "severity": "error",
  "message": "Korak 5: polje 'Navodilo' mora biti prazno...",
  "sheet": "Receptura 1",
  "workbook": "MOD-QA.xlsx",
  "row": 7,
  "col": "Navodilo"
}
```

### Response model za job

```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": 0.4,
  "message": "Validacija 2/5: MOD-QA.xlsx",
  "created_at": "2026-06-05T10:00:00"
}
```

---

## 7. Okoljske spremenljivke

| Spremenljivka | Privzeto | Opis |
|---------------|----------|------|
| `MES_WEB_WORKDIR` | sistemski temp | mapa za začasne datoteke jobov |
| `MES_WEB_MAX_WORKERS` | `2` | število hkratnih validacij |
| `MES_WEB_MAX_UPLOAD_MB` | `50` | največja velikost datoteke |
| `MES_WEB_JOB_TTL_MIN` | `120` | po koliko minutah se job počisti |
| `MES_WEB_CORS_ORIGINS` | (prazno) | dovoljeni CORS origini |
| `MES_WEB_SERVE_FRONTEND` | `1` | ali strežnik postreže tudi frontend |

---

## 8. Docker / intranet deployment

```bash
# Zgradba in zagon na notranjem strežniku
docker compose -f web/deploy/docker-compose.yml up -d --build

# Dostop iz službenega omrežja
http://<streznik>:8080
```

### Docker Compose zahteve

- Samostojna slika — deluje brez interneta
- nginx reverse proxy pred FastAPI
- Volume za temp podatke (`validator_data`)
- Opcijski volume za šifrante/SOP iz network share (`:ro`)
- `restart: unless-stopped`
- Port `8080` (HTTP) ali `8443` (HTTPS z internim certifikatom)

### nginx zahteve

- Proxy pass na FastAPI (`validator:8000`)
- Brez dostopa izven podjetja (firewall na infrastrukturni ravni)
- Zakomentirana HTTPS sekcija za AD CS certifikat

### Razvojni zagon (lokalno)

```bash
pip install -r web/requirements-web.txt
python run_web.py                       # http://127.0.0.1:8000
python run_web.py --host 0.0.0.0 --port 8080
python run_web.py --reload              # razvojni način
```

API dokumentacija (OpenAPI): `http://127.0.0.1:8000/docs`

---

## 9. Nefunkcionalne zahteve

| Zahteva | Opis |
|---------|------|
| Zmogljivost | Validacija 10–60 s; background job, ne blokiraj UI |
| Varnost | MIME validacija, sanitizacija imen, avtomatski cleanup |
| Offline | Brez CDN, brez zunanjih API-jev, vendorani JS/CSS |
| Testiranje | pytest za API + obstoječi testi engine ostanejo |
| Logiranje | Strukturirani logi, korelacijski ID na job |
| Kompatibilnost | CLI in desktop GUI morata še naprej delovati |
| CHANGELOG | Vsaka sprememba kode → posodobi `CHANGELOG.md` (slovensko) |

---

## 10. Faza 2 (ne v MVP, a pripravi arhitekturo)

- Primerjava razdelkov med listi (kot gumb v Qt GUI)
- Windows AD / LDAP avtentikacija
- Audit trail (kdo, kdaj, katera datoteka)
- Zgodovina zagonov (integracija z `validation_progress.json`)
- WebSocket za real-time progress
- HTTPS z AD CS certifikatom (produkcija)

---

## 11. Omejitve in pravila razvoja

1. **Ne refaktoriraj** `control.py`, `shared_context.py` ali pravil — ločen task
2. **Ne dodajaj** ORM-ja v core — DB samo za web plast (če sploh)
3. Vsaka sprememba obstoječe kode → posodobi `CHANGELOG.md`
4. Ohrani kompatibilnost z obstoječim CLI in desktop GUI
5. Uporabi `samples/Poročilo/` datoteke za ročno/E2E testiranje
6. Frontend brez npm v produkciji — vendorani React/Babel
7. Aplikacija mora delovati brez internetne povezave

---

## 12. Deliverables

1. `web/` mapa z backend API in frontend
2. `web/deploy/docker-compose.yml` + `Dockerfile` + `nginx.conf`
3. `run_web.py` — vstopna točka za razvojni zagon
4. `web/README.md` — navodila za zagon, API, intranet deployment
5. E2E test: naloži `samples/Poročilo/MOD-QA.xlsx` → preveri JSON report in Excel download

---

## 13. Korak implementacije (predlagan vrstni red)

1. Preveri obstoječe `web/` — če MVP obstaja, preskoči na korake 4–7
2. FastAPI skeleton + `register_all()` + health endpoint
3. `POST /api/validate` z eno datoteko → background job → JSON report
4. Frontend: upload + tabela napak + filtri
5. Več datotek + Excel/JSON/TXT download
6. Nastavitve (strict, bypass, katalogi, SOP, zaklenipolja)
7. Sartorius tema + grupiranje
8. Docker Compose + nginx + intranet README
9. E2E test z vzorčnimi datotekami

---

## 14. Testni scenariji (intranet)

| # | Scenarij | Pričakovan rezultat |
|---|----------|---------------------|
| 1 | Upload `MOD-QA.xlsx` | JSON report z napakami, status INVALID |
| 2 | Upload brez interneta (offline strežnik) | Aplikacija deluje |
| 3 | Dostop iz drugega PC-ja v LAN | `http://streznik:8080` odpre UI |
| 4 | Dostop izven LAN (brez VPN) | Zavrnjeno (firewall) |
| 5 | Upload 3 receptur hkrati | Napredek 1/3, 2/3, 3/3 |
| 6 | Prenos Excel poročila | `.xlsx` z listoma Napake + Povzetek |
| 7 | Strict mode | WARNING postane ERROR |
| 8 | SOP + šifranti | Validacija z dodatnimi pravili |

---

## 15. Model za razvoj v Cursorju (junij 2026)

| Faza | Model |
|------|-------|
| Arhitektura + integracija z engineom | **Claude Opus 4.8 (Thinking)** |
| Implementacija (backend + frontend) | **Composer 2.5** |
| Docker + deployment | **Composer 2.5 (Standard)** |
| Debugging integracije | **Claude Opus 4.8** |
| Ne veš, kaj izbrati | **Auto** |

Na začetku eksplicitno napiši agentu:

> Za arhitekturo uporabi Opus 4.8. Za implementacijo preklopi na Composer 2.5.
> Ne spreminjaj `core/`, `rules/`, `excel/` razen nujnega API wrapperja.
> Deployment je SAMO intranet — brez javnega interneta, brez CDN, brez clouda.

---

## 16. Začetek dela

Začni s pregledom obstoječe mape `web/`. Če MVP že obstaja, oceni kaj manjka
za produkcijski intranet deployment in dokončaj. Če ne obstaja, začni s
korakom 2 (FastAPI skeleton + prvi endpoint).

Po končani spremembi posodobi `CHANGELOG.md` pod `[Unreleased]`.
