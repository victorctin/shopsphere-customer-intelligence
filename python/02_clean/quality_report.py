"""Grade the cleaning audit against the dirty-data injection manifest.
The manifest is the ground truth: every injected defect class must be found
exactly (delta 0) for the report to grade PERFECT."""
import re
from pathlib import Path

import pandas as pd

_ROW_RE = re.compile(r"^\|\s*([a-z_]+)\s*\|\s*(\d+)\s*\|$")


def parse_manifest(path: Path) -> dict[str, int]:
    manifest: dict[str, int] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _ROW_RE.match(line.strip())
        if m:
            manifest[m.group(1)] = int(m.group(2))
    return manifest


def grade(audit: dict[str, int], manifest: dict[str, int]) -> pd.DataFrame:
    rows = []
    for defect, injected in manifest.items():
        found = int(audit.get(defect, 0))
        delta = found - injected
        rows.append({"defect": defect, "injected": injected, "found": found,
                     "delta": delta, "verdict": "PASS" if delta == 0 else "MISS"})
    return pd.DataFrame(rows, columns=["defect", "injected", "found", "delta", "verdict"])


def write_report(grade_df: pd.DataFrame, path: Path) -> None:
    passed = int((grade_df["verdict"] == "PASS").sum())
    total = len(grade_df)
    overall = "PERFECT" if passed == total else "INCOMPLETE"
    lines = [
        "# Data Quality Report (bronze -> silver)",
        "",
        f"**Grade: {overall} — {passed}/{total} defect classes matched exactly**",
        "",
        "Graded against `docs/dirty_data_manifest.md` (injection ground truth).",
        "`delta` = found - injected; every class must be 0 or explicitly waived.",
        "",
        "| Defect | Injected | Found | Delta | Verdict |",
        "|---|---|---|---|---|",
    ]
    for _, r in grade_df.iterrows():
        lines.append(f"| {r['defect']} | {r['injected']} | {r['found']} "
                     f"| {r['delta']} | {r['verdict']} |")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
