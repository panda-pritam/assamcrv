from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import TableStyle
from reportlab.lib.enums import TA_CENTER

# Global color variables
tb_header_bg = colors.HexColor('#e1edff')
tb_border_color = colors.HexColor('#96b9e7')
tb_border_width = 0.20

# page heading 
heading_color=colors.HexColor('#245fae')

heading_box_color = colors.HexColor("#e1edff")


#heading left Indent
heading_left_indent=-45

#body left Indent
body_left_indent=-45

# Common table style
common_table_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), tb_header_bg),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ('GRID', (0, 0), (-1, -1), tb_border_width, tb_border_color),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    #   ('ALIGN', (0, 1), (0, -1), 'RIGHT'), 
])

styles = getSampleStyleSheet()

toc_main_heading = ParagraphStyle(
    name='TOCMainHeading',
    parent=styles['Heading1'],
    textColor=heading_color,
    alignment=TA_CENTER,
    underline=1,
    leftIndent=0,      # ✅ reset
    rightIndent=0,     # ✅ reset
    spaceAfter=12
)
list_of_table_heading= ParagraphStyle(
        name='ListofTableHeading',
        parent=styles['Heading2'],
        textColor=heading_color,
        leftIndent=heading_left_indent,
        underline=1
    )

# Table heading
table_heading = ParagraphStyle(
        name='UserLineHeading',
        parent=styles['Heading1'],
        textColor=colors.brown,
        leftIndent=heading_left_indent,
        underline=1
    )
# Blue heading style    
blue_heading = ParagraphStyle(
    name='BlueHeading',
    parent=styles['Heading1'],
    textColor=heading_color,
     leftIndent=heading_left_indent,
    
)

box_heading_text=ParagraphStyle(
    name='BoxHeadingText',
    parent=styles['Heading1'],
    textColor=heading_color,
    #  leftIndent=heading_left_indent,
    
)



blue_sub_heading = ParagraphStyle(
        name='BlueSubHeading',
        parent=styles['Heading2'],
        textColor=heading_color,
        leftIndent=heading_left_indent,
        fontSize=12
    )

blue_sub_heading_sub = ParagraphStyle(
        name='BlueSubHeading',
        parent=styles['Heading2'],
        textColor=heading_color,
        leftIndent=-55,
        fontSize=12
    )

blue_level3_heading= ParagraphStyle(
        name='BlueLevel3Heading',
        parent=styles['Heading2'],
        textColor=heading_color,
        leftIndent=heading_left_indent,
        fontSize=10
    )

blue_level4_heading= ParagraphStyle(
        name='BlueLevel4Heading',
        parent=styles['Heading3'],
        textColor=heading_color,
        leftIndent=heading_left_indent,
        fontSize=10
    )

# User line heading style
underline_heading = ParagraphStyle(
        name='UserLineHeading',
        parent=styles['Heading2'],
        textColor=colors.black,
        leftIndent=heading_left_indent,
        underline=1
    )

# Table title style
table_sub_title = ParagraphStyle(
        name='TableTitle',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=12,
        alignment=1,
        textColor=colors.HexColor('#ae2e24')
    )


image_title = ParagraphStyle(
        name='ImageTitle',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=14,
        alignment=1,
        textColor=colors.black
    )


# Create a custom heading style that won't be included in TOC
non_toc_heading = ParagraphStyle(
    name='NonTOCHeading',
    parent=getSampleStyleSheet()['Heading1'],
    fontSize=12,
    # leading=16,
    textColor=colors.black,
    # spaceAfter=6,
    # These properties help ensure it's not picked up by TOC
    outlineLevel=0,  # 0 means not a heading level
    keepWithNext=0,
    leftIndent=heading_left_indent + 4    ,
    # IMPORTANT
    spaceBefore=6,
    spaceAfter=0,
)


body_style=ParagraphStyle(
        name='BodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leftIndent=body_left_indent,
    )

notes_style=ParagraphStyle(
        name='NotesText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leftIndent=-30,
        spaceBefore=8,
        fontName='Helvetica-Oblique'
    )


Legend_heading = ParagraphStyle(
        name='Legend_heading',
        parent=styles['Heading2'],
         fontSize=14,
        textColor=colors.black,
        leftIndent=heading_left_indent,
        underline=1
    )


indented_style = ParagraphStyle(
    'Indented',
    parent=styles['Normal'],  # inherit base Normal style
    leftIndent=20,            # 20 points indent from left
    spaceAfter=3              # small gap after each line
)

non_indented_style = ParagraphStyle(
    'Indented',
    parent=styles['Normal'],  # inherit base Normal style
    leftIndent=-40,           
    spaceAfter=3              # small gap after each line
)

srNoStyle=[
      ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
       ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
]

normal_style = styles['Normal']
bold_style = ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold')
center_style = ParagraphStyle('Bold', parent=normal_style,alignment=1,)
bold_center_style = ParagraphStyle('Bold', parent=normal_style,alignment=1,fontName='Helvetica-Bold',)
bold_center_style_9 = ParagraphStyle('Bold', parent=normal_style,alignment=1,fontName='Helvetica-Bold',fontSize=9)
# table header bg #e1edff
# table border bg #96b9e7

bold_12 = ParagraphStyle(
    'Bold12',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=9
)

bold_12_center = ParagraphStyle(
    'Bold12',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=9,
    alignment=1
)

left_indent_paragraph_sec = ParagraphStyle(
    'LeftIndent',
    parent=styles['Normal'],
    leftIndent=-28,
)

left_indent_paragraph = ParagraphStyle(
    'LeftIndent',
    parent=styles['Normal'],
    leftIndent=heading_left_indent,
)

right_align_text = ParagraphStyle ( name='RightAlign', parent=styles['Normal'], alignment=2)

bold_right_align_text = ParagraphStyle (name='BoldRightAlign', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold',fontSize=9,)


