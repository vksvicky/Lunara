"""HTML report for the Lunara visual checks."""

from __future__ import annotations

import os
from datetime import datetime


def _badge(result, update_baselines=False) -> str:
    if update_baselines and result.get("passed"):
        return '<span class="badge badge-pass">BASELINE UPDATED</span>'
    if not result.get("has_baseline", False) and not update_baselines:
        return '<span class="badge badge-nobase">NO BASELINE</span>'
    if result.get("passed", False):
        return '<span class="badge badge-pass">PASS</span>'
    return '<span class="badge badge-fail">FAIL</span>'


def _img_tag(path, root: str, alt="") -> str:
    if path and os.path.exists(path):
        rel = os.path.relpath(path, os.path.join(root, "test_output"))
        return f'<img src="{rel}" alt="{alt}" loading="lazy">'
    return '<div class="no-img">No image</div>'


def _diff_cell(result, root: str) -> str:
    if not result.get("has_baseline") and result.get("diff_pct") != 0.0:
        return '<div class="no-img">No baseline yet. Run with --update-baselines.</div>'
    if result.get("diff_img") and os.path.exists(result["diff_img"]):
        badge = ""
        if result.get("diff_pct") is not None:
            cls = "badge-pass" if result["diff_pct"] <= 5.0 else "badge-fail"
            badge = f'<div><span class="badge {cls}">{result["diff_pct"]:.2f}% diff</span></div>'
        return _img_tag(result["diff_img"], root, "Diff") + badge
    if result.get("has_baseline"):
        return _img_tag(result.get("baseline_img"), root, "Baseline")
    return '<div class="no-img">No diff</div>'


def generate_report(all_results, branch, report_path, root, update_baselines=False) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = f"branch: <code>{branch}</code>"
    if update_baselines:
        mode += " · <strong>BASELINE CAPTURE</strong>"
    sections = ""
    for dev_id, res_info, dev_name, results in all_results:
        passed = sum(1 for result in results if result.get("passed"))
        failed = len(results) - passed
        warn = " warn" if failed else ""
        rows = ""
        for result in results:
            slots = "".join(f"<li>{item}</li>" for item in result.get("slots", []))
            issues = "".join(f"<li>{item}</li>" for item in result.get("issues", []))
            issue_html = f'<ul class="issues-list">{issues}</ul>' if issues else ""
            rows += f"""
        <tr>
          <td class="pass-name">
            <strong>{result.get("pass_name", result["id"])}</strong><br>
            <small>{result.get("description", "")}</small><br>
            {_badge(result, update_baselines)}
            <ul class="slot-list">{slots}</ul>
            {issue_html}
          </td>
          <td class="img-cell">{_img_tag(result.get("current_img"), root, result["id"])}</td>
          <td class="img-cell">{_img_tag(result.get("zones_img"), root, result["id"] + " zones")}</td>
          <td class="img-cell">{_diff_cell(result, root)}</td>
        </tr>"""
        failed_html = f'<span class="stat{warn}">{failed} failed</span>' if failed else ""
        sections += f"""
    <div class="device-section">
      <div class="device-header">
        <h2>{dev_name} <small>{dev_id}</small></h2>
        <span class="badge-res">{res_info}</span>
        <span class="stat">{passed} passed</span>
        {failed_html}
      </div>
      <table class="result-table">
        <thead>
          <tr>
            <th>Pass &amp; Assertions</th>
            <th>Watch Face Screenshot</th>
            <th>Layout Zones &amp; Clearance</th>
            <th>Baseline Comparison (Diff)</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Lunara Visual Regression &amp; Layout Validation Report</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a; color: #f1f5f9; margin: 0; padding: 24px; }}
    h1 {{ text-align: center; color: #38bdf8; margin-bottom: 4px; }}
    .meta {{ text-align: center; color: #94a3b8; margin-bottom: 28px; }}
    .meta code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #7dd3fc; }}
    .device-section {{ background: #1e293b; border-radius: 12px; border: 1px solid #334155; margin-bottom: 32px; overflow: hidden; }}
    .device-header {{ padding: 16px 20px; background: #162032; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
    .device-header h2 {{ margin: 0; color: #e2e8f0; font-size: 1.1rem; }}
    .device-header small {{ color: #94a3b8; font-weight: 400; }}
    .badge-res {{ background: #0284c7; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 700; }}
    .stat {{ font-size: .82rem; color: #4ade80; }}
    .stat.warn {{ color: #f87171; }}
    .result-table {{ width: 100%; border-collapse: collapse; }}
    .result-table th {{ background: #0f172a; color: #7dd3fc; text-align: left; padding: 10px 16px; font-size: .8rem; text-transform: uppercase; }}
    .result-table td {{ padding: 12px 16px; border-top: 1px solid #334155; vertical-align: top; }}
    .pass-name {{ width: 260px; }}
    .pass-name small {{ color: #94a3b8; }}
    .img-cell img {{ max-width: 100%; border-radius: 6px; border: 1px solid #334155; }}
    .no-img {{ color: #94a3b8; font-size: .8rem; padding: 20px; text-align: center; }}
    .slot-list {{ margin: 6px 0 0; padding-left: 16px; font-size: .75rem; color: #94a3b8; }}
    .issues-list {{ margin: 6px 0 0; padding-left: 16px; font-size: .75rem; color: #f87171; font-weight: 700; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: .75rem; font-weight: 700; margin-top: 6px; }}
    .badge-pass {{ background: #14532d; color: #4ade80; }}
    .badge-fail {{ background: #7f1d1d; color: #f87171; }}
    .badge-nobase {{ background: #854d0e; color: #fef08a; }}
  </style>
</head>
<body>
  <h1>Lunara Visual Regression &amp; Layout Report</h1>
  <p class="meta">{mode} · {timestamp} · {len(all_results)} devices</p>
  {sections}
</body>
</html>"""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"\nReport → {report_path}")
