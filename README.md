# The Betti poset does not determine ideal Stanley projective dimension

Anonymous · 14 October 2026 · v2.0.0-candidate

Version DOI: https://doi.org/10.5281/zenodo.23362079

An unrefereed mathematical research candidate. Two six-generated monomial ideals have isomorphic Betti posets over every field but ideal Stanley projective dimensions 3 and 2. The finite census establishes that six is the least possible number of generators. The result refutes the **ideal** assertion of Katthän's Betti-poset conjecture; the quotient assertion and the restricted stoss programme remain unresolved by this work.

The revision repairs the nine-point obstruction argument, corrects the quotient realisation, distinguishes unresolved solver thresholds from infeasibility, and supplies an explicit squarefree single-variable colon presentation. It does not refute Stanley's inequality for ideals.

## Reading and checking

Start with [AI_INDEX.md](AI_INDEX.md), [CLAIMS.json](CLAIMS.json), [ASSURANCE.md](ASSURANCE.md), and [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md). The scientific manuscript is `paper.tex` and its generated `paper.pdf`. The original finite checker is `code/verify.py`; its kernel is `code/exact_core.py`.

From the repository root, the complete verification commands are:

```sh
python3 -B code/verify.py --census
python3 -B -O code/verify.py --census
```

The public checker uses Python's standard library. Consult [ENVIRONMENT.txt](ENVIRONMENT.txt) and the actual replay receipt for the tested runtime and results. A command listed here is not a declaration that it has passed. Final execution records belong in `certificates/verification-normal.json` and `certificates/verification-optimized.json`; they bind the checked inputs. Archive hashes and public-provider parity are separate publication checks.

## Scope

- The positive ideal witnesses contain 32 spaces for I and 79 for J.
- The displayed quotient boxes contain 55 and 625 points, not the stale six-variable quotient count.
- The census has 7,443 five-atom lattice representatives and 1,485 Betti-poset classes; the new comparison is ideal-side. The small-generator quotient theorem is prior work.
- All-field conclusions require the integral-homology evidence, not rational ranks alone.
- Finite replay, written proof, priority assessment, formal verification and independent reproduction are different assurance dimensions.

Repository: https://github.com/ipitchford/katthan-betti-poset-counterexample

Original prose and project-generated data: CC0-1.0 ([LICENSE](LICENSE)). Original code: MIT ([LICENSE-CODE](LICENSE-CODE)). Cited works and private referee material are not relicensed or redistributed.
