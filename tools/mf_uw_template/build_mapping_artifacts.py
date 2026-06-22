"""
MF Track 4 / Phase 0 — build mapping artifacts from registry.json.

Reads `tools/mf_uw_template/registry.json` and emits, alongside it:
  - `mapping_mindmap.html`   — self-contained interactive visualizer
  - `MAPPING_TRACKER.md`     — human-readable tracker
  - `mapping_tracker.csv`    — diffable CSV (one row per concept × template version)

Modular by design: extending the registry with a new template version (e.g. "v16")
under `templates` and adding `"v16": {...}` target entries to each concept regenerates
all three artifacts without code changes here.

Mirrors the ALF generator at `tools/uw_template/build_mapping_artifacts.py`, adapted for
the MF intake paths (rent_roll → Rent Roll Analysis grid, t12 → T-12 Analysis Layer 1)
and the MF source systems (raw operator docs, no Analyzer substrate).

Run:
    python tools/mf_uw_template/build_mapping_artifacts.py
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry.json"


def _primary_template(reg: dict) -> str:
    """The binding/primary template = highest numeric version (e.g. v20 > v15).
    Honors an explicit `primary_template` registry key when present."""
    if reg.get("primary_template") in reg.get("templates", {}):
        return reg["primary_template"]
    return max(reg["templates"], key=lambda v: int("".join(filter(str.isdigit, v)) or 0))

STATUS_COLOR = {
    "mapped": "#1f6b52",
    "proposed": "#c78a18",
    "gap_source": "#a0322a",
    "gap_target": "#a0322a",
    "derived": "#2a5f8a",
    "manual": "#5a4a8a",
    "header_only": "#888888",
}

CATEGORY_ORDER = [
    # metadata
    "metadata",
    # rent_roll path
    "rr_identity", "rr_status", "rr_dates", "rr_rates",
    "rr_ar", "rr_ancillary", "rr_other",
    # t12 path
    "t12_raw", "t12_mapping", "t12_derived",
]

PATH_ORDER = ["metadata", "rent_roll", "t12"]
PATH_LABEL = {
    "metadata": "Metadata · Property / period → Prop Info + headers",
    "rent_roll": "Rent Roll Path · operator RR (+AR) → Rent Roll Analysis grid row 273+",
    "t12": "T-12 Path · operator T-12 → T-12 Analysis Layer 1 row 106+",
}


def load_registry() -> dict:
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def fmt_source(src: dict) -> str:
    sysname = src.get("system", "?")
    if sysname == "mf_rr":
        a = src.get("address") or src.get("column", "")
        return f"RR!{a}" if a else "RR"
    if sysname == "mf_rr_sortable":
        return f"Sortable-RR/{src.get('sheet', '?')}"
    if sysname == "mf_ar":
        a = src.get("column") or src.get("address", "")
        return f"AR!{a}" if a else "AR"
    if sysname == "mf_t12":
        a = src.get("address") or src.get("column", "")
        return f"T-12!{a}" if a else "T-12"
    if sysname == "cell":
        return f"{src.get('sheet')}!{src.get('address')}"
    if sysname == "derived":
        return "derived"
    if sysname == "gap":
        return "—  (no operator source)"
    if sysname == "manual":
        return "manual"
    return sysname


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
                c.get("path", ""),
                c["key"], c.get("label", ""), c.get("category", ""), c.get("status", ""),
                src.get("system", ""),
                src.get("sheet", "") or src.get("name", ""),
                src.get("address", "") or src.get("column", ""),
                src.get("label", ""),
            ]
            for tv in template_versions:
                t = (c.get("targets") or {}).get(tv)
                if t:
                    row += [t.get("sheet", ""), t.get("address", ""),
                            t.get("target_label", "") or t.get("label_at", "")]
                else:
                    row += ["", "", ""]
            row.append(c.get("notes", ""))
            w.writerow(row)


def write_markdown(reg: dict, path: Path) -> None:
    template_versions = sorted(reg["templates"].keys())
    tv_primary = _primary_template(reg)

    lines: list[str] = []
    lines.append("# MF UW Model — Mapping Tracker")
    lines.append("")
    lines.append(f"> Generated from `tools/mf_uw_template/registry.json` on "
                 f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.  "
                 f"**Do not edit by hand** — edit `registry.json` and re-run "
                 f"`python tools/mf_uw_template/build_mapping_artifacts.py`.")
    lines.append("")
    lines.append(f"- Product line: **MF** (multifamily). No Analyzer substrate — "
                 f"source is the raw operator docs in `MF Docs/`.")
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

    by_path: dict[str, dict[str, list[dict]]] = {}
    for c in reg["concepts"]:
        p = c.get("path", "")
        cat = c.get("category", "other")
        by_path.setdefault(p, {}).setdefault(cat, []).append(c)

    lines.append("## Status rollup by path")
    lines.append("")
    lines.append("| Path | Total | mapped | gap_source | proposed | other |")
    lines.append("|---|---|---|---|---|---|")
    for p in PATH_ORDER:
        if p not in by_path:
            continue
        items = [c for cs in by_path[p].values() for c in cs]
        cnt: dict[str, int] = {}
        for c in items:
            cnt[c["status"]] = cnt.get(c["status"], 0) + 1
        other = sum(v for k, v in cnt.items()
                    if k not in {"mapped", "gap_source", "proposed"})
        lines.append(
            f"| **{p}** | {len(items)} | {cnt.get('mapped',0)} | "
            f"{cnt.get('gap_source',0)} | {cnt.get('proposed',0)} | {other} |"
        )
    lines.append("")

    lines.append("## Mappings by path & category")
    lines.append("")
    for p in PATH_ORDER:
        if p not in by_path:
            continue
        lines.append(f"### {PATH_LABEL.get(p, p).upper()}")
        lines.append("")
        path_cats = by_path[p]
        cats = [c for c in CATEGORY_ORDER if c in path_cats] + sorted(
            set(path_cats.keys()) - set(CATEGORY_ORDER)
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

    lines.append("## Unmapped template surface (writer does NOT populate)")
    lines.append("")
    for u in reg.get("intake_targets_unmapped", []):
        sheet = u.get("sheet", "")
        kind = u.get("kind", "")
        rng = u.get("rows_range") or u.get("rows") or "—"
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
    tv_primary = _primary_template(reg)
    registry_inline = json.dumps(reg, ensure_ascii=False)

    counts: dict[str, int] = {}
    for c in reg["concepts"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    rollup_html = " ".join(
        f'<span class="pill pill-{escape(k)}">{escape(k)} · {v}</span>'
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    )

    status_options = "".join(
        f'<option value="{escape(k)}">{escape(k)}</option>' for k in STATUS_COLOR
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>MF UW Model — Mapping Mind Map (Track 4 / Phase 0)</title>
<style>
  :root {{
    --bg:#f7f7f5; --fg:#232323; --muted:#777; --card:#fff; --border:#e2e0db;
    --accent:#0070c0; --mapped:#1f6b52; --proposed:#c78a18; --gap:#a0322a;
    --derived:#2a5f8a; --manual:#5a4a8a;
  }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background:var(--bg); color:var(--fg); margin:0; line-height:1.45; }}
  header {{ background:var(--accent); color:#fff; padding:18px 28px; }}
  header h1 {{ margin:0 0 4px 0; font-size:22px; font-weight:600; }}
  header .sub {{ font-size:13px; opacity:.85; }}
  .toolbar {{ background:#fff; border-bottom:1px solid var(--border); padding:12px 28px;
    display:flex; gap:18px; flex-wrap:wrap; align-items:center; font-size:13px; }}
  .toolbar label {{ display:flex; gap:6px; align-items:center; }}
  .toolbar input[type="text"] {{ padding:6px 10px; border:1px solid var(--border);
    border-radius:4px; min-width:240px; font-size:13px; }}
  .toolbar select {{ padding:5px 8px; border:1px solid var(--border); border-radius:4px;
    background:#fff; font-size:13px; }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px;
    color:#fff; background:var(--muted); margin-right:4px; }}
  .pill-mapped {{ background:var(--mapped); }}
  .pill-proposed {{ background:var(--proposed); }}
  .pill-gap_source,.pill-gap_target {{ background:var(--gap); }}
  .pill-derived {{ background:var(--derived); }}
  .pill-manual {{ background:var(--manual); }}
  .pill-header_only {{ background:#888; }}
  .path-tag {{ display:inline-block; padding:1px 7px; border-radius:3px; font-size:10px;
    font-weight:600; margin-right:6px; letter-spacing:0.04em; text-transform:uppercase; }}
  .path-metadata   {{ background:#e7e3f0; color:#5a4a8a; }}
  .path-rent_roll  {{ background:#d8eedb; color:#1f6b52; }}
  .path-t12        {{ background:#d6e4f0; color:#1f4e79; }}
  main {{ padding:16px 28px 60px; }}
  .path-block {{ margin-bottom:36px; }}
  .path-header {{ margin:0 0 10px 0; padding:12px 16px; border-radius:6px; font-size:14px;
    color:#222; background:#ecebe6; border-left:4px solid var(--accent); }}
  .path-block[data-path="metadata"] .path-header  {{ border-left-color:#5a4a8a; background:#f0edf6; }}
  .path-block[data-path="rent_roll"] .path-header {{ border-left-color:#1f6b52; background:#ebf3ee; }}
  .path-block[data-path="t12"] .path-header       {{ border-left-color:#1f4e79; background:#eaf1f8; }}
  section.category {{ margin-bottom:12px; background:var(--card); border:1px solid var(--border);
    border-radius:8px; overflow:hidden; }}
  section.category > h2 {{ margin:0; padding:12px 18px; background:#ecebe6; font-size:14px;
    text-transform:uppercase; letter-spacing:0.04em; color:#333; border-bottom:1px solid var(--border);
    cursor:pointer; user-select:none; }}
  section.category > h2 .count {{ color:var(--muted); font-weight:normal; margin-left:8px;
    font-size:12px; letter-spacing:0; text-transform:none; }}
  section.category.collapsed .grid {{ display:none; }}
  .grid {{ display:grid; grid-template-columns:1fr 32px 1fr; gap:0; padding:8px 0; }}
  .row {{ display:contents; }}
  .row .source,.row .target,.row .link {{ border-bottom:1px solid #f1efe9; padding:10px 14px; font-size:13px; }}
  .row:last-child .source,.row:last-child .target,.row:last-child .link {{ border-bottom:none; }}
  .row .source {{ background:#fbfaf7; border-right:1px solid #f1efe9; }}
  .row .target {{ border-left:1px solid #f1efe9; }}
  .row .link {{ text-align:center; color:var(--muted); background:#fbfaf7; border-right:1px solid #f1efe9;
    border-left:1px solid #f1efe9; padding:10px 4px; font-size:11px; line-height:1.2; }}
  .row .arrow {{ display:block; font-size:18px; color:var(--accent); }}
  .label {{ font-weight:600; color:#222; margin-bottom:2px; }}
  .addr {{ font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace; font-size:12px; color:#555; }}
  .notes {{ font-size:12px; color:#555; margin-top:6px; line-height:1.35; }}
  .key {{ font-family:ui-monospace,monospace; font-size:11px; color:var(--muted); }}
  .row.hidden {{ display:none; }}
  .row.gap_source .source {{ background:#fcf3f2; border-left:3px solid var(--gap); }}
  .meta {{ background:#fff; border:1px solid var(--border); border-radius:8px; padding:14px 18px;
    margin-bottom:20px; font-size:13px; }}
  .meta strong {{ color:#333; }}
  .meta code {{ font-family:ui-monospace,monospace; background:#f1efe9; padding:1px 5px;
    border-radius:3px; font-size:12px; }}
  details {{ margin-top:6px; }}
  details summary {{ cursor:pointer; color:var(--accent); font-weight:500; }}
  details ul {{ margin:6px 0 0 0; padding-left:18px; }}
  details li {{ margin:4px 0; font-size:13px; color:#444; }}
  footer {{ text-align:center; color:var(--muted); font-size:12px; padding:20px; }}
</style>
</head>
<body>
<header>
  <h1>MF UW Model — Mapping Mind Map</h1>
  <div class="sub">MF Track 4 · Phase 0 (inspection only — no writer yet)</div>
</header>

<div class="toolbar">
  <label>Search <input id="q" type="text" placeholder="label, key, sheet, address..."/></label>
  <label>Path
    <select id="path">
      <option value="">all paths</option>
      <option value="metadata">Metadata</option>
      <option value="rent_roll">Rent Roll</option>
      <option value="t12">T-12</option>
    </select>
  </label>
  <label>Status
    <select id="status">
      <option value="">all</option>
      {status_options}
    </select>
  </label>
  <label>Template
    <select id="tv">
      {''.join(f'<option value="{escape(v)}">{escape(v)}</option>' for v in template_versions)}
    </select>
  </label>
  <span style="flex:1"></span>
  <span>{rollup_html}</span>
</div>

<main>
<div class="meta">
  <div><strong>Product line:</strong> MF (multifamily) — no Analyzer substrate; source is the raw operator docs in <code>MF Docs/</code></div>
  <div><strong>Template:</strong> <code id="tplFile">{escape(reg['templates'][tv_primary]['file'])}</code></div>
  <div><strong>Intake sheets:</strong>
       <code>{escape(', '.join(reg['templates'][tv_primary]['intake_sheets']))}</code></div>
  <details>
    <summary>Open questions ({len(reg.get('open_questions',[]))})</summary>
    <ul>{''.join(f'<li>{escape(q)}</li>' for q in reg.get('open_questions',[]))}</ul>
  </details>
  <details>
    <summary>Unmapped template surface</summary>
    <ul>{''.join(
      f"<li><code>{escape(u.get('sheet','?'))}</code> <em>({escape(u.get('kind','?'))})</em> — "
      f"{escape(str(u.get('rows_range') or u.get('rows') or ''))}: {escape(u.get('notes',''))}</li>"
      for u in reg.get('intake_targets_unmapped',[]))}</ul>
  </details>
</div>
<div id="map"></div>
</main>

<footer>
  Built from <code>tools/mf_uw_template/registry.json</code> · Generated
  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</footer>

<script>
const REGISTRY = {registry_inline};
const CATEGORY_ORDER = {json.dumps(CATEGORY_ORDER)};
const PATH_ORDER = {json.dumps(PATH_ORDER)};
const PATH_LABEL = {json.dumps(PATH_LABEL)};

function fmtSource(src) {{
  if (!src) return '—';
  if (src.system === 'mf_rr') {{ const a = src.address || src.column || ''; return a ? `RR!${{a}}` : 'RR'; }}
  if (src.system === 'mf_rr_sortable') return `Sortable-RR/${{src.sheet || '?'}}`;
  if (src.system === 'mf_ar') {{ const a = src.column || src.address || ''; return a ? `AR!${{a}}` : 'AR'; }}
  if (src.system === 'mf_t12') {{ const a = src.address || src.column || ''; return a ? `T-12!${{a}}` : 'T-12'; }}
  if (src.system === 'cell') return `${{src.sheet}}!${{src.address}}`;
  if (src.system === 'derived') return 'derived';
  if (src.system === 'gap') return '—  (no operator source)';
  if (src.system === 'manual') return 'manual';
  return src.system || '—';
}}
function fmtTarget(tgt) {{ return tgt ? `${{tgt.sheet}}!${{tgt.address}}` : '—'; }}
function targetLabel(tgt) {{ return tgt ? (tgt.target_label || tgt.label_at || '') : ''; }}

function render() {{
  const tv = document.getElementById('tv').value;
  document.getElementById('tplFile').textContent = REGISTRY.templates[tv].file;
  const byPath = {{}};
  for (const c of REGISTRY.concepts) {{
    const p = c.path || 'other';
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
    pathH.className = 'path-header';
    const total = Object.values(byPath[p]).reduce((s, a) => s + a.length, 0);
    pathH.innerHTML = `<span class="path-tag path-${{p}}">${{p.replace('_',' ')}}</span> ${{PATH_LABEL[p] || p}}
      <span class="count" style="color:#888;font-weight:normal;font-size:13px;margin-left:10px;">${{total}} concepts</span>`;
    pathBlock.appendChild(pathH);
    const cats = byPath[p];
    const order = [...CATEGORY_ORDER, ...Object.keys(cats).filter(k => !CATEGORY_ORDER.includes(k))];
    for (const cat of order) {{
      const items = cats[cat];
      if (!items) continue;
      const sec = document.createElement('section');
      sec.className = 'category'; sec.dataset.cat = cat; sec.dataset.path = p;
      const h3 = document.createElement('h2');
      h3.innerHTML = `${{cat.toUpperCase()}}<span class="count">${{items.length}} concept${{items.length===1?'':'s'}}</span>`;
      h3.onclick = () => sec.classList.toggle('collapsed');
      sec.appendChild(h3);
      const grid = document.createElement('div'); grid.className = 'grid';
      for (const c of items) {{
        const tgt = (c.targets || {{}})[tv];
        const row = document.createElement('div');
        row.className = `row ${{c.status}}`; row.dataset.key = c.key; row.dataset.path = p;
        row.dataset.search = [c.key, c.label, c.category, c.status, p, c.notes || '',
          fmtSource(c.source), fmtTarget(tgt), targetLabel(tgt)].join(' ').toLowerCase();
        const src = document.createElement('div');
        src.className = 'source';
        src.innerHTML = `<span class="path-tag path-${{p}}">${{p.replace('_',' ')}}</span>
          <div class="label">${{c.label}}</div><div class="addr">${{fmtSource(c.source)}}</div>
          <div class="key">${{c.key}}</div>`;
        const link = document.createElement('div');
        link.className = 'link';
        link.innerHTML = `<span class="arrow">→</span><span class="pill pill-${{c.status}}">${{c.status}}</span>`;
        const tlabel = targetLabel(tgt);
        const tgt_div = document.createElement('div');
        tgt_div.className = 'target';
        if (tgt) {{
          tgt_div.innerHTML = `<div class="label">${{tlabel || c.label}}</div>
            <div class="addr">${{fmtTarget(tgt)}}</div>${{c.notes ? `<div class="notes">${{c.notes}}</div>` : ''}}`;
        }} else {{
          tgt_div.innerHTML = `<div class="label" style="color:#a0322a">— no target —</div>
            ${{c.notes ? `<div class="notes">${{c.notes}}</div>` : ''}}`;
        }}
        row.appendChild(src); row.appendChild(link); row.appendChild(tgt_div);
        grid.appendChild(row);
      }}
      sec.appendChild(grid); pathBlock.appendChild(sec);
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
    sec.style.display = sec.querySelector('.row:not(.hidden)') ? '' : 'none';
  }});
  document.querySelectorAll('.path-block').forEach(pb => {{
    pb.style.display = pb.querySelector('.row:not(.hidden)') ? '' : 'none';
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
    print("  - tools/mf_uw_template/mapping_tracker.csv")
    print("  - tools/mf_uw_template/MAPPING_TRACKER.md")
    print("  - tools/mf_uw_template/mapping_mindmap.html")


if __name__ == "__main__":
    main()
