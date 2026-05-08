import json
from opcodes import opcode_table
from utils import parse_instruction, reg_to_bin, imm_to_bin

def assemble(assembly_lines):
    """
    Assembly kodunu okur ve Linker için Object (.o) Dosyası formatında döner.
    Dönen yapı: text_segment, data_segment, symbol_table, relocation_table
    """
    object_file = {
        "text_segment": [],
        "data_segment": [],
        "symbol_table": {},
        "relocation_table": []
    }
    
    # Pass 1: Etiketleri, Global/Extern direktiflerini ve bölüm adreslerini tespit et
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

    # Pass 2: Makine Kodunu ve Relocation tablosunu oluştur
    for line, section, loc in cleaned_code:
        komut, argumanlar = parse_instruction(line)
        
        if section == "data":
            if komut == ".word":
                deger_bin = imm_to_bin(argumanlar[0], 32)
                hex_code = hex(int(deger_bin, 2))[2:].zfill(8).upper()
                object_file["data_segment"].append({
                    "original": line,
                    "binary": deger_bin,
                    "hex": hex_code,
                    "offset": loc
                })
            continue
            
        # Text Section komutları
        if komut not in opcode_table:
            print(f"HATA: Desteklenmeyen komut -> '{komut}'")
            continue
            
        info = opcode_table[komut]
        tip = info["type"]
        opcode = info["opcode"]
        machine_code_bin = ""
        
        # Eğer etiket gerektiren bir komutsa (B, J) ve etiket extern ise veya başka bölümdeyse relocation ekle
        needs_relocation = False
        reloc_label = None
        
        if tip == "U":
            rd = reg_to_bin(argumanlar[0])
            imm = imm_to_bin(argumanlar[1], 20)
            machine_code_bin = imm + rd + opcode
            
        elif tip == "R":
            rd = reg_to_bin(argumanlar[0])
            rs1 = reg_to_bin(argumanlar[1])
            rs2 = reg_to_bin(argumanlar[2])
            machine_code_bin = info["funct7"] + rs2 + rs1 + info["funct3"] + rd + opcode
            
        elif tip == "I":
            rd = reg_to_bin(argumanlar[0])
            if komut == "lw":
                imm = imm_to_bin(argumanlar[1], 12)
                rs1 = reg_to_bin(argumanlar[2])
            else:
                rs1 = reg_to_bin(argumanlar[1])
                imm = imm_to_bin(argumanlar[2], 12)
            machine_code_bin = imm + rs1 + info["funct3"] + rd + opcode
            
        elif tip == "S":
            rs2 = reg_to_bin(argumanlar[0])
            imm = imm_to_bin(argumanlar[1], 12)
            rs1 = reg_to_bin(argumanlar[2])
            machine_code_bin = imm[0:7] + rs2 + rs1 + info["funct3"] + imm[7:12] + opcode
            
        elif tip == "B":
            rs1 = reg_to_bin(argumanlar[0])
            rs2 = reg_to_bin(argumanlar[1])
            label_name = argumanlar[2]
            
            # Şimdilik offset 0 kabul edip taslak üreteceğiz, Linker tamamlayacak
            offset = 0
            # Dosya içi bilinen bir etiketse (ve extern değilse) offset hesaplanabilir ama Linker her türlü B ve J typeları ayarlayacak.
            # Biz relocation'a ekleyelim.
            object_file["relocation_table"].append({
                "offset": loc,
                "label": label_name,
                "type": "B_TYPE",
                "rs1": rs1,
                "rs2": rs2,
                "funct3": info["funct3"],
                "opcode": opcode
            })
            # Taslak (dummy) kod
            machine_code_bin = "0000000" + rs2 + rs1 + info["funct3"] + "00000" + opcode
            
        elif tip == "J":
            rd = reg_to_bin(argumanlar[0])
            label_name = argumanlar[1]
            
            object_file["relocation_table"].append({
                "offset": loc,
                "label": label_name,
                "type": "J_TYPE",
                "rd": rd,
                "opcode": opcode
            })
            # Taslak (dummy) kod
            machine_code_bin = "00000000000000000000" + rd + opcode

        hex_code = hex(int(machine_code_bin, 2))[2:].zfill(8).upper()
        
        object_file["text_segment"].append({
            "original": line,
            "binary": machine_code_bin, # Taslak olabilir
            "hex": hex_code,
            "offset": loc,
            "type": tip
        })
        
    return object_file
