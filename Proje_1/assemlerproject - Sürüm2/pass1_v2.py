def pass_one_v2(ham_kod):
    symbol_table = {}
    temiz_kod = []
    
    current_segment = '.text'
    text_sayaci = 0
    data_sayaci = 0
    
    for satir in ham_kod:
        satir = satir.split('#')[0].strip()
        if not satir:
            continue
            
        if satir == '.data':
            current_segment = '.data'
            temiz_kod.append(satir)
            continue
        elif satir == '.text':
            current_segment = '.text'
            temiz_kod.append(satir)
            continue
            
        if satir.startswith('.global'):
            etiket = satir.split()[1]
            if etiket not in symbol_table:
                # Başlangıçta segment bilinmiyor, sonradan aşağıda güncellenecek
                symbol_table[etiket] = {'adres': None, 'tip': 'global', 'segment': 'BİLİNMİYOR'}
            else:
                symbol_table[etiket]['tip'] = 'global'
            continue
        elif satir.startswith('.extern'):
            etiket = satir.split()[1]
            symbol_table[etiket] = {'adres': None, 'tip': 'extern', 'segment': 'EXTERN'}
            continue
            
        if ':' in satir:
            etiket_parcalari = satir.split(':')
            etiket_adi = etiket_parcalari[0].strip()
            
            adres = text_sayaci if current_segment == '.text' else data_sayaci
                
            if etiket_adi not in symbol_table:
                symbol_table[etiket_adi] = {'adres': adres, 'tip': 'local', 'segment': current_segment}
            else:
                symbol_table[etiket_adi]['adres'] = adres
                symbol_table[etiket_adi]['segment'] = current_segment
                
            kalan_komut = etiket_parcalari[1].strip()
            if not kalan_komut:
                continue
            satir = kalan_komut
            
        if current_segment == '.data':
            if '.word' in satir:
                data_sayaci += 4
                temiz_kod.append(satir)
        elif current_segment == '.text':
            text_sayaci += 4
            temiz_kod.append(satir)
            
    return symbol_table, temiz_kod