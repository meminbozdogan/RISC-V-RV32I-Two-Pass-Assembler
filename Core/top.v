module top (
    input clk,
    input reset_btn,
    output [5:0] leds
);

    // S1 Butonu basılı değilken 1, basılıyken 0 verir. 
    // PicoRV32 resetn (Active-Low) beklediği için doğrudan bağlıyoruz.
    wire resetn = reset_btn; 

    wire mem_valid;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [3:0] mem_wstrb;
    wire [31:0] mem_rdata;
    wire mem_ready;
    
    reg [5:0] led_reg;

    picorv32 #(
        .ENABLE_COUNTERS(0),
        .ENABLE_REGS_16_31(1)
    ) cpu (
        .clk         (clk),
        .resetn      (resetn),
        .mem_valid   (mem_valid),
        .mem_addr    (mem_addr),
        .mem_wdata   (mem_wdata),
        .mem_wstrb   (mem_wstrb),
        .mem_rdata   (mem_rdata),
        .mem_ready   (mem_ready)
    );

    my_prom instruction_memory (
        .ad(mem_addr[7:0]),
        .ce(mem_valid),
        .dout(mem_rdata)
    );

    assign mem_ready = 1'b1;

    always @(posedge clk) begin
        if (!resetn) begin
            led_reg <= 6'b000000;
        end else if (mem_valid && mem_wstrb != 4'b0000 && mem_addr == 32'd1024) begin
            led_reg <= mem_wdata[5:0];
        end
    end

    // Tang Nano 9K Özel: 0=Yanar, 1=Söner. 
    // Bu yüzden register'daki değeri tersliyoruz (~).
    assign leds = ~led_reg;

endmodule