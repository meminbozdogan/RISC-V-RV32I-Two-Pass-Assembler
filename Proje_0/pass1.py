# pass1.py

def pass_one(assembly_lines):
    """Etiket adreslerini hesaplar ve bellek bölümlerini ayırır."""
    symbol_table = {}
    location_counter = 0  
    cleaned_code = []
    
    current_section = "text" 

    for line in assembly_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:
            line = line.split('#')[0].strip()

        if line == ".data":
            current_section = "data"
            continue
        elif line == ".text":
            current_section = "text"
            continue

        if ':' in line:
            parts = line.split(':')
            label_name = parts[0].strip()
            symbol_table[label_name] = location_counter
            
            line = parts[1].strip()
            if not line:
                continue

        cleaned_code.append(line)
        location_counter += 4 
            
    return symbol_table, cleaned_code
