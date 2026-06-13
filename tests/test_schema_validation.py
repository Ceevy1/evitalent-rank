from evitalent.extraction.schema_validator import validate_json_file
from evitalent.settings import PROJECT_ROOT


def test_all_fixtures_match_schema():
    for path in sorted((PROJECT_ROOT / "data" / "fixtures" / "extracted").glob("*.json")):
        payload = validate_json_file(path)
        assert payload["candidate_id"]
        assert len(payload["achievement_events"]) >= 2
        assert len(payload["evidence_items"]) >= 3
