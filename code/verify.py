#!/usr/bin/env python3
"""Original, stdlib-only finite replay. No assertion is disabled by python -O.

Run with --census for the full 7,443-record census. Output is JSON on stdout;
--output FILE additionally creates a new receipt (refuses overwrite).
This is finite exact computation, not formal verification or a novelty audit.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import reduce
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from exact_core import (I, J, Canonicalizer, Decision, Status, Unresolved,
                        VerificationError, belongs, betti, box_bound,
                        characteristic, check_partition, decide, exact_depth,
                        family_bits, integral_complex, lattice, leq, members,
                        require, unit_rank, validate_generators)


def read(root, relative):
    return json.loads((root / relative).read_text())


def mask(values):
    require(len(values) == len(set(values)), "duplicate atom in a set")
    return sum(1 << i for i in values)


def witness_bound(generators, point, blocked):
    require(not belongs(point, generators), "upper-bound witness lies in ideal")
    require(len(blocked) == len(set(blocked)), "duplicate blocked coordinate")
    for coordinate in blocked:
        require(0 <= coordinate < len(point), "invalid blocked coordinate")
        shifted = list(point)
        shifted[coordinate] += 1
        require(belongs(shifted, generators), "claimed blocked variable is free")
    return len(point) - len(blocked)


def require_rejection(label, callback, exception=VerificationError):
    try:
        callback()
    except exception:
        return label
    raise VerificationError("negative control unexpectedly accepted: " + label)


def negative_controls(partition):
    controls = []
    controls.append(require_rejection("missing interval", lambda: check_partition(I, partition[1:], 2)))
    controls.append(require_rejection("overlapping interval", lambda: check_partition(I, partition + partition[:1], 2)))
    controls.append(require_rejection("wrong ambient dimension", lambda: check_partition(I, [[[0]*6, [0]*6]], 0, True)))
    controls.append(require_rejection("false socle witness", lambda: witness_bound(I, I[0], [0])))
    controls.append(require_rejection("nonunit boundary is unresolved", lambda: unit_rank([[2]]), Unresolved))
    controls.append(require_rejection("status has no truth value", lambda: bool(Status.UNKNOWN), TypeError))
    controls.append(require_rejection("decision has no truth value", lambda: bool(Decision(Status.UNSAT)), TypeError))
    require(decide(I, 3, max_incidence=0).status is Status.UNKNOWN, "incidence cap must return UNKNOWN")
    controls.append("incidence exhaustion stays UNKNOWN")
    require(decide(I, 3, node_limit=0).status is Status.UNKNOWN, "node cap must return UNKNOWN")
    controls.append("node exhaustion stays UNKNOWN")
    calls = []
    def unresolved_then_sat(gens, depth, **kwargs):
        calls.append(depth)
        return Decision(Status.UNKNOWN if len(calls) == 1 else Status.SAT)
    controls.append(require_rejection("UNKNOWN cannot lower exact depth", lambda: exact_depth(I, decision=unresolved_then_sat), Unresolved))
    require(calls == [5], "depth search continued after UNKNOWN")
    controls.append(require_rejection("redundant generator", lambda: validate_generators(I + (I[0],))))
    return controls


def core_checks(root):
    certificate = read(root, "certificates/counterexample_certificate.json")
    li, lj = lattice(I), lattice(J)
    require(len(li) == 60 and len(lj) == 59 and li - lj == {62} and lj <= li, "lattice pair mismatch")
    bi, bj = betti(li, 6), betti(lj, 6)
    require(bi == bj and len(bi) == 56, "Betti posets differ")
    totals = Counter()
    for values in bi.values():
        totals.update(values)
    require([totals[i] for i in range(6)] == [1, 6, 15, 20, 12, 2], "Betti totals mismatch")
    positive = {}
    for name, gens, depth, family in (("I", I, 2, li), ("I'", J, 5, lj)):
        record = certificate[name]
        require({mask(row) for row in record["lattice"]} | {0} == family, "certificate lattice mismatch")
        supplied = {mask(json.loads(key)): {int(i): v for i, v in value.items()}
                    for key, value in record["betti"].items()}
        require({0: {0: 1}, **supplied} == bi, "certificate Betti data mismatch")
        require(record["sdepth"] == depth, "certificate depth mismatch")
        positive[name] = check_partition(gens, record["partition"], depth)
    require(positive["I"]["intervals"] == 32 and positive["I'"]["intervals"] == 79, "partition size mismatch")
    core_record = read(root, "certificates/unsat_core_I5.json")
    require(tuple(core_record["lcm"]) == box_bound(I), "core bound mismatch")
    core = core_record["core_points"]
    require(len(core) == 9 and len(set(map(tuple, core))) == 9, "nine distinct core points required")
    obstruction = decide(I, 3, required=core)
    require(obstruction.status is Status.UNSAT, "core obstruction not proved")
    deletions = []
    for i in range(len(core)):
        result = decide(I, 3, required=core[:i] + core[i+1:])
        require(result.status is Status.SAT, "core deletion not satisfiable")
        deletions.append({"deleted_point": core[i], **result.record()})
    # This legal merged interval falsifies the old unconditional F5 shortcut.
    merger = [[[2, 1, 1, 0, 0], [2, 1, 1, 2, 2]]]
    check_partition(I, merger, 3, required=[(2, 1, 1, 1, 0), (2, 1, 1, 0, 1)])
    j_upper = decide(J, 6)
    require(j_upper.status is Status.UNSAT, "J depth-six obstruction not proved")
    quotient = read(root, "certificates/quotient_certificate.json")
    quotient_results = {}
    for name, gens, depth in (("S/I", I, 0), ("S/J", J, 2)):
        entry = quotient[name]
        require(tuple(map(tuple, entry["generators"])) == gens, "quotient realization mismatch")
        require(entry["ambient_variables"] == len(gens[0]), "quotient dimension mismatch")
        require(tuple(entry["lcm"]) == box_bound(gens), "quotient bound mismatch")
        require(entry["sdepth"] == depth and entry["spdim"] == len(gens[0]) - depth, "quotient claimed depth mismatch")
        quotient_results[name] = check_partition(gens, entry["partition"], depth, True)
        require(witness_bound(gens, entry["upper_bound_witness"], entry["blocked_coordinates"]) == depth, "quotient upper bound mismatch")
    computed_zero, _ = exact_depth(I, quotient=True)
    require(computed_zero == 0, "depth-zero search regression")
    return {"lattice_sizes": [len(li), len(lj)], "common_Betti_poset_size": len(bi),
            "quotient_Betti_totals": [totals[i] for i in range(6)],
            "integral_boundaries": "all reduced using unimodular unit pivots; no nonunit residual",
            "ideal_partitions": positive, "core_obstruction": obstruction.record(),
            "core_deletion_witnesses": deletions, "merged_interval_regression": "PASS",
            "J_depth_six": j_upper.record(), "quotient_partitions_and_upper_bounds": quotient_results,
            "negative_controls": negative_controls(certificate["I"]["partition"])}


def meet_irreducibles(family):
    top = reduce(int.__or__, family)
    result = []
    for element in family - {top}:
        strict_uppers = [x for x in family if x != element and element & x == element]
        if reduce(int.__and__, strict_uppers, top) != element:
            result.append(element)
    return frozenset(result)


def colon_checks():
    labels_text = ["125", "245", "2345", "12345", "1246", "2346", "12346",
                   "256", "2356", "12356", "1456", "3456", "13456", "23456"]
    labels = [sum(1 << (int(c)-1) for c in label) for label in labels_text]
    expected_supports = [(2, 3, 6, 8, 9, 12, 14), (11, 12, 13), (1, 2, 5, 8, 11),
                         (1, 8, 9, 10), (5, 6, 7), (1, 2, 3, 4)]
    h = tuple(tuple(int(not label & (1 << i)) for label in labels) for i in range(6))
    require([tuple(j+1 for j, x in enumerate(g) if x) for g in h] == expected_supports, "squarefree displayed generators mismatch")
    colon = tuple(g[:-1] + (0,) for g in h)
    validate_generators(h)
    validate_generators(colon)
    li, lj = lattice(I), lattice(J)
    require(set(labels) == meet_irreducibles(li) | meet_irreducibles(lj), "label union mismatch")
    require([i for i, g in enumerate(h) if g[-1]] == [0], "colon changes a generator other than g1")
    require(lattice(h) == li and lattice(colon) == lj, "squarefree colon lattice mismatch")
    # Reconstruct every subset-lcm and its atom closure, including the empty set.
    records = []
    for subset in range(64):
        row = {"atom_subset_mask": subset}
        for name, gens, family in (("H", h, li), ("colon", colon, lj)):
            value = tuple(max((g[j] for i, g in enumerate(gens) if subset >> i & 1), default=0) for j in range(14))
            closure = sum(1 << i for i, g in enumerate(gens) if leq(g, value))
            expected = reduce(int.__and__, (x for x in family if x & subset == subset), 63)
            require(closure == expected, "subset-lcm closure mismatch")
            row[name] = {"lcm": value, "atom_closure_mask": closure}
        records.append(row)
    return {"variables": 14, "generators": h, "colon_generators": colon,
            "labels_one_based": labels_text, "subset_lcm_checks": records,
            "conclusion": "exact lattice reconstruction only; Stanley dimensions transferred by cited lattice-invariance theorem"}


def census_checks(root):
    supplied_families = read(root, "data/lattices_k5.json")
    invariants = read(root, "data/invariants_k5.json")
    classes = read(root, "data/betti_classes_k5.json")
    require(len(supplied_families) == len(invariants) == 7443, "census size mismatch")
    canonical = Canonicalizer(5)
    families = [frozenset(map(mask, row)) for row in supplied_families]
    keys = {canonical(family_bits(family)) for family in families}
    require(len(keys) == 7443 and family_bits(range(32)) in keys, "duplicate orbit or missing Boolean lattice")
    children = set()
    grouping = defaultdict(list)
    distribution = Counter()
    complex_masks = set()
    decisions = []
    max_nodes = 0
    for index, (family, record) in enumerate(zip(families, invariants)):
        require({0, 1, 2, 4, 8, 16, 31} <= family, "missing lattice atom/bound")
        require(all(x & y in family for x in family for y in family), "family not meet closed")
        require(record["idx"] == index and record["family"] == supplied_families[index], "record/family order mismatch")
        height = {0: 0}
        for element in sorted(family - {0}, key=int.bit_count):
            height[element] = 1 + max(height[x] for x in family if x != element and x & element == x)
        require(record["size"] == len(family) and record["length"] == height[31], "lattice size/length mismatch")
        for removed in meet_irreducibles(family):
            if removed and removed & (removed - 1):
                child = family_bits(family - {removed})
                children.add(child)
                require(canonical(child) in keys, "missing allowable deletion child")
        computed = betti(family, 5)
        ordered = list(map(mask, record["family"]))
        stored = {ordered[int(i)]: {int(h): v for h, v in values.items()} for i, values in record["betti"].items()}
        require(computed == stored, "stored multigraded Betti numbers disagree at " + str(index))
        pdim = max(h for values in computed.values() for h in values)
        require(record["pdim_SI"] == pdim and record["pdim_I"] == pdim - 1, "projective dimension mismatch")
        require(set(record["betti_elems"]) == {i for i, element in enumerate(ordered) if element in computed}, "Betti support mismatch")
        # Stored edges index the ordered Betti support, not the whole family.
        support = [ordered[i] for i in record["betti_elems"]]
        expected_edges = {(i, j) for i, x in enumerate(support) for j, y in enumerate(support)
                          if i != j and x & y == x}
        require(set(map(tuple, record["betti_edges"])) == expected_edges, "Betti order mismatch")
        for member in family - {0}:
            faces = 1
            for lower in family:
                if lower != member and lower & member == lower:
                    sub = lower
                    while sub:
                        faces |= 1 << sub
                        sub = (sub - 1) & lower
            complex_masks.add(faces)
        gens = tuple(map(tuple, record["gens"]))
        require(lattice(gens) == family, "realization mismatch")
        require(record["n_vars"] == len(gens[0]) and tuple(record["lcm"]) == box_bound(gens), "realization dimension/bound mismatch")
        result = decide(gens, len(gens[0]) - 1)
        if result.status is Status.UNKNOWN:
            raise Unresolved("census index " + str(index) + ": " + result.reason)
        spdim = 1 if result.status is Status.SAT else 2
        require(result.status in (Status.SAT, Status.UNSAT), "invalid verdict")
        require(spdim == record["spdim_I"], "stored Stanley dimension disagrees at " + str(index))
        grouping[canonical(family_bits(computed))].append(index)
        distribution[spdim] += 1
        decisions.append({"index": index, "spdim_I": spdim, "status_at_n_minus_one": result.status.value,
                          "nodes": result.nodes, "candidate_intervals": result.candidates})
        max_nodes = max(max_nodes, result.nodes)
        if index and index % 1000 == 0:
            print("verified census records: " + str(index), file=sys.stderr, flush=True)
    require(len(children) == 28668, "deletion child count mismatch")
    require(sorted(map(tuple, grouping.values())) == sorted(tuple(sorted(group)) for group in classes), "Betti class partition mismatch")
    require(len(grouping) == 1485 and len(complex_masks) == 367, "class/complex count mismatch")
    require(distribution == {1: 1358, 2: 6085}, "Stanley distribution mismatch")
    require(all(len({invariants[i]["spdim_I"] for i in group}) == 1 for group in classes), "class discrepancy")
    require(read(root, "data/violations_k5.json") == [], "stored violation list is not empty")
    return {"representatives": 7443, "Betti_classes": len(grouping), "distinct_labelled_deletion_children": len(children),
            "distinct_integral_crosscut_complexes": len(complex_masks), "spdim_distribution": dict(distribution),
            "class_discrepancies": 0, "unresolved": 0, "max_search_nodes": max_nodes, "decisions": decisions,
            "external_dependencies": ["deletion reachability of finite atomistic lattices from the Boolean lattice",
                                      "lcm-lattice invariance", "five-generator bound 1 <= spdim(I) <= floor(5/2)"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--census", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    start = time.monotonic()
    root = args.root.resolve()
    result = {"schema": 1, "utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "optimized": sys.flags.optimize, "scope": "finite exact checks; not a universal proof or independent reproduction"}
    result["core"] = core_checks(root)
    result["squarefree_colon"] = colon_checks()
    result["census"] = census_checks(root) if args.census else {"status": "NOT RUN; use --census"}
    paths = sorted((root / "code").glob("*.py")) + sorted((root / "data").glob("*.json"))
    paths += [root / "certificates" / name for name in ("counterexample_certificate.json", "unsat_core_I5.json", "quotient_certificate.json")]
    result["input_sha256"] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result["elapsed_seconds"] = time.monotonic() - start
    result["status"] = "PASS"
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as output:
            output.write(encoded)
        print(json.dumps({"status": "PASS", "receipt": str(args.output), "elapsed_seconds": result["elapsed_seconds"],
                          "census": args.census, "optimized": sys.flags.optimize}))
    else:
        print(encoded, end="")


if __name__ == "__main__":
    try:
        main()
    except (VerificationError, Unresolved) as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(2)
