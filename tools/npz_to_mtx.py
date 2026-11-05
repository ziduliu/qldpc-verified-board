#!/usr/bin/env python3
"""Converts an archived code (npz with HX, HZ as 0/1 arrays, or bit-packed rows) into two MatrixMarket files.

    python tools/npz_to_mtx.py <code.npz> <n> <out_dir>

Writes <out_dir>/HX.mtx and <out_dir>/HZ.mtx (coordinate format, pattern). Rows whose stored width is smaller than n
are unpacked with numpy.unpackbits (most significant bit first) and cut to n columns."""
import os
import sys

import numpy as np
from scipy.io import mmwrite
from scipy.sparse import coo_matrix


def load(path, n):
    z = np.load(path, allow_pickle=True)
    out = {}
    for key in ("HX", "HZ"):
        m = np.asarray(z[key], dtype=np.uint8)
        if m.shape[1] < n:
            m = np.unpackbits(m, axis=1)[:, :n]
        elif m.shape[1] > n:
            raise ValueError("%s has %d columns, more than n = %d" % (key, m.shape[1], n))
        out[key] = (m & 1).astype(np.uint8)
    return out["HX"], out["HZ"]


def main(path, n, out_dir):
    n = int(n)
    hx, hz = load(path, n)
    if ((hx.astype(np.int64) @ hz.T.astype(np.int64)) % 2).any():
        raise SystemExit("H_X H_Z^T != 0")
    os.makedirs(out_dir, exist_ok=True)
    for key, m in (("HX", hx), ("HZ", hz)):
        mmwrite(os.path.join(out_dir, key + ".mtx"), coo_matrix(m), field="pattern", comment="%s of a CSS code on %d qubits" % (key, n))
    print("wrote", out_dir, "rows", hx.shape[0], hz.shape[0], "n", n)


if __name__ == "__main__":
    main(*sys.argv[1:4])
