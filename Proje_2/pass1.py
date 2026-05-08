from utils import parse_instruction

def assembler_pass_one(assembly_lines):
    """
    Pass 1: Etiketleri, Global/Extern direktiflerini ve bölüm adreslerini tespit et.
    Dönen yapı: cleaned_code ve object_file (symbol_table dolu halde).
    """
    object_file = {
        "text_segment": [],
        "data_segment": [],
        "symbol_table": {},
        "relocation_table": []
    }
    
    location_counter = 0
    current_section = "text"
    cleaned_code = []
    
    extern_symbols = set()
    global_symbols = set()
    
    for line_idx, line in enumerate(assembly_lines):
        orj_line = line.strip()
        if not orj_line or orj_line.startswith('#'):
            continue
        if '#' in orj_line:
            orj_line = orj_line.split('#')[0].strip()
            
        if orj_line == ".data":
            current_section = "data"
            continue
        elif orj_line == ".text":
            current_section = "text"
            continue
            
        # .global, .extern ve .start direktifleri
        if orj_line.startswith(".global"):
            _, sym = parse_instruction(orj_line)
            if sym: global_symbols.add(sym[0])
            continue
        elif orj_line.startswith(".extern"):
            _, sym = parse_instruction(orj_line)
            if sym: extern_symbols.add(sym[0])
            continue
        elif orj_line.startswith(".start"):
            continue
            
        # Etiket kontrolü
        if ':' in orj_line:
            parts = orj_line.split(':')
            label_name = parts[0].strip()
            
            # Sembol tablosuna ekle
            object_file["symbol_table"][label_name] = {
                "offset": location_counter,
                "section": current_section,
                "is_global": label_name in global_symbols
            }
            
            orj_line = parts[1].strip()
            if not orj_line:
                continue
                
        cleaned_code.append((orj_line, current_section, location_counter))
        location_counter += 4
        
    return cleaned_code, object_file