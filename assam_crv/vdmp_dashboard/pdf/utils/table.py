
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from ..global_styles import tb_header_bg, tb_border_color, tb_border_width, blue_heading,underline_heading



def create_styled_table(table_data, col_width, merg=False, heading=True, custom_styles=None,title=None):
   
    wrap_style = ParagraphStyle(
        name="wrap_style",
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        wordWrap='CJK',
        alignment=1
    )

    # Wrap strings inside Paragraphs for text wrapping
    wrapped_data = []
    num_columns = max(len(row) for row in table_data)

    for row_idx, row in enumerate(table_data):
        wrapped_row = []
        for col_idx in range(num_columns):
            try:
                cell = row[col_idx]
            except IndexError:
                cell = ""  # Fill missing columns with empty string

            if isinstance(cell, str):
                if heading and row_idx == 0:
                    wrapped_row.append(Paragraph(f"<b>{cell}</b>", wrap_style))
                elif merg and row_idx == 1:
                    wrapped_row.append(Paragraph(f"<b>{cell}</b>", wrap_style))
                else:
                    wrapped_row.append(cell)
            else:
                wrapped_row.append(cell)

        wrapped_data.append(wrapped_row)

    # Table creation
    table = Table(wrapped_data, colWidths=col_width)
    
   
    # Base styles
    table_styles = [
        # ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), tb_border_width, tb_border_color),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]

    # print(custom_styles)
    # Add custom styles first so they can be overridden by heading styles if needed
    


    # Default alignment (can be overridden by custom styles)
    # if not custom_styles or not any('ALIGN' in str(style) for style in custom_styles):
    #     table_styles.append(("ALIGN", (0, 0), (-1, -1), "LEFT"))
    
    # if not custom_styles or not any('ALIGN' in str(style) for style in custom_styles):
    #     table_styles.append(("ALIGN", (0, 0), (-1, -1), "CENTER"))


    if heading:
        table_styles.extend([
        ("BACKGROUND", (0, 0), (-1, 0), tb_header_bg),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
       ("VALIGN", (0, 0), (-1, -0), "CENTER"),
    ])
        

    if merg:
        table_styles.insert(0, ('SPAN', (0, 0), (1, 0))),  # Example merge
        table_styles.append( ('BACKGROUND', (0, 0), (1, 0),tb_header_bg))  # Example merge
        
    if custom_styles:
        # Validate SPAN operations before applying
        validated_styles = []
        for style in custom_styles:
            if style[0] == 'SPAN':
                start_col, start_row, end_col, end_row = style[1][0], style[1][1], style[2][0], style[2][1]
                # Check if span coordinates are within table bounds
                if (start_col < num_columns and end_col < num_columns and 
                    start_row < len(wrapped_data) and end_row < len(wrapped_data)):
                    validated_styles.append(style)
            else:
                validated_styles.append(style)
        table_styles.extend(validated_styles)
    
    table.setStyle(TableStyle(table_styles))
    return table
