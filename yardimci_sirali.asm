# --- yardimci_sirali.asm ---
.start 02
.extern SOLA_KAYDIR

.text
SAGA_KAYDIR:
    srli x1, x1, 1          # 1 bit sağa kaydır
    sw x1, 0(x2)            # Mevcut LED'i yak
    lui x3, 0x004C4         # Gecikme sayacını yükle
GECIKME_2:
    addi x3, x3, -1         # Sayacı 1 azalt
    bne x3, x0, GECIKME_2   # Sıfır değilse devam et
    bne x1, x0, SAGA_KAYDIR # Sıfır olmadıysa sağa devam et
    
    addi x1, x0, 1          # x1'i tekrar 1 yap
    jal x0, SOLA_KAYDIR     # SOLA_KAYDIR'a dön