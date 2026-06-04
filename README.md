# openapi-diff-checker

Verify if two OpenAPI files are **functionally equivalent**. Ignores cosmetic fields (descriptions, summaries, extensions), handles optional defaults, and compares paths, data types, formats, and structural shape. Resolves `$ref` references before comparing.

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

  [added] /paths//users/post/responses/401 (src:34, dest:42): response '401' added
  [changed] /servers (src:7, dest:7): set-like array length 2 -> 1
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

### Equivalence rules

The checker compares the **functional contract** of two specs, not their exact text. The following high-level rules apply.

#### Treated as equivalent (ignored or normalized)

- **Documentation fields** — `description`, `summary`, `externalDocs`, and any `x-` extension.
- **Info metadata** — `title`, `version`, `description`, `termsOfService`, `contact`, `license`.
- **Examples** — `example` / `examples` values, including when an example is present on only one side.
- **Order, where order has no meaning** — `required`, `tags`, `servers`, `enum`, `oneOf` / `anyOf` / `allOf`, the `parameters` list, and the order of paths.
- **References & components** — a `$ref` vs its inlined equivalent, the names of schema components, and unused (orphan) component definitions.
- **Omitted vs default** — an optional field left at its default value (e.g. `required: false`, `nullable: false`, `additionalProperties: true`) vs the field being omitted.
- **Formatting** — quoted vs unquoted response codes (`"200"` vs `200`) and YAML style (flow vs block).
- **OpenAPI patch version** — the patch component of the `openapi` field is ignored (`3.0.0` vs `3.0.3`), per the spec; major/minor differences are still flagged.
- **Path parameter names** — `/items/{id}` and `/items/{itemId}` describe the same endpoint.
- **Security scheme names** — a scheme name is a local binding, so the same definition under different names (e.g. `BearerAuth` vs `bearerAuth`) is equivalent.
- **`operationId`** — an operation's `operationId` is a tooling/codegen identifier, not part of the request/response contract, so it is ignored (a Link Object's `operationId`, which targets an operation, is still compared — see below).
- **Security expressed differently** — a global `security` default vs the same requirement repeated per operation, and an explicit `security: []` vs an implicitly public operation.

#### Treated as a difference (flagged)

- **Added or removed** paths, operations, responses, parameters, or properties.
- **Data type / format changes** — `type`, `format`, or a value whose type changes.
- **Schema changes** — changed `enum` members or changed structural shape.
- **Security changes** — adding/removing a required scheme, or changing a security scheme definition (e.g. `scheme: bearer` → `basic`, or `bearerFormat`).
- **Different URL structure** — extra or renamed path segments, or a different number of path parameters.
- **Parameter identity** — the same parameter name in a different location (e.g. `path` vs `query`).
- **Required vs omitted** — `required: true` vs the field being absent.
- **Link target** — a Link Object's `operationId` (which operation a link points to) changing.

`$ref` references are fully resolved before comparison.

### Known limitations

`$ref` resolution is not yet cycle-safe or fault-tolerant. These inputs currently raise an exception instead of producing a diff:

- **Circular `$ref`** — a schema that references itself (directly or transitively, e.g. a recursive tree/linked-list node) causes infinite resolution (`RecursionError`).
- **Dangling `$ref`** — an internal `$ref` pointing at a non-existent component (e.g. `#/components/schemas/Missing`) raises a `KeyError`.

Both are known and not yet handled; avoid running the checker on specs with recursive or broken references until this is addressed.

## Development

> **Working with an AI agent?** See [`.llm/AGENTS.md`](.llm/AGENTS.md) for the
> principles on how to extend this tool (TDD, driver + guard tests, keeping the
> README in sync, the comparison pipeline, and what's out of scope).

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
