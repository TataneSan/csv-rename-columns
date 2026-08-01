# csv-rename-columns

Rename CSV columns via OLD=NEW pairs or a regex with capture groups.

Zero dependencies. Pure Python 3.9+.

## Features

- Explicit OLD=NEW pairs via --map or a mapping file
- --regex PATTERN=REPL renames every matching header with capture groups
- Refuses renames that would create duplicate columns
- --json report; --check CI mode fails when no column was renamed

## Install

```bash
pip install .
# or directly from GitHub:
pip install git+https://github.com/TataneSan/csv-rename-columns.git
```

## Usage

```
csv-rename-columns --help
```

Reads from stdin when no file is given (or when the file is `-`).

### Rename two columns explicitly

```bash
csv-rename-columns -m first_name=given last_name=family users.csv
```

### Rename with a regex

```bash
csv-rename-columns --regex '_(name|addr)$=-\1' contacts.csv
```

### CI: fail when nothing matches

```bash
csv-rename-columns -m old=new --check -q data.csv
```


## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | I/O or CLI error |
| 2    | --check condition not satisfied |

## License

MIT
