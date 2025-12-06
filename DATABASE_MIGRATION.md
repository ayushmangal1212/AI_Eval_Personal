# SQLite Database Migration Guide

## Overview

The AI Evaluation System has been migrated from JSON file storage to SQLite database for better performance, data integrity, and scalability.

## Database Schema

### Tables

#### 1. **users**
Stores user account information
- `username` (TEXT, PRIMARY KEY)
- `name` (TEXT)
- `email` (TEXT)
- `experience` (TEXT)
- `password` (TEXT) - hashed password
- `created_at` (TEXT) - timestamp
- `eval_chances` (TEXT) - JSON string of role-specific attempt limits
- `eval_taken_counts` (TEXT) - JSON string of attempts used per role

#### 2. **evaluations**
Stores evaluation results and history
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `username` (TEXT, FOREIGN KEY)
- `date` (TEXT) - timestamp
- `role` (TEXT) - evaluated role
- `score` (INTEGER) - total score achieved
- `max_score` (INTEGER) - maximum possible score
- `percentage` (REAL) - percentage score
- `time_taken` (REAL) - time in seconds
- `qa_history` (TEXT) - JSON array of Q&A pairs with scores and feedback

#### 3. **feedback**
Stores user feedback submissions
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `username` (TEXT, FOREIGN KEY)
- `date` (TEXT) - timestamp
- `role` (TEXT) - related role (optional)
- `skills` (TEXT) - JSON array of skills
- `message` (TEXT) - feedback message
- `resolved` (INTEGER) - 0/1 boolean flag
- `admin_comment` (TEXT) - admin response (optional)

## Migration Process

### Step 1: Backup Existing Data

Before migration, your existing JSON files will be automatically backed up to a timestamped folder:
```
json_backup_YYYYMMDD_HHMMSS/
├── users.json
├── evaluation_history.json
└── feedback.json
```

### Step 2: Run Migration Script

Execute the migration script to transfer data from JSON to SQLite:

```powershell
python migrate_to_db.py
```

The script will:
1. Check for existing JSON files
2. Create a backup of all JSON files
3. Initialize the SQLite database with proper schema
4. Import all data from JSON files to database tables
5. Display a summary of migrated records

### Step 3: Verify Migration

After migration:
1. Run your application: `streamlit run eval.py`
2. Test login functionality
3. Check evaluation history displays correctly
4. Verify admin console functions properly
5. Test creating new users and evaluations

## Database File

The SQLite database is stored as:
```
evaluation_system.db
```

## API Compatibility

The database module (`db_utils.py`) maintains the same API as the original JSON functions:

- `load_users()` → Returns dict of all users
- `save_users(users)` → Saves users dict to database
- `load_eval_history()` → Returns dict of evaluation history
- `save_eval_history(history)` → Saves evaluation history
- `load_feedback()` → Returns dict of feedback entries
- `save_feedback(feedback)` → Saves feedback entries
- `save_evaluation_result(username, eval_data)` → Saves single evaluation
- `add_feedback_entry(username, message, role, skills)` → Adds single feedback

## Benefits of SQLite Migration

1. **Performance**: Faster queries with indexed lookups
2. **Data Integrity**: ACID compliance, foreign key constraints
3. **Scalability**: Better handling of large datasets
4. **Concurrent Access**: Better support for multiple users
5. **Data Safety**: Reduced risk of file corruption
6. **Query Capabilities**: SQL queries for advanced reporting
7. **Backup**: Single file backup instead of multiple JSON files

## Rollback

If you need to rollback to JSON files:
1. Stop the application
2. Restore JSON files from the backup folder
3. Remove or rename `db_utils.py`
4. Revert the import statements in eval.py, eval_new.py, eval3pm.py
5. Restore the original `load_users()`, `save_users()`, etc. functions

## Database Management

### View Database Contents

You can use any SQLite client to view/query the database:

```powershell
# Using sqlite3 command-line tool
sqlite3 evaluation_system.db

# Example queries
SELECT COUNT(*) FROM users;
SELECT username, name, email FROM users;
SELECT username, date, role, score, percentage FROM evaluations ORDER BY date DESC;
SELECT username, date, message, resolved FROM feedback WHERE resolved = 0;
```

### Export Data

The admin console still provides CSV export functionality for evaluations.

## Troubleshooting

### Migration Issues

If migration fails:
1. Check the console output for error messages
2. Ensure JSON files are not corrupted
3. Check file permissions
4. Review logs for detailed error information
5. Restore from backup if needed

### Database Locked Error

If you see "database is locked":
1. Ensure no other processes are accessing the database
2. Close all Streamlit sessions
3. Restart the application

### Performance Issues

If database queries are slow:
1. Check database file size
2. Consider adding more indexes for frequently queried columns
3. Use `VACUUM` command to optimize database

```sql
VACUUM;
```

## Security Notes

1. The database file should have appropriate file permissions
2. Password hashes are stored using SHA256 (same as JSON version)
3. Consider encrypting the database file for production use
4. Regular backups are recommended

## Maintenance

### Regular Backups

Create regular backups of the database:

```powershell
# Simple file copy
Copy-Item evaluation_system.db "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### Database Cleanup

Periodically check for orphaned records or data integrity issues using SQLite tools.

## Support

For issues or questions about the database migration:
1. Check the logs in the application
2. Review this documentation
3. Contact the system administrator
4. Check SQLite documentation: https://www.sqlite.org/docs.html
