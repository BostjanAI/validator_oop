#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pretvorba Markdown dokumenta v Word (.docx) s pisavo TT Norms Pro
"""

import re
import argparse
import tempfile
import zipfile
import os
import time
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_border(cell, **kwargs):
    """
    Set cell border
    Usage:
    set_cell_border(
        cell,
        top={"sz": 12, "val": "single", "color": "#000000"},
        bottom={"sz": 12, "val": "single", "color": "#000000"},
        start={"sz": 12, "val": "single", "color": "#000000"},
        end={"sz": 12, "val": "single", "color": "#000000"},
    )
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = OxmlElement(tag)
            for key in ["sz", "val", "color", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))
            tcPr.append(element)

def set_font(run, font_name='TT Norms Pro', size=11):
    """Nastavi pisavo za run"""
    run.font.name = font_name
    run.font.size = Pt(size)
    # Za Windows compatibility
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def parse_markdown_table(lines):
    """Parsira markdown tabelo"""
    if len(lines) < 2:
        return None
    
    # Prva vrstica so headerji
    headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]
    
    # Druga vrstica je separator (preskočimo)
    
    # Ostale vrstice so podatki
    rows = []
    for line in lines[2:]:
        if line.strip():
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)
    
    return headers, rows

def add_table_to_doc(doc, headers, rows, font_name='TT Norms Pro'):
    """Dodaj tabelo v dokument"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Dodaj headerje
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        cell = hdr_cells[i]
        # Odstrani markdown bold oznake
        header_text = header.replace('**', '')
        p = cell.paragraphs[0]
        run = p.add_run(header_text)
        run.bold = True
        set_font(run, font_name=font_name, size=11)
        
        # Obarvan ozadje za header
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), 'D9E1F2')
        cell._element.get_or_add_tcPr().append(shading_elm)
    
    # Dodaj podatke
    for i, row in enumerate(rows):
        row_cells = table.rows[i + 1].cells
        for j, cell_text in enumerate(row):
            cell = row_cells[j]
            # Obdelaj markdown formatting
            cell_text = cell_text.replace('<br>', '\n')
            p = cell.paragraphs[0]
            
            # Parsaj bold tekst
            parts = re.split(r'(\*\*.*?\*\*)', cell_text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                    set_font(run, font_name=font_name, size=10)
                elif part:
                    run = p.add_run(part)
                    set_font(run, font_name=font_name, size=10)
    
    return table

def process_inline_formatting(text):
    """Obdelaj inline markdown formatting (bold, italic, code)"""
    # Nadomesti markdown sintakso
    text = text.replace('`', '"')
    return text

def add_formatted_paragraph(doc, text, style=None, font_name='TT Norms Pro', font_size=11, italic=False):
    """Dodaj odstavek z inline formatiranjem"""
    p = doc.add_paragraph(style=style)
    
    # Parsaj bold tekst
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
            run.italic = italic
            set_font(run, font_name=font_name, size=font_size)
        elif part:
            run = p.add_run(process_inline_formatting(part))
            run.italic = italic
            set_font(run, font_name=font_name, size=font_size)
    
    return p

def markdown_to_docx(
    md_file,
    docx_file,
    font_name='TT Norms Pro',
    author=None,
    last_modified_by=None,
    comments=None,
    title=None,
    subject=None,
    application=None,
):
    """Glavna funkcija za pretvorbo"""
    
    # Preberi markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Ustvari document
    doc = Document()
    
    # Nastavi privzete sloge
    style = doc.styles['Normal']
    font = style.font
    font.name = font_name
    font.size = Pt(11)

    # Nastavi core properties (metapodatki dokumenta)
    cp = doc.core_properties
    if author is not None:
        cp.author = author
    if last_modified_by is not None:
        cp.last_modified_by = last_modified_by
    if comments is not None:
        if comments == "__CLEAR__":
            comments = ""
        cp.comments = comments
    if title is not None:
        cp.title = title
    if subject is not None:
        cp.subject = subject
    
    # Procesiranje vrstic
    i = 0
    in_table = False
    table_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Preskočimo prazne vrstice
        if not line:
            i += 1
            continue
        
        # Horizontalna črta
        if line.strip() == '---':
            doc.add_paragraph()
            i += 1
            continue
        
        # Naslovi
        if line.startswith('#'):
            if in_table:
                # Dodaj tabelo pred naslovom
                if len(table_lines) >= 2:
                    headers, rows = parse_markdown_table(table_lines)
                    if headers and rows:
                        add_table_to_doc(doc, headers, rows)
                in_table = False
                table_lines = []
            
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            
            if level == 1:
                p = doc.add_heading(text, level=1)
                p.runs[0].font.name = font_name
                p.runs[0].font.size = Pt(18)
                p.runs[0].font.color.rgb = RGBColor(31, 78, 120)
            elif level == 2:
                p = doc.add_heading(text, level=2)
                p.runs[0].font.name = font_name
                p.runs[0].font.size = Pt(14)
                p.runs[0].font.color.rgb = RGBColor(31, 78, 120)
            else:
                p = doc.add_heading(text, level=3)
                p.runs[0].font.name = font_name
                p.runs[0].font.size = Pt(12)
            
            i += 1
            continue
        
        # Tabele
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        
        # Konec tabele
        if in_table:
            if len(table_lines) >= 2:
                headers, rows = parse_markdown_table(table_lines)
                if headers and rows:
                    add_table_to_doc(doc, headers, rows, font_name=font_name)
            in_table = False
            table_lines = []
        
        # Blockquote / opombe (npr. > Opomba: ...)
        if line.lstrip().startswith('> '):
            text = line.lstrip()[2:].strip()
            add_formatted_paragraph(doc, text, style=None, font_name=font_name, font_size=10, italic=True)
            i += 1
            continue

        # Bullet listi (tudi zamaknjeni)
        stripped = line.lstrip()
        if stripped.startswith('- '):
            text = stripped[2:].strip()
            add_formatted_paragraph(doc, text, style='List Bullet', font_name=font_name, font_size=11)
            i += 1
            continue
        
        # Navadni odstavki
        add_formatted_paragraph(doc, line, font_name=font_name, font_size=11)
        i += 1
    
    # Dodaj zadnjo tabelo, če obstaja
    if in_table and len(table_lines) >= 2:
        headers, rows = parse_markdown_table(table_lines)
        if headers and rows:
            add_table_to_doc(doc, headers, rows, font_name=font_name)
    
    # Shrani dokument
    if application is None:
        doc.save(docx_file)
    else:
        # Če želimo nastaviti Application, shranimo v začasno datoteko in nato zapišemo končni DOCX brez replace().
        out_dir = os.path.dirname(os.path.abspath(docx_file)) or None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=out_dir) as tmp:
            tmp_docx = tmp.name
        try:
            doc.save(tmp_docx)
            write_docx_with_patched_application(tmp_docx, docx_file, application)
        finally:
            if os.path.exists(tmp_docx):
                try:
                    os.remove(tmp_docx)
                except OSError:
                    pass

    print(f"OK - Dokument uspešno ustvarjen: {docx_file}")


def write_docx_with_patched_application(src_docx_path, dst_docx_path, application_text):
    """
    Prebere obstoječi DOCX (src) in zapiše NOV DOCX (dst),
    kjer docProps/app.xml -> <Application>...</Application> ima želeno vrednost.

    (Windows File Properties -> Details -> Program name)
    """
    app_xml_path = "docProps/app.xml"

    with zipfile.ZipFile(src_docx_path, "r") as zin:
        # Parse existing app.xml
        app_xml = zin.read(app_xml_path)
        root = ET.fromstring(app_xml)
        ns = {"ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}

        app_el = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Application")
        if app_el is None:
            app_el = ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Application")
        app_el.text = application_text

        # Keep AppVersion if present; set to typical Office 16 if missing
        ver_el = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}AppVersion")
        if ver_el is None:
            ver_el = ET.SubElement(root, "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}AppVersion")
        if not (ver_el.text and ver_el.text.strip()):
            ver_el.text = "16.0000"

        # Serialize XML with UTF-8 declaration
        new_app_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True, method="xml")

        # Write destination DOCX without duplicate zip entries
        with zipfile.ZipFile(dst_docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == app_xml_path:
                    data = new_app_xml
                zout.writestr(item, data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pretvori Markdown (.md) v Word (.docx) s pisavo TT Norms Pro.")
    parser.add_argument("--input", required=True, help="Pot do vhodne .md datoteke")
    parser.add_argument("--output", required=True, help="Pot do izhodne .docx datoteke")
    parser.add_argument("--font", default="TT Norms Pro", help="Ime pisave (privzeto: TT Norms Pro)")
    parser.add_argument("--author", default=None, help="Metapodatek: Author (npr. Boštjan Komac)")
    parser.add_argument("--last-modified-by", default=None, help="Metapodatek: Last saved by")
    parser.add_argument("--comments", default=None, help="Metapodatek: Comments (pusti prazno za odstranitev)")
    parser.add_argument("--title", default=None, help="Metapodatek: Title")
    parser.add_argument("--subject", default=None, help="Metapodatek: Subject")
    parser.add_argument("--application", default=None, help="Extended property: Application (Program name), npr. Microsoft Office Word")
    args = parser.parse_args()

    markdown_to_docx(
        args.input,
        args.output,
        font_name=args.font,
        author=args.author,
        last_modified_by=args.last_modified_by,
        comments=args.comments,
        title=args.title,
        subject=args.subject,
        application=args.application,
    )
