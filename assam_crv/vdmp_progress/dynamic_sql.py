def sync_attribute_texts():
    """Sync attribute texts from mobile DB to AttributeMapping table"""
    from vdmp_dashboard.models import AttributeMapping
    from django.conf import settings
    import psycopg2
    
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