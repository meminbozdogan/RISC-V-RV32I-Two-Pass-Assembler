//=============================================================================
// Modül       : uart_tx
// Açıklama    : UART Verici Modülü (8N1 formatı)
//               - 8 veri biti, parite yok, 1 dur biti
//               - LSB önce gönderilir
//               - tx hattı boşta iken HIGH seviyesindedir
//               - tx_busy sinyali iletim süresince HIGH kalır
//=============================================================================

module uart_tx #(
    parameter CLK_FREQ  = 50_000_000,  // Sistem saat frekansı (Hz)
    parameter BAUD_RATE = 115200        // UART baud hızı (bit/s)
)(
    input  wire       clk,       // Sistem saati
    input  wire       rst_n,     // Aktif düşük sıfırlama sinyali
    input  wire [7:0] tx_data,   // Gönderilecek 8 bitlik veri
    input  wire       tx_start,  // Gönderme başlatma sinyali (1 çevrim HIGH)
    output reg        tx,        // UART TX hattı (seri çıkış, boşta HIGH)
    output reg        tx_busy    // Meşgul sinyali (iletim sırasında HIGH)
);

    //=========================================================================
    // Baud hızı hesaplaması
    // Bir bit süresi boyunca kaç saat çevrimi geçtiğini hesaplıyoruz.
    // Örnek: 50 MHz saat / 115200 baud = ~434 saat çevrimi/bit
    //=========================================================================
    localparam CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;

    //=========================================================================
    // FSM Durum Tanımları
    // IDLE      : Boşta bekleme durumu, gönderim komutu bekleniyor
    // START_BIT : Başlangıç bitinin gönderilmesi (LOW)
    // DATA_BITS : 8 veri bitinin sırayla gönderilmesi (LSB önce)
    // STOP_BIT  : Dur bitinin gönderilmesi (HIGH)
    //=========================================================================
    localparam [1:0] IDLE      = 2'b00;
    localparam [1:0] START_BIT = 2'b01;
    localparam [1:0] DATA_BITS = 2'b10;
    localparam [1:0] STOP_BIT  = 2'b11;

    //=========================================================================
    // Dahili Kayıtçılar (Register'lar)
    //=========================================================================
    reg [1:0]  state;       // Mevcut FSM durumu
    reg [31:0] clk_cnt;     // Saat çevrimi sayacı (bit zamanlama)
    reg [2:0]  bit_idx;     // Gönderilen bit indeksi (0-7)
    reg [7:0]  tx_shift;    // Kaydırma yazmacı (gönderilecek veriyi tutar)

    //=========================================================================
    // Ana FSM - UART Verici Durum Makinesi
    //=========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Sıfırlama: tüm kayıtçıları başlangıç değerlerine ayarla
            state    <= IDLE;
            clk_cnt  <= 32'd0;
            bit_idx  <= 3'd0;
            tx_shift <= 8'd0;
            tx       <= 1'b1;    // TX hattı boşta HIGH olmalı
            tx_busy  <= 1'b0;    // Meşgul değil
        end else begin
            case (state)
                //=============================================================
                // IDLE (Boşta) Durumu
                // TX hattı HIGH tutulur. tx_start sinyali geldiğinde
                // gönderilecek veri kaydırma yazmacına yüklenir ve
                // START_BIT durumuna geçilir.
                //=============================================================
                IDLE: begin
                    tx      <= 1'b1;    // Boşta TX hattı HIGH
                    tx_busy <= 1'b0;    // Meşgul değil
                    clk_cnt <= 32'd0;
                    bit_idx <= 3'd0;

                    if (tx_start == 1'b1) begin
                        // Gönderim komutu alındı
                        tx_shift <= tx_data;  // Veriyi kaydırma yazmacına yükle
                        tx_busy  <= 1'b1;     // Meşgul durumuna geç
                        state    <= START_BIT;
                    end
                end

                //=============================================================
                // START_BIT (Başlangıç Biti) Durumu
                // TX hattını LOW'a çekerek başlangıç bitini gönderiyoruz.
                // Bir tam bit süresi (CLKS_PER_BIT çevrim) boyunca
                // LOW tutuyoruz, ardından veri bitlerine geçiyoruz.
                //=============================================================
                START_BIT: begin
                    tx <= 1'b0;  // Başlangıç biti = LOW

                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        // Bir bit süresi tamamlandı
                        clk_cnt <= 32'd0;
                        state   <= DATA_BITS;
                    end else begin
                        clk_cnt <= clk_cnt + 32'd1;
                    end
                end

                //=============================================================
                // DATA_BITS (Veri Bitleri) Durumu
                // 8 veri bitini LSB'den başlayarak sırayla gönderiyoruz.
                // Her bit için CLKS_PER_BIT çevrim boyunca TX hattını
                // ilgili bit değerinde tutuyoruz. Kaydırma yazmacı
                // kullanarak bitleri sırayla çıkışa veriyoruz.
                //=============================================================
                DATA_BITS: begin
                    tx <= tx_shift[bit_idx];  // Mevcut biti TX hattına yaz

                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        // Bir bit süresi tamamlandı
                        clk_cnt <= 32'd0;

                        if (bit_idx == 3'd7) begin
                            // Tüm 8 veri biti gönderildi, dur bitine geç
                            bit_idx <= 3'd0;
                            state   <= STOP_BIT;
                        end else begin
                            bit_idx <= bit_idx + 3'd1;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 32'd1;
                    end
                end

                //=============================================================
                // STOP_BIT (Dur Biti) Durumu
                // TX hattını HIGH'a çekerek dur bitini gönderiyoruz.
                // Bir tam bit süresi boyunca HIGH tutuyoruz.
                // Tamamlandığında IDLE durumuna geri dönüyoruz.
                //=============================================================
                STOP_BIT: begin
                    tx <= 1'b1;  // Dur biti = HIGH

                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        // Dur biti tamamlandı, boşta durumuna dön
                        clk_cnt <= 32'd0;
                        tx_busy <= 1'b0;    // İletim bitti, meşgul değil
                        state   <= IDLE;
                    end else begin
                        clk_cnt <= clk_cnt + 32'd1;
                    end
                end

                //=============================================================
                // Varsayılan durum: beklenmeyen durumlarda güvenli konuma dön
                //=============================================================
                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
