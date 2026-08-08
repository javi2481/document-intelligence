"""Unitarios de PNG anotado (sin OCR)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.annotate import _poly_points, render_annotated_from_result


def test_poly_points() -> None:
    assert _poly_points([[1, 2], [3, 4]]) == [(1.0, 2.0), (3.0, 4.0)]
    assert _poly_points(None) == []
    assert _poly_points("x") == []


def test_render_annotated_empty_regions(tmp_path: Path) -> None:
    src = tmp_path / "in.png"
    Image.new("RGB", (40, 30), (255, 255, 255)).save(src)
    out = tmp_path / "out.png"
    render_annotated_from_result(src, {"regions": []}, out)
    assert out.exists()
    with Image.open(out) as img:
        assert img.size == (40, 30)
        assert img.format == "PNG"


def test_render_annotated_with_poly_and_bbox(tmp_path: Path) -> None:
    src = tmp_path / "in.png"
    Image.new("RGB", (80, 60), (240, 240, 240)).save(src)
    out = tmp_path / "annotated.png"
    result = {
        "regions": [
            {
                "id": 0,
                "confidence": 0.95,
                "poly": [[5, 5], [40, 5], [40, 25], [5, 25]],
                "bbox": {"x": 5, "y": 5, "width": 35, "height": 20},
                "text": "hi",
            },
            {
                "id": 1,
                "confidence": 0.7,
                "poly": [],
                "bbox": {"x": 50, "y": 10, "width": 20, "height": 15},
                "text": "box",
            },
        ],
    }
    render_annotated_from_result(src, result, out)
    assert out.exists()
    assert out.stat().st_size > 0
    with Image.open(out) as img:
        assert img.size == (80, 60)
