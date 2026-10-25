// Self-checking testbench: runs every vector in vectors/perm_vectors.mem through the RTL
// permutation and compares against the Python model's expected output.
`timescale 1ns/1ps
module tb_ascon_perm;
    reg clk = 0, rst_n = 0, start = 0, sel_p8 = 0;
    reg  [319:0] state_in = 0;
    wire busy, done;
    wire [319:0] state_out;
    ascon_perm dut (.clk(clk), .rst_n(rst_n), .start(start), .sel_p8(sel_p8),
                    .state_in(state_in), .busy(busy), .done(done), .state_out(state_out));
    always #5 clk = ~clk;

    reg [63:0] mem [0:2047];
    integer n, k, base, errors, checked;
    reg [319:0] expect_out;

    initial begin
        $readmemh("vectors/perm_vectors.mem", mem);
        n = mem[0]; errors = 0; checked = 0;
        repeat (3) @(posedge clk);
        rst_n = 1;
        for (k = 0; k < n; k = k + 1) begin
            base = 1 + k * 11;
            sel_p8   = mem[base][0];
            state_in = {mem[base+1], mem[base+2], mem[base+3], mem[base+4], mem[base+5]};
            expect_out = {mem[base+6], mem[base+7], mem[base+8], mem[base+9], mem[base+10]};
            @(negedge clk) start = 1;
            @(negedge clk) start = 0;
            wait (done);
            @(negedge clk);
            checked = checked + 1;
            if (state_out !== expect_out) begin
                errors = errors + 1;
                $display("FAIL vector %0d (%s): got %h expected %h", k, sel_p8 ? "p8" : "p12", state_out, expect_out);
            end
            @(negedge clk);
        end
        if (errors == 0) $display("PASS: %0d permutation vectors matched (p12 and p8)", checked);
        else             $display("FAILED: %0d of %0d vectors mismatched", errors, checked);
        $finish;
    end
    initial begin #50000000; $display("FAILED: timeout"); $finish; end
endmodule
