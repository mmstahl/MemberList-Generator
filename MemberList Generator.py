import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime

FONT_NAME      = 'Alef'
FONT_NAME_BOLD = 'Alef-Bold'


def _ensure_fonts(fonts_dir):
    """Register Alef fonts if not already registered."""
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME,      os.path.join(fonts_dir, 'Alef-Regular.ttf')))
        pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, os.path.join(fonts_dir, 'Alef-Bold.ttf')))


def format_hebrew(text):
    """Reshape and apply BiDi algorithm for RTL text rendering."""
    if not text or pd.isna(text) or str(text).strip().lower() in ["nan", ""]:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)


def clean_phone(val):
    """Clean phone numbers of NaN or '0' values."""
    if pd.isna(val) or str(val).strip().lower() == "nan" or str(val).strip() == "0":
        return ""
    return str(val).strip()


def generate_pdf(input_path, output_path, fonts_dir):
    """Generate Hebrew member list PDF.

    fonts_dir must contain Alef-Regular.ttf and Alef-Bold.ttf.
    """
    _ensure_fonts(fonts_dir)

    try:
        df = pd.read_csv(input_path, encoding='utf-8-sig')
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find input file: {input_path}")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    elements = []

    # Date stamp (top left)
    current_date = datetime.now().strftime("%d/%m/%Y")
    date_style = ParagraphStyle(
        'DateStyle', fontName=FONT_NAME, fontSize=8, alignment=0, spaceAfter=0
    )
    elements.append(Paragraph(current_date, date_style))

    # Title
    title_style = ParagraphStyle(
        'TitleStyle', fontName=FONT_NAME_BOLD, fontSize=18, alignment=1, spaceAfter=15
    )
    elements.append(Paragraph(format_hebrew("קהילת ידידיה - רשימת חברים - תשפ\"ו"), title_style))

    # Table headers
    table_data = [[
        format_hebrew("טלפון"),
        format_hebrew("אימייל"),
        format_hebrew("שם"),
        ""  # Order column placeholder
    ]]

    line_indices  = []
    family_ranges = []

    for _, row in df.iterrows():
        start_row   = len(table_data)
        address_raw = str(row['home_address']).strip()
        is_reference_row = address_raw.lower() == "skip"

        full_name = f"{row['last_name']} {row['first_name']}"
        order_val = str(row['order']) if not pd.isna(row['order']) else ""

        if is_reference_row:
            table_data.append([
                "",
                format_hebrew(row['user_email']),
                format_hebrew(full_name),
                format_hebrew(order_val)
            ])
        else:
            # Line 1: Main member
            table_data.append([
                clean_phone(row['cellphone1']),
                row['user_email'] if not pd.isna(row['user_email']) else "",
                format_hebrew(full_name),
                format_hebrew(order_val)
            ])

            # Line 2: Partner (if exists)
            p_first = str(row['partnerfirst']).strip()
            if p_first and p_first.lower() != "nan":
                p_full_name = f"{row['partnerlast']} {row['partnerfirst']}"
                table_data.append([
                    clean_phone(row['partnerphone']),
                    row['partneremail'] if not pd.isna(row['partneremail']) else "",
                    format_hebrew(p_full_name),
                    ""
                ])

            # Line 3: Address & home phone
            table_data.append([
                clean_phone(row['homephone']),
                "",
                format_hebrew(address_raw),
                ""
            ])

        end_row = len(table_data) - 1
        line_indices.append(end_row)
        family_ranges.append((start_row, end_row))

    col_widths = [135, 200, 160, 40]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = TableStyle([
        ('FONT',          (0, 0), (-1, -1), FONT_NAME, 10),
        ('ALIGN',         (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ('TOPPADDING',    (0, 0), (-1, -1), 0.5),
        # Header styling
        ('FONT',          (0, 0), (-1, 0),  FONT_NAME_BOLD, 11),
        ('LINEBELOW',     (0, 0), (-1, 0),  1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  4),
    ])

    for start, end in family_ranges:
        ts.add('NOSPLIT', (0, start), (-1, end))

    for idx in line_indices:
        ts.add('LINEBELOW',     (0, idx), (-1, idx), 0.5, colors.grey)
        ts.add('BOTTOMPADDING', (0, idx), (-1, idx), 2)

    table.setStyle(ts)
    elements.append(table)

    doc.build(elements)


if __name__ == "__main__":
    import defaults_manager as dm

    script_dir  = os.path.dirname(os.path.abspath(__file__))
    input_path  = dm.get('members_list', 'processed_csv_path')
    output_path = dm.get('members_list', 'pdf_path')
    generate_pdf(input_path, output_path, fonts_dir=script_dir)
    print(f"Success: {output_path} generated.")
