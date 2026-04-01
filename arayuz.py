import tkinter as tk
from tkinter import scrolledtext, messagebox
import os 

# Modüllerimizi çağırıyoruz
from pass1 import pass_one
from pass2 import pass_two

def cevir_butonuna_tiklandi():
    ham_kod = input_text.get("1.0", tk.END).splitlines()
    
    if not ham_kod or all(line.strip() == "" for line in ham_kod):
        messagebox.showwarning("Uyarı", "Lütfen çevrilecek bir Assembly kodu girin.")
        return

    try:
        # 1. Motoru Çalıştır
        sembol_tablosu, temiz_kod = pass_one(ham_kod)
        data_bolumu, text_bolumu = pass_two(temiz_kod, sembol_tablosu)
        
        # 2. Ana Çıktıyı Formatla
        output_str = ""
        if data_bolumu:
            output_str += "=== .DATA BÖLÜMÜ (Veri Hafızası) ===\n"
            output_str += f"{'Direktif / Etiket':<22} | {'32-Bit Saf Veri (Binary)':<35} | {'Hex Veri'}\n"
            output_str += "-" * 75 + "\n"
            for orjinal, binary, hexa in data_bolumu:
                output_str += f"{orjinal:<22} | {binary:<35} | 0x{hexa}\n"
            output_str += "\n\n"
            
        output_str += "=== .TEXT BÖLÜMÜ (Çalıştırılabilir Kod) ===\n"
        output_str += f"{'Komut (Instruction)':<22} | {'32-Bit Makine Kodu':<35} | {'Hex Kod'}\n"
        output_str += "-" * 75 + "\n"
        for orjinal, binary, hexa in text_bolumu:
            output_str += f"{orjinal:<22} | {binary:<35} | 0x{hexa}\n"
            
        # 3. SEMBOL TABLOSUNU FORMATLA (Yeni Eklenen Kısım)
        symbol_str = f"{'Etiket (Label)':<15} | {'Adres (Dec)':<12} | {'Adres (Hex)'}\n"
        symbol_str += "-" * 45 + "\n"
        for etiket, adres in sembol_tablosu.items():
            symbol_str += f"{etiket:<15} | {adres:<12} | 0x{hex(adres)[2:].zfill(4).upper()}\n"

        # 4. Arayüz kutularını güncelle
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)  
        output_text.insert(tk.END, output_str)
        output_text.config(state=tk.DISABLED)

        symbol_text.config(state=tk.NORMAL)
        symbol_text.delete("1.0", tk.END)
        symbol_text.insert(tk.END, symbol_str)
        symbol_text.config(state=tk.DISABLED)
        
        # 5. Dosyaya Kaydet
        calisma_dizini = os.path.dirname(os.path.abspath(__file__))
        cikti_dosyasi = os.path.join(calisma_dizini, "makine_kodu.hex")
        with open(cikti_dosyasi, "w", encoding="utf-8") as f:
            f.write(output_str)
            f.write("\n\n=== SEMBOL TABLOSU ===\n")
            f.write(symbol_str)
            
    except Exception as e:
        messagebox.showerror("Hata", f"Derleme sırasında bir hata oluştu:\nLütfen komut sözdizimini kontrol edin.")

# --- TASARIM ---
pencere = tk.Tk()
pencere.title("RV32I Assembler Sürüm-1")
pencere.geometry("1200x750")
pencere.configure(bg="#2b2b2b") 

font_baslik = ("Courier New", 11, "bold")
font_kod = ("Consolas", 10)

# Ana Başlık
tk.Label(pencere, text="RV32I Assembler Sürüm-1", font=("Courier New", 18, "bold"), bg="#2b2b2b", fg="#ffffff").pack(pady=10)

# Üst Çerçeve (Girdi ve Çıktı için)
ust_frame = tk.Frame(pencere, bg="#2b2b2b")
ust_frame.pack(fill=tk.BOTH, expand=True, padx=20)

# Sol: Girdi
sol_frame = tk.Frame(ust_frame, bg="#2b2b2b")
sol_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
tk.Label(sol_frame, text="Assembly Kodu (Girdi)", font=font_baslik, bg="#2b2b2b", fg="#00ff00").pack(anchor="w")
input_text = scrolledtext.ScrolledText(sol_frame, font=font_kod, bg="#1e1e1e", fg="#ffffff", insertbackground="white", height=20)
input_text.pack(fill=tk.BOTH, expand=True)

# Sağ: Çıktı
sag_frame = tk.Frame(ust_frame, bg="#2b2b2b")
sag_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
tk.Label(sag_frame, text="Makine Kodu (Çıktı)", font=font_baslik, bg="#2b2b2b", fg="#ffaa00").pack(anchor="w")
output_text = scrolledtext.ScrolledText(sag_frame, font=font_kod, bg="#1e1e1e", fg="#00ffff", state=tk.DISABLED, height=20)
output_text.pack(fill=tk.BOTH, expand=True)

# Alt Çerçeve (Sembol Tablosu için)
alt_frame = tk.Frame(pencere, bg="#2b2b2b")
alt_frame.pack(fill=tk.X, padx=20, pady=10)

tk.Label(alt_frame, text="🔍 Sembol Tablosu İzleyici (Symbol Table Tracker)", font=font_baslik, bg="#2b2b2b", fg="#e066ff").pack(anchor="w")
symbol_text = scrolledtext.ScrolledText(alt_frame, font=font_kod, bg="#1e1e1e", fg="#e066ff", state=tk.DISABLED, height=8)
symbol_text.pack(fill=tk.X)

# Buton
cevir_butonu = tk.Button(pencere, text="► Kodu Derle (Assemble) ve Kaydet", font=("Courier New", 14, "bold"), bg="#007acc", fg="white", activebackground="#005999", command=cevir_butonuna_tiklandi)
cevir_butonu.pack(pady=15)

# Örnek Kod
ornek_kod = """.data               
sayi_on:  .word 10  
sayi_yirmi: .word 20 
sonuc:    .word 0   

.text               
START:
addi x1, x0, 5      
addi x2, x0, 15     
add  x3, x1, x2     
beq  x1, x2, END    
sub  x4, x2, x1     
and  x5, x4, x1     
END:
sw   x3, 0(x5)"""
input_text.insert(tk.END, ornek_kod)

pencere.mainloop()