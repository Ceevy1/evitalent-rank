def test_upload_parse_and_redact_demo_docx():
    from fastapi.testclient import TestClient
    from evitalent.api.main import app
    from scripts.generate_demo_resume_files import OUTPUT_DIR, main as generate_demo_files

    generate_demo_files()
    path = OUTPUT_DIR / "demo_hr_resume.docx"
    client = TestClient(app)
    with path.open("rb") as f:
        upload = client.post("/api/v1/resumes/upload", files={"file": ("demo_hr_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    parsed = client.post(f"/api/v1/resumes/{document_id}/parse")
    assert parsed.status_code == 200
    payload = parsed.json()
    assert payload["parse_status"] == "success"
    text = str(payload)
    assert "13900001234" not in text
    assert "28K" not in text
    assert "陆晨" not in text
    assert "[电话已脱敏]" in payload["redacted_preview"]
