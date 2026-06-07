# BRAM Sıfırlama (Memory Initialization) Testi
.start 1
.global main

.text
main:
    # x10: Dizinin BRAM'deki başlangıç adresi (0x00000800)
    lui x10, 1          
    addi x10, x10, -2048
    
    # x11: Dizi boyutu (Örn: 10 eleman)
    addi x11, x0, 10    
    
    # x12: Döngü sayacı (i = 0)
    add x12, x0, x0     
    
    # x13: Yazılacak veri (0)
    add x13, x0, x0     

DONGU_BASLA:
    beq x12, x11, DONGU_BITIS 
    
    sw x13, 0(x10)            
    addi x10, x10, 4          
    addi x12, x12, 1          
    
    jal x0, DONGU_BASLA       

DONGU_BITIS:
    # --- BAŞARI IŞIĞI ---
    addi x30, x0, 1024   # x30 = 0x0400 (LED Adresi)
    addi x31, x0, 255    # x31 = 255 (Tüm LED'leri yak)
    sw x31, 0(x30)       # Donanıma yaz

SON:
    jal x0, SON          # Sonsuz döngü
