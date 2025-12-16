from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from django.conf import settings

def add_common_header_footer(canvas, doc,data=None):
    """Adds common header and footer to content pages"""
    canvas.saveState()
    width, height = A4
   
    # === Header ===
    # Left Header Text
    header_text = "Socio Technical Agency (STA) Climate Resilient Village (CRV), Assam"
    canvas.drawString(inch * 0.5, height - 0.5 * inch, header_text)
 
    # Right-side logo
     #Right Header Image (adjust path)
    image_path = os.path.join(settings.BASE_DIR, "static", "images", "AIRBMP_logo.jpg")  # use your logo image path
    if os.path.exists(image_path):
        image_width = 60
        image_height = 30
        canvas.drawImage(image_path, width - 1.5 * inch, height - 0.6 * inch, width=image_width, height=image_height)
 
    # === Footer ===
    width = doc.pagesize[0]
    canvas.setStrokeColor(colors.grey)
    canvas.setLineWidth(0.5)
    canvas.line(inch * 0.75, inch * 0.55, width - inch * 0.75, inch * 0.55)
 
    canvas.setFont("Helvetica", 9)
    if data and hasattr(data, 'name') and hasattr(data, 'gram_panchayat'):
        footer_text = f"VDMP: {data.name}, {data.gram_panchayat.circle.district.name}"
    else:
        footer_text = "VDMP: Village, District"
    canvas.drawString(inch * 0.75, inch * 0.35, footer_text)
   
    # Page number
    page_num = f"Page {doc.page}"
    canvas.drawRightString(width - inch * 0.75, inch * 0.35, page_num)
 
    canvas.restoreState()
