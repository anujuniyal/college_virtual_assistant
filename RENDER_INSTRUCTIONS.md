# Render Database Migration Instructions

## Issue
Your bot is still getting database field length errors because the migration wasn't applied to the Render production database.

## Quick Fix - Run on Render

### Method 1: Render Shell (Recommended)
1. Go to your Render dashboard
2. Select your service
3. Click **"Shell"** tab
4. Run this command:
```bash
python RENDER_MIGRATION_FIX.py
```

### Method 2: Manual SQL
If the script doesn't work, run these SQL commands in Render Shell:

```bash
python -c "
from app.extensions import db
from app import create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE students ALTER COLUMN phone TYPE VARCHAR(20);'))
        db.session.execute(text('ALTER TABLE student_registrations ALTER COLUMN phone TYPE VARCHAR(20);'))
        db.session.execute(text('ALTER TABLE visitor_queries ALTER COLUMN phone_number TYPE VARCHAR(20);'))
        db.session.commit()
        print('Migration completed!')
    except Exception as e:
        print(f'Error: {e}')
        db.session.rollback()
"
```

## Verification
After running the migration, test your bot:
1. Send `register EDU2025001` to your bot
2. Should work without database errors

## Alternative: Restart Service
If migration fails, try:
1. **Manual Deploy** in Render dashboard
2. **Deploy Latest Commit**
3. Then run migration again

## Expected Result
Bot should handle roll number registration without field length errors.
