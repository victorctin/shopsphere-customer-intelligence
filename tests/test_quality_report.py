import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python" / "02_clean"))

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "docs" / "dirty_data_manifest.md"

PERFECT_AUDIT = {
    "duplicate_orders": 290, "missing_emails": 240, "malformed_emails": 118,
    "messy_countries": 480, "bad_quantities": 155, "fat_finger_prices": 15,
    "events_before_session": 2000, "orders_before_signup": 100,
    "orphan_order_items": 62,
}


def test_parse_manifest_reads_all_nine_defects():
    from quality_report import parse_manifest
    manifest = parse_manifest(MANIFEST_PATH)
    assert len(manifest) == 9
    assert manifest["duplicate_orders"] == 290
    assert manifest["orphan_order_items"] == 62


def test_grade_perfect_audit_all_pass():
    from quality_report import grade, parse_manifest
    df = grade(PERFECT_AUDIT, parse_manifest(MANIFEST_PATH))
    assert list(df.columns) == ["defect", "injected", "found", "delta", "verdict"]
    assert len(df) == 9
    assert (df["delta"] == 0).all()
    assert (df["verdict"] == "PASS").all()


def test_grade_mismatch_flags_miss():
    from quality_report import grade, parse_manifest
    audit = dict(PERFECT_AUDIT, duplicate_orders=289)
    df = grade(audit, parse_manifest(MANIFEST_PATH))
    row = df[df["defect"] == "duplicate_orders"].iloc[0]
    assert row["delta"] == -1
    assert row["verdict"] == "MISS"
    assert (df[df["defect"] != "duplicate_orders"]["verdict"] == "PASS").all()


def test_write_report_perfect(tmp_path):
    from quality_report import grade, parse_manifest, write_report
    df = grade(PERFECT_AUDIT, parse_manifest(MANIFEST_PATH))
    out = tmp_path / "report.md"
    write_report(df, out)
    text = out.read_text(encoding="utf-8")
    assert "PERFECT" in text
    assert "duplicate_orders" in text
    assert "9/9" in text


def test_write_report_with_miss(tmp_path):
    from quality_report import grade, parse_manifest, write_report
    df = grade(dict(PERFECT_AUDIT, bad_quantities=0), parse_manifest(MANIFEST_PATH))
    out = tmp_path / "report.md"
    write_report(df, out)
    text = out.read_text(encoding="utf-8")
    assert "PERFECT" not in text
    assert "MISS" in text
    assert "8/9" in text
