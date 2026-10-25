"""Ascon-AEAD128 golden model (NIST SP 800-232), written for readability.

This is a verification reference, not production crypto: it is not
constant-time and has no side-channel protection.

State = five 64-bit words x0..x4. Bytes are loaded little-endian into each word.
"""
MASK = (1 << 64) - 1
RATE = 16            # bytes
TAG_LEN = 16
IV = 0x00001000808C0001   # Ascon-AEAD128: p12 init, p8 per block, 128-bit tag, 16 B rate


def ror(x, n):
    return ((x >> n) | (x << (64 - n))) & MASK


def round_(s, c):
    x0, x1, x2, x3, x4 = s
    x2 ^= c
    x0 ^= x4; x4 ^= x3; x2 ^= x1
    t0 = x0 ^ (~x1 & MASK & x2)
    t1 = x1 ^ (~x2 & MASK & x3)
    t2 = x2 ^ (~x3 & MASK & x4)
    t3 = x3 ^ (~x4 & MASK & x0)
    t4 = x4 ^ (~x0 & MASK & x1)
    t1 ^= t0; t0 ^= t4; t3 ^= t2; t2 = ~t2 & MASK
    return [t0 ^ ror(t0, 19) ^ ror(t0, 28),
            t1 ^ ror(t1, 61) ^ ror(t1, 39),
            t2 ^ ror(t2, 1) ^ ror(t2, 6),
            t3 ^ ror(t3, 10) ^ ror(t3, 17),
            t4 ^ ror(t4, 7) ^ ror(t4, 41)]


def permutation(s, rounds):
    """Ascon-p[rounds]; uses the last `rounds` of the 12 round constants."""
    s = list(s)
    for i in range(12 - rounds, 12):
        s = round_(s, ((0xF - i) << 4) | i)
    return s


def _load(b):
    return int.from_bytes(b, "little")


def _store(x, n):
    return (x & MASK).to_bytes(8, "little")[:n]


def _init(key, nonce):
    k0, k1 = _load(key[:8]), _load(key[8:])
    s = permutation([IV, k0, k1, _load(nonce[:8]), _load(nonce[8:])], 12)
    s[3] ^= k0; s[4] ^= k1
    return s, k0, k1


def _absorb_ad(s, ad):
    if not ad:
        return s
    while len(ad) >= RATE:
        s[0] ^= _load(ad[:8]); s[1] ^= _load(ad[8:16])
        s = permutation(s, 8)
        ad = ad[RATE:]
    if len(ad) >= 8:
        s[0] ^= _load(ad[:8]); s[1] ^= _load(ad[8:]); s[1] ^= 1 << (8 * (len(ad) - 8))
    else:
        s[0] ^= _load(ad); s[0] ^= 1 << (8 * len(ad))
    return permutation(s, 8)


def _finalize(s, k0, k1):
    s[2] ^= k0; s[3] ^= k1
    s = permutation(s, 12)
    s[3] ^= k0; s[4] ^= k1
    return _store(s[3], 8) + _store(s[4], 8)


def encrypt(key, nonce, ad, pt):
    """Return ciphertext || 16-byte tag."""
    assert len(key) == 16 and len(nonce) == 16
    s, k0, k1 = _init(key, nonce)
    s = _absorb_ad(s, ad)
    s[4] ^= 1 << 63                       # domain separation
    ct = b""
    while len(pt) >= RATE:
        s[0] ^= _load(pt[:8]); s[1] ^= _load(pt[8:16])
        ct += _store(s[0], 8) + _store(s[1], 8)
        s = permutation(s, 8)
        pt = pt[RATE:]
    if len(pt) >= 8:
        s[0] ^= _load(pt[:8]); s[1] ^= _load(pt[8:])
        ct += _store(s[0], 8) + _store(s[1], len(pt) - 8)
        s[1] ^= 1 << (8 * (len(pt) - 8))
    else:
        s[0] ^= _load(pt)
        ct += _store(s[0], len(pt))
        s[0] ^= 1 << (8 * len(pt))
    return ct + _finalize(s, k0, k1)


def decrypt(key, nonce, ad, ct_tag):
    """Return plaintext, or None if the tag does not verify (nothing is released)."""
    assert len(key) == 16 and len(nonce) == 16
    if len(ct_tag) < TAG_LEN:
        return None
    ct, tag = ct_tag[:-TAG_LEN], ct_tag[-TAG_LEN:]
    s, k0, k1 = _init(key, nonce)
    s = _absorb_ad(s, ad)
    s[4] ^= 1 << 63
    pt = b""
    c = ct
    while len(c) >= RATE:
        c0, c1 = _load(c[:8]), _load(c[8:16])
        pt += _store(s[0] ^ c0, 8) + _store(s[1] ^ c1, 8)
        s[0], s[1] = c0, c1
        s = permutation(s, 8)
        c = c[RATE:]
    if len(c) >= 8:
        c0, c1 = _load(c[:8]), _load(c[8:])
        n1 = len(c) - 8
        pt += _store(s[0] ^ c0, 8) + _store(s[1] ^ c1, n1)
        s[0] = c0
        mask = (1 << (8 * n1)) - 1
        s[1] = (s[1] & ~mask & MASK) | c1
        s[1] ^= 1 << (8 * n1)
    else:
        n0 = len(c)
        c0 = _load(c)
        pt += _store(s[0] ^ c0, n0)
        mask = (1 << (8 * n0)) - 1
        s[0] = (s[0] & ~mask & MASK) | c0
        s[0] ^= 1 << (8 * n0)
    expect = _finalize(s, k0, k1)
    diff = 0
    for a, b in zip(expect, tag):
        diff |= a ^ b
    return pt if diff == 0 else None
