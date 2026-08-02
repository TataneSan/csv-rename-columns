# csv-rename-columns

Rename CSV columns from a mapping. Pure Python, zero dependencies.

## Features

- `--map old=new,...` renames header columns; unmapped columns pass through
- `--drop-unmapped` removes columns not present in the mapping (with data)
- Unknown mapped names warn on stderr; `--require-mapped` turns them into
  a hard failure (exit 2)
- Duplicate column names after renaming are rejected (exit 2)
- Custom `--delimiter`, `-o FILE` output
- `--json` report of what was renamed/kept/dropped
- Reads stdin when no file is given (or file is `-`)

## Install

```bash
pip install .
# or
pip install git+https://github.com/TataneSan/csv-rename-columns.git
```

## Usage

```bash
# Rename two columns
csv-rename-columns users.csv --map 'first_name=first,last_name=last'

# Keep only the mapped columns
csv-rename-columns users.csv --map 'id=user_id' --drop-unmapped

# Strict CI: every mapped old name must exist
csv-rename-columns users.csv --map 'id=user_id,email=mail' --require-mapped

# From stdin
cat users.csv | csv-rename-columns --map 'email=mail'
```

## Exit codes

- `0` success
- `1` I/O or CLI error
- `2` validation failed (unknown column with `--require-mapped`, or
  duplicate names after renaming)

## License

MIT
