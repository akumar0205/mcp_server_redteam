from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mcp_redteam.suite.models import Suite


def load_suite(path: Path) -> Suite:
    if path.is_dir():
        suite_path = path / "suite.yaml"
    else:
        suite_path = path
    if not suite_path.exists():
        raise FileNotFoundError(f"Suite file not found: {suite_path}")
    data = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Suite YAML must be a mapping")
    data.setdefault("name", suite_path.parent.name)
    return Suite.model_validate(data)
