from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationError


class AuthType(str, Enum):
    none = "none"
    bearer = "bearer"


class AuthConfig(BaseModel):
    type: AuthType = AuthType.none
    token_env: Optional[str] = None


class EndpointConfig(BaseModel):
    name: str
    base_url: HttpUrl
    auth: AuthConfig = Field(default_factory=AuthConfig)


class EndpointsFile(BaseModel):
    endpoints: list[EndpointConfig]


class TargetConfig(BaseModel):
    base_url: HttpUrl
    auth: AuthConfig = Field(default_factory=AuthConfig)


def load_json_config(path: Path, model: type[BaseModel]) -> BaseModel:
    data = path.read_text(encoding="utf-8")
    try:
        return model.model_validate_json(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid config at {path}: {exc}") from exc


def auth_headers(auth: AuthConfig) -> dict[str, str]:
    if auth.type == AuthType.bearer:
        if not auth.token_env:
            return {}
        import os

        value = os.environ.get(auth.token_env)
        if value:
            return {"Authorization": f"Bearer {value}"}
        return {}
    return {}


def is_localhost(url: str) -> bool:
    return url.startswith("http://127.0.0.1") or url.startswith("http://localhost")
