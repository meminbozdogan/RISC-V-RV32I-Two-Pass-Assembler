import json
from opcodes import opcode_table # Genişlettiğimiz efsane komut sözlüğümüz!

def parse_reg(reg_str):
    """ 'x1', 'x2' gibi stringleri integer 1, 2'ye çevirir """
    return int(reg_str.replace('x', '').replace(',', ''))

def int_to_bin_str(deger, bit_sayisi):
    """ Sayıları İki'ye tümleyen (Two's complement) ile binary string üretir """
    if deger < 0:
        deger = (1 << bit_sayisi) + deger
    # Taşmaları önlemek için bit sayısına göre maskele
    mask = (1 << bit_sayisi) - 1
    deger = deger & mask
    return format(deger, f'0{bit_sayisi}b')

def pass_two_v2(temiz_kod, symbol_table):
    text_segment = []
    data_segment = []
    relocation_table = []
    
    current_segment = '.text'
    location_counter = 0 
    
    for satir in temiz_kod:
        if satir == '.data':
            current_segment = '.data'
            continue
        elif satir == '.text':
            current_segment = '.text'
            continue
            
        # ====================================================
        # 1. VERİ İŞLEME (DATA SEGMENT)
        # ====================================================
        if current_segment == '.data':
            if '.word' in satir:
                deger = int(satir.split()[-1])
                hex_deger = f"{deger & 0xFFFFFFFF:08X}" 
                data_segment.append(hex_deger)
        
        # ====================================================
        # 2. KOMUT İŞLEME VE RELOCATION (TEXT SEGMENT)
        # ====================================================
        elif current_segment == '.text':
            # Virgülleri ve parantezleri boşlukla değiştirip parçala 
            # (Örn: lw x1, 0(x0) -> lw x1 0 x0)
            islenmis_satir = satir.replace(',', ' ').replace('(', ' ').replace(')', ' ')
            komut_parcalari = islenmis_satir.split()
            opcode_adi = komut_parcalari[0]
            
            if opcode_adi not in opcode_table:
                print(f"[UYARI] Tanımlanmayan komut atlandı: {opcode_adi}")
                continue
                
            komut_bilgisi = opcode_table[opcode_adi]
            komut_tipi = komut_bilgisi["type"]
            opcode_bin = komut_bilgisi["opcode"]
            
            makine_kodu_bin = ""
            
            # ------------------------------------------------
            # R-Type: add rd, rs1, rs2
            # ------------------------------------------------
            if komut_tipi == "R":
                rd = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                rs1 = int_to_bin_str(parse_reg(komut_parcalari[2]), 5)
                rs2 = int_to_bin_str(parse_reg(komut_parcalari[3]), 5)
                funct3 = komut_bilgisi["funct3"]
                funct7 = komut_bilgisi["funct7"]
                
                makine_kodu_bin = funct7 + rs2 + rs1 + funct3 + rd + opcode_bin
                
            # ------------------------------------------------
            # I-Type: addi rd, rs1, imm VEYA lw rd, imm(rs1)
            # ------------------------------------------------
            elif komut_tipi == "I":
                rd = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                funct3 = komut_bilgisi["funct3"]
                
                if opcode_adi in ["lw"]: # lw x1, 0(x0) formatı için
                    imm_val = int(komut_parcalari[2])
                    rs1 = int_to_bin_str(parse_reg(komut_parcalari[3]), 5)
                else: # addi x1, x2, 10 formatı için
                    rs1 = int_to_bin_str(parse_reg(komut_parcalari[2]), 5)
                    imm_val = int(komut_parcalari[3])
                    
                imm_bin = int_to_bin_str(imm_val, 12)
                makine_kodu_bin = imm_bin + rs1 + funct3 + rd + opcode_bin
                
            # ------------------------------------------------
            # S-Type: sw rs2, imm(rs1)
            # ------------------------------------------------
            elif komut_tipi == "S":
                rs2 = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                imm_val = int(komut_parcalari[2])
                rs1 = int_to_bin_str(parse_reg(komut_parcalari[3]), 5)
                funct3 = komut_bilgisi["funct3"]
                
                imm_bin = int_to_bin_str(imm_val, 12)
                imm_11_5 = imm_bin[0:7]
                imm_4_0 = imm_bin[7:12]
                
                makine_kodu_bin = imm_11_5 + rs2 + rs1 + funct3 + imm_4_0 + opcode_bin
                
            # ------------------------------------------------
            # B-Type: beq rs1, rs2, etiket
            # ------------------------------------------------
            elif komut_tipi == "B":
                rs1 = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                rs2 = int_to_bin_str(parse_reg(komut_parcalari[2]), 5)
                funct3 = komut_bilgisi["funct3"]
                hedef_etiket = komut_parcalari[3]
                
                imm_val = 0 # Extern için varsayılan offset SIFIRDIR
                
                if hedef_etiket in symbol_table:
                    if symbol_table[hedef_etiket]['tip'] == 'extern':
                        # EXTERN İSE: Relocation tablosuna not bırak, offset 0 kalır!
                        relocation_table.append({
                            "adres": location_counter,
                            "hedef_sembol": hedef_etiket,
                            "komut_tipi": "B-Type"
                        })
                    else:
                        # LOCAL İSE: Kendi içinde normal ofset hesapla
                        imm_val = symbol_table[hedef_etiket]['adres'] - location_counter
                
                imm_bin = int_to_bin_str(imm_val, 13) 
                
                imm_12 = imm_bin[0]
                imm_10_5 = imm_bin[2:8]
                imm_4_1 = imm_bin[8:12]
                imm_11 = imm_bin[1]
                
                makine_kodu_bin = imm_12 + imm_10_5 + rs2 + rs1 + funct3 + imm_4_1 + imm_11 + opcode_bin

            # ------------------------------------------------
            # U-Type: lui rd, imm
            # ------------------------------------------------
            elif komut_tipi == "U":
                rd = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                imm_val = int(komut_parcalari[2])
                imm_bin = int_to_bin_str(imm_val, 20)
                
                makine_kodu_bin = imm_bin + rd + opcode_bin

            # ------------------------------------------------
            # J-Type: jal rd, etiket
            # ------------------------------------------------
            elif komut_tipi == "J":
                rd = int_to_bin_str(parse_reg(komut_parcalari[1]), 5)
                hedef_etiket = komut_parcalari[2]
                
                imm_val = 0
                
                if hedef_etiket in symbol_table:
                    if symbol_table[hedef_etiket]['tip'] == 'extern':
                        # EXTERN İSE: Linker'a not bırak, offset 0 kalsın!
                        relocation_table.append({
                            "adres": location_counter,
                            "hedef_sembol": hedef_etiket,
                            "komut_tipi": "J-Type"
                        })
                    else:
                        imm_val = symbol_table[hedef_etiket]['adres'] - location_counter
                        
                imm_bin = int_to_bin_str(imm_val, 21) 
                
                imm_20 = imm_bin[0]
                imm_10_1 = imm_bin[10:20]
                imm_11 = imm_bin[9]
                imm_19_12 = imm_bin[1:9]
                
                makine_kodu_bin = imm_20 + imm_10_1 + imm_11 + imm_19_12 + rd + opcode_bin

            # Binary string'i 32-bit Hex formata çevirip paketle
            if makine_kodu_bin:
                hex_deger = f"{int(makine_kodu_bin, 2):08X}"
                text_segment.append(hex_deger)
            else:
                text_segment.append("00000000") 
                
            location_counter += 4

    # ====================================================
    # 3. NİHAİ OBJECT (.o) DOSYASININ PAKETLENMESİ
    # ====================================================
    object_file = {
        "header": {
            "text_size": len(text_segment) * 4,
            "data_size": len(data_segment) * 4
        },
        "text_segment": text_segment,
        "data_segment": data_segment,
        "symbol_table": symbol_table,
        "relocation_table": relocation_table
    }
    
    return object_file