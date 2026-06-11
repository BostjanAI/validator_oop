# MES Excel Validator — spletna aplikacija

Spletna plast (UI + API) nad obstoječim `ValidatorEngine`. **Ne vsebuje
validacijske logike** — ta ostaja v `core/` in `rules/`. Ta paket samo
sprejme datoteke prek brskalnika, zažene validacijo v ozadju in dostavi
poročila.

## Arhitektura

```
Brskalnik (React, vendoran, brez build koraka)
        │  HTTP / JSON + multipart upload
        ▼
FastAPI backend  (web/backend)
   ├─ app.py            REST endpointi + serviranje frontenda
   ├─ jobs.py           jobi v ozadju (ThreadPoolExecutor) + napredek
   ├─ service.py        ovojnica okrog ValidatorEngine + generiranje poročil
   ├─ rules_catalog.py  seznam pravil/kod za konfiguracijo
   ├─ schemas.py        Pydantic modeli (vhod/izhod)
   └─ settings.py       nastavitve (okoljske spremenljivke)
        │
        ▼
ValidatorEngine  (obstoječe jedro – nespremenjeno)
```

Stroga ločitev: frontend ⟷ API ⟷ engine. Frontend ne ve ničesar o Pythonu,
engine ne ve ničesar o HTTP-ju.

## Zagon (razvoj / lokalno)

```bash
# Namestitev odvisnosti (poleg osnovnih requirements.txt)
pip install -r web/requirements-web.txt

# Zagon strežnika (iz korena paketa validator_oop)
python run_web.py                       # http://127.0.0.1:8000
python run_web.py --host 0.0.0.0 --port 8080
python run_web.py --reload              # razvojni način
```

Odpri `http://127.0.0.1:8000` v brskalniku. API dokumentacija (OpenAPI):
`http://127.0.0.1:8000/docs`.

> Frontend je v celoti **offline**: React, ReactDOM in Babel so lokalno
> vendorani v `web/frontend/static/vendor/`. Brez npm/Node.js, brez CDN.

## Deployment (on-prem, interno omrežje)

```bash
docker compose -f web/deploy/docker-compose.yml up -d --build
# Dostop: http://<streznik>:8080  (prek nginx reverse proxyja)
```

- Slika je samostojna in deluje brez interneta.
- Za HTTPS z internim certifikatom (AD CS) glej zakomentirani del v
  `web/deploy/nginx.conf` in `docker-compose.yml`.
- Šifrante/SOP lahko priklopiš z network share (volume `:ro`).

## API (povzetek)

| Metoda | Pot | Opis |
|--------|-----|------|
| GET  | `/api/health` | zdravstveni pregled |
| GET  | `/api/rules`  | katalog pravil + kod napak |
| POST | `/api/validate` | naloži recepture (+ SOP/šifranti) + konfiguracijo → `job_id` |
| GET  | `/api/jobs/{id}` | stanje/napredek joba |
| GET  | `/api/jobs/{id}/results` | rezultati validacije |
| GET  | `/api/jobs/{id}/files/{idx}/report/{name}` | prenos poročila za posamezno datoteko |
| GET  | `/api/jobs/{id}/report/{name}` | prenos skupnega (batch) poročila |

Ob nalaganju se preverjajo končnice datotek: recepture `.xlsx`/`.xlsm`,
SOP `.docx`, šifranti `.xlsx`/`.xlsm` — napačen tip vrne `415`.

## Nastavitve (okoljske spremenljivke)

| Spremenljivka | Privzeto | Opis |
|---------------|----------|------|
| `MES_WEB_WORKDIR` | sistemski temp | mapa za začasne datoteke jobov |
| `MES_WEB_MAX_WORKERS` | `2` | število hkratnih validacij |
| `MES_WEB_MAX_UPLOAD_MB` | `50` | največja velikost datoteke |
| `MES_WEB_JOB_TTL_MIN` | `120` | po koliko minutah se job počisti |
| `MES_WEB_CORS_ORIGINS` | (prazno) | dovoljeni CORS origini (ločeni z vejico) |
| `MES_WEB_SERVE_FRONTEND` | `1` | ali strežnik postreže tudi frontend |

## Funkcionalnosti

- Nalaganje ene ali več receptur (.xlsx/.xlsm), drag & drop, validacija
  tipov datotek ob uploadu.
- Opcijske vhodne datoteke: SOP (.docx), šifrant raztopin, šifrant kemikalij.
- Konfiguracija: strogi način, formule, SOP/šifranti, preskoči pravila/kode,
  zaklenipolja zastavice, (opcijsko) auto-fix. Konfiguracija se ohrani med
  sejami (localStorage).
- Validacija v ozadju z napredkom (po datotekah, slovenski statusi).
- Pregled rezultatov: povzetek (kliklive ploščice za hitro filtriranje),
  iskanje, filtri (resnost/list/koda/datoteka), grupiranje (po
  listu/kodi/resnosti/datoteki), razvrščanje po stolpcih, graf napak po
  kodah, strni/razširi vse skupine.
- Prenos poročil: Excel, JSON, TXT, management (.md) in (opcijsko) auto-fix;
  pri več datotekah tudi **skupno poročilo** za celoten batch.
- Vizualna identiteta: Sartorius črno-rumena tema (kot desktop PyQt6 GUI).

## Testi

```bash
pytest tests/test_web_api.py        # API testi (TestClient, brez strežnika)
```

E2E testi uporabljajo `samples/Poročilo/MOD-QA.xlsx` (preskočeni, če
datoteka ni na voljo). Za poganjanje so potrebne odvisnosti iz
`web/requirements-web.txt` ter `httpx`.
