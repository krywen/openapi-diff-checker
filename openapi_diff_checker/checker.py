from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

COSMETIC_KEYS = frozenset({
    "description",
    "summary",
    "externalDocs",
    "x-",
})

EXAMPLE_KEYS = frozenset({
    "example",
    "examples",
})

INFO_COSMETIC_KEYS = frozenset({
    "title",
    "version",
    "description",
    "termsOfService",
    "contact",
    "license",
})

DEFAULT_VALUES: dict[str, Any] = {
    "required": False,
    "nullable": False,
    "deprecated": False,
    "allowEmptyValue": False,
    "explode": False,
    "allowReserved": False,
    "readOnly": False,
    "writeOnly": False,
    "exclusiveMinimum": False,
    "exclusiveMaximum": False,
    "additionalProperties": True,
}

SET_SEMANTICS_KEYS = frozenset({
    "required",
    "tags",
    "security",
    "servers",
    "enum",
})


@dataclass
class Difference:
    path: str
    kind: str  # "added", "removed", "changed", "type_changed"
    detail: str
    src_line: int | None = None
    dest_line: int | None = None

    def __str__(self) -> str:
        parts = []
        if self.src_line is not None:
            parts.append(f"src:{self.src_line}")
        if self.dest_line is not None:
            parts.append(f"dest:{self.dest_line}")
        loc = f" ({', '.join(parts)})" if parts else ""
        return f"[{self.kind}] {self.path}{loc}: {self.detail}"


@dataclass
class DiffResult:
    equivalent: bool
    differences: list[Difference] = field(default_factory=list)


def compare(
    src: str | Path,
    dest: str | Path,
) -> DiffResult:
    src_spec = _load(src)
    dest_spec = _load(dest)

    src_lines = _build_line_map(src)
    dest_lines = _build_line_map(dest)

    src_resolved = _resolve_security(_resolve_refs(src_spec, src_spec))
    dest_resolved = _resolve_security(_resolve_refs(dest_spec, dest_spec))
    src_resolved = _strip_orphan_components(src_resolved)
    dest_resolved = _strip_orphan_components(dest_resolved)

    diffs: list[Difference] = []
    _compare_nodes(src_resolved, dest_resolved, "", diffs, src_lines, dest_lines)
    return DiffResult(equivalent=len(diffs) == 0, differences=diffs)


def _load(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _build_line_map(path: str | Path) -> dict[str, int]:
    text = Path(path).read_text(encoding="utf-8")
    root_node = yaml.compose(text, Loader=yaml.SafeLoader)
    if root_node is None:
        return {}
    line_map: dict[str, int] = {}
    _walk_yaml_node(root_node, "", line_map)
    return line_map


def _walk_yaml_node(
    node: yaml.Node,
    path: str,
    line_map: dict[str, int],
) -> None:
    line_map[path] = node.start_mark.line + 1
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            child_path = f"{path}/{key_node.value}"
            _walk_yaml_node(value_node, child_path, line_map)
    elif isinstance(node, yaml.SequenceNode):
        for i, item_node in enumerate(node.value):
            child_path = f"{path}[{i}]"
            _walk_yaml_node(item_node, child_path, line_map)


def _lookup_line(line_map: dict[str, int], path: str) -> int | None:
    if path in line_map:
        return line_map[path]
    p = path
    while p:
        if "[" in p and p.endswith("]"):
            p = p.rsplit("[", 1)[0]
        elif "/" in p:
            p = p.rsplit("/", 1)[0]
        else:
            break
        if p in line_map:
            return line_map[p]
    return line_map.get("", None)


def _make_diff(
    path: str,
    kind: str,
    detail: str,
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> Difference:
    return Difference(
        path=path,
        kind=kind,
        detail=detail,
        src_line=_lookup_line(src_lines, path),
        dest_line=_lookup_line(dest_lines, path),
    )


_CONTAINER_LABELS = {
    "responses": "response",
    "properties": "property",
    "parameters": "parameter",
    "schemas": "schema",
    "requestBodies": "request body",
    "securitySchemes": "security scheme",
    "headers": "header",
    "paths": "path",
}


def _container_label(parent_path: str) -> str | None:
    segment = parent_path.rsplit("/", 1)[-1] if "/" in parent_path else parent_path
    return _CONTAINER_LABELS.get(segment)


def _describe_change(parent_path: str, key: str, value: Any, verb: str) -> str:
    """Build a human-readable detail for an added/removed key.

    Leads with *what* changed (named by its container, e.g. "response '401'")
    rather than dumping the whole subtree, so a newly added response reads as
    a new response and not as a change to whatever field it happens to contain.
    """
    label = _container_label(parent_path)
    subject = f"{label} {key!r}" if label else f"{key!r}"
    if isinstance(value, dict):
        return f"{subject} {verb}"
    if isinstance(value, list):
        return f"{subject} {verb} ({len(value)} item(s))"
    return f"{subject} {verb} (value {value!r})"


_HTTP_METHODS = frozenset({
    "get", "put", "post", "delete", "options", "head", "patch", "trace",
})


def _resolve_security(spec: Any) -> Any:
    """Push the global ``security`` default down onto each operation.

    Decision: the same effective security expressed differently is equivalent.
    A top-level ``security`` is the default for every operation that does not
    declare its own, so we inline it onto those operations and drop the
    top-level key. After this, a spec that declares a requirement globally
    compares equal to one that repeats it per operation.

    An operation that declares its own ``security`` (including an explicit
    empty ``[]``, meaning "public") keeps it untouched.
    """
    if not isinstance(spec, dict):
        return spec

    global_security = spec.get("security")
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return spec

    spec = copy.deepcopy(spec)
    for path_item in spec["paths"].values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            if "security" not in operation and global_security is not None:
                operation["security"] = copy.deepcopy(global_security)

    spec.pop("security", None)
    return spec


def _resolve_refs(node: Any, root: dict) -> Any:
    if isinstance(node, dict):
        if "$ref" in node and len(node) == 1:
            resolved = _follow_ref(node["$ref"], root)
            return _resolve_refs(resolved, root)
        return {k: _resolve_refs(v, root) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, root) for item in node]
    return node


def _follow_ref(ref: str, root: dict) -> Any:
    if not ref.startswith("#/"):
        return {"$ref": ref}
    parts = ref[2:].split("/")
    node = root
    for part in parts:
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    return copy.deepcopy(node)


def _collect_refs(node: Any, refs: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                refs.add(value)
            else:
                _collect_refs(value, refs)
    elif isinstance(node, list):
        for item in node:
            _collect_refs(item, refs)


def _strip_orphan_components(spec: Any) -> Any:
    """Drop component definitions that nothing references.

    Decision: orphan (unreferenced) components do not affect functional
    equivalence. ``_resolve_refs`` inlines every internal ``$ref`` before this
    runs, so any definition left under ``/components`` that is not the target of
    a surviving ``$ref`` describes nothing in the actual API contract. Such
    leftovers are removed before comparison so that, e.g., factoring an enum out
    into a named schema (and referencing it) compares equal to inlining it.

    Components still pointed at by a surviving ``$ref`` (e.g. an unresolved
    external reference) are kept, so genuine differences are never hidden.
    """
    if not isinstance(spec, dict) or not isinstance(spec.get("components"), dict):
        return spec

    refs: set[str] = set()
    _collect_refs(spec, refs)

    spec = copy.deepcopy(spec)
    kept_components: dict[str, Any] = {}
    for group, items in spec["components"].items():
        if not isinstance(items, dict):
            kept_components[group] = items
            continue
        kept = {
            name: defn
            for name, defn in items.items()
            if f"#/components/{group}/{name}" in refs
        }
        if kept:
            kept_components[group] = kept

    if kept_components:
        spec["components"] = kept_components
    else:
        del spec["components"]
    return spec


def _is_cosmetic(key: str) -> bool:
    if key in COSMETIC_KEYS:
        return True
    if key.startswith("x-"):
        return True
    return False


def _is_info_cosmetic(key: str) -> bool:
    return key in INFO_COSMETIC_KEYS


def _compare_nodes(
    src: Any,
    dest: Any,
    path: str,
    diffs: list[Difference],
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> None:
    if type(src) is not type(dest):
        diffs.append(_make_diff(
            path or "/", "type_changed",
            f"{type(src).__name__} -> {type(dest).__name__}",
            src_lines, dest_lines,
        ))
        return

    if isinstance(src, dict):
        _compare_dicts(src, dest, path, diffs, src_lines, dest_lines)
    elif isinstance(src, list):
        _compare_lists(src, dest, path, diffs, src_lines, dest_lines)
    elif src != dest:
        diffs.append(_make_diff(
            path or "/", "changed",
            f"{src!r} -> {dest!r}",
            src_lines, dest_lines,
        ))


def _normalize_keys(d: dict) -> dict[str, Any]:
    return {str(k): v for k, v in d.items()}


def _compare_dicts(
    src: dict,
    dest: dict,
    path: str,
    diffs: list[Difference],
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> None:
    src = _normalize_keys(src)
    dest = _normalize_keys(dest)
    is_info = path == "/info"

    all_keys = set(src) | set(dest)
    for key in sorted(all_keys):
        if _is_cosmetic(key):
            continue
        if is_info and _is_info_cosmetic(key):
            continue

        child_path = f"{path}/{key}"

        if key not in dest:
            if key in DEFAULT_VALUES and src[key] == DEFAULT_VALUES[key]:
                continue
            diffs.append(_make_diff(
                child_path, "removed",
                _describe_change(path, key, src[key], "removed"),
                src_lines, dest_lines,
            ))
        elif key not in src:
            if key in DEFAULT_VALUES and dest[key] == DEFAULT_VALUES[key]:
                continue
            diffs.append(_make_diff(
                child_path, "added",
                _describe_change(path, key, dest[key], "added"),
                src_lines, dest_lines,
            ))
        elif key in EXAMPLE_KEYS:
            _compare_example(src[key], dest[key], child_path, diffs,
                             src_lines, dest_lines)
        else:
            _compare_nodes(src[key], dest[key], child_path, diffs,
                           src_lines, dest_lines)


def _compare_lists(
    src: list,
    dest: list,
    path: str,
    diffs: list[Difference],
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> None:
    parent_key = path.rsplit("/", 1)[-1] if "/" in path else ""

    if parent_key in SET_SEMANTICS_KEYS:
        _compare_as_sets(src, dest, path, diffs, src_lines, dest_lines)
        return

    if len(src) != len(dest):
        diffs.append(_make_diff(
            path, "changed",
            f"array length {len(src)} -> {len(dest)}",
            src_lines, dest_lines,
        ))
        return

    for i, (s, d) in enumerate(zip(src, dest)):
        _compare_nodes(s, d, f"{path}[{i}]", diffs, src_lines, dest_lines)


def _compare_as_sets(
    src: list,
    dest: list,
    path: str,
    diffs: list[Difference],
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> None:
    src_hashable = all(_is_hashable(item) for item in src)
    dest_hashable = all(_is_hashable(item) for item in dest)

    if src_hashable and dest_hashable:
        src_set = set(_make_hashable(item) for item in src)
        dest_set = set(_make_hashable(item) for item in dest)
        for item in sorted(src_set - dest_set, key=str):
            diffs.append(_make_diff(
                path, "removed", f"{item!r} removed",
                src_lines, dest_lines,
            ))
        for item in sorted(dest_set - src_set, key=str):
            diffs.append(_make_diff(
                path, "added", f"{item!r} added",
                src_lines, dest_lines,
            ))
    else:
        src_normalized = sorted(src, key=_sort_key)
        dest_normalized = sorted(dest, key=_sort_key)
        if len(src_normalized) != len(dest_normalized):
            diffs.append(_make_diff(
                path, "changed",
                f"set-like array length {len(src)} -> {len(dest)}",
                src_lines, dest_lines,
            ))
            return
        for i, (s, d) in enumerate(zip(src_normalized, dest_normalized)):
            _compare_nodes(s, d, f"{path}[{i}]", diffs, src_lines, dest_lines)


def _is_hashable(value: Any) -> bool:
    if isinstance(value, (dict, list)):
        return False
    return True


def _make_hashable(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_make_hashable(item) for item in value)
    return value


def _sort_key(value: Any) -> str:
    if isinstance(value, dict):
        return str(sorted(value.items()))
    return str(value)


def _compare_example(
    src: Any,
    dest: Any,
    path: str,
    diffs: list[Difference],
    src_lines: dict[str, int],
    dest_lines: dict[str, int],
) -> None:
    if type(src) is not type(dest):
        diffs.append(_make_diff(
            path, "type_changed",
            f"{type(src).__name__} -> {type(dest).__name__}",
            src_lines, dest_lines,
        ))
