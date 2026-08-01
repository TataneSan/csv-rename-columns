#!/usr/bin/env python3
"""csv-rename-columns: rename CSV columns via OLD=NEW pairs or a regex.

Renames columns of a CSV file given an explicit mapping (``old=new``
arguments or a mapping file with one pair per line) or a regex applied to
every header name with capture-group backreferences. Unmapped columns keep
their original name.

Exit codes:
    0  Success.
    1  I/O or CLI error.
    2  --check mode and no column was renamed at all.
"""

import argparse
import csv
import io
import json
import re
import sys


def read_rows(path):
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (path, exc), file=sys.stderr)
        sys.exit(1)
    return list(csv.reader(io.StringIO(text)))


def parse_pair(pair, source):
    if "=" not in pair:
        print("error: %s: expected OLD=NEW, got %r" % (source, pair),
              file=sys.stderr)
        sys.exit(1)
    old, new = pair.split("=", 1)
    return old.strip(), new.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csv-rename-columns",
        description="Rename CSV columns via OLD=NEW pairs or a regex.",
    )
    parser.add_argument(
        "file", nargs="?", default="-",
        help="input CSV file (default: stdin; '-' = stdin)",
    )
    parser.add_argument(
        "-m", "--map", nargs="*", default=[], metavar="OLD=NEW",
        help="explicit column rename pairs (may be repeated)",
    )
    parser.add_argument(
        "--map-file",
        help="file with one OLD=NEW pair per line ('#' comments allowed)",
    )
    parser.add_argument(
        "--regex", metavar="PATTERN=REPL",
        help="rename every header matching PATTERN using REPL "
        "(separated by '='; \\1 ... for capture groups)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="emit a JSON report instead of the renamed CSV",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="CI mode: exit 2 if no column was renamed",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress CSV output (useful with --check)",
    )
    args = parser.parse_args(argv)

    mapping = {}
    for pair in args.map:
        old, new = parse_pair(pair, "--map")
        mapping[old] = new
    if args.map_file:
        try:
            with open(args.map_file, "r", encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    old, new = parse_pair(line, "%s:%d" % (args.map_file, lineno))
                    mapping[old] = new
        except OSError as exc:
            print("error: cannot read %s: %s" % (args.map_file, exc),
                  file=sys.stderr)
            return 1

    rx = None
    rx_repl = None
    if args.regex:
        if "=" not in args.regex:
            print("error: --regex expects PATTERN=REPL", file=sys.stderr)
            return 1
        pattern, rx_repl = args.regex.split("=", 1)
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            print("error: invalid --regex pattern: %s" % exc, file=sys.stderr)
            return 1

    rows = read_rows(args.file)
    if not rows:
        print("error: empty input", file=sys.stderr)
        return 1
    header = rows[0]

    renamed = 0
    renames = {}
    new_header = []
    for name in header:
        if name in mapping:
            new_header.append(mapping[name])
            renames[name] = mapping[name]
            renamed += 1
        elif rx is not None and rx.search(name):
            try:
                new_name = rx.sub(rx_repl, name)
            except re.error as exc:
                print("error: invalid --regex replacement: %s" % exc,
                      file=sys.stderr)
                return 1
            if new_name != name:
                renames[name] = new_name
                renamed += 1
            new_header.append(new_name)
        else:
            new_header.append(name)

    dupes = sorted({n for n in new_header if new_header.count(n) > 1})
    if dupes:
        print("error: renaming would create duplicate columns: %s"
              % ", ".join(dupes), file=sys.stderr)
        return 1

    rows[0] = new_header
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerows(rows)

    if args.as_json:
        print(json.dumps({
            "columns": len(header),
            "renamed": renamed,
            "renames": renames,
            "header": new_header,
        }, indent=2, ensure_ascii=False))
    elif not args.quiet:
        sys.stdout.write(out.getvalue())

    if args.check and renamed == 0:
        print("check failed: no column was renamed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
