from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.generate_demo_resume_files import main as generate_demo_files

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates
from evitalent.services.document_service import DocumentService
from evitalent.services.extraction_service import ExtractionService, ExtractionServiceError
from evitalent.settings import get_settings


def main() -> None:
    generate_demo_files()
    docx_path = ROOT / "data" / "fixtures" / "source_documents" / "demo_hr_resume.docx"
    service = DocumentService()
    saved = service.save_upload_bytes(docx_path.name, docx_path.read_bytes())
    parsed = service.parse_and_redact(saved["document_id"])
    print(f"redaction_completed={parsed['redaction_completed']}")

    settings = get_settings()
    mode = settings.llm_provider if settings.llm_provider in {"local_ollama", "compatible_api"} else "mock"
    if mode == "mock":
        print("no configured local_ollama/compatible_api model; using mock fixture safely")
        candidate = MockExtractor().extract("demo_hr_001")
    else:
        try:
            summary = ExtractionService().extract_document(saved["document_id"], mode)
            candidate = ExtractionService.load_extracted_candidate(ROOT / "data" / "extracted" / f"{summary['candidate_id']}.json")
        except ExtractionServiceError as exc:
            print(f"llm_extraction_failed={exc}")
            print("fallback=mock")
            candidate = MockExtractor().extract("demo_hr_001")

    domain = candidate.candidate_profile.target_domain_candidates[0].domain
    result = rank_candidates([candidate], domain, ranking_id="llm_demo_safe")
    item = result.candidates[0]
    print(f"candidate_id={candidate.candidate_id}")
    print(f"domain={domain}")
    print(f"achievement_count={len(candidate.achievement_events)}")
    print(f"evidence_count={len(candidate.evidence_items)}")
    print(f"rank_score={item.rank_score}")
    print("privacy=only redacted text is eligible for model input")


if __name__ == "__main__":
    main()
