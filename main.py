import sys
import os
import json
from assembler import assemble
from linker import link

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

    print("Derleyici (Assembler) Çalışıyor...")
    object_file = assemble(asm_kodlari)
    
    obj_dosyasi = girdi_dosyasi.replace(".asm", ".o")
    with open(obj_dosyasi, "w", encoding="utf-8") as f:
        json.dump(object_file, f, indent=4)
    print(f"Ara Object (.o) dosyası oluşturuldu: {obj_dosyasi}\n")
    
    print("Bağlayıcı (Linker) Çalışıyor...")
    with open(obj_dosyasi, "r", encoding="utf-8") as f:
        okunan_obj = json.load(f)
        
    merged_text, merged_data, global_symbol_table, all_symbols, all_relocations = link([okunan_obj])

    # --- YENİ: SEMBOL TABLOSUNU EKRANA BAS ---
    print("\n" + "="*55)
    print(" 🔍 CANLI SEMBOL TABLOSU (SYMBOL TABLE)")
    print("="*55)
    for sym in all_symbols:
        etiket = sym['label']
        adres = sym['abs_addr']
        tur = "Global" if sym['is_global'] else "Local"
        print(f"[{etiket:<12}] -> Adres: 0x{hex(adres)[2:].zfill(8).upper()} [{tur}]")
    print("="*55 + "\n")

    # 3. AŞAMA: Dosyaya Yaz (Terminolojik olarak düzeltilmiş başlıklar)
    with open(cikti_dosyasi, "w", encoding="utf-8") as f:
        
        # --- DATA SEGMENT YAZDIRMA ---
        if merged_data:
            f.write(f"=== .DATA BÖLÜMÜ (Veri Hafızası) ===\n")
            f.write(f"{'Adres (Hex)':<12} | {'Direktif / Etiket':<22} | {'32-Bit Saf Veri (Binary)':<35} | {'Hex Veri'}\n")
            f.write("-" * 90 + "\n")
            for d in merged_data:
                addr_hex = f"0x{hex(d['abs_addr'])[2:].zfill(8).upper()}"
                f.write(f"{addr_hex:<12} | {d['original']:<22} | {d['binary']:<35} | 0x{d['hex']}\n")
            f.write("\n\n")

        # --- TEXT SEGMENT YAZDIRMA ---
        f.write(f"=== .TEXT BÖLÜMÜ (Çalıştırılabilir Kod) ===\n")
        f.write(f"{'Adres (Hex)':<12} | {'Komut (Instruction)':<22} | {'32-Bit Makine Kodu':<35} | {'Hex Kod'}\n")
        f.write("-" * 90 + "\n")
        for t in merged_text:
            addr_hex = f"0x{hex(t['abs_addr'])[2:].zfill(8).upper()}"
            f.write(f"{addr_hex:<12} | {t['original']:<22} | {t['binary']:<35} | 0x{t['hex']}\n")

    print(f"\nBAŞARILI! Çıktı dosyası güncel terminoloji ile şu konuma kaydedildi:\n-> {cikti_dosyasi}")