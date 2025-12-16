from reportlab.platypus import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import red,white
import os
from datetime import datetime
from reportlab.lib.colors import HexColor
from django.conf import settings


#   add_cover_page([], canvas, image_path, "Village", village_obj)
def add_cover_page(arr, c, image_path, village, village_obj):
    # Full-page background image
    page_width, page_height = c._pagesize
    image_path = os.path.join(settings.BASE_DIR, "static", "images", "reportCoverPage.jpg")
    c.drawImage(image_path, 0, 0, width=page_width, height=page_height)

    # Set font and color
    c.setFont("Helvetica-Bold", 21)
    c.setFillColor(white)

    # Dynamic label (like VDMP)
    c.drawRightString(page_width - 1.3 * inch, page_height - 6 * inch, "VDMP")

    # Dynamic field (like Village: RUPAKUCHI)
    if village_obj and hasattr(village_obj, 'name'):
        dynamic_label = f"{village}: {village_obj.name.upper()}"
    else:
        dynamic_label = f"{village}: Village"
    c.drawRightString(page_width - 0.2 * inch, page_height - 6.4 * inch, dynamic_label)

    # Dynamic month and year
    month_year = datetime.now().strftime("%B %Y")
    c.setFillColor(HexColor("#B8860B"))
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(page_width - 1 * inch, page_height - 7 * inch, month_year)

    # Footer with village name and district
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#000000"))
    if village_obj and hasattr(village_obj, 'name') and hasattr(village_obj, 'gram_panchayat'):
        footer_text = f"{village_obj.name}, {village_obj.gram_panchayat.circle.district.name}"
    else:
        footer_text = "Village, District"
    c.drawString(0.5 * inch, 0.5 * inch, footer_text)

    # Force page break
    c.showPage()

