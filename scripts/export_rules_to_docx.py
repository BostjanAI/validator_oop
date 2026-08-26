"""
Skripta izvozi vsa pravila validatorja v Word dokument (.docx).
Zahteva: pip install python-docx
Uporaba: python scripts/export_rules_to_docx.py
"""

from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Namestite python-docx: pip install python-docx")
    raise

# Podatki o pravilih (ime, opis, modul)
RULES = [
    # Structural
    ("required_columns", "Preveri prisotnost vseh obveznih stolpcev (št. Koraka, Navodilo, Tip podatka, Ključ preverjanja, Vrednost, Labela, Tip objekta).", "Strukturna pravila"),
    ("step_numbering", "Preveri pravilno številčenje korakov: celo število, brez podvajanj, brez vrzeli, začetek s 1.", "Strukturna pravila"),
    # Field
    ("tip_objekta_rule", "Tip objekta mora biti zapolnjen in med dovoljenimi vrednostmi (edit, checkbox, crta, formula, gumbdatumcas, itd.).", "Pravila polj"),
    ("data_object_compatibility", "Tip podatka mora imeti ustrezen Tip objekta (npr. kemikalija → edit, checkbox → checkbox).", "Pravila polj"),
    ("label_requirements", "Za določene tipe (kemikalija, zaposleni, monolit, repro, reproodpis) mora biti Labela = 'koda'; enota v Labela se mora ujemati z Navodilo.", "Pravila polj"),
    ("key_validation", "Ključ preverjanja: dovoljeni znaki (črke, številke, _, -, .); za kemikalija/raztopina/masa/tehtnica je obvezen.", "Pravila polj"),
    ("formula_syntax", "Formulska polja (formula, formula0, formula1) morajo imeti Vrednost z '=' in sklice na korake ($n).", "Pravila polj"),
    ("comma_number_rule", "Decimalna pika je privzeta; vejice v številih niso dovoljene (razen v Navodilo in parametrih zaklenipolja/aliObstajaPogoj).", "Pravila polj"),
    ("formula_reference_rule", "Formule se lahko sklicujejo le na obstoječe korake.", "Pravila polj"),
    ("formula_step_edit_labela_rule", "Koraki, na katere se formula sklicuje (v stolpcu Vrednost), morajo imeti Tip objekta 'edit', 'formula', 'formula0' ali 'formula1'.", "Pravila polj"),
    # Relational
    ("duplicate_key_rule", "Ključi za kemikalija, raztopina, datumcaszacetek, datumcaskonec in masa morajo biti unikatni znotraj zavihka/razdelka.", "Relacijska pravila"),
    ("mass_owner_rule", "Masa mora imeti pripadajočo kemikalijo ali raztopino; ujemanje ključev med kemikalija/raztopina in masa.", "Relacijska pravila"),
    ("repro_kolicina_owner_rule", "Kolicina mora imeti predhodni repro z enakim ključem preverjanja (par repro–kolicina).", "Relacijska pravila"),
    ("time_pair_rule", "Par datumcaszacetek / datumcaskonec: za začetni čas mora obstajati končni in obratno.", "Relacijska pravila"),
    ("key_numbering_rule", "Oštevilčenje ključev (base1, base2, …) brez vrzeli in brez podvajanja 'base' + 'base1'.", "Relacijska pravila"),
    ("tehtnica_masa_pair_rule", "Povezava tehtnica–masa in ustrezne vrednosti.", "Relacijska pravila"),
    ("tehtnica_vrednost_from_formula_rule", "Vrednost pri tehtnici (masa >= 10 ali < 10) glede na kontekst.", "Relacijska pravila"),
    # Control
    ("unknown_controls_rule", "Ime kontrole mora biti med dovoljenimi (kontrolaPraznoPolje, kontrolaIntervala, kontrolaCasa, zaklenipolja, itd.).", "Kontrolna pravila"),
    ("control_context_rule", "Kontrola mora biti v ustreznem kontekstu glede na Tip podatka / Tip objekta (npr. kontrola kemikalije samo pri kemikalija).", "Kontrolna pravila"),
    ("required_controls_rule", "Obvezna kontrola za prazno polje kjer je potrebna; pri checkboxu, naslovu in črti ne sme biti kontrola praznega polja.", "Kontrolna pravila"),
    ("expected_controls_rule", "Pričakovane kontrole glede na tip (npr. kemikalija: kontrola veljavnosti in ustreznosti; masa: kontrola mase, interval, razlika).", "Kontrolna pravila"),
    ("zakleni_param_rule", "Parametri za zaklenipolja: Param1 = koraki z aliObstajaPogoj; za checkbox obvezna kontrola praznega polja (ali obratno glede na konfiguracijo).", "Kontrolna pravila"),
    ("aliobstajapogoj_combo_rule", "Pravilna kombinacija aliObstajaPogoj (Param1 = ključi, Param2 = 0/1) in vrednost polja, ko je pogoj izpolnjen.", "Kontrolna pravila"),
    ("zaklenipolja_unique_key_rule", "Pri zaklenipolja ne sme biti podvojenega ključa preverjanja.", "Kontrolna pravila"),
    ("zakleni_inverse_rule", "Za korake iz Param1 pri zaklenipolja mora obstajati kontrola aliObstajaPogoj z ustreznimi Param1/Param2.", "Kontrolna pravila"),
    ("zakleni_checkbox_rule", "Pri checkboxu in zaklenipolja: dovoljena/zahtevana kontrola praznega polja glede na konfiguracijo.", "Kontrolna pravila"),
    ("aliobkljukan_param_rule", "aliObkljukan zahteva Param1 'DA' ali 'NE'.", "Kontrolna pravila"),
    ("kontrola_interval_param_rule", "Kontrola intervala: Param1/Param2 morata biti številčni in v mejah iz Navodila (obseg ali ±).", "Kontrolna pravila"),
    ("kontrola_interval_advanced_rule", "Strožje preverjanje intervalov (meje, enote, decimalna mesta).", "Kontrolna pravila"),
    ("kontrola_casa_rule", "Kontrola časa: min/max vrednosti, ujemanje z Navodilom (ure, minute, dnevi).", "Kontrolna pravila"),
    # SOP
    ("sop_compliance_rule", "Preverjanje skladnosti recepture s SOP-om: IPO šifre, dovoljene vrste, volumni, pretoki, zahtevani elementi.", "SOP skladnost"),
]

ALLOWED_CONTROLS = [
    "kontrolapraznopolje", "kontrolaintervala", "kontrolainterval", "kontrolacasa",
    "aliobstajapogoj", "aliobstajapogoj_ali", "aliobkljukan", "aliniobkljukan",
    "kdoizpolni", "alipravavloga", "alipravavlogakoda", "zaklenipolja",
    "kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije",
    "kontrolamase", "kontrolarazmerjakemikalij", "kontrolaembalaze", "kontrolaprazneembalaze",
    "kontrolaveljavnostiopreme", "kontrolaustreznostiopreme", "kontrolaustreznostiopremeizmase",
    "kontrolaveljavnostimonolita", "kontrolaustreznostimonolita",
    "kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine",
    "kontrolaveljavnostirepro", "kontrolaustreznostirepro", "kontrolaprimernostirepro",
    "kontrolaprimernostitelesainpokrova", "prenosrepro", "prenosset",
    "kontrolarazlika", "aliisto", "kontrolaistizapis",
    "kontrolaustreznostimonomerne", "kontrolaveljavnostimonomerne",
    "kontrolaustreznostiseta", "kontrolaveljavnostiseta", "kontrolaustreznostilinije", "odpispraznemm",
]


def main():
    out_dir = Path(__file__).resolve().parent.parent
    out_path = out_dir / "Pravila_validatorja.docx"

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Naslov
    title = doc.add_heading("Pravila validatorja MES (recepture Excel)", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(
        "Dokument vsebuje seznam vseh vgrajenih pravil, ki jih validator preverja pri validaciji Excel receptur."
    )
    doc.add_paragraph()

    # Pregled po kategorijah
    doc.add_heading("1. Pregled pravil po kategorijah", level=1)
    current_module = None
    for name, desc, mod in RULES:
        if mod != current_module:
            current_module = mod
            doc.add_heading(current_module, level=2)
        p = doc.add_paragraph()
        p.add_run(f"{name}").bold = True
        p.add_run(f" — {desc}")
    doc.add_paragraph()

    # Številčenje
    doc.add_heading("2. Seznam vseh pravil (zaporedno)", level=1)
    for i, (name, desc, _) in enumerate(RULES, 1):
        p = doc.add_paragraph()
        p.add_run(f"{i}. {name}").bold = True
        p.add_run(f": {desc}")
    doc.add_paragraph()

    # Dovoljene kontrole
    doc.add_heading("3. Dovoljene kontrole (Kontrola N)", level=1)
    doc.add_paragraph(
        "Imena kontrole v stolpcih »Kontrola N« morajo biti ena od naslednjih (neobčutljivo na velikost in presledke):"
    )
    for c in ALLOWED_CONTROLS:
        doc.add_paragraph(c, style="List Bullet")
    doc.add_paragraph()

    # Kode napak
    doc.add_heading("4. Kode napak (izbor)", level=1)
    doc.add_paragraph(
        "Validator poroča napake z ustreznimi kodami. V constants.py so definirane vse kode in njihovi slovenski opisi (CODE_TRANSLATIONS)."
    )
    doc.add_paragraph("Primeri: MANJKA_STOLPEC, KORAK_PODVOJEN, KLJUC_NAPAKEN_FORMAT, TIP_NE_USREZA, KONTROLA_NEZNAN, SOP_IPO_NE_USREZA, itd.")
    doc.add_paragraph()

    doc.add_paragraph("— Konec dokumenta —")
    doc.save(out_path)
    print(f"Dokument shranjen: {out_path}")


if __name__ == "__main__":
    main()
