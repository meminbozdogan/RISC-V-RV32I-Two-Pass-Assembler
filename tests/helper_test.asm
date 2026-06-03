.start 2
.global sum_array

.text
sum_array:
    # Giriş Parametreleri:
    # x10 : Dizinin başlangıç adresi
    # x11 : Dizinin eleman sayısı (uzunluk)
    # Çıkış Parametresi:
    # x10 : Toplam değer

    add x12, x0, x0      # x12 (Toplam sum) = 0
    add x13, x0, x0      # x13 (Döngü sayacı i) = 0
    
loop_start:
    bne x13, x11, loop_body  # Eğer i != uzunluk ise loop_body'ye atla
    jal x0, end_func         # Değilse, döngü bitti end_func'a git

loop_body:
    lw x14, 0(x10)       # x14 = array[i]
    add x12, x12, x14    # sum = sum + array[i]
    
    addi x10, x10, 4     # Pointer'ı bir sonraki kelimeye (4 byte) kaydır
    addi x13, x13, 1     # Döngü sayacını (i) 1 artır
    
    jal x0, loop_start   # Başa dön

end_func:
    # Toplam değeri x12'den x10'a (Standart dönüş kaydedicisi) aktar
    add x10, x12, x0
    jalr x0, 0(x1)       # Çağrılan yere (x1'deki adrese) geri dön
