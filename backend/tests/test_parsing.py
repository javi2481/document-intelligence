"""Unitarios de parsing (sin Paddle)."""

from __future__ import annotations

from app.parsing import (
    _build_result,
    _normalize_poly,
    _parse_paddle_raw,
    _polygon_to_bbox,
)
from app.schemas import InferOptions


def test_normalize_poly_points() -> None:
    poly = [[1.234, 2.345], [10, 2], [10, 8.9], [1, 9]]
    assert _normalize_poly(poly) == [
        [1.23, 2.35],
        [10.0, 2.0],
        [10.0, 8.9],
        [1.0, 9.0],
    ]


def test_normalize_poly_flat() -> None:
    assert _normalize_poly([0, 0, 10, 0, 10, 5, 0, 5]) == [
        [0.0, 0.0],
        [10.0, 0.0],
        [10.0, 5.0],
        [0.0, 5.0],
    ]


def test_normalize_poly_empty() -> None:
    assert _normalize_poly(None) == []
    assert _normalize_poly([]) == []


def test_polygon_to_bbox() -> None:
    bbox = _polygon_to_bbox([[10, 20], [40, 20], [40, 50], [10, 50]])
    assert bbox == {"x": 10.0, "y": 20.0, "width": 30.0, "height": 30.0}


def test_parse_paddle_raw_empty() -> None:
    assert _parse_paddle_raw(None) == ([], [])
    assert _parse_paddle_raw([]) == ([], [])


def test_parse_paddle_raw_dt_polys_master() -> None:
    page = {
        "dt_polys": [
            [[0, 0], [10, 0], [10, 5], [0, 5]],
            [[0, 10], [20, 10], [20, 18], [0, 18]],
        ],
        "rec_texts": ["hi"],
        "rec_scores": [0.91],
        "textline_orientation_angles": [0, 180],
    }
    lines, angles = _parse_paddle_raw([page])
    assert len(lines) == 2
    assert lines[0][1] == ("hi", 0.91)
    assert lines[1][1] == ("", 0.0)  # det sin rec
    assert angles == [0, 180]


def test_build_result_regions_and_metrics() -> None:
    poly = [[0, 0], [20, 0], [20, 10], [0, 10]]
    lines = [
        (poly, ("alpha", 0.95)),
        (poly, ("beta", 0.80)),
    ]
    item = {
        "filename": "a.png",
        "page_index": 1,
        "page_count": 3,
        "source_format": "pdf",
    }
    result = _build_result(
        "id-1",
        item,
        lines,
        elapsed=12.5,
        width=100,
        height=80,
        options=InferOptions(conf_threshold=0.9),
        orientations=[0.0, -90.0],
    )
    assert result.image_id == "id-1"
    assert result.regions_count == 2
    assert result.low_confidence_count == 1
    assert result.confidence_avg == 0.875
    assert result.regions[1].orientation == -90.0
    assert result.page_index == 1
    assert result.page_count == 3
    assert result.source_format == "pdf"
    assert result.ocr_tier == "medium"
