"""Fixtures compartidos: app FastAPI sin lifespan, store aislado, OCR mockeado."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.routes import register_routes
from app import storage
from app import routes as routes_mod


# PDF mínimo válido (1 página) que pypdfium2 puede rasterizar.
MINIMAL_PDF_1PAGE = (
    b"%PDF-1.4\n"
    b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
    b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
    b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] >>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<< /Size 4 /Root 1 0 R >>\n"
    b"startxref\n190\n%%EOF\n"
)


def png_bytes(color: tuple[int, int, int] = (240, 240, 240), size: tuple[int, int] = (32, 32)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def tiff_bytes(page_count: int = 2) -> bytes:
    frames = [Image.new("RGB", (24, 24), (200 + i * 10, 200, 200)) for i in range(page_count)]
    buf = BytesIO()
    frames[0].save(
        buf,
        format="TIFF",
        save_all=True,
        append_images=frames[1:],
    )
    return buf.getvalue()


def fake_paddle_lines() -> tuple[list, list[int]]:
    poly = [[1.0, 2.0], [40.0, 2.0], [40.0, 18.0], [1.0, 18.0]]
    return [(poly, ("hello", 0.95))], [0]


@pytest.fixture()
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    upload = tmp_path / "uploads"
    annotated = upload / "annotated"
    upload.mkdir()
    annotated.mkdir()

    monkeypatch.setattr(storage, "UPLOAD_DIR", upload)
    monkeypatch.setattr(storage, "ANNOTATED_DIR", annotated)
    monkeypatch.setattr(routes_mod, "ANNOTATED_DIR", annotated)
    storage.store.clear()

    test_app = FastAPI(title="LexOCR-test")
    register_routes(test_app)
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def mock_ocr(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Mockea _run_paddle y rescue; expone calls para asserts."""
    paddle = MagicMock(side_effect=lambda path, options=None: fake_paddle_lines())
    rescue_calls: list[dict[str, Any]] = []

    def _rescue(path: str, lines: list, textline_angles: list[int]):
        rescue_calls.append({"path": path, "n_lines": len(lines)})
        orients = [0.0] * len(lines)
        return lines, orients

    rescue = MagicMock(side_effect=_rescue)
    monkeypatch.setattr(routes_mod, "_run_paddle", paddle)
    monkeypatch.setattr(routes_mod, "_rescue_oriented_lines", rescue)
    return {"paddle": paddle, "rescue": rescue, "rescue_calls": rescue_calls}


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    storage.store.clear()
    yield
    storage.store.clear()
