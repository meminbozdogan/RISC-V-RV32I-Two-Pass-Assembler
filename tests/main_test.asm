.start 1
.global main
.extern sum_array

.data
my_array:
    .word 5
    .word 10
    .word 15
    .word 20
array_len:
    .word 4
result:
    .word 0

.text
main:
    # my_array dizisinin adresini x10'a yükle
    lui x10, 1           # x10 = 0x1000
    addi x10, x10, 0

    # array_len değerini x11'e yükle
    lui x15, 1
    addi x15, x15, 16    # x15 = 0x1010
    lw x11, 0(x15)       # x11 = 4

    # Dışarıdaki sum_array fonksiyonunu çağır
    jal x1, sum_array    # x1'e dönüş adresini kaydet, fonksiyona git

    # Fonksiyondan dönen sonucu (x10 içinde) belleğe (result) kaydet
    lui x15, 1
    addi x15, x15, 20    # x15 = 0x1014
    sw x10, 0(x15)       # RAM'e yaz

infinite_loop:
    jal x0, infinite_loop # Program bitişinde sonsuz döngü
