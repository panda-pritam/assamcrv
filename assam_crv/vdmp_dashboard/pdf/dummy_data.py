from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
normal_style = styles['Normal']
from .global_styles import  blue_heading,table_sub_title,blue_sub_heading,image_title,notes_style,tb_header_bg,Legend_heading,indented_style,bold_style,normal_style,srNoStyle,non_toc_heading,blue_level3_heading,non_indented_style

abbreviations={
  "abbreviations": [
    {
      "abbreviation": "AAY",
      "expanded_form": "Aantyodaya Anna Yojana"
    },
    {
      "abbreviation": "AIRBMP",
      "expanded_form": "Assam Integrated River Basin Management Program"
    },
    {
      "abbreviation": "APL",
      "expanded_form": "Above Poverty Line"
    },
    {
      "abbreviation": "ASDMA",
      "expanded_form": "Assam State Disaster Management Authority"
    },
    {
      "abbreviation": "AY",
      "expanded_form": "Annapurna Yojana"
    },
    {
      "abbreviation": "BPL",
      "expanded_form": "Below Poverty Line"
    },
    {
      "abbreviation": "CPR",
      "expanded_form": "Cardiopulmonary Resuscitation"
    },
    {
      "abbreviation": "CRV",
      "expanded_form": "Climate Resilient Village"
    },
    {
      "abbreviation": "DDMA",
      "expanded_form": "District Disaster Management Authority"
    },
    {
      "abbreviation": "DEM",
      "expanded_form": "Digital Elevation Model"
    },
    {
      "abbreviation": "DEOC",
      "expanded_form": "District Emergency Operation Centre"
    },
    {
      "abbreviation": "DM",
      "expanded_form": "Disaster Management"
    },
    {
      "abbreviation": "DMC",
      "expanded_form": "Disaster Management Committee"
    },
    {
      "abbreviation": "DMT",
      "expanded_form": "Disaster Management Team"
    },
    {
      "abbreviation": "GIS",
      "expanded_form": "Geographic Information System"
    },
    {
      "abbreviation": "HH",
      "expanded_form": "Household"
    },
    {
      "abbreviation": "IMD",
      "expanded_form": "Indian Meteorological Depart"
    },
    {
      "abbreviation": "INR",
      "expanded_form": "Indian Rupee"
    },
    {
      "abbreviation": "IWRM",
      "expanded_form": "Integrated Water Resources Management"
    },
    {
      "abbreviation": "JJM",
      "expanded_form": "Jal Jeevan Mission"
    },
    {
      "abbreviation": "KVK",
      "expanded_form": "Krishi Vigyan Kendra"
    },
    {
      "abbreviation": "L.P. School",
      "expanded_form": "Lower Primary School"
    },
    {
      "abbreviation": "LULC",
      "expanded_form": "Land Use Land Cover"
    },
    {
      "abbreviation": "LVI",
      "expanded_form": "Livelihood Vulnerability Index"
    },
    {
      "abbreviation": "MEM",
      "expanded_form": "Marginalized Excluded Minorities"
    },
    {
      "abbreviation": "MMI",
      "expanded_form": "Modified Mercalli Intensity"
    },
    {
      "abbreviation": "MNREGA",
      "expanded_form": "Mahatma Gandhi National Rural Employment Guarantee Act"
    },
    {
      "abbreviation": "MRP",
      "expanded_form": "Max Retail Price"
    },
    {
      "abbreviation": "MSL",
      "expanded_form": "Mean Sea Level"
    },
    {
      "abbreviation": "MSP",
      "expanded_form": "Minimum Support Price"
    },
    {
      "abbreviation": "MRP",
      "expanded_form": "Maximum Retail Price"
    },
    {
      "abbreviation": "NGO",
      "expanded_form": "Non Governmental Organization"
    },
    {
      "abbreviation": "PGA",
      "expanded_form": "Peak Ground Acceleration"
    },
    {
      "abbreviation": "PHC",
      "expanded_form": "Primary Health Centre"
    },
    {
      "abbreviation": "PHED",
      "expanded_form": "Public Health & Engineering Department"
    },
    {
      "abbreviation": "PHH",
      "expanded_form": "Priority Household"
    },
    {
      "abbreviation": "PMAY",
      "expanded_form": "Pradhan Mantri Awas Yojana"
    },
    {
      "abbreviation": "PNRD",
      "expanded_form": "Panchayat and Rural Development"
    },
    {
      "abbreviation": "PWD",
      "expanded_form": "Public Works Department"
    },
    {
      "abbreviation": "SDRF",
      "expanded_form": "State Disaster Response Force"
    },
    {
      "abbreviation": "SOP",
      "expanded_form": "Standard Operating Procedure"
    },
    {
      "abbreviation": "STA",
      "expanded_form": "Socio Technical Agency"
    },
    {
      "abbreviation": "VDMP",
      "expanded_form": "Village Disaster Management Plan"
    },
    {
      "abbreviation": "VLCDMC",
      "expanded_form": "The village has a Village Land Conservation & Disaster Management Committee"
    },
    {
      "abbreviation": "WASH",
      "expanded_form": "Water Sanitation and Hygiene"
    },
    {
      "abbreviation": "WRD",
      "expanded_form": "Water Resources Department"
    }
  ]
}



# def generate_socio_economic_summary_table(village_id):
#     return [
#         ['Socio-Economic Summary'],
#         ['Total Population', 4325],
#         ['Total Households', 1026],
#         ['Dominant House Type', 'Kachcha (tin roof and tin wall) - 86%'],
#         ['Major Land Use', 'Agriculture land (wet land) - 43%'],
#         ['Occupational Category', 'Agriculture'],
#         ['Sanitation Facilities', 'Kachcha toilet - 76%']
#     ]

# def getHazardAssessment(village_id):
#     return [
#         ['Hazard Assessment'],
#         ['Flood Hazard', 'Almost every year'],
#         ['Erosion Hazard', 'Severe & high, 2.4 km river stretch'],
#         ['Strong Wind Hazard', 'Low (38–51 kmph)'],
#         ['Earthquake Hazard', 'Zone V']
#     ]

# def getVulnerabilityAssessment(village_id):
#     return [
        
#         ["Vulnerability Assessment"],
#         ['Economic Status', 'BPL - 64%, Priority Households - 25%'],
#         ['Vulnerable Population', '1112 (26%)'],
#         ['Flood Vulnerability Houses', 'Severe - 84%'],
#         ['Erosion Vulnerability Houses', 'High - 1%'],
#         ['Flood Vulnerability Roads', 'Nil'],
#         ['Erosion Vulnerability Roads', 'Nil'],
#         ['Schools', '3 (2 high, 1 moderate)'],
#         ['Livelihood Vulnerability Index', 2.5],
#         ['Index Interpretation', 'between moderate and high']
#     ]


# def getRiskAssessment(village_id):
#     return [
#         ['Risk Assessment (excluding content loss in INR Crore)'],
#         ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'),'Earthquake 475 RP','Strong wind 100 RP'],
#         ['Residential', '2.24'],
#         ['Commercial', '0.04'],
#         ['Critical Facilities', '0.03'],
#         ['Roads', '0.50'],
#         ['Agriculture', '0.76'],
#         ['Note', 'Excluding content loss']
#     ]

# def getMitigationIntervention(village_id):
#     return [
#         ['Mitigation intervention'],
#         ['Resilient Housing', Paragraph('Only reconstruction cost considered')],
#         ['Resilient Roads', 'INR 2,82,00,000'],
#         ['River Bank Protection', 'INR 1,80,00,000'],
#         ['Resilient Essential Services', ''],
#         ['Educational Facilities', 'INR 5,50,00,000'],
#         ['Health Facilities', 'Nil'],
#         ['Public WASH Facilities and Drinking Water', 'INR 1,10,000'],
#         ['Electric Facilities', 'INR 17,75,000'],
#         ['Resilient Livelihood & Economic Security', ''],
#         ['Amount', 'INR 4,30,00,000'],
#         ['Additional Support', 'regional programs']
#     ]
    
# def getDistrictLevelOfficialsData():
#     return [
#         ["S. No.", "Name", "Gender", "Phone Number", "Position/Responsibility"],
#         ["1", "Ms. Nandita Dutta", "F", "8638347974", "DPO, DDMA, Barpeta"],
#         ["2", "Mr. Abizur Rahman Khan", "M", "8638984834", "FO"],
#         ["3", Paragraph("Mr. Abdul Malik, Anchalik Gram Unnayan Parishad, Jania"), "M", "8638199690", Paragraph("Chief Functionary of NGO and IAG Member (District Chapter), Barpeta")]
#     ]
def getEmergencyTollFreeContactData():
    return [
        ["S. No.", "Important Contact Person", "Contact Number"],
        ["1", "Police Station", "100"],
        ["2", "Fire Station", "102"],
        ["3", "Ambulance", "108"],
        ["4", Paragraph("District Commissioner (Emergency Toll-Free)"), Paragraph("<para align=center>1077 (District), 1079 (State)</para>")],
        ["5", Paragraph("District Emergency Operation Centre, Barpeta"), "9864643089"]
    ]
# def getImportantEmergencyContactData():
#     return [
#         ["S. No.", "Important Contact Person", "Contact Number"],
#         ["1", "District Collector", "03674-284455"],
#         ["2", "DDMA/DEOC (Helpline Toll Free)", "1077 (District), 1079 (State)"],
#         ["3", "Circle Officer, Baghbor", ""],
#         ["4", "Field Officer", "7002837614"]
#     ]
    
# # ------------------ Village Profile ----------------------------
# def getVillageLocationDetails():
#     return [
#         ["Village Location Details"],
#         ["Village Name", "Rupakuchi"],
#         ["Block", "Mandia"],
#         ["Revenue Circle", "Baghbor"],
#         ["District", "Barpeta"],
#         ["State", "Assam"],
        
#     ]
    
# def getVillageDemographic():
#     return [
#         ["Household Characteristic", "Total"],
#         ["No of Males", "2,149"],
#         ["No of Females", "2,176"],
#         ["Total Population", "4,325"],
#         ["Number of Households", "1,026"],
#         ["Absentee House", "14"],
#         ["Average Family Size", "4.2"],
#         ["Male-Female Ratio", "988"]
#     ]
    
    
# def getSocialEconomicStatusData():
#     return [
#         ["Social/Economic Status Household", "AAY", "APL", "AY", "BPL", "PHH", "Total", "%"],
#         ["Married Male", "82", "30", "3", "598", "238", "951", "93%"],
#         ["Single Man", "2", "0", "0", "15", "4", "21", "2%"],
#         ["Single Women", "0", "0", "0", "1", "0", "1", "0%"],
#         ["Widow", "3", "1", "0", "38", "11", "53", "5%"],
#         ["Total", "87", "31", "3", "652", "253", "1,026", ""],
#         ["%", "8%", "3%", "0%", "64%", "25%", "", ""]
#     ]
# def getIncomeGroupData():
#     return [
#         ["Income Group", "No. of Household", "Percentage"],
#         ["Upto 50,000", "30", "2.9%"],
#         ["Upto 1,50,000", "821", "80.0%"],
#         ["Upto 2,50,000", "148", "14.4%"],
#         ["> 2,50,000", "27", "2.6%"],
#         ["Total", "1,026", "100%"]
#     ]
    
# def getAgricultureLandHoldingData():
#     return [
#         ["Agricultural land ownership (in bigha)", "< 0.5", "0.5–1.5", "1.5–2.5", "> 2.5", "Total"],
#         ["Leased", "27", "72", "81", "43", "223"],
#         ["% leased to total leased", "12%", "32%", "36%", "19%", "100%"],
#         ["Owned", "14", "117", "115", "61", "307"],
#         ["% owned to total HH with own agriculture land", "5%", "38%", "37%", "20%", "100%"],
#         ["No land (basically manual labour)", "", "", "", "", "496"],
#         ["Total", "", "", "", "", "1,028"]
#     ]


# def getAverageExpenditureBreakdownData():
#     return [
#         ["Expenditure", "%"],
#         ["Agriculture/livestock", "8.55%"],
#         ["Festival, marriage and other social functions per year", "10.55%"],
#         ["Repair of house every year", "11.71%"],
#         ["Tobacco, liquor etc per annum", "0.21%"],
#         ["Education of children including tuition fee, books, etc.", "10.98%"],
#         ["Health related including buying medicine, hospital charges, etc.", "14.30%"],
#         ["Food and household expenditure", "43.69%"]
#     ]

# def getHouseholdDebtLiabilityData():
#     return [
#         ["Loan Amount (INR)", "Number of HH", "%"],
#         ["0", "897", "87.43%"],
#         ["<10k", "5", "0.49%"],
#         ["10–50K", "56", "5.46%"],
#         ["50–100K", "68", "6.63%"]
#     ]

# def getPrimaryLivelihoodDistributionData():
#     return [
#       ['Livelihood','Primary economic activity'],
#         ["", "No. of Household", "%"],
#         ["Agriculture", "336", "33%"],
#         ["Fishing", "15", "1%"],
#         ["Livestock", "4", "0%"],
#         ["Manual labour", "534", "52%"],
#         ["No job", "1", "0%"],
#         ["Service", "30", "3%"],
#         ["Shop", "106", "10%"],
#         ["Total", "1,026", "100%"]
#     ]

# def getCropCultivationData():
#     return [
#         ["Number of Crops Cultivated Every Year", "Household", "%"],
#         ["One crop", "661", "64%"],
#         ["Two crops", "139", "14%"],
#         ["Three crops", "226", "22%"],
#         ["Total", "1,026", "100%"]
#     ]

def getLivestockOwnershipData(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Count", "Livestock","","Small cattle"], ["", "HH with Big Cattle", "%", "HH with Small Cattle", "%"], ["0", "0", "0%", "0", "0%"], ["< 3", "0", "0%", "0", "0%"], ["3–6", "0", "0%", "0", "0%"], [">6", "0", "0%", "0", "0%"]]
        
        # Count big cattle
        big_0 = households.filter(big_cattle='No Big Cattle').count()
        big_3 = households.filter(big_cattle='Upto 3 Big Cattle').count()
        big_3_6 = households.filter(big_cattle='3 To 6 Big Cattle').count()
        big_6_plus = households.filter(big_cattle='Morethan 6 Big Cattle').count()
        
        # Count small cattle
        small_0 = households.filter(small_cattle='No Small Cattle').count()
        small_3 = households.filter(small_cattle='Upto 3 Small Cattle').count()
        small_3_6 = households.filter(small_cattle='3 To 6 Small Cattle').count()
        small_6_plus = households.filter(small_cattle='Morethan 6 Small Cattle').count()
        
        # Calculate percentages
        big_0_pct = f"{round(big_0/total_households*100)}%"
        big_3_pct = f"{round(big_3/total_households*100)}%"
        big_3_6_pct = f"{round(big_3_6/total_households*100)}%"
        big_6_plus_pct = f"{round(big_6_plus/total_households*100)}%"
        
        small_0_pct = f"{round(small_0/total_households*100, 2)}%"
        small_3_pct = f"{round(small_3/total_households*100, 2)}%"
        small_3_6_pct = f"{round(small_3_6/total_households*100, 2)}%"
        small_6_plus_pct = f"{round(small_6_plus/total_households*100, 2)}%"
        
        return [
            ["Count", "Livestock","","Small cattle"],
            ["", "HH with Big Cattle", "%", "HH with Small Cattle", "%"],
            ["0", str(big_0), big_0_pct, str(small_0), small_0_pct],
            ["< 3", str(big_3), big_3_pct, str(small_3), small_3_pct],
            ["3–6", str(big_3_6), big_3_6_pct, str(small_3_6), small_3_6_pct],
            [">6", str(big_6_plus), big_6_plus_pct, str(small_6_plus), small_6_plus_pct]
        ]
    except Exception:
        return [
            ["Count", "Livestock","","Small cattle"],
            ["", "HH with Big Cattle", "%", "HH with Small Cattle", "%"],
            ["0", "N/A", "N/A", "N/A", "N/A"],
            ["< 3", "N/A", "N/A", "N/A", "N/A"],
            ["3–6", "N/A", "N/A", "N/A", "N/A"],
            [">6", "N/A", "N/A", "N/A", "N/A"]
        ]


# def getHousingTypologyData(village_id):
#     try:
#         households = HouseholdSurvey.objects.filter(village=village_id)
#         total_households = households.count()
        
#         if total_households == 0:
#             return [["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"], ["No. of Household", "0", "0", "0", "0"], ["%", "0%", "0%", "0%", ""]]
        
#         # Count households by house type
#         kachcha = households.filter(house_type='Kachcha').count()
#         semi_pucca = households.filter(house_type='Semi Pucca').count()
#         pucca = households.filter(house_type='Pucca').count()
        
#         # Calculate percentages
#         kachcha_pct = f"{round(kachcha/total_households*100, 1)}%"
#         semi_pucca_pct = f"{round(semi_pucca/total_households*100, 1)}%"
#         pucca_pct = f"{round(pucca/total_households*100, 1)}%"
        
#         return [
#             ["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
#             ["No. of Household", str(kachcha), str(semi_pucca), str(pucca), str(total_households)],
#             ["%", kachcha_pct, semi_pucca_pct, pucca_pct, ""]
#         ]
#     except Exception:
#         return [
#             ["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
#             ["No. of Household", "N/A", "N/A", "N/A", "N/A"],
#             ["%", "N/A", "N/A", "N/A", ""]
#         ]




def getPublicAssetsData(village_id):
    try:
        from ..models import Commercial
        facilities = Commercial.objects.filter(village=village_id)
        
        if facilities.count() == 0:
            return [["Presence of facilities"], ["Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"], ["Anganwadi", "0", "0", "0", "0", "0", "0"], ["LP School", "0", "0", "0", "0", "0", "0"], ["Middle School", "0", "0", "0", "0", "0", "0"], ["Religious Place", "0", "0", "0", "0", "0", "0"]]
        
        facility_types = ['Anganwadi', 'LP School', 'Middle School', 'Religious Place']
        result = [["Presence of facilities"], ["Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"]]
        
        for facility_type in facility_types:
            type_facilities = facilities.filter(type_of_occupancy=facility_type)
            total_count = type_facilities.count()
            
            electricity_count = type_facilities.filter(house_has_electric_connection='Yes').count()
            drinking_water_count = type_facilities.exclude(drinking_water_source__isnull=True).exclude(drinking_water_source='yes').count()
            sanitation_count = type_facilities.exclude(toilet_facility__isnull=True).exclude(toilet_facility='yes').count()
            good_road_count = type_facilities.filter(access_road_during_flood='Good Road').count()
            good_building_count = type_facilities.filter(building_quality__in=['Good', 'Good ']).count()
            
            result.append([
                facility_type,
                str(total_count),
                str(electricity_count),
                str(drinking_water_count),
                str(sanitation_count),
                str(good_road_count),
                str(good_building_count)
            ])
        
        return result
    except Exception:
        return [
            ["Presence of facilities"],
            ["Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"],
            ["Anganwadi", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["LP School", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["Middle School", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["Religious Place", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
        ]

# def getRoadLengthByTypologyData():
#     return [
#         ["Surface Type", "Length (km)", "% to Total Road Length"],
#         ["PNRD (Cement block road)", "2.44", "22.88%"],
#         ["PNRD (Earthen road)", "6.79", "63.64%"],
#         ["PWD (Bituminous road)", "0.49", "4.63%"],
#         ["PWD (Cement block road)", "0.94", "8.85%"],
#         ["Total", "10.66", "100.00%"]
#     ]

# def getFacilityAccessData():
#     return [
#         ["Sr. No.","Asset Type", "Distance from Village", "Remarks"],
#         ["1","Higher education/College", "13 km", "Barpeta"],
#         ["2","Post Office", "3 km", "Jania Market"],
#         ["3","Police Station", "13 km", "Barpeta"],
#         ["4","Banks", "3 km", "Jania Market"],
#         ["5","Cooperative Societies", "4 km", Paragraph("Amul Cooperative Society")],
#         ["6","PHC/CHC", "13 km", "Mandia"],
#         ["7","Private Clinic/Hospital", "3 km", "Jogijan"],
#         ["8","Major Government Offices", "13 km", "Barpeta"],
#         ["9","Ambulance", "13 km", "Barpeta"],
#         ["10","Bus Service", "3 km", "Jania Market"],
#         ["11","Main Markets", "3 km", "Jania Market"],
#         ["12","Veterinary Hospitals", "3 km", "Mohammadpur"]
#     ]

# def getLandUseClassificationData():
#     return [
#         ["Landuse", "Area (sqm)", "%"],
#         ["Agricultural Land", "10,11,302", "30%"],
#         ["Fallow Land", "4,54,753", "13%"],
#         ["Open Land", "6,46,647", "19%"],
#         ["Pond/Waterbody", "2,52,621", "7%"],
#         ["River/Stream", "3,29,892", "10%"],
#         ["Roads", "44,716", "1%"],
#         ["Settlement", "1,31,423", "4%"],
#         ["Scrub Land", "4,479", "0%"],
#         ["Tree Clad Area", "4,93,886", "15%"],
#         ["Total Area", "33,69,719", ""]
#     ]

# ------------- 4.1 --------------






#---------------------- 4.2 ----------------





# def getVulnerabilityAssessmentTableData():
#     return [
#         ["Vulnerability level", "Flood","", "Erosion"],
#         ['','Number of HH','%','Number of HH','%'],
#         ["Severe", "123", "11.99%", "71", "6.92%"],
#         ["High", "691", "67.35%", "169", "16.47%"],
#         ["Medium", "189", "18.42%", "219", "21.35%"],
#         ["Low", "23", "2.24%", "567", "55.26%"]
#     ]
# def getHouseTypologyTableData():
#     return [
#         ["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
#         ["Number of Household", "881", "142", "3", "1,026"],
#         ["%", "86%", "14%", "0.3%", ""]
#     ]
# def getBuildingQualityTableData():
#     return [
#         ["Building quality", "Number of HH", "%"],
#         ["Bad", "145", "14%"],
#         ["Good", "170", "17%"]
#     ]





# def getDevelopmentIssuesTable():
#     data = [
#         [Paragraph("S.No.", bold_style), Paragraph("Development Issues/Needs", bold_style), Paragraph("Explanation", bold_style)],
#         ['1', Paragraph("Housing", normal_style), Paragraph("Majority kachcha houses and are vulnerable to flood, earthquake and wind", normal_style)],
#         ['2', Paragraph("Road infrastructure", normal_style), Paragraph("Need intervention to improve resilience", normal_style)],
#         ['3', Paragraph("Public drinking water", normal_style), Paragraph("Need to raise the height of hand pumps", normal_style)],
#         ['4', Paragraph("Public sanitation during flood", normal_style), Paragraph("Needed", normal_style)],
#         ['5', Paragraph("Flood shelter", normal_style), Paragraph("LP school, Rupakuchi. Need intervention of resilient structure, WASH and power supply", normal_style)],
#         ['6', Paragraph("Raised flood platform", normal_style), Paragraph("Nil and needed", normal_style)],
#         ['7' ,Paragraph("Livelihood – Agriculture", normal_style), Paragraph("Three crops, agricultural activities mostly manual, high cost of input, need irrigation facilities for summer crops, storage facilities and solar drying facilities. Majority of the community are manual labours and doing agriculture in lease land", normal_style)],
#         ['8', Paragraph("Livelihood – Livestock", normal_style), Paragraph("Small scale homestead", normal_style)],
#         ['9', Paragraph("Livelihood – Others", normal_style), Paragraph("Fishing in small scale", normal_style)],
#         ['10', Paragraph("JJM water supply", normal_style), Paragraph("Not fully operational", normal_style)]
#     ]
#     return data

# def getResidentialVulnerabilityTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Indicators", bold_style), Paragraph("Quantity", bold_style)],
#         ['1',Paragraph("Number of structurally poor houses", normal_style), Paragraph("1,001", normal_style)],
#         ['2',Paragraph("Number of severe and high flood vulnerable houses", normal_style), Paragraph("814", normal_style)],
#         ['3',Paragraph("Number of houses with plinth height < 2.0 feet", normal_style), Paragraph("758", normal_style)],
#         ['4',Paragraph("Number of severe and high erosion vulnerable houses", normal_style), Paragraph("240", normal_style)],
#         ['5',Paragraph("Number of BPL household", normal_style), Paragraph("652", normal_style)]
#     ]
#     return data

# def getResilientHousingCostTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Housing typology", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Number", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style)],
#         ['1',Paragraph("Kachcha house (R1 (Mud House), R2A (Ikra House), R2B (Ikra House), R4 Bamboo House, R5A Tin House, R5B Tin House", normal_style), 
#          Paragraph("Reconstruction", normal_style), Paragraph("875", normal_style), Paragraph("5,00,000", normal_style), Paragraph("4,37,500,000", normal_style)],
#         ['2',Paragraph("Kachcha house (R3A (Chang House), R3B (Chang House)", normal_style), 
#          Paragraph("Renovation", normal_style), Paragraph("-", normal_style), Paragraph("1,50,000", normal_style), Paragraph("-", normal_style)],
#         ['3',Paragraph("R6 (Semi-pucca house), R6A (Semi-pucca house)", normal_style), 
#          Paragraph("Renovation", normal_style), Paragraph("126", normal_style), Paragraph("1,50,000", normal_style), Paragraph("18,900,000", normal_style)],
#         ['4',Paragraph("R7 (Pucca house)", normal_style), 
#          Paragraph("Renovation", normal_style), Paragraph("3", normal_style), Paragraph("3,00,000", normal_style), Paragraph("900,000", normal_style)]
#     ]
#     return data

# def getRoadTypologyTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Road type", bold_style), Paragraph("Total length (km)", bold_style), 
#          Paragraph("Severe+high flood vulnerable length (km)", bold_style), Paragraph("Severe+high erosion vulnerable length (km)", bold_style)],
#         ['1',Paragraph("PNRD (Cement block road)", normal_style), Paragraph("3.11", normal_style), 
#          Paragraph("2.99", normal_style), Paragraph("0", normal_style)],
#         ['2',Paragraph("PNRD (Earthen road)", normal_style), Paragraph("7.40", normal_style), 
#          Paragraph("6.25", normal_style), Paragraph("2.44", normal_style)],
#         ['3',Paragraph("PWD (Bituminous road)", normal_style), Paragraph("1.09", normal_style), 
#          Paragraph("0.39", normal_style), Paragraph("0.39", normal_style)],
#         ['4',Paragraph("PWD (Cement block road)", normal_style), Paragraph("0.98", normal_style), 
#          Paragraph("0.86", normal_style), Paragraph("0", normal_style)]
#     ]
#     return data

# def getRoadInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Road type", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Department", bold_style)],
#         ['1',Paragraph("Embankment road (presently earthen road)", normal_style), Paragraph("Top layering - Bituminous", normal_style), 
#          Paragraph("3.0 km", normal_style), Paragraph("13,000,000", normal_style), Paragraph("3,90,00,000", normal_style), Paragraph("PNRD", normal_style)],
#         ['2',Paragraph("Earthen road (Panchayat road)", normal_style), Paragraph("Top layering – Cement block", normal_style), 
#          Paragraph("1.7 km", normal_style), Paragraph("10,000,000", normal_style), Paragraph("1,70,00,000", normal_style), Paragraph("PWD", normal_style)],
#         ['3',Paragraph("Cement block road (two road northern part of the village)", normal_style), Paragraph("Culvert - Box culvert - 1X2X2 meter", normal_style), 
#          Paragraph("4", normal_style), Paragraph("2,00,000", normal_style), Paragraph("8,00,000", normal_style), Paragraph("PWD", normal_style)],
#         ['4',Paragraph("", normal_style), Paragraph("Side slope stabilization", normal_style), 
#          Paragraph("1.6 km", normal_style), Paragraph("50,00,000", normal_style), Paragraph("80,00,000", normal_style), Paragraph("PWD", normal_style)]
#     ]
#     return data

# def getRiverBankProtectionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("River length km needs protection", bold_style), Paragraph("Bank characteristic", bold_style), 
#          Paragraph("Erosion severity", bold_style), Paragraph("Remarks", bold_style)],
#         ['1',Paragraph("4.7 km", normal_style), Paragraph("Steep slope", normal_style), 
#          Paragraph("Moderate", normal_style), Paragraph("Past bank protection efforts using geobag. The bank is slumping and the geobag at many places damaged", normal_style)]
#     ]
#     return data

# def getRiverBankInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("River bank", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Department", bold_style)],
#         ['1',Paragraph("Chaulkhoa River", normal_style), Paragraph("Geobag and bamboo porcupine and reed grass planting", normal_style), 
#          Paragraph("3.0 km", normal_style), Paragraph("6,00,00,000", normal_style), Paragraph("1,80,00,000", normal_style), Paragraph("PNRD", normal_style)]
#     ]
#     return data

# def getEducationalFacilitiesTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Name of the facility", bold_style), Paragraph("Flood vulnerability", bold_style), 
#          Paragraph("Number of students", bold_style), Paragraph("Number of rooms", bold_style), Paragraph("Resilient WASH", bold_style), Paragraph("Resilient power supply", bold_style)],
#         ['1',Paragraph("275 Tapajuli LP School Rupakuchi (Government school)", normal_style), Paragraph("Severe", normal_style), 
#          Paragraph("120", normal_style), Paragraph("8", normal_style), Paragraph("Nil", normal_style), Paragraph("Nil", normal_style)],
#         ['2',Paragraph("Anganwadi, Tapajuli", normal_style), Paragraph("Moderate", normal_style), 
#          Paragraph("30", normal_style), Paragraph("2", normal_style), Paragraph("Nil", normal_style), Paragraph("Nil", normal_style)],
#         ['3',Paragraph("940 LPS School, Rupakuchi (Government school)", normal_style), Paragraph("Moderate", normal_style), 
#          Paragraph("120", normal_style), Paragraph("5", normal_style), Paragraph("Yes, poor", normal_style), Paragraph("Nil", normal_style)],
#         ['4',Paragraph("LP School, Rupakuchi (Government school)", normal_style), Paragraph("High", normal_style), 
#          Paragraph("20", normal_style), Paragraph("4", normal_style), Paragraph("Yes, poor", normal_style), Paragraph("Nil", normal_style)],
#         ['5',Paragraph("MEM community School", normal_style), Paragraph("Moderate", normal_style), 
#          Paragraph("10", normal_style), Paragraph("1", normal_style), Paragraph("Nil", normal_style), Paragraph("Nil", normal_style)],
#         ['6',Paragraph("Anganwadi, near MEM community school", normal_style), Paragraph("Low", normal_style), 
#          Paragraph("30", normal_style), Paragraph("2", normal_style), Paragraph("Yes", normal_style), Paragraph("Nil", normal_style)]
#     ]
#     return data

# def getEducationalInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
#         ['1',Paragraph("275 Tapajuli LP School Rupakuchi", normal_style), Paragraph("Culvert to drain water from school across the road", normal_style), 
#          Paragraph("1", normal_style), Paragraph("2,00,000", normal_style), Paragraph("2,00,000", normal_style), Paragraph("This can address small flood", normal_style)],
#         ['2',Paragraph("275 Tapajuli LP School Rupakuchi", normal_style), Paragraph("Renovate – increase plinth height by 3 feet", normal_style), 
#          Paragraph("1", normal_style), Paragraph("10,000,000", normal_style), Paragraph("10,000,000", normal_style), Paragraph("Cost effective solution. Adequate retrofitting needed", normal_style)],
#         ['3',Paragraph("275 Tapajuli LP School Rupakuchi", normal_style), Paragraph("Reconstruct - Multi-purpose facility centre", normal_style), 
#          Paragraph("1", normal_style), Paragraph("35,000,000", normal_style), Paragraph("35,000,000", normal_style), Paragraph("Demolish and reconstruct with 3 feet plinth height", normal_style)],
#         ['4',Paragraph("940 LPS School, Rupakuchi", normal_style), Paragraph("Renovate – increase plinth height by 3 feet", normal_style), 
#          Paragraph("1", normal_style), Paragraph("10,000,000", normal_style), Paragraph("10,000,000", normal_style), Paragraph("Cost effective solution. Strengthen access road", normal_style)]
#     ]
#     return data

# def getWASHInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
#         ['1',Paragraph("Public WASH facilities", normal_style), Paragraph("Resilient public WASH", normal_style), 
#          Paragraph("5", normal_style), Paragraph("22,000", normal_style), Paragraph("1,10,000", normal_style), Paragraph("Location – school used as shelter or embankment road", normal_style)],
#         ['2',Paragraph("Household facilities", normal_style), Paragraph("Resilient facilities - double pit sealed septic tank", normal_style), 
#          Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("Individuals have to construct", normal_style)]
#     ]
#     return data

# def getElectricInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
#         ['1',Paragraph("Transformer", normal_style), Paragraph("Fencing", normal_style), 
#          Paragraph("5", normal_style), Paragraph("30,000", normal_style), Paragraph("1,50,000", normal_style), Paragraph("Mandatory requirement", normal_style)],
#         ['2',Paragraph("Transformer", normal_style), Paragraph("Elevate 2 feet", normal_style), 
#          Paragraph("2", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("Below flood level", normal_style)],
#         ['3',Paragraph("Electric poles", normal_style), Paragraph("Strengthening of base", normal_style), 
#          Paragraph("325", normal_style), Paragraph("5,000", normal_style), Paragraph("16,25,000", normal_style), Paragraph("Vulnerable", normal_style)],
#         ['4',Paragraph("Electric lines", normal_style), Paragraph("Pruning of tree branches", normal_style), 
#          Paragraph("Entire network", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("Routine check before monsoon", normal_style)]
#     ]
#     return data

# def getLivelihoodInterventionTable():
#     data = [
#         [Paragraph("S.No.", bold_style),Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style), 
#          Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
#         ['1',Paragraph("Sluice gate", normal_style), Paragraph("Drainage development for water to flow. Maintenance of culvert", normal_style), 
#          Paragraph("1", normal_style), Paragraph("10,000,000", normal_style), Paragraph("10,000,000", normal_style), Paragraph("Canal needs to construct to water to drain out", normal_style)],
#         ['2',Paragraph("Solar based facilities", normal_style), Paragraph("Irrigation pumps and solar drier", normal_style), 
#          Paragraph("4", normal_style), Paragraph("5,00,000", normal_style), Paragraph("20,00,000", normal_style), Paragraph("Community based installation", normal_style)],
#         ['3',Paragraph("Construction of harvest storage space", normal_style), Paragraph("Construction of public pay and use godown", normal_style), 
#          Paragraph("1", normal_style), Paragraph("40,000,000", normal_style), Paragraph("40,000,000", normal_style), Paragraph("10,000 sq feet with partition for individual storage", normal_style)]
#     ]
#     return data









# Original functions commented out and copied with values replaced by "-"


def generate_socio_economic_summary_table(village_id):
    return [
        ['Socio-Economic Summary'],
        ['Total Population', '-'],
        ['Total Households', ''],
        ['Dominant House Type', ''],
        ['Major Land Use', '-'],
        ['Occupational Category', '-'],
        ['Sanitation Facilities', '-']
    ]

def getHazardAssessment(village_id):
    return [
        ['Hazard Assessment'],
        ['Flood Hazard', '-'],
        ['Erosion Hazard', '-'],
        ['Strong Wind Hazard', '-'],
        ['Earthquake Hazard', '-']
    ]


def getVulnerabilityAssessment(village_id):
    return [
        ["Vulnerability Assessment"],
        ['Economic Status', '-'],
        ['Vulnerable Population', '-'],
        ['Flood Vulnerability Houses', '-'],
        ['Erosion Vulnerability Houses', '-'],
        ['Flood Vulnerability Roads', '-'],
        ['Erosion Vulnerability Roads', '-'],
        ['Schools', '-'],
        ['Livelihood Vulnerability Index', '-'],
        ['Index Interpretation', '-']
    ]

# def getRiskAssessment(village_id):
#     return [
#         ['Risk Assessment (excluding content loss in INR Crore)'],
#         ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'),'Earthquake 475 RP','Strong wind 100 RP'],
#         ['Residential', '-'],
#         ['Commercial', '-'],
#         ['Critical Facilities', '-'],
#         ['Roads', '-'],
#         ['Agriculture', '-'],
#         ['Note', '-']
#     ]


def getMitigationIntervention(village_id):
    return [
        ['Mitigation intervention'],
        ['Resilient Housing', '-'],
        ['Resilient Roads', '-'],
        ['River Bank Protection', '-'],
        ['Resilient Essential Services', '-'],
        ['Educational Facilities', '-'],
        ['Health Facilities', '-'],
        ['Public WASH Facilities and Drinking Water', '-'],
        ['Electric Facilities', '-'],
        ['Resilient Livelihood & Economic Security', '-'],
        ['Amount', '-'],
        ['Additional Support', '-']
    ]


def getDistrictLevelOfficialsData():
    return [
        ["S. No.", "Name", "Gender", "Phone Number", "Position/Responsibility"],
        ["-", "-", "-", "-", "-"],
        ["-", "-", "-", "-", "-"],
        ["-", "-", "-", "-", "-"]
    ]


def getImportantEmergencyContactData():
    return [
        ["S. No.", "Important Contact Person", "Contact Number"],
        ["-", "-", "-"],
        ["-", "-", "-"],
        ["-", "-", "-"],
        ["-", "-", "-"]
    ]


def getVillageLocationDetails():
    return [
        ["Village Location Details"],
        ["Village Name", "-"],
        ["Block", "-"],
        ["Revenue Circle", "-"],
        ["District", "-"],
        ["State", "-"],
    ]

def getVillageDemographic():
    return [
        ["Household Characteristic", "Total"],
        ["No of Males", "-"],
        ["No of Females", "-"],
        ["Total Population", "-"],
        ["Number of Households", "-"],
        ["Absentee House", "-"],
        ["Average Family Size", "-"],
        ["Male-Female Ratio", "-"]
    ]


def getSocialEconomicStatusData():
    return [
        ["Social/Economic Status Household", "AAY", "APL", "AY", "BPL", "PHH", "Total", "%"],
        ["Married Male", "-", "-", "-", "-", "-", "-", "-"],
        ["Single Man", "-", "-", "-", "-", "-", "-", "-"],
        ["Single Women", "-", "-", "-", "-", "-", "-", "-"],
        ["Widow", "-", "-", "-", "-", "-", "-", "-"],
        ["Total", "-", "-", "-", "-", "-", "-", "-"],
        ["%", "-", "-", "-", "-", "-", "-", "-"]
    ]


def getIncomeGroupData():
    return [
        ["Income Group", "No. of Household", "Percentage"],
        ["Upto 50,000", "-", "-"],
        ["Upto 1,50,000", "-", "-"],
        ["Upto 2,50,000", "-", "-"],
        ["> 2,50,000", "-", "-"],
        ["Total", "-", "-"]
    ]

def getAgricultureLandHoldingData():
    return [
        ["Agricultural land ownership (in bigha)", "< 0.5", "0.5–1.5", "1.5–2.5", "> 2.5", "Total"],
        ["Leased", "-", "-", "-", "-", "-"],
        ["% leased to total leased", "-", "-", "-", "-", "-"],
        ["Owned", "-", "-", "-", "-", "-"],
        ["% owned to total HH with own agriculture land", "-", "-", "-", "-", "-"],
        ["No land (basically manual labour)", "-", "-", "-", "-", "-"],
        ["Total", "-", "-", "-", "-", "-"]
    ]

def getAverageExpenditureBreakdownData():
    return [
        ["Expenditure", "%"],
        ["Agriculture/livestock", "-"],
        ["Festival, marriage and other social functions per year", "-"],
        ["Repair of house every year", "-"],
        ["Tobacco, liquor etc per annum", "-"],
        ["Education of children including tuition fee, books, etc.", "-"],
        ["Health related including buying medicine, hospital charges, etc.", "-"],
        ["Food and household expenditure", "-"]
    ]


def getHouseholdDebtLiabilityData():
    return [
        ["Loan Amount (INR)", "Number of HH", "%"],
        ["0", "-", "-"],
        ["<10k", "-", "-"],
        ["10–50K", "-", "-"],
        ["50–100K", "-", "-"]
    ]


def getPrimaryLivelihoodDistributionData():
    return [
      ['Livelihood','Primary economic activity'],
        ["", "No. of Household", "%"],
        ["Agriculture", "-", "-"],
        ["Fishing", "-", "-"],
        ["Livestock", "-", "-"],
        ["Manual labour", "-", "-"],
        ["No job", "-", "-"],
        ["Service", "-", "-"],
        ["Shop", "-", "-"],
        ["Total", "-", "-"]
    ]


def getCropCultivationData():
    return [
        ["Number of Crops Cultivated Every Year", "Household", "%"],
        ["One crop", "-", "-"],
        ["Two crops", "-", "-"],
        ["Three crops", "-", "-"],
        ["Total", "-", "-"]
    ]

def getRoadLengthByTypologyData():
    return [
        ["Surface Type", "Length (km)", "% to Total Road Length"],
        ["PNRD (Cement block road)", "-", "-"],
        ["PNRD (Earthen road)", "-", "-"],
        ["PWD (Bituminous road)", "-", "-"],
        ["PWD (Cement block road)", "-", "-"],
        ["Total", "-", "-"]
    ]


def getFacilityAccessData():
    return [
        ["Sr. No.","Asset Type", "Distance from Village", "Remarks"],
        ["-","-", "-", "-"],

    ]

def getLandUseClassificationData():
    return [
        ["Landuse", "Area (sqm)", "%"],
        ["Agricultural Land", "-", "-"],
        ["Fallow Land", "-", "-"],
        ["Open Land", "-", "-"],
        ["Pond/Waterbody", "-", "-"],
        ["River/Stream", "-", "-"],
        ["Roads", "-", "-"],
        ["Settlement", "-", "-"],
        ["Scrub Land", "-", "-"],
        ["Tree Clad Area", "-", "-"],
        ["Total Area", "-", "-"]
    ]


def getVulnerabilityAssessmentTableData():
    return [
        ["Vulnerability level", "Flood","", "Erosion"],
        ['','Number of HH','%','Number of HH','%'],
        ["Severe", "-", "-", "-", "-"],
        ["High", "-", "-", "-", "-"],
        ["Medium", "-", "-", "-", "-"],
        ["Low", "-", "-", "-", "-"]
    ]


def getHouseTypologyTableData():
    return [
        ["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
        ["Number of Household", "-", "-", "-", "-"],
        ["Percent %", "-", "-", "-", "-"]
    ]

def getBuildingQualityTableData():
    return [
        ["Building quality", "Number of HH", "%"],
        ["Bad", "-", "-"],
        ["Good", "-", "-"]
    ]


def getDevelopmentIssuesTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Development Issues/Needs", bold_style), Paragraph("Explanation", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getResidentialVulnerabilityTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Indicators", bold_style), Paragraph("Quantity", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getResilientHousingCostTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Housing typology", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Number", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getRoadTypologyTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Road type", bold_style), Paragraph("Total length (km)", bold_style),
         Paragraph("Severe+high flood vulnerable length (km)", bold_style), Paragraph("Severe+high erosion vulnerable length (km)", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getRoadInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Road type", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Department", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getRiverBankProtectionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("River length km needs protection", bold_style), Paragraph("Bank characteristic", bold_style),
         Paragraph("Erosion severity", bold_style), Paragraph("Remarks", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getRiverBankInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("River bank", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Department", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getEducationalFacilitiesTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Name of the facility", bold_style), Paragraph("Flood vulnerability", bold_style),
         Paragraph("Number of students", bold_style), Paragraph("Number of rooms", bold_style), Paragraph("Resilient WASH", bold_style), Paragraph("Resilient power supply", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getEducationalInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getWASHInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getElectricInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data


def getLivelihoodInterventionTable():
    data = [
        [Paragraph("S.No.", bold_style), Paragraph("Name of asset", bold_style), Paragraph("Intervention", bold_style),
         Paragraph("Quantity", bold_style), Paragraph("Unit cost in INR", bold_style), Paragraph("Total cost in INR", bold_style), Paragraph("Remarks", bold_style)],
        ['-', Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style), Paragraph("-", normal_style)]
    ]
    return data
