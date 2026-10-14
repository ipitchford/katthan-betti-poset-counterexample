# Internal replay, 14 October 2026

Original public implementation: Python standard library, normal and optimized execution, each with `--census`. Both completed with identical mathematical results. Detailed input-bound observations are in `certificates/verification-normal.json` and `certificates/verification-optimized.json`.

Both reconstructed lattices have 60 and 59 elements and the same 56-element Betti poset, including bottom. Integral unit-pivot reductions resolved all encountered boundaries. All 32 I and 79 J positive intervals passed exact membership, disjointness and coverage. The nine-point obstruction has 264 candidate intervals and is UNSAT after 20,391 states in this implementation; each single-point deletion has a checked feasible partial cover. The J depth-six check has 3,097 intervals and is UNSAT after 50 states. The private supplied audit used different memoization/order and visited 564 and 18 states respectively; these are not contradictory mathematical outcomes.

Corrected quotient certificates bind five and seven variables, 55 and 625 box points, and depths zero and two. Direct annihilator witnesses establish their upper bounds. The explicit fourteen-variable squarefree colon construction passed all 64 subset-lcm comparisons, generator minimality and the intended 60/59 lattice identifications. Its Stanley dimensions transfer through the cited lattice-invariance theorem, not a new large-box depth search.

The full census checked all 7,443 orbit representatives, 28,668 distinct labelled deletion children, 367 integral crosscut complexes and 1,485 Betti-poset classes. Values were 1 for 1,358 representatives and 2 for 6,085; no class discrepancy or unresolved search occurred. The largest census search visited 176 states. Completeness additionally uses the cited Boolean-deletion reachability theorem.

Eleven semantic controls passed in both modes. The separate manuscript checker matched all 111 rows and rejected seven corruptions in both modes. Seventeen private manifest-checker fixtures were tested in both modes. These are scoped internal checks, not external reproduction or formal proof.

The three supplied private audit scripts also replayed normally and under optimization with explicit assertion preservation. They are not redistributed. The final public archive is separately replayed from clean extraction by the retained publication gate; the observations above do not substitute for that archive-bound gate.

All twelve manuscript pages were visually inspected after local compilation and successful built-in compilation. The title, equations and complete breakable tables are legible; no proof-bearing overfull box was reported. PDF text and source-table checks remain separate from visual inspection.
