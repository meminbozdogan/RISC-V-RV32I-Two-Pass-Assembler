#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UART Yükleyici (Loader) - Ana Bilgisayar Tarafı

Bu betik, linker tarafından üretilen hex dosyalarını UART seri haberleşme
üzerinden FPGA'ya gönderir. Paket tabanlı protokol ile veri bütünlüğü
sağlanır ve her paket için ACK/NACK doğrulaması yapılır.

Paket Formatı:
    [SYNC(0xAA)] [CMD] [LEN_LO] [LEN_HI] [PAYLOAD...] [CHECKSUM]

Kullanım:
    python loader_host.py --port COM3 --baud 115200 --file program.hex
"""

import argparse
import struct
import sys
import time

import serial
import serial.tools.list_ports


class UARTLoader:
    """
    FPGA'ya UART üzerinden program yüklemek için kullanılan sınıf.

    Linker çıktısı olan hex dosyasını okur, paketlere böler ve
    seri port üzerinden FPGA'ya güvenilir biçimde aktarır.
    """

    # --- Protokol Sabitleri ---
    SYNC = 0xAA                # Senkronizasyon baytı
    CMD_DATA_WRITE = 0x01      # Veri yazma komutu
    CMD_BOOT_CPU = 0x02        # İşlemciyi başlatma komutu
    CMD_ACK = 0x03             # Onay yanıtı (FPGA'dan)
    CMD_NACK = 0x04            # Ret yanıtı (FPGA'dan)
    MAX_PAYLOAD_SIZE = 256     # Paket başına maksimum yük boyutu (bayt) = 64 kelime
    MAX_RETRIES = 3            # Başarısız gönderimde tekrar deneme sayısı
    RESPONSE_TIMEOUT = 2.0     # Yanıt bekleme zaman aşımı (saniye)

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        """
        Seri portu açar ve UART bağlantısını başlatır.

        Args:
            port: Seri port adı (örn. 'COM3' veya '/dev/ttyUSB0')
            baudrate: Baud hızı (varsayılan: 115200)
            timeout: Okuma zaman aşımı süresi (saniye)

        Raises:
            serial.SerialException: Port açılamazsa hata fırlatır.
        """
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            # Bağlantı kararlılığı için kısa bir bekleme
            time.sleep(0.1)
            # Tamponu temizle
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"[BİLGİ] Seri port açıldı: {port} @ {baudrate} baud")
        except serial.SerialException as e:
            raise serial.SerialException(
                f"[HATA] Seri port açılamadı ({port}): {e}"
            ) from e

    def calculate_checksum(self, data: bytes) -> int:
        """
        8 bitlik sağlama toplamını (checksum) hesaplar.

        Formül: (~toplam(veri)) & 0xFF
        Doğrulama: (toplam(veri) + checksum) & 0xFF == 0xFF

        Args:
            data: Sağlama toplamı hesaplanacak bayt dizisi
                  (CMD + LEN_LO + LEN_HI + PAYLOAD)

        Returns:
            Hesaplanan 8 bitlik sağlama toplamı değeri
        """
        toplam = sum(data) & 0xFF
        return (~toplam) & 0xFF

    def build_packet(self, cmd: int, payload: bytes = b'') -> bytes:
        """
        Gönderilecek komple paketi oluşturur.

        Paket yapısı:
            SYNC(1) + CMD(1) + LEN_LO(1) + LEN_HI(1) + PAYLOAD(N) + CHECKSUM(1)

        Args:
            cmd: Komut baytı (CMD_DATA_WRITE veya CMD_BOOT_CPU)
            payload: Gönderilecek veri yükü (varsayılan: boş)

        Returns:
            Gönderime hazır paket bayt dizisi
        """
        # Yük uzunluğunu 2 bayt little-endian olarak kodla
        uzunluk = len(payload)
        len_lo = uzunluk & 0xFF
        len_hi = (uzunluk >> 8) & 0xFF

        # Sağlama toplamı için veriyi hazırla (CMD + LEN_LO + LEN_HI + PAYLOAD)
        checksum_verisi = bytes([cmd, len_lo, len_hi]) + payload
        checksum = self.calculate_checksum(checksum_verisi)

        # Komple paketi birleştir
        paket = bytes([self.SYNC, cmd, len_lo, len_hi]) + payload + bytes([checksum])
        return paket

    def wait_for_response(self):
        """
        FPGA'dan ACK veya NACK yanıt paketini bekler ve ayrıştırır.

        Beklenen yanıt formatı (5 bayt):
            SYNC(1) + CMD(1) + LEN_LO(1) + LEN_HI(1) + CHECKSUM(1)

        Returns:
            int veya None: CMD_ACK (0x03) veya CMD_NACK (0x04) döner.
                           Zaman aşımı veya geçersiz pakette None döner.
        """
        try:
            # SYNC baytını ara
            baslangic_zamani = time.time()
            while time.time() - baslangic_zamani < self.RESPONSE_TIMEOUT:
                bayt = self.ser.read(1)
                if len(bayt) == 0:
                    # Zaman aşımı - veri gelmedi
                    print("[UYARI] Yanıt bekleme zaman aşımı")
                    return None
                if bayt[0] == self.SYNC:
                    break
            else:
                print("[UYARI] SYNC baytı bulunamadı, zaman aşımı")
                return None

            # Kalan 4 baytı oku (CMD + LEN_LO + LEN_HI + CHECKSUM)
            kalan = self.ser.read(4)
            if len(kalan) < 4:
                print("[UYARI] Eksik yanıt paketi alındı")
                return None

            yanit_cmd = kalan[0]
            len_lo = kalan[1]
            len_hi = kalan[2]
            checksum = kalan[3]

            # Sağlama toplamını doğrula
            dogrulama_verisi = bytes([yanit_cmd, len_lo, len_hi])
            beklenen_checksum = self.calculate_checksum(dogrulama_verisi)

            if checksum != beklenen_checksum:
                print(
                    f"[UYARI] Sağlama toplamı uyuşmazlığı: "
                    f"beklenen=0x{beklenen_checksum:02X}, alınan=0x{checksum:02X}"
                )
                return None

            # Komut tipini kontrol et
            if yanit_cmd == self.CMD_ACK:
                return self.CMD_ACK
            elif yanit_cmd == self.CMD_NACK:
                return self.CMD_NACK
            else:
                print(f"[UYARI] Bilinmeyen yanıt komutu: 0x{yanit_cmd:02X}")
                return None

        except serial.SerialException as e:
            print(f"[HATA] Yanıt okuma hatası: {e}")
            return None

    def send_packet_with_retry(self, cmd: int, payload: bytes = b'') -> bool:
        """
        Paketi gönderir ve ACK yanıtı bekler. Başarısızlıkta yeniden dener.

        NACK veya zaman aşımı durumunda MAX_RETRIES kadar tekrar denenir.

        Args:
            cmd: Komut baytı
            payload: Veri yükü

        Returns:
            True: ACK alındı, gönderim başarılı
            False: Tüm denemeler başarısız oldu
        """
        paket = self.build_packet(cmd, payload)

        for deneme in range(1, self.MAX_RETRIES + 1):
            try:
                # Giriş tamponunu temizle (eski veriler varsa)
                self.ser.reset_input_buffer()

                # Paketi gönder
                self.ser.write(paket)
                self.ser.flush()

                # Yanıt bekle
                yanit = self.wait_for_response()

                if yanit == self.CMD_ACK:
                    return True
                elif yanit == self.CMD_NACK:
                    print(
                        f"[UYARI] NACK alındı (deneme {deneme}/{self.MAX_RETRIES})"
                    )
                else:
                    print(
                        f"[UYARI] Yanıt alınamadı (deneme {deneme}/{self.MAX_RETRIES})"
                    )

            except serial.SerialException as e:
                print(
                    f"[HATA] Gönderim hatası (deneme {deneme}/{self.MAX_RETRIES}): {e}"
                )

            # Tekrar denemeden önce kısa bekleme
            if deneme < self.MAX_RETRIES:
                time.sleep(0.2)

        print("[HATA] Tüm gönderim denemeleri başarısız oldu")
        return False

    def load_hex_file(self, filepath: str) -> bytes:
        """
        Linker çıktısı hex dosyasını okur ve makine koduna dönüştürür.

        Her satır 8 onaltılık karakter içerir (32 bit kelime).
        Her kelime 4 bayt little-endian formatına dönüştürülür.

        Args:
            filepath: Hex dosyasının yolu

        Returns:
            Tüm kelimelerin little-endian bayt olarak birleştirilmiş hali

        Raises:
            FileNotFoundError: Dosya bulunamazsa hata fırlatır.
            ValueError: Geçersiz hex verisi varsa hata fırlatır.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as dosya:
                satirlar = dosya.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"[HATA] Hex dosyası bulunamadı: {filepath}"
            )
        except IOError as e:
            raise IOError(f"[HATA] Dosya okuma hatası: {e}") from e

        makine_kodu = bytearray()
        satir_no = 0

        for satir in satirlar:
            satir_no += 1
            satir = satir.strip()

            # Boş satırları ve yorum satırlarını atla
            if not satir or satir.startswith('#') or satir.startswith('//'):
                continue

            # Her satırda tam olarak 8 hex karakter bekleniyor
            if len(satir) != 8:
                raise ValueError(
                    f"[HATA] Satır {satir_no}: Geçersiz uzunluk "
                    f"(beklenen: 8 karakter, bulunan: {len(satir)}): '{satir}'"
                )

            try:
                # Hex stringi 32 bit tamsayıya çevir
                kelime = int(satir, 16)
            except ValueError:
                raise ValueError(
                    f"[HATA] Satır {satir_no}: Geçersiz onaltılık değer: '{satir}'"
                )

            # 32 bit kelimeyi 4 bayt little-endian olarak ekle
            makine_kodu.extend(struct.pack('<I', kelime))

        if len(makine_kodu) == 0:
            raise ValueError("[HATA] Hex dosyası boş veya geçerli veri içermiyor")

        kelime_sayisi = len(makine_kodu) // 4
        print(
            f"[BİLGİ] Hex dosyası yüklendi: {kelime_sayisi} kelime "
            f"({len(makine_kodu)} bayt)"
        )
        return bytes(makine_kodu)

    def upload_to_fpga(self, filepath: str, progress_callback=None) -> bool:
        """
        Hex dosyasını FPGA'ya yükler ve işlemciyi başlatır.

        İşlem adımları:
            1. Hex dosyasını oku ve makine koduna dönüştür
            2. Veriyi MAX_PAYLOAD_SIZE baytlık parçalara böl
            3. Her parçayı DATA_WRITE paketi olarak gönder
            4. Tüm veri gönderildikten sonra BOOT_CPU komutu gönder

        Args:
            filepath: Hex dosyasının yolu
            progress_callback: İlerleme bildirimi fonksiyonu
                               callback(mevcut_paket, toplam_paket) şeklinde çağrılır

        Returns:
            True: Yükleme ve başlatma başarılı
            False: Yükleme veya başlatma başarısız
        """
        # Hex dosyasını yükle
        try:
            makine_kodu = self.load_hex_file(filepath)
        except (FileNotFoundError, ValueError, IOError) as e:
            print(str(e))
            return False

        # Veriyi parçalara ayır
        parcalar = []
        for i in range(0, len(makine_kodu), self.MAX_PAYLOAD_SIZE):
            parca = makine_kodu[i:i + self.MAX_PAYLOAD_SIZE]
            parcalar.append(parca)

        toplam_paket = len(parcalar)
        print(f"[BİLGİ] Toplam {toplam_paket} paket gönderilecek")
        print("-" * 50)

        # Her parçayı DATA_WRITE paketi olarak gönder
        for idx, parca in enumerate(parcalar):
            mevcut_paket = idx + 1
            basarili = self.send_packet_with_retry(self.CMD_DATA_WRITE, parca)

            if not basarili:
                print(
                    f"[HATA] Paket {mevcut_paket}/{toplam_paket} gönderilemedi. "
                    f"Yükleme iptal edildi."
                )
                return False

            # İlerleme bildirimini çağır
            if progress_callback is not None:
                progress_callback(mevcut_paket, toplam_paket)

        print("-" * 50)
        print("[BİLGİ] Tüm veri paketleri başarıyla gönderildi")

        # BOOT_CPU komutu gönder
        print("[BİLGİ] İşlemci başlatma komutu (BOOT_CPU) gönderiliyor...")
        basarili = self.send_packet_with_retry(self.CMD_BOOT_CPU)

        if basarili:
            print("[BİLGİ] İşlemci başarıyla başlatıldı!")
            return True
        else:
            print("[HATA] İşlemci başlatma komutu başarısız oldu")
            return False

    @staticmethod
    def get_available_ports() -> list:
        """
        Sistemde mevcut olan seri portları listeler.

        Returns:
            Kullanılabilir COM port adlarının listesi
        """
        portlar = serial.tools.list_ports.comports()
        port_listesi = [port.device for port in portlar]
        return port_listesi

    def close(self):
        """
        Seri port bağlantısını kapatır.

        Açık olan portu güvenli biçimde kapatır ve kaynakları serbest bırakır.
        """
        if hasattr(self, 'ser') and self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[BİLGİ] Seri port kapatıldı")


def upload_program(port: str, filepath: str, baudrate: int = 115200,
                   progress_callback=None) -> bool:
    """
    Arayüzden doğrudan çağrılabilecek wrapper fonksiyon.

    UARTLoader sınıfını kullanarak hex dosyasını FPGA'ya yükler.
    Bağlantı açma/kapama işlemlerini otomatik olarak yönetir.

    Args:
        port: Seri port adı (örn. 'COM3')
        filepath: Hex dosyasının yolu
        baudrate: Baud hızı (varsayılan: 115200)
        progress_callback: İlerleme bildirimi fonksiyonu
                           callback(mevcut_paket, toplam_paket) şeklinde çağrılır

    Returns:
        True: Yükleme başarılı
        False: Yükleme başarısız
    """
    loader = UARTLoader(port, baudrate)
    try:
        result = loader.upload_to_fpga(filepath, progress_callback)
        return result
    finally:
        loader.close()


def _konsol_ilerleme(mevcut: int, toplam: int):
    """
    Konsola ilerleme çubuğu yazdıran yardımcı fonksiyon.

    Args:
        mevcut: Gönderilen paket numarası
        toplam: Toplam paket sayısı
    """
    yuzde = (mevcut / toplam) * 100
    cubuk_uzunluk = 30
    dolu = int(cubuk_uzunluk * mevcut / toplam)
    cubuk = '█' * dolu + '░' * (cubuk_uzunluk - dolu)
    print(f"\r  [{cubuk}] {yuzde:5.1f}% ({mevcut}/{toplam})", end='', flush=True)
    if mevcut == toplam:
        print()  # Son pakette yeni satıra geç


if __name__ == '__main__':
    # Komut satırı argümanlarını ayrıştır
    # Örnek kullanım:
    #   python loader_host.py --port COM3 --baud 115200 --file program.hex
    #   python loader_host.py --port COM5 --file cikti.hex
    #   python loader_host.py --list-ports

    parser = argparse.ArgumentParser(
        description='FPGA UART Yükleyici - Hex dosyasını FPGA\'ya gönderir',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnek Kullanım:
  %(prog)s --port COM3 --file program.hex
  %(prog)s --port COM3 --baud 9600 --file program.hex
  %(prog)s --list-ports
        """
    )
    parser.add_argument(
        '--port',
        type=str,
        help='Seri port adı (örn. COM3, /dev/ttyUSB0)'
    )
    parser.add_argument(
        '--baud',
        type=int,
        default=115200,
        help='Baud hızı (varsayılan: 115200)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Yüklenecek hex dosyasının yolu'
    )
    parser.add_argument(
        '--list-ports',
        action='store_true',
        help='Mevcut seri portları listele ve çık'
    )

    args = parser.parse_args()

    # Mevcut portları listeleme modu
    if args.list_ports:
        portlar = UARTLoader.get_available_ports()
        if portlar:
            print("Kullanılabilir seri portlar:")
            for p in portlar:
                print(f"  - {p}")
        else:
            print("Hiçbir seri port bulunamadı.")
        sys.exit(0)

    # Zorunlu argümanları kontrol et
    if not args.port:
        print("[HATA] --port parametresi belirtilmelidir.")
        print("       Mevcut portları görmek için: --list-ports")
        parser.print_help()
        sys.exit(1)

    if not args.file:
        print("[HATA] --file parametresi belirtilmelidir.")
        parser.print_help()
        sys.exit(1)

    # Yükleme işlemini başlat
    print("=" * 50)
    print("   FPGA UART Yükleyici")
    print("=" * 50)
    print(f"  Port     : {args.port}")
    print(f"  Baud     : {args.baud}")
    print(f"  Dosya    : {args.file}")
    print("=" * 50)

    try:
        sonuc = upload_program(
            port=args.port,
            filepath=args.file,
            baudrate=args.baud,
            progress_callback=_konsol_ilerleme
        )

        if sonuc:
            print("\n✓ Program FPGA'ya başarıyla yüklendi!")
            sys.exit(0)
        else:
            print("\n✗ Program yükleme başarısız oldu!")
            sys.exit(1)

    except serial.SerialException as e:
        print(f"\n[HATA] Seri port hatası: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[BİLGİ] Kullanıcı tarafından iptal edildi.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[HATA] Beklenmeyen hata: {e}")
        sys.exit(1)
