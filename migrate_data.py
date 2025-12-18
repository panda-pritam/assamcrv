import psycopg2
import sys

# Source database config
SOURCE_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'crv_assam',
    'user': 'postgres',
    'password': 'admin'
}

# Target database config
TARGET_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'assam_crv_new',
    'user': 'postgres',
    'password': 'admin'
}

def get_tables(conn):
    """Get all table names from public schema"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    return [row[0] for row in cursor.fetchall()]

def migrate_data():
    try:
        # Connect to source database
        source_conn = psycopg2.connect(**SOURCE_CONFIG)
        print(f"Connected to source database: {SOURCE_CONFIG['database']}")
        
        # Connect to target database
        target_conn = psycopg2.connect(**TARGET_CONFIG)
        print(f"Connected to target database: {TARGET_CONFIG['database']}")
        
        # Create crv schema if not exists
        target_cursor = target_conn.cursor()
        target_cursor.execute("CREATE SCHEMA IF NOT EXISTS crv")
        target_conn.commit()
        print("Created/verified crv schema")
        
        # Disable foreign key checks
        target_cursor.execute("SET session_replication_role = replica")
        target_conn.commit()
        
        # Get all tables from source
        tables = get_tables(source_conn)
        print(f"Found {len(tables)} tables to migrate")
        
        for table in tables:
            print(f"Migrating table: {table}")
            
            # Get table structure
            source_cursor = source_conn.cursor()
            source_cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            columns = [desc[0] for desc in source_cursor.description]
            
            # Use pg_dump to get exact table structure
            import subprocess
            try:
                dump_cmd = f'pg_dump -h {SOURCE_CONFIG["host"]} -p {SOURCE_CONFIG["port"]} -U {SOURCE_CONFIG["user"]} -d {SOURCE_CONFIG["database"]} -t {table} --schema-only --no-owner --no-privileges'
                result = subprocess.run(dump_cmd, shell=True, capture_output=True, text=True, env={'PGPASSWORD': SOURCE_CONFIG['password']})
                
                if result.returncode == 0:
                    # Modify the SQL to use crv schema
                    create_sql = result.stdout.replace(f'CREATE TABLE public.{table}', f'CREATE TABLE IF NOT EXISTS crv.{table}')
                    # Remove any schema references
                    create_sql = create_sql.replace('public.', 'crv.')
                    target_cursor.execute(create_sql)
                else:
                    print(f"  Skipping {table} - could not get structure")
                    continue
            except Exception as e:
                print(f"  Skipping {table} - error: {e}")
                continue
            
            # Clear existing data
            try:
                target_cursor.execute(f"DELETE FROM crv.{table}")
            except:
                pass
            
            # Copy data
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()
            
            if rows:
                placeholders = ','.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO crv.{table} ({','.join(columns)}) VALUES ({placeholders})"
                target_cursor.executemany(insert_sql, rows)
                print(f"  Copied {len(rows)} rows")
            
            target_conn.commit()
        
        # Re-enable foreign key checks
        target_cursor.execute("SET session_replication_role = DEFAULT")
        target_conn.commit()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()

if __name__ == "__main__":
    migrate_data()