"""Check the Python model against the Ascon team's AEAD128 known-answer file (LWC format)."""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
import ascon_aead128 as A

KAT = os.path.join(HERE, "..", "vectors", "LWC_AEAD_KAT_128_128.txt")


def load_kat(path=KAT):
    vecs, cur = [], {}
    with open(path) as f:
        lines = f.read().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            if cur: vecs.append(cur); cur = {}
            continue
        k, v = [x.strip() for x in line.split("=", 1)]
        cur[k] = bytes.fromhex(v) if k != "Count" else int(v)
    if cur: vecs.append(cur)
    return vecs


class KnownAnswer(unittest.TestCase):
    def test_all_vectors(self):
        vecs = load_kat()
        self.assertGreater(len(vecs), 1000)
        for v in vecs:
            out = A.encrypt(v["Key"], v["Nonce"], v["AD"], v["PT"])
            self.assertEqual(out, v["CT"], "encrypt mismatch, Count=%d" % v["Count"])
            self.assertEqual(A.decrypt(v["Key"], v["Nonce"], v["AD"], v["CT"]), v["PT"],
                             "decrypt mismatch, Count=%d" % v["Count"])
        print("KAT: %d vectors encrypt+decrypt OK" % len(vecs))


if __name__ == "__main__":
    unittest.main()
