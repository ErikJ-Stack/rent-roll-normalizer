"""
Track 4 / Phase 0 — build mapping artifacts from registry.json.

Reads `tools/uw_template/registry.json` and emits, alongside it:
  - `mapping_mindmap.html`   — self-contained interactive visualizer
  - `MAPPING_TRACKER.md`     — human-readable tracker
  - `mapping_tracker.csv`    — diffable CSV (one row per concept × template version)

Modular by design: extending the registry with a new template version (e.g. "v5") under
`templates` and adding `"v5": {...}` target entries to each concept regenerates all three
artifacts without code changes here.

Run:
    python tools/uw_template/build_mapping_artifacts.py
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry.json"

STATUS_COLOR = {
    "mapped": "#1f6b52",
    "proposed": "#c78a18",
    "gap_source": "#a0322a",
    "gap_target": "#a0322a",
    "header_only": "#888888",
    "manual": "#5a4a8a",
    "derived": "#2a5f8a",
    "decided_pending_upstream": "#d05a3c",
    "substrate_ready_parser_pending": "#a37418",
}

CATEGORY_ORDER = [
    # t12 path
    "metadata", "capacity", "revenue", "waterfall",
    "labor", "nonlabor", "mgmt_noi",
    # rent_roll path
    "rr_identity", "rr_dates", "rr_rates",
    "rr_ancillary", "rr_subtotals", "rr_other",
    # ar path
    "ar_aging",
]

PATH_ORDER = ["t12", "rent_roll", "ar"]
PATH_LABEL = {
    "t12": "T-12 Path · UW Output → T-12 Analysis",
    "rent_roll": "Rent Roll Path · Rent Roll Input → Rent Roll Analysis row 211+",
    "ar": "AR Path · AR & Collections → Rent Roll Analysis cols N–Q",
}


def load_registry() -> dict:
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def fmt_source(src: dict) -> str:
    sys = src.get("system", "?")
    if sys == "uw_output":
        col = src.get("column", "")
        row = src.get("row", "")
        return f"UW Output!{col}{row}" if row else "UW Output"
    if sys == "rr_input":
        col = src.get("column", "")
        addr = src.get("address", "")
        return f"Rent Roll Input!{addr}" if addr else f"Rent Roll Input col {col}"
    if sys == "named_range":
        return f"@{src.get('name')} → {src.get('resolves_to', '?')}"
    if sys == "cell":
        return f"{src.get('sheet')}!{src.get('address')}"
    if sys == "derived":
        return "derived"
    if sys == "gap":
        return "—  (not in Analyzer)"
    return sys


def fmt_target(tgt: dict | None) -> str:
    if not tgt:
        return "—"
    return f"{tgt.get('sheet')}!{tgt.get('address')}"


def write_csv(reg: dict, path: Path) -> None:
    template_versions = sorted(reg["templates"].keys())
    headers = [
        "path", "key", "label", "category", "status",
        "source_system", "source_sheet", "source_address", "source_label",
    ]
    for tv in template_versions:
        headers += [f"target_{tv}_sheet", f"target_{tv}_address", f"target_{tv}_label"]
    headers += ["notes"]

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in reg["concepts"]:
            src = c.get("source", {})
            row = [
                c.get("path", "t12"),
                c["key"], c.get("label", ""), c.get("category", ""), c.get("status", ""),
                src.get("system", ""),
                src.get("sheet", "") or src.get("name", ""),
                src.get("address", "") or (
                    f"{src.get('column','')}{src.get('row','')}" if src.get("row") else ""
                ),
                src.get("label", ""),
            ]
            for tv in template_versions:
                t = (c.get("targets") or {}).get(tv)
                if t:
                    row += [t.get("sheet", ""), t.get("address", ""), t.get("label_at", "") or t.get("target_label", "")]
                else:
                    row += ["", "", ""]
            row.append(c.get("notes", ""))
            w.writerow(row)


def write_markdown(reg: dict, path: Path) -> None:
    template_versions = sorted(reg["templates"].keys())
    tv_primary = template_versions[0]  # primary template version for the readable tracker

    lines: list[str] = []
    lines.append("# ALF UW Template — Mapping Tracker")
    lines.append("")
    lines.append(f"> Generated from `tools/uw_template/registry.json` on "
                 f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.  "
                 f"**Do not edit by hand** — edit `registry.json` and re-run "
                 f"`python tools/uw_template/build_mapping_artifacts.py`.")
    lines.append("")
    lines.append(f"- Analyzer source: `{reg['analyzer']['file']}` (substrate "
                 f"`{reg['analyzer']['substrate_version']}`)")
    lines.append(f"- Primary template: `{tv_primary}` → "
                 f"`{reg['templates'][tv_primary]['file']}`")
    lines.append(f"- Intake sheets: " + ", ".join(
        f"`{s}`" for s in reg['templates'][tv_primary]['intake_sheets']))
    lines.append("")
    lines.append("## Status legend")
    lines.append("")
    for k, v in reg["status_legend"].items():
        lines.append(f"- **`{k}`** — {v}")
    lines.append("")

    # Status rollup
    counts: dict[str, int] = {}
    for c in reg["concepts"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    lines.append("## Status rollup")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---|")
    for k in sorted(counts.keys(), key=lambda s: -counts[s]):
        lines.append(f"| `{k}` | {counts[k]} |")
    lines.append(f"| **Total concepts** | **{sum(counts.values())}** |")
    lines.append("")

    # By path × category
    by_path: dict[str, dict[str, list[dict]]] = {}
    for c in reg["concepts"]:
        p = c.get("path", "t12")
        cat = c.get("category", "other")
        by_path.setdefault(p, {}).setdefault(cat, []).append(c)

    # path-level status rollup
    lines.append("## Status rollup by path")
    lines.append("")
    lines.append("| Path | Total | mapped | gap_target | gap_source | proposed | other |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in PATH_ORDER:
        if p not in by_path:
            continue
        items = [c for cs in by_path[p].values() for c in cs]
        cnt: dict[str, int] = {}
        for c in items:
            cnt[c["status"]] = cnt.get(c["status"], 0) + 1
        other = sum(v for k, v in cnt.items()
                    if k not in {"mapped", "gap_target", "gap_source", "proposed"})
        lines.append(
            f"| **{p}** | {len(items)} | {cnt.get('mapped',0)} | "
            f"{cnt.get('gap_target',0)} | {cnt.get('gap_source',0)} | "
            f"{cnt.get('proposed',0)} | {other} |"
        )
    lines.append("")

    lines.append("## Mappings by path & category")
    lines.append("")
    ordered_cats = CATEGORY_ORDER
    for p in PATH_ORDER:
        if p not in by_path:
            continue
        lines.append(f"### {PATH_LABEL.get(p, p).upper()}")
        lines.append("")
        path_cats = by_path[p]
        cats = [c for c in ordered_cats if c in path_cats] + sorted(
            set(path_cats.keys()) - set(ordered_cats)
        )
        for cat in cats:
            items = path_cats[cat]
            lines.append(f"#### {cat} ({len(items)})")
            lines.append("")
            lines.append("| Concept | Source | Target (`" + tv_primary + "`) | Status | Notes |")
            lines.append("|---|---|---|---|---|")
            for c in items:
                src = fmt_source(c.get("source", {}))
                tgt = fmt_target((c.get("targets") or {}).get(tv_primary))
                notes = (c.get("notes") or "").replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| **{c['label']}** <br/> `{c['key']}` | `{src}` | "
                    f"`{tgt}` | `{c['status']}` | {notes} |"
                )
            lines.append("")

    lines.append("## Unmapped template intake (rows the writer does NOT populate)")
    lines.append("")
    for u in reg.get("intake_targets_unmapped", []):
        sheet = u.get("sheet", "")
        kind = u.get("kind", "")
        rng = u.get("rows_range") or u.get("monthly_cols") or u.get("rows") or "—"
        notes = u.get("notes", "")
        lines.append(f"- **`{sheet}`** ({kind}) — {rng}: {notes}")
    lines.append("")

    lines.append("## Open questions")
    lines.append("")
    for q in reg.get("open_questions", []):
        lines.append(f"- {q}")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(reg: dict, path: Path) -> None:
    template_versions = sorted(reg["templates"].keys())
    tv_primary = template_versions[0]
    registry_inline = json.dumps(reg, ensure_ascii=False)

    counts: dict[str, int] = {}
    for c in reg["concepts"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    rollup_html = " ".join(
        f'<span class="pill pill-{escape(k)}">{escape(k)} · {v}</span>'
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>ALF UW Template — Mapping Mind Map (Track 4 / Phase 0)</title>
<style>
  :root {{
    --bg: #f7f7f5;
    --fg: #232323;
    --muted: #777;
    --card: #fff;
    --border: #e2e0db;
    --accent: #1f4e79;
    --mapped: #1f6b52;
    --proposed: #c78a18;
    --gap: #a0322a;
    --header_only: #888;
    --manual: #5a4a8a;
    --derived: #2a5f8a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--fg);
    margin: 0;
    line-height: 1.45;
  }}
  header {{
    background: var(--accent);
    color: #fff;
    padding: 18px 28px;
  }}
  header h1 {{ margin: 0 0 4px 0; font-size: 22px; font-weight: 600; }}
  header .sub {{ font-size: 13px; opacity: .85; }}
  .toolbar {{
    background: #fff;
    border-bottom: 1px solid var(--border);
    padding: 12px 28px;
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
    align-items: center;
    font-size: 13px;
  }}
  .toolbar label {{ display: flex; gap: 6px; align-items: center; }}
  .toolbar input[type="text"] {{
    padding: 6px 10px;
    border: 1px solid var(--border);
    border-radius: 4px;
    min-width: 240px;
    font-size: 13px;
  }}
  .toolbar select {{
    padding: 5px 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: #fff;
    font-size: 13px;
  }}
  .pill {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    color: #fff;
    background: var(--muted);
    margin-right: 4px;
  }}
  .pill-mapped {{ background: var(--mapped); }}
  .pill-proposed {{ background: var(--proposed); }}
  .pill-gap_source, .pill-gap_target {{ background: var(--gap); }}
  .pill-header_only {{ background: var(--header_only); }}
  .pill-manual {{ background: var(--manual); }}
  .pill-derived {{ background: var(--derived); }}
  .pill-decided_pending_upstream {{ background: #d05a3c; }}
  .pill-substrate_ready_parser_pending {{ background: #a37418; }}

  .path-tag {{
    display: inline-block;
    padding: 1px 7px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    margin-right: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }}
  .path-t12        {{ background: #d6e4f0; color: #1f4e79; }}
  .path-rent_roll  {{ background: #d8eedb; color: #1f6b52; }}
  .path-ar         {{ background: #f4dcd4; color: #8a3a18; }}

  main {{ padding: 16px 28px 60px; }}

  .path-block {{
    margin-bottom: 36px;
  }}
  .path-header {{
    margin: 0 0 10px 0;
    padding: 12px 16px;
    border-radius: 6px;
    font-size: 14px;
    color: #222;
    background: #ecebe6;
    border-left: 4px solid var(--accent);
  }}
  .path-block[data-path="t12"] .path-header        {{ border-left-color: #1f4e79; background: #eaf1f8; }}
  .path-block[data-path="rent_roll"] .path-header  {{ border-left-color: #1f6b52; background: #ebf3ee; }}
  .path-block[data-path="ar"] .path-header         {{ border-left-color: #8a3a18; background: #f6ebe5; }}

  section.category {{
    margin-bottom: 12px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  section.category > h2 {{
    margin: 0;
    padding: 12px 18px;
    background: #ecebe6;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #333;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    user-select: none;
  }}
  section.category > h2 .count {{
    color: var(--muted);
    font-weight: normal;
    margin-left: 8px;
    font-size: 12px;
    letter-spacing: 0;
    text-transform: none;
  }}
  section.category.collapsed .grid {{ display: none; }}

  .grid {{
    display: grid;
    grid-template-columns: 1fr 32px 1fr;
    gap: 0;
    padding: 8px 0;
  }}
  .row {{
    display: contents;
  }}
  .row .source, .row .target, .row .link {{
    border-bottom: 1px solid #f1efe9;
    padding: 10px 14px;
    font-size: 13px;
  }}
  .row:last-child .source, .row:last-child .target, .row:last-child .link {{
    border-bottom: none;
  }}
  .row .source {{
    background: #fbfaf7;
    border-right: 1px solid #f1efe9;
  }}
  .row .target {{
    border-left: 1px solid #f1efe9;
  }}
  .row .link {{
    text-align: center;
    color: var(--muted);
    background: #fbfaf7;
    border-right: 1px solid #f1efe9;
    border-left: 1px solid #f1efe9;
    padding: 10px 4px;
    font-size: 11px;
    line-height: 1.2;
  }}
  .row .arrow {{
    display: block;
    font-size: 18px;
    color: var(--accent);
  }}
  .label {{
    font-weight: 600;
    color: #222;
    margin-bottom: 2px;
  }}
  .addr {{
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 12px;
    color: #555;
  }}
  .notes {{
    font-size: 12px;
    color: #555;
    margin-top: 6px;
    line-height: 1.35;
  }}
  .key {{
    font-family: ui-monospace, monospace;
    font-size: 11px;
    color: var(--muted);
  }}
  .row.hidden {{ display: none; }}
  .row.gap_source .source, .row.gap_target .target {{
    background: #fcf3f2;
  }}
  .row.gap_target .target, .row.gap_source .source {{
    border-left: 3px solid var(--gap);
  }}

  .meta {{
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    font-size: 13px;
  }}
  .meta strong {{ color: #333; }}
  .meta code {{
    font-family: ui-monospace, monospace;
    background: #f1efe9;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
  }}
  details {{ margin-top: 6px; }}
  details summary {{ cursor: pointer; color: var(--accent); font-weight: 500; }}
  details ul {{ margin: 6px 0 0 0; padding-left: 18px; }}
  details li {{ margin: 4px 0; font-size: 13px; color: #444; }}

  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 20px;
  }}
</style>
</head>
<body>
<header>
  <h1>ALF UW Template — Mapping Mind Map</h1>
  <div class="sub">Track 4 · Phase 0 (inspection only — no writer yet)</div>
</header>

<div class="toolbar">
  <label>Search <input id="q" type="text" placeholder="label, key, sheet, address..."/></label>
  <label>Path
    <select id="path">
      <option value="">all paths</option>
      <option value="t12">T-12</option>
      <option value="rent_roll">Rent Roll</option>
      <option value="ar">AR</option>
    </select>
  </label>
  <label>Status
    <select id="status">
      <option value="">all</option>
      <option value="mapped">mapped</option>
      <option value="proposed">proposed</option>
      <option value="gap_source">gap_source</option>
      <option value="gap_target">gap_target</option>
      <option value="header_only">header_only</option>
      <option value="manual">manual</option>
      <option value="derived">derived</option>
      <option value="decided_pending_upstream">decided_pending_upstream</option>
      <option value="substrate_ready_parser_pending">substrate_ready_parser_pending</option>
    </select>
  </label>
  <label>Template version
    <select id="tv">
      {''.join(f'<option value="{escape(v)}">{escape(v)}</option>' for v in template_versions)}
    </select>
  </label>
  <span style="flex:1"></span>
  <span>{rollup_html}</span>
</div>

<main>

<div class="meta">
  <div><strong>Analyzer:</strong> <code>{escape(reg['analyzer']['file'])}</code>
       (substrate <code>{escape(reg['analyzer']['substrate_version'])}</code>)</div>
  <div><strong>Template:</strong> <code id="tplFile">{escape(reg['templates'][tv_primary]['file'])}</code></div>
  <div><strong>Intake sheets:</strong>
       <code>{escape(', '.join(reg['templates'][tv_primary]['intake_sheets']))}</code></div>

  <details>
    <summary>Open questions ({len(reg.get('open_questions',[]))})</summary>
    <ul>
      {''.join(f'<li>{escape(q)}</li>' for q in reg.get('open_questions',[]))}
    </ul>
  </details>

  <details>
    <summary>Unmapped template intake</summary>
    <ul>
      {''.join(
        f"<li><code>{escape(u.get('sheet','?'))}</code> "
        f"<em>({escape(u.get('kind','?'))})</em> — "
        f"{escape(str(u.get('rows_range') or u.get('monthly_cols') or u.get('rows') or ''))}"
        f": {escape(u.get('notes',''))}</li>"
        for u in reg.get('intake_targets_unmapped',[])
      )}
    </ul>
  </details>
</div>

<div id="map"></div>
</main>

<footer>
  Built from <code>tools/uw_template/registry.json</code> · Generated
  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</footer>

<script>
const REGISTRY = {registry_inline};

const CATEGORY_ORDER = {json.dumps(CATEGORY_ORDER)};
const PATH_ORDER = {json.dumps(PATH_ORDER)};
const PATH_LABEL = {json.dumps(PATH_LABEL)};

function fmtSource(src) {{
  if (!src) return '—';
  if (src.system === 'uw_output') {{
    const col = src.column || '';
    const row = src.row || '';
    return row ? `UW Output!${{col}}${{row}}` : 'UW Output';
  }}
  if (src.system === 'rr_input') {{
    return src.address ? `Rent Roll Input!${{src.address}}` : `Rent Roll Input col ${{src.column || '?'}}`;
  }}
  if (src.system === 'named_range') return `@${{src.name}} → ${{src.resolves_to || '?'}}`;
  if (src.system === 'cell') return `${{src.sheet}}!${{src.address}}`;
  if (src.system === 'derived') return 'derived';
  if (src.system === 'gap') return '—  (not in Analyzer)';
  return src.system || '—';
}}

function fmtTarget(tgt) {{
  if (!tgt) return '—';
  return `${{tgt.sheet}}!${{tgt.address}}`;
}}

function targetLabel(tgt) {{
  if (!tgt) return '';
  return tgt.target_label || tgt.label_at || '';
}}

function render() {{
  const tv = document.getElementById('tv').value;
  document.getElementById('tplFile').textContent = REGISTRY.templates[tv].file;

  // bucket by path → category
  const byPath = {{}};
  for (const c of REGISTRY.concepts) {{
    const p = c.path || 't12';
    (byPath[p] ||= {{}});
    (byPath[p][c.category || 'other'] ||= []).push(c);
  }}

  const root = document.getElementById('map');
  root.innerHTML = '';

  const pathOrder = [...PATH_ORDER, ...Object.keys(byPath).filter(p => !PATH_ORDER.includes(p))];
  for (const p of pathOrder) {{
    if (!byPath[p]) continue;
    const pathBlock = document.createElement('div');
    pathBlock.className = 'path-block';
    pathBlock.dataset.path = p;

    const pathH = document.createElement('h2');
    pathH.className = `path-header path-${{p}}-bg`;
    const total = Object.values(byPath[p]).reduce((s, a) => s + a.length, 0);
    pathH.innerHTML = `
      <span class="path-tag path-${{p}}">${{p.replace('_',' ')}}</span>
      ${{PATH_LABEL[p] || p}}
      <span class="count" style="color:#888; font-weight:normal; font-size:13px; margin-left:10px;">
        ${{total}} concepts
      </span>
    `;
    pathBlock.appendChild(pathH);

    const cats = byPath[p];
    const order = [...CATEGORY_ORDER, ...Object.keys(cats).filter(k => !CATEGORY_ORDER.includes(k))];
    for (const cat of order) {{
      const items = cats[cat];
      if (!items) continue;
      const sec = document.createElement('section');
      sec.className = 'category';
      sec.dataset.cat = cat;
      sec.dataset.path = p;

      const h3 = document.createElement('h2');
      h3.innerHTML = `${{cat.toUpperCase()}}<span class="count">${{items.length}} concept${{items.length===1?'':'s'}}</span>`;
      h3.onclick = () => sec.classList.toggle('collapsed');
      sec.appendChild(h3);

      const grid = document.createElement('div');
      grid.className = 'grid';

      for (const c of items) {{
        const tgt = (c.targets || {{}})[tv];
        const row = document.createElement('div');
        row.className = `row ${{c.status}}`;
        row.dataset.key = c.key;
        row.dataset.path = p;
        row.dataset.search = [
          c.key, c.label, c.category, c.status, p,
          c.notes || '',
          fmtSource(c.source), fmtTarget(tgt),
          (tgt && (tgt.label_at || tgt.target_label)) || '',
        ].join(' ').toLowerCase();

        const src = document.createElement('div');
        src.className = 'source';
        src.innerHTML = `
          <span class="path-tag path-${{p}}">${{p.replace('_',' ')}}</span>
          <div class="label">${{c.label}}</div>
          <div class="addr">${{fmtSource(c.source)}}</div>
          <div class="key">${{c.key}}</div>
        `;

        const link = document.createElement('div');
        link.className = 'link';
        link.innerHTML = `
          <span class="arrow">→</span>
          <span class="pill pill-${{c.status}}">${{c.status}}</span>
        `;

        const tlabel = targetLabel(tgt);
        const tgt_div = document.createElement('div');
        tgt_div.className = 'target';
        if (tgt) {{
          tgt_div.innerHTML = `
            <div class="label">${{tlabel || c.label}}</div>
            <div class="addr">${{fmtTarget(tgt)}}</div>
            ${{c.notes ? `<div class="notes">${{c.notes}}</div>` : ''}}
          `;
        }} else {{
          tgt_div.innerHTML = `
            <div class="label" style="color:#a0322a">— no target —</div>
            ${{c.notes ? `<div class="notes">${{c.notes}}</div>` : ''}}
          `;
        }}

        row.appendChild(src);
        row.appendChild(link);
        row.appendChild(tgt_div);
        grid.appendChild(row);
      }}

      sec.appendChild(grid);
      pathBlock.appendChild(sec);
    }}

    root.appendChild(pathBlock);
  }}

  applyFilters();
}}

function applyFilters() {{
  const q = document.getElementById('q').value.trim().toLowerCase();
  const status = document.getElementById('status').value;
  const path = document.getElementById('path').value;
  document.querySelectorAll('.row').forEach(r => {{
    const matchesQ = !q || r.dataset.search.includes(q);
    const matchesS = !status || r.classList.contains(status);
    const matchesP = !path || r.dataset.path === path;
    r.classList.toggle('hidden', !(matchesQ && matchesS && matchesP));
  }});
  document.querySelectorAll('section.category').forEach(sec => {{
    const anyVisible = !!sec.querySelector('.row:not(.hidden)');
    sec.style.display = anyVisible ? '' : 'none';
  }});
  document.querySelectorAll('.path-block').forEach(pb => {{
    const anyVisible = !!pb.querySelector('.row:not(.hidden)');
    pb.style.display = anyVisible ? '' : 'none';
  }});
}}

document.getElementById('q').addEventListener('input', applyFilters);
document.getElementById('status').addEventListener('change', applyFilters);
document.getElementById('path').addEventListener('change', applyFilters);
document.getElementById('tv').addEventListener('change', render);
render();
</script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    reg = load_registry()
    write_csv(reg, ROOT / "mapping_tracker.csv")
    write_markdown(reg, ROOT / "MAPPING_TRACKER.md")
    write_html(reg, ROOT / "mapping_mindmap.html")
    n = len(reg["concepts"])
    tv = sorted(reg["templates"].keys())
    print(f"OK — {n} concepts emitted for template version(s): {', '.join(tv)}")
    print(f"  - tools/uw_template/mapping_tracker.csv")
    print(f"  - tools/uw_template/MAPPING_TRACKER.md")
    print(f"  - tools/uw_template/mapping_mindmap.html")


if __name__ == "__main__":
    main()
