"""
Migration script to move data from JSON files to SQLite database
Run this script once to migrate existing data
"""

import os
import sys
import db_utils
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Run the migration from JSON to SQLite"""
    print("=" * 60)
    print("JSON to SQLite Database Migration")
    print("=" * 60)
    print()
    
    # Check if JSON files exist
    json_files = ['users.json', 'evaluation_history.json', 'feedback.json']
    existing_files = [f for f in json_files if os.path.exists(f)]
    
    if not existing_files:
        print("No JSON files found to migrate.")
        print("Database is ready to use.")
        return
    
    print(f"Found {len(existing_files)} JSON file(s) to migrate:")
    for f in existing_files:
        print(f"  - {f}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed with migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    print()
    print("Step 1: Creating backup of JSON files...")
    try:
        backup_dir, backed_up = db_utils.backup_json_files()
        if backed_up:
            print(f"✓ Backed up {len(backed_up)} file(s) to: {backup_dir}")
            for f in backed_up:
                print(f"  - {f}")
        else:
            print("No files were backed up.")
    except Exception as e:
        print(f"✗ Error creating backup: {e}")
        print("Migration cancelled for safety.")
        return
    
    print()
    print("Step 2: Migrating data to SQLite database...")
    try:
        migrated = db_utils.migrate_from_json()
        print("✓ Migration completed successfully!")
        print(f"  - Users migrated: {migrated['users']}")
        print(f"  - Evaluations migrated: {migrated['evaluations']}")
        print(f"  - Feedback entries migrated: {migrated['feedback']}")
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        print("Please check the logs and backup files.")
        return
    
    print()
    print("=" * 60)
    print("Migration Summary:")
    print("=" * 60)
    print(f"Database file: {db_utils.DB_FILE}")
    print(f"Backup location: {backup_dir}")
    print()
    print("Next steps:")
    print("1. Test your application to ensure everything works correctly")
    print("2. If everything works, you can archive or delete the JSON files")
    print("3. Keep the backup folder safe until you're confident in the migration")
    print()
    print("The application will now use SQLite database for all operations.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        logging.exception("Migration failed with exception")
        sys.exit(1)
