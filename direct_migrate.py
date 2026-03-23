import sqlite3
import psycopg2
import os
from datetime import datetime

def convert_sqlite_type_to_postgresql(sqlite_type):
    """Convert SQLite data types to PostgreSQL types"""
    sqlite_type = sqlite_type.upper()
    
    if 'INTEGER' in sqlite_type and 'PRIMARY KEY' in sqlite_type:
        return 'SERIAL PRIMARY KEY'
    elif 'INTEGER' in sqlite_type:
        return 'INTEGER'
    elif 'TEXT' in sqlite_type or 'VARCHAR' in sqlite_type:
        return 'TEXT'
    elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
        return 'REAL'
    elif 'BOOLEAN' in sqlite_type:
        return 'BOOLEAN'
    elif 'DATETIME' in sqlite_type:
        return 'TIMESTAMP'
    elif 'BLOB' in sqlite_type:
        return 'BYTEA'
    else:
        return 'TEXT'

def migrate_data():
    """Migrate SQLite data to PostgreSQL"""
    print("🚀 Direct SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # SQLite database
    sqlite_path = 'edubot_management.db'
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found!")
        return False
    
    # PostgreSQL connection
    pg_host = "dpg-d6q7g53uibrs73a4irpg-a.oregon-postgres.render.com"
    pg_port = "5432"
    pg_db = "anuj_uniyal"
    pg_user = "anuj_uniyal_user"
    pg_password = "ZjJ9nl5VrY2bjdMd0Tc2IgyDJGjArA8s"
    
    connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    
    try:
        print("🔍 Connecting to PostgreSQL...")
        pg_conn = psycopg2.connect(connection_string)
        pg_cursor = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
        
        print("🔍 Connecting to SQLite...")
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        print("✅ Connected to SQLite")
        
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables to migrate")
        
        migrated_tables = 0
        total_records = 0
        
        for table_name, in tables:
            if table_name == 'sqlite_sequence':
                continue  # Skip SQLite internal table
            
            try:
                print(f"🔄 Migrating table: {table_name}")
                
                # Drop table if exists in PostgreSQL
                pg_cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                
                # Get table schema from SQLite
                sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
                columns = sqlite_cursor.fetchall()
                
                # Create table in PostgreSQL
                column_defs = []
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    pg_type = convert_sqlite_type_to_postgresql(col_type)
                    col_def = f'"{col_name}" {pg_type}'
                    if not_null:
                        col_def += " NOT NULL"
                    if default_val and default_val != 'None':
                        if default_val == 'CURRENT_TIMESTAMP':
                            col_def += " DEFAULT CURRENT_TIMESTAMP"
                        elif col_type.upper() == 'BOOLEAN' and default_val in ['0', '1']:
                            # Convert integer defaults for boolean columns
                            bool_default = 'TRUE' if default_val == '1' else 'FALSE'
                            col_def += f" DEFAULT {bool_default}"
                        else:
                            col_def += f" DEFAULT {default_val}"
                    if pk:
                        col_def += " PRIMARY KEY"
                    column_defs.append(col_def)
                
                create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
                pg_cursor.execute(create_table_sql)
                
                # Get data from SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                rows = sqlite_cursor.fetchall()
                
                if rows:
                    # Get column names from the schema info
                    column_names = [f'"{col[1]}"' for col in columns]  # col[1] is the column name
                    placeholders = ', '.join(['%s'] * len(column_names))
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                    
                    # Convert data types for PostgreSQL compatibility
                    converted_rows = []
                    for row in rows:
                        converted_row = []
                        for i, value in enumerate(row):
                            col_info = columns[i]
                            col_type = col_info[2].upper()
                            if col_type == 'BOOLEAN' and value in [0, 1]:
                                # Convert integer boolean to PostgreSQL boolean
                                converted_row.append(bool(value))
                            else:
                                converted_row.append(value)
                        converted_rows.append(tuple(converted_row))
                    
                    # Insert data into PostgreSQL
                    pg_cursor.executemany(insert_sql, converted_rows)
                    total_records += len(rows)
                
                migrated_tables += 1
                print(f"✅ Migrated {len(rows)} rows from {table_name}")
                
            except Exception as e:
                print(f"⚠️  Error migrating table {table_name}: {str(e)}")
                continue
        
        # Commit changes
        pg_conn.commit()
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"   Tables migrated: {migrated_tables}/{len(tables)}")
        print(f"   Total records: {total_records}")
        print(f"   Your data is now available on PostgreSQL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    migrate_data()
