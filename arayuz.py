import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os

from assembler import assemble
from linker import link

def dosya_ekle():
    dosyalar = filedialog.askopenfilenames(
        title="Assembly Dosyaları Seç",
        filetypes=(("Assembly Dosyaları", "*.asm"), ("Tüm Dosyalar", "*.*"))
    )
    mevcut_dosyalar = listbox.get(0, tk.END)
    for d in dosyalar:
        if d not in mevcut_dosyalar:
            listbox.insert(tk.END, d)

def dosya_cikar():
    secili_indexler = listbox.curselection()
    if not secili_indexler:
        messagebox.showinfo("Bilgi", "Lütfen listeden çıkarmak istediğiniz dosyayı seçin.")
        return
    for index in reversed(secili_indexler):
        listbox.delete(index)

# Global değişkenler (Dışa aktarma işlemi için)
son_merged_text = []
son_merged_data = []

def hex_kaydet():
    if not son_merged_text and not son_merged_data:
        messagebox.showwarning("Uyarı", "Kaydedilecek bir makine kodu bulunamadı. Lütfen önce derleme yapın.")
        return
        
    dosya_yolu = filedialog.asksaveasfilename(
        title="FPGA İçin Hex Dosyasını Kaydet",
        defaultextension=".hex",
        initialfile="fpga_bram_init.hex",
        filetypes=(("BRAM Hex Dosyaları", "*.hex"), ("Memory Dosyaları", "*.mem"), ("Tüm Dosyalar", "*.*"))
    )
    
    if dosya_yolu:
        try:
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                # Sadece hex kodlarını alt alta yazdırıyoruz
                if son_merged_text:
                    for t in son_merged_text:
                        f.write(f"{t['hex']}\n")
                        
                if son_merged_data:
                    for d in son_merged_data:
                        f.write(f"{d['hex']}\n")
                        
            messagebox.showinfo("Başarılı", f"FPGA BRAM yüklemesine uygun RAW HEX dosyası kaydedildi:\n{dosya_yolu}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu:\n{str(e)}")

def cevir_butonuna_tiklandi():
    dosyalar = listbox.get(0, tk.END)
    if not dosyalar:
        messagebox.showwarning("Uyarı", "Lütfen derlenecek en az bir Assembly (.asm) dosyası ekleyin.")
        return

    try:
        parsed_files = []
        for dosya_yolu in dosyalar:
            try:
                with open(dosya_yolu, "r", encoding="utf-8") as f:
                    ham_kod = f.readlines()
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya okunurken hata oluştu: {dosya_yolu}\n{str(e)}")
                return
                
            if ham_kod and any(line.strip() != "" for line in ham_kod):
                order = 99 # Varsayılan sıra
                for line in ham_kod:
                    sline = line.strip().lower()
                    if sline.startswith(".start"):
                        try:
                            order = int(sline.split()[1])
                        except:
                            pass
                        break
                parsed_files.append((order, ham_kod))
        
        # .start numarasına göre sırala
        parsed_files.sort(key=lambda x: x[0])
        
        objects = []
        for order, ham_kod in parsed_files:
            obj = assemble(ham_kod)
            if obj:
                objects.append(obj)
        
        if not objects:
            messagebox.showwarning("Uyarı", "Okunan dosyalarda derlenecek geçerli kod bulunamadı.")
            return

        # Linker çağrısı (Artık 5 eleman dönüyor)
        merged_text, merged_data, global_symbol_table, all_symbols, all_relocations = link(objects)
        
        global son_merged_text, son_merged_data
        son_merged_text = merged_text
        son_merged_data = merged_data
        
        # 1. Ana Çıktıyı Formatla
        output_str = ""
        if merged_data:
            output_str += "=== .DATA BÖLÜMÜ (Veri Hafızası) ===\n"
            output_str += f"{'Adres (Hex)':<12} | {'Direktif / Etiket':<22} | {'32-Bit Saf Veri (Binary)':<35} | {'Hex Veri'}\n"
            output_str += "-" * 90 + "\n"
            for d in merged_data:
                addr_hex = f"0x{hex(d['abs_addr'])[2:].zfill(8).upper()}"
                output_str += f"{addr_hex:<12} | {d['original']:<22} | {d['binary']:<35} | 0x{d['hex']}\n"
            output_str += "\n\n"
            
        output_str += "=== .TEXT BÖLÜMÜ (Çalıştırılabilir Kod) ===\n"
        output_str += f"{'Adres (Hex)':<12} | {'Komut (Instruction)':<22} | {'32-Bit Makine Kodu':<35} | {'Hex Kod'}\n"
        output_str += "-" * 90 + "\n"
        for t in merged_text:
            addr_hex = f"0x{hex(t['abs_addr'])[2:].zfill(8).upper()}"
            output_str += f"{addr_hex:<12} | {t['original']:<22} | {t['binary']:<35} | 0x{t['hex']}\n"
            
        # 2. Global Sembol Tablosunu Formatla
        global_str = f"{'Global Etiket':<20} | {'Mutlak Adres (Hex)'}\n"
        global_str += "-" * 45 + "\n"
        for etiket, adres in global_symbol_table.items():
            global_str += f"{etiket:<20} | 0x{hex(adres)[2:].zfill(8).upper()}\n"

        # 3. Tüm Semboller (Lokal/Mutlak) Tablosunu Formatla
        local_str = f"{'Dosya Index':<12} | {'Etiket':<20} | {'Mutlak Adres':<15} | {'Tür'}\n"
        local_str += "-" * 65 + "\n"
        for sym in all_symbols:
            tur = "Global" if sym['is_global'] else "Yerel (Local)"
            local_str += f"Dosya {sym['file_idx']:<6} | {sym['label']:<20} | 0x{hex(sym['abs_addr'])[2:].zfill(8).upper():<13} | {tur}\n"

        # 4. Relocation Tablosunu Formatla
        reloc_str = f"{'Dosya Index':<12} | {'Etiket':<20} | {'Current Addr':<15} | {'Target Addr':<15} | {'Offset (Dec)':<15} | {'Type'}\n"
        reloc_str += "-" * 100 + "\n"
        for rel in all_relocations:
            c_addr = f"0x{hex(rel['current_addr'])[2:].zfill(8).upper()}"
            t_addr = f"0x{hex(rel['target_addr'])[2:].zfill(8).upper()}"
            reloc_str += f"Dosya {rel['file_idx']:<6} | {rel['label']:<20} | {c_addr:<15} | {t_addr:<15} | {rel['offset']:<15} | {rel['type']}\n"

        # Arayüz güncellemeleri
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)  
        output_text.insert(tk.END, output_str)
        output_text.config(state=tk.DISABLED)

        tab_global_text.config(state=tk.NORMAL)
        tab_global_text.delete("1.0", tk.END)
        tab_global_text.insert(tk.END, global_str)
        tab_global_text.config(state=tk.DISABLED)

        tab_local_text.config(state=tk.NORMAL)
        tab_local_text.delete("1.0", tk.END)
        tab_local_text.insert(tk.END, local_str)
        tab_local_text.config(state=tk.DISABLED)

        tab_reloc_text.config(state=tk.NORMAL)
        tab_reloc_text.delete("1.0", tk.END)
        tab_reloc_text.insert(tk.END, reloc_str)
        tab_reloc_text.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Hata", f"Derleme veya Bağlama (Linking) sırasında bir hata oluştu:\n{str(e)}")


# --- TASARIM ---
pencere = tk.Tk()
pencere.title("RV32I Assembler & Linker")
pencere.geometry("1400x850")
pencere.configure(bg="#2b2b2b")

# Stil ayarları (Notebook için)
style = ttk.Style()
style.theme_use('default')
style.configure("TNotebook", background="#2b2b2b", borderwidth=0)
style.configure("TNotebook.Tab", background="#3c3f41", foreground="#ffffff", padding=[10, 5], font=("Courier New", 10, "bold"))
style.map("TNotebook.Tab", background=[("selected", "#007acc")])

font_baslik = ("Courier New", 11, "bold")
font_kod = ("Consolas", 10)

tk.Label(pencere, text="RV32I Assembler & Linker (Çoklu Dosya)", font=("Courier New", 18, "bold"), bg="#2b2b2b", fg="#ffffff").pack(pady=10)

ust_frame = tk.Frame(pencere, bg="#2b2b2b")
ust_frame.pack(fill=tk.BOTH, expand=True, padx=20)

sol_frame = tk.Frame(ust_frame, bg="#2b2b2b")
sol_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

tk.Label(sol_frame, text="Kaynak Dosyalar (.asm)", font=font_baslik, bg="#2b2b2b", fg="#00ff00").pack(anchor="w", pady=(0,5))

list_frame = tk.Frame(sol_frame, bg="#1e1e1e")
list_frame.pack(fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
listbox = tk.Listbox(list_frame, font=font_kod, bg="#1e1e1e", fg="#ffffff", selectbackground="#007acc", yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
scrollbar.config(command=listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Dosya Yönetim Butonları 1
btn_frame_1 = tk.Frame(sol_frame, bg="#2b2b2b")
btn_frame_1.pack(fill=tk.X, pady=(10, 5))

btn_ekle = tk.Button(btn_frame_1, text="[+] Dosya Ekle", font=font_baslik, bg="#4CAF50", fg="white", command=dosya_ekle)
btn_ekle.pack(side=tk.LEFT, padx=(0, 10))

btn_cikar = tk.Button(btn_frame_1, text="[-] Seçili Dosyayı Çıkar", font=font_baslik, bg="#F44336", fg="white", command=dosya_cikar)
btn_cikar.pack(side=tk.LEFT)

sag_frame = tk.Frame(ust_frame, bg="#2b2b2b")
sag_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
tk.Label(sag_frame, text="Makine Kodu (Linked Çıktı)", font=font_baslik, bg="#2b2b2b", fg="#ffaa00").pack(anchor="w", pady=(0,5))
output_text = scrolledtext.ScrolledText(sag_frame, font=font_kod, bg="#1e1e1e", fg="#00ffff", state=tk.DISABLED)
output_text.pack(fill=tk.BOTH, expand=True)

# Alt Çerçeve (Tablolar için Notebook)
alt_frame = tk.Frame(pencere, bg="#2b2b2b")
alt_frame.pack(fill=tk.X, padx=20, pady=10)

tk.Label(alt_frame, text="🔍 Linker Tabloları", font=font_baslik, bg="#2b2b2b", fg="#e066ff").pack(anchor="w", pady=(0,5))

table_notebook = ttk.Notebook(alt_frame)
table_notebook.pack(fill=tk.X)

# Sekme: Global Semboller
tab_global = tk.Frame(table_notebook, bg="#1e1e1e")
table_notebook.add(tab_global, text="Global Semboller")
tab_global_text = scrolledtext.ScrolledText(tab_global, font=font_kod, bg="#1e1e1e", fg="#e066ff", state=tk.DISABLED, height=6)
tab_global_text.pack(fill=tk.X)

# Sekme: Tüm Semboller (Lokal/Mutlak)
tab_local = tk.Frame(table_notebook, bg="#1e1e1e")
table_notebook.add(tab_local, text="Tüm Semboller (Mutlak Değer Tablosu)")
tab_local_text = scrolledtext.ScrolledText(tab_local, font=font_kod, bg="#1e1e1e", fg="#4CAF50", state=tk.DISABLED, height=6)
tab_local_text.pack(fill=tk.X)

# Sekme: Relocation Tablosu
tab_reloc = tk.Frame(table_notebook, bg="#1e1e1e")
table_notebook.add(tab_reloc, text="Relocation Tablosu")
tab_reloc_text = scrolledtext.ScrolledText(tab_reloc, font=font_kod, bg="#1e1e1e", fg="#ffaa00", state=tk.DISABLED, height=6)
tab_reloc_text.pack(fill=tk.X)

# Butonlar
alt_buton_frame = tk.Frame(pencere, bg="#2b2b2b")
alt_buton_frame.pack(pady=10)

cevir_butonu = tk.Button(alt_buton_frame, text="► Seçili Dosyaları Derle & Bağla", font=("Courier New", 14, "bold"), bg="#007acc", fg="white", activebackground="#005999", command=cevir_butonuna_tiklandi)
cevir_butonu.pack(side=tk.LEFT, padx=10)

kaydet_butonu = tk.Button(alt_buton_frame, text="💾 Hex Dosyasını Dışa Aktar (Export)", font=("Courier New", 14, "bold"), bg="#ff9800", fg="white", activebackground="#e68a00", command=hex_kaydet)
kaydet_butonu.pack(side=tk.LEFT, padx=10)

pencere.mainloop()