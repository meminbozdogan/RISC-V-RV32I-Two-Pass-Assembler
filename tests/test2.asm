# ============================================================
# Test 2 - Bellek Manipülasyonu (Dizi İşleme)
# ============================================================
# Bu test dosyası bellek erişimi ve dizi işleme yeteneklerini doğrular.
# Yapılan işlemler:
#   - Bellekteki bir diziyi döngü ile okuma (lw)
#   - Dizi elemanlarının toplamını hesaplama
#   - Toplam sonucunu belleğe yazma (sw)
#   - İkinci döngü: Her elemanı 2 ile çarpma (slli) ve geri yazma
#   - Döngü kontrolü: bne ile sayaç karşılaştırma
#
# Bellek haritası (.data bölümü 0x1000'den başlar):
#   0x1000: dizi[0] = 10
#   0x1004: dizi[1] = 20
#   0x1008: dizi[2] = 30
#   0x100C: dizi[3] = 40
#   0x1010: dizi[4] = 50
#   0x1014: dizi_uzunluk = 5
#   0x1018: toplam_sonuc = 0
# ============================================================
.start 1

.data
dizi:
    .word 10
    .word 20
    .word 30
    .word 40
    .word 50
dizi_uzunluk:
    .word 5
toplam_sonuc:
    .word 0

.text
basla:
    # --- Aşama 1: Dizi toplamını hesapla ---

    # Dizi temel adresini yükle: x10 = 0x1000
    lui x10, 1               # x10 = 0x1000
    addi x10, x10, 0         # x10 = 0x1000 (dizi başlangıcı)

    # Dizi uzunluğunu bellekten oku: x11 = 5
    lui x15, 1               # x15 = 0x1000
    addi x15, x15, 20        # x15 = 0x1014 (dizi_uzunluk adresi)
    lw x11, 0(x15)           # x11 = 5 (dizi uzunluğu)

    # Sayaçları sıfırla
    add x12, x0, x0          # x12 = 0 (toplam akümülatör)
    add x13, x0, x0          # x13 = 0 (döngü sayacı i)
    add x14, x10, x0         # x14 = x10 (mevcut dizi adresi işaretçisi)

    # Toplama döngüsü
toplam_dongusu:
    beq x13, x11, toplam_bitti   # Eğer i == uzunluk ise döngüden çık
    lw x16, 0(x14)           # x16 = dizi[i] (mevcut elemanı oku)
    add x12, x12, x16        # toplam = toplam + dizi[i]
    addi x14, x14, 4         # İşaretçiyi sonraki elemana ilerlet (+4 bayt)
    addi x13, x13, 1         # Sayacı artır (i = i + 1)
    jal x0, toplam_dongusu   # Döngü başına geri dön

toplam_bitti:
    # Toplam sonucunu belleğe yaz: toplam_sonuc (0x1018)
    lui x15, 1               # x15 = 0x1000
    addi x15, x15, 24        # x15 = 0x1018 (toplam_sonuc adresi)
    sw x12, 0(x15)           # toplam_sonuc = 150 (10+20+30+40+50)

    # --- Aşama 2: Her elemanı 2 ile çarp (sola kaydır) ---

    # Dizi adresini ve sayacı sıfırla
    add x14, x10, x0         # x14 = 0x1000 (dizi başlangıcına geri dön)
    add x13, x0, x0          # x13 = 0 (döngü sayacını sıfırla)

    # Çarpma döngüsü
carpma_dongusu:
    beq x13, x11, carpma_bitti   # Eğer i == uzunluk ise döngüden çık
    lw x16, 0(x14)           # x16 = dizi[i] (mevcut elemanı oku)
    slli x16, x16, 1         # x16 = x16 * 2 (1 bit sola kaydır)
    sw x16, 0(x14)           # dizi[i] = x16 (güncellenmiş değeri geri yaz)
    addi x14, x14, 4         # İşaretçiyi sonraki elemana ilerlet
    addi x13, x13, 1         # Sayacı artır
    jal x0, carpma_dongusu   # Döngü başına geri dön

carpma_bitti:
    # Program bitti, sonsuz döngüye gir
sonsuz_dongu:
    jal x0, sonsuz_dongu     # Sonsuz döngü - program burada durur
