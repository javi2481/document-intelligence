"""Golden OCR: PP-OCRv6 real sobre corpus manual (lento).

Correr aparte:
  pytest -m slow -o addopts=
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_01 = REPO_ROOT / "archivos_pruebas" / "doc_01.webp"


@pytest.mark.slow
def test_golden_doc_01_infer(client: TestClient) -> None:
    """Soft golden: hay texto y confianza usable (sin assert de string frágil)."""
    if not DOC_01.is_file():
        pytest.skip(f"Falta fixture {DOC_01}")

    data = DOC_01.read_bytes()
    up = client.post(
        "/upload",
        files={"file": ("doc_01.webp", data, "image/webp")},
    )
    assert up.status_code == 200, up.text
    image_id = up.json()["image_id"]

    # OCR real: puede tardar minutos la primera vez (carga de modelos).
    r = client.post(f"/infer/{image_id}", json={"conf_threshold": 0.9})
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["status"] == "completed"
    assert body["regions_count"] >= 1
    assert body["confidence_avg"] >= 0.3
    texts = [reg["text"].strip() for reg in body["regions"] if reg.get("text", "").strip()]
    assert texts, "se esperaba al menos una región con texto no vacío"
    assert body.get("ocr_tier") == "medium"
