"""Unit tests for the M8 final-report builder (no MySQL, no Edge)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python" / "05_delivery"))

from build_final_report import (FIGURES, FIGURES_DIR, PNG_MAGIC,
                                TEMPLATE_PATH, embed_figures,
                                extract_kpi_json, format_values,
                                make_data_window, print_pdf, render_html)

SYNTH_KPIS = {
    "total_revenue": 1234567.89, "completed_orders": 17000.0, "aov": 92.5,
    "buyers": 11000.0, "one_time_rate": 0.692, "abandonment": 0.706,
    "top20_share": 0.569, "paid_cac": 73.89, "nps": 8.2,
}
SYNTH_AB = {"lift": 0.1506, "p_value": 7.9e-4,
            "conv_control": 0.0343, "conv_treatment": 0.0395}


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


def test_render_flags_braced_and_capitalized_placeholders():
    # Review finding: $Name and ${name} are valid Template syntax and must
    # not slip through the missing-placeholder check.
    with pytest.raises(ValueError) as exc:
        render_html("<p>$Total and ${aov}</p>", {})
    assert "Total" in str(exc.value) and "aov" in str(exc.value)


def test_make_data_window_raises_on_empty_view():
    with pytest.raises(ValueError, match="gold_revenue_trend"):
        make_data_window(None, "2026-06")
    assert make_data_window("2024-07", "2026-06") == "2024-07 – 2026-06"


def test_embed_figures_rejects_corrupt_png(tmp_path):
    for name in FIGURES:
        (tmp_path / f"{name}.png").write_bytes(PNG_MAGIC + b"payload")
    (tmp_path / f"{FIGURES[0]}.png").write_bytes(b"")   # corrupt one
    with pytest.raises(ValueError, match=FIGURES[0]):
        embed_figures(tmp_path)


def test_print_pdf_removes_stale_pdf_and_raises(tmp_path):
    # Review finding: a stale PDF from a previous run must not mask an Edge
    # failure. Use the Python interpreter as a fake "edge" that rejects the
    # Chromium flags (nonzero exit) and writes nothing.
    html = tmp_path / "r.html"
    html.write_text("<html></html>", encoding="utf-8")
    stale = tmp_path / "r.pdf"
    stale.write_bytes(b"%PDF- stale from previous run")
    with pytest.raises(RuntimeError, match="print-to-pdf failed"):
        print_pdf(sys.executable, html, stale)
    assert not stale.exists(), "stale PDF must be deleted before printing"
