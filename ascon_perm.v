// Iterative Ascon permutation: one round per clock (12 clocks for p12, 8 for p8).
// State is {x0,x1,x2,x3,x4}, each 64 bits, x0 in the top bits.
// Verification-stage core: not yet wired into an AEAD controller.
module ascon_perm (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,       // pulse when idle
    input  wire         sel_p8,      // 0 = p12, 1 = p8
    input  wire [319:0] state_in,
    output reg          busy,
    output reg          done,        // high for one cycle when state_out is final
    output wire [319:0] state_out
);
    reg [319:0] st;
    reg [3:0]   i;                   // round index 0..11 (p8 starts at 4)
    assign state_out = st;

    function [63:0] ror(input [63:0] x, input integer n);
        ror = (x >> n) | (x << (64 - n));
    endfunction

    function [319:0] ascon_round(input [319:0] s, input [7:0] c);
        reg [63:0] x0, x1, x2, x3, x4, t0, t1, t2, t3, t4;
        begin
            {x0, x1, x2, x3, x4} = s;
            x2 = x2 ^ {56'b0, c};
            x0 = x0 ^ x4; x4 = x4 ^ x3; x2 = x2 ^ x1;
            t0 = x0 ^ (~x1 & x2);
            t1 = x1 ^ (~x2 & x3);
            t2 = x2 ^ (~x3 & x4);
            t3 = x3 ^ (~x4 & x0);
            t4 = x4 ^ (~x0 & x1);
            t1 = t1 ^ t0; t0 = t0 ^ t4; t3 = t3 ^ t2; t2 = ~t2;
            ascon_round = { t0 ^ ror(t0, 19) ^ ror(t0, 28),
                            t1 ^ ror(t1, 61) ^ ror(t1, 39),
                            t2 ^ ror(t2, 1)  ^ ror(t2, 6),
                            t3 ^ ror(t3, 10) ^ ror(t3, 17),
                            t4 ^ ror(t4, 7)  ^ ror(t4, 41) };
        end
    endfunction

    wire [7:0] rc = {4'hF - i, i};   // 0xF0, 0xE1, ... 0x4B

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= 320'b0; i <= 4'd0; busy <= 1'b0; done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (start) begin
                    st   <= state_in;
                    i    <= sel_p8 ? 4'd4 : 4'd0;
                    busy <= 1'b1;
                end
            end else begin
                st <= ascon_round(st, rc);
                i  <= i + 4'd1;
                if (i == 4'd11) begin busy <= 1'b0; done <= 1'b1; end
            end
        end
    end
endmodule
