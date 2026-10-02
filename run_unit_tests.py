#!/usr/bin/env python3
"""Run the Lunara Python unit suite and write test_output/unit_report.html."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(ROOT, "test_output", "unit_report.html")


class RecordingResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append((str(test), "PASS", ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.rows.append((str(test), "FAIL", self._exc_info_to_string(err, test)))

    def addError(self, test, err):
        super().addError(test, err)
        self.rows.append((str(test), "ERROR", self._exc_info_to_string(err, test)))


def write_report(rows, elapsed: float) -> None:
    passed = sum(1 for _name, status, _detail in rows if status == "PASS")
    failed = len(rows) - passed
    body = ""
    for name, status, detail in rows:
        cls = "pass" if status == "PASS" else "fail"
        extra = f"<pre>{detail}</pre>" if detail else ""
        body += f"<tr><td>{name}</td><td class='{cls}'>{status}</td></tr>{extra and ''}"
        if detail:
            body += f"<tr><td colspan='2'><pre>{detail}</pre></td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Lunara Unit Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0f172a; color:#f1f5f9; margin:0; padding:24px; }}
    h1 {{ color:#38bdf8; text-align:center; }}
    .meta {{ text-align:center; color:#94a3b8; }}
    table {{ width:100%; border-collapse:collapse; margin-top:24px; }}
    th, td {{ text-align:left; padding:10px 12px; border-top:1px solid #334155; vertical-align:top; }}
    th {{ color:#7dd3fc; }}
    .pass {{ color:#4ade80; font-weight:700; }}
    .fail {{ color:#f87171; font-weight:700; }}
    pre {{ white-space:pre-wrap; color:#fecaca; font-size:.8rem; }}
  </style>
</head>
<body>
  <h1>Lunara Unit Report</h1>
  <p class="meta">{datetime.now().strftime("%Y-%m-%d %H:%M")} · {passed} passed · {failed} failed · {elapsed:.2f}s</p>
  <table>
    <thead><tr><th>Test</th><th>Result</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</body>
</html>"""
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Report → {REPORT_PATH}")


def main() -> int:
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    os.chdir(os.path.join(ROOT, "tools"))
    suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
    result = RecordingResult()
    started = datetime.now()
    suite.run(result)
    elapsed = (datetime.now() - started).total_seconds()
    for name, status, _detail in result.rows:
        print(f"{status}: {name}")
    print(f"\n{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
    write_report(result.rows, elapsed)
    return 1 if not result.wasSuccessful() else 0


if __name__ == "__main__":
    sys.exit(main())
