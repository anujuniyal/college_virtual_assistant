# SQLite Commands for Your Application

## 🎯 Quick Start - Using SQLite with Your App

### **Current Status**
✅ **Database**: SQLite (`edubot_management.db`)
✅ **ORM**: SQLAlchemy (manages SQLite automatically)
✅ **Configuration**: Ready for production use

## 📋 Essential SQLite Commands

### **1. Start Application & Create Database**
```bash
# This creates the database automatically
python run_app.py

# Or create database manually
python -c "
from app.factory import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print('Database created successfully!')
"
```

### **2. Direct Database Access**
```bash
# Open SQLite database
sqlite3 edubot_management.db

# Once inside SQLite:
sqlite> .tables                    # Show all tables
sqlite> SELECT COUNT(*) FROM students;  # Count students
sqlite> SELECT * FROM students LIMIT 5;  # Show 5 students
sqlite> .quit                      # Exit
```

### **3. Python Database Operations**
```python
# Direct Python SQLite access
import sqlite3

def check_database():
    conn = sqlite3.connect('edubot_management.db')
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [table[0] for table in tables])
    
    # Count records in each table
    for table in [table[0] for table in tables]:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"{table[0]}: {count} records")
    
    conn.close()

# Run the function
check_database()
```

### **4. Real-Time Database Monitoring**
```python
# Monitor database changes in real-time
import sqlite3
import time

def monitor_database():
    conn = sqlite3.connect('edubot_management.db')
    cursor = conn.cursor()
    
    last_student_count = 0
    
    while True:
        cursor.execute("SELECT COUNT(*) FROM students")
        current_count = cursor.fetchone()[0]
        
        if current_count != last_student_count:
            print(f"Student count changed: {last_student_count} → {current_count}")
            last_student_count = current_count
        
        time.sleep(5)  # Check every 5 seconds
    
    conn.close()

# Run monitor (use Ctrl+C to stop)
# monitor_database()
```

### **5. Database Backup & Restore**
```bash
# Create backup
sqlite3 edubot_management.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Export to SQL
sqlite3 edubot_management.db ".dump > backup_$(date +%Y%m%d_%H%M%S).sql"

# Import from backup
sqlite3 new_db.db ".read backup_20240312_143022.sql"

# Check database integrity
sqlite3 edubot_management.db "PRAGMA integrity_check;"
```

### **6. Performance Optimization**
```bash
# Analyze query performance
sqlite3 edubot_management.db "EXPLAIN QUERY PLAN SELECT * FROM students;"

# Vacuum database
sqlite3 edubot_management.db "VACUUM;"

# Check database size
du -h edubot_management.db
```

## 🔧 Development Workflow

### **Daily Development Tasks**
```bash
# 1. Start application
python run_app.py

# 2. Make changes (data automatically saved to SQLite)

# 3. Test changes
curl -X POST -d "data=test" http://localhost:5000/admin/add-student

# 4. Check database
sqlite3 edubot_management.db "SELECT * FROM students ORDER BY created_at DESC LIMIT 5;"
```

### **Debugging Database Issues**
```python
# Check if database is locked
import sqlite3
try:
    conn = sqlite3.connect('edubot_management.db')
    print("Database connection successful")
except sqlite3.OperationalError as e:
    print(f"Database locked: {e}")

# Check table structure
sqlite3 edubot_management.db ".schema students"
```

## 📱 SQLite GUI Tools

### **Install Optional GUI Tools**
```bash
# SQLite Browser (recommended for development)
pip install sqlite-browser

# Run GUI
sqlite-browser edubot_management.db

# Alternative: DBeaver (free)
pip install dbeaver-sqlite
```

## 🚀 Production Deployment

### **Production Database Setup**
```bash
# Production environment
export DATABASE_URL=sqlite:///var/lib/edubot/edubot.db

# Start with production config
gunicorn -w 4 -b 0.0.0.0:5000 run_app:app

# Or with waitress (production WSGI server)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 run_app:app
```

### **Database Security**
```bash
# Set proper permissions
chmod 644 edubot_management.db
chown www-data:www-data edubot_management.db

# Enable WAL mode for better concurrency
sqlite3 edubot_management.db "PRAGMA journal_mode=WAL;"
```

## 📊 Current Database Schema

Your application uses these tables:

```sql
-- Students Table
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120),
    phone VARCHAR(15) UNIQUE,
    department VARCHAR(50),
    semester INTEGER,
    password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Faculty Table
CREATE TABLE faculty (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL,
    role VARCHAR(20) DEFAULT 'faculty',
    consultation_time VARCHAR(100),
    phone VARCHAR(15),
    password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Admin Table
CREATE TABLE admins (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 Summary

✅ **Your SQLite setup is PERFECT for development and production!**

**Key Advantages:**
- **Zero Configuration**: Works out of the box
- **Portable**: Single file database
- **Fast**: Excellent performance for your use case
- **Reliable**: No external database server needed
- **ORM Integration**: SQLAlchemy handles all SQLite operations
- **Real-time Updates**: Your dashboard refreshes every 30 seconds

**You're all set to use SQLite effectively with your College Virtual Assistant!**
