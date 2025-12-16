from django.shortcuts import render, redirect
from training.models import tbl_Training_Activities
from rescue_equipment.models import tbl_Rescue_Equipment, tbl_Rescue_Equipment_Status
from django.utils.translation import get_language
from accounts.models import tblRoles, tblDepartment, tblModule
from village_profile.models import tblDistrict
from vdmp_progress.models import tblVDMP_Activity
from utils import is_admin_or_superuser
from django.contrib.auth.decorators import  user_passes_test
from django.db.models import F

from django.db.models.functions import Cast
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
import pandas as pd
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from utils import TRAINING_MASTER_LIST,RESCUE_EQUEP_MASTER_LIST,VDMP_ACTIVITIES



def administrator_home_view(request):
    """Renders the administrator dashboard page.
    This is the home view for administrators."""
    return render(request, 'administrator/dashboard.html')





def admin_get_training_activities(request):
    """Fetches and displays training activities.
    Activity names are shown in the current selected language."""
    lang = get_language()

    field_name = f"name_{lang}"
    name_field = field_name if hasattr(tbl_Training_Activities, field_name) else "name"

    activities = tbl_Training_Activities.objects.all()
    activity_list = []
    for activity in activities:
        name = getattr(activity, name_field) or activity.name  
        activity_list.append({
            'id': activity.id,
            'name': name,
            'name_en': activity.name,
            'name_bn': activity.name_bn,
            'name_as': activity.name_as,
        })

    return render(request, 'administrator/training/training_data.html', {'activities': activity_list})


def get_rescue_equipment(request):
    """
    Displays the rescue equipment data with translations.
    Language-specific fields are rendered based on selected locale.
    """
    lang = get_language()

    def localized_field(model, base_field):
        field_name = f"{base_field}_{lang}"
        return field_name if hasattr(model, field_name) else base_field

    name_field = localized_field(tbl_Rescue_Equipment, 'name')
    task_force_field = localized_field(tbl_Rescue_Equipment, 'task_force')
    specification_field = localized_field(tbl_Rescue_Equipment, 'specification')

    equipments = tbl_Rescue_Equipment.objects.annotate(
        custom_name=F(name_field),
        custom_task_force=F(task_force_field),
        custom_specification=F(specification_field)
    )

    rescue_equipment_list = tbl_Rescue_Equipment_Status.objects.all()

    context = {
        'equipments': equipments,
        'rescue_equipment_list': rescue_equipment_list
    }
    return render(request, 'administrator/rescue_equipments/rescue_equipments.html', context)


@user_passes_test(is_admin_or_superuser)
def get_users_list(request):
    """Fetches and displays list of users, roles, and departments.
    Only accessible by admin or superuser."""
    all_roles = tblRoles.objects.all()
    all_departments = tblDepartment.objects.all()
    context = {
        'roles': all_roles,
        'departments': all_departments,
    }
    return render(request, 'administrator/users/users_data.html', context)


def admin_get_roles_list(request):
    """Displays the list of user roles.
    Supports multi-language role name display."""
    lang = get_language()
    all_roles = tblRoles.objects.all()
    return render(request, 'administrator/users/roles.html', {'roles': all_roles})


def get_village_profile(request):
    """Displays village profile selection page.
    Lists all available districts for selection."""
    districts = tblDistrict.objects.all()
    return render(request, 'administrator/village_profile/village_profile.html', {'districts': districts})


@user_passes_test(is_admin_or_superuser)
def get_department_list(request):
    """Shows departments along with linked modules.
    Only accessible by admin or superuser users."""
    modules = list(tblModule.objects.values('id', 'name')) 
    context = {
        'modules': modules,
    }
    return render(request, 'administrator/users/department.html', context)


def get_vdmp_dashboard(request):
    """Renders the VDMP dashboard interface.
    This view loads the VDMP monitoring dashboard."""
    return render(request, 'administrator/vdmp_dashboard/vdmp_dashboard.html')



def get_vdmp_progres_dashboard(request):
    """Renders the VDMP dashboard interface with language-specific custom_name field."""
    lang = get_language()
    dynamic_field = f"name_{lang}"

    # Fallback to 'name' if dynamic field does not exist in the model
    name_field = dynamic_field if hasattr(tblVDMP_Activity, dynamic_field) else 'name'

    vdmp_progress = tblVDMP_Activity.objects.annotate(
        custom_name=F(name_field)
    )

    return render(
        request,
        'administrator/vdmp_progress/vdmp_progress_admin.html',
        {'vdmp_progress': vdmp_progress}
    )


# MASTER Data update using excel sheet - Fixed Encoding Issues

import pandas as pd
import chardet
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

def process_training_activity(data, index):
    name = data.get('name', '').strip()
    if not name:
        return None, f"Row {index+2}: Missing name"
    
    obj, is_created = tbl_Training_Activities.objects.get_or_create(
        name=name,
        defaults={'name_bn': data.get('name_bn', ''), 'name_as': data.get('name_as', '')}
    )
    
    if is_created:
        return 'created', None
    elif obj.name_bn != data.get('name_bn', '') or obj.name_as != data.get('name_as', ''):
        obj.name_bn = data.get('name_bn', '')
        obj.name_as = data.get('name_as', '')
        obj.save()
        return 'updated', None
    return 'unchanged', None

def process_rescue_equipment(data, index):
    name = data.get('name', '').strip()
    if not name:
        return None, f"Row {index+2}: Missing name"
    
    obj, is_created = tbl_Rescue_Equipment.objects.get_or_create(
        name=name,
        defaults={
            'name_bn': data.get('name_bn', ''), 'name_as': data.get('name_as', ''),
            'task_force': data.get('task_force', ''), 'task_force_bn': data.get('task_force_bn', ''), 'task_force_as': data.get('task_force_as', ''),
            'specification': data.get('specification', ''), 'specification_bn': data.get('specification_bn', ''), 'specification_as': data.get('specification_as', '')
        }
    )
    
    if is_created:
        return 'created', None
    
    fields = [('name_bn', data.get('name_bn', '')), ('name_as', data.get('name_as', '')), ('task_force', data.get('task_force', '')), 
              ('task_force_bn', data.get('task_force_bn', '')), ('task_force_as', data.get('task_force_as', '')), 
              ('specification', data.get('specification', '')), ('specification_bn', data.get('specification_bn', '')), ('specification_as', data.get('specification_as', ''))]
    
    updated = False
    for field_name, new_value in fields:
        if getattr(obj, field_name) != new_value:
            setattr(obj, field_name, new_value)
            updated = True
    
    if updated:
        obj.save()
        return 'updated', None
    return 'unchanged', None

def process_vdmp_activity(data, index):
    name = data.get('name', '').strip()
    if not name:
        return None, f"Row {index+2}: Missing name"
    
    obj, is_created = tblVDMP_Activity.objects.get_or_create(
        name=name,
        defaults={
            'name_bn': data.get('name_bn', ''), 
            'name_as': data.get('name_as', ''),
            'order': data.get('order')
        }
    )
    
    if is_created:
        return 'created', None
    elif (obj.name_bn != data.get('name_bn', '') or 
          obj.name_as != data.get('name_as', '') or 
          obj.order != data.get('order')):
        obj.name_bn = data.get('name_bn', '')
        obj.name_as = data.get('name_as', '')
        obj.order = data.get('order')
        obj.save()
        return 'updated', None
    return 'unchanged', None

def detect_file_encoding(file):
    """Detect the encoding of uploaded file"""
    try:
        # Read a sample of the file for encoding detection
        file.seek(0)
        sample = file.read(10000)
        file.seek(0)  # Reset file pointer
        
        result = chardet.detect(sample)
        return result.get('encoding', 'utf-8')
    except:
        return 'utf-8'

@login_required
@require_POST
def upload_master_data(request):
    file = request.FILES.get("file")
    data_type = request.POST.get("data_type")

    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        # Detect encoding for better text handling
        detected_encoding = detect_file_encoding(file)
        print(f"Detected encoding: {detected_encoding}")
        
        # Check if file encoding is UTF-8-SIG
        if detected_encoding != 'UTF-8-SIG':
            return JsonResponse({"error": "File encoding must be UTF-8-SIG. Please save your Excel file as CSV UTF-8 (Comma delimited) format."}, status=400)
        
        if file.name.endswith(".csv"):
            # Try multiple encodings for CSV files
            encodings_to_try = [detected_encoding, 'utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings_to_try:
                try:
                    file.seek(0)  # Reset file pointer
                    df = pd.read_csv(file, encoding=encoding)
                    print(f"Successfully read CSV with encoding: {encoding}")
                    break
                except (UnicodeDecodeError, UnicodeError) as e:
                    print(f"Failed to read with encoding {encoding}: {e}")
                    continue
            
            if df is None:
                return JsonResponse({"error": "Could not read CSV file with any supported encoding"}, status=400)
                
        elif file.name.endswith((".xls", ".xlsx")):
            # Excel files usually handle encoding automatically
            file.seek(0)
            df = pd.read_excel(file, engine='openpyxl')
        else:
            return JsonResponse({"error": "Unsupported file format. Please upload .xls, .xlsx, or .csv files."}, status=400)

        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Debug: Print first few rows to check encoding
        print("DataFrame columns:", df.columns.tolist())
        print("First row sample:")
        if not df.empty:
            for col in df.columns:
                sample_value = df.iloc[0][col] if not pd.isna(df.iloc[0][col]) else 'NaN'
                print(f"  {col}: {sample_value} (type: {type(sample_value)})")

    except Exception as e:
        return JsonResponse({"error": f"Failed to read file: {str(e)}"}, status=400)

    PROCESSORS = {
        "training_activity_master": (TRAINING_MASTER_LIST, process_training_activity),
        "rescue_equipment_master": (RESCUE_EQUEP_MASTER_LIST, process_rescue_equipment),
        "vdmp_activity_master": (VDMP_ACTIVITIES, process_vdmp_activity)
    }
    
    if data_type not in PROCESSORS:
        return JsonResponse({"error": f"Invalid data_type. Must be one of: {list(PROCESSORS.keys())}."}, status=400)

    mapping, processor = PROCESSORS[data_type]
    created = 0
    updated = 0
    failed = []

    for index, row in df.iterrows():
        print(f"Processing row {index+1}:")
        try:
            data = {}
            for excel_field, model_field in mapping.items():
                raw_value = row.get(excel_field, '')
                
                # Handle NaN values and convert to string properly
                if pd.isna(raw_value):
                    value = ''
                else:
                    # Ensure proper string conversion for Unicode text
                    if isinstance(raw_value, (int, float)):
                        value = str(raw_value).strip()
                    else:
                        # For text data, ensure it's properly encoded
                        value = str(raw_value).strip()
                        
                data[model_field] = value
                print(f"  {excel_field} -> {model_field}: '{value}' (len: {len(value)})")

            result, error = processor(data, index)
            
            if error:
                failed.append(error)
            elif result == 'created':
                created += 1
            elif result == 'updated':
                updated += 1

        except Exception as e:
            error_msg = f"Row {index+2}: {str(e)}"
            print(f"Error processing row {index+2}: {e}")
            failed.append(error_msg)

    return JsonResponse({
        "status": "success",
        "records_created": created,
        "records_updated": updated,
        "errors": failed
    })

# Additional helper functions for better file handling

def clean_unicode_text(text):
    """Clean and normalize Unicode text"""
    if not text or pd.isna(text):
        return ''
    
    # Convert to string and strip
    text = str(text).strip()
    
    # Remove any BOM characters
    text = text.replace('\ufeff', '')
    
    # Normalize Unicode text (optional)
    import unicodedata
    text = unicodedata.normalize('NFC', text)
    
    return text

def validate_file_before_processing(file):
    """Validate file content before processing"""
    try:
        # Check file size (optional)
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            return False, "File too large. Maximum size is 50MB."
        
        # Check if file is not empty
        if file.size == 0:
            return False, "File is empty."
        
        return True, None
    except Exception as e:
        return False, f"File validation error: {str(e)}"