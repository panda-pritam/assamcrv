from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from .global_styles import blue_heading,body_style


def draw_about_this_document(elements):
    styles = getSampleStyleSheet()

    

    # Add heading
    heading = Paragraph("<a name='about_document'/>1  About this Document", blue_heading)
    
    elements.append(heading)
    elements.append(Spacer(1, 12))

    # Add paragraphs
    para1 = """
    The Government of Assam, through the Assam State Disaster Management Authority (ASDMA), is implementing the Assam Integrated River Basin Management Program (AIRBMP). The Program supports improved Integrated Water Resources Management (IWRM) for the economic growth and prosperity of the State, together with addressing flood and river erosion risks. One of the components of this project is to develop Village Disaster Mitigation Plans (VDMPs) for 50 villages selected across 7 districts, which are prone to frequent flooding and erosion. The identified districts are (1) Barpeta, (2) Bajali, (3) Sonitpur, (4) Biswanath, (5) Golaghat, (6) Majuli, and (7) Lakhimpur. This activity comes under Phase I of the Program. ASDMA has hired RMSI Private Limited as the Socio-Technical Agency (STA) to implement this project.
    """
    para2 = """
    The development of a village-level Village Disaster Mitigation Plan (VDMP) is one of the key deliverables of this assignment. This document presents the VDMP for Rupakuchi village in Barpeta District. The plan has been developed through a multi-step process, including field surveys, community consultations, consultations with line department officials, and the use of GIS and remote sensing technologies.
    """

    elements.append(Paragraph(para1.strip(), body_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(para2.strip(), body_style))
    elements.append(PageBreak())

    
