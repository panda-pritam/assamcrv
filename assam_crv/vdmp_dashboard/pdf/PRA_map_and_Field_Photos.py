from reportlab.platypus import Paragraph, Spacer,  ListFlowable, ListItem, Image
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

import os
from .global_styles import  blue_heading,table_sub_title,blue_sub_heading,image_title,notes_style,tb_header_bg,Legend_heading,indented_style,bold_style,normal_style,srNoStyle,non_toc_heading,blue_level3_heading,non_indented_style
from .utils.table import create_styled_table
# from .utils.geoserverLayerImage import get_geoserver_image_path, get_geoserver_legend_path
from task_force.models import *
from village_profile.models import tblVillage
from .dummy_data import getFacilityAccessData
from django.db.models import Sum, Count
import requests
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from field_images.models import FieldImage
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
page_width, page_height = A4
max_width = page_width - 2*inch   # leave 1 inch margin left/right
max_height = page_height - 3*inch  # leave space for header/footer

# max_height = page_height * 0.4  # leave space for header/footer

# http://127.0.0.1:8000/en/administrator/field_images

def get_scaled_image(img_path):
    # get original size
    with PILImage.open(img_path) as im:
        iw, ih = im.size  

    aspect = ih / float(iw)

    # fit to max width
    width = min(max_width, iw)
    height = width * aspect

    # if still too tall, scale by height
    if height > max_height:
        height = max_height
        width = height / aspect

    return Image(img_path, width=width, height=height)


def draw_PRA_map_and_field_photos(elements,village_id):
    """
    Generate PRA map and field photos section for the report
    """
    # Main heading
    heading = Paragraph("<a name='draw_PRA_map_and_field_photos'/><b>7	PRA map and Field Photos </b>", blue_heading)
    elements.append(heading)
    elements.append(Spacer(1, 12))
    
    # Define the sections mapping
    sections_map = {
        'PRA Map': {
            'heading': "PRA Map",
            'DB_field': "PRA Map"
        },
        'PRA and field consultations': {
            'heading': "Field photographs – PRA and field consultations",
            'DB_field': "PRA and field consultations"
        },
        'housing': {
            'heading': "Field photographs – housing",
            'DB_field': "housing"
        },
        "Infrastructure": {
            'heading': "Field photographs – Infrastructure",
            'DB_field': 'Infrastructure'
        },
        "River bank protection/erosion": {
            'heading': "Field photographs – River bank protection/erosion",
            'DB_field': 'River bank protection/erosion'
        },
        "Educational facilities": {
            'heading': "Field photographs – Educational facilities",
            'DB_field': 'Educational facilities'
        },
        "Livelihood": {
            'heading': "Field photographs – Livelihood",
            'DB_field': 'Livelihood'
        }
    }
    
    # Counter for sub-section numbering
    sub_section_counter = 1
    
    # Iterate through each section
    for key, section_info in sections_map.items():
        try:
            # Check if images exist for this category and village
            field_images = FieldImage.objects.filter(
                village_id=village_id,
                category=section_info['DB_field']
            ).order_by('upload_datetime')
            
            if field_images.exists():
                # Add sub-section heading
                sub_heading = Paragraph(
                    f"<b>7.{sub_section_counter} {section_info['heading']}</b>", 
                    blue_sub_heading
                )
                elements.append(sub_heading)
                elements.append(Spacer(1, 8))
                
                # Get images (max 2 per category)
                images = list(field_images[:2])
                
                # Process all images (1 or 2) - display them one below the other
                for img_obj in images:
                    try:
                        # Calculate 80% of page width (letter size is 8.5 inches, so 80% ≈ 6.8 inches)
                        img_width = 2*inch
                        
                        # Create image with 80% page width, maintain aspect ratio
                        # img = Image(img_obj.image.path, width=500)
                        img = get_scaled_image(img_obj.image.path)
                        img.hAlign = 'CENTER'
                        elements.append(img)
                        
                        # Add image caption if name exists
                        if img_obj.name:
                            caption = Paragraph(f"<i>{img_obj.name}</i>", image_title)
                            caption.alignment = 1  # Center alignment
                            elements.append(caption)
                        
                        # Add spacing between images
                        elements.append(Spacer(1, 8))
                            
                    except Exception as e:
                        error_text = Paragraph(f"Error loading image: {str(e)}", normal_style)
                        elements.append(error_text)
                        elements.append(Spacer(1, 8))
                
                elements.append(Spacer(1, 12))
                sub_section_counter += 1
                
        except Exception as e:
            # Log error but continue with next section
            print(f"Error processing section {key}: {str(e)}")
            continue
    
    # If no sections were added, add a note
    if sub_section_counter == 1:
        no_data_text = Paragraph(
            "No field photographs or PRA maps are available for this village.", 
            normal_style
        )
        elements.append(no_data_text)
        elements.append(Spacer(1, 12))