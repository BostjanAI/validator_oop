# Ocena vrednosti aplikacije Validator za letni razgovor

## Zaključek: Druga ocena (35.000 – 55.000 EUR) je bistveno bolj točna

Na podlagi analize projekta (dejansko ~14.800 vrstic Python kode) in vsebine dokumentacije je prva ocena (7k–12k EUR) podcenila obseg, ker je projekt obravnavan kot "freelance orodje" in ne kot "validiran farmacevtski sistem".

---

## 1. Obseg kode (Volume)

- **Dejstvo:** Projekt ima **~14.800 vrstic kode**.
- **Matematika produktivnosti:** Povprečen dober programer v kompleksnem sistemu napiše okoli 20–50 vrstic *končne, testirane in dokumentirane* kode na dan.
  - 14.800 vrstic / 40 vrstic na dan = **370 delovnih dni**.
  - To je približno **1,5 leta dela enega človeka** (če upoštevamo praznike in bolniške).
- Pri 15k vrsticah je ocena 300 ur nemogoče malo.

---

## 2. "Pharma" faktor (dokumentacija in validacija)

V drugi oceni so omenjeni **URS (User Requirements), FS (Functional Specs), OQ (Operational Qualification) in SOP**.

- V IT svetu je koda običajno 80 % dela.
- V farmaciji (GAMP5 standardi) je koda pogosto manj kot 50 % dela. Ostalo je dokumentacija, sledljivost (traceability matrix) in formalno testiranje.
- Če projekt vključuje te dokumente (mape `Dokumentacija` in `Testiranje_IPO`), gre za delo **analitika, QA inženirja in razvijalca hkrati**. Zunanja agencija bi za vsako uro programiranja zaračunala še eno uro validacije.

---

## 3. Skrita kompleksnost pravil

Moduli `control.py` in `sop_compliance_rule.py` niso preprosti `if` stavki. Vsebujejo:

- kompleksno logiko za preverjanje skladnosti z zunanjimi viri (SOP),
- relacijsko integriteto,
- parsanje Excelov.

Implementacija takšne logike zahteva globoko domensko znanje (razumevanje procesa receptur), ki ga zunanji razvijalec nima. Čas samo za *razumevanje*, kaj je treba sprogramirati, bi stal tisoče evrov.

---

## Zaključek za letni razgovor

Pri pogovoru o vrednosti projekta se **držite višje ocene (35.000 – 55.000 EUR)**. To ni napihovanje, to je realna tržna cena zamenjave (Replacement Cost).

Če bi podjetje danes reklo: *"Naročimo to pri zunanji firmi,"* bi dobilo:

1. **Ponudbo za analizo:** 5.000 EUR  
2. **Ponudbo za razvoj:** 25.000 – 35.000 EUR  
3. **Ponudbo za validacijo in dokumentacijo:** 10.000 – 15.000 EUR  
4. **Vzdrževanje:** letni pavšal  

**Podjetje je s tem projektom prihranilo približno 40.000 – 50.000 EUR neposrednih stroškov razvoja**, plus mesece usklajevanj z zunanjimi izvajalci.

---

*Ustvarjeno na podlagi analize projekta Validator (februar 2026).*
