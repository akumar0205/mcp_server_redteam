from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    name: str
    prompt: str
    policy: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Suite(BaseModel):
    name: str
    description: Optional[str] = None
    tests: list[TestCase]
