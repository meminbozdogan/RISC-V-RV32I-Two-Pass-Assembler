# PicoRV32 (RV32I) Temel Komut Seti Opcode Tablosu
opcode_table = {
    # R-Type Komutlar (Register-Register)
    # Format: funct7 + rs2 + rs1 + funct3 + rd + opcode
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "and":  {"type": "R", "opcode": "0110011", "funct3": "111", "funct7": "0000000"},
    "or":   {"type": "R", "opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    
    # I-Type Komutlar (Immediate / Load)
    # Format: imm[11:0] + rs1 + funct3 + rd + opcode
    "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
    "lw":   {"type": "I", "opcode": "0000011", "funct3": "010"},
    
    # S-Type Komutlar (Store)
    # Format: imm[11:5] + rs2 + rs1 + funct3 + imm[4:0] + opcode
    "sw":   {"type": "S", "opcode": "0100011", "funct3": "010"},
    
    # B-Type Komutlar (Branch)
    # Format: imm[12|10:5] + rs2 + rs1 + funct3 + imm[4:1|11] + opcode
    "beq":  {"type": "B", "opcode": "1100011", "funct3": "000"},
    "blt":  {"type": "B", "opcode": "1100011", "funct3": "100"},
    "bne":  {"type": "B", "opcode": "1100011", "funct3": "001"},
    
    # J-Type Komutlar (Jump)
    # Format: imm[20|10:1|11|19:12] + rd + opcode
    "jal":  {"type": "J", "opcode": "1101111"},
    
    # U-Type Komutlar
    "lui":  {"type": "U", "opcode": "0110111"},
    
    # I-Type (Jump and Link Register)
    # Format: imm[11:0] + rs1 + funct3 + rd + opcode
    "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"},
    "slli": {"type": "I", "opcode": "0010011", "funct3": "001"},
    "srli": {"type": "I", "opcode": "0010011", "funct3": "101"},
}