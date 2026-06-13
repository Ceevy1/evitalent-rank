from __future__ import annotations

from evitalent.official_samples.private_manifest import OfficialDocumentRecord, OfficialManifest


def select_redaction_pilot_documents(manifest: OfficialManifest, domains: list[str]) -> list[OfficialDocumentRecord]:
    selected: list[OfficialDocumentRecord] = []
    for domain in domains:
        candidates = [
            item
            for item in manifest.documents
            if item.folder_domain == domain and item.parser_readable and not item.is_duplicate
        ]
        if candidates:
            selected.append(sorted(candidates, key=lambda item: item.document_id)[0])
    return selected
