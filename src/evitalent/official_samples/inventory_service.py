from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from evitalent.official_samples.private_manifest import (
    OfficialDocumentRecord,
    OfficialManifest,
    anonymous_document_id,
    save_private_manifest,
    sha256_file,
    write_json,
)
from evitalent.official_samples.settings import OfficialSampleSettings
from evitalent.parser.docx_parser import DocxDocumentParser


class OfficialInventoryService:
    def __init__(self, settings: OfficialSampleSettings, parser: DocxDocumentParser | None = None) -> None:
        self.settings = settings
        self.parser = parser or DocxDocumentParser()

    def scan(self) -> OfficialManifest:
        records: list[OfficialDocumentRecord] = []
        for domain in self.settings.domains:
            domain_dir = self.settings.resume_input_root / domain
            if not domain_dir.exists():
                continue
            for path in sorted(domain_dir.iterdir(), key=lambda item: item.name.lower()):
                if not path.is_file() or path.suffix.lower() not in self.settings.allowed_extensions:
                    continue
                sha = sha256_file(path)
                readable, warning = self._readability(path)
                records.append(
                    OfficialDocumentRecord(
                        document_id=anonymous_document_id(domain, sha),
                        folder_domain=domain,
                        private_relative_path=str(path.relative_to(self.settings.resume_input_root)),
                        original_filename=path.name,
                        sha256=sha,
                        file_size_bytes=path.stat().st_size,
                        parser_readable=readable,
                        parse_warning=warning,
                    )
                )
        self._mark_duplicates(records)
        return OfficialManifest(version=self.settings.version, input_root=str(self.settings.resume_input_root), documents=records)

    def save_outputs(self, manifest: OfficialManifest) -> dict[str, list[dict] | str]:
        save_private_manifest(manifest, self.settings.raw_manifest_path)
        summary = build_inventory_safe_summary(manifest, self.settings.domains)
        write_json(self.settings.inventory_safe_summary_path, summary)
        return {"private_manifest_path": str(self.settings.raw_manifest_path), "safe_summary": summary}

    def _readability(self, path: Path) -> tuple[bool, str | None]:
        try:
            parsed = self.parser.parse(path)
        except Exception as exc:
            return False, type(exc).__name__
        if not parsed.cleaned_text.strip():
            return False, "; ".join(parsed.warnings) or "empty_text"
        return True, "; ".join(parsed.warnings) if parsed.warnings else None

    @staticmethod
    def _mark_duplicates(records: list[OfficialDocumentRecord]) -> None:
        by_domain_sha: dict[tuple[str, str], int] = Counter((item.folder_domain, item.sha256) for item in records)
        domains_by_sha: dict[str, set[str]] = defaultdict(set)
        for item in records:
            domains_by_sha[item.sha256].add(item.folder_domain)
        for item in records:
            item.duplicate_within_domain = by_domain_sha[(item.folder_domain, item.sha256)] > 1
            item.duplicate_across_domains = len(domains_by_sha[item.sha256]) > 1


def build_inventory_safe_summary(manifest: OfficialManifest, domains: list[str]) -> list[dict]:
    rows: list[dict] = []
    for domain in domains:
        docs = [item for item in manifest.documents if item.folder_domain == domain]
        rows.append(
            {
                "domain": domain,
                "document_count": len(docs),
                "readable_count": sum(1 for item in docs if item.parser_readable),
                "unreadable_count": sum(1 for item in docs if not item.parser_readable),
                "duplicate_count": sum(1 for item in docs if item.is_duplicate),
                "total_file_size_bytes": sum(item.file_size_bytes for item in docs),
            }
        )
    return rows
