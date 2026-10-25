# Ascon-AEAD128 Verification Suite

![status](https://img.shields.io/badge/status-in%20progress-orange)

Verification base for the **Secure Optical Image Beacon** (Team INDUS, VConnecTech Engineering Marathon 2026):
an FPGA pipeline that compresses a small image, protects it with Ascon-AEAD128 and sends it over an LED and
phototransistor link. Before building the full encryption core in RTL, we want a trusted reference model and a
way to prove each hardware block matches it. This repo is that foundation.

> **Status: in progress.** The Python model and the RTL permutation are verified. The full AEAD controller in
> RTL is not written yet. See [docs/STATUS.md](docs/STATUS.md) for the honest checklist.

## What is here

| Part | What it does | Status |
|---|---|---|
| `python/ascon_aead128.py` | Readable golden model of Ascon-AEAD128 (NIST SP 800-232): encrypt, and decrypt that releases nothing unless the tag verifies | Done |
| `tests/test_kat.py` | Encrypts and decrypts every vector in the Ascon team's AEAD128 known-answer file (1,089 vectors) | Passing |
| `tests/test_tamper.py` | Flips tag, ciphertext, header (associated data), nonce and key; checks truncation and lengths | Passing |
| `rtl/ascon_perm.v` | Iterative Ascon permutation, one round per clock (p12 = 12 clocks, p8 = 8 clocks) | Matches model |
| `tb/tb_ascon_perm.v` | Self-checking testbench: 126 p12/p8 vectors from the Python model | Passing |
| AEAD controller in RTL (init, absorb, finalise, tag check) | Next step | Not started |

## Run it

```bash
make all        # Python tests, vector generation, RTL simulation
make test-py    # Python only (no simulator needed)
make sim        # RTL only (needs Icarus Verilog)
```

Needs Python 3 and [Icarus Verilog](https://steveicarus.github.io/iverilog/). No other dependencies.
The same Verilog is plain Verilog-2005, so it can also be run in the Vivado simulator.

## How we check ourselves

1. The Python model is compared with the official known-answer vectors. If it were wrong, these would fail.
2. The RTL permutation is compared with the Python model, so the RTL is only trusted through the model.
3. We also checked that the checks can fail: changing one rotation constant in the RTL, or one round constant in
   the model, makes the tests fail.

## What this is not

- Not production cryptography. The model is not constant-time and has no side-channel protection.
- Not a security proof. Tamper tests only show that the tested cases are rejected.
- No hardware results yet: no synthesis numbers, no timing, no optical-link measurements.

## Next steps

1. AEAD controller FSM in RTL (initialisation, header as associated data, data blocks, finalisation, tag compare).
2. Full-AEAD RTL testbench against the same known-answer file, including altered-tag and altered-header rejection.
3. Packet framing and CRC-16 model, then the electrical loopback and LED link.

## Attribution

`vectors/LWC_AEAD_KAT_128_128.txt` is the Ascon-AEAD128 known-answer file from the Ascon reference implementation
([github.com/ascon/ascon-c](https://github.com/ascon/ascon-c), CC0). The algorithm follows NIST SP 800-232.
Code in this repo is MIT licensed.
