import os

base_path = r'D:\Do an\MTUFace\MTUFace\NDKHM_DDSV_MTU\templates\base.html'
with open(base_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Try to find the exact block
start_idx = content.find('<!-- Header Section -->')
if start_idx != -1:
    end_idx = content.find('</div>', start_idx) + 6
    original_block = content[start_idx:end_idx]
    
    new_block = "<!-- Header Section -->\n            {% block header_section %}\n" + original_block.split('<!-- Header Section -->\n', 1)[-1] + "\n            {% endblock %}"
    
    content = content[:start_idx] + new_block + content[end_idx:]
    with open(base_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
dashboard_path = r'D:\Do an\MTUFace\MTUFace\NDKHM_DDSV_MTU\templates\dashboard\index.html'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dash = f.read()

if '{% block header_section %}{% endblock %}' not in dash:
    dash = dash.replace('{% block page_title %}Tổng quan{% endblock %}', 
                        '{% block page_title %}Tổng quan{% endblock %}\n{% block header_section %}{% endblock %}')

    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dash)

print('Success')
