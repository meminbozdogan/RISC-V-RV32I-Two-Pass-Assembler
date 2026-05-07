import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import sys

from assembler_v2 import assembler_derle
from linker import basit_linker

class PrintYonlendirici:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

class PicoRVToolchainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PicoRV32 Toolchain Sürüm-2 (Assembler & Linker)")
        self.root.geometry("1050x700") # Sütun sığsın diye biraz genişlettim
        
        self.bg_color = "#ffffff"
        self.fg_color = "#333333"
        self.highlight_bg = "#f0f2f5"
        self.root.configure(bg=self.bg_color)

        self.dosyalar = []

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=self.highlight_bg, 
                        foreground=self.fg_color, 
                        font=("Arial", 10, "bold"), 
                        padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", "#e0e6ed")], foreground=[("selected", "#0056b3")])
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_konsol = tk.Frame(self.notebook, bg=self.bg_color)
        self.tab_sembol = tk.Frame(self.notebook, bg=self.bg_color)
        self.tab_bellek = tk.Frame(self.notebook, bg=self.bg_color)

        self.notebook.add(self.tab_konsol, text="🚀 Derleme & Linker (Konsol)")
        self.notebook.add(self.tab_sembol, text="📊 Sembol ve Relocation Tablosu")
        self.notebook.add(self.tab_bellek, text="💾 Üretilen HEX Çıktıları")

        self.arayuz_konsol_olustur()
        self.arayuz_sembol_olustur()
        self.arayuz_bellek_olustur()

        sys.stdout = PrintYonlendirici(self.txt_log)

    def arayuz_konsol_olustur(self):
        ust_frame = tk.Frame(self.tab_konsol, bg=self.bg_color)
        ust_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sol_frame = tk.Frame(ust_frame, bg=self.bg_color)
        sol_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        tk.Label(sol_frame, text="Kaynak Dosyalar (.asm)", font=("Arial", 11, "bold"), bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        self.listbox = tk.Listbox(sol_frame, font=("Consolas", 11), bg=self.highlight_bg, fg=self.fg_color, relief="solid", bd=1, selectbackground="#cce5ff", selectforeground="black", width=35)
        self.listbox.pack(fill=tk.Y, expand=True, pady=5)

        tk.Button(sol_frame, text="+ Dosya Ekle", command=self.dosya_ekle, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(sol_frame, text="Listeyi Temizle", command=self.listeyi_temizle, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(sol_frame, text="⚡ Sürüm 2'yi Başlat", command=self.sistemi_atesle, bg="#007BFF", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill=tk.X, pady=10)

        sag_frame = tk.Frame(ust_frame, bg=self.bg_color)
        sag_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        tk.Label(sag_frame, text="Linker Sistem Logları", font=("Arial", 11, "bold"), bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        self.txt_log = scrolledtext.ScrolledText(sag_frame, font=("Consolas", 11), bg="#fdfdfd", fg="#212529", relief="solid", bd=1)
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=5)

    def arayuz_sembol_olustur(self):
        style = ttk.Style()
        style.configure("Treeview", background="#ffffff", foreground=self.fg_color, fieldbackground="#ffffff", font=("Consolas", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=self.highlight_bg, foreground=self.fg_color)
        
        # SÜTUN SAYISI 4'E ÇIKTI!
        self.tree_sembol = ttk.Treeview(self.tab_sembol, columns=("etiket", "adres", "segment", "tip"), show="headings", height=15)
        self.tree_sembol.heading("etiket", text="Sembol Adı")
        self.tree_sembol.heading("adres", text="Adres (Dec)")
        self.tree_sembol.heading("segment", text="Bölüm (Segment)")
        self.tree_sembol.heading("tip", text="Tip")
        
        self.tree_sembol.column("etiket", width=220, anchor=tk.W)
        self.tree_sembol.column("adres", width=120, anchor=tk.CENTER)
        self.tree_sembol.column("segment", width=150, anchor=tk.CENTER)
        self.tree_sembol.column("tip", width=120, anchor=tk.CENTER)
        
        self.tree_sembol.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def arayuz_bellek_olustur(self):
        sol_frame = tk.Frame(self.tab_bellek, bg=self.bg_color)
        sol_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(sol_frame, text="Instruction BRAM (.text)", font=("Arial", 11, "bold"), bg=self.bg_color, fg="#d9534f").pack()
        self.txt_inst_bram = scrolledtext.ScrolledText(sol_frame, font=("Consolas", 12, "bold"), bg="#fffafa", fg="#d9534f", width=30, relief="solid", bd=1)
        self.txt_inst_bram.pack(fill=tk.BOTH, expand=True)

        sag_frame = tk.Frame(self.tab_bellek, bg=self.bg_color)
        sag_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(sag_frame, text="Data BRAM (.data)", font=("Arial", 11, "bold"), bg=self.bg_color, fg="#0275d8").pack()
        self.txt_data_bram = scrolledtext.ScrolledText(sag_frame, font=("Consolas", 12, "bold"), bg="#f4f8fb", fg="#0275d8", width=30, relief="solid", bd=1)
        self.txt_data_bram.pack(fill=tk.BOTH, expand=True)

    def dosya_ekle(self):
        secilenler = filedialog.askopenfilenames(title="Assembly Dosyaları Seç", filetypes=[("Assembly Dosyası", "*.asm")])
        for dosya in secilenler:
            if dosya not in self.dosyalar:
                self.dosyalar.append(dosya)
                self.listbox.insert(tk.END, os.path.basename(dosya))

    def listeyi_temizle(self):
        self.dosyalar.clear()
        self.listbox.delete(0, tk.END)
        self.ekranlari_sifirla()

    def ekranlari_sifirla(self):
        self.txt_log.delete(1.0, tk.END)
        self.tree_sembol.delete(*self.tree_sembol.get_children())
        self.txt_inst_bram.delete(1.0, tk.END)
        self.txt_data_bram.delete(1.0, tk.END)

    def sistemi_atesle(self):
        self.ekranlari_sifirla()
        
        if not self.dosyalar:
            messagebox.showwarning("Eksik Dosya", "Lütfen en az bir adet .asm dosyası yükleyin!")
            return

        self.root.update()
        print("==================================================")
        print(" PicoRV32 Toolchain Sürüm-2 Başlatılıyor...")
        print("==================================================\n")

        try:
            print("--- 1. AŞAMA: ASSEMBLER (Derleme) ---")
            obj_dosyalar = []
            for asm_yol in self.dosyalar:
                dosya_adi = os.path.basename(asm_yol)
                obj_adi = dosya_adi.replace('.asm', '.o')
                assembler_derle(asm_yol, obj_adi) 
                obj_dosyalar.append(obj_adi)

            print("\n--- 2. AŞAMA: LINKER (Bağlama) ---")
            master_tablo = basit_linker(obj_dosyalar)

            if master_tablo:
                print("\n[BİLGİ] Linker işlemi tamam! FPGA BRAM dosyaları başarıyla üretildi.")
                
                # TABLOYU DOLDURMA KISMI (YENİ SÜTUNLA BİRLİKTE)
                for etiket, bilgi in master_tablo.items():
                    adres_str = str(bilgi['adres']) if bilgi['adres'] is not None else "ÇÖZÜLEMEDİ"
                    segment_str = str(bilgi.get('segment', 'BİLİNMİYOR')).upper()
                    tip_str = str(bilgi['tip']).upper()
                    
                    # 4 bilgiyi de arayüze ekliyoruz!
                    self.tree_sembol.insert("", tk.END, values=(etiket, adres_str, segment_str, tip_str))
                
                if os.path.exists('instruction_bram.hex'):
                    with open('instruction_bram.hex', 'r') as f:
                        self.txt_inst_bram.insert(tk.END, f.read())
                
                if os.path.exists('data_bram.hex'):
                    with open('data_bram.hex', 'r') as f:
                        self.txt_data_bram.insert(tk.END, f.read())
                        
                messagebox.showinfo("Başarılı", "Derleme ve Bağlama işlemi başarıyla tamamlandı!\nSonuçları sekmelerden inceleyebilirsiniz.")
                self.notebook.select(self.tab_sembol)
                
            else:
                print("\n[HATA] Linker adres bağlama sırasında kritik bir hata oluştu!")

        except Exception as e:
            print(f"\n[SİSTEM ÇÖKTÜ]: Beklenmeyen bir hata: {str(e)}")

if __name__ == "__main__":
    pencere = tk.Tk()
    uygulama = PicoRVToolchainGUI(pencere)
    pencere.mainloop()