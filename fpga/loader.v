//=============================================================================
// Modül       : loader
// Açıklama    : UART Tabanlı Program Yükleyici (Loader) Durum Makinesi
//               - Host bilgisayardan gelen UART paketlerini çözümler
//               - Makine kodunu RAM'e yazar
//               - BOOT_CPU komutuyla işlemciyi başlatır
//               - ACK/NACK yanıtlarını UART TX ile gönderir
//               - loader_host.py ile tam uyumlu protokol
//
// Protokol Formatı:
//   Gelen Paket : [SYNC(0xAA)] [CMD] [LEN_LO] [LEN_HI] [PAYLOAD...] [CHECKSUM]
//   Yanıt Paketi: [SYNC(0xAA)] [CMD] [0x00]   [0x00]   [CHECKSUM]
//
// Komutlar:
//   0x01 = DATA_WRITE : Veri yazma (payload = makine kodu baytları)
//   0x02 = BOOT_CPU   : İşlemciyi başlat (payload yok)
//   0x03 = ACK        : Onay yanıtı (FPGA → Host)
//   0x04 = NACK       : Ret yanıtı  (FPGA → Host)
//
// Checksum:
//   (~toplam(CMD + LEN_LO + LEN_HI + PAYLOAD)) & 0xFF
//
// Yazar       : Otomatik oluşturuldu
// Tarih       : 2026-06-03
//=============================================================================

module loader #(
    parameter RAM_ADDR_WIDTH = 10       // RAM adres genişliği (10 bit = 1024 kelime)
)(
    input  wire        clk,             // Sistem saati
    input  wire        rst_n,           // Aktif düşük sıfırlama

    // UART RX Arayüzü
    input  wire [7:0]  rx_data,         // UART'tan alınan bayt
    input  wire        rx_valid,        // Alınan bayt geçerli sinyali

    // UART TX Arayüzü
    output reg  [7:0]  tx_data,         // UART'a gönderilecek bayt
    output reg         tx_start,        // Gönderim başlatma sinyali
    input  wire        tx_busy,         // TX meşgul sinyali

    // RAM Yazma Arayüzü (Port B)
    output reg  [RAM_ADDR_WIDTH-1:0] ram_addr,   // RAM yazma adresi (kelime)
    output reg  [31:0]               ram_wdata,  // RAM yazma verisi (32-bit)
    output reg                       ram_we,     // RAM yazma etkinleştirme

    // CPU Kontrol
    output reg         cpu_running     // CPU çalışma durumu (1=çalışıyor, 0=durdu)
);

    //=========================================================================
    // Protokol Sabitleri
    //=========================================================================
    localparam [7:0] SYNC           = 8'hAA;
    localparam [7:0] CMD_DATA_WRITE = 8'h01;
    localparam [7:0] CMD_BOOT_CPU   = 8'h02;
    localparam [7:0] CMD_ACK        = 8'h03;
    localparam [7:0] CMD_NACK       = 8'h04;

    //=========================================================================
    // FSM Durumları
    //=========================================================================
    localparam [3:0] S_IDLE          = 4'd0;   // SYNC baytı bekleniyor
    localparam [3:0] S_CMD           = 4'd1;   // Komut baytı bekleniyor
    localparam [3:0] S_LEN_LO        = 4'd2;   // Uzunluk düşük bayt bekleniyor
    localparam [3:0] S_LEN_HI        = 4'd3;   // Uzunluk yüksek bayt bekleniyor
    localparam [3:0] S_PAYLOAD       = 4'd4;   // Payload baytları alınıyor
    localparam [3:0] S_CHECKSUM      = 4'd5;   // Checksum baytı bekleniyor
    localparam [3:0] S_PROCESS       = 4'd6;   // Komutu işle (RAM yaz / CPU başlat)
    localparam [3:0] S_SEND_RESP_0   = 4'd7;   // Yanıt gönder: SYNC baytı
    localparam [3:0] S_SEND_RESP_1   = 4'd8;   // Yanıt gönder: CMD baytı
    localparam [3:0] S_SEND_RESP_2   = 4'd9;   // Yanıt gönder: LEN_LO (0x00)
    localparam [3:0] S_SEND_RESP_3   = 4'd10;  // Yanıt gönder: LEN_HI (0x00)
    localparam [3:0] S_SEND_RESP_4   = 4'd11;  // Yanıt gönder: CHECKSUM

    //=========================================================================
    // Dahili Kayıtçılar
    //=========================================================================
    reg [3:0]  state;                 // Mevcut FSM durumu
    reg [7:0]  cmd_reg;               // Alınan komut baytı
    reg [15:0] payload_len;           // Payload uzunluğu (bayt)
    reg [15:0] byte_cnt;              // Alınan payload bayt sayacı
    reg [7:0]  checksum_acc;          // Çalışan checksum akümülatörü

    // Payload bayt toplama (4 bayt → 1 kelime, little-endian)
    reg [31:0] word_buffer;           // 4 baytı birleştirme tamponu
    reg [1:0]  byte_in_word;          // Kelime içindeki bayt pozisyonu (0-3)

    // RAM yazma adresi sayacı (yükleme boyunca artırılır)
    reg [RAM_ADDR_WIDTH-1:0] write_addr;

    // Yanıt gönderim kaydı
    reg [7:0]  resp_cmd;              // Yanıt komutu (ACK veya NACK)
    reg [7:0]  resp_checksum;         // Yanıt checksum değeri

    //=========================================================================
    // Yanıt Checksum Hesaplama
    // Yanıt paketi: [SYNC][CMD][0x00][0x00][CHECKSUM]
    // Checksum = (~(CMD + 0x00 + 0x00)) & 0xFF = (~CMD) & 0xFF
    //=========================================================================
    wire [7:0] calc_resp_checksum = (~resp_cmd) & 8'hFF;

    //=========================================================================
    // RAM Yazma İşlemi İçin Geçici Sinyaller
    //=========================================================================
    reg        ram_write_pending;     // RAM yazma bekliyor
    reg [31:0] ram_write_data;        // Yazılacak veri
    reg [RAM_ADDR_WIDTH-1:0] ram_write_addr; // Yazılacak adres

    //=========================================================================
    // Ana FSM - Loader Durum Makinesi
    //=========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= S_IDLE;
            cmd_reg         <= 8'd0;
            payload_len     <= 16'd0;
            byte_cnt        <= 16'd0;
            checksum_acc    <= 8'd0;
            word_buffer     <= 32'd0;
            byte_in_word    <= 2'd0;
            write_addr      <= {RAM_ADDR_WIDTH{1'b0}};
            cpu_running     <= 1'b0;
            tx_data         <= 8'd0;
            tx_start        <= 1'b0;
            ram_addr        <= {RAM_ADDR_WIDTH{1'b0}};
            ram_wdata       <= 32'd0;
            ram_we          <= 1'b0;
            resp_cmd        <= 8'd0;
            resp_checksum   <= 8'd0;
            ram_write_pending <= 1'b0;
            ram_write_data  <= 32'd0;
            ram_write_addr  <= {RAM_ADDR_WIDTH{1'b0}};
        end else begin
            // Varsayılan: tek çevrimlik sinyalleri sıfırla
            tx_start <= 1'b0;
            ram_we   <= 1'b0;

            // Bekleyen RAM yazma işlemini gerçekleştir
            if (ram_write_pending) begin
                ram_addr  <= ram_write_addr;
                ram_wdata <= ram_write_data;
                ram_we    <= 1'b1;
                ram_write_pending <= 1'b0;
            end

            case (state)
                //=============================================================
                // S_IDLE: SYNC Baytı Bekleme
                // Her gelen baytı kontrol et, 0xAA ise paket başlangıcı
                //=============================================================
                S_IDLE: begin
                    if (rx_valid) begin
                        if (rx_data == SYNC) begin
                            checksum_acc <= 8'd0;
                            state        <= S_CMD;
                        end
                        // SYNC olmayan baytlar sessizce yoksayılır
                    end
                end

                //=============================================================
                // S_CMD: Komut Baytı Alımı
                //=============================================================
                S_CMD: begin
                    if (rx_valid) begin
                        cmd_reg      <= rx_data;
                        checksum_acc <= rx_data; // Checksum: CMD eklendi
                        state        <= S_LEN_LO;
                    end
                end

                //=============================================================
                // S_LEN_LO: Uzunluk Düşük Bayt
                //=============================================================
                S_LEN_LO: begin
                    if (rx_valid) begin
                        payload_len[7:0] <= rx_data;
                        checksum_acc     <= checksum_acc + rx_data;
                        state            <= S_LEN_HI;
                    end
                end

                //=============================================================
                // S_LEN_HI: Uzunluk Yüksek Bayt
                //=============================================================
                S_LEN_HI: begin
                    if (rx_valid) begin
                        payload_len[15:8] <= rx_data;
                        checksum_acc      <= checksum_acc + rx_data;
                        byte_cnt          <= 16'd0;
                        byte_in_word      <= 2'd0;
                        word_buffer       <= 32'd0;

                        // Payload uzunluğu 0 ise doğrudan checksum'a git
                        // (BOOT_CPU gibi payload'sız komutlar)
                        if ({rx_data, payload_len[7:0]} == 16'd0) begin
                            state <= S_CHECKSUM;
                        end else begin
                            state <= S_PAYLOAD;
                        end
                    end
                end

                //=============================================================
                // S_PAYLOAD: Payload Baytları Alımı
                // Her 4 baytı little-endian 32-bit kelimeye birleştir
                // ve RAM'e yaz
                //=============================================================
                S_PAYLOAD: begin
                    if (rx_valid) begin
                        checksum_acc <= checksum_acc + rx_data;
                        byte_cnt     <= byte_cnt + 16'd1;

                        // Little-endian bayt birleştirme
                        case (byte_in_word)
                            2'd0: word_buffer[ 7: 0] <= rx_data;
                            2'd1: word_buffer[15: 8] <= rx_data;
                            2'd2: word_buffer[23:16] <= rx_data;
                            2'd3: begin
                                // 4. bayt geldi → kelime tamamlandı
                                // DATA_WRITE ise RAM'e yaz
                                if (cmd_reg == CMD_DATA_WRITE) begin
                                    ram_write_pending <= 1'b1;
                                    ram_write_data    <= {rx_data, word_buffer[23:0]};
                                    ram_write_addr    <= write_addr;
                                    write_addr        <= write_addr + 1'b1;
                                end
                            end
                        endcase

                        byte_in_word <= byte_in_word + 2'd1;

                        // Tüm payload baytları alındı mı?
                        // payload_len birleşik değer: {payload_len[15:8], payload_len[7:0]}
                        if ((byte_cnt + 16'd1) == {payload_len[15:8], payload_len[7:0]}) begin
                            state <= S_CHECKSUM;
                        end
                    end
                end

                //=============================================================
                // S_CHECKSUM: Sağlama Toplamı Doğrulama
                // Beklenen: (~checksum_acc) & 0xFF == alınan checksum
                // Yani: (checksum_acc + alınan) & 0xFF == 0xFF
                //=============================================================
                S_CHECKSUM: begin
                    if (rx_valid) begin
                        if (((checksum_acc + rx_data) & 8'hFF) == 8'hFF) begin
                            // Checksum geçerli → komutu işle
                            state <= S_PROCESS;
                        end else begin
                            // Checksum hatalı → NACK gönder
                            resp_cmd <= CMD_NACK;
                            state    <= S_SEND_RESP_0;
                        end
                    end
                end

                //=============================================================
                // S_PROCESS: Komut İşleme
                // DATA_WRITE → ACK gönder (veri zaten payload sırasında yazıldı)
                // BOOT_CPU   → CPU'yu başlat, ACK gönder
                //=============================================================
                S_PROCESS: begin
                    case (cmd_reg)
                        CMD_DATA_WRITE: begin
                            // Veri zaten RAM'e yazıldı, ACK gönder
                            resp_cmd <= CMD_ACK;
                            state    <= S_SEND_RESP_0;
                        end

                        CMD_BOOT_CPU: begin
                            // CPU'yu başlat
                            cpu_running <= 1'b1;
                            resp_cmd    <= CMD_ACK;
                            state       <= S_SEND_RESP_0;
                        end

                        default: begin
                            // Bilinmeyen komut → NACK gönder
                            resp_cmd <= CMD_NACK;
                            state    <= S_SEND_RESP_0;
                        end
                    endcase
                end

                //=============================================================
                // Yanıt Paketi Gönderimi (5 bayt)
                // Format: [SYNC(0xAA)] [CMD] [0x00] [0x00] [CHECKSUM]
                //=============================================================

                // Bayt 0: SYNC
                S_SEND_RESP_0: begin
                    if (!tx_busy) begin
                        tx_data      <= SYNC;
                        tx_start     <= 1'b1;
                        resp_checksum <= calc_resp_checksum;
                        state         <= S_SEND_RESP_1;
                    end
                end

                // Bayt 1: CMD (ACK veya NACK)
                S_SEND_RESP_1: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data  <= resp_cmd;
                        tx_start <= 1'b1;
                        state    <= S_SEND_RESP_2;
                    end
                end

                // Bayt 2: LEN_LO = 0x00
                S_SEND_RESP_2: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data  <= 8'h00;
                        tx_start <= 1'b1;
                        state    <= S_SEND_RESP_3;
                    end
                end

                // Bayt 3: LEN_HI = 0x00
                S_SEND_RESP_3: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data  <= 8'h00;
                        tx_start <= 1'b1;
                        state    <= S_SEND_RESP_4;
                    end
                end

                // Bayt 4: CHECKSUM
                S_SEND_RESP_4: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data  <= resp_checksum;
                        tx_start <= 1'b1;
                        state    <= S_IDLE;  // Yanıt gönderildi, yeni paket bekle
                    end
                end

                //=============================================================
                // Varsayılan durum: güvenli konuma dön
                //=============================================================
                default: begin
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
