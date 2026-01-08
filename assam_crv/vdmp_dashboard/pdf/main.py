from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.pagesizes import A4
from datetime import datetime
from reportlab.platypus.tableofcontents import TableOfContents
import os
from django.conf import settings
from io import BytesIO
from reportlab.lib.units import cm
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.lib.units import cm
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Style
from .global_styles import non_toc_heading,blue_heading,list_of_table_heading

from .cover import add_cover_page
from .client_info import draw_client_info_table

from .lists import draw_list_of_figures, draw_list_of_tables, draw_abbreviations
from .abouts import draw_about_this_document
from .village_summary import village_summary   
from .village_profile import draw_village_profile
from .hazard_Vulnerability_risk import draw_hazard_Vulnerability_risk
from .layout import add_common_header_footer
from .Disaster_preparedness_and_response_plan import draw_disaster_preparedness_and_response_plan
from .Mitigation_Intervention_and_Investment_Plan import draw_mitigation_intervention_and_investment_plan
from .PRA_map_and_Field_Photos import draw_PRA_map_and_field_photos



h1 = PS(name='Heading1', fontSize=14, leading=16)
h2 = PS(name='Heading2', fontSize=12, leading=14, leftIndent=10)

from reportlab.platypus.flowables import Flowable

class ListOfTablesPlaceholder(Flowable):
    def __init__(self):
        super().__init__()

    def draw(self):
        pass  # It's just a placeholder

class ListOfFiguresPlaceholder(Flowable):
    def __init__(self):
        super().__init__()

    def draw(self):
        pass  # It's just a placeholder
 
class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, village=None, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
       
        self.allowSplitting = 1
        self.figure_list = []  # Stores (title, page_number)
        self.table_list = []   # Stores (title, page_number)
        self.village = village or "RUPAKUCHI"
        # Add page templates
        self.addPageTemplates([
            PageTemplate(id='Cover', frames=[Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm)], onPage=self.cover_page),
            PageTemplate(id='Normal', frames=[Frame(3*cm, 2.5*cm, 15*cm, 25*cm)], onPage=self.normal_page),
            PageTemplate(id='Last', frames=[Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm)], onPage=self.last_page)
        ])
   
    def cover_page(self, canvas, doc):
        """First page only"""
        image_path = os.path.join(settings.BASE_DIR, "static", "images", "dd.jpg")
        add_cover_page([], canvas, image_path, "VILLAGE", self.village)
        doc.pageTemplate = self.pageTemplates[1]  # Switch to normal template
   
    def normal_page(self, canvas, doc):
        """All content pages except last"""
        canvas.saveState()
        if doc.page >= 3:  # Start from 3rd page (after cover and TOC)
            add_common_header_footer(canvas, doc,self.village)
        canvas.restoreState()
   
    def last_page(self, canvas, doc):
        """Last page only"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(2.5*cm, 28*cm, f"Page {doc.page}")
        canvas.setFont('Helvetica', 10)
        canvas.drawString(2.5*cm, 2*cm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.restoreState()
   
    def afterFlowable(self, flowable):
        """Register TOC entries and add destinations for linking"""
        if isinstance(flowable, Paragraph):
            text = flowable.getPlainText()
            style = flowable.style.name
           
            # Standard heading styles
            if style == 'Heading1':
                key = f'h1_{hash(text)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
            elif style == 'Heading2':
                key = f'h2_{hash(text)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (1, text, self.page, key))
            
            # Add any other styles you want in TOC here
            # elif style == 'UserLineHeading':
            #     key = f'h1_{hash(text)}'
            #     self.canv.bookmarkPage(key)
            #     self.notify('TOCEntry', (0, text, self.page, key))
                
            # Heading1 and its variants
            elif style in ['Heading1','ListofTableHeading','BlueHeading']:
                key = f'h1_{hash(text)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
            
            # Heading2 and its variants
            elif style in ['Heading2', 'BlueSubHeading']:
                key = f'h2_{hash(text)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (1, text, self.page, key))
                
              # Heading2 and its variants
            elif style in ['Heading2', 'BlueLevel3Heading']:
                key = f'h2_{hash(text)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (2, text, self.page, key))
                
            # Handle table titles
            if style in ['table_sub_title','TableTitle']:
                key = f'h2_{hash(text)}'
                self.canv.bookmarkPage(key)
                # Add to table_list only if title is not already added
                if not any(entry['title'] == text for entry in self.table_list):
                    self.table_list.append({'title': text, 'page': self.page})
                    # print(f"Added table to list: {style} on page {self.page}------{text}")
            
            # Handle figure titles - add these style names based on your figure caption styles
            if style in ['image_title', 'ImageTitle', 'FigureCaption']:
                key = f'h2_{hash(text)}'
                self.canv.bookmarkPage(key)
                # Add to figure_list only if title is not already added
                if not any(entry['title'] == text for entry in self.figure_list):
                    self.figure_list.append({'title': text, 'page': self.page})
                    # print(f"Added figure to list: {style} on page {self.page}------{text}")
                
def generate_pdf(village_id=None, village=None):
    buffer = BytesIO()
   
    # Define styles with explicit names
    styles = {
        'Heading1': ParagraphStyle(name='Heading1', fontSize=14, ),
        'Heading2': ParagraphStyle(name='Heading2', fontSize=12, leftIndent=10),
        'TOCHeading1': ParagraphStyle(name='TOCHeading1', fontSize=12, textColor=HexColor('#0066CC'), fontName='Helvetica-Bold',leftIndent=10),
        'TOCHeading2': ParagraphStyle(name='TOCHeading2', fontSize=10, textColor=HexColor('#0066CC'), leftIndent=15),
        'TOCHeading3': ParagraphStyle(name='TOCHeading2', fontSize=10, textColor=HexColor('#0066CC'), leftIndent=20)
    }
 
    # Create document
    doc = MyDocTemplate(buffer, village=village, pagesize=A4)
   
    # Configure TOC
    toc = TableOfContents()
    toc.levelStyles = [styles['TOCHeading1'], styles['TOCHeading2'],styles['TOCHeading3']]
   
    # FIRST PASS: Build document to collect table and figure information
    elements = []
    draw_client_info_table(elements)
   
    # Add TOC section
    elements.append(Paragraph("Table of Contents", list_of_table_heading))
    elements.append(toc)
    elements.append(PageBreak())
   
    # Placeholder for List of Figures (will be replaced in second pass)
    elements.append(Paragraph("<b>List of Figures</b>", list_of_table_heading))
    elements.append(Spacer(1, 12))
    elements.append(ListOfFiguresPlaceholder())
    elements.append(PageBreak())
    
    # Placeholder for List of Tables (will be replaced in second pass)
    elements.append(Paragraph("<b>List of Tables</b>", list_of_table_heading))
    elements.append(Spacer(1, 12))
    elements.append(ListOfTablesPlaceholder())
    elements.append(PageBreak())
    
    draw_abbreviations(elements)
   
    draw_about_this_document(elements)
   
    village_summary(elements,village_id)
   
    # draw_village_profile(elements,village_id)
    # elements.append(PageBreak())
    # draw_hazard_Vulnerability_risk(elements,village_id)
    # elements.append(PageBreak())
    # draw_disaster_preparedness_and_response_plan(elements, village_id)
    # elements.append(PageBreak())
    # draw_mitigation_intervention_and_investment_plan(elements, village_id)
    # elements.append(PageBreak())
    # draw_PRA_map_and_field_photos(elements, village_id)
    
    # Build first time to populate figure_list and table_list
    doc.multiBuild(elements)
    
    # SECOND PASS: Now rebuild with actual lists
    elements = []
    draw_client_info_table(elements)
   
    # Add TOC section
    elements.append(Paragraph("Table of Contents", list_of_table_heading))
    elements.append(toc)
    elements.append(PageBreak())
   
    # Now add the actual list of figures using the populated doc.figure_list
    draw_list_of_figures(elements, doc)  # Pass the doc to access figure_list
    elements.append(PageBreak())
    
    # Now add the actual list of tables using the populated doc.table_list
    draw_list_of_tables(elements, doc)  # Pass the doc to access table_list
    elements.append(PageBreak())
    
    draw_abbreviations(elements)
    
    draw_about_this_document(elements)
    
    village_summary(elements,village_id)
    # draw_village_profile(elements,village_id)
    # elements.append(PageBreak())
    # draw_hazard_Vulnerability_risk(elements,village_id)
    # elements.append(PageBreak())
    # draw_disaster_preparedness_and_response_plan(elements, village_id)
    # elements.append(PageBreak())
    # draw_mitigation_intervention_and_investment_plan(elements, village_id)
    # elements.append(PageBreak())
    # draw_PRA_map_and_field_photos(elements, village_id)
    
    # Final build with complete lists
    doc.multiBuild(elements)
    
    buffer.seek(0)
    return buffer