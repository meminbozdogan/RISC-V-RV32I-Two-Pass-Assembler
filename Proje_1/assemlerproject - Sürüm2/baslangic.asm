.data
veri_bir: .word 100
veri_iki: .word 200

.text
.global main
.extern islem_yap

main:
# --- SİSTEM KESİNLİKLE BURADAN BAŞLAMALI ---
lw x1, 0(x0)
lw x2, 4(x0)

# Kütüphanedeki fonksiyona atla
jal x10, islem_yap

# Program sonu (Sonsuz döngü simülasyonu)
bitir:
beq x0, x0, bitir