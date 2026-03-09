import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime # Added for the date

# --- CONFIGURATION ---michael.stahl@testprincipia.com
FONT_NAME = 'Alef'
FONT_NAME_BOLD = 'Alef-Bold'
FONT_FILE = 'Alef-Regular.ttf' 
FONT_FILE_BOLD = 'Alef-Bold.ttf' 
INPUT_FILE = 'pre-processing output.csv'
OUTPUT_FILE = 'members_list_2026.pdf'

# Register fonts
pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_FILE_BOLD))

def format_hebrew(text):
    """Reshapes and applies BiDi algorithm for RTL text rendering."""
    if not text or pd.isna(text) or str(text).strip().lower() in ["nan", ""]:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

def clean_phone(val):
    """Cleans phone numbers of NaN or '0' values."""
    if pd.isna(val) or str(val).strip().lower() == "nan" or str(val).strip() == "0":
        return ""
    return str(val).strip()

def generate_community_directory():
    try:
        # utf-8-sig handles the Byte Order Mark from the CSV
        df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}")
        return

    doc = SimpleDocTemplate(
        OUTPUT_FILE, 
        pagesize=A4, 
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    
    elements = []

    # --- NEW: DATE STAMP (TOP LEFT) ---
    current_date = datetime.now().strftime("%d/%m/%Y")
    date_style = ParagraphStyle(
        'DateStyle', 
        fontName=FONT_NAME, 
        fontSize=8, 
        alignment=0, # Left alignment
        spaceAfter=0
    )
    elements.append(Paragraph(current_date, date_style))
    
    # 1. TITLE
    title_style = ParagraphStyle(
        'TitleStyle', fontName=FONT_NAME_BOLD, fontSize=18, alignment=1, spaceAfter=15
    )
    elements.append(Paragraph(format_hebrew("קהילת ידידיה - רשימת חברים - תשפ\"ו"), title_style))

    # 2. TABLE HEADERS (טלפון, אימייל, שם)
    table_data = [[
        format_hebrew("טלפון"),
        format_hebrew("אימייל"),
        format_hebrew("שם"),
        "" # Order column placeholder
    ]]
    
    line_indices = []
    family_ranges = []

    for _, row in df.iterrows():
        start_row = len(table_data)
        
        # Identify Row Type
        address_raw = str(row['home_address']).strip()
        is_reference_row = address_raw.lower() == "skip"
        
        full_name = f"{row['last_name']} {row['first_name']}"
        order_val = str(row['order']) if not pd.isna(row['order']) else ""

        if is_reference_row:
            # --- REFERENCE ROW: Single Line Only ---
            table_data.append([
                "", # No phone number
                format_hebrew(row['user_email']), # Render Hebrew "-ראה-" correctly RTL
                format_hebrew(full_name), 
                format_hebrew(order_val) 
            ])
        else:
            # --- STANDARD BLOCK: Multi-Line ---
            # Line 1: Main Member
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

            # Line 3: Address & Home Phone
            table_data.append([
                clean_phone(row['homephone']), 
                "", 
                format_hebrew(address_raw), 
                ""
            ])

        # Track indices for Styling
        end_row = len(table_data) - 1
        line_indices.append(end_row)
        family_ranges.append((start_row, end_row))

    # 3. CREATE TABLE
    col_widths = [135, 200, 160, 40]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    ts = TableStyle([
        ('FONT', (0, 0), (-1, -1), FONT_NAME, 10),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
        
        # Header Styling
        ('FONT', (0, 0), (-1, 0), FONT_NAME_BOLD, 11),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
    ])

    # Keep family blocks together on pages
    for start, end in family_ranges:
        ts.add('NOSPLIT', (0, start), (-1, end))

    # Add separator lines after each family or reference unit
    for idx in line_indices:
        ts.add('LINEBELOW', (0, idx), (-1, idx), 0.5, colors.grey) # Light grey for cleaner look
        ts.add('BOTTOMPADDING', (0, idx), (-1, idx), 2)

    table.setStyle(ts)
    elements.append(table)
    
    # 4. BUILD PDF
    doc.build(elements)
    print(f"Success: {OUTPUT_FILE} generated.")

if __name__ == "__main__":
    generate_community_directory()