# AI research index

## Identity and status

Anonymous, v2.0.0-candidate, 2026-10-14. This is an unrefereed research candidate, not a formal proof-assistant development or a verified human-peer-review record. Read [ASSURANCE.md](ASSURANCE.md) before promoting any claim.

Version DOI: https://doi.org/10.5281/zenodo.23362079. Intended immutable tag: `v2.0.0-candidate`.

## Claims and dependencies

[CLAIMS.json](CLAIMS.json) identifies the exact scope and dependencies. The central separation needs three distinct ingredients: matching lcm-lattice/Betti-poset computation; the negative nine-point obstruction for I; and a positive depth-five partition for J. Exact equality for J additionally needs its depth-six exclusion. Generator minimality additionally needs census completeness, integral Betti classification and all ideal invariant values; it does not follow just from the two ideals.

The squarefree colon corollary uses the same lattice invariance theorem, not a new general theorem about colon operations. The quotient values agree. Neither tensor additivity nor the restricted stoss conjecture is assumed.

## Evidence navigation

- [certificates](certificates): concrete partitions and obstruction inputs; corrected quotient identity and final replay summaries are maintained here.
- [data](data): supplied lattice census and invariant/classification inputs, which must be checked rather than trusted as an oracle.
- [code](code): original public finite checking implementation. The complete route is `python3 -B code/verify.py --census`, repeated with `-O`; see [README.md](README.md).
- [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md): objection-by-objection scientific and implementation dispositions.
- [RESEARCH_GATES.json](RESEARCH_GATES.json): retrospective intake scope and explicit verification boundaries.
- [ENVIRONMENT.txt](ENVIRONMENT.txt): dependency and runtime recording policy.

The manuscript source is `paper.tex`; its PDF is `paper.pdf`. Interpret the exact generator correspondence there, not the original draft's differently ordered list. Bottom inclusion contributes beta_0=1 separately from interval homology. Counts of 56 Betti-poset elements include that bottom convention.

## Replay interpretation and failure behaviour

`SAT` means a supplied partition was constructed/checked; `UNSAT` requires an exhaustive negative decision; `UNKNOWN` is neither and cannot silently produce an exact invariant. Normal and optimized execution are separate checks. Semantic negative controls test sensitivity to plausible corruptions, not global mathematical correctness. A manifest checks bytes, not theorem adequacy. Read retained output summaries before reporting any pass, and retain exclusions and unfinished gates explicitly.

## Prior art and trust boundary

Katthän's arXiv:1509.08275v2 supplies the conjecture, distinct ideal/quotient implications, meet closure including top, and colon formulation. Ichim–Katthän–Moyano-Fernández arXiv:1405.3602 supplies lattice invariance and its hypotheses; arXiv:1408.4255 supplies the known census framework and small-generator quotient theorem. The 14 October intake search found no matching earlier resolution in its bounded scope; it is not a proof of novelty. The public package does not redistribute the private reviewer audit or certify its authorship as human/independent. See [ASSURANCE.md](ASSURANCE.md).

Original material licensing is described in [LICENSE](LICENSE) and [LICENSE-CODE](LICENSE-CODE). Do not treat cited papers as covered by those grants. Do not infer four-star quality, a quotient counterexample, a refutation of Stanley's ideal inequality, or resolution of the stoss-restricted programme from this package.
