import sys
import os
from pass1 import pass_one
from pass2 import pass_two

if __name__ == "__main__":
    calisma_dizini = os.path.dirname(os.path.abspath(__file__))
    girdi_dosyasi = os.path.join(calisma_dizini, "program.asm")
    cikti_dosyasi = os.path.join(calisma_dizini, "makine_kodu.hex")

    try:
        with open(girdi_dosyasi, "r", encoding="utf-8") as f:
            asm_kodlari = f.readlines()
    except FileNotFoundError:
        print(f"HATA: '{girdi_dosyasi}' dosyası bulunamadı!")
        sys.exit(1)

    print(f"[{girdi_dosyasi}] dosyası okunuyor...\n")

    print("1. Adım: Pass-1 Çalışıyor...")
    sembol_tablosu, temiz_kod = pass_one(asm_kodlari)
    print("1. Adım: Pass-1 Çalışıyor...")
    sembol_tablosu, temiz_kod = pass_one(asm_kodlari)
    
    # --- YENİ: SEMBOL TABLOSUNU EKRANA BAS ---
    print("\n" + "="*45)
    print(" 🔍 CANLI SEMBOL TABLOSU (SYMBOL TABLE)")
    print("="*45)
    for etiket, adres in sembol_tablosu.items():
        print(f"[{etiket:<12}] -> Bellek Adresi: {adres:<3} (Hex: 0x{hex(adres)[2:].zfill(4).upper()})")
    print("="*45 + "\n")
    
    print("2. Adım: Pass-2 Çalışıyor...")
    
    print("2. Adım: Pass-2 Çalışıyor...")
    data_bolumu, text_bolumu = pass_two(temiz_kod, sembol_tablosu)

    # 3. AŞAMA: Dosyaya Yaz (Terminolojik olarak düzeltilmiş başlıklar)
    with open(cikti_dosyasi, "w", encoding="utf-8") as f:
        
        # --- DATA SEGMENT YAZDIRMA ---
        if data_bolumu:
            f.write(f"=== .DATA BÖLÜMÜ (Veri Hafızası) ===\n")
            f.write(f"{'Direktif / Etiket':<22} | {'32-Bit Saf Veri (Binary)':<35} | {'Hex Veri'}\n")
            f.write("-" * 75 + "\n")
            for orjinal, binary, hexa in data_bolumu:
                f.write(f"{orjinal:<22} | {binary:<35} | 0x{hexa}\n")
            f.write("\n\n")

        # --- TEXT SEGMENT YAZDIRMA ---
        f.write(f"=== .TEXT BÖLÜMÜ (Çalıştırılabilir Kod) ===\n")
        f.write(f"{'Komut (Instruction)':<22} | {'32-Bit Makine Kodu':<35} | {'Hex Kod'}\n")
        f.write("-" * 75 + "\n")
        for orjinal, binary, hexa in text_bolumu:
            f.write(f"{orjinal:<22} | {binary:<35} | 0x{hexa}\n")

    print(f"\nBAŞARILI! Çıktı dosyası güncel terminoloji ile şu konuma kaydedildi:\n-> {cikti_dosyasi}")
