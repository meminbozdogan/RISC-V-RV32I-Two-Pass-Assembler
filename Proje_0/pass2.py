# pass2.py

from opcodes import opcode_table
from utils import parse_instruction, reg_to_bin, imm_to_bin

def pass_two(cleaned_code, symbol_table):
    """Temizlenmiş kodları okur ve Data/Text olarak iki ayrı makine kodu listesi üretir."""
    data_segment = []
    text_segment = []
    location_counter = 0

    for line in cleaned_code:
        komut, argumanlar = parse_instruction(line)
        
        if komut == ".word":
            deger_bin = imm_to_bin(argumanlar[0], 32)
            hex_code = hex(int(deger_bin, 2))[2:].zfill(8).upper()
            data_segment.append((line, deger_bin, hex_code))
            location_counter += 4
            continue

        if komut not in opcode_table:
            print(f"HATA: Desteklenmeyen komut -> '{komut}'")
            location_counter += 4
            continue

        info = opcode_table[komut]
        tip = info["type"]
        opcode = info["opcode"]
        machine_code_bin = ""

        if tip == "R":
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
            
            offset = symbol_table[label_name] - location_counter
            imm = imm_to_bin(offset, 13) 
            
            machine_code_bin = imm[0] + imm[2:8] + rs2 + rs1 + info["funct3"] + imm[8:12] + imm[1] + opcode

        hex_code = hex(int(machine_code_bin, 2))[2:].zfill(8).upper()
        
        text_segment.append((line, machine_code_bin, hex_code))
        location_counter += 4

    return data_segment, text_segment
