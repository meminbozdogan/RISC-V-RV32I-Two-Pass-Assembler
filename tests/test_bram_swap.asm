# BRAM Tam Kapasite Swap (Bellek Uçları Yer Değiştirme) Testi
.start 1
.global main

.text
main:
    # Sol Pointer (0x00001000)
    lui x10, 1          
    addi x10, x10, 0

    # Sağ Pointer (0x00001FFC)
    lui x11, 2          
    addi x11, x11, -4   

SWAP_DONGUSU:
    blt x11, x10, SWAP_BITIS  
    beq x10, x11, SWAP_BITIS  

    lw x12, 0(x10)      
    lw x13, 0(x11)      

    sw x13, 0(x10)      
    sw x12, 0(x11)      

    addi x10, x10, 4    
    addi x11, x11, -4   

    jal x0, SWAP_DONGUSU
    
SWAP_BITIS:
    # --- BAŞARI IŞIĞI ---
    lui x30, 0x10000     # x30 = 0x10000000 (LED Adresi)
    addi x31, x0, 170    # x31 = 170 (Atlamalı LED deseni)
    sw x31, 0(x30)       # Donanıma yaz

SON:
    jal x0, SON
