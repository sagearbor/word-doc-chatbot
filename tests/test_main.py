try:
    from fastapi.testclient import TestClient
    from backend.main import app
except ModuleNotFoundError:
    TestClient = None
    app = None

import pytest

client = TestClient(app) if TestClient and app else None


@pytest.mark.skipif(client is None, reason="FastAPI is not installed")
def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}


@pytest.mark.skipif(client is None, reason="FastAPI is not installed")
def test_process_document_endpoint(tmp_path, monkeypatch):
    from docx import Document
    from backend import llm_handler

    doc = Document()
    doc.add_paragraph("Hello World")
    doc_path = tmp_path / "test.docx"
    doc.save(doc_path)

    monkeypatch.setattr(llm_handler, "get_llm_suggestions", lambda *a, **k: [])

    with open(doc_path, "rb") as f:
        response = client.post(
            "/process-document/",
            files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={
                "instructions": "none",
                "author_name": "",
                "case_sensitive": "true",
                "add_comments": "true",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
