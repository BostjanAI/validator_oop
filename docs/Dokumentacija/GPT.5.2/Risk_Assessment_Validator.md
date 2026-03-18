# Risk Assessment – Validator MES Receptur

## Dokumentni podatki

- **Naziv**: Risk Assessment – Validator MES Receptur
- **Sistem / aplikacija**: Validator (`validator_oop`)
- **ID dokumenta**: VAL-RA-001
- **Verzija**: 1.0
- **Datum**: 2026-02-04
- **Pripravil**: ______________________
- **Pregledal (QA)**: ______________________
- **Odobril**: ______________________

## 1. Namen

Namen ocene tveganja je identificirati in ovrednotiti tveganja, povezana z uporabo Validatorja, ter definirati ustrezne kontrole za zmanjšanje tveganj na sprejemljivo raven.

## 2. Obseg in kontekst

- Validator je **offline** orodje za validacijo Excel receptur in (opcijsko) skladnosti s SOP.
- Validator ne izvaja neposrednega procesnega krmiljenja in nima elektronskih podpisov.
- Rezultat validatorja je **podpora odločanju**; končno odobritev in odgovornost nosi uporabnik/proces.

## 3. Metodologija

Ocena tveganja uporablja kvalitativno lestvico:

- **S (Severity / Resnost)**: 1 (nizka) … 5 (kritična)
- **P (Probability / Verjetnost)**: 1 (redko) … 5 (pogosto)
- **D (Detectability / Zaznavnost)**: 1 (zlahka zaznavno) … 5 (težko zaznavno)
- **RPN** \(= S \times P \times D\)

### 3.1 Sprejemljivost tveganja (primer)

> Pragovi so organizacijski; spodaj je predlog, ki se lahko prilagodi.

- **RPN 1–20**: sprejemljivo
- **RPN 21–40**: sprejemljivo z utemeljitvijo / dodatnimi kontrolami
- **RPN > 40**: zahteva dodatne kontrole ali spremembo zasnove/procesa

## 4. Klasifikacija sistema (GAMP – informativno)

Validator je po naravi **custom**/konfigurabilno orodje z vgrajenimi pravili (GAMP 5 tipično **kategorija 4 ali 5**, odvisno od formalne interpretacije in uporabe). Ker vpliva na kakovost podatkov receptur, je priporočljiv proporcionalen nivo validacije (URS/FS/OQ + kontrola sprememb).

## 5. Identifikacija tveganj in kontrole

### 5.1 Tabela tveganj

| ID | Nevarnost / Failure mode | Vzrok | Potencialni vpliv | S | P | D | RPN | Kontrole (preventivne/detekcijske) | Preostalo tveganje |
|---|---|---|---|---:|---:|---:|---:|---|---|
| RA-01 | **False negative** (Validator ne zazna napake) | napaka v pravilu; nepričakovan format Excel; filtriranje listov preskoči relevanten list | napačna receptura se lahko uporabi; potencialni vpliv na kakovost/batch | 5 | 2 | 4 | 40 | OQ z realnimi vzorci; periodični pregled pravil; obvezna človeška kontrola; kontrola sprememb; poročilo z lokacijami | znižano (odvisno od procesa) |
| RA-02 | **False positive** (preveč napak) | pravilo preveč strogo; formatne variacije | nepotrebne korekcije, zamude | 2 | 3 | 2 | 12 | proces za obravnavo odstopanj; bypass po odobritvi; tuning pravil | nizko |
| RA-03 | Nepravilno generirano Excel poročilo | napaka v zapisovalniku; nezdružljiv openpyxl | uporabnik napačno interpretira ali izgubi rezultate | 3 | 2 | 3 | 18 | OQ test poročil; možnost JSON/TXT; vizualna kontrola poročila; log datoteka | nizko |
| RA-04 | Runtime napaka pri branju Excel | poškodovana datoteka; manjkajo odvisnosti | validacija se ne izvede; zamude | 2 | 3 | 1 | 6 | jasna sporočila; log; navodila namestitve; fallback na CLI/GUI | nizko |
| RA-05 | Nepravilna interpretacija formul | `include_formulas` ni uporabljen; formula parser ne pokrije vseh oblik | napačna odločitev pri pravilih odvisnih od formul | 4 | 2 | 4 | 32 | OQ test s formulami; v GUI privzeto `include_formulas=True`; dokumentirana omejitev; ročna verifikacija pri kritičnih primerih | srednje |
| RA-06 | SOP `.docx` napačno interpretiran | drugačna struktura SOP; OCR/formatiranje; python-docx omejitve | napačne SOP napake ali izpuščena neskladnost | 4 | 2 | 4 | 32 | SOP validacija opcijska; log ekstrakcije; OQ test z referenčnim SOP; QA pregled SOP mapiranja; obravnava odstopanj | srednje |
| RA-07 | Nepravilna uporaba `--bypass` | uporabnik izključi kritično pravilo brez kontrole | pomembne napake ostanejo neodkrite | 5 | 2 | 4 | 40 | SOP za uporabo + omejitev bypass na power user; dokumentiranje bypass; QA pregled; strict/baseline primerjava v OQ | srednje |
| RA-08 | `apply fixes` spremeni napačne celice | neustrezno mapiranje target_cell; napačna predlagana vrednost | poškodovana kopija recepture; možnost napačne uporabe kopije | 4 | 1 | 3 | 12 | apply-fixes samo na kopijo; jasno poimenovanje `_AUTOFIX`; obvezna ročna kontrola kopije; OQ dokaz | nizko |
| RA-09 | Nezadostna sledljivost rezultatov (audit trail) | brez centralnega logiranja/identitete uporabnika | težje dokazovanje kdo/kdaj/kaj | 3 | 2 | 4 | 24 | shranjevanje poročil v kontrolirano mapo; log datoteka `MESValidator.log`; proceduralna kontrola (SOP) | srednje |
| RA-10 | Nepravilna lokalizacija/encoding (Windows konzola) | ne-UTF-8 console; šumniki | nerazumljiv izpis; zmeda pri uporabi | 1 | 3 | 1 | 3 | Excel/TXT poročila kot primarni artefakt; ASCII-safe status v CLI kjer relevantno | nizko |

### 5.2 Ključne kontrole (povzetek)

- **Validacija proporcionalno tveganju**:
  - URS/FS/OQ komplet (ta paket) + retest ob spremembah pravil.
- **Operativne kontrole**:
  - uporaba kot podporno orodje; obvezna človeška presoja pred odobritvijo recepture.
  - shranjevanje poročil v kontrolirano lokacijo.
- **Tehnične kontrole**:
  - izhodni formati (Excel + JSON/TXT) zmanjšajo tveganje izgube evidence.
  - log datoteka `MESValidator.log` za diagnostiko.
  - `apply fixes` deluje na kopiji.

## 6. Preostalo tveganje in zaključek

Z ustreznimi kontrolami (OQ, proceduralna uporaba, kontrola sprememb, ročna presoja) je preostalo tveganje ocenjene kot **sprejemljivo**, pri čemer je za kritične točke (false negative, bypass, SOP interpretacija) priporočena okrepljena kontrola (QA pregled, retest po spremembah, dokazila uporabe).

Podpisi:

- Pripravil: ______________________ Datum: ____________
- QA pregled: ______________________ Datum: ____________
- Odobril: _________________________ Datum: ____________

