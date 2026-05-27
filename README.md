# openapi-diff-checker

Verify if two OpenAPI files are **functionally equivalent*. Ignores cosmetic fields (descriptions, summaries, extensions), handle optional defaults, and compares paths, data types, formats, and structural shape. Resolves `$ref` references before comparing.

## Installation

Requires Python 3.9+.

```bash
pip install openapi-diff-checker
```

Or install from source:

```bash
git clone https://github.com/lorenzobelli/openapi-diff-checker.git
cd openapi-diff-checker
pip install .
```

## Usage

### Command line

```bash
openapi-diff-checker path/to/source.yaml path/to/dest.yaml
```

Exits with code `0` if the specs are functionally equivalent, `1` if differences are found.

Example output when differences exist:

```
Found 2 functional difference(s):

  [added] /paths/~1users/post: value 'object' added
  [removed] /paths/~1health/get: value 'string' removed
```

### As a Python library

```python
from openapi_diff_checker import compare

result = compare("source.yaml", "dest.yaml")

if result.equivalent:
    print("No functional differences")
else:
    for diff in result.differences:
        print(diff.path, diff.kind, diff.detail)
```

`compare()` returns a `DiffResult` with:
- `equivalent` (bool) -- whether the specs are functionally identical
- `differences` (list of `Difference`) -- each with `path`, `kind` (`added`/`removed`/`changed`/`type_changed`), and `detail`

### What is compared

The checker ignores these cosmetic fields:
- `description`, `summary`, `externalDocs`, any `x-` extension
- Inside `/info`: `description`, `termsOfService`, `contact`, `license`

Lists under `required`, `tags`, `security`, and `servers` are compared with set semantics (order doesn't matter). All other fields are compared structurally.

`$ref` references are fully resolved before comparison.

## Development

### Setup

```bash
git clone https://github.com/lorenzobelli/openapi-diff-checker.git
cd openapi-diff-checker
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]' 2>/dev/null || pip install -e .
pip install pytest
```

### Run tests

```bash
pytest
```

### Build

```bash
pip install build
python -m build
```

This produces a wheel and sdist in `dist/`.

## License

MIT
