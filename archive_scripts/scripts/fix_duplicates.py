import os

ROUTES_DIR = 'routes'

for root, dirs, files in os.walk(ROUTES_DIR):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            modified = False
            prev_line = None
            
            for line in lines:
                if line.strip().startswith('def ') and line == prev_line:
                    modified = True
                    continue
                new_lines.append(line)
                prev_line = line
                
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"Fixed duplicates in {filepath}")
print("Fixing complete!")
