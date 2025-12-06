"""
Quick fix for admin_dashboard.html feedback section
"""

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic feedback loop
old_code = """{% for item in feedback %}
                        <tr style="border-bottom: 1px solid var(--glass-border);">
                            <td style="padding: 1rem;"><strong>{{ item.username }}</strong></td>
                            <td style="padding: 1rem;">{{ item.question[:50] }}...</td>
                            <td style="padding: 1rem;">{{ item.ai_score }}/20</td>
                            <td style="padding: 1rem;">{{ item.expected_score }}/20</td>"""

new_code = """{% for item in feedback %}
                        {% if item is mapping %}
                        <tr style="border-bottom: 1px solid var(--glass-border);">
                            <td style="padding: 1rem;"><strong>{{ item.get('username', 'N/A') }}</strong></td>
                            <td style="padding: 1rem;">{{ (item.get('question_text', 'N/A') | string)[:50] }}...</td>
                            <td style="padding: 1rem;">{{ item.get('ai_score', 0) }}/20</td>
                            <td style="padding: 1rem;">{{ item.get('user_expected_score', 0) }}/20</td>"""

if old_code in content:
    content = content.replace(old_code, new_code)
    
    # Also fix the closing
    content = content.replace(
        """</tr>
                        {% endfor %}""",
        """</tr>
                        {% endif %}
                        {% endfor %}"""
    )
    
    with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("SUCCESS: Fixed admin_dashboard.html feedback section")
else:
    print("ERROR: Could not find the code to replace")
