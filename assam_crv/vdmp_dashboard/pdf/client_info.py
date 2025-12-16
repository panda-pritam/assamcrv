from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from .global_styles import tb_header_bg,tb_border_color,tb_border_width

def draw_client_info_table(elements):
    styles = getSampleStyleSheet()

    # Remove italic + align left manually
    heading_style = ParagraphStyle(
        name="CleanHeading4",
        parent=styles['Heading4'],
        alignment=0,  # Left align
         leftIndent=-45,   
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceAfter=12,
        italic=False
    )

    normal = styles['Normal']
    bold = ParagraphStyle(
    name="BoldCentered",
    parent=normal,
    fontName="Helvetica-Bold",
    # alignment=1  # Center
)

    # ✅ More readable as list of lists
    data = [
        [Paragraph('<b>Client Information</b>', bold), ''],  # Row 0 (merged header)
        ['Client Address', 'Assam State Disaster Management Authority, Assam'],
        ['Contact details', 'CEO, ASDMA, Assam'],
        ['RMSI Contact', Paragraph('Dr. Muralikrishna M (Team Leader)<br/>Muralikrishna.M@rmsi.com<br/>info@rmsi.com', normal)],
        [Paragraph('<b>Company Information</b>', bold), ''],  # Row 4 (merged header)
        ['Name', 'RMSI Private Limited'],
        ['CIN', 'U74899DL1992PTC047149'],
        ['Registered Office Address', Paragraph('RMSI Private Limited - 50/9, 1st Floor, Tolstoy Lane, Janpath, New Delhi, India – 110001', normal)],
        ['Corporate Office Address', Paragraph(
            'A-8, Sector-16<br/>NOIDA, 201 301, India<br/>Tel: +91 120 251 1102, 251 2101<br/>Fax: +91 120 251 1109, 251 0963<br/>E-mail: info@rmsi.com',
            normal
        )],
    ]

    table = Table(data, colWidths=[2.5 * inch, 4.5 * inch])
    table.setStyle(TableStyle([
        # === Merged header rows ===
        ('SPAN', (0, 0), (1, 0)),  # Merge first row (Client Info)
        ('SPAN', (0, 4), (1, 4)),  # Merge fifth row (Company Info)

        # === Background color for section headers ===
        ('BACKGROUND', (0, 0), (-1, 0), tb_header_bg),  # Client Info
        ('BACKGROUND', (0, 4), (-1, 4), tb_header_bg),  # Company Info
        # ✅ Center align text for both section headers
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
    ('ALIGN', (0, 4), (-1, 4), 'CENTER'),
    ('VALIGN', (0, 4), (-1, 4), 'MIDDLE'),

        # === Border for all cells ===
        
        ('GRID', (0, 0), (-1, -1), tb_border_width, tb_border_color),

        # === Text & cell formatting ===
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))

    # === Add elements ===
    elements.append(Paragraph("For the kind attention of:", heading_style))  # Clean heading
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(table)
    elements.append(PageBreak())  # Next page (e.g., TOC or section)
