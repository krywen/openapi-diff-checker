from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_specs(tmp_path):
    def _write(src_yaml: str, dest_yaml: str) -> tuple[Path, Path]:
        src = tmp_path / "src.yaml"
        dest = tmp_path / "dest.yaml"
        src.write_text(textwrap.dedent(src_yaml))
        dest.write_text(textwrap.dedent(dest_yaml))
        return src, dest
    return _write
