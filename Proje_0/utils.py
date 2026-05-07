# utils.py

def parse_instruction(line):
    """Satırı okur, komutu ve argümanları ayrıştırır."""
    line = line.replace(",", " ").replace("(", " ").replace(")", " ")
    parts = line.split()
    if not parts:
        return None, []
    instruction = parts[0].lower()
    arguments = parts[1:]
    return instruction, arguments

def reg_to_bin(reg_str):
    """ 'x1' gibi bir stringi '00001' şeklinde 5-bit binary yapar. """
    reg_num = int(reg_str.replace("x", ""))
    return format(reg_num, '05b')

def imm_to_bin(imm_val, bits):
    """Sabit sayıları istenen bit uzunluğunda binary yapar (İkiye Tümleyen destekli)."""
    imm = int(imm_val)
    if imm < 0:
        imm = (1 << bits) + imm
    return format(imm, f'0{bits}b')
