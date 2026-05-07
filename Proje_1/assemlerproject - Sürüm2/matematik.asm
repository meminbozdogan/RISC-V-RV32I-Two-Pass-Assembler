.text
.global ozel_islem

ozel_islem:
# 1. Yeni R-Type komutlarımızın testleri
add x3, x1, x2     
xor x3, x3, x1     

# 2. Fonksiyondan geri dönüş (I-Type jalr Testi)
jalr x0, x10, 0