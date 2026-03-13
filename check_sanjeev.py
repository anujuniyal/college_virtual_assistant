import sqlite3

# Check both database files
for db_file in ['college_assistant.db', 'edubot_management.db']:
    print(f'\n=== Checking {db_file} ===')
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print('Tables:', [t[0] for t in tables])
        
        # Check for Sanjeev in each table
        for table in ['students', 'faculty', 'admins']:
            if table in [t[0] for t in tables]:
                try:
                    if table == 'students':
                        cursor.execute("SELECT name, roll_number, phone FROM students WHERE name LIKE ?", ('%sanjeev%',))
                    elif table == 'faculty':
                        cursor.execute("SELECT name, email FROM faculty WHERE name LIKE ?", ('%sanjeev%',))
                    elif table == 'admins':
                        cursor.execute("SELECT username, email FROM admins WHERE username LIKE ?", ('%sanjeev%',))
                    
                    results = cursor.fetchall()
                    if results:
                        print(f'{table.capitalize()} named Sanjeev:')
                        for result in results:
                            print(f'  - {result[0]} ({result[1]})')
                    else:
                        print(f'No {table} named Sanjeev found')
                except Exception as e:
                    print(f'Error checking {table}: {e}')
        
        conn.close()
    except Exception as e:
        print(f'Error with {db_file}: {e}')
