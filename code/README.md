# Exact finite checks

Python 3.10 or later; standard library only. From the repository root:

```sh
python3 -B code/verify.py --census
python3 -B -O code/verify.py --census
python3 -B code/check_manifest.py
```

The verifier resolves data paths relative to its own file, not the working directory. `--root` overrides the repository directory. Without `--census`, the 7,443-record census is explicitly marked not run. `--output NEW_FILE.json` creates a receipt and refuses to overwrite an existing file. The committed normal/optimized receipts are historical observations, not files the default command changes.

`exact_core.py` and `verify.py` are original replacements for the legacy computational pipeline. They do not import the private supplied audit, NetworkX, a SAT solver, NumPy, or SymPy. They use explicit exceptions, so `python -O` does not remove checks. `SAT`, `UNSAT`, and `UNKNOWN` have no Boolean truth value. Incidence/node exhaustion gives `UNKNOWN`; an exact-depth search then stops rather than lowering its answer. Depth zero is included.

The main checks reconstruct both lcm-lattices, verify integral crosscut homology by unimodular unit pivots, check all 32 and 79 positive ideal intervals, exhaust the nine-point obstruction allowing merged intervals, check its nine deletion witnesses, and exhaust the depth-six obstruction for J. Quotient checks bind ambient dimensions and generators: the corrected five-variable quotient has a 55-singleton depth-zero partition, while the seven-variable quotient has a 125-interval depth-two partition. Exact annihilator witnesses give the matching upper bounds. The obsolete six-coordinate quotient certificate is not included.

The squarefree check constructs all six 14-variable generators from the union of meet-irreducibles, checks minimality and the single-variable colon, and compares all 64 subset-lcms with both closure families. It verifies the concrete reconstruction, not a separate 14-variable depth search; transfer of Stanley dimensions uses the cited lattice-invariance theorem.

The census checks closure, orbit uniqueness, Boolean-lattice inclusion, every allowable meet-irreducible deletion, stored realization and invariant fields, all Betti classes and their common ideal Stanley dimension. Its interpretation relies on the mathematical deletion-reachability theorem, lcm-lattice invariance and the five-generator bound `1 <= spdim(I) <= 2`. Integral reduction refuses a nonzero residual without a unit pivot rather than declaring it torsion-free. All 367 encountered five-atom complexes resolve.

The eleven semantic negative controls include missing/overlapping intervals, wrong ambient dimension, a false annihilator witness, nonunit integral residuals, unsafe truthiness, resource exhaustion, propagation of `UNKNOWN`, and redundant generators. A separate positive regression retains the merged interval that invalidated the old unconditional F5 shortcut. Exhaustive UNSAT claims are reproduced by the search; no DRAT certificate or formal proof-assistant verification is claimed. These finite checks are not a novelty search, independent external reproduction, or computational verification of every prose argument.

`check_manifest.py` checks exact recursive inventory, bytes and SHA-256 against `MANIFEST.json`. The manifest excludes itself, `.git` and `__pycache__`; missing, extra, unsafe, duplicate and symlink entries are rejected. It does not authenticate authorship or validate mathematics.
