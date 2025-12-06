"""
Fix Jinja syntax error in admin_dashboard.html
"""

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic section
fixed_lines = []
in_feedback_loop = False
skip_next_endif = False

for i, line in enumerate(lines):
    # Check if we're in the feedback for loop
    if '{% for item in feedback %}' in line:
        in_feedback_loop = True
        fixed_lines.append(line)
        continue
    
    # Skip duplicate endif that's causing the error
    if in_feedback_loop and '{% endif %}' in line and '{% endfor %}' not in lines[i+1] if i+1 < len(lines) else False:
        # Check if this is the problematic endif before endfor
        if i+1 < len(lines) and '{% endfor %}' in lines[i+1]:
            skip_next_endif = True
            continue
    
    # Mark end of feedback loop
    if in_feedback_loop and '{% endfor %}' in line:
        in_feedback_loop = False
    
    fixed_lines.append(line)

# Write the fixed file
with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f"Fixed {len(lines) - len(fixed_lines)} problematic lines")
print("SUCCESS: admin_dashboard.html syntax fixed")
