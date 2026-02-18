from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from .global_styles import blue_heading, body_style
from village_profile.models import tblVillage


def draw_about_this_document(elements, village_id):

    # 🔹 Get village with full relation in single query (optimized)
    village = tblVillage.objects.select_related(
        "gram_panchayat__circle__district"
    ).get(id=village_id)

    village_name = village.name
    district_name = village.gram_panchayat.circle.district.name

    # Add heading
    heading = Paragraph("<a name='about_document'/>1  About this Document", blue_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))

    # Static paragraph
    para1 = """
    The Government of Assam, through the Assam State Disaster Management Authority (ASDMA), is implementing the Assam Integrated River Basin Management Program (AIRBMP). The Program supports improved Integrated Water Resources Management (IWRM) for the economic growth and prosperity of the State, together with addressing flood and river erosion risks. One of the components of this project is to develop Village Disaster Mitigation Plans (VDMPs) for 50 villages selected across 7 districts, which are prone to frequent flooding and erosion. The identified districts are (1) Barpeta, (2) Bajali, (3) Sonitpur, (4) Biswanath, (5) Golaghat, (6) Majuli, (7) Lakhimpur, (8) Naogoan, (9) Dibugargh and (10) Demaji. This activity comes under Phase I of the Program. ASDMA has hired RMSI Private Limited as the Socio-Technical Agency (STA) to implement this project.
    """

    # 🔹 Dynamic paragraph
    para2 = f"""
    The development of a village-level Village Disaster Mitigation Plan (VDMP) 
    is one of the key deliverables of this assignment. This document presents 
    the VDMP for <b>{village_name}</b> village in <b>{district_name}</b> District. 
    The plan has been developed through a multi-step process, including field 
    surveys, community consultations, consultations with line department officials, 
    and the use of GIS and remote sensing technologies.
    """

    elements.append(Paragraph(para1.strip(), body_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(para2.strip(), body_style))
    elements.append(PageBreak())
