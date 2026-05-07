# PicoRV32 (RV32I) Genişletilmiş Komut Seti Opcode Tablosu
opcode_table = {
    # ==========================================
    # R-Type Komutlar (Register-Register)
    # Format: funct7 + rs2 + rs1 + funct3 + rd + opcode
    # ==========================================
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "and":  {"type": "R", "opcode": "0110011", "funct3": "111", "funct7": "0000000"},
    "or":   {"type": "R", "opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    "xor":  {"type": "R", "opcode": "0110011", "funct3": "100", "funct7": "0000000"},
    "sll":  {"type": "R", "opcode": "0110011", "funct3": "001", "funct7": "0000000"}, # Sola Kaydır (Shift Left Logical)
    "srl":  {"type": "R", "opcode": "0110011", "funct3": "101", "funct7": "0000000"}, # Sağa Kaydır (Shift Right Logical)
    "slt":  {"type": "R", "opcode": "0110011", "funct3": "010", "funct7": "0000000"}, # Küçüksen Set Et (Set Less Than)

    # ==========================================
    # I-Type Komutlar (Immediate / Load / Jalr)
    # Format: imm[11:0] + rs1 + funct3 + rd + opcode
    # ==========================================
    "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
    "slli": {"type": "I", "opcode": "0010011", "funct3": "001"},
    "srli": {"type": "I", "opcode": "0010011", "funct3": "101"},
    "andi": {"type": "I", "opcode": "0010011", "funct3": "111"},
    "ori":  {"type": "I", "opcode": "0010011", "funct3": "110"},
    "xori": {"type": "I", "opcode": "0010011", "funct3": "100"},
    "slti": {"type": "I", "opcode": "0010011", "funct3": "010"},
    "lw":   {"type": "I", "opcode": "0000011", "funct3": "010"}, # Load Word (32-bit)
    "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"}, # Jump and Link Register (Fonksiyondan Dönüş)

    # ==========================================
    # S-Type Komutlar (Store)
    # Format: imm[11:5] + rs2 + rs1 + funct3 + imm[4:0] + opcode
    # ==========================================
    "sw":   {"type": "S", "opcode": "0100011", "funct3": "010"}, # Store Word (32-bit)
    "sh":   {"type": "S", "opcode": "0100011", "funct3": "001"}, # Store Halfword (16-bit)
    "sb":   {"type": "S", "opcode": "0100011", "funct3": "000"}, # Store Byte (8-bit)

    # ==========================================
    # B-Type Komutlar (Branch)
    # Format: imm[12|10:5] + rs2 + rs1 + funct3 + imm[4:1|11] + opcode
    # ==========================================
    "beq":  {"type": "B", "opcode": "1100011", "funct3": "000"}, # Branch if Equal (Eşitse)
    "bne":  {"type": "B", "opcode": "1100011", "funct3": "001"}, # Branch if Not Equal (Eşit Değilse)
    "blt":  {"type": "B", "opcode": "1100011", "funct3": "100"}, # Branch if Less Than (Küçükse)
    "bge":  {"type": "B", "opcode": "1100011", "funct3": "101"}, # Branch if Greater/Equal (Büyük Eşitse)

    # ==========================================
    # U-Type Komutlar (Upper Immediate)
    # Format: imm[31:12] + rd + opcode
    # ==========================================
    "lui":  {"type": "U", "opcode": "0110111"}, # Load Upper Immediate
    "auipc":{"type": "U", "opcode": "0010111"}, # Add Upper Immediate to PC

    # ==========================================
    # J-Type Komutlar (Jump)
    # Format: imm[20|10:1|11|19:12] + rd + opcode
    # ==========================================
    "jal":  {"type": "J", "opcode": "1101111"}  # Jump and Link (Fonksiyon Çağrısı)
}