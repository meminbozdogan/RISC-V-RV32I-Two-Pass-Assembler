import json

def hex_kodunu_yama(eski_hex, atlama_miktari, komut_tipi):
    """
    Sıfır bırakılmış makine kodunun içine, Linker'ın bulduğu gerçek atlama ofsetini gömer.
    """
    komut_int = int(eski_hex, 16)
    offset = atlama_miktari & 0xFFFFFFFF
    
    if komut_tipi == "J-Type": 
        imm20 = (offset >> 20) & 0x1
        imm10_1 = (offset >> 1) & 0x3FF
        imm11 = (offset >> 11) & 0x1
        imm19_12 = (offset >> 12) & 0xFF
        komut_int |= (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12)
        
    elif komut_tipi == "B-Type": 
        imm12 = (offset >> 12) & 0x1
        imm10_5 = (offset >> 5) & 0x3F
        imm4_1 = (offset >> 1) & 0xF
        imm11 = (offset >> 11) & 0x1
        komut_int |= (imm12 << 31) | (imm10_5 << 25) | (imm4_1 << 8) | (imm11 << 7)

    return f"{komut_int:08X}"

def basit_linker(obj_dosya_isimleri):
    # ====================================================
    # AŞAMA 0: AKILLI BAŞLANGIÇ (ENTRY POINT) BULUCU
    # ====================================================
    yuklenen_objeler = {}
    ana_dosya = None
    
    for dosya_adi in obj_dosya_isimleri:
        with open(dosya_adi, 'r') as f:
            yuklenen_objeler[dosya_adi] = json.load(f)
            
    for dosya_adi, obj in yuklenen_objeler.items():
        if 'main' in obj['symbol_table']:
            if obj['symbol_table']['main']['tip'] in ['local', 'global']:
                ana_dosya = dosya_adi
                break
                
    sirali_dosyalar = []
    if ana_dosya:
        print(f"[SİSTEM] Akıllı Linker: 'main' etiketi tespit edildi. '{ana_dosya}' başa alınıyor!")
        sirali_dosyalar.append(ana_dosya)
        for d in obj_dosya_isimleri:
            if d != ana_dosya:
                sirali_dosyalar.append(d)
    else:
        print("[UYARI] 'main' etiketi bulunamadı! İşleme mevcut sırayla devam ediliyor.")
        sirali_dosyalar = obj_dosya_isimleri

    master_symbol_table = {}  
    nihai_text_segment = []   
    nihai_data_segment = []   
    
    text_base_adresleri = {} 
    data_base_adresleri = {} # VERİLER İÇİN YENİ OFSET HARİTASI
    
    mevcut_text_offset = 0  
    mevcut_data_offset = 0  
    
    # ====================================================
    # 1. AŞAMA: Harita Çıkar ve Uç Uca Ekle
    # ====================================================
    for dosya_adi in sirali_dosyalar:
        obj = yuklenen_objeler[dosya_adi]
        text_base_adresleri[dosya_adi] = mevcut_text_offset
        data_base_adresleri[dosya_adi] = mevcut_data_offset
        
        for etiket, bilgi in obj['symbol_table'].items():
            if bilgi['tip'] in ['local', 'global'] and bilgi['adres'] is not None:
                # Segment'e göre doğru ofseti ekle!
                segment_turu = bilgi.get('segment', '.text')
                if segment_turu == '.data':
                    gercek_adres = bilgi['adres'] + mevcut_data_offset
                else:
                    gercek_adres = bilgi['adres'] + mevcut_text_offset
                    
                master_symbol_table[etiket] = {
                    'adres': gercek_adres, 
                    'tip': bilgi['tip'],
                    'segment': segment_turu # Arayüz için not düşüyoruz
                }
        
        nihai_text_segment.extend(obj['text_segment'])
        nihai_data_segment.extend(obj['data_segment'])
        
        mevcut_text_offset += obj['header']['text_size']
        mevcut_data_offset += obj['header']['data_size']

    # ====================================================
    # 2. AŞAMA: BÜYÜK DİKİŞ (YAMAMA)
    # ====================================================
    for dosya_adi in sirali_dosyalar:
        obj = yuklenen_objeler[dosya_adi]
        base_adres = text_base_adresleri[dosya_adi]
        
        for reloc_notu in obj['relocation_table']:
            hedef_sembol = reloc_notu['hedef_sembol']
            komut_tipi = reloc_notu['komut_tipi']
            komut_indexi = int(reloc_notu['adres'] / 4) 
            sorunlu_komutun_kendi_adresi = reloc_notu['adres'] + base_adres
            
            if hedef_sembol in master_symbol_table:
                hedef_gercek_adres = master_symbol_table[hedef_sembol]['adres']
                atlama_miktari = hedef_gercek_adres - sorunlu_komutun_kendi_adresi
                
                eski_hex = obj['text_segment'][komut_indexi]
                
                # İşte az önce bulunamayan o kritik fonksiyonu çağırıyoruz!
                yeni_hex = hex_kodunu_yama(eski_hex, atlama_miktari, komut_tipi)
                
                gercek_index = int(sorunlu_komutun_kendi_adresi / 4)
                nihai_text_segment[gercek_index] = yeni_hex
                print(f"[BAŞARILI] '{hedef_sembol}' bağlandı. Ofset: {atlama_miktari}. Yeni Kod: {yeni_hex}")
            else:
                print(f"[HATA] Linker Error: '{hedef_sembol}' bulunamadı!")
                return None

    # ====================================================
    # 3. AŞAMA: DOSYA ÇIKTILARI
    # ====================================================
    with open('instruction_bram.hex', 'w') as f:
        for hex_kod in nihai_text_segment: f.write(f"{hex_kod}\n")
            
    with open('data_bram.hex', 'w') as f:
        for hex_kod in nihai_data_segment: f.write(f"{hex_kod}\n")

    return master_symbol_table