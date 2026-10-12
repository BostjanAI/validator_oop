# MES Excel Validator — spletna aplikacija

Spletna plast (UI + API) nad obstoječim `ValidatorEngine`. **Ne vsebuje
validacijske logike** — ta ostaja v `core/` in `rules/`. Ta paket samo
sprejme datoteke prek brskalnika, zažene validacijo v ozadju in dostavi
poročila.

**Faza 2 (produkcijska intranet plast):** AD/LDAP prijava z rolami
(tehnolog / QA / admin), audit trail, trajna zgodovina validacij,
primerjava razdelkov med listi, diff dveh verzij recepture in napredek
v realnem času (WebSocket).

## Arhitektura

```
Brskalnik (React, vendoran, brez build koraka)
        │  HTTP / JSON + multipart upload + WebSocket
        ▼
FastAPI backend  (web/backend)
   ├─ app.py            REST + WebSocket endpointi + serviranje frontenda
   ├─ jobs.py           jobi v ozadju (ThreadPoolExecutor) + napredek
   ├─ service.py        ovojnica okrog ValidatorEngine + generiranje poročil
   ├─ auth.py           AD/LDAP + lokalna prijava, seje, role (faza 2)
   ├─ db.py             SQLite (uporabniki, seje, audit, zgodovina) (faza 2)
   ├─ history.py        trajna zgodovina validacij (faza 2)
   ├─ rules_catalog.py  seznam pravil/kod za konfiguracijo
   ├─ schemas.py        Pydantic modeli (vhod/izhod)
   └─ settings.py       nastavitve (okoljske spremenljivke)
        │
        ▼
ValidatorEngine  (obstoječe jedro – nespremenjeno)
   +  excel/section_compare.py   primerjava razdelkov (izoliran modul)
   +  excel/recipe_diff.py       diff dveh verzij (izoliran modul)
```

Stroga ločitev: frontend ⟷ API ⟷ engine. Frontend ne ve ničesar o Pythonu,
engine ne ve ničesar o HTTP-ju. Podatki spletne plasti (seje, audit,
zgodovina) so v SQLite (`validator_web.db` v `MES_WEB_WORKDIR`), stdlib
`sqlite3` — brez dodatnih odvisnosti.

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
| WS   | `/api/ws/jobs/{id}` | napredek joba v realnem času (faza 2) |
| POST | `/api/auth/login` | prijava (AD/LDAP ali lokalni uporabnik) (faza 2) |
| POST | `/api/auth/logout` | odjava (faza 2) |
| GET  | `/api/auth/me` | stanje prijave (faza 2) |
| GET  | `/api/history` | trajna zgodovina validacij (faza 2) |
| GET  | `/api/history/{id}` | podrobnosti vnosa zgodovine z rezultati (faza 2) |
| GET  | `/api/history/{id}/files/{idx}/report/{name}` | prenos poročila iz zgodovine (faza 2) |
| GET  | `/api/history/{id}/report/{name}` | prenos skupnega poročila iz zgodovine (faza 2) |
| POST | `/api/section-compare` | primerjava razdelkov med listi recepture (faza 2) |
| POST | `/api/diff` | diff dveh verzij recepture (upload ali iz zgodovine) (faza 2) |
| GET  | `/api/audit` | revizijska sled — samo QA/admin (faza 2) |

Ob nalaganju se preverjajo končnice datotek: recepture `.xlsx`/`.xlsm`,
SOP `.docx`, šifranti `.xlsx`/`.xlsm` — napačen tip vrne `415`.

## Avtentikacija in role (faza 2)

Privzeto je prijava **izklopljena** (razvojni način, obnašanje kot MVP).
Vklop: `MES_WEB_AUTH_ENABLED=1`. Načini (`MES_WEB_AUTH_MODE`):

- `ldap` — samo AD/LDAP (potrebuje paket `ldap3` in `MES_WEB_LDAP_*`),
- `local` — samo lokalni uporabniki,
- `mixed` — najprej AD/LDAP, ob neuspehu lokalni fallback (privzeto).

Role in pravice:

| Rola | Validacija | Zgodovina | Audit |
|------|-----------|-----------|-------|
| `tehnolog` | ✔ | samo lastna | ✘ |
| `qa` | ✔ | vsa | ✔ |
| `admin` | ✔ | vsa | ✔ |

Pri AD/LDAP se rola določi iz članstva v AD skupinah
(`MES_WEB_LDAP_GROUP_TEHNOLOG/QA/ADMIN`); uporabnik brez mapirane skupine
dobi `MES_WEB_LDAP_DEFAULT_ROLE` (prazno = prijava zavrnjena).

Lokalni uporabniki: JSON datoteka (`MES_WEB_LOCAL_USERS_FILE`) s PBKDF2
hashi gesel. Vnos pripraviš z:

```python
from validator_oop.web.backend.auth import generate_local_user_entry
print(generate_local_user_entry("mnovak", "geslo123", "qa", "Miha Novak"))
```

Za hiter razvoj/dev: `MES_WEB_DEV_USERS="admin:geslo:admin"` (čistopis,
samo za razvoj!).

Seje: strežniški žetoni v SQLite + HttpOnly piškotek `mes_session`
(`MES_WEB_SESSION_TTL_MIN`, privzeto 480 min). Ob HTTPS vklopi
`MES_WEB_SECURE_COOKIES=1`.

## Zgodovina in audit (faza 2)

- Vsaka zaključena validacija se trajno shrani: povzetek v SQLite,
  celotni rezultati + poročila + vhodne datoteke v `workdir/history/{id}/`
  (vhodne datoteke omogočajo kasnejši diff verzij).
- Retencija: `MES_WEB_HISTORY_TTL_DAYS` (0 = brez samodejnega brisanja).
- Audit trail beleži: prijave (tudi neuspešne), odjave, zagon in zaključek
  validacij, prenose poročil, primerjave razdelkov in diff verzij —
  z uporabnikom, rolo, IP naslovom in časom.

## Nastavitve (okoljske spremenljivke)

| Spremenljivka | Privzeto | Opis |
|---------------|----------|------|
| `MES_WEB_WORKDIR` | sistemski temp | mapa za začasne datoteke jobov + zgodovino + SQLite |
| `MES_WEB_MAX_WORKERS` | `2` | število hkratnih validacij |
| `MES_WEB_MAX_UPLOAD_MB` | `50` | največja velikost datoteke |
| `MES_WEB_JOB_TTL_MIN` | `120` | po koliko minutah se začasni job počisti |
| `MES_WEB_CORS_ORIGINS` | (prazno) | dovoljeni CORS origini (ločeni z vejico) |
| `MES_WEB_SERVE_FRONTEND` | `1` | ali strežnik postreže tudi frontend |
| `MES_WEB_AUTH_ENABLED` | `0` | vklop prijave (faza 2) |
| `MES_WEB_AUTH_MODE` | `mixed` | `ldap` / `local` / `mixed` |
| `MES_WEB_SESSION_TTL_MIN` | `480` | veljavnost seje |
| `MES_WEB_SECURE_COOKIES` | `0` | `Secure` atribut piškotka (vklopi ob HTTPS) |
| `MES_WEB_LOCAL_USERS_FILE` | (prazno) | JSON datoteka lokalnih uporabnikov |
| `MES_WEB_DEV_USERS` | (prazno) | dev uporabniki `user:geslo:rola,…` |
| `MES_WEB_LDAP_SERVER` | (prazno) | npr. `ldaps://dc1.podjetje.local:636` |
| `MES_WEB_LDAP_USE_SSL` | `0` | LDAPS |
| `MES_WEB_LDAP_USER_DN` | `{username}` | predloga bind DN/UPN, npr. `{username}@podjetje.local` |
| `MES_WEB_LDAP_BASE_DN` | (prazno) | baza za iskanje uporabnika/skupin |
| `MES_WEB_LDAP_GROUP_TEHNOLOG` | (prazno) | AD skupina za rolo tehnolog |
| `MES_WEB_LDAP_GROUP_QA` | (prazno) | AD skupina za rolo QA |
| `MES_WEB_LDAP_GROUP_ADMIN` | (prazno) | AD skupina za rolo admin |
| `MES_WEB_LDAP_DEFAULT_ROLE` | `tehnolog` | rola brez skupine (prazno = zavrni) |
| `MES_WEB_DB_PATH` | `workdir/validator_web.db` | pot do SQLite baze |
| `MES_WEB_HISTORY_TTL_DAYS` | `0` | retencija zgodovine (0 = neomejeno) |

## Funkcionalnosti

- Nalaganje ene ali več receptur (.xlsx/.xlsm), drag & drop, validacija
  tipov datotek ob uploadu.
- Opcijske vhodne datoteke: SOP (.docx), šifrant raztopin, šifrant kemikalij, šifrant repro materiala.
- Validacija teče s privzetimi nastavitvami (brez konfiguracije v vmesniku).
- Validacija v ozadju z napredkom v **realnem času** (WebSocket, samodejni
  fallback na polling; po datotekah, slovenski statusi).
- Pregled rezultatov: povzetek neveljavnih datotek, iskanje, filtri
  (list/koda/datoteka), grupiranje (po listu/kodi/datoteki), razvrščanje po
  stolpcih, graf napak po kodah, strni/razširi vse skupine.
- Prenos poročil: samo Excel; pri več datotekah tudi **skupno Excel poročilo**
  za celoten batch.
- **Prijava** (AD/LDAP ali lokalni uporabnik) z rolami tehnolog/QA/admin.
- **Zgodovina validacij**: trajni pregled preteklih validacij s ponovnim
  prenosom Excel poročil (tudi po TTL čiščenju začasnih jobov).
- **Diff dveh verzij recepture**: naloženi datoteki ali datoteki iz
  zgodovine; dodane/odstranjene/spremenjene vrstice po stolpcih.
- **Audit trail** (QA/admin): kdo, kdaj, kaj — s filtri in straničenjem.
- Vizualna identiteta: Sartorius črno-rumena tema (kot desktop PyQt6 GUI).

## Testi

```bash
pytest tests/test_web_api.py        # API testi MVP (TestClient, brez strežnika)
pytest tests/test_web_phase2.py     # testi faze 2 (auth, zgodovina, audit, WS, primerjave)
```

E2E testi MVP uporabljajo `samples/Poročilo/MOD-QA.xlsx` (preskočeni, če
datoteka ni na voljo); testi faze 2 generirajo lastne testne recepture.
Za poganjanje so potrebne odvisnosti iz `web/requirements-web.txt` ter
`httpx`.

## HTTPS (AD CS)

Za vklop HTTPS z internim certifikatom glej `web/deploy/HTTPS_AD_CS.md`
(izdaja certifikata pri internem AD CS, namestitev v nginx, WebSocket
prek `wss://`, `MES_WEB_SECURE_COOKIES`).
