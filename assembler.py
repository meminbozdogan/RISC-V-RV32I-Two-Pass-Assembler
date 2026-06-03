from pass1 import assembler_pass_one
from pass2 import assembler_pass_two

def assemble(assembly_lines):
    """
    Assembly kodunu okur ve Linker için Object (.o) Dosyası formatında döner.
    Dönen yapı: text_segment, data_segment, symbol_table, relocation_table
    (Modüler yapıya geçilmiştir. Pass 1 ve Pass 2 ayrı modüllerde çalışır.)
    """
    # 1. Aşama: Etiketleri, Global/Extern durumlarını ve Bellek adreslerini belirle
    cleaned_code, object_file = assembler_pass_one(assembly_lines)
    
    # 2. Aşama: Temizlenmiş kodlardan makine kodunu (text/data segmentleri) ve relocation tablosunu oluştur
    object_file = assembler_pass_two(cleaned_code, object_file)
    
    return object_file
