from utils import imm_to_bin

TEXT_BASE = 0x00000000
DATA_BASE = 0x00001000

def link(object_files):
    """
    Birden fazla Object dosyasını alır.
    Text ve Data bölümlerini birleştirir, absolute (mutlak) adresleri hesaplar.
    Global sembolleri çözer ve Relocation tablosunu kullanarak offsetleri hesaplar.
    Sonuç olarak tek bir HEX yapısı (Text ve Data) ve diğer tabloları döner.
    """
    global_symbol_table = {}
    all_symbols = [] # Tüm lokal ve global sembolleri tutmak için
    all_relocations = [] # Çözümlenen relocation'ları tutmak için
    
    current_text_addr = TEXT_BASE
    current_data_addr = DATA_BASE
    
    merged_text = []
    merged_data = []
    
    file_bases = []

    # 1. Aşama: Belleğe Yerleştirme ve Global Sembolleri Toplama
    for file_idx, obj in enumerate(object_files):
        base_info = {
            "text_base": current_text_addr,
            "data_base": current_data_addr,
            "obj": obj,
            "file_idx": file_idx
        }
        file_bases.append(base_info)
        
        # Local sembolleri mutlak adrese çevirip global ise ana tabloya atma
        for label, info in obj["symbol_table"].items():
            if info["section"] == "text":
                abs_addr = current_text_addr + info["offset"]
            else:
                abs_addr = current_data_addr + info["offset"]
                
            info["abs_addr"] = abs_addr
            
            all_symbols.append({
                "label": label,
                "abs_addr": abs_addr,
                "is_global": info["is_global"],
                "file_idx": file_idx
            })
            
            if info["is_global"]:
                if label in global_symbol_table:
                    print(f"UYARI: '{label}' sembolü birden fazla kez tanımlanmış!")
                global_symbol_table[label] = abs_addr
                
        # Data segmentleri birleştir
        for data in obj["data_segment"]:
            data_copy = data.copy()
            data_copy["abs_addr"] = current_data_addr + data["offset"]
            merged_data.append(data_copy)
            
        current_data_addr += len(obj["data_segment"]) * 4
        
        # Text segmentleri birleştir
        for text in obj["text_segment"]:
            text_copy = text.copy()
            text_copy["abs_addr"] = current_text_addr + text["offset"]
            merged_text.append(text_copy)
            
        current_text_addr += len(obj["text_segment"]) * 4

    # 2. Aşama: Relocation (Adres Bağlama / Offset Hesaplama)
    for base_info in file_bases:
        obj = base_info["obj"]
        t_base = base_info["text_base"]
        f_idx = base_info["file_idx"]
        
        for reloc in obj["relocation_table"]:
            label = reloc["label"]
            current_addr = t_base + reloc["offset"]
            
            target_addr = None
            if label in global_symbol_table:
                target_addr = global_symbol_table[label]
            elif label in obj["symbol_table"]:
                target_addr = obj["symbol_table"][label]["abs_addr"]
            else:
                print(f"HATA: '{label}' sembolü hiçbir dosyada bulunamadı!")
                continue
                
            offset = target_addr - current_addr
            
            all_relocations.append({
                "file_idx": f_idx,
                "label": label,
                "current_addr": current_addr,
                "target_addr": target_addr,
                "offset": offset,
                "type": reloc["type"]
            })
            
            for t in merged_text:
                if t["abs_addr"] == current_addr:
                    if reloc["type"] == "B_TYPE":
                        imm_bin = imm_to_bin(offset, 13)
                        mac_bin = imm_bin[0] + imm_bin[2:8] + reloc["rs2"] + reloc["rs1"] + reloc["funct3"] + imm_bin[8:12] + imm_bin[1] + reloc["opcode"]
                        t["binary"] = mac_bin
                        t["hex"] = hex(int(mac_bin, 2))[2:].zfill(8).upper()
                        
                    elif reloc["type"] == "J_TYPE":
                        imm_bin = imm_to_bin(offset, 21)
                        mac_bin = imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9] + reloc["rd"] + reloc["opcode"]
                        t["binary"] = mac_bin
                        t["hex"] = hex(int(mac_bin, 2))[2:].zfill(8).upper()
                    break

    return merged_text, merged_data, global_symbol_table, all_symbols, all_relocations
