import re

with open("phage_atb_native.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# Extract all strings in UI
matches = re.findall(r'(?:text|label)=[\'\"]([^\'\"]+)[\'\"]', content)
# Also Treeview headings: heading\([^,]+,\s*text=[\'\"]([^\'\"]+)[\'\"]
headings = re.findall(r'heading\([^,]+,\s*text=[\'\"]([^\'\"]+)[\'\"]', content)
matches.extend(headings)

matches = sorted(set(matches))

# Now import the class to get the dictionary
import sys
import os
sys.path.append(os.getcwd())

from phage_atb_native import PhageATBApp

app = PhageATBApp()
dictionary = app.i18n_dict

missing = []
for m in matches:
    # Filter out obvious non-cyrillic or empty
    if any("\u0400" <= c <= "\u04FF" for c in m):
        if m not in dictionary:
            missing.append(m)

print("Missing cyrillic strings:")
for m in missing:
    print(f"'{m}'")
