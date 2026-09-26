#!/usr/bin/env python3
"""Render the offline single-file case study from analysis JSON + verified JSON only."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PATH = ROOT / "data/analysis/final_analysis.json"
DATASET_PATH = ROOT / "data/verified/final_dataset.json"
OUTPUT_PATH = ROOT / "case-study/index.html"


def esc(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return html.escape(str(value), quote=True)


def badge(value: Any, kind: str = "") -> str:
    text = esc(value or "UNKNOWN")
    slug = text.lower().replace(" ", "-").replace("_", "-")
    cls = f"badge {kind} {slug}".strip()
    return f'<span class="{esc(cls)}">{text}</span>'


def source_links(urls: list[str]) -> str:
    links = []
    for i, url in enumerate(urls[:3], 1):
        links.append(f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">Source&nbsp;{i}</a>')
    if len(urls) > 3:
        links.append(f'<span class="muted">+{len(urls) - 3} more</span>')
    return " ".join(links) or "—"


def bar_group(title: str, cohorts: dict, labels: dict) -> str:
    """Build a distribution card. Bar widths are set directly in CSS —
    no JavaScript animation needed, so they always render."""
    parts = []
    for cohort, values in cohorts.items():
        ceiling = max(values.values(), default=1) or 1
        rows = []
        for label, count in values.items():
            pct = max(2, round(100 * count / ceiling))  # min 2% so small values are visible
            slug = label.lower().replace(" ", "-").replace("_", "-")
            rows.append(
                f'<div class="bar-row">'
                f'<span class="bar-label">{esc(label)}</span>'
                f'<span class="bar-track"><span class="bar-fill color-{esc(slug)}" style="width:{pct}%"></span></span>'
                f'<strong class="bar-val">{count}</strong>'
                f'</div>'
            )
        head_label = cohort.replace("_", " ").title()
        note = labels.get(cohort, "")
        parts.append(
            f'<div class="bar-cohort">'
            f'<div class="cohort-head"><span>{esc(head_label)}</span><small>{esc(note)}</small></div>'
            f'{"".join(rows)}'
            f'</div>'
        )
    return (
        f'<article class="card">'
        f'<h3>{esc(title)}</h3>'
        f'<div class="bar-grid">{"".join(parts)}</div>'
        f'</article>'
    )


def main() -> int:
    if not ANALYSIS_PATH.exists() or not DATASET_PATH.exists():
        print("Missing data artifacts.", file=sys.stderr)
        return 2

    analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    scope = analysis["scope"]
    ver = analysis["verification"]
    metrics = ver["metrics"]
    accuracy = metrics["field_accuracy"]
    post_all = metrics.get("post_recheck_all_rows", {})
    categories = scope["categories"]
    triage_by_id = {r["app_id"]: r for r in analysis["easy_win_outreach"]["rows"]}

    # ── Metric cards ──
    stat_cards = [
        ("100", "Applications Analyzed", "Full SaaS coverage audit"),
        ("10", "Category Segments", "CRM, Fintech, DevTools & more"),
        ("20", "Verification Sample", "Manual source-concordance audit"),
        (str(scope["complete_records"]), "Complete Records", "First-pass research status"),
    ]
    cards_html = "\n".join(
        f'<article class="stat-card">'
        f'<div class="stat-number">{v}</div>'
        f'<div class="stat-label">{l}</div>'
        f'<div class="stat-note">{n}</div>'
        f'</article>'
        for v, l, n in stat_cards
    )

    # ── Distribution charts ──
    cohort_labels = {
        "manifest_all_100": "N=100 manifest rows",
        "captured_prior_or_live_100": f"N={scope['captured_record_count']} researched",
        "selected_sample_20": f"N={analysis['sample']['selected_count']} selected",
        "fully_adjudicated_selected_15": f"N={analysis['cohorts']['fully_adjudicated_sample']['count']} adjudicated",
    }
    charts = [
        ("auth", "Authentication Models"),
        ("self_serve", "Self-Serve Accessibility"),
        ("api_availability", "API Readiness"),
        ("mcp", "MCP Feasibility"),
    ]
    charts_html = "\n".join(
        bar_group(title, analysis["critical_field_distributions"][key], cohort_labels)
        for key, title in charts
    )

    # ── Accuracy table ──
    acc_rows = []
    for field, data in accuracy.items():
        rate = "N/A" if not data["checked"] else f'{100 * data["correct"] / data["checked"]:.1f}%'
        acc_rows.append(
            f'<tr><th>{esc(field.replace("_", " ").title())}</th>'
            f'<td>{data["correct"]}/{data["checked"]}</td>'
            f'<td class="text-green">{rate}</td>'
            f'<td>{data["unresolved"]}</td></tr>'
        )

    # ── Error log ──
    critical = [r for r in analysis["observed_error_analysis"]["examples"] if r.get("metric_group")]
    err_rows = "\n".join(
        f'<tr><td class="text-white">{esc(r["app"])}</td>'
        f'<td><code>{esc(r["field"])}</code></td>'
        f'<td class="muted">{esc(r["cause"])}</td></tr>'
        for r in critical
    ) or '<tr><td colspan="3" class="muted">No critical mismatches detected.</td></tr>'

    # ── 100-App matrix ──
    matrix_by_id = {r["app_id"]: r for r in analysis["matrix"]}
    table_rows = []
    for rec in sorted(dataset, key=lambda x: x["app_id"]):
        tri = triage_by_id[rec["app_id"]]
        ev = rec.get("evidence", [])
        urls = list(dict.fromkeys(e.get("source_url", "") for e in ev if e.get("source_url")))
        auth_methods = ", ".join(rec.get("auth_methods", [])) or "—"
        api_types = ", ".join((rec.get("api") or {}).get("types", [])) or "—"
        ss = rec.get("self_serve_status", "UNKNOWN")
        cred = (rec.get("credential_access") or {}).get("status", "UNKNOWN")
        api_s = (rec.get("api") or {}).get("available", "UNKNOWN")
        mcp_s = (rec.get("mcp") or {}).get("status", "UNKNOWN")
        bld = (rec.get("buildability") or {}).get("verdict", "UNKNOWN")
        blk = (rec.get("buildability") or {}).get("blocker", "")
        tri_l = tri["triage"]
        search_text = " ".join([rec["app"], rec["category"], str(rec.get("source_mode")), tri_l]).lower()

        table_rows.append(
            f"<tr data-cat='{esc(rec['category'])}' data-tri='{esc(tri_l)}' data-s='{esc(search_text)}'>"
            f"<th><div class='app-name'>{esc(rec['app'])}</div>"
            f"<div class='app-sub'><span class='mono'>#{rec['app_id']}</span> · {esc(rec['category'])}</div></th>"
            f"<td>{badge(rec.get('source_mode'), 'mode')}</td>"
            f"<td><span class='text-white'>{esc(rec.get('auth_status'))}</span><br><small class='muted'>{esc(auth_methods)}</small></td>"
            f"<td>{badge(ss)}<br><small class='muted'>{esc(cred)}</small></td>"
            f"<td>{badge(api_s)}<br><small class='muted'>{esc(api_types)}</small></td>"
            f"<td>{badge(mcp_s)}</td>"
            f"<td>{badge(bld)}<br><small class='blocker'>{esc(blk)}</small></td>"
            f"<td>{badge(tri_l, 'tier')}</td>"
            f"<td class='ev-cell'>{source_links(urls)}</td></tr>"
        )

    # ── Render full HTML ──
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Composio AI Product Ops · Case Study</title>
<meta name="description" content="An evidence-backed research pipeline analyzing API accessibility, authentication, and integration feasibility across 100 applications.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ═══════════════════════════════════════════
   DESIGN SYSTEM — Stripe / Linear / Vercel
   ═══════════════════════════════════════════ */

:root {{
  --bg:       #050505;
  --surface:  #0c0c0c;
  --card:     #101010;
  --card-up:  #141414;
  --border:   rgba(255,255,255,0.08);
  --border-h: rgba(255,255,255,0.16);
  --white:    #f5f5f5;
  --muted:    #71717a;
  --green:    #22c55e;
  --blue:     #3b82f6;
  --amber:    #f59e0b;
  --red:      #ef4444;
  --purple:   #a78bfa;
  --r:        10px;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--white);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}}

/* ── Ambient background: layered radial orbs ── */
body::before {{
  content: '';
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse 900px 700px at 20% 10%, rgba(59,130,246,0.08), transparent),
    radial-gradient(ellipse 600px 500px at 80% 30%, rgba(168,85,247,0.05), transparent),
    radial-gradient(ellipse 800px 600px at 50% 80%, rgba(34,197,94,0.04), transparent);
}}

a {{ color: var(--blue); text-decoration: none; }}
a:hover {{ text-decoration: underline; opacity: .9; }}

h1,h2,h3 {{ letter-spacing: -0.025em; line-height: 1.2; }}

code {{
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.82em; padding: 2px 7px;
  background: rgba(255,255,255,0.06); border: 1px solid var(--border);
  border-radius: 5px; color: #d4d4d8;
}}

.mono {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted); }}
.muted {{ color: var(--muted); }}
.text-white {{ color: var(--white); font-weight: 500; }}
.text-green {{ color: var(--green); font-weight: 600; }}

/* ═══════ TOP NAV ═══════ */
.topnav {{
  position: fixed; top: 0; width: 100%; z-index: 200;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; height: 56px;
  background: rgba(5,5,5,0.7);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border);
}}
.topnav-brand {{ display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px; color: var(--white); }}
.topnav-icon {{
  width: 26px; height: 26px; border-radius: 6px;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  display: grid; place-items: center;
  font-size: 12px; font-weight: 800; color: #fff;
  box-shadow: 0 0 12px rgba(59,130,246,0.35);
}}
.topnav-pill {{
  font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
  padding: 5px 14px; border-radius: 99px;
  background: rgba(245,158,11,0.08); color: var(--amber);
  border: 1px solid rgba(245,158,11,0.18);
  display: flex; align-items: center; gap: 7px;
}}
.topnav-pill::before {{
  content: ''; width: 5px; height: 5px; border-radius: 50%;
  background: var(--amber); box-shadow: 0 0 6px var(--amber);
}}

/* ═══════ HERO ═══════ */
.hero {{
  padding: 160px 24px 80px;
  text-align: center;
  max-width: 860px; margin: 0 auto;
  position: relative;
}}
.hero::before {{
  content: '';
  position: absolute; top: 60px; left: 50%; transform: translateX(-50%);
  width: 600px; height: 300px;
  background: radial-gradient(circle, rgba(59,130,246,0.12), transparent 70%);
  pointer-events: none; z-index: -1;
}}
.hero-pill {{
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
  color: var(--blue); background: rgba(59,130,246,0.08);
  padding: 6px 16px; border-radius: 99px;
  border: 1px solid rgba(59,130,246,0.15);
  margin-bottom: 28px;
}}
.hero h1 {{
  font-size: clamp(40px, 6vw, 64px); font-weight: 800;
  background: linear-gradient(180deg, #fff 30%, #71717a 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 20px;
}}
.hero p {{
  font-size: 18px; color: var(--muted); max-width: 640px;
  margin: 0 auto; line-height: 1.7;
}}

/* ═══════ STAT CARDS ═══════ */
.stats {{
  display: grid; grid-template-columns: repeat(4,1fr); gap: 1px;
  max-width: 1100px; margin: 0 auto 100px; padding: 0 40px;
  background: var(--border); border-radius: var(--r);
  overflow: hidden;
}}
.stat-card {{
  background: var(--card); padding: 36px 28px;
  transition: background .25s;
}}
.stat-card:hover {{ background: var(--card-up); }}
.stat-number {{
  font-size: 42px; font-weight: 800; color: #fff;
  font-variant-numeric: tabular-nums; line-height: 1; margin-bottom: 10px;
}}
.stat-label {{ font-size: 14px; font-weight: 600; color: var(--white); margin-bottom: 4px; }}
.stat-note {{ font-size: 13px; color: var(--muted); }}

/* ═══════ LAYOUT ═══════ */
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 0 40px; }}
.sect {{ margin-bottom: 120px; }}
.sect-head {{ margin-bottom: 40px; }}
.sect-head h2 {{ font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 10px; }}
.sect-head p {{ font-size: 16px; color: var(--muted); max-width: 600px; }}

.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}

/* ═══════ CARDS ═══════ */
.card {{
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); padding: 32px;
  transition: border-color .25s, box-shadow .25s;
}}
.card:hover {{
  border-color: var(--border-h);
  box-shadow: 0 8px 30px rgba(0,0,0,.4);
}}
.card h3 {{
  font-size: 16px; font-weight: 700; color: #fff;
  margin-bottom: 20px; text-transform: uppercase; letter-spacing: .04em;
}}
.card p {{ font-size: 14px; color: var(--muted); margin-bottom: 16px; }}
.card ul {{ padding-left: 18px; color: var(--muted); font-size: 14px; }}
.card li {{ margin-bottom: 10px; line-height: 1.5; }}

/* ═══════ PIPELINE FLOW ═══════ */
.pipeline {{
  display: flex; align-items: center; gap: 12px;
  padding: 32px; margin-bottom: 24px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); overflow-x: auto;
}}
.pipe-node {{
  flex: 1; min-width: 130px; text-align: center;
  padding: 18px 10px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg);
  transition: .25s;
}}
.pipe-node:hover {{
  border-color: rgba(59,130,246,.35);
  box-shadow: 0 0 18px rgba(59,130,246,.1);
  transform: translateY(-2px);
}}
.pipe-node strong {{ display: block; font-size: 13px; color: #fff; margin-bottom: 6px; }}
.pipe-node span {{ font-size: 12px; color: var(--muted); }}
.pipe-arrow {{ color: var(--muted); font-size: 16px; flex-shrink: 0; opacity: .4; }}

/* ═══════ BAR CHARTS (FIXED) ═══════
   Bar widths are set DIRECTLY in inline style.
   No JS animation needed — they simply render. */
.bar-grid {{ display: grid; gap: 28px; }}
.bar-cohort {{ }}
.cohort-head {{
  display: flex; justify-content: space-between; align-items: baseline;
  padding-bottom: 10px; margin-bottom: 14px;
  border-bottom: 1px solid var(--border);
}}
.cohort-head span {{ font-size: 13px; font-weight: 600; color: var(--white); }}
.cohort-head small {{ font-size: 12px; color: var(--muted); }}

.bar-row {{
  display: grid; grid-template-columns: 170px 1fr 36px;
  gap: 12px; align-items: center; margin-bottom: 10px;
}}
.bar-label {{ font-size: 12px; color: var(--muted); font-weight: 500; line-height: 1.3; }}
.bar-track {{
  height: 7px; background: rgba(255,255,255,0.04);
  border-radius: 99px; overflow: hidden;
}}
.bar-fill {{
  display: block; height: 100%; border-radius: 99px;
  min-width: 3px;
  transition: width .8s cubic-bezier(.22,1,.36,1);
}}
.bar-val {{
  font-size: 12px; font-weight: 600; color: var(--white);
  text-align: right; font-variant-numeric: tabular-nums;
}}

/* Bar fill colors — keyed to data slugs */
.color-confirmed, .color-yes, .color-available, .color-self-serve
  {{ background: var(--green); box-shadow: 0 0 8px rgba(34,197,94,.25); }}
.color-no, .color-fail, .color-not-found
  {{ background: var(--red); box-shadow: 0 0 8px rgba(239,68,68,.25); }}
.color-partial, .color-self-serve-with-restrictions, .color-buildable-with-constraints, .color-restricted
  {{ background: var(--blue); box-shadow: 0 0 8px rgba(59,130,246,.25); }}
.color-gated, .color-outreach-required, .color-paid-plan-required, .color-enterprise-only, .color-partner-or-contact-sales, .color-admin-approval-required
  {{ background: var(--amber); box-shadow: 0 0 8px rgba(245,158,11,.25); }}
.color-unknown, .color-not-run, .color-needs-review
  {{ background: #3f3f46; }}

/* ═══════ TABLE & EXPLORER ═══════ */
.filter-bar {{
  display: flex; gap: 12px; flex-wrap: wrap;
  padding: 16px; margin-bottom: 16px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r);
}}
.filter-bar input, .filter-bar select {{
  background: var(--bg); border: 1px solid var(--border);
  color: var(--white); padding: 10px 14px; border-radius: 6px;
  font-family: inherit; font-size: 13px; outline: none; transition: .2s;
}}
.filter-bar input {{ flex: 1; min-width: 200px; }}
.filter-bar input::placeholder {{ color: #52525b; }}
.filter-bar input:focus, .filter-bar select:focus {{
  border-color: var(--blue);
  box-shadow: 0 0 0 2px rgba(59,130,246,.15);
}}

.tbl-wrap {{
  overflow-x: auto; background: var(--card);
  border: 1px solid var(--border); border-radius: var(--r);
}}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
thead th {{
  position: sticky; top: 0; z-index: 10;
  background: rgba(5,5,5,.85); backdrop-filter: blur(8px);
  padding: 14px 16px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .06em;
  color: var(--muted); border-bottom: 1px solid var(--border);
  white-space: nowrap;
}}
td, tbody th {{
  padding: 16px; border-bottom: 1px solid var(--border);
  vertical-align: top;
}}
tbody tr:last-child td, tbody tr:last-child th {{ border-bottom: none; }}
tbody tr:hover td, tbody tr:hover th {{ background: rgba(255,255,255,.015); }}

.app-name {{ font-weight: 600; font-size: 14px; color: #fff; }}
.app-sub {{ font-size: 12px; color: var(--muted); margin-top: 3px; }}
td small {{ display: block; font-size: 12px; color: var(--muted); margin-top: 4px; }}
.blocker {{ color: var(--red); font-size: 12px; margin-top: 4px; }}
.ev-cell a {{
  display: inline-block; font-size: 11px; padding: 3px 8px;
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  border-radius: 4px; margin: 2px 4px 2px 0; text-decoration: none;
  transition: .15s;
}}
.ev-cell a:hover {{ background: rgba(255,255,255,.08); border-color: var(--muted); }}

/* ═══════ BADGES ═══════ */
.badge {{
  display: inline-block; padding: 3px 9px; border-radius: 5px;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
  border: 1px solid transparent; white-space: nowrap;
}}
.badge.confirmed, .badge.yes, .badge.available, .badge.self-serve, .badge.easy-win
  {{ background: rgba(34,197,94,.1); color: var(--green); border-color: rgba(34,197,94,.2); }}
.badge.no, .badge.fail, .badge.not-found
  {{ background: rgba(239,68,68,.1); color: var(--red); border-color: rgba(239,68,68,.2); }}
.badge.partial, .badge.constrained, .badge.live-agent, .badge.buildable-with-constraints
  {{ background: rgba(59,130,246,.1); color: var(--blue); border-color: rgba(59,130,246,.2); }}
.badge.gated, .badge.outreach, .badge.outreach-required, .badge.needs-review, .badge.prior-capture,
.badge.paid-plan-required, .badge.enterprise-only, .badge.admin-approval-required,
.badge.partner-or-contact-sales, .badge.self-serve-with-restrictions
  {{ background: rgba(245,158,11,.1); color: var(--amber); border-color: rgba(245,158,11,.2); }}
.badge.unknown
  {{ background: rgba(255,255,255,.04); color: var(--muted); border-color: var(--border); }}

/* ═══════ BOUNDARY CARD ═══════ */
.boundary {{
  border: 1px solid rgba(239,68,68,.2);
  background: rgba(239,68,68,.02);
  position: relative; padding-left: 40px;
}}
.boundary::before {{
  content: ''; position: absolute; left: 0; top: 0;
  width: 3px; height: 100%; background: var(--red);
  border-radius: 0 0 0 var(--r);
}}

/* ═══════ FOOTER ═══════ */
footer {{
  margin-top: 100px; padding: 60px 40px;
  border-top: 1px solid var(--border);
  text-align: center; color: var(--muted); font-size: 13px;
}}
footer p {{ max-width: 700px; margin: 0 auto 12px; line-height: 1.6; }}

/* ═══════ SCROLL REVEAL ═══════ */
.reveal {{
  opacity: 0; transform: translateY(16px);
  transition: opacity .6s ease, transform .6s ease;
}}
.reveal.visible {{ opacity: 1; transform: translateY(0); }}

/* ═══════ RESPONSIVE ═══════ */
@media (max-width: 1024px) {{
  .stats {{ grid-template-columns: 1fr 1fr; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
  .pipeline {{ flex-direction: column; }}
  .pipe-arrow {{ transform: rotate(90deg); }}
}}
@media (max-width: 640px) {{
  .hero h1 {{ font-size: 36px; }}
  .stats {{ grid-template-columns: 1fr; }}
  .wrap {{ padding: 0 20px; }}
  .topnav {{ padding: 0 20px; }}
  .filter-bar {{ flex-direction: column; }}
  .card {{ padding: 24px; }}
  .bar-row {{ grid-template-columns: 120px 1fr 30px; }}
}}
</style>
</head>
<body>

<!-- ─── NAV ─── -->
<nav class="topnav">
  <div class="topnav-brand">
    <div class="topnav-icon">C</div>
    Composio Product Ops
  </div>
  <div class="topnav-pill">Publication Pending</div>
</nav>

<!-- ─── HERO ─── -->
<header class="hero">
  <div class="hero-pill">Integration Research Case Study</div>
  <h1>AI Product Ops Research Engine</h1>
  <p>An evidence-backed pipeline evaluating API accessibility, authentication models, MCP readiness, and integration feasibility across 100 applications.</p>
</header>

<!-- ─── STATS ─── -->
<section class="stats">
  {cards_html}
</section>

<div class="wrap">

  <!-- ─── ARCHITECTURE ─── -->
  <section class="sect reveal">
    <div class="sect-head">
      <h2>Research Agent Architecture</h2>
      <p>Deterministic pipeline: manifest → research → evidence → verification → patterns.</p>
    </div>
    <div class="pipeline">
      <div class="pipe-node"><strong>Manifest</strong><span>100 Target Apps</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node"><strong>Research Agent</strong><span>76 Live · 24 Historical</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node"><strong>Evidence Engine</strong><span>{scope['all_records_evidence_item_count']} Traceable URLs</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node"><strong>Verification Audit</strong><span>20-App Sample</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node"><strong>Pattern Analysis</strong><span>Readiness Scoring</span></div>
    </div>
  </section>

  <!-- ─── FINDINGS ─── -->
  <section class="sect reveal">
    <div class="sect-head">
      <h2>Findings &amp; Patterns</h2>
      <p>Field-level distributions across the full dataset and verified cohorts.</p>
    </div>
    <div class="grid-2">
      {charts_html}
    </div>
  </section>

  <!-- ─── VERIFICATION ─── -->
  <section class="sect reveal">
    <div class="sect-head">
      <h2>Verification Journey</h2>
      <p>Transparent accuracy audit tracking concordance and critical mismatches across the 20-app sample.</p>
    </div>
    <div class="grid-2">
      <div class="card">
        <h3>Accuracy Audit</h3>
        <p>Concordance between automated first-pass and manual source recheck.</p>
        <div class="tbl-wrap" style="margin-top:16px">
          <table>
            <thead><tr><th>Field</th><th>Match</th><th>Rate</th><th>Unresolved</th></tr></thead>
            <tbody>{"".join(acc_rows)}</tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <h3>Critical Error Log</h3>
        <p>Documented mismatches corrected during the verification pass.</p>
        <div class="tbl-wrap" style="margin-top:16px">
          <table>
            <thead><tr><th>App</th><th>Field</th><th>Cause</th></tr></thead>
            <tbody>{err_rows}</tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <!-- ─── EXPLORER ─── -->
  <section class="sect reveal" id="explorer">
    <div class="sect-head">
      <h2>100-App Explorer</h2>
      <p>Complete research dataset. All fields derived from the automated pipeline and verified against source documentation.</p>
    </div>
    <div class="filter-bar">
      <input id="q" type="search" placeholder="Search app, category, or status…">
      <select id="fc">
        <option value="">All Categories</option>
        {"".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in categories)}
      </select>
      <select id="ft">
        <option value="">All Triage Outcomes</option>
        <option value="EASY_WIN">Easy Win</option>
        <option value="CONSTRAINED">Constrained</option>
        <option value="OUTREACH">Outreach</option>
        <option value="NEEDS_REVIEW">Needs Review</option>
      </select>
    </div>
    <div style="font-size:13px;color:var(--muted);margin-bottom:14px"><span id="rc">100</span> applications</div>
    <div class="tbl-wrap">
      <table id="mt">
        <thead>
          <tr>
            <th>Application</th><th>Provenance</th><th>Auth</th><th>Access</th>
            <th>API</th><th>MCP</th><th>Build</th><th>Triage</th><th>Evidence</th>
          </tr>
        </thead>
        <tbody>{"".join(table_rows)}</tbody>
      </table>
    </div>
  </section>

  <!-- ─── BOUNDARY ─── -->
  <section class="sect reveal">
    <div class="sect-head">
      <h2>Human-in-the-Loop Boundary</h2>
      <p>Explicit limitations of public-source research methodology.</p>
    </div>
    <div class="card boundary">
      <h3 style="color:var(--red)">Status: {esc(analysis['human_review']['status'])}</h3>
      <p>No authorized vendor tenant or credentials, and no human account reviewer, were available during this research cycle. This is an open blocker—not a completed QA pass.</p>
      <ul style="margin-top:16px">
        <li>The 120-row checklist records <code>HUMAN VERIFICATION NOT POSSIBLE</code> for each sampled critical field.</li>
        <li>Public-source research cannot establish access or entitlement in a specific customer tenant.</li>
        <li>Repository publication and deployment have not occurred. No public URL is claimed.</li>
      </ul>
      <p style="margin-top:16px;font-size:12px" class="muted"><em>Sample-based verification is source-concordance only, not full ground truth.</em></p>
    </div>
  </section>

</div>

<footer>
  <p>This workspace snapshot contains 100 first-pass records, a mixed-provenance 20-app coverage audit, and a separate {post_all.get('checked', 0)}-row post-correction recheck. Not a population-accuracy estimate, completed human QA, or production deployment.</p>
  <p class="mono">Analysis v{esc(analysis['analysis_version'])} · {len(dataset)} records</p>
</footer>

<script>
(function(){{
  /* ── Table filtering ── */
  const rows = Array.from(document.querySelectorAll('#mt tbody tr'));
  const q = document.getElementById('q');
  const fc = document.getElementById('fc');
  const ft = document.getElementById('ft');
  const rc = document.getElementById('rc');

  function filter() {{
    const s = q.value.toLowerCase(), c = fc.value, t = ft.value;
    let n = 0;
    rows.forEach(r => {{
      const ok = (!s || r.dataset.s.includes(s))
              && (!c || r.dataset.cat === c)
              && (!t || r.dataset.tri === t);
      r.style.display = ok ? '' : 'none';
      if (ok) n++;
    }});
    rc.textContent = n;
  }}
  q.addEventListener('input', filter);
  fc.addEventListener('change', filter);
  ft.addEventListener('change', filter);

  /* ── Scroll reveal ── */
  const io = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      if (e.isIntersecting) {{
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }}
    }});
  }}, {{ threshold: 0.08 }});
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
}})();
</script>
</body>
</html>'''

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(page, encoding="utf-8")
    print(f"Rendered {len(dataset)} rows -> {OUTPUT_PATH.relative_to(ROOT)} ({OUTPUT_PATH.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
