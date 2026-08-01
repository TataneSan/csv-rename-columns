"""csv-rename-columns - rename CSV columns in bulk.

Renames are provided as a JSON map file ({"old": "new", ...}) or as
OLD=NEW pairs on the command line. An alternative pattern mode applies a
regex substitution to every column name.

Exit codes:
  0  success
  1  error (io, unknown column, bad map)
  2  --check mode: no rename rule matched anything
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys

__version__ = "1.0.0"


def _read(path):
    if path in ("-", None):
        data = sys.stdin.read()
    else:
        with open(path, newline="", encoding="utf-8") as fh:
            data = fh.read()
    try:
        dialect = csv.Sniffer().sniff(data[:8192], delimiters=";,\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.reader(data.splitlines(), dialect))
    if not rows:
        raise ValueError("empty input")
    return rows, dialect


def load_renames(args):
    pairs = {}
    if args.map_file:
        with open(args.map_file, encoding="utf-8") as fh:
            obj = json.load(fh)
        if not isinstance(obj, dict):
            raise ValueError("map file must contain a JSON object")
        pairs.update({str(k): str(v) for k, v in obj.items()})
    for spec in args.pairs or []:
        if "=" not in spec:
            raise ValueError("rename spec must be OLD=NEW: %s" % spec)
        old, new = spec.split("=", 1)
        pairs[old] = new
    return pairs


def main(argv=None):
    p = argparse.ArgumentParser(prog="csv-rename-columns",
                                description="Bulk-rename CSV columns (map file, OLD=NEW pairs, or regex pattern).")
    p.add_argument("input", help="csv file (- / omitted for stdin)")
    p.add_argument("pairs", nargs="*", help="OLD=NEW rename pairs")
    p.add_argument("-m", "--map-file", help="JSON file {old_name: new_name}")
    p.add_argument("--pattern", help="regex applied to each column name")
    p.add_argument("--replace", default=r"\g<0>", help="replacement for --pattern (default: keep match)")
    p.add_argument("--lower", action="store_true", help="lowercase all column names")
    p.add_argument("--snake", action="store_true", help="convert column names to snake_case")
    p.add_argument("--check", action="store_true", help="exit 2 if nothing would be renamed")
    p.add_argument("--dry-run", action="store_true", help="show renames, do not output csv")
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("--json", action="store_true", help="JSON report of renames on stderr")
    p.add_argument("-o", "--output", help="output file (default stdout)")
    p.add_argument("-V", "--version", action="version", version="csv-rename-columns " + __version__)
    args = p.parse_args(argv)

    try:
        rows, dialect = _read(args.input)
        header = rows[0]
        pairs = load_renames(args)

        rx = re.compile(args.pattern) if args.pattern else None

        def transform(name):
            original = name
            if name in pairs:
                name = pairs[name]
            elif rx:
                name = rx.sub(args.replace, name)
                args._touched = True
            if args.lower:
                name = name.lower()
            if args.snake:
                name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name.strip())
                name = re.sub(r"[^0-9A-Za-z]+", "_", name)
                name = re.sub(r"_+", "_", name).strip("_").lower()
            return name, name != original

        new_header = []
        changed = []
        for i, col in enumerate(header):
            nn, did = transform(col)
            new_header.append(nn)
            if did:
                changed.append({"index": i, "old": col, "new": nn})

        known = []
        for old in pairs:
            if old not in header:
                known.append(old)
        if known:
            raise ValueError("column(s) not in header: %s" % ", ".join(known))

        if args.json:
            print(json.dumps({"renamed": changed, "count": len(changed)}, ensure_ascii=False), file=sys.stderr)

        if args.check:
            if not changed:
                if not args.quiet:
                    print("nothing to rename", file=sys.stderr)
                return 2
            return 0

        if args.dry_run:
            for c in changed:
                print("%s -> %s" % (c["old"], c["new"]))
            if not changed and not args.quiet:
                print("no renames")
            return 0

        out_fh = sys.stdout if args.output in ("-", None) else open(args.output, "w", newline="", encoding="utf-8")
        try:
            w = csv.writer(out_fh, dialect=dialect, lineterminator="\n")
            w.writerow(new_header)
            for r in rows[1:]:
                w.writerow(r)
        finally:
            if out_fh is not sys.stdout:
                out_fh.close()
        return 0
    except (ValueError, OSError, csv.Error, json.JSONDecodeError, re.error) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
