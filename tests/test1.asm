# ============================================================
# Test 1 - Basit Matematiksel ve Lojik İşlemler
# ============================================================
# Bu test dosyası temel aritmetik ve mantık işlemlerini doğrular.
# Yapılan işlemler:
#   - addi ile yazmaçlara sabit değer yükleme
#   - add ile toplama (x5 = x1 + x2 = 25 + 10 = 35)
#   - sub ile çıkarma (x6 = x1 - x2 = 25 - 10 = 15)
#   - and ile mantıksal VE (x7 = x1 AND x3 = 0x19 AND 0xFF = 0x19)
#   - or ile mantıksal VEYA (x8 = x2 OR x3 = 0x0A OR 0xFF = 0xFF)
# Tüm sonuçlar .data bölümüne yazılır.
# ============================================================
.start 1

.data
sonuc_toplam:
    .word 0
sonuc_cikarma:
    .word 0
sonuc_and:
    .word 0
sonuc_or:
    .word 0

.text
basla:
    # Yazmaçlara sabit değerler yükle
    addi x1, x0, 25         # x1 = 25 (0x19)
    addi x2, x0, 10         # x2 = 10 (0x0A)
    addi x3, x0, 255        # x3 = 255 (0xFF)

    # Toplama işlemi: x5 = x1 + x2 = 35
    add x5, x1, x2          # x5 = 25 + 10 = 35

    # Çıkarma işlemi: x6 = x1 - x2 = 15
    sub x6, x1, x2          # x6 = 25 - 10 = 15

    # Mantıksal VE işlemi: x7 = x1 AND x3 = 0x19
    and x7, x1, x3          # x7 = 0x19 AND 0xFF = 0x19

    # Mantıksal VEYA işlemi: x8 = x2 OR x3 = 0xFF
    or x8, x2, x3           # x8 = 0x0A OR 0xFF = 0xFF

    # --- Sonuçları belleğe kaydet ---

    # .data bölümü 0x1000 adresinden başlar
    # sonuc_toplam = 0x1000, sonuc_cikarma = 0x1004
    # sonuc_and = 0x1008, sonuc_or = 0x100C

    # Temel adres oluştur: x20 = 0x1000
    lui x20, 1               # x20 = 0x1000
    addi x20, x20, 0         # x20 = 0x1000 (açıkça belirt)

    # Toplama sonucunu kaydet (0x1000)
    sw x5, 0(x20)            # sonuc_toplam = 35

    # Çıkarma sonucunu kaydet (0x1004)
    sw x6, 4(x20)            # sonuc_cikarma = 15

    # AND sonucunu kaydet (0x1008)
    sw x7, 8(x20)            # sonuc_and = 0x19

    # OR sonucunu kaydet (0x100C)
    sw x8, 12(x20)           # sonuc_or = 0xFF

    # Program bitti, sonsuz döngüye gir
sonsuz_dongu:
    jal x0, sonsuz_dongu     # Sonsuz döngü - program burada durur
