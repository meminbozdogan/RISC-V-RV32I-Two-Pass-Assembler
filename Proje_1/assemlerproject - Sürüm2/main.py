# Sürüm-2 Toolchain Ana Yönetici Dosyası
from assembler_v2 import assembler_derle  # Senin pass1 ve pass2'yi çağıran fonksiyonun
from linker import basit_linker

def main():
    print("--- 1. AŞAMA: ASSEMBLER (Derleme) ---")
    # Dosyaları ayrı ayrı .o formatına çevir
    assembler_derle("main_kod.asm", "main_kod.o")
    assembler_derle("matematik.asm", "matematik.o")
    print("[OK] Object dosyaları üretildi.\n")

    print("--- 2. AŞAMA: LINKER (Bağlama) ---")
    # Üretilen dosyaları Linker'a ver
    obj_dosyalar = ["main_kod.o", "matematik.o"]
    master_tablo = basit_linker(obj_dosyalar)
    
    if master_tablo:
        print("\n--- İŞLEM BAŞARILI! ---")
        print("BRAM için instruction_bram.hex ve data_bram.hex dosyaları oluşturuldu.")

if __name__ == "__main__":
    main()