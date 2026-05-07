import json
import sys
# Yazdığımız o iki efsane motoru içeri aktarıyoruz
from pass1_v2 import pass_one_v2
from pass2_v2 import pass_two_v2

def assembler_derle(asm_dosyasi, obj_dosyasi):
    """
    Sürüm-2 Derleyici Motoru:
    .asm dosyasını alır, Pass-1 ve Pass-2'den geçirir, JSON formatında .o dosyası üretir.
    """
    # 1. Ham Kodu Okuma (Hata Kontrollü - Hatırlarsan sys.exit(1) muhabbeti!)
    try:
        with open(asm_dosyasi, 'r', encoding='utf-8') as f:
            ham_kod = f.readlines()
    except FileNotFoundError:
        print(f"[HATA] '{asm_dosyasi}' adlı girdi dosyası bulunamadı!")
        sys.exit(1)

    print(f"[İŞLEM] '{asm_dosyasi}' derleniyor...")

    # 2. BİRİNCİ GEÇİŞ (Harita Mühendisi - Sembol Tablosunu Çıkar)
    symbol_table, temiz_kod = pass_one_v2(ham_kod)

    # 3. İKİNCİ GEÇİŞ (Paketleme Uzmanı - Makine kodunu ve Relocation'ı üret)
    object_file = pass_two_v2(temiz_kod, symbol_table)

    # 4. OBJECT (.o) DOSYASINI YAZDIRMA
    # (JSON formatında kaydediyoruz ki Linker bunu rahatça okuyabilsin)
    with open(obj_dosyasi, 'w', encoding='utf-8') as f:
        json.dump(object_file, f, indent=4)
        
    print(f"[BAŞARILI] -> {obj_dosyasi} oluşturuldu.\n")