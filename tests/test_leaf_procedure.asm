# Yaprak Fonksiyon (Leaf Procedure) Testi
.start 1
.global main

.text
main:
    # Parametreleri yükle
    addi x10, x0, 15    
    addi x11, x0, 20    
    addi x12, x0, 5     
    addi x13, x0, 10    

    # Alt programı çağır
    jal x1, YAPRAK_FONKSIYON

    # Sonucu RAM'e yaz (Adres: 0x0800)
    lui x15, 1
    addi x15, x15, -2048
    sw x14, 0(x15)

    # --- BAŞARI IŞIĞI ---
    addi x30, x0, 1024   # x30 = 0x0400 (LED Adresi)
    addi x31, x0, 255    # x31 = 255 (Tüm LED'leri yak)
    sw x31, 0(x30)       # Donanıma yaz

ANA_PROGRAM_BITIS:
    jal x0, ANA_PROGRAM_BITIS

# --- ALT PROGRAM ---
YAPRAK_FONKSIYON:
    add x5, x10, x11    
    add x6, x12, x13    
    sub x14, x5, x6     
    
    jalr x0, 0(x1)
