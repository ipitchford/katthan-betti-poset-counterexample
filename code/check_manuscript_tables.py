#!/usr/bin/env python3
"""Compare every printed decomposition row with its JSON interval certificate.

Run from any directory: python3 -B code/check_manuscript_tables.py
Uses only the standard library and explicit checks, also under python -O.
This deliberately parses the release's restricted literal longtable syntax,
not general TeX. It checks transcription, not PDF visibility or mathematical
partition validity (those are separate visual and code/verify.py gates).
All negative controls operate on in-memory copies; inputs are never modified.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys


class TableError(ValueError):
    """Malformed input or mismatch: never a successful partial check."""


def require(condition, message):
    if not condition:
        raise TableError(message)


SPECS = (
    ("I", "I", (2, 2, 2, 2, 2), 32, 188, 2),
    ("J", "I'", (2, 3, 2, 1, 1, 2, 2), 79, 671, 5),
)
TABLE = re.compile(r"\\begin\{longtable\}(.*?)\\end\{longtable\}", re.S)
ROW = re.compile(
    r"\s*([1-9][0-9]*)\s*&\s*\$\(([0-9]+(?:\s*,\s*[0-9]+)*)\)\$"
    r"\s*&\s*\$\\\{([1-9][0-9]*(?:\s*,\s*[1-9][0-9]*)*)\\\}\$\s*\\\\\s*"
)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + str(key))
        result[key] = value
    return result


def vector(raw, length, label):
    require(isinstance(raw, list) and len(raw) == length, label + ": wrong dimension")
    require(all(type(v) is int and v >= 0 for v in raw), label + ": noninteger exponent")
    return tuple(raw)


def check_tables(tex, certificate):
    require(isinstance(certificate, dict), "certificate must be a JSON object")
    require(tex.count(r"\begin{longtable}") == 2, "expected exactly two longtable openings")
    require(tex.count(r"\end{longtable}") == 2, "expected exactly two longtable endings")
    tables = TABLE.findall(tex)
    require(len(tables) == 2, "could not parse exactly two longtables")
    result = {}
    for block, (name, key, bound, count, points, depth) in zip(tables, SPECS):
        require(block.count(r"\endlastfoot") == 1, name + ": missing/ambiguous row-body marker")
        header, body = block.split(r"\endlastfoot")
        caption = (r"\caption{All " + str(count) + " spaces for $" + name
                   + "$", ", covering " + str(points) + " box points; minimum dimension "
                   + str(depth) + ".}")
        require("".join(caption) in header, name + ": unexpected caption or table order")
        require(key in certificate and isinstance(certificate[key], dict), name + ": missing certificate entry")
        partition = certificate[key].get("partition")
        require(isinstance(partition, list) and len(partition) == count, name + ": wrong certificate row count")
        lines = [line for line in body.splitlines() if line.strip()]
        require(len(lines) == count, name + ": wrong printed row count")
        for index, (line, interval) in enumerate(zip(lines, partition), 1):
            label = name + " row " + str(index)
            match = ROW.fullmatch(line)
            require(match is not None, label + ": malformed literal row")
            number, raw_c, raw_z = match.groups()
            require(int(number) == index, label + ": missing, duplicate or reordered row number")
            c_printed = tuple(map(int, raw_c.split(",")))
            z_printed = tuple(map(int, raw_z.split(",")))
            require(isinstance(interval, list) and len(interval) == 2, label + ": malformed certificate interval")
            c = vector(interval[0], len(bound), label)
            d = vector(interval[1], len(bound), label)
            require(all(lo <= hi <= maximum for lo, hi, maximum in zip(c, d, bound)), label + ": invalid interval bounds")
            require(all(hi in (lo, maximum) for lo, hi, maximum in zip(c, d, bound)), label + ": non-normalised interval")
            expected_z = tuple(i + 1 for i, (hi, maximum) in enumerate(zip(d, bound)) if hi == maximum)
            require(len(expected_z) >= depth, label + ": certificate below stated depth")
            require(c_printed == c, label + ": printed exponent vector differs from certificate")
            require(z_printed == expected_z, label + ": printed free-variable indices differ from certificate")
        result[name] = {"rows": count, "certificate_key": key, "ambient_dimension": len(bound),
                        "status": "PASS: every literal row matches"}
    return result


def negative_controls(tex, certificate):
    first = next(line for line in tex.splitlines() if ROW.fullmatch(line))
    mutations = {
        "corrupt exponent": first.replace("(0,0,0,0,2)", "(1,0,0,0,2)"),
        "corrupt free indices": first.replace(r"\{1,3,5\}", r"\{1,3,4\}"),
        "duplicate row number": first.replace("1 &", "2 &", 1),
        "missing row": "",
        "commented row": "% " + first,
        "missing row terminator": first.rstrip().removesuffix(r"\\"),
    }
    rejected = []
    for name, replacement in mutations.items():
        require(replacement != first, "negative control was not mutated: " + name)
        try:
            check_tables(tex.replace(first, replacement, 1), certificate)
        except TableError:
            rejected.append(name)
        else:
            raise TableError("negative control unexpectedly passed: " + name)
    corrupted = copy.deepcopy(certificate)
    corrupted["I"]["partition"][0][1][0] = 1
    try:
        check_tables(tex, corrupted)
    except TableError:
        rejected.append("non-normalised certificate interval")
    else:
        raise TableError("negative control unexpectedly passed: non-normalised certificate interval")
    return rejected


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", type=Path, default=root / "paper.tex")
    parser.add_argument("--certificate", type=Path, default=root / "certificates/counterexample_certificate.json")
    args = parser.parse_args()
    try:
        manuscript_bytes = args.manuscript.read_bytes()
        certificate_bytes = args.certificate.read_bytes()
        tex = manuscript_bytes.decode("utf-8")
        certificate = json.loads(certificate_bytes.decode("utf-8"), object_pairs_hook=unique_object)
        rows = check_tables(tex, certificate)
        controls = negative_controls(tex, certificate)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS", "scope": "literal manuscript-table transcription; not PDF layout or a fresh partition proof",
        "rows_checked": sum(row["rows"] for row in rows.values()), "tables": rows,
        "negative_controls_rejected": controls,
        "sha256": {"manuscript": hashlib.sha256(manuscript_bytes).hexdigest(),
                   "certificate": hashlib.sha256(certificate_bytes).hexdigest(),
                   "checker": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
