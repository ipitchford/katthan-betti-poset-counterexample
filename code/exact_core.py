"""Original exact combinatorial kernel; Python 3.10+, standard library only.

SAT and UNSAT are distinct from UNKNOWN. No result object or verdict has a
truth value: callers must inspect its explicit status. Resource exhaustion
cannot silently lower a reported depth. Integral boundary reduction uses only
unimodular unit pivots and refuses unresolved residual matrices.
"""
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from itertools import combinations, permutations, product


class VerificationError(Exception):
    pass


class Unresolved(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


class Status(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    UNKNOWN = "UNKNOWN"

    def __bool__(self):
        raise TypeError("Inspect SAT/UNSAT/UNKNOWN explicitly, never by truthiness")


@dataclass
class Decision:
    status: Status
    partition: object = None
    nodes: int = 0
    candidates: int = 0
    reason: str = ""

    def __bool__(self):
        raise TypeError("Inspect Decision.status explicitly")

    def record(self):
        return {"status": self.status.value, "partition": self.partition,
                "nodes": self.nodes, "candidate_intervals": self.candidates,
                "reason": self.reason}


I = ((0, 1, 2, 0, 0), (0, 0, 0, 0, 2), (1, 1, 1, 1, 1),
     (2, 0, 1, 0, 0), (0, 0, 0, 2, 0), (1, 2, 0, 0, 0))
J = ((0, 2, 2, 0, 0, 1, 1), (0, 0, 0, 0, 1, 0, 2),
     (1, 1, 1, 1, 1, 0, 0), (2, 0, 2, 0, 0, 0, 0),
     (0, 0, 0, 1, 0, 2, 0), (1, 3, 0, 0, 0, 0, 0))


def leq(a, b):
    require(len(a) == len(b), "coordinate dimension mismatch")
    return all(x <= y for x, y in zip(a, b))


def validate_generators(generators):
    require(bool(generators) and bool(generators[0]), "nonempty proper monomial ideal required")
    n = len(generators[0])
    require(all(len(g) == n and any(g) and all(type(x) is int and x >= 0 for x in g)
                for g in generators), "invalid generator vector")
    require(all(not leq(g, h) for i, g in enumerate(generators)
                for j, h in enumerate(generators) if i != j), "generators must be distinct and minimal")


def box_bound(generators):
    validate_generators(generators)
    return tuple(max(values) for values in zip(*generators))


def belongs(point, generators):
    return any(leq(g, point) for g in generators)


def characteristic(generators, quotient=False):
    bound = box_bound(generators)
    points = tuple(p for p in product(*(range(g + 1) for g in bound))
                   if belongs(p, generators) != quotient)
    return bound, points


def members(lower, upper):
    return product(*(range(a, b + 1) for a, b in zip(lower, upper)))


def check_partition(generators, partition, depth, quotient=False, required=None):
    bound, points = characteristic(generators, quotient)
    universe = set(points)
    target = universe if required is None else set(map(tuple, required))
    require(target <= universe, "required point outside characteristic poset")
    seen = set()
    for row in partition:
        require(len(row) == 2, "interval needs two endpoints")
        lower, upper = map(tuple, row)
        require(len(lower) == len(bound) == len(upper), "partition ambient dimension mismatch")
        require(all(type(x) is int and x >= 0 for x in lower + upper), "invalid interval coordinate")
        require(leq(lower, upper) and leq(upper, bound), "interval outside box")
        require(all(b == a or b == g for a, b, g in zip(lower, upper, bound)), "interval is not normalized")
        require(sum(b == g for b, g in zip(upper, bound)) >= depth, "partition depth too low")
        covered = set(members(lower, upper))
        require(covered <= universe, "interval leaves characteristic poset")
        require(not seen.intersection(covered), "overlapping intervals")
        seen.update(covered)
    require(target <= seen, "partition misses required points")
    if required is None:
        require(seen == universe, "partition not exact")
    return {"points": len(points), "intervals": len(partition), "depth_at_least": depth}


def normalized_intervals(points, bound, depth, max_incidence):
    require(type(depth) is int and 0 <= depth <= len(bound), "invalid depth threshold")
    index = {point: i for i, point in enumerate(points)}
    rows, incidence = [], 0
    for lower in points:
        unfixed = [i for i, value in enumerate(lower) if value < bound[i]]
        for count in range(min(len(unfixed), len(bound) - depth) + 1):
            for fixed in combinations(unfixed, count):
                fixed = set(fixed)
                upper = tuple(lower[i] if i in fixed else bound[i] for i in range(len(bound)))
                if upper not in index:
                    continue
                mask, valid = 0, True
                for point in members(lower, upper):
                    incidence += 1
                    if incidence > max_incidence:
                        raise Unresolved("point-interval incidence limit")
                    if point not in index:
                        valid = False
                        break
                    mask |= 1 << index[point]
                if valid:
                    rows.append((lower, upper, mask))
    return rows


def decide(generators, depth, quotient=False, required=None,
           node_limit=2000000, max_incidence=5000000):
    bound, points = characteristic(generators, quotient)
    index = {point: i for i, point in enumerate(points)}
    targets = points if required is None else tuple(map(tuple, required))
    require(all(point in index for point in targets), "required point not in poset")
    needed = sum(1 << index[point] for point in set(targets))
    try:
        rows = normalized_intervals(points, bound, depth, max_incidence)
    except Unresolved as error:
        return Decision(Status.UNKNOWN, reason=str(error))
    rows = [row for row in rows if row[2] & needed]
    by_point = {}
    for j, (_, _, mask) in enumerate(rows):
        overlap = mask & needed
        while overlap:
            bit = overlap & -overlap
            by_point.setdefault(bit, []).append(j)
            overlap ^= bit
    nodes = 0

    @lru_cache(None)
    def search(occupied):
        nonlocal nodes
        nodes += 1
        if nodes > node_limit:
            raise Unresolved("backtracking node limit")
        remaining = needed & ~occupied
        if not remaining:
            return ()
        best = None
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            choices = [j for j in by_point.get(bit, ()) if not rows[j][2] & occupied]
            if not choices:
                return None
            if best is None or len(choices) < len(best):
                best = choices
                if len(best) == 1:
                    break
        for j in best:
            suffix = search(occupied | rows[j][2])
            if suffix is not None:
                return (j,) + suffix
        return None

    try:
        answer = search(0)
    except (Unresolved, RecursionError) as error:
        return Decision(Status.UNKNOWN, nodes=nodes, candidates=len(rows), reason=str(error))
    if answer is None:
        return Decision(Status.UNSAT, nodes=nodes, candidates=len(rows), reason="exhaustive search exhausted")
    partition = [[list(rows[j][0]), list(rows[j][1])] for j in answer]
    check_partition(generators, partition, depth, quotient, targets)
    return Decision(Status.SAT, partition, nodes, len(rows), "partition checked exactly")


def exact_depth(generators, quotient=False, decision=decide, **limits):
    for depth in range(len(generators[0]), -1, -1):
        result = decision(generators, depth, quotient=quotient, **limits)
        if result.status is Status.UNKNOWN:
            raise Unresolved("depth unresolved at threshold " + str(depth) + ": " + result.reason)
        if result.status is Status.SAT:
            return depth, result.partition
        require(result.status is Status.UNSAT, "unrecognized decision status")
    raise VerificationError("depth zero must admit the singleton partition")


def lattice(generators):
    validate_generators(generators)
    family = {0}
    for mask in range(1, 1 << len(generators)):
        selected = [g for i, g in enumerate(generators) if mask >> i & 1]
        bound = tuple(max(values) for values in zip(*selected))
        family.add(sum(1 << i for i, g in enumerate(generators) if leq(g, bound)))
    return frozenset(family)


def family_bits(family):
    return sum(1 << member for member in family)


def unit_rank(matrix):
    """Certify Smith diagonal entries all units using unimodular elimination.

    A nonzero matrix without a unit pivot is UNKNOWN, never called torsion-free.
    Returning rank certifies equivalence over Z to diag(1,...,1,0,...,0).
    """
    work = [list(row) for row in matrix]
    rank = 0
    while work and work[0]:
        pivot = next(((i, j) for i, row in enumerate(work) for j, x in enumerate(row) if abs(x) == 1), None)
        if pivot is None:
            if any(x for row in work for x in row):
                raise Unresolved("nonunit residual integral boundary; general Smith reduction required")
            break
        i, j = pivot
        work[0], work[i] = work[i], work[0]
        for row in work:
            row[0], row[j] = row[j], row[0]
        leading = [x * work[0][0] for x in work[0]]
        work = [[x - row[0] * y for x, y in zip(row[1:], leading[1:])] for row in work[1:]]
        rank += 1
    return rank


@lru_cache(None)
def integral_complex(face_mask, atoms):
    faces = [tuple(i for i in range(atoms) if mask >> i & 1)
             for mask in range(1 << atoms) if face_mask >> mask & 1]
    require(() in faces, "augmented complex must contain empty face")
    by_size = [[face for face in faces if len(face) == size] for size in range(atoms + 1)]
    ranks = [0] * (atoms + 2)
    for size in range(1, atoms + 1):
        rows, columns = by_size[size - 1], by_size[size]
        lookup = {face: i for i, face in enumerate(rows)}
        matrix = [[0] * len(columns) for _ in rows]
        for j, face in enumerate(columns):
            for i in range(size):
                boundary_face = face[:i] + face[i + 1:]
                require(boundary_face in lookup, "faces not downward closed")
                matrix[lookup[boundary_face]][j] = (-1) ** i
        ranks[size] = unit_rank(matrix)
    return tuple((size + 1, len(by_size[size]) - ranks[size] - ranks[size + 1])
                 for size in range(atoms + 1) if len(by_size[size]) - ranks[size] - ranks[size + 1])


def betti(family, atoms):
    result = {0: {0: 1}}
    for member in sorted(family):
        if not member:
            continue
        faces = 1
        for lower in family:
            if lower != member and lower & member == lower:
                sub = lower
                while sub:
                    faces |= 1 << sub
                    sub = (sub - 1) & lower
        homology = dict(integral_complex(faces, atoms))
        if homology:
            result[member] = homology
    return result


class Canonicalizer:
    """Atom permutation orbit minimum, via independently built byte tables."""
    def __init__(self, atoms):
        self.atoms = atoms
        self.tables = []
        self.cache = {}
        width = (1 << atoms) // 8
        require(atoms >= 3, "byte canonicalizer requires at least three atoms")
        for permutation in permutations(range(atoms)):
            image = [sum(1 << permutation[i] for i in range(atoms) if subset >> i & 1)
                     for subset in range(1 << atoms)]
            blocks = []
            for block in range(width):
                table = [0] * 256
                for value in range(1, 256):
                    bit = value & -value
                    table[value] = table[value ^ bit] | (1 << image[8 * block + bit.bit_length() - 1])
                blocks.append(table)
            self.tables.append(blocks)

    def __call__(self, bits):
        if bits not in self.cache:
            chunks = [(bits >> (8 * i)) & 255 for i in range(len(self.tables[0]))]
            best = bits
            for blocks in self.tables:
                value = 0
                for table, chunk in zip(blocks, chunks):
                    value |= table[chunk]
                best = min(best, value)
            self.cache[bits] = best
        return self.cache[bits]
