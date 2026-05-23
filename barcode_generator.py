# ─────────────────────────────────────────────
#  barcode_generator.py
#  Generates EAN-13 barcodes for all products
#  and saves them as a printable PDF
#
#  Install:
#    pip install python-barcode reportlab pillow --break-system-packages
#
#  Usage:
#    python3 barcode_generator.py
#    → Output: barcodes/barcode_sheet.pdf
# ─────────────────────────────────────────────

import os
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from PIL import Image as PILImage
from database import products

# ── Settings ─────────────────────────────────
OUTPUT_DIR   = "barcodes"
PDF_OUTPUT   = os.path.join(OUTPUT_DIR, "barcode_sheet.pdf")
COLS         = 3      # Barcodes per row
IMG_W        = 5.5    # cm — barcode image width
IMG_H        = 2.8    # cm — barcode image height

# ─────────────────────────────────────────────
def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[DIR] Output folder: {OUTPUT_DIR}/")

def pad_to_ean13(code):
    """
    Pad or trim a barcode string to 12 digits
    (EAN-13 checksum is auto-calculated).
    """
    digits = ''.join(filter(str.isdigit, code))
    digits = digits[:12].ljust(12, '0')
    return digits

def generate_barcode_image(barcode_num, product_name):
    """
    Generate a single EAN-13 barcode PNG image.
    Returns the file path.
    """
    padded   = pad_to_ean13(barcode_num)
    filename = os.path.join(OUTPUT_DIR, f"barcode_{padded}")

    try:
        ean = barcode.get('ean13', padded, writer=ImageWriter())
        saved = ean.save(filename, options={
            "module_width" : 0.25,
            "module_height": 12.0,
            "font_size"    : 8,
            "text_distance": 3.5,
            "quiet_zone"   : 4.0,
            "write_text"   : True,
            "background"   : "white",
            "foreground"   : "black",
        })
        return saved   # returns path with .png extension
    except Exception as e:
        print(f"[ERROR] Could not generate barcode for {barcode_num}: {e}")
        return None

def generate_all_barcodes():
    """Generate PNG images for all products in database."""
    print("\n[STEP 1] Generating barcode images...")
    image_map = {}   # barcode_num → image_path

    for barcode_num, info in products.items():
        path = generate_barcode_image(barcode_num, info['name'])
        if path:
            image_map[barcode_num] = path
            print(f"  ✅  {info['name']:<28} → {os.path.basename(path)}")
        else:
            print(f"  ❌  {info['name']} — skipped")

    print(f"\n  Generated {len(image_map)} barcode images")
    return image_map

def build_pdf(image_map):
    """
    Assemble all barcodes into a clean printable PDF sheet.
    Layout: 3 columns, product name + price + barcode per cell.
    """
    print("\n[STEP 2] Building PDF barcode sheet...")

    doc = SimpleDocTemplate(
        PDF_OUTPUT,
        pagesize    = A4,
        leftMargin  = 1.5 * cm,
        rightMargin = 1.5 * cm,
        topMargin   = 1.5 * cm,
        bottomMargin= 1.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent   = styles['Normal'],
        fontSize = 18,
        fontName = 'Helvetica-Bold',
        alignment= TA_CENTER,
        spaceAfter= 4,
        textColor= colors.HexColor('#1e1e2e'),
    )
    sub_style = ParagraphStyle(
        'Sub',
        parent   = styles['Normal'],
        fontSize = 9,
        fontName = 'Helvetica',
        alignment= TA_CENTER,
        textColor= colors.HexColor('#888888'),
        spaceAfter= 14,
    )
    name_style = ParagraphStyle(
        'Name',
        parent   = styles['Normal'],
        fontSize = 9,
        fontName = 'Helvetica-Bold',
        alignment= TA_CENTER,
        textColor= colors.HexColor('#1e1e2e'),
    )
    price_style = ParagraphStyle(
        'Price',
        parent   = styles['Normal'],
        fontSize = 9,
        fontName = 'Helvetica',
        alignment= TA_CENTER,
        textColor= colors.HexColor('#2d7a2d'),
        spaceAfter= 4,
    )

    story = []

    # ── Title ─────────────────────────────────
    story.append(Paragraph("🛒 Smart Cart — Product Barcode Sheet", title_style))
    story.append(Paragraph(
        f"Print and attach these barcodes to your products | {len(products)} products",
        sub_style))

    # ── Build table cells ─────────────────────
    all_items  = list(products.items())
    table_data = []
    row        = []

    for i, (barcode_num, info) in enumerate(all_items):
        img_path = image_map.get(barcode_num)

        # Product name
        name_para  = Paragraph(info['name'], name_style)
        # Price
        price_para = Paragraph(f"${info['price']:.2f}", price_style)
        # Barcode number
        code_para  = Paragraph(
            f"<font size='7' color='#888888'>{barcode_num}</font>",
            ParagraphStyle('Code', parent=styles['Normal'],
                           alignment=TA_CENTER))

        if img_path and os.path.exists(img_path):
            bc_img = Image(img_path,
                           width  = IMG_W * cm,
                           height = IMG_H * cm)
        else:
            bc_img = Paragraph(
                "<font color='red'>Image Error</font>",
                ParagraphStyle('Err', parent=styles['Normal'],
                               alignment=TA_CENTER))

        # Cell content
        cell = [name_para, price_para, bc_img, code_para]
        row.append(cell)

        if len(row) == COLS or i == len(all_items) - 1:
            # Pad last row with empty cells
            while len(row) < COLS:
                row.append([''])
            table_data.append(row)
            row = []

    # ── Table Layout ──────────────────────────
    col_w = (A4[0] - 3 * cm) / COLS

    table = Table(table_data,
                  colWidths  = [col_w] * COLS,
                  repeatRows = 0)

    table.setStyle(TableStyle([
        # Cell padding
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        # Alignment
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        # Borders
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        # Row backgrounds
        ('ROWBACKGROUNDS',(0,0), (-1,-1),
            [colors.HexColor('#f9f9f9'), colors.white]),
    ]))

    story.append(table)

    # ── Footer note ───────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Cut out each barcode and stick it to the matching product. "
        "The Smart Cart camera will scan these automatically.",
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=8, alignment=TA_CENTER,
                       textColor=colors.HexColor('#aaaaaa'))))

    doc.build(story)
    print(f"\n  ✅  PDF saved: {PDF_OUTPUT}")

def main():
    print("=" * 52)
    print("   🏷️   Smart Cart Barcode Generator")
    print("=" * 52)

    ensure_output_dir()
    image_map = generate_all_barcodes()

    if not image_map:
        print("\n[ERROR] No barcodes generated. Check database.py")
        return

    build_pdf(image_map)

    print("\n" + "=" * 52)
    print("   ✅  Done!")
    print(f"   📄  Open: {PDF_OUTPUT}")
    print("   🖨️   Print and attach to products")
    print("=" * 52)

if __name__ == "__main__":
    main()
