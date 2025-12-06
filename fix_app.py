"""
Fix app.py by removing duplicate routes
"""

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Original file: {len(lines)} lines")

# The duplicate starts at line 721 (index 720)
# Find where ADMIN CONTROL ENDPOINTS starts
admin_start = None
for i in range(720, len(lines)):
    if 'ADMIN CONTROL ENDPOINTS' in lines[i]:
        admin_start = i - 2  # Include blank lines before
        break

if admin_start:
    print(f"Found ADMIN CONTROL ENDPOINTS at line {admin_start + 1}")
    
    # Complete the incomplete function at line 718-720
    fixed_ending = [
        '    status = data.get(\'status\', \'reviewed\')\n',
        '    result = feedback_db.update_feedback_status(feedback_id, status)\n',
        '    return jsonify(result)\n',
        '\n',
        '\n'
    ]
    
    # Build the fixed file
    new_lines = []
    new_lines.extend(lines[:720])  # Everything up to line 720 (data = request.get_json())
    new_lines.extend(fixed_ending)  # Complete the function
    new_lines.extend(lines[admin_start:])  # ADMIN section to end
    
    # Write the fixed file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Fixed file: {len(new_lines)} lines")
    print(f"Removed {len(lines) - len(new_lines)} duplicate lines")
    print("SUCCESS: app.py has been fixed!")
else:
    print("ERROR: Could not find ADMIN CONTROL ENDPOINTS")
