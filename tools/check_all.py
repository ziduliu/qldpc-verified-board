#!/usr/bin/env python3
"""Checks every entry of codes/ that has matrices in this repository: H_X H_Z^T = 0, the stated n, k and check weights,
every listed logical operator (commutes with the opposite checks, lies outside its own stabilizer group, has the stated
weight), and, for certificates that use the even-weight argument, that the all-ones vector lies in the row spaces of
H_X and of H_Z. It does not re-run the exact enumerations; their records are named in each entry. Leaderboard entries
carry no matrices here; their operators were checked against the rebuilt matrices when the entry was written.
Exit status 1 if anything fails.

    python tools/check_all.py"""
import glob
import json
import os
import sys

import numpy as np
from scipy.io import mmread

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from verify import gf2_rank  # noqa: E402


def main():
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
        e = json.load(open(f))
        if not e.get("matrices"):
            print("%-26s (leaderboard entry, no matrices here)" % e["slug"])
            continue
        hx = (np.asarray(mmread(os.path.join(ROOT, e["matrices"]["HX"])).todense()) % 2).astype(np.uint8)
        hz = (np.asarray(mmread(os.path.join(ROOT, e["matrices"]["HZ"])).todense()) % 2).astype(np.uint8)
        n = hx.shape[1]
        ok = hz.shape[1] == n and not ((hx.astype(np.int64) @ hz.T.astype(np.int64)) % 2).any()
        rx, rz = gf2_rank(hx), gf2_rank(hz)
        k = n - rx - rz
        ok &= (n == e["n"] and k == e["k"] and int(hx.sum(1).max()) == e["wX"] and int(hz.sum(1).max()) == e["wZ"])
        msg = "n %d k %d wX %d wZ %d" % (n, k, hx.sum(1).max(), hz.sum(1).max())
        cert = (e.get("evidence") or {}).get("certificate") or {}
        if cert.get("parity_argument"):
            ones = np.ones(n, dtype=np.uint8)
            par = gf2_rank(np.vstack([hx, ones])) == rx and gf2_rank(np.vstack([hz, ones])) == rz
            ok &= par
            msg += " even-weight condition %s" % ("holds" if par else "FAILS")
        if e.get("witness"):
            w = json.load(open(os.path.join(ROOT, e["witness"])))
            best = {}
            for t, ops, h_other, h_same, r_same in (("x", w["wx"], hz, hx, rx), ("z", w["wz"], hx, hz, rz)):
                ws = []
                for s in ops:
                    v = np.zeros(n, dtype=np.uint8)
                    v[s] = 1
                    good = not ((h_other.astype(np.int64) @ v) % 2).any() and gf2_rank(np.vstack([h_same, v])) == r_same + 1
                    ok &= good
                    ws.append(int(v.sum()))
                best[t] = min(ws) if ws else None
            lightest = min(v for v in best.values() if v is not None)
            ok &= (e["d_upper"] is not None and lightest == e["d_upper"])
            msg += " operators x %s z %s" % (best["x"], best["z"])
        elif e["d_status"] == "exact":
            msg += " (operator file pending)"
        print("%-26s %s %s" % (e["slug"], "OK " if ok else "FAIL", msg))
        bad += not ok
    print("failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
