# Agent instructions — openapi-diff-checker

Instructions for AI agents (Claude Code and others) working on this repository.
Read this before making changes.

## What this project is

A CLI + Python library that decides whether two OpenAPI specs are **functionally
equivalent** — i.e. they describe the same wire contract a client must obey
(paths, operations, parameters, request/response schemas, types, formats,
security requirements).

It is **not** a breaking-change detector, and it does **not** care about codegen
or SDK concerns. "Equivalent" means *a client interacting with either spec
behaves identically*, not *the YAML is identical*.

## Golden rules (do not skip these)

1. **Keep the README in sync.** Any change to what is or isn't considered a
   difference MUST update the "Equivalence rules" section in `README.md` (and
   "Known limitations" when relevant). The README is the user-facing source of
   truth for behavior.
2. **Test-driven, always.** Write a failing test first, run it and watch it
   fail, then implement, then watch it pass. Never implement first.
3. **Every equivalence relaxation needs two tests:** a *driver* ("X and Y are
   equivalent") **and** a *guard* ("a genuinely different X is still flagged").
   Making something equivalent without a guard risks silently swallowing real
   differences — never do it.
4. **Document every decision in three places:** a code comment with the
   rationale (and a link to the OpenAPI spec when the decision is spec-based),
   a test class docstring stating the decision, and the README.
5. **Verify on the sample files** (`src.yaml`/`dst.yaml`, `src1.yaml`/`dst1.yaml`)
   after a change, in addition to the test suite.

## How to decide "equivalent vs different"

- **Equivalent** = identical functional contract. Ignore things that don't
  change what a client sends, receives, or how it authenticates:
  documentation (`description`/`summary`/`externalDocs`/`x-*`), info metadata,
  examples, ordering where order is semantically irrelevant, **local
  identifiers** (schema component names, security scheme names, path-parameter
  names, `operationId`), formatting (response-code quoting, YAML flow vs block),
  omitted-vs-default values, and the OpenAPI patch version.
- **Different** = anything that changes the contract: added/removed
  paths/operations/responses/parameters/properties, type/format changes, enum
  membership, schema constraints, security requirements or scheme definitions,
  URL structure, parameter identity (`name`+`in`), required-vs-omitted.
- **When unsure**, consult the OpenAPI specification and prefer the
  wire-contract interpretation. Cite the spec section in a comment. Distinguish
  "valid alternative spelling" (e.g. `"200"` vs `200` → equivalent) from
  "invalid value" (e.g. `type: Number` → a real difference, since only
  lowercase `number` is valid).

## Architecture

- All comparison logic lives in `openapi_diff_checker/checker.py`; the CLI is in
  `cli.py`.
- `compare()` runs a pipeline of **pure transform functions** over the parsed
  specs, then does a structural diff:

  ```
  _resolve_refs            # inline internal $refs
  _resolve_security        # push global security onto operations; canonicalize public
  _normalize_openapi_version  # compare major.minor only
  _normalize_path_params   # /items/{id} == /items/{x} (positional placeholders)
  _inline_security_schemes # scheme names are local bindings; inline definitions
  _strip_orphan_components # drop unreferenced components
  _compare_nodes           # the structural diff
  ```

- **To add a new equivalence rule**, prefer a pure function (parsed dict in,
  transformed dict out; `copy.deepcopy` before mutating) inserted into the
  pipeline. For simpler cases, extend the data-driven sets:
  `COSMETIC_KEYS`, `INFO_COSMETIC_KEYS`, `SET_SEMANTICS_KEYS`, `DEFAULT_VALUES`.
- **Order-independent lists** go in `SET_SEMANTICS_KEYS`. Lists whose items have
  an identity (e.g. `parameters` keyed by `name`+`in`) get a dedicated keyed
  comparison rather than set semantics.
- **Line numbers** come from the raw YAML (`_LineMap`). They are resolved either
  exactly or by following `$ref` provenance back to the component definition.
  Never fabricate a line: if a path is synthetic and unresolvable, return
  `None` so the line is omitted rather than wrong.

## Tests

- Run the suite: `.venv/bin/python -m pytest` (the package is installed editable,
  so source edits need no rebuild; only `pyproject.toml` changes do).
- Coverage: `.venv/bin/python -m pytest --cov=openapi_diff_checker --cov-report=term-missing`
- Tests are split by concern — put new tests in the matching file, or create a
  new one for a new concern:
  - `test_core_diff.py` — baseline diff, add/remove, type changes, methods, content types
  - `test_cosmetic.py` — ignored fields (docs, info, examples, quoting, version, operationId)
  - `test_ordering.py` — set semantics / order-independence
  - `test_references.py` — `$ref` resolution, orphan components
  - `test_parameters.py` — path-param naming, parameter identity
  - `test_security.py` — effective-security model, scheme-name local binding
  - `test_schema_changes.py` — constraints, required members
  - `test_line_numbers.py` — line-number resolution
  - `test_defaults.py` — default-value semantics
  - `conftest.py` — the shared `tmp_specs` fixture (used by all files)

## Known limitations (don't regress; fix only with care + tests)

- **Circular `$ref`** → `RecursionError`; **dangling internal `$ref`** →
  `KeyError`. Both are documented in the README and currently unhandled by
  decision. If asked to fix, add cycle detection in `_resolve_refs` and graceful
  handling of missing targets, with driver + guard tests.

## Out of scope (do not add without an explicit request)

- Breaking-change classification or request/response directionality
  (this tool answers symmetric equivalence, not "is this breaking").
- Codegen / SDK-stability concerns.
- `allOf` flattening/merging.
