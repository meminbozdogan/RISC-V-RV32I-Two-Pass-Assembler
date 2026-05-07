.text
.global islem_yap

islem_yap:
# Gelen iki veriyi topla ve x3'e yaz
add x3, x1, x2

# Geldiğin yere geri dön
jalr x0, x10, 0