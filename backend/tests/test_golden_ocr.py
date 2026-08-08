"""Golden OCR: PP-OCRv6 real sobre corpus `archivos_pruebas/` (lento).

Correr aparte:
  pytest -m slow -o addopts=
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "archivos_pruebas"

# Imágenes de una página (todas menos el PDF).
IMAGE_DOCS = [
    "doc_01.webp",
    "doc_02.webp",
    "doc_03.jpeg",
    "doc_04.jpeg",
    "doc_05.png",
    "doc_06.jpg",
    "doc_08.jpg",
    "doc_09.jpeg",
    "doc_10.jpeg",
    "doc_11.jpeg",
    "doc_12.jpeg",
]
PDF_DOC = "doc_07.pdf"

_MIME = {
    ".webp": "image/webp",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


def _mime_for(name: str) -> str:
    return _MIME.get(Path(name).suffix.lower(), "application/octet-stream")


def _assert_soft_ocr(body: dict) -> None:
    assert body["status"] == "completed"
    assert body["regions_count"] >= 1
    assert body["confidence_avg"] >= 0.3
    texts = [reg["text"].strip() for reg in body["regions"] if reg.get("text", "").strip()]
    assert texts, "se esperaba al menos una región con texto no vacío"
    assert body.get("ocr_tier") == "medium"


@pytest.mark.slow
@pytest.mark.parametrize("filename", IMAGE_DOCS)
def test_golden_image_doc(client: TestClient, filename: str) -> None:
    path = CORPUS / filename
    if not path.is_file():
        pytest.skip(f"Falta fixture {path}")

    up = client.post(
        "/upload",
        files={"file": (filename, path.read_bytes(), _mime_for(filename))},
    )
    assert up.status_code == 200, up.text
    image_id = up.json()["image_id"]

    r = client.post(f"/infer/{image_id}", json={"conf_threshold": 0.9})
    assert r.status_code == 200, r.text
    _assert_soft_ocr(r.json())


@pytest.mark.slow
def test_golden_pdf_first_page(client: TestClient) -> None:
    path = CORPUS / PDF_DOC
    if not path.is_file():
        pytest.skip(f"Falta fixture {path}")

    up = client.post(
        "/upload",
        files={"file": (PDF_DOC, path.read_bytes(), "application/pdf")},
    )
    assert up.status_code == 200, up.text
    body = up.json()
    assert body.get("page_count", 0) >= 1
    assert body.get("pages")
    page_id = body["pages"][0]["image_id"]

    r = client.post(f"/infer/{page_id}", json={"conf_threshold": 0.9})
    assert r.status_code == 200, r.text
    result = r.json()
    _assert_soft_ocr(result)
    assert result.get("source_format") == "pdf"
    assert result.get("page_index") == 0
