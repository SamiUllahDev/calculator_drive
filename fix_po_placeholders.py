import re

def fix_po_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.strip().startswith('msgid "'):
            # Collect full msgid
            current_msgid = line.strip()[7:-1]
            current_msgid_line_index = i
            msgid_lines_indices = [i]
            
            # Check for multi-line msgid
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"'):
                current_msgid += lines[j].strip()[1:-1]
                msgid_lines_indices.append(j)
                j += 1
            
            # Now find corresponding msgstr
            while j < len(lines) and not lines[j].strip().startswith('msgstr "'):
                j += 1
            
            if j < len(lines):
                # Found msgstr
                current_msgstr_start_index = j
                current_msgstr = lines[j].strip()[8:-1]
                msgstr_lines_indices = [j]
                
                k = j + 1
                while k < len(lines) and lines[k].strip().startswith('"'):
                    current_msgstr += lines[k].strip()[1:-1]
                    msgstr_lines_indices.append(k)
                    k += 1
                
                # logic to fix placeholders
                # Find all {var} patterns
                msgid_vars = re.findall(r'\{(\w+)\}', current_msgid)
                msgstr_vars = re.findall(r'\{(\w+)\}', current_msgstr)
                
                needs_reset = False
                
                if msgid_vars:
                    # If msgid has vars, msgstr MUST have them too
                    if not msgstr_vars:
                         needs_reset = True
                    elif set(msgid_vars) != set(msgstr_vars):
                        # Try to map them 1-to-1 if counts match
                        if len(msgid_vars) == len(msgstr_vars):
                             replacements = dict(zip(msgstr_vars, msgid_vars))
                             for idx in msgstr_lines_indices:
                                 new_content = lines[idx]
                                 for src, dst in replacements.items():
                                     new_content = new_content.replace('{' + src + '}', '{' + dst + '}')
                                 lines[idx] = new_content
                             
                             # Re-check after replacement
                             # (Simplified: assume it worked, or next compilation will verify)
                        else:
                            needs_reset = True
                
                if needs_reset:
                   # Replace translation with English original to fix build error
                   # We need to handle multi-line replacement carefully
                   # Simplest way: Make msgstr "" and copy msgid content
                   
                   # BUT if msgid is multi-line, we must replicate that structure or just flatten it?
                   # Flattening is easier but PO files support wrapping.
                   # Let's just create a valid msgstr that matches msgid content.
                   
                   # Clear existing msgstr lines
                   lines[current_msgstr_start_index] = 'msgstr "' + current_msgid + '"\n'
                   # If there were multiple lines, we empty them or remove them?
                   # Removing them is tricky with index iteration.
                   # Better: just comment them out or make them empty strings? No.
                   
                   # Strategy: We will rewrite the file based on logic, not in-place modification of 'lines' list for this block
                   pass # Proceed to manual reset logic below
                   
                   if len(msgstr_lines_indices) > 1:
                       # Complex case: multi-line msgstr.
                       # We'll just replace the first one with the full content (escaped) and empty the others or remove them.
                       # A safer bet for this script is to just copy msgid exactly.
                       pass 

                   # Actually, let's just use the fact that we can iterate line by line
                   # This script is getting complicated for in-place edit.
                   # Let's restart the approach with a cleaner logic in the loop:
    
    # Second pass: safer implementation
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We can parse entries by splitting by blank lines or finding msgid/msgstr blocks
    # But regex on the whole file is risky.
    pass

def fix_po_file_v2(filepath):
    import polib
    
    try:
        po = polib.pofile(filepath)
        count_fixed = 0
        for entry in po:
            msgid_vars = re.findall(r'\{(\w+)\}', entry.msgid)
            msgstr_vars = re.findall(r'\{(\w+)\}', entry.msgstr)
            
            if msgid_vars:
                if set(msgid_vars) != set(msgstr_vars):
                    # Check if we can map 1-to-1
                    if len(msgid_vars) == len(msgstr_vars):
                        # Attempt fix
                        replacements = dict(zip(msgstr_vars, msgid_vars))
                        new_msgstr = entry.msgstr
                        for src, dst in replacements.items():
                             new_msgstr = new_msgstr.replace('{' + src + '}', '{' + dst + '}')
                        entry.msgstr = new_msgstr
                        count_fixed += 1
                    else:
                        # Fallback: Reset to msgid
                        entry.msgstr = entry.msgid
                        count_fixed += 1
                        
        po.save()
        print(f"Fixed {count_fixed} entries.")
        
    except ImportError:
        print("polib not installed, using naive fallback")
        # Fallback to naive regex replacement showing earlier
        # Since I can't install packages, I should check if I can rely on regex
        pass

if __name__ == "__main__":
    # Check if polib exists
    try:
        import polib
        fix_po_file_v2("locale/es/LC_MESSAGES/django.po")
    except ImportError:
        # Use a robust manual parsing
        fix_manual("locale/es/LC_MESSAGES/django.po")

def fix_manual(filepath):
    # Read all lines
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('msgid "'):
            # Parse msgid
            msgid_start_idx = i
            current_msgid = line.strip()[7:-1]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('"'):
                current_msgid += lines[i].strip()[1:-1]
                i += 1
            
            # Look for msgstr
            while i < len(lines) and not lines[i].strip().startswith('msgstr "'):
                if lines[i].strip():
                     # Comments or others, keep them
                     pass
                i += 1
            
            if i < len(lines) and lines[i].strip().startswith('msgstr "'):
                msgstr_start_idx = i
                current_msgstr = lines[i].strip()[8:-1]
                msgstr_lines_count = 1
                i += 1
                while i < len(lines) and lines[i].strip().startswith('"'):
                    current_msgstr += lines[i].strip()[1:-1]
                    msgstr_lines_count += 1
                    i += 1
                
                # Now we have clean msgid and msgstr. Check vars.
                msgid_vars = re.findall(r'\{(\w+)\}', current_msgid)
                msgstr_vars = re.findall(r'\{(\w+)\}', current_msgstr)
                
                fixed_msgstr = current_msgstr
                
                if msgid_vars:
                    if set(msgid_vars) != set(msgstr_vars):
                        # Fix needed
                        if len(msgid_vars) == len(msgstr_vars):
                             replacements = dict(zip(msgstr_vars, msgid_vars))
                             for src, dst in replacements.items():
                                 fixed_msgstr = fixed_msgstr.replace('{' + src + '}', '{' + dst + '}')
                        else:
                             # Reset to msgid
                             fixed_msgstr = current_msgid
                
                # Reconstruct output
                # Append lines before msgid
                # (Actually we need to traverse simpler)
                pass 
                
    # Retrying a line-by-line processor that reconstructs the file
    pass

# Third time's the charm: Read file as string, regex sub all entries
def fix_regex(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match msgid "..." (multiline) followed by msgstr "..." (multiline)
    # This is hard with regex.
    pass

# Back to line iteration with state, but writing to new list immediately
def run_fix(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    i = 0
    
    while i < len(lines):
        if lines[i].strip().startswith('msgid "'):
            # Parse msgid block
            msgid_lines = [lines[i]]
            current_msgid = lines[i].strip()[7:-1]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('"'):
                msgid_lines.append(lines[i])
                current_msgid += lines[i].strip()[1:-1]
                i += 1
            
            # Comments/empty lines between msgid and msgstr?
            # Standard PO shouldn't have them usually, but tolerate
            interrim_lines = []
            while i < len(lines) and not lines[i].strip().startswith('msgstr "'):
                interrim_lines.append(lines[i])
                i += 1
            
            if i < len(lines) and lines[i].strip().startswith('msgstr "'):
                msgstr_lines = [lines[i]]
                current_msgstr = lines[i].strip()[8:-1]
                i += 1
                while i < len(lines) and lines[i].strip().startswith('"'):
                    msgstr_lines.append(lines[i])
                    current_msgstr += lines[i].strip()[1:-1]
                    i += 1
                
                # Check vars
                msgid_vars = re.findall(r'\{(\w+)\}', current_msgid)
                msgstr_vars = re.findall(r'\{(\w+)\}', current_msgstr)
                
                should_fix = False
                fixed_msgstr = current_msgstr
                
                if msgid_vars:
                   if set(msgid_vars) != set(msgstr_vars):
                       should_fix = True
                       if len(msgid_vars) == len(msgstr_vars):
                           replacements = dict(zip(msgstr_vars, msgid_vars))
                           for src, dst in replacements.items():
                               fixed_msgstr = fixed_msgstr.replace('{' + src + '}', '{' + dst + '}')
                       else:
                           fixed_msgstr = current_msgid
                
                if should_fix:
                    # Write msgid lines
                    new_lines.extend(msgid_lines)
                    new_lines.extend(interrim_lines)
                    # Write new msgstr
                    # For simplicity, write it as a single line or wrapped?
                    # Writing as single line is safer than trying to wrap manually
                    # Escape quotes
                    escaped_msgstr = fixed_msgstr.replace('"', '\\"')
                    new_lines.append(f'msgstr "{escaped_msgstr}"\n')
                else:
                    # Keep original
                    new_lines.extend(msgid_lines)
                    new_lines.extend(interrim_lines)
                    new_lines.extend(msgstr_lines)
                    
            else:
                # No msgstr found? (shouldn't happen in valid PO)
                new_lines.extend(msgid_lines)
                new_lines.extend(interrim_lines)
        else:
            new_lines.append(lines[i])
            i += 1
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
if __name__ == "__main__":
    run_fix("locale/es/LC_MESSAGES/django.po")
