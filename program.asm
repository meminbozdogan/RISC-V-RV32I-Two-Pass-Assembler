# ==========================================
# BELLEK SEGMENTASYONU VE DİREKTİF TESTİ
# ==========================================

.data               # DEPO MODU: Aşağıdakiler hafızada tutulacak sabit sayılardır!
sayi_on:  .word 10  # 'sayi_on' etiketiyle hafızaya 32-bitlik 10 sayısını yaz
sayi_yirmi: .word 20 # 'sayi_yirmi' etiketiyle hafızaya 32-bitlik 20 sayısını yaz
sonuc:    .word 0   # Sonucu tutmak için hafızada boş bir yer (0) ayır

.text               # AKSİYON MODU: Asıl komutlar buradan başlıyor!
START:
addi x1, x0, 5      # x1 yazmacına 5 yükle
addi x2, x0, 15     # x2 yazmacına 15 yükle
add  x3, x1, x2     # x3 = x1 + x2 (Sonuç 20 olacak)

# Dallanma ve Mantık Testi
beq  x1, x2, END    # x1 ve x2 eşitse END etiketine atla (Eşit değil, devam edecek)
sub  x4, x2, x1     # x4 = 15 - 5 = 10
and  x5, x4, x1     # x4 ve x1'i bit seviyesinde VE (AND) işlemine sok

END:
sw   x3, 0(x5)      # Bulunan sonucu belleğe yaz