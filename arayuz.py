import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import json
import threading
import tempfile

from assembler import assemble
from linker import link
from loader_host import UARTLoader, upload_program

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

def com_portlarini_yenile():
    """Mevcut COM portlarını tarayıp combobox'a yükler."""
    portlar = UARTLoader.get_available_ports()
    combo_port['values'] = portlar if portlar else ["Port bulunamadı"]
    if portlar:
        combo_port.set(portlar[0])
    else:
        combo_port.set("Port bulunamadı")

def fpga_yukle():
    """Derlenmiş makine kodunu UART üzerinden FPGA'ya yükler."""
    global son_merged_text, son_merged_data

    # Derleme yapılmış mı kontrol et
    if not son_merged_text and not son_merged_data:
        messagebox.showwarning("Uyarı", "Yüklenecek makine kodu bulunamadı.\nLütfen önce 'Derle & Bağla' işlemini yapın.")
        return

    # Seçili port kontrolü
    secili_port = combo_port.get()
    if not secili_port or secili_port == "Port bulunamadı":
        messagebox.showwarning("Uyarı", "Geçerli bir seri port seçin.\nPortları yenilemek için 🔄 butonuna basın.")
        return

    # Baud rate al
    try:
        baud = int(combo_baud.get())
    except ValueError:
        messagebox.showwarning("Uyarı", "Geçersiz baud rate değeri.")
        return

    # Geçici hex dosyası oluştur
    try:
        temp_dir = tempfile.gettempdir()
        temp_hex_path = os.path.join(temp_dir, "fpga_loader_temp.hex")
        with open(temp_hex_path, "w", encoding="utf-8") as f:
            if son_merged_text:
                for t in son_merged_text:
                    f.write(f"{t['hex']}\n")
            if son_merged_data:
                for d in son_merged_data:
                    f.write(f"{d['hex']}\n")
    except Exception as e:
        messagebox.showerror("Hata", f"Geçici hex dosyası oluşturulamadı:\n{str(e)}")
        return

    # UI elemanlarını güncelle
    btn_fpga_yukle.config(state=tk.DISABLED, text="⏳ Yükleniyor...")
    progress_bar['value'] = 0
    lbl_durum.config(text="🔌 Bağlanıyor...")
    pencere.update_idletasks()

    def ilerleme_guncelle(mevcut, toplam):
        """İlerleme çubuğunu ve durum etiketini günceller (thread-safe)."""
        yuzde = int((mevcut / toplam) * 100)
        def guncelle():
            progress_bar['value'] = yuzde
            lbl_durum.config(text=f"📡 Gönderiliyor... Paket {mevcut}/{toplam} ({yuzde}%)")
        pencere.after(0, guncelle)

    def yukleme_islemi():
        """Yükleme işlemini ayrı bir thread'de çalıştırır."""
        try:
            sonuc, sure_ms = upload_program(
                port=secili_port,
                filepath=temp_hex_path,
                baudrate=baud,
                progress_callback=ilerleme_guncelle
            )
            def bitir():
                if sonuc:
                    progress_bar['value'] = 100
                    lbl_durum.config(text=f"✅ Yükleme başarılı! Süre: {sure_ms:.2f} ms")
                    messagebox.showinfo("Başarılı", f"Program FPGA'ya başarıyla yüklendi!\nYükleme süresi: {sure_ms:.2f} ms")
                else:
                    lbl_durum.config(text="❌ Yükleme başarısız!")
                    messagebox.showerror("Hata", "FPGA'ya program yükleme başarısız oldu.\nBağlantıyı ve portu kontrol edin.")
                btn_fpga_yukle.config(state=tk.NORMAL, text="🚀 FPGA'ya Yükle")
            pencere.after(0, bitir)

        except Exception as e:
            def hata_goster():
                lbl_durum.config(text=f"❌ Hata: {str(e)[:50]}")
                messagebox.showerror("Hata", f"Yükleme sırasında hata oluştu:\n{str(e)}")
                btn_fpga_yukle.config(state=tk.NORMAL, text="🚀 FPGA'ya Yükle")
            pencere.after(0, hata_goster)

        finally:
            # Geçici dosyayı temizle
            try:
                os.remove(temp_hex_path)
            except:
                pass

    # Yükleme işlemini arka plan thread'inde başlat
    yukle_thread = threading.Thread(target=yukleme_islemi, daemon=True)
    yukle_thread.start()

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
                parsed_files.append((order, ham_kod, dosya_yolu))
        
        # .start numarasına göre sırala
        parsed_files.sort(key=lambda x: x[0])
        
        objects = []
        for order, ham_kod, dosya_yolu in parsed_files:
            obj = assemble(ham_kod)
            if obj:
                # O Dosyasını oluştur (JSON formatında kaydet)
                obj_yolu = dosya_yolu.replace(".asm", ".o")
                with open(obj_yolu, "w", encoding="utf-8") as f:
                    json.dump(obj, f, indent=4)
                
                # O Dosyasını geri oku (Linker için simülasyon)
                with open(obj_yolu, "r", encoding="utf-8") as f:
                    okunan_obj = json.load(f)
                objects.append(okunan_obj)
        
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
alt_buton_frame.pack(pady=5)

cevir_butonu = tk.Button(alt_buton_frame, text="► Seçili Dosyaları Derle & Bağla", font=("Courier New", 14, "bold"), bg="#007acc", fg="white", activebackground="#005999", command=cevir_butonuna_tiklandi)
cevir_butonu.pack(side=tk.LEFT, padx=10)

kaydet_butonu = tk.Button(alt_buton_frame, text="💾 Hex Dosyasını Dışa Aktar (Export)", font=("Courier New", 14, "bold"), bg="#ff9800", fg="white", activebackground="#e68a00", command=hex_kaydet)
kaydet_butonu.pack(side=tk.LEFT, padx=10)

# === FPGA UART Yükleyici Paneli ===
fpga_frame = tk.LabelFrame(pencere, text="🔧 FPGA UART Yükleyici", font=("Courier New", 11, "bold"), bg="#2b2b2b", fg="#00e5ff", bd=2, relief=tk.GROOVE)
fpga_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

# Üst satır: Port seçimi, baud rate, butonlar
fpga_ust = tk.Frame(fpga_frame, bg="#2b2b2b")
fpga_ust.pack(fill=tk.X, padx=10, pady=5)

# COM Port etiketi ve seçici
tk.Label(fpga_ust, text="Seri Port:", font=("Courier New", 10), bg="#2b2b2b", fg="#ffffff").pack(side=tk.LEFT, padx=(0, 5))
combo_port = ttk.Combobox(fpga_ust, width=12, font=("Courier New", 10), state="readonly")
combo_port.pack(side=tk.LEFT, padx=(0, 5))
combo_port.set("Seçiniz...")

# Port yenile butonu
btn_port_yenile = tk.Button(fpga_ust, text="🔄", font=("Courier New", 10), bg="#3c3f41", fg="white", width=3, command=com_portlarini_yenile)
btn_port_yenile.pack(side=tk.LEFT, padx=(0, 15))

# Baud Rate etiketi ve seçici
tk.Label(fpga_ust, text="Baud:", font=("Courier New", 10), bg="#2b2b2b", fg="#ffffff").pack(side=tk.LEFT, padx=(0, 5))
combo_baud = ttk.Combobox(fpga_ust, width=8, font=("Courier New", 10), state="readonly", values=["9600", "19200", "38400", "57600", "115200", "230400", "460800"])
combo_baud.pack(side=tk.LEFT, padx=(0, 15))
combo_baud.set("115200")

# FPGA'ya Yükle butonu
btn_fpga_yukle = tk.Button(fpga_ust, text="🚀 FPGA'ya Yükle", font=("Courier New", 12, "bold"), bg="#e91e63", fg="white", activebackground="#c2185b", command=fpga_yukle)
btn_fpga_yukle.pack(side=tk.LEFT, padx=10)

# Alt satır: İlerleme çubuğu ve durum
fpga_alt = tk.Frame(fpga_frame, bg="#2b2b2b")
fpga_alt.pack(fill=tk.X, padx=10, pady=(0, 5))

# İlerleme çubuğu
style.configure("Custom.Horizontal.TProgressbar", troughcolor="#1e1e1e", background="#00e676", thickness=18)
progress_bar = ttk.Progressbar(fpga_alt, orient=tk.HORIZONTAL, length=400, mode='determinate', style="Custom.Horizontal.TProgressbar")
progress_bar.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

# Durum etiketi
lbl_durum = tk.Label(fpga_alt, text="⏸ Hazır - Program derleyip FPGA'ya yükleyebilirsiniz", font=("Courier New", 9), bg="#2b2b2b", fg="#aaaaaa", anchor="w")
lbl_durum.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Başlangıçta portları otomatik tara
pencere.after(500, com_portlarini_yenile)

pencere.mainloop()