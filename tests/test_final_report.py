"""Unit tests for the M8 final-report builder (no MySQL, no Edge)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python" / "05_delivery"))

from build_final_report import (FIGURES, FIGURES_DIR, TEMPLATE_PATH,
                                extract_kpi_json, format_values, render_html)

SYNTH_KPIS = {
    "total_revenue": 1234567.89, "completed_orders": 17000.0, "aov": 92.5,
    "buyers": 11000.0, "one_time_rate": 0.692, "abandonment": 0.706,
    "top20_share": 0.569, "paid_cac": 73.89, "nps": 8.2,
}
SYNTH_AB = {"lift": 0.1506, "p_value": 7.9e-4}


def synth_values() -> dict:
    values = format_values(SYNTH_KPIS, SYNTH_AB, "2024-07 – 2026-06")
    values.update({f"fig_{name}": "data:image/png;base64,AAAA"
                   for name in FIGURES})
    return values


def test_render_fills_every_placeholder():
    html = render_html(TEMPLATE_PATH.read_text(encoding="utf-8"),
                       synth_values())
    assert "$1,234,567.89" in html          # formatted revenue landed
    assert "69.2%" in html                  # one-time rate landed
    assert html.count("data:image/png;base64,") == len(FIGURES)


def test_render_preserves_literal_dollar_amounts():
    html = render_html(TEMPLATE_PATH.read_text(encoding="utf-8"),
                       synth_values())
    assert "$487" in html                   # prose $-amounts must survive
    assert "$282,875" in html


def test_render_raises_on_missing_placeholder():
    values = synth_values()
    del values["aov"]
    with pytest.raises(ValueError, match="aov"):
        render_html(TEMPLATE_PATH.read_text(encoding="utf-8"), values)


def test_kpi_json_roundtrip():
    html = render_html(TEMPLATE_PATH.read_text(encoding="utf-8"),
                       synth_values())
    raw = extract_kpi_json(html)
    assert raw["total_revenue"] == 1234567.89
    assert raw["buyers"] == 11000
    assert raw["ab_lift"] == 0.1506


def test_extract_raises_without_json_block():
    with pytest.raises(ValueError, match="kpi-values"):
        extract_kpi_json("<html><body>no block</body></html>")


def test_format_values_display_strings():
    values = format_values(SYNTH_KPIS, SYNTH_AB, "w")
    assert values["total_revenue"] == "$1,234,567.89"
    assert values["one_time_rate"] == "69.2%"
    assert values["ab_lift"] == "+15.1%"
    assert values["ab_p"] == "7.9e-04"
    assert values["completed_orders"] == "17,000"


def test_expected_figures_exist_on_disk():
    missing = [n for n in FIGURES
               if not (FIGURES_DIR / f"{n}.png").is_file()]
    assert missing == [], f"figures missing from reports/figures: {missing}"
