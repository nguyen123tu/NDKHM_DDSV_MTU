import os
import re

ROUTES_DIR = 'routes'

def add_swagger_to_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all route decorators and their function definitions
    # pattern: @xxx.route(...)\ndef func_name(...):
    # Then we check if it already has a swagger docstring (contains '---' or 'tags:')
    
    # We will split by lines to process safely
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Detect route
        if re.search(r'@\w+\.route\(', line):
            # Look ahead for def
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('def '):
                new_lines.append(lines[j])
                j += 1
            
            if j < len(lines):
                def_line = lines[j]
                new_lines.append(def_line)
                
                # Now check next line for docstring
                k = j + 1
                has_docstring = False
                docstring_start = -1
                if k < len(lines) and lines[k].strip().startswith('"""'):
                    has_docstring = True
                    docstring_start = k
                
                # Check if it already has Swagger (contains 'tags:' or '---' in docstring)
                has_swagger = False
                if has_docstring:
                    temp_k = k
                    while temp_k < len(lines):
                        if 'tags:' in lines[temp_k] or '---' in lines[temp_k]:
                            has_swagger = True
                            break
                        if temp_k > k and '"""' in lines[temp_k]:
                            break
                        temp_k += 1
                
                if not has_swagger:
                    modified = True
                    # Extract route path for the name
                    route_path_match = re.search(r"@\w+\.route\(['\"](.*?)['\"]", line)
                    path_name = route_path_match.group(1) if route_path_match else "API"
                    
                    # Determine Tag
                    tag = "Web API"
                    if 'api_mobile' in filepath: tag = "Mobile App API"
                    elif 'deepface' in filepath: tag = "DeepFace AI API"
                    elif 'chatbot' in filepath: tag = "Chatbot AI API"
                    elif 'public' in filepath: tag = "Kiosk Public API"
                    
                    swagger_yaml = f'''    """
    {path_name}
    ---
    tags:
      - {tag}
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """'''
                    
                    if has_docstring:
                        # Replace existing docstring with combined
                        original_doc = ""
                        end_k = k
                        if lines[k].strip() == '"""':
                            end_k += 1
                            while end_k < len(lines) and '"""' not in lines[end_k]:
                                original_doc += lines[end_k].strip() + "\n    "
                                end_k += 1
                        else:
                            original_doc = lines[k].replace('"""', '').strip()
                            end_k = k
                        
                        swagger_yaml = f'''    """
    {original_doc}
    ---
    tags:
      - {tag}
    responses:
      200:
        description: Thành công
    """'''
                        # Skip original docstring lines
                        for _ in range(k, end_k + 1):
                            pass
                        i = end_k # Move main pointer
                    
                    new_lines.append(swagger_yaml)
                i = j if not has_docstring else i
            else:
                i = j - 1
        i += 1
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"Updated {filepath}")

for root, dirs, files in os.walk(ROUTES_DIR):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            add_swagger_to_file(os.path.join(root, file))

print("Xong!")
