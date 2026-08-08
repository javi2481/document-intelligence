"""Tests de API: upload, límites, infer (OCR mock), status, annotated."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import routes as routes_mod
from app import storage
from tests.conftest import MINIMAL_PDF_1PAGE, png_bytes, tiff_bytes


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "device" in body
    assert "cuda_compiled" in body


def test_upload_png(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_format"] == "png"
    assert len(body["pages"]) == 1
    assert body["pages"][0]["status"] == "pending"
    assert body["pages"][0]["page_index"] == 0
    assert body["pages"][0]["page_count"] == 1
    assert body["image_id"] in storage.store
    assert storage.store[body["image_id"]]["status"] == "pending"


def test_upload_tiff_multipage(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("doc.tiff", tiff_bytes(2), "image/tiff")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_format"] == "tiff"
    assert body["page_count"] == 2
    assert len(body["pages"]) == 2
    assert body["pages"][0]["page_index"] == 0
    assert body["pages"][1]["page_index"] == 1
    assert all(p["status"] == "pending" for p in body["pages"])
    assert " · p.1/2" in body["pages"][0]["filename"]
    assert " · p.2/2" in body["pages"][1]["filename"]


def test_upload_pdf(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("one.pdf", MINIMAL_PDF_1PAGE, "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_format"] == "pdf"
    assert body["page_count"] == 1
    assert len(body["pages"]) == 1
    assert body["pages"][0]["status"] == "pending"
    assert body["pages"][0]["source_format"] == "pdf"


def test_upload_rejects_over_20mb(client: TestClient) -> None:
    huge = b"\x89PNG\r\n\x1a\n" + b"x" * (20 * 1024 * 1024 + 1)
    r = client.post(
        "/upload",
        files={"file": ("big.png", huge, "image/png")},
    )
    assert r.status_code == 400
    assert "20MB" in r.json()["detail"]


def test_upload_rejects_over_max_pages(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routes_mod, "_tiff_frame_count", lambda path: 51)
    r = client.post(
        "/upload",
        files={"file": ("many.tiff", tiff_bytes(2), "image/tiff")},
    )
    assert r.status_code == 400
    assert "50" in r.json()["detail"]


def test_upload_rejects_garbage(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("x.bin", b"not-an-image", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_infer_image_calls_rescue(client: TestClient, mock_ocr: dict) -> None:
    up = client.post(
        "/upload",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )
    image_id = up.json()["image_id"]

    r = client.post(f"/infer/{image_id}", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["regions_count"] == 1
    assert body["regions"][0]["text"] == "hello"
    assert body["ocr_tier"] == "medium"
    mock_ocr["paddle"].assert_called_once()
    mock_ocr["rescue"].assert_called_once()
    assert storage.store[image_id]["status"] == "completed"


def test_infer_pdf_page_skips_rescue(client: TestClient, mock_ocr: dict) -> None:
    up = client.post(
        "/upload",
        files={"file": ("one.pdf", MINIMAL_PDF_1PAGE, "application/pdf")},
    )
    page_id = up.json()["pages"][0]["image_id"]

    r = client.post(f"/infer/{page_id}", json={})
    assert r.status_code == 200
    assert r.json()["source_format"] == "pdf"
    mock_ocr["paddle"].assert_called_once()
    mock_ocr["rescue"].assert_not_called()


def test_infer_tiff_page_skips_rescue(client: TestClient, mock_ocr: dict) -> None:
    up = client.post(
        "/upload",
        files={"file": ("doc.tiff", tiff_bytes(2), "image/tiff")},
    )
    page_id = up.json()["pages"][0]["image_id"]

    r = client.post(f"/infer/{page_id}", json={})
    assert r.status_code == 200
    assert r.json()["source_format"] == "tiff"
    mock_ocr["rescue"].assert_not_called()


def test_infer_unknown_id(client: TestClient, mock_ocr: dict) -> None:
    r = client.post("/infer/does-not-exist", json={})
    assert r.status_code == 404


def test_infer_rejects_document_source(client: TestClient, mock_ocr: dict) -> None:
    up = client.post(
        "/upload",
        files={"file": ("doc.tiff", tiff_bytes(2), "image/tiff")},
    )
    # El parent_id queda en store con is_document_source; el image_id de respuesta
    # es la primera página. Buscamos el entry documento.
    parent_ids = [
        iid for iid, item in storage.store.items() if item.get("is_document_source")
    ]
    assert parent_ids
    r = client.post(f"/infer/{parent_ids[0]}", json={})
    assert r.status_code == 400


def test_status_pending_then_completed(client: TestClient, mock_ocr: dict) -> None:
    up = client.post(
        "/upload",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )
    image_id = up.json()["image_id"]

    st = client.get(f"/status/{image_id}")
    assert st.status_code == 200
    assert st.json()["status"] == "pending"

    client.post(f"/infer/{image_id}", json={})
    st2 = client.get(f"/status/{image_id}")
    assert st2.json()["status"] == "completed"


def test_export_annotated_without_result(client: TestClient) -> None:
    up = client.post(
        "/upload",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )
    image_id = up.json()["image_id"]
    r = client.get(f"/export/{image_id}/annotated")
    assert r.status_code == 400
    assert "Sin resultado" in r.json()["detail"]


def test_export_annotated_ok(
    client: TestClient,
    mock_ocr: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    up = client.post(
        "/upload",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )
    image_id = up.json()["image_id"]
    client.post(f"/infer/{image_id}", json={})

    def fake_render(src: Path, result: dict, out: Path) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(png_bytes((10, 20, 30)))
        return out

    monkeypatch.setattr(routes_mod, "render_annotated_from_result", fake_render)
    r = client.get(f"/export/{image_id}/annotated")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
