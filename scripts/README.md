# Scripts Directory

This directory contains various utility and deployment scripts organized by category.

## Directory Structure

### 📁 database/
Database-related scripts for setup, migration, and management.

- `database_manager.py` - Database management utilities
- `migrate_to_postgresql.py` - Migration script from SQLite to PostgreSQL
- `setup_database.py` - Initial database setup script
- `setup_database_complete.py` - Complete database setup with all tables and data

### 📁 bot/
Telegram bot related scripts.

- `run_telegram_bot.py` - Main Telegram bot runner
- `run_telegram_bot_polling.py` - Telegram bot with polling mechanism

### 📁 deployment/
Deployment and application startup scripts.

- `run_app.py` - Main application runner
- `start.bat` - Windows batch file to start the application
- `start.sh` - Unix shell script to start the application

## Usage

### Database Scripts
```bash
# Setup database
python scripts/database/setup_database.py

# Migrate to PostgreSQL
python scripts/database/migrate_to_postgresql.py
```

### Bot Scripts
```bash
# Run Telegram bot
python scripts/bot/run_telegram_bot.py

# Run with polling
python scripts/bot/run_telegram_bot_polling.py
```

### Deployment Scripts
```bash
# Run the main application
python scripts/deployment/run_app.py

# Or use the platform-specific scripts
./scripts/deployment/start.sh    # Unix/Linux
scripts\deployment\start.bat     # Windows
```

## Notes

- All scripts are organized by functionality for better maintainability
- Database scripts should be run with appropriate permissions
- Bot scripts require valid Telegram bot tokens
- Deployment scripts are configured for production use
