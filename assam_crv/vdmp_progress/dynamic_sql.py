from vdmp_dashboard.models import AttributeMapping
from django.conf import settings
import psycopg2


def sync_attribute_texts():
    """Sync attribute texts from mobile DB to AttributeMapping table"""
  
    
    mobile_db_config = settings.DATABASES['mobile_db']
    
    with psycopg2.connect(
        host=mobile_db_config['HOST'],
        port=mobile_db_config['PORT'],
        database=mobile_db_config['NAME'],
        user=mobile_db_config['USER'],
        password=mobile_db_config['PASSWORD']
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, attribute_name FROM public.attributes ORDER BY id")
            attributes = cursor.fetchall()
            
            for attr_id, attr_name in attributes:
                AttributeMapping.objects.filter(
                    mobile_db_attribute_id=attr_id
                ).update(attribute_text=attr_name)
    
    print(f"Synced {len(attributes)} attribute texts")


def get_dynamic_sql_script(village_id, model_name='HouseholdSurvey'):
    """Generate SQL script dynamically based on AttributeMapping"""
    from vdmp_dashboard.models import AttributeMapping
    
    # Get active mappings for the model where is_calculated=False
    mappings = AttributeMapping.objects.filter(
        model_name=model_name,
        is_active=True,
        is_calculated=False
    ).values('mobile_db_attribute_id', 'attribute_text', 'alias_name', 'tab_id')
    
    if not mappings:
        raise Exception(f"No active mappings found for model {model_name}")
    
    # Get tab_id (assuming all mappings have same tab_id)
    tab_id = mappings[0]['tab_id'] or 1
    
    # Build dynamic SELECT clauses
    select_clauses = []
    for mapping in mappings:
        mobile_db_id = mapping['mobile_db_attribute_id']
        attribute_text = mapping['attribute_text']
        alias_name = mapping['alias_name']
        
        if mobile_db_id:
            if attribute_text:
                clause = f"MAX(CASE WHEN a.attribute_name ILIKE '%%{attribute_text}%%' THEN av.value END) AS {alias_name}"
            else:
                clause = f"MAX(CASE WHEN a.id = {mobile_db_id} THEN av.value END) AS {alias_name}"
            select_clauses.append(clause)
    
    dynamic_selects = ',\n        '.join(select_clauses)
    
    sql_script = f"""
    WITH media_urls AS (
        SELECT
            fd.spatial_id,
            fd.attribute_id,
            STRING_AGG(fd.media_id::text, ',' ORDER BY fd.media_id) AS media_ids_str
        FROM public.formdata fd
        JOIN public.attributes att
            ON fd.attribute_id = att.id
        WHERE att.widget_id = 10
          AND att.tab_id = {tab_id}
          AND fd.media_id IS NOT NULL
        GROUP BY fd.spatial_id, fd.attribute_id
    ),
    attribute_values AS (
        SELECT
            fd.form_id,
            fd.spatial_id,
            fd.attribute_id,
            CASE
                WHEN att.widget_id IN (2,4) THEN
                    STRING_AGG(DISTINCT ao.option_text, ', ' ORDER BY ao.option_text)
                WHEN att.widget_id = 10 THEN
                    'https://jkiofs.in/fastapi/PincerApps/images/test'
                    || COALESCE(mu.media_ids_str,'')
                    || '/' || fd.spatial_id
                ELSE MAX(fd.attribute_value)
            END AS value
        FROM public.formdata fd
        JOIN public.attributes att
            ON att.id = fd.attribute_id
        LEFT JOIN public.attributes_option ao
            ON ao.attribute_id = fd.attribute_id
           AND att.widget_id IN (2,4)
           AND ao.option_id = ANY (
                string_to_array(
                    regexp_replace(fd.attribute_value, '[^0-9,]', '', 'g'),
                    ','
                )::INT[]
           )
        LEFT JOIN media_urls mu
            ON mu.spatial_id = fd.spatial_id
           AND mu.attribute_id = fd.attribute_id
        WHERE att.tab_id = {tab_id}
          AND fd.spatial_id IN (
              SELECT id FROM public.spatialdata WHERE village_id = %s
          )
        GROUP BY
            fd.form_id,
            fd.spatial_id,
            fd.attribute_id,
            att.widget_id,
            mu.media_ids_str
    )
    SELECT
        s.survey_id,
        s.spatial_id,
        v.district_name,
        v.village_name,
        SPLIT_PART(s.geometry, ' ', 1) AS latitude,
        SPLIT_PART(s.geometry, ' ', 2) AS longitude,
        s.polygon_id AS point_id,
       
        s.unique_id,
        MIN(f.form_id) AS form_id,
        {dynamic_selects}
    FROM public.formdata f
    JOIN attribute_values av
        ON av.spatial_id = f.spatial_id
       AND av.attribute_id = f.attribute_id
    JOIN public.attributes a
        ON a.id = f.attribute_id
    JOIN public.spatialdata s
        ON s.id = f.spatial_id
    JOIN public.users u
        ON u.id = s.user_id
    JOIN public.villages v
        ON v.id = s.village_id
    WHERE a.tab_id = {tab_id}
      AND v.id = %s
    GROUP BY
        s.survey_id, s.spatial_id, v.district_name, v.village_name,
        s.geometry, s.polygon_id, s.unique_id
    ORDER BY s.survey_id
    """
    
    return sql_script, (village_id, village_id)





# def get_others_sql_script(village_id, tab_id):
#     sql = """
#     WITH media_urls AS (
#         SELECT
#             fd.spatial_id,
#             fd.attribute_id,
#             STRING_AGG(fd.media_id::text, ',' ORDER BY fd.media_id) AS media_ids_str
#         FROM public.formdata fd
#         JOIN public.attributes att ON att.id = fd.attribute_id
#         WHERE att.widget_id = 10
#           AND att.tab_id = %(tab_id)s
#           AND fd.media_id IS NOT NULL
#         GROUP BY fd.spatial_id, fd.attribute_id
#     ),
#     raw_values AS (
#         SELECT
#             fd.spatial_id,
#             fd.attribute_id,
#             fd.form_id,
#             CASE
#                 WHEN att.widget_id = 2 THEN ao.option_text
#                 WHEN att.widget_id = 10 THEN
#                     'https://jkiofs.in/fastapi/PincerApps/images/test'
#                     || COALESCE(mu.media_ids_str,'')
#                     || '/' || fd.spatial_id
#                 ELSE fd.attribute_value
#             END AS value
#         FROM public.formdata fd
#         JOIN public.attributes att ON att.id = fd.attribute_id
#         LEFT JOIN public.attributes_option ao
#             ON ao.attribute_id = fd.attribute_id
#            AND att.widget_id = 2
#            AND ao.option_id = CAST(NULLIF(regexp_replace(fd.attribute_value, '[^0-9]', '', 'g'), '') AS BIGINT)
#         LEFT JOIN media_urls mu
#             ON mu.spatial_id = fd.spatial_id
#            AND mu.attribute_id = fd.attribute_id
#         WHERE att.tab_id = %(tab_id)s
#           AND fd.spatial_id IN (
#                 SELECT id FROM public.spatialdata WHERE village_id = %(village_id)s
#           )
#     ),
#     attribute_values AS (
#         SELECT
#             spatial_id,
#             attribute_id,
#             STRING_AGG(DISTINCT value, ', ' ORDER BY value) AS value
#         FROM raw_values
#         GROUP BY spatial_id, attribute_id
#     )
#     SELECT
#         s.survey_id,
#         s.spatial_id,
#         v.district_name,
#         v.village_name,
#         SPLIT_PART(s.geometry, ' ', 1) AS latitude,
#         SPLIT_PART(s.geometry, ' ', 2) AS longitude,
#         s.polygon_id AS point_id,
#         s.unique_id,
#         MIN(rv.form_id) AS form_id,
#         MAX(CASE WHEN a.attribute_name ILIKE '%%Assets Type%%' THEN av.value END) AS assets_type,
#         MAX(CASE WHEN a.attribute_name ILIKE '%%Asset Name%%' THEN av.value END) AS asset_name,
#         MAX(CASE WHEN a.attribute_name ILIKE '%%Material%%' THEN av.value END) AS material,
#         MAX(CASE WHEN a.attribute_name ILIKE '%%Condition%%' THEN av.value END) AS condition,
#         MAX(CASE WHEN a.attribute_name ILIKE '%%Photo%%' THEN av.value END) AS photo
#     FROM raw_values rv
#     JOIN attribute_values av
#         ON av.spatial_id = rv.spatial_id
#        AND av.attribute_id = rv.attribute_id
#     JOIN public.attributes a ON a.id = rv.attribute_id
#     JOIN public.spatialdata s ON s.id = rv.spatial_id
#     JOIN public.villages v ON v.id = s.village_id
#     WHERE a.tab_id = %(tab_id)s
#       AND v.id = %(village_id)s
#     GROUP BY
#         s.survey_id, s.spatial_id,
#         v.district_name, v.village_name,
#         s.geometry, s.polygon_id, s.unique_id
#     ORDER BY s.survey_id
#     """
#     return sql, {"tab_id": tab_id, "village_id": village_id}

import re

def sanitize_alias(name):
    """Convert to safe SQL column alias"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.strip().lower())


def build_dynamic_selects_from_mappings(model_name):
    """
    Build dynamic SELECT clauses using AttributeMapping table
    """

    mappings = AttributeMapping.objects.filter(
        model_name=model_name,
        is_active=True,
        is_calculated=False
    ).values(
        'mobile_db_attribute_id',
        'attribute_text',
        'alias_name',
        'tab_id'
    )

    if not mappings:
        raise Exception(f"No active mappings found for model {model_name}")

    # All records must share same tab_id
    tab_id = 14

    select_clauses = []

    for m in mappings:
        mobile_db_id = m['mobile_db_attribute_id']
        attribute_text = m['attribute_text']
        alias_name = sanitize_alias(m['alias_name'])

        if attribute_text:
            clause = (
                f"MAX(CASE WHEN a.attribute_name ILIKE "
                f"'%%{attribute_text}%%' THEN av.value END) AS {alias_name}"
            )
        elif mobile_db_id:
            clause = (
                f"MAX(CASE WHEN a.id = {mobile_db_id} "
                f"THEN av.value END) AS {alias_name}"
            )
        else:
            continue

        select_clauses.append(clause)

    return ",\n        ".join(select_clauses)



def get_others_sql_script(village_id, model_name):
    """
    Dynamic SQL builder for Others / Transformer / Electric Pole
    """

    dynamic_selects = build_dynamic_selects_from_mappings('others')
    tab_id=14

    sql = f"""
    WITH media_urls AS (
        SELECT
            fd.spatial_id,
            fd.attribute_id,
            STRING_AGG(fd.media_id::text, ',' ORDER BY fd.media_id) AS media_ids_str
        FROM public.formdata fd
        JOIN public.attributes att ON att.id = fd.attribute_id
        WHERE att.widget_id = 10
          AND att.tab_id = %(tab_id)s
          AND fd.media_id IS NOT NULL
        GROUP BY fd.spatial_id, fd.attribute_id
    ),
    raw_values AS (
        SELECT
            fd.spatial_id,
            fd.attribute_id,
            fd.form_id,
            CASE
                WHEN att.widget_id = 2 THEN ao.option_text
                WHEN att.widget_id = 10 THEN
                    'https://jkiofs.in/fastapi/PincerApps/images/test'
                    || COALESCE(mu.media_ids_str,'')
                    || '/' || fd.spatial_id
                ELSE fd.attribute_value
            END AS value
        FROM public.formdata fd
        JOIN public.attributes att ON att.id = fd.attribute_id
        LEFT JOIN public.attributes_option ao
            ON ao.attribute_id = fd.attribute_id
           AND att.widget_id = 2
           AND ao.option_id = CAST(
                NULLIF(regexp_replace(fd.attribute_value, '[^0-9]', '', 'g'), '') AS BIGINT
           )
        LEFT JOIN media_urls mu
            ON mu.spatial_id = fd.spatial_id
           AND mu.attribute_id = fd.attribute_id
        WHERE att.tab_id = %(tab_id)s
          AND fd.spatial_id IN (
                SELECT id FROM public.spatialdata WHERE village_id = %(village_id)s
          )
    ),
    attribute_values AS (
        SELECT
            spatial_id,
            attribute_id,
            STRING_AGG(DISTINCT value, ', ' ORDER BY value) AS value
        FROM raw_values
        GROUP BY spatial_id, attribute_id
    )
    SELECT
        s.survey_id,
        s.spatial_id,
        v.district_name,
        v.village_name,
        SPLIT_PART(s.geometry, ' ', 1) AS latitude,
        SPLIT_PART(s.geometry, ' ', 2) AS longitude,
        s.polygon_id AS point_id,
        s.unique_id,
        MIN(rv.form_id) AS form_id,
        {dynamic_selects}
    FROM raw_values rv
    JOIN attribute_values av
        ON av.spatial_id = rv.spatial_id
       AND av.attribute_id = rv.attribute_id
    JOIN public.attributes a ON a.id = rv.attribute_id
    JOIN public.spatialdata s ON s.id = rv.spatial_id
    JOIN public.villages v ON v.id = s.village_id
    WHERE a.tab_id = %(tab_id)s
      AND v.id = %(village_id)s
    GROUP BY
        s.survey_id, s.spatial_id,
        v.district_name, v.village_name,
        s.geometry, s.polygon_id, s.unique_id
    ORDER BY s.survey_id
    """

    params = {
        "tab_id": tab_id,
        "village_id": village_id
    }

    return sql, params
