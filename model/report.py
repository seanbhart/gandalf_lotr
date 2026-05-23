from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pandas as pd

from model.scenarios import run_all_scenarios, summarize_scenarios


FINDINGS = [
    "The valuation invariant holds in the scenario set: Limit Token + Redeem Token equals collateral after configured transfer fees.",
    "Both lower-limit hedges and higher-limit speculative orders can be represented with the same crossing logic by tracking price direction.",
    "Oracle and DEX availability are first-order viability risks because a crossed limit can still leave holders with an execution failure state.",
    "Execution reward and DEX slippage reduce realized execution value directly, while transfer fees reduce the redeemable token-pair value.",
    "Redemption is an important competing path: if both token halves are reunited before execution, collateral exits and execution should no longer occur for that pair.",
]


def _line_chart_svg(df: pd.DataFrame, scenario: str, width: int = 720, height: int = 220) -> str:
    group = df[(df["scenario"] == scenario) & (df["run"] == 1)].sort_values("timestep")
    values = group[["target_price", "limit_token_price", "redeem_token_price"]]
    if group.empty:
        return ""

    padding = 28
    x_values = group["timestep"].tolist()
    y_min = 0.0
    y_max = max(float(values.max().max()), 1.0)

    def point(value, index):
        x_span = max(len(x_values) - 1, 1)
        x = padding + (index / x_span) * (width - (padding * 2))
        y = height - padding - ((float(value) - y_min) / (y_max - y_min)) * (height - (padding * 2))
        return f"{x:.1f},{y:.1f}"

    series = [
        ("target_price", "#2563eb"),
        ("limit_token_price", "#7c3aed"),
        ("redeem_token_price", "#111827"),
    ]
    paths = []
    for column, color in series:
        points = " ".join(point(value, index) for index, value in enumerate(group[column].tolist()))
        paths.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" />')

    limit_y = height - padding - ((float(group["limit_price"].iloc[-1]) - y_min) / (y_max - y_min)) * (height - (padding * 2))
    return f"""
<svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(scenario)} chart">
  <rect width="{width}" height="{height}" fill="#ffffff" />
  <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#d1d5db" />
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#d1d5db" />
  <line x1="{padding}" y1="{limit_y:.1f}" x2="{width-padding}" y2="{limit_y:.1f}" stroke="#dc2626" stroke-dasharray="5 5" />
  {''.join(paths)}
</svg>
"""


def _html_report(records: pd.DataFrame, summary: pd.DataFrame) -> str:
    cards = []
    for _, row in summary.iterrows():
        scenario = row["scenario"]
        cards.append(
            f"""
<section class="scenario">
  <h2>{html.escape(scenario.replace("_", " ").title())}</h2>
  {_line_chart_svg(records, scenario)}
  <dl>
    <div><dt>Executed</dt><dd>{int(row["executed_runs"])}</dd></div>
    <div><dt>Redeemed</dt><dd>{int(row["redeemed_runs"])}</dd></div>
    <div><dt>Failed</dt><dd>{int(row["failed_runs"])}</dd></div>
    <div><dt>Failure</dt><dd>{html.escape(str(row["failure_reasons"]) or "none")}</dd></div>
    <div><dt>Pair Value</dt><dd>{row["avg_pair_value"]}</dd></div>
    <div><dt>Exec Value</dt><dd>{row["avg_execution_value"]}</dd></div>
  </dl>
</section>
"""
        )

    findings = "\n".join(f"<li>{html.escape(finding)}</li>" for finding in FINDINGS)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LOTR radCAD Scenario Dashboard</title>
  <style>
    body {{ margin: 0; font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; background: #f8fafc; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
    h1 {{ font-size: 30px; margin: 0 0 8px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    .lede {{ margin: 0 0 28px; color: #4b5563; }}
    .findings, .scenario {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 18px; }}
    .findings {{ margin-bottom: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px; }}
    svg {{ width: 100%; height: auto; border: 1px solid #e5e7eb; border-radius: 6px; }}
    dl {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0 0; }}
    dt {{ color: #6b7280; font-size: 12px; }}
    dd {{ margin: 2px 0 0; font-weight: 600; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <main>
    <h1>LOTR radCAD Scenario Dashboard</h1>
    <p class="lede">Scenario outputs for Limit Order Token Reserve valuation, execution, redemption, and market-friction edge cases.</p>
    <section class="findings">
      <h2>Findings</h2>
      <ul>{findings}</ul>
    </section>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def _notebook(records_path: Path, summary_path: Path) -> dict:
    markdown = "\n".join(f"- {finding}" for finding in FINDINGS)
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# LOTR radCAD Scenario Report\n",
                    "\n",
                    "This notebook loads the generated scenario records and summary tables for TH-2.\n",
                    "\n",
                    "## Findings\n",
                    markdown,
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    f"records = pd.read_csv('{records_path.as_posix()}')\n",
                    f"summary = pd.read_csv('{summary_path.as_posix()}')\n",
                    "summary\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "for scenario, group in records.groupby('scenario', sort=False):\n",
                    "    ax = group[group['run'] == 1].plot(\n",
                    "        x='timestep',\n",
                    "        y=['target_price', 'limit_token_price', 'redeem_token_price'],\n",
                    "        title=scenario,\n",
                    "        figsize=(8, 3),\n",
                    "        grid=True,\n",
                    "    )\n",
                    "    ax.axhline(group['limit_price'].iloc[-1], color='red', linestyle='--', linewidth=1)\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def generate_reports(output_dir: str | Path = "reports") -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = run_all_scenarios()
    summary = summarize_scenarios(records)

    records_path = output_dir / "lotr_scenario_records.csv"
    summary_path = output_dir / "lotr_scenario_summary.csv"
    dashboard_path = output_dir / "lotr_dashboard.html"
    notebook_path = output_dir / "lotr_scenario_report.ipynb"

    records.to_csv(records_path, index=False)
    summary.to_csv(summary_path, index=False)
    dashboard_path.write_text(_html_report(records, summary), encoding="utf-8")
    notebook_path.write_text(
        json.dumps(_notebook(records_path, summary_path), indent=2),
        encoding="utf-8",
    )

    return {
        "records": records_path,
        "summary": summary_path,
        "dashboard": dashboard_path,
        "notebook": notebook_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LOTR scenario outputs.")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    paths = generate_reports(args.output_dir)
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
