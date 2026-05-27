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
    "description",
    "termsOfService",
    "contact",
    "license",
})

SET_SEMANTICS_KEYS = frozenset({
    "required",
    "tags",
    "security",
    "servers",
})


@dataclass
class Difference:
    path: str
    kind: str  # "added", "removed", "changed", "type_changed"
    detail: str

    def __str__(self) -> str:
        return f"[{self.kind}] {self.path}: {self.detail}"


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

    src_resolved = _resolve_refs(src_spec, src_spec)
    dest_resolved = _resolve_refs(dest_spec, dest_spec)

    diffs: list[Difference] = []
    _compare_nodes(src_resolved, dest_resolved, "", diffs)
    return DiffResult(equivalent=len(diffs) == 0, differences=diffs)


def _load(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return yaml.safe_load(text)


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
) -> None:
    if type(src) is not type(dest):
        diffs.append(Difference(
            path=path or "/",
            kind="type_changed",
            detail=f"{type(src).__name__} -> {type(dest).__name__}",
        ))
        return

    if isinstance(src, dict):
        _compare_dicts(src, dest, path, diffs)
    elif isinstance(src, list):
        _compare_lists(src, dest, path, diffs)
    elif src != dest:
        diffs.append(Difference(
            path=path or "/",
            kind="changed",
            detail=f"{src!r} -> {dest!r}",
        ))


def _compare_dicts(
    src: dict,
    dest: dict,
    path: str,
    diffs: list[Difference],
) -> None:
    is_info = path == "/info"

    all_keys = set(src) | set(dest)
    for key in sorted(all_keys):
        if _is_cosmetic(key):
            continue
        if is_info and _is_info_cosmetic(key):
            continue

        child_path = f"{path}/{key}"

        if key not in dest:
            diffs.append(Difference(
                path=child_path,
                kind="removed",
                detail=f"value {src[key]!r} removed",
            ))
        elif key not in src:
            diffs.append(Difference(
                path=child_path,
                kind="added",
                detail=f"value {dest[key]!r} added",
            ))
        elif key in EXAMPLE_KEYS:
            _compare_example(src[key], dest[key], child_path, diffs)
        else:
            _compare_nodes(src[key], dest[key], child_path, diffs)


def _compare_lists(
    src: list,
    dest: list,
    path: str,
    diffs: list[Difference],
) -> None:
    parent_key = path.rsplit("/", 1)[-1] if "/" in path else ""

    if parent_key in SET_SEMANTICS_KEYS:
        _compare_as_sets(src, dest, path, diffs)
        return

    if len(src) != len(dest):
        diffs.append(Difference(
            path=path,
            kind="changed",
            detail=f"array length {len(src)} -> {len(dest)}",
        ))
        return

    for i, (s, d) in enumerate(zip(src, dest)):
        _compare_nodes(s, d, f"{path}[{i}]", diffs)


def _compare_as_sets(
    src: list,
    dest: list,
    path: str,
    diffs: list[Difference],
) -> None:
    src_hashable = all(_is_hashable(item) for item in src)
    dest_hashable = all(_is_hashable(item) for item in dest)

    if src_hashable and dest_hashable:
        src_set = set(_make_hashable(item) for item in src)
        dest_set = set(_make_hashable(item) for item in dest)
        for item in sorted(src_set - dest_set, key=str):
            diffs.append(Difference(
                path=path,
                kind="removed",
                detail=f"{item!r} removed",
            ))
        for item in sorted(dest_set - src_set, key=str):
            diffs.append(Difference(
                path=path,
                kind="added",
                detail=f"{item!r} added",
            ))
    else:
        src_normalized = sorted(src, key=_sort_key)
        dest_normalized = sorted(dest, key=_sort_key)
        if len(src_normalized) != len(dest_normalized):
            diffs.append(Difference(
                path=path,
                kind="changed",
                detail=f"set-like array length {len(src)} -> {len(dest)}",
            ))
            return
        for i, (s, d) in enumerate(zip(src_normalized, dest_normalized)):
            _compare_nodes(s, d, f"{path}[{i}]", diffs)


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
) -> None:
    if type(src) is not type(dest):
        diffs.append(Difference(
            path=path,
            kind="type_changed",
            detail=f"{type(src).__name__} -> {type(dest).__name__}",
        ))
