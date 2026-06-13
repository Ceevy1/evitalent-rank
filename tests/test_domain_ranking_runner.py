from __future__ import annotations

import json

from evitalent.official_samples.batch_state_store import COMPLETED_ELIGIBLE, FAILED_GROUNDING, BatchStateStore
from evitalent.official_samples.domain_ranking_runner import DomainRankingRunner
from evitalent.official_samples.private_manifest import write_json
from evitalent.official_samples.settings import load_official_sample_settings
from evitalent.settings import PROJECT_ROOT
from official_samples_test_utils import DOMAINS, make_private_tree


def test_domain_ranking_runner_only_eligible_and_safe(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    fixture = json.loads((PROJECT_ROOT / "data" / "fixtures" / "extracted" / "demo_hr_001.json").read_text(encoding="utf-8"))
    state = {"documents": {}}
    for domain in DOMAINS:
        doc_id = f"{domain}_doc"
        payload = dict(fixture)
        payload["document_id"] = doc_id
        payload["candidate_id"] = doc_id
        result_path = settings.batch_output_dir / "extraction_results_private" / domain / f"{doc_id}.json"
        write_json(result_path, {"candidate_extraction": payload})
        state["documents"][doc_id] = {"document_id": doc_id, "domain": domain, "status": COMPLETED_ELIGIBLE, "result_path": str(result_path)}
    state["documents"]["hr_failed"] = {"document_id": "hr_failed", "domain": "hr", "status": FAILED_GROUNDING}
    BatchStateStore(settings.batch_state_path).save(state)

    result = DomainRankingRunner(settings).run()
    assert set(result["domains"]) == set(DOMAINS)
    assert result["domains"]["hr"]["candidate_count"] == 1
    text = (settings.rankings_dir / "all_domains_safe_summary.json").read_text(encoding="utf-8")
    assert "sample.docx" not in text
    assert "姓名" not in text
    assert (settings.private_data_root / "config" / "domain_weights.yaml").exists() is False
