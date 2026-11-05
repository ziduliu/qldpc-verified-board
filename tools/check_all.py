#!/usr/bin/env python3
"""Checks every entry of codes/: the matrices (when present) are a CSS pair with the stated n, k and check weights,
and every listed logical operator commutes with the opposite checks and lies outside its stabilizer group, so that
its weight is a valid upper bound on the distance. Exit status 1 if anything fails.

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
            print("%-28s no matrices in this repository (board entry); witness checked against the rebuilt matrices at import time" % e["slug"])
            continue
        hx = (np.asarray(mmread(os.path.join(ROOT, e["matrices"]["HX"])).todense()) % 2).astype(np.uint8)
        hz = (np.asarray(mmread(os.path.join(ROOT, e["matrices"]["HZ"])).todense()) % 2).astype(np.uint8)
        n = hx.shape[1]
        ok = hz.shape[1] == n and not ((hx.astype(np.int64) @ hz.T.astype(np.int64)) % 2).any()
        rx, rz = gf2_rank(hx), gf2_rank(hz)
        k = n - rx - rz
        ok &= (n == e["n"] and k == e["k"] and int(hx.sum(1).max()) == e["wX"] and int(hz.sum(1).max()) == e["wZ"])
        msg = "n %d k %d wX %d wZ %d" % (n, k, hx.sum(1).max(), hz.sum(1).max())
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
            ok &= (e["d_upper"] is not None and lightest <= e["d_upper"] + 0 and lightest >= e["d_upper"])
            msg += " witnesses x %s z %s" % (best["x"], best["z"])
        print("%-28s %s %s" % (e["slug"], "OK " if ok else "FAIL", msg))
        bad += not ok
    print("failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
