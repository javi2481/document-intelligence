"""Tests unitarios de storage / helpers de rutas."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routes import _page_filename
from app.storage import _detect_format
from tests.conftest import MINIMAL_PDF_1PAGE, png_bytes, tiff_bytes


def test_detect_format_png() -> None:
    assert _detect_format(png_bytes(), "x.png", "image/png") == "png"


def test_detect_format_jpeg_magic() -> None:
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert _detect_format(data, "photo.jpg", "image/jpeg") == "jpeg"


def test_detect_format_pdf() -> None:
    assert _detect_format(MINIMAL_PDF_1PAGE, "a.pdf", "application/pdf") == "pdf"


def test_detect_format_tiff() -> None:
    assert _detect_format(tiff_bytes(1), "a.tiff", "image/tiff") == "tiff"


def test_detect_format_unsupported() -> None:
    with pytest.raises(HTTPException) as ei:
        _detect_format(b"????", "x.xyz", "application/octet-stream")
    assert ei.value.status_code == 400


def test_page_filename() -> None:
    assert _page_filename("informe.pdf", 0, 3) == "informe · p.1/3"
    assert _page_filename("informe.pdf", 2, 3) == "informe · p.3/3"
    assert _page_filename("sin_ext", 0, 1) == "sin_ext · p.1/1"
