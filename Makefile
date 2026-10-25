.PHONY: all test-py vectors sim clean
all: test-py vectors sim

test-py:
	python3 tests/test_kat.py
	python3 tests/test_tamper.py

vectors:
	python3 scripts/gen_perm_vectors.py

sim: vectors
	iverilog -g2005 -o build_perm.vvp rtl/ascon_perm.v tb/tb_ascon_perm.v
	vvp build_perm.vvp | tee sim.log
	@grep -q "^PASS" sim.log

clean:
	rm -f build_perm.vvp sim.log
