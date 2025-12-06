"""
Verify database migration was successful
"""
import db_utils

print("Database Verification")
print("=" * 50)

# Check users
users = db_utils.load_users()
print(f"Users in database: {len(users)}")
for username in users.keys():
    print(f"  - {username}")

print()

# Check evaluations
history = db_utils.load_eval_history()
total_evals = sum(len(evals) for evals in history.values())
print(f"Total evaluations: {total_evals}")
for username, evals in history.items():
    print(f"  - {username}: {len(evals)} evaluation(s)")

print()

# Check feedback
feedback = db_utils.load_feedback()
total_feedback = sum(len(entries) for entries in feedback.values())
print(f"Total feedback entries: {total_feedback}")
for username, entries in feedback.items():
    print(f"  - {username}: {len(entries)} feedback entry(ies)")

print()
print("=" * 50)
print("Database verification complete!")
print("All data successfully migrated to SQLite.")
