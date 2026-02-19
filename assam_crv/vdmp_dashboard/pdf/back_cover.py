from reportlab.lib.units import inch
import os
from django.conf import settings


def add_back_cover_page(c):
    page_width, page_height = c._pagesize
    image_path = os.path.join(settings.BASE_DIR, "static", "images", "VDMP_back_cover_page.jpg")
    c.drawImage(image_path, 0, 0, width=page_width, height=page_height)
    c.showPage()


def back_cover_page(self, canvas, doc):
    page_width, page_height = canvas._pagesize
    image_path = os.path.join(settings.BASE_DIR, "static", "images", "VDMP_back_cover_page.jpg")
    
    # Debug: print to console to confirm path
    print(f"Back cover image path: {image_path}")
    print(f"Image exists: {os.path.exists(image_path)}")
    
    if os.path.exists(image_path):
        canvas.drawImage(
            image_path, 0, 0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=False,
            mask='auto'
        )
    else:
        # Fallback: red background so you can see the page IS being created
        canvas.setFillColorRGB(1, 0, 0)
        canvas.rect(0, 0, page_width, page_height, fill=1)