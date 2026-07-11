"""Build the M8 final report from the gold layer, then validate.

Renders reports/shopsphere_final_report.html from report_template.html
(headline KPIs queried live with the same SQL as the M3 gate, 15 figures
embedded as base64), prints it to PDF via headless Microsoft Edge, then
re-opens the written HTML and asserts its embedded KPI values against
freshly queried SQL. Exit 1 on any mismatch. Read-only against MySQL.

Zero new dependencies: stdlib + the already-pinned stack. Edge is invoked
as a subprocess (override the binary with the EDGE_PATH env var).
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from string import Template

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from build_excel_workbook import (AB_LIFT_EXPECTED, AOV_EXPECTED,
                                  REL_TOLERANCE, compute_ab, compute_kpis,
                                  fetch_scalar)

TEMPLATE_PATH = Path(__file__).resolve().parent / "report_template.html"
FIGURES_DIR = settings.PROJECT_ROOT / "reports" / "figures"
HTML_PATH = settings.PROJECT_ROOT / "reports" / "shopsphere_final_report.html"
PDF_PATH = settings.PROJECT_ROOT / "reports" / "shopsphere_final_report.pdf"

FIGURES = [
    "monthly_revenue", "aov_distribution", "funnel_conversion",
    "cac_by_channel", "customer_pareto", "repeat_purchase",
    "rfm_segment_sizes", "rfm_heatmap", "rfm_segment_value",
    "rfm_channel_value", "clv_distribution", "churn_roc_calibration",
    "churn_feature_importance", "ab_conversion_ci", "ab_power_curve",
]
MIN_PDF_BYTES = 300_000        # 744 KB of embedded figures ⇒ a thin PDF is a failure
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
KPI_JSON_RE = re.compile(
    r'<script type="application/json" id="kpi-values">(.*?)</script>',
    re.DOTALL)


def find_edge() -> str:
    """Locate msedge.exe; EDGE_PATH env var wins. Fail loud if absent."""
    override = os.environ.get("EDGE_PATH")
    if override:
        if Path(override).is_file():
            return override
        raise FileNotFoundError(f"EDGE_PATH set but not a file: {override}")
    for candidate in EDGE_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    found = shutil.which("msedge")
    if found:
        return found
    raise FileNotFoundError(
        "Microsoft Edge not found — set EDGE_PATH to msedge.exe")


def embed_figures(figures_dir: Path) -> dict:
    """Read every expected PNG and return {fig_<name>: data URI}."""
    out = {}
    for name in FIGURES:
        png = figures_dir / f"{name}.png"
        if not png.is_file():
            raise FileNotFoundError(f"Missing figure: {png}")
        data = png.read_bytes()
        if not data.startswith(PNG_MAGIC):
            raise ValueError(f"Not a valid PNG (bad magic): {png}")
        encoded = base64.b64encode(data).decode("ascii")
        out[f"fig_{name}"] = f"data:image/png;base64,{encoded}"
    return out


def format_values(kpis: dict, ab: dict, data_window: str) -> dict:
    """Display strings for the template, plus the raw-value JSON block."""
    raw = {
        "total_revenue": round(kpis["total_revenue"], 2),
        "completed_orders": int(kpis["completed_orders"]),
        "aov": round(kpis["aov"], 4),
        "buyers": int(kpis["buyers"]),
        "one_time_rate": round(kpis["one_time_rate"], 4),
        "abandonment": round(kpis["abandonment"], 4),
        "top20_share": round(kpis["top20_share"], 4),
        "paid_cac": round(kpis["paid_cac"], 4),
        "nps": round(kpis["nps"], 2),
        "ab_lift": round(ab["lift"], 4),
        "ab_p": ab["p_value"],
    }
    return {
        "data_window": data_window,
        "build_date": date.today().isoformat(),
        "total_revenue": f"${kpis['total_revenue']:,.2f}",
        "completed_orders": f"{int(kpis['completed_orders']):,}",
        "aov": f"${kpis['aov']:,.2f}",
        "buyers": f"{int(kpis['buyers']):,}",
        "one_time_rate": f"{kpis['one_time_rate']:.1%}",
        "abandonment": f"{kpis['abandonment']:.1%}",
        "top20_share": f"{kpis['top20_share']:.1%}",
        "paid_cac": f"${kpis['paid_cac']:,.2f}",
        "nps": f"{kpis['nps']:.1f}",
        "ab_lift": f"{ab['lift']:+.1%}",
        "ab_p": f"{ab['p_value']:.1e}",
        "ab_conv_control": f"{ab['conv_control']:.2%}",
        "ab_conv_treatment": f"{ab['conv_treatment']:.2%}",
        "kpi_json": json.dumps(raw),
    }


def render_html(template_text: str, values: dict) -> str:
    """safe_substitute (the prose contains literal $-amounts like $487),
    after failing loud on any template placeholder missing from values —
    get_identifiers() sees every $name/${name} form, any case."""
    template = Template(template_text)
    missing = sorted(set(template.get_identifiers()) - values.keys())
    if missing:
        raise ValueError(f"Unfilled template placeholders: {missing}")
    return template.safe_substitute(values)


def extract_kpi_json(html_text: str) -> dict:
    match = KPI_JSON_RE.search(html_text)
    if not match:
        raise ValueError("kpi-values JSON block not found in HTML")
    return json.loads(match.group(1))


def print_pdf(edge: str, html_path: Path, pdf_path: Path) -> None:
    # A stale PDF from a previous run must not mask an Edge failure.
    pdf_path.unlink(missing_ok=True)
    cmd = [edge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=10000",
           f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError(
            f"Edge print-to-pdf failed (rc={result.returncode}): "
            f"{result.stderr.strip()[-500:]}")
    with pdf_path.open("rb") as fh:
        if fh.read(5) != b"%PDF-":
            raise RuntimeError(f"Edge wrote a non-PDF file: {pdf_path}")


def make_data_window(first, last) -> str:
    if first is None or last is None:
        raise ValueError("gold_revenue_trend returned no months — empty view?")
    return f"{first} – {last}"


def build(engine) -> dict:
    edge = find_edge()          # fail before writing any artifact
    kpis = compute_kpis(engine)
    ab = compute_ab(engine)
    with engine.connect() as conn:
        first = conn.execute(text(
            "SELECT MIN(order_month) FROM gold_revenue_trend")).scalar_one()
        last = conn.execute(text(
            "SELECT MAX(order_month) FROM gold_revenue_trend")).scalar_one()
    values = format_values(kpis, ab, make_data_window(first, last))
    values.update(embed_figures(FIGURES_DIR))
    html = render_html(TEMPLATE_PATH.read_text(encoding="utf-8"), values)
    HTML_PATH.write_text(html, encoding="utf-8")
    print_pdf(edge, HTML_PATH, PDF_PATH)
    return {"kpis": kpis, "ab": ab}


def validate(engine) -> bool:
    """Re-open the written HTML + PDF; assert against fresh SQL."""
    html = HTML_PATH.read_text(encoding="utf-8")
    written = extract_kpi_json(html)
    with engine.connect() as conn:
        fresh_rev = fetch_scalar(
            conn, "SELECT SUM(order_revenue) FROM gold_order_revenue "
                  "WHERE order_status = 'completed'")
        fresh_buyers = fetch_scalar(conn,
                                    "SELECT COUNT(*) FROM gold_customer_pareto")
    pdf_bytes = PDF_PATH.stat().st_size if PDF_PATH.is_file() else 0
    checks = [
        ("Revenue in HTML == SQL",
         abs(written["total_revenue"] - fresh_rev) < 0.01,
         f"{written['total_revenue']:,.2f} vs {fresh_rev:,.2f}"),
        ("Buyers in HTML == gold_customer_pareto",
         written["buyers"] == int(fresh_buyers),
         f"{written['buyers']} vs {int(fresh_buyers)}"),
        ("AOV within 0.5% of gate value",
         abs(written["aov"] - AOV_EXPECTED) <= AOV_EXPECTED * REL_TOLERANCE,
         f"{written['aov']:.4f} vs {AOV_EXPECTED}"),
        ("A/B lift within 0.005 of calibration",
         abs(written["ab_lift"] - AB_LIFT_EXPECTED) < 0.005,
         f"{written['ab_lift']:.4f} vs {AB_LIFT_EXPECTED}"),
        ("All figures embedded",
         html.count("data:image/png;base64,") == len(FIGURES),
         f"{html.count('data:image/png;base64,')} of {len(FIGURES)}"),
        ("PDF written and non-trivial",
         pdf_bytes > MIN_PDF_BYTES,
         f"{pdf_bytes:,} bytes (floor {MIN_PDF_BYTES:,})"),
    ]
    ok = True
    for name, passed, detail in checks:
        ok = ok and passed
        print(f"  {'PASS' if passed else 'FAIL'} {name}: {detail}")
    return ok


def main() -> int:
    from config.db import get_engine
    engine = get_engine()
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    built = build(engine)
    print(f"Wrote {HTML_PATH.name} + {PDF_PATH.name} "
          f"(revenue {built['kpis']['total_revenue']:,.2f}, "
          f"AOV {built['kpis']['aov']:.4f}, "
          f"lift {built['ab']['lift']:+.3%})")
    ok = validate(engine)
    print("Report gate:", "PASS (6/6)" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
