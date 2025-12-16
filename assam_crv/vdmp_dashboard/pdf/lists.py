from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .dummy_data import abbreviations
from .global_styles import common_table_style, blue_heading, list_of_table_heading
from reportlab.lib.colors import HexColor


list_of_figures=[]
list_of_tables=[]

def draw_list_of_figures(elements, doc):
    """Generate the list of figures section using collected figure data"""
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    
    # Table style configuration
    tb_header_bg = HexColor('#D3D3D3')  # Light gray
    tb_border_color = colors.black
    tb_border_width = 0.5
    
    # Add heading
    elements.append(Paragraph("<b>List of Figures</b>", list_of_table_heading))
    elements.append(Spacer(1, 12))

    # Create table data - header + rows
    data = [["Sr. No.", "Figure Number and Title", "Page"]]
    
    # Sort figures by page number
    sorted_figures = sorted(doc.figure_list, key=lambda x: x['page'])
    
    # print("Figures found:", sorted_figures)    
    
    for i, figure in enumerate(sorted_figures, 1):
        title = figure['title']
        page = figure['page']
        
        if ':' in title:
            figure_num, figure_title = title.split(':', 1)
            figure_num = figure_num.strip()
            figure_title = figure_title.strip()
            figure_title_text = Paragraph(f"<b>{figure_num}</b>: {figure_title}", normal)
        else:
            figure_title_text = Paragraph(title, normal)

        data.append([str(i), figure_title_text, str(page)])

    # Create the table
    table = Table(data, colWidths=[50, 350, 100])
    table.setStyle(common_table_style)
    
    elements.append(table)

def draw_list_of_tables(elements, doc):
    """Generate the list of tables section using collected table data"""
    # from reportlab.platypus import Table, TableStyle
    # from reportlab.lib import colors
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    # Table style configuration
    tb_header_bg = HexColor('#D3D3D3')  # Light gray
    tb_border_color = colors.black
    tb_border_width = 0.5
    
    # # Add heading
    elements.append(Paragraph("<b>List of Tables</b>", list_of_table_heading))
    elements.append(Spacer(1, 12))
    
        # Create the heading paragraph
    # heading = Paragraph("List of Tables", list_of_table_heading)

    # # Wrap the heading in a one-cell table
    # heading_table = Table([[heading]], colWidths=[500])  # Adjust width to match page width
    
    # elements.append(heading_table)

    # Apply background and padding
    # heading_table.setStyle(TableStyle([
    #     ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),  # Background color
    #     ('LEFTPADDING', (0, 0), (-1, -1), 6),
    #     ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    #     ('TOPPADDING', (0, 0), (-1, -1), 4),
    #     ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    # ]))

    # Create table data - header + rows
    data = [["Sr. No.", "Table Number and Title", "Page"]]
    
    # Sort tables by page number
    sorted_tables = sorted(doc.table_list, key=lambda x: x['page'])
    
    # print(sorted_tables)    
    
    for i, table in enumerate(sorted_tables, 1):
        title = table['title']
        page = table['page']
        
        if ':' in title:
            table_num, table_title = title.split(':', 1)
            table_num = table_num.strip()
            table_title = table_title.strip()
            table_title_text = Paragraph(f"<b>{table_num}</b>: {table_title}", normal)
        else:
            table_title_text = Paragraph(title, normal)

        data.append([str(i), table_title_text, str(page)])

    # Create the table
    table = Table(data, colWidths=[50, 350, 100])
    table.setStyle(common_table_style)
    
    elements.append(table)
    # elements.append(PageBreak())



def draw_abbreviations(elements):
    styles = getSampleStyleSheet()
    
    
    # Heading
    heading = Paragraph("<b>List of Abbreviations Used</b>", list_of_table_heading,)
    
    elements.append(heading)
    elements.append(Spacer(1, 12))

    # Table header
    table_data = [["Sr. No.","Abbreviation", "Full Form"]]

    # Convert JSON list to table format
    for i, entry in enumerate(abbreviations["abbreviations"], 1):
        table_data.append([
            str(i),
            Paragraph(entry["abbreviation"], styles["Normal"]),
            Paragraph(entry["expanded_form"], styles["Normal"])
        ])

    # Define table layout and styles
    table = Table(table_data, colWidths=[50, 120, 350])
    table.setStyle(common_table_style)

    elements.append(table)
    elements.append(PageBreak())