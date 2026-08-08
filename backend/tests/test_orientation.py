"""Unitarios de helpers de orientation (sin recognizer / OpenCV de rescue completo)."""

from __future__ import annotations

from app.orientation import (
    DIAGONAL_ANGLES,
    SWEEP_DELTAS,
    _dedupe_angles,
    _is_diagonal,
    _normalize_text_angle,
    _rescue_candidate_angles,
)


def test_normalize_text_angle() -> None:
    assert _normalize_text_angle(0) == 0.0
    assert _normalize_text_angle(90) == 90.0
    # En Python (-90) % 180 == 90 → normaliza a 90.
    assert _normalize_text_angle(-90) == 90.0
    assert _normalize_text_angle(180.0) == 0.0
    assert _normalize_text_angle(135.0) == -45.0
    assert _normalize_text_angle(-135.0) == 45.0


def test_is_diagonal() -> None:
    assert _is_diagonal(0) is False
    assert _is_diagonal(90) is False
    assert _is_diagonal(-90) is False
    assert _is_diagonal(45) is True
    assert _is_diagonal(-30) is True
    assert _is_diagonal(10) is False  # dentro de _AXIS_EPS=15


def test_dedupe_angles() -> None:
    assert _dedupe_angles([90.0, 90.04, -90.0, 90.0]) == [90.0, -90.0]


def test_rescue_candidate_vertical_paddle_ratio() -> None:
    seed, angles = _rescue_candidate_angles(
        ratio=1.6,
        orig_conf=0.96,
        area=100.0,
        textline_angle=0,
        estimated=None,
    )
    assert seed == 90.0
    assert -90.0 in angles


def test_rescue_candidate_vertical_flipped_textline() -> None:
    seed, angles = _rescue_candidate_angles(
        ratio=1.6,
        orig_conf=0.96,
        area=100.0,
        textline_angle=180,
        estimated=None,
    )
    assert seed == -90.0
    assert 90.0 in angles


def test_rescue_candidate_estimated_sweep() -> None:
    seed, angles = _rescue_candidate_angles(
        ratio=1.0,
        orig_conf=0.5,
        area=100.0,
        textline_angle=0,
        estimated=45.0,
    )
    assert seed == 0.0
    for d in SWEEP_DELTAS:
        assert 45.0 + d in angles
    assert 180.0 in angles  # orig_conf < 0.9


def test_rescue_candidate_diagonal_fallback_grid() -> None:
    _, angles = _rescue_candidate_angles(
        ratio=1.0,
        orig_conf=0.5,
        area=100.0,
        textline_angle=0,
        estimated=None,
    )
    for a in DIAGONAL_ANGLES:
        assert a in angles
