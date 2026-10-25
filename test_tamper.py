"""Tamper, header and replay-style checks: nothing may be released unless the tag verifies."""
import os, random, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import ascon_aead128 as A

KEY, NONCE = bytes(range(16)), bytes(range(16, 32))
HEADER = bytes.fromhex("0400") + (1).to_bytes(4, "big") + (7).to_bytes(2, "big")  # mode/len, session, counter
PT = bytes(random.Random(1).randrange(256) for _ in range(1024))


def flip(b, i): return b[:i] + bytes([b[i] ^ 1]) + b[i + 1:]


class Tamper(unittest.TestCase):
    def setUp(self): self.ct = A.encrypt(KEY, NONCE, HEADER, PT)

    def test_roundtrip(self):
        self.assertEqual(A.decrypt(KEY, NONCE, HEADER, self.ct), PT)

    def test_flip_every_tag_byte(self):
        for i in range(len(self.ct) - 16, len(self.ct)):
            self.assertIsNone(A.decrypt(KEY, NONCE, HEADER, flip(self.ct, i)))

    def test_flip_ciphertext_samples(self):
        for i in (0, 1, 15, 16, 511, 1023):
            self.assertIsNone(A.decrypt(KEY, NONCE, HEADER, flip(self.ct, i)))

    def test_flip_each_header_byte(self):          # header is associated data
        for i in range(len(HEADER)):
            self.assertIsNone(A.decrypt(KEY, NONCE, flip(HEADER, i), self.ct))

    def test_wrong_nonce_and_key(self):
        self.assertIsNone(A.decrypt(KEY, flip(NONCE, 0), HEADER, self.ct))
        self.assertIsNone(A.decrypt(flip(KEY, 0), NONCE, HEADER, self.ct))

    def test_truncated_and_extended(self):
        self.assertIsNone(A.decrypt(KEY, NONCE, HEADER, self.ct[:-1]))
        self.assertIsNone(A.decrypt(KEY, NONCE, HEADER, self.ct + b"\x00"))
        self.assertIsNone(A.decrypt(KEY, NONCE, HEADER, b"short"))

    def test_lengths_roundtrip(self):
        for n in list(range(0, 40)) + [255, 1024]:
            for adn in (0, 1, 7, 8, 9, 16, 17):
                m, a = PT[:n], HEADER[:1] * adn
                self.assertEqual(A.decrypt(KEY, NONCE, a, A.encrypt(KEY, NONCE, a, m)), m)


if __name__ == "__main__":
    unittest.main()
