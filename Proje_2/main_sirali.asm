# --- main_sirali.asm ---
.start 01
.global SOLA_KAYDIR

.text
START:
    addi x2, x0, 1024       # LED donanım adresi (0x0400)
    addi x1, x0, 1          # İlk LED biti (00000001)
    addi x9, x0, 64         # Sınır: 7. LED (01000000)

SOLA_KAYDIR:
    sw x1, 0(x2)            # Mevcut LED'i yak
    lui x3, 0x004C4         # Gecikme sayacını yükle
GECIKME_1:
    addi x3, x3, -1         # Sayacı 1 azalt
    bne x3, x0, GECIKME_1   # Sıfır değilse devam et
    slli x1, x1, 1          # 1 bit sola kaydır
    blt x1, x9, SOLA_KAYDIR # Sınıra gelmediyse sola devam et
