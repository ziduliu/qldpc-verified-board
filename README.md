# qldpc-verified-board

A table of quantum LDPC codes in which every distance statement says what is actually proven, with the files needed
to check it. Site: the `docs/` folder (GitHub Pages). Data: `codes/*.json`, one entry per code.

## What a row means

- **exact** distance `d`: a certificate shows that no logical operator of weight below `d` exists on either side
  (irreducible-cluster enumeration, Dumer–Kovalev–Pryadko 2017, with Tanner-graph automorphism orbits; for the
  pair-partition codes an even-weight argument covers the odd levels), and an explicit logical operator of weight `d`
  is given in `witnesses/`.
- **search bound** `d ≤ w`: the lightest logical operator found by a long GPU search (directed BP+OSD with 128-column
  ordered statistics, several runs of 600 s to 3600 s). The operator is published in `witnesses/` so anyone can check
  it; the true distance may be smaller.
- **lower bound** `d ≥ w`: a certificate without a matching operator.

Entries marked *leaderboard, re-measured* are codes of the Unitary Foundation qLDPC challenge
(github.com/unitaryfoundation/qldpc-challenge, snapshot eb2aeae of 2026-11-01). Their check matrices are rebuilt from
the entry's check lists and are not copied here; the row gives the claimed distance, the lightest operator our search
found, and the operator itself, which can be verified against the entry file linked in the row.

## Files

- `codes/<slug>.json` the entry: parameters, family, construction, source, the distance evidence, links to files.
- `matrices/<slug>/HX.mtx`, `HZ.mtx` check matrices (MatrixMarket, pattern, 1-based).
- `witnesses/<slug>.json` supports (0-based qubit indices) of verified logical operators, lists `wx` and `wz`.
- `data/published_codes.json` parameters of published codes used as reference points in the figure (no matrices).
- `tools/verify.py` checks one code and its operators; `tools/check_all.py` checks the whole repository;
  `tools/build_site.py` regenerates `docs/`; `tools/npz_to_mtx.py` converts archived matrices.

```
python tools/verify.py matrices/pp-564-194-60f2ec0b/HX.mtx matrices/pp-564-194-60f2ec0b/HZ.mtx witnesses/pp-564-194-60f2ec0b.json
python tools/check_all.py
```

## Sources of the entries

- The lifted-product codes of arXiv:2606.24808 (v2) with their certificates (repository ziduliu/sce-qldpc).
- Pair-partition codes (construction of arXiv:2609.30069, Lee et al.) found by our program-evolution framework in
  October and November 2026, certified or long-searched as stated per row.
- Non-abelian pair-partition codes designed by hand on 2026-10-31 (marked as such in the source field).
- Re-measured leaderboard entries.

## Submitting a code

Open a pull request with `codes/<slug>.json` and the two check matrices (MatrixMarket, as in `matrices/`), or an
issue with the files attached. We run the same search and, where feasible, the certifier, and add the result as a row
with the evidence. Entries are never listed with a distance that has not been checked here.

## License

Apache License 2.0 (`LICENSE`).
