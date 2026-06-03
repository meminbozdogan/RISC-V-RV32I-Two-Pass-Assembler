//=============================================================================
// Modül       : top
// Açıklama    : Üst Seviye SoC (System-on-Chip) Modülü
//               PicoRV32 işlemci + SDP RAM + UART Loader entegrasyonu
//
//               Sistem Çalışma Modu:
//               1. YÜKLEME MODU: Reset sonrası CPU durdurulur, Loader FSM
//                  UART üzerinden gelen makine kodunu RAM'e yazar.
//               2. ÇALIŞTIRMA MODU: BOOT_CPU komutu alındığında CPU
//                  serbest bırakılır ve RAM'den program çalıştırır.
//
//               RAM Mimarisi (Simple Dual-Port):
//                 Okuma Portu → her zaman CPU
//                 Yazma Portu → mux ile CPU veya Loader
//
//               Bellek Haritası:
//                 0x0000_0000 - 0x0000_0FFF : RAM (4 KB)
//                 0x0000_0400              : LED çıkışı (memory-mapped I/O)
//
//               Hedef Kart: Tang Nano 9K (Gowin GW1NR-9)
//=============================================================================

module top (
    input  wire       clk,           // 27 MHz sistem saati
    input  wire       reset_btn,     // S1 butonu (aktif düşük, basılınca 0)
    output wire [5:0] leds,          // 6 adet LED çıkışı
    input  wire       uart_rx,       // UART RX girişi (PC → FPGA)
    output wire       uart_tx        // UART TX çıkışı (FPGA → PC)
);

    //=========================================================================
    // Parametre Tanımları
    //=========================================================================
    localparam CLK_FREQ       = 27_000_000;  // Tang Nano 9K: 27 MHz
    localparam BAUD_RATE      = 115200;       // UART baud hızı
    localparam RAM_ADDR_WIDTH = 10;           // 2^10 = 1024 kelime = 4 KB

    //=========================================================================
    // Reset Yönetimi
    //=========================================================================
    wire sys_rst_n  = reset_btn;               // Sistem reset (aktif düşük)
    wire cpu_running;                           // Loader'dan gelen CPU çalışma sinyali
    wire cpu_resetn = cpu_running;              // CPU reset = loader kontrolünde

    //=========================================================================
    // PicoRV32 CPU Sinyalleri
    //=========================================================================
    wire        mem_valid;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [3:0]  mem_wstrb;
    wire [31:0] mem_rdata;
    reg         mem_ready;

    //=========================================================================
    // UART Sinyalleri
    //=========================================================================
    wire [7:0] rx_data;
    wire       rx_valid;
    wire [7:0] tx_data;
    wire       tx_start;
    wire       tx_busy;

    //=========================================================================
    // Loader RAM Sinyalleri
    //=========================================================================
    wire [RAM_ADDR_WIDTH-1:0] loader_ram_addr;
    wire [31:0]               loader_ram_wdata;
    wire                      loader_ram_we;

    //=========================================================================
    // LED Register (Memory-Mapped I/O)
    // Adres: 0x0000_0400 (1024 ondalık)
    //=========================================================================
    reg [5:0] led_reg;

    //=========================================================================
    // Adres Çözümleme
    //=========================================================================
    wire [RAM_ADDR_WIDTH-1:0] cpu_ram_addr = mem_addr[2 +: RAM_ADDR_WIDTH];
    wire ram_select = mem_valid && (mem_addr[31:12] == 20'h00000);
    wire led_select = mem_valid && (mem_addr == 32'h0000_0400);
    wire cpu_writing = ram_select && (mem_wstrb != 4'b0000);

    //=========================================================================
    // RAM Yazma Portu Mux
    // Yükleme modunda (cpu_running=0) → Loader yazma portunu kontrol eder
    // Çalıştırma modunda (cpu_running=1) → CPU yazma portunu kontrol eder
    //=========================================================================
    wire [RAM_ADDR_WIDTH-1:0] ram_w_addr;
    wire [31:0]               ram_w_data;
    wire [3:0]                ram_w_strb;

    assign ram_w_addr = cpu_running ? cpu_ram_addr     : loader_ram_addr;
    assign ram_w_data = cpu_running ? mem_wdata         : loader_ram_wdata;
    assign ram_w_strb = cpu_running ? (cpu_writing ? mem_wstrb : 4'b0000)
                                    : (loader_ram_we ? 4'b1111 : 4'b0000);

    //=========================================================================
    // RAM Okuma Verisi → CPU
    //=========================================================================
    wire [31:0] ram_r_data;

    assign mem_rdata = ram_select ? ram_r_data : 32'h0000_0000;

    //=========================================================================
    // Bellek Hazır Sinyali
    // Tek çevrimli gecikme: mem_valid geldiğinde sonraki çevrimde mem_ready
    //=========================================================================
    always @(posedge clk) begin
        if (!sys_rst_n)
            mem_ready <= 1'b0;
        else
            mem_ready <= mem_valid && !mem_ready;
    end

    //=========================================================================
    // LED Register Yazma
    //=========================================================================
    always @(posedge clk) begin
        if (!sys_rst_n)
            led_reg <= 6'b000000;
        else if (led_select && (mem_wstrb != 4'b0000))
            led_reg <= mem_wdata[5:0];
    end

    assign leds = ~led_reg;  // Tang Nano 9K: LED'ler aktif düşük

    //=========================================================================
    // PicoRV32 İşlemci Çekirdeği
    //=========================================================================
    picorv32 #(
        .ENABLE_COUNTERS   (0),
        .ENABLE_REGS_16_31 (1),
        .PROGADDR_RESET    (32'h0000_0000),
        .STACKADDR         (32'h0000_0FFC)
    ) cpu (
        .clk       (clk),
        .resetn    (cpu_resetn),
        .mem_valid (mem_valid),
        .mem_addr  (mem_addr),
        .mem_wdata (mem_wdata),
        .mem_wstrb (mem_wstrb),
        .mem_rdata (mem_rdata),
        .mem_ready (mem_ready)
    );

    //=========================================================================
    // Simple Dual-Port RAM
    // Okuma Portu: CPU (her zaman)
    // Yazma Portu: CPU veya Loader (mux ile seçilir)
    //=========================================================================
    dual_port_ram #(
        .ADDR_WIDTH (RAM_ADDR_WIDTH)
    ) program_ram (
        .clk     (clk),

        // Okuma Portu → CPU
        .r_addr  (cpu_ram_addr),
        .r_en    (ram_select),
        .r_data  (ram_r_data),

        // Yazma Portu → Mux (CPU veya Loader)
        .w_addr  (ram_w_addr),
        .w_data  (ram_w_data),
        .w_strb  (ram_w_strb)
    );

    //=========================================================================
    // UART Alıcı (RX)
    //=========================================================================
    uart_rx #(
        .CLK_FREQ  (CLK_FREQ),
        .BAUD_RATE (BAUD_RATE)
    ) uart_receiver (
        .clk      (clk),
        .rst_n    (sys_rst_n),
        .rx       (uart_rx),
        .rx_data  (rx_data),
        .rx_valid (rx_valid)
    );

    //=========================================================================
    // UART Verici (TX)
    //=========================================================================
    uart_tx #(
        .CLK_FREQ  (CLK_FREQ),
        .BAUD_RATE (BAUD_RATE)
    ) uart_transmitter (
        .clk      (clk),
        .rst_n    (sys_rst_n),
        .tx_data  (tx_data),
        .tx_start (tx_start),
        .tx       (uart_tx),
        .tx_busy  (tx_busy)
    );

    //=========================================================================
    // Loader Durum Makinesi
    //=========================================================================
    loader #(
        .RAM_ADDR_WIDTH (RAM_ADDR_WIDTH)
    ) program_loader (
        .clk         (clk),
        .rst_n       (sys_rst_n),
        .rx_data     (rx_data),
        .rx_valid    (rx_valid),
        .tx_data     (tx_data),
        .tx_start    (tx_start),
        .tx_busy     (tx_busy),
        .ram_addr    (loader_ram_addr),
        .ram_wdata   (loader_ram_wdata),
        .ram_we      (loader_ram_we),
        .cpu_running (cpu_running)
    );

endmodule