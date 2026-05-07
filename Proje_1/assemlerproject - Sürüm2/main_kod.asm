.data
deger_bir: .word 15
deger_iki: .word 25
sonuc:     .word 0

.text
.global main
.extern ozel_islem

main:
# 1. RAM'den verileri çek (I-Type Testi)
lw x1, 0(x0)
lw x2, 4(x0)

# 2. Dışarıdaki fonksiyona atlama (J-Type ve Relocation Testi)
jal x10, ozel_islem

# 3. Dönen sonucu (x3'te dönecek) RAM'e kaydet (S-Type Testi)
sw x3, 8(x0)

# 4. Kendi içinde dallanma (B-Type ve Local Offset Testi)
beq x3, x0, atla
addi x4, x0, 1
atla:
addi x5, x0, 2