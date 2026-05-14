module my_prom (
    input [7:0] ad,
    input ce,
    output [31:0] dout
);
    reg [31:0] mem [0:63];

    initial begin
        $readmemh("src/ledsirali.hex", mem);
    end

   
    assign dout = (ce) ? mem[ad[7:2]] : 32'h0;

endmodule
