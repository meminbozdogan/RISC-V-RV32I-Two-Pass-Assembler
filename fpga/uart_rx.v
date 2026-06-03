//=============================================================================
// Modül       : uart_rx
// Açıklama    : UART Alıcı Modülü (8N1 formatı)
//               - 8 veri biti, parite yok, 1 dur biti
//               - LSB önce alınır
//               - Metastabilite koruması için 2 aşamalı senkronizör içerir
//               - Baud hızı, saat frekansına göre otomatik hesaplanır
// Yazar       : Otomatik oluşturuldu
// Tarih       : 2026-05-29
//=============================================================================

module uart_rx #(
    parameter CLK_FREQ  = 50_000_000,  // Sistem saat frekansı (Hz)
    parameter BAUD_RATE = 115200        // UART baud hızı (bit/s)
)(
    input  wire       clk,      // Sistem saati
    input  wire       rst_n,    // Aktif düşük sıfırlama sinyali
    input  wire       rx,       // UART RX hattı (seri giriş)
    output reg  [7:0] rx_data,  // Alınan 8 bitlik veri
    output reg        rx_valid  // Veri hazır sinyali (1 saat çevrimi sürer)
);

    //=========================================================================
    // Baud hızı hesaplaması
    // Bir bit süresi boyunca kaç saat çevrimi geçtiğini hesaplıyoruz.
    // Örnek: 50 MHz saat / 115200 baud = ~434 saat çevrimi/bit
    //=========================================================================
    localparam CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;

    //=========================================================================
    // FSM Durum Tanımları
    // IDLE      : Boşta bekleme durumu, başlangıç biti bekleniyor
    // START_BIT : Başlangıç bitinin ortasında örnekleme yapılıyor
    // DATA_BITS : 8 veri bitinin sırayla alınması (LSB önce)
    // STOP_BIT  : Dur bitinin doğrulanması ve verinin çıkışa yazılması
    //=========================================================================
    localparam [1:0] IDLE      = 2'b00;
    localparam [1:0] START_BIT = 2'b01;
    localparam [1:0] DATA_BITS = 2'b10;
    localparam [1:0] STOP_BIT  = 2'b11;

    //=========================================================================
    // Metastabilite Koruması - 2 Aşamalı Senkronizör
    // Harici RX sinyali farklı bir saat alanından geldiği için,
    // metastabilite sorunlarını önlemek adına iki flip-flop ile
    // senkronize ediyoruz.
    //=========================================================================
    reg rx_sync_0;  // İlk senkronizör kademesi
    reg rx_sync_1;  // İkinci senkronizör kademesi (kararlı sinyal)

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync_0 <= 1'b1;  // Boşta durumda RX hattı HIGH olmalı
            rx_sync_1 <= 1'b1;
        end else begin
            rx_sync_0 <= rx;        // Ham RX sinyalini ilk FF'ye al
            rx_sync_1 <= rx_sync_0; // Kararlı sinyal ikinci FF'den çıkar
        end
    end

    // Senkronize edilmiş RX sinyali
    wire rx_s = rx_sync_1;

    //=========================================================================
    // Dahili Kayıtçılar (Register'lar)
    //=========================================================================
    reg [1:0]  state;       // Mevcut FSM durumu
    reg [31:0] clk_cnt;     // Saat çevrimi sayacı (bit zamanlama)
    reg [2:0]  bit_idx;     // Alınan bit indeksi (0-7)
    reg [7:0]  rx_shift;    // Kaydırma yazmacı (alınan bitleri toplar)

    //=========================================================================
    // Ana FSM - UART Alıcı Durum Makinesi
    //=========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Sıfırlama: tüm kayıtçıları başlangıç değerlerine ayarla
            state    <= IDLE;
            clk_cnt  <= 32'd0;
            bit_idx  <= 3'd0;
            rx_shift <= 8'd0;
            rx_data  <= 8'd0;
            rx_valid <= 1'b0;
        end else begin
            // Varsayılan olarak rx_valid sıfırla (yalnızca 1 çevrim HIGH kalır)
            rx_valid <= 1'b0;

            case (state)
                //=============================================================
                // IDLE (Boşta) Durumu
                // RX hattı HIGH iken bekliyoruz. Başlangıç biti (LOW)
                // algılandığında START_BIT durumuna geçiyoruz.
                //=============================================================
                IDLE: begin
                    clk_cnt <= 32'd0;
                    bit_idx <= 3'd0;

                    if (rx_s == 1'b0) begin
                        // Başlangıç biti algılandı, doğrulama için ilerle
                        state <= START_BIT;
                    end
                end

                //=============================================================
                // START_BIT (Başlangıç Biti) Durumu
                // Başlangıç bitinin ortasına kadar bekliyoruz
                // (CLKS_PER_BIT/2 çevrim). Ortada örnekleyerek
                // bitin gerçekten LOW olduğunu doğruluyoruz.
                // Eğer hâlâ LOW ise geçerli bir başlangıç bitidir.
                //=============================================================
                START_BIT: begin
                    if (clk_cnt == (CLKS_PER_BIT / 2)) begin
                        // Bitin ortasına ulaştık
                        if (rx_s == 1'b0) begin
                            // Geçerli başlangıç biti, veri bitlerine geç
                            clk_cnt <= 32'd0;
                            state   <= DATA_BITS;
                        end else begin
                            // Sahte başlangıç biti, geri dön
                            state <= IDLE;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 32'd1;
                    end
                end

                //=============================================================
                // DATA_BITS (Veri Bitleri) Durumu
                // Her bir veri bitinin ortasında örnekleme yapıyoruz.
                // CLKS_PER_BIT çevrim sayarak bir sonraki bitin ortasına
                // ulaşıyoruz. LSB önce alındığı için bit_idx=0 en düşük
                // anlamlı bittir.
                //=============================================================
                DATA_BITS: begin
                    if (clk_cnt == CLKS_PER_BIT) begin
                        // Bitin ortasında örnekle
                        clk_cnt            <= 32'd0;
                        rx_shift[bit_idx]  <= rx_s;  // LSB önce yerleştir

                        if (bit_idx == 3'd7) begin
                            // Tüm 8 bit alındı, dur bitine geç
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
                // Dur bitinin sonuna kadar bekliyoruz (CLKS_PER_BIT çevrim).
                // Dur biti HIGH olmalıdır. Tamamlandığında alınan veriyi
                // rx_data'ya yazıp rx_valid sinyalini 1 çevrim boyunca
                // yüksek tutuyoruz.
                //=============================================================
                STOP_BIT: begin
                    if (clk_cnt == CLKS_PER_BIT) begin
                        // Dur biti tamamlandı, veriyi çıkışa yaz
                        rx_data  <= rx_shift;
                        rx_valid <= 1'b1;    // 1 saat çevrimi boyunca HIGH
                        clk_cnt  <= 32'd0;
                        state    <= IDLE;     // Boşta durumuna geri dön
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
