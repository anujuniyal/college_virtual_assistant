# Database Setup Guide

This guide explains how to set up your application with dual database support (SQLite for local development, PostgreSQL for production).

## Overview

The application automatically switches between SQLite and PostgreSQL based on environment variables:

- **Local Development**: Uses SQLite (`edubot_management.db`)
- **Production (Render)**: Uses PostgreSQL (provided by Render)

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python database_manager.py init
```

3. Run the application:
```bash
python run_app.py
```

### Production Deployment (Render)

1. Deploy to Render - the `render.yaml` configuration will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Initialize the database schema
   - Start the application

## Database Management Tools

### database_manager.py

A comprehensive tool for managing your database:

```bash
# Initialize database (creates schema and default data)
python database_manager.py init

# Test database connection
python database_manager.py test

# Show database information
python database_manager.py info

# Backup SQLite database
python database_manager.py backup

# Migrate from SQLite to PostgreSQL
python database_manager.py migrate
```

### migrate_to_postgresql.py

Interactive migration tool for moving from SQLite to PostgreSQL:

```bash
python migrate_to_postgresql.py
```

This tool will:
- Check dependencies (psycopg2-binary)
- Verify SQLite database exists
- Prompt for PostgreSQL connection details
- Create a backup of your SQLite data
- Migrate all data to PostgreSQL
- Verify the migration was successful

## Environment Variables

The application uses these environment variables to determine database configuration:

### Required for Production
- `DATABASE_URL`: PostgreSQL connection string (automatically set by Render)
- `FLASK_ENV`: Set to `production` (automatically set by render.yaml)

### Optional
- `POSTGRESQL_URL`: Alternative PostgreSQL URL if DATABASE_URL is not set
- `SECRET_KEY`: Application secret key
- `DEFAULT_ADMIN_*`: Default admin user credentials

## Database Switching Logic

The configuration in `app/config.py` automatically determines the database:

1. **If `DATABASE_URL` is set** → Use PostgreSQL (Render deployment)
2. **If `FLASK_ENV=production` and `POSTGRESQL_URL` is set** → Use PostgreSQL
3. **Otherwise** → Use SQLite (local development)

## Migration Process

### From Local SQLite to Production PostgreSQL

1. **Before deploying**, migrate your local data:
```bash
python migrate_to_postgresql.py
```

2. **Deploy to Render** - the migrated data will be available in production.

### Manual Migration Steps

If you prefer manual migration:

1. **Set up PostgreSQL database** (on Render or local)
2. **Get connection string**:
   - Render: Automatically provided as `DATABASE_URL`
   - Local: `postgresql://username:password@localhost:5432/database_name`
3. **Run migration**:
```bash
DATABASE_URL="your_connection_string" python database_manager.py migrate
```

## Troubleshooting

### Common Issues

1. **"Authentication failed on Render"**
   - Cause: Database not properly initialized
   - Solution: Ensure `preDeployCommand` runs in render.yaml

2. **"No DATABASE_URL found"**
   - Cause: PostgreSQL database not created on Render
   - Solution: Check Render dashboard for database service

3. **"psycopg2 not installed"**
   - Cause: Missing PostgreSQL dependency
   - Solution: `pip install psycopg2-binary`

4. **Migration fails**
   - Cause: Connection issues or permissions
   - Solution: Check PostgreSQL connection details and permissions

### Debug Commands

```bash
# Check current database configuration
python database_manager.py info

# Test database connection
python database_manager.py test

# Check environment variables
python -c "import os; print('DATABASE_URL:', os.environ.get('DATABASE_URL'))"
```

## File Structure

```
├── app/
│   └── config.py              # Database switching logic
├── database_manager.py        # Database management tool
├── migrate_to_postgresql.py   # Migration script
├── render.yaml               # Render deployment configuration
├── requirements.txt          # Includes psycopg2-binary
└── edubot_management.db      # SQLite database (local only)
```

## Best Practices

1. **Always backup before migration**: The migration tools create automatic backups
2. **Test locally first**: Use a local PostgreSQL instance to test migration
3. **Keep requirements updated**: Ensure psycopg2-binary is included
4. **Monitor logs**: Check Render logs for database initialization messages
5. **Use environment variables**: Never hardcode database credentials

## Production Considerations

1. **Database Backups**: Render provides automatic PostgreSQL backups
2. **Connection Pooling**: Consider using connection pooling for high traffic
3. **Security**: Use Render's built-in SSL connections
4. **Monitoring**: Monitor database connection health via `/health` endpoint

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Render logs for deployment errors
3. Verify environment variables are set correctly
4. Test with the provided database management tools
