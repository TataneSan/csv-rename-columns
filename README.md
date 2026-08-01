# csv-rename-columns

Bulk-rename CSV columns: JSON map, OLD=NEW pairs, regex pattern, --lower/--snake normalizers.

Part of a collection of small zero-dependency CLI utilities for file, text and data processing.

## Features

- Renames via JSON map file and/or inline `OLD=NEW` pairs
- `--pattern/--replace` regex renaming applied to every column
- Normalizers: `--lower`, `--snake` (snake_case)
- `--dry-run`, `--check` (exit 2 when nothing matches), `--json` report
- Auto delimiter detection, stdin/stdout

## Install

Requires Python >= 3.9, standard library only.

```bash
pip install .
# or directly from GitHub:
pip install git+https://github.com/TataneSan/csv-rename-columns.git
```

## Usage

```
csv-rename-columns FILE [OLD=NEW ...] [-m map.json] [--pattern RE --replace R] [--lower] [--snake]
```

### Examples

```bash
csv-rename-columns users.csv 'First Name=first_name' 'Last Name=last_name'
csv-rename-columns data.csv --pattern '^col_' --replace ''
cat data.csv | csv-rename-columns - --snake --lower
csv-rename-columns data.csv -m renames.json --dry-run
```

## Exit codes

| Code | Meaning |
|-----:|---------|
| 0 | success |
| 1 | error (io, unknown column, bad map) |
| 2 | --check: no rename matched |

## License

MIT — Copyright (c) 2026 TataneSan
