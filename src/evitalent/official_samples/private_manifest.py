from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OfficialDocumentRecord:
    document_id: str
    folder_domain: str
    private_relative_path: str
    original_filename: str
    sha256: str
    file_size_bytes: int
    parser_readable: bool
    parse_warning: str | None = None
    duplicate_within_domain: bool = False
    duplicate_across_domains: bool = False

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_within_domain or self.duplicate_across_domains


@dataclass
class OfficialManifest:
    version: str
    input_root: str
    documents: list[OfficialDocumentRecord] = field(default_factory=list)

    def to_private_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "input_root": self.input_root,
            "documents": [asdict(item) for item in self.documents],
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def anonymous_document_id(folder_domain: str, sha256: str, prefix_length: int = 10) -> str:
    return f"{folder_domain}_{sha256[:prefix_length]}"


def save_private_manifest(manifest: OfficialManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_private_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_private_manifest(path: Path) -> OfficialManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return OfficialManifest(
        version=payload.get("version", "1.0.0"),
        input_root=payload["input_root"],
        documents=[OfficialDocumentRecord(**item) for item in payload.get("documents", [])],
    )


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
