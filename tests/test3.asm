# ============================================================
# Test 3 - Memory-Mapped I/O LED Kontrolü (Knight Rider Efekti)
# ============================================================
# Bu test dosyası bellek eşlemeli G/Ç (memory-mapped I/O) ile
# LED kontrolünü doğrular. Klasik "Knight Rider" kayan ışık
# efekti uygulanır.
#
# Çalışma prensibi:
#   - GPIO LED yazmacı 0x10000000 adresinde
#   - 8 adet LED varsayılır (bit 0 - bit 7)
#   - LED deseni sola kaydırılır (1 -> 2 -> 4 -> ... -> 128)
#   - Sınıra ulaşınca sağa kaydırılır (128 -> 64 -> ... -> 1)
#   - Bu döngü sürekli tekrar eder
#
# Kullanılan yazmaçlar:
#   x2  = GPIO LED yazmacı adresi (0x10000000)
#   x3  = Mevcut LED değeri (başlangıç: 1)
#   x9  = Üst sınır (128 = 0x80, bit 7)
#   x10 = Alt program dönüş adresi (jal bağlantı yazmacı)
#   x5  = Gecikme sayacı (alt program içinde)
# ============================================================
.start 1

.text
basla:
    # GPIO LED yazmacı adresini oluştur: x2 = 0x10000000
    lui x2, 0x10000          # x2 = 0x10000 << 12 = 0x10000000
    addi x2, x2, 0           # x2 = 0x10000000 (açıkça belirt)

    # LED başlangıç değeri: x3 = 1 (bit 0 aktif)
    addi x3, x0, 1           # x3 = 1 (ilk LED)

    # Üst sınır: x9 = 128 (bit 7 aktif)
    addi x9, x0, 128         # x9 = 128 (0x80)

    # --- Ana döngü: Sola kayma fazı ---
sola_kaydir:
    sw x3, 0(x2)             # LED değerini GPIO yazmacına yaz
    jal x10, gecikme         # Gecikme alt programını çağır (x10'a dönüş adresi kaydedilir)
    slli x3, x3, 1           # LED desenini 1 bit sola kaydır
    blt x3, x9, sola_kaydir  # Sınıra gelmediyse sola kaydırmaya devam et

    # Sınıra ulaşıldı (x3 = 128), son konumu göster
    sw x3, 0(x2)             # Son LED pozisyonunu yaz
    jal x10, gecikme         # Gecikme

    # --- Sağa kayma fazı ---
saga_kaydir:
    srli x3, x3, 1           # LED desenini 1 bit sağa kaydır
    sw x3, 0(x2)             # LED değerini GPIO yazmacına yaz
    jal x10, gecikme         # Gecikme alt programını çağır
    addi x4, x0, 1           # x4 = 1 (alt sınır kontrolü için)
    bne x3, x4, saga_kaydir  # x3 henüz 1 değilse sağa kaydırmaya devam et

    # x3 = 1'e ulaşıldı, tekrar sola kaydırmaya başla
    jal x0, sola_kaydir      # Ana döngünün başına dön

# ============================================================
# Gecikme Alt Programı
# ============================================================
# Basit bir azaltma döngüsü ile zaman gecikmesi sağlar.
# Yaklaşık 0x00100 * 4096 = ~1M çevrim (50 MHz'de ~20 ms)
# Giriş: yok (sayaç dahili olarak yüklenir)
# Dönüş: jalr ile x10 yazmacındaki adrese döner
# Kullanılan yazmaç: x5 (gecikme sayacı)
# ============================================================
gecikme:
    lui x5, 0x00100          # x5 = 0x00100 << 12 = 0x00100000 (~1M)
gecikme_dongusu:
    addi x5, x5, -1          # Sayacı 1 azalt
    bne x5, x0, gecikme_dongusu  # Sıfır olmadıysa döngüye devam et
    jalr x0, 0(x10)          # Çağıran yere geri dön (x10'daki adrese)
