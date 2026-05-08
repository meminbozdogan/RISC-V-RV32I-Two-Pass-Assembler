from opcodes import opcode_table
from utils import parse_instruction, reg_to_bin, imm_to_bin

def assembler_pass_two(cleaned_code, object_file):
    """
    Pass 2: Makine Kodunu ve Relocation tablosunu oluştur.
    Temizlenmiş kodları (cleaned_code) alır, object_file nesnesini tamamlar ve geri döndürür.
    """
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
            if komut == "lw" or (komut == "jalr" and len(argumanlar) == 3 and "x" in argumanlar[2]):
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
            "binary": machine_code_bin,
            "hex": hex_code,
            "offset": loc,
            "type": tip
        })
        
    return object_file