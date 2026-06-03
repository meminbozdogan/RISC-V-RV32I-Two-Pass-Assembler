//=============================================================================
// Modül       : dual_port_ram
// Açıklama    : Basit Çift Portlu RAM (Simple Dual-Port - SDP)
//               - Gowin SDPB primitive olarak sentezlenir (DPB DEĞİL)
//               - WRITE_MODE sorunu yok çünkü portlar ayrışık:
//                   Okuma Portu: SADECE okur (CPU tarafı)
//                   Yazma Portu: SADECE yazar (CPU veya Loader, mux ile)
//               - 4 adet 8-bit banka ile bayt-maskelemeli yazma desteği
//               - 1024 kelime x 32 bit = 4 KB kapasite
//=============================================================================

module dual_port_ram #(
    parameter ADDR_WIDTH = 10
)(
    input  wire                    clk,

    // Okuma Portu (CPU her zaman buradan okur)
    input  wire [ADDR_WIDTH-1:0]   r_addr,
    input  wire                    r_en,
    output wire [31:0]             r_data,

    // Yazma Portu (top.v'de mux ile CPU veya Loader seçilir)
    input  wire [ADDR_WIDTH-1:0]   w_addr,
    input  wire [31:0]             w_data,
    input  wire [3:0]              w_strb       // Bayt yazma maskesi
);

    // Okuma çıktı register'ları
    reg [7:0] rd0, rd1, rd2, rd3;
    assign r_data = {rd3, rd2, rd1, rd0};

    //=========================================================================
    // Banka 0 — Bayt 0 (bit [7:0])
    //=========================================================================
    reg [7:0] bank0 [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin                 // Yazma portu
        if (w_strb[0])
            bank0[w_addr] <= w_data[7:0];
    end

    always @(posedge clk) begin                 // Okuma portu
        if (r_en)
            rd0 <= bank0[r_addr];
    end

    //=========================================================================
    // Banka 1 — Bayt 1 (bit [15:8])
    //=========================================================================
    reg [7:0] bank1 [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (w_strb[1])
            bank1[w_addr] <= w_data[15:8];
    end

    always @(posedge clk) begin
        if (r_en)
            rd1 <= bank1[r_addr];
    end

    //=========================================================================
    // Banka 2 — Bayt 2 (bit [23:16])
    //=========================================================================
    reg [7:0] bank2 [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (w_strb[2])
            bank2[w_addr] <= w_data[23:16];
    end

    always @(posedge clk) begin
        if (r_en)
            rd2 <= bank2[r_addr];
    end

    //=========================================================================
    // Banka 3 — Bayt 3 (bit [31:24])
    //=========================================================================
    reg [7:0] bank3 [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (w_strb[3])
            bank3[w_addr] <= w_data[31:24];
    end

    always @(posedge clk) begin
        if (r_en)
            rd3 <= bank3[r_addr];
    end

endmodule
