"""csv-rename-columns: rename CSV columns from a mapping.

Rewrites the header row of a CSV according to --map old=new pairs.
Columns not listed in the mapping are kept unchanged unless --drop-unmapped
is given (then they are removed with their data).

Exit codes:
    0  success
    1  I/O, parse or CLI error
    2  a CI gate failed (unknown column in --map, --require-mapped,
       duplicate column names after renaming)
"""

import argparse
import csv
import io
import json
import sys


def parse_mapping(spec):
    mapping = {}
    for pair in spec.split(","):
        if "=" not in pair:
            raise ValueError(f"invalid mapping entry {pair!r} (expected old=new)")
        old, new = pair.split("=", 1)
        old, new = old.strip(), new.strip()
        if not old or not new:
            raise ValueError(f"invalid mapping entry {pair!r}")
        mapping[old] = new
    return mapping


def read_csv(path, delimiter):
    if path is None or path == "-":
        return list(csv.reader(sys.stdin, delimiter=delimiter))
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh, delimiter=delimiter))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csv-rename-columns",
        description="Rename CSV columns from a --map old=new mapping.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="CSV file (default: stdin, '-' for stdin)",
    )
    parser.add_argument(
        "--map",
        required=True,
        metavar="OLD=NEW,...",
        help="comma-separated rename pairs",
    )
    parser.add_argument(
        "--delimiter", default=",", metavar="C", help="CSV delimiter (default: ,)"
    )
    parser.add_argument(
        "--drop-unmapped",
        action="store_true",
        help="drop columns not present in the mapping (with their data)",
    )
    parser.add_argument(
        "--require-mapped",
        action="store_true",
        help="fail (exit 2) when a mapped old name is absent from the header",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="write result to FILE"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="suppress normal output"
    )
    args = parser.parse_args(argv)

    try:
        mapping = parse_mapping(args.map)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        rows = read_csv(args.file, args.delimiter)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("error: empty CSV", file=sys.stderr)
        return 1

    header = [c.strip() for c in rows[0]]
    header_set = set(header)

    failures = []
    unknown = [o for o in mapping if o not in header_set]
    if unknown:
        if args.require_mapped:
            failures.append(
                f"mapped column(s) not in header: {', '.join(unknown)}"
            )
        else:
            print(
                f"warning: ignored unknown column(s) in --map: {', '.join(unknown)}",
                file=sys.stderr,
            )

    keep_idx = [
        i for i, name in enumerate(header) if not args.drop_unmapped or name in mapping
    ]
    new_header = [mapping.get(header[i], header[i]) for i in keep_idx]

    dupes = sorted({c for c in new_header if new_header.count(c) > 1})
    if dupes:
        failures.append(f"duplicate column name(s) after rename: {', '.join(dupes)}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 2

    out_rows = [new_header]
    for row in rows[1:]:
        out_rows.append([row[i] if i < len(row) else "" for i in keep_idx])

    if args.json:
        print(
            json.dumps(
                {
                    "renamed": {o: n for o, n in mapping.items() if o in header_set},
                    "kept": len(keep_idx),
                    "dropped": len(header) - len(keep_idx),
                    "new_header": new_header,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=args.delimiter, lineterminator="\n")
    writer.writerows(out_rows)
    output = buf.getvalue()

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as fh:
                fh.write(output)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"wrote {args.output}")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
