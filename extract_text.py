import re
with open("phage_atb_native.py", "r", encoding="utf-8") as f:
    content = f.read()
    matches = re.findall(r'text=[\'"]([^\'"]+)[\'"]', content)
    matches += re.findall(r'heading\(.*?, text=[\'"]([^\'"]+)[\'"]\)', content)
    matches += re.findall(r'add\([\'"]([^\'"]+)[\'"]\)', content)
    matches += re.findall(r'messagebox\.\w+\([\'"][^\'"]+[\'"],\s*[\'"]([^\'"]+)[\'"]\)', content)
    print(sorted(set(matches)))
