from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from evitalent.settings import PROJECT_ROOT


class SchemaValidationError(ValueError):
    pass


class SchemaValidator:
    def __init__(self, schema_path: str | Path | None = None) -> None:
        self.schema_path = Path(schema_path) if schema_path else PROJECT_ROOT / "schemas" / "candidate_extraction.schema.json"
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema)

    def validate(self, payload: dict[str, Any]) -> list[str]:
        errors = sorted(self.validator.iter_errors(payload), key=lambda error: list(error.path))
        readable: list[str] = []
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            readable.append(f"{path}: {error.message}")
        return readable

    def validate_or_raise(self, payload: dict[str, Any]) -> None:
        errors = self.validate(payload)
        if errors:
            raise SchemaValidationError("; ".join(errors[:8]))

    def validate_file_or_raise(self, path: str | Path) -> dict[str, Any]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.validate_or_raise(payload)
        return payload


def load_schema(schema_name: str = "candidate_extraction.schema.json") -> dict[str, Any]:
    path = PROJECT_ROOT / "schemas" / schema_name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], schema_name: str = "candidate_extraction.schema.json") -> None:
    SchemaValidator(PROJECT_ROOT / "schemas" / schema_name).validate_or_raise(payload)


def validate_json_file(path: str | Path, schema_name: str = "candidate_extraction.schema.json") -> dict[str, Any]:
    return SchemaValidator(PROJECT_ROOT / "schemas" / schema_name).validate_file_or_raise(path)
