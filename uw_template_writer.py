"""
uw_template_writer.py — Track 4 / Phase 2

Pure function that populates the ALF UW Template from a populated Analyzer
workbook, driven by the mapping registry at `tools/uw_template/registry.json`.

Public API:
    populate_uw_template(analyzer_bytes, template_bytes, *,
                         template_version='v4',
                         scenario='normalized',
                         registry_path=None) -> (bytes, PopulateReport)

Conventions:

  - **Analyzer** is loaded with `data_only=True` because UW Output cells are
    formula references into T12 Analytics. The Analyzer must have been
    saved through Excel (or LibreOffice) at least once so the cached values
    are present. The reader does not evaluate formulas itself.
  - **Template** is loaded with `data_only=False` so formula columns on
    Rent Roll Analysis (V, X, Y, Z, AA, AB, AS — see registry's
    intake_targets_unmapped) and all of the downstream output sheets
    (Cover, Scenarios, P&L, Waterfall, ...) preserve their formulas
    untouched. The writer only mutates cells corresponding to mapped
    concepts.
  - **Scenarios** parameter selects T-12 path source column:
      'normalized'  → UW Output col F (default; contract §8 says this is
                      the underwriting figure)
      't12_actual'  → UW Output col E
  - **Bad debt placement:** by default the writer writes the Analyzer's
    bad-debt value to T-12 Analysis!N62 (revenue contra-line — template's
    structural choice). The Analyzer's opex Bad Debt Expense (UW Output
    row 57) is mapped to template N106 in the registry but flagged as a
    duplicate target. The writer skips N106 to avoid double-counting; see
    `_SPECIAL_SKIP_KEYS` below. Override by passing the key in
    `allow_special_keys`.

The writer does NOT modify the Analyzer (read-only) and does NOT mutate
the input bytes (returns new bytes via `io.BytesIO`).
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import get_column_letter

# ──────────────────────────────────────────────────────────────────────────────
# Defaults
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "tools" / "uw_template" / "registry.json"

# Statuses for which the writer skips by default. Override by passing
# `include_statuses=(...)` to populate_uw_template.
_DEFAULT_SKIP_STATUSES = frozenset({
    "gap_source",
    "gap_target",
    "header_only",
    "derived",
    "manual",
    "substrate_ready_parser_pending",
    "decided_pending_upstream",
})

# Hard-coded skip set — concepts the writer deliberately does not populate
# because including them would double-count or conflict with another concept.
# Each key maps to a one-line reason for the report.
_SPECIAL_SKIP_KEYS: dict[str, str] = {
    "opex_bad_debt_expense": (
        "Bad Debt Expense (UW Output row 57) is already written to N62 "
        "(revenue contra-line) via `bad_debt_writeoffs_revenue`. Writing "
        "to N106 too would double-count. Override with allow_special_keys."
    ),
}

# Status colours mirror the generator — duplicated here so the writer can
# tag the report with consistent labels.
_STATUS_LABELS: dict[str, str] = {
    "mapped": "mapped",
    "proposed": "proposed",
    "gap_source": "gap_source",
    "gap_target": "gap_target",
    "header_only": "header_only",
    "manual": "manual",
    "derived": "derived",
    "decided_pending_upstream": "decided_pending_upstream",
    "substrate_ready_parser_pending": "substrate_ready_parser_pending",
}


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class UWTemplateWriterError(Exception):
    """Base exception for the UW Template writer."""


class TemplateVersionMissing(UWTemplateWriterError):
    """Raised when the registry has no entry for the requested template version."""


# ──────────────────────────────────────────────────────────────────────────────
# Report dataclasses
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ConceptResult:
    """Per-concept outcome of a single populate run."""
    key: str
    path: str  # 't12' | 'rent_roll' | 'ar'
    status: str  # registry status
    outcome: str  # 'written' | 'skipped' | 'error' | 'no_source' | 'no_target' | 'written_list'
    target_address: str = ""  # 'Sheet!A1' when applicable
    cells_written: int = 0
    notes: str = ""
    sample_value: Any = None  # first / sample value for spot-checking


@dataclass
class PopulateReport:
    """Structured outcome of populate_uw_template.

    Inspect `summary` for counts and `results` for per-concept detail.
    """
    template_version: str
    scenario: str
    summary: dict[str, int] = field(default_factory=dict)
    results: list[ConceptResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def write_count(self) -> int:
        return sum(r.cells_written for r in self.results)

    def by_outcome(self) -> dict[str, list[ConceptResult]]:
        out: dict[str, list[ConceptResult]] = {}
        for r in self.results:
            out.setdefault(r.outcome, []).append(r)
        return out

    def to_dict(self) -> dict:
        return {
            "template_version": self.template_version,
            "scenario": self.scenario,
            "summary": self.summary,
            "warnings": self.warnings,
            "results": [
                {
                    "key": r.key, "path": r.path, "status": r.status,
                    "outcome": r.outcome,
                    "target_address": r.target_address,
                    "cells_written": r.cells_written,
                    "notes": r.notes,
                    "sample_value": (
                        str(r.sample_value) if r.sample_value is not None else None
                    ),
                }
                for r in self.results
            ],
        }


# ──────────────────────────────────────────────────────────────────────────────
# Source resolution
# ──────────────────────────────────────────────────────────────────────────────

_ADDR_RE = re.compile(r"^\$?([A-Z]+)\$?(\d+)$")


def _split_qualified(qualified: str) -> tuple[str, str]:
    """Split 'Sheet!$A$5' into ('Sheet', 'A5').

    Handles single-quoted sheet names: "'Rent Roll Recon'!$B$2" → ('Rent Roll Recon', 'B2').
    """
    if "!" not in qualified:
        raise ValueError(f"Not a qualified address: {qualified!r}")
    sheet, addr = qualified.rsplit("!", 1)
    sheet = sheet.strip().strip("'")
    addr = addr.replace("$", "")
    return sheet, addr


def _resolve_uw_output_value(wb_analyzer, src: dict, scenario: str) -> Any:
    """Read a scalar value from UW Output at (row, column-by-scenario)."""
    sheet = src.get("sheet", "UW Output")
    row = src.get("row")
    col_spec = src.get("column", "")
    if row is None:
        return None
    if col_spec == "E_or_F":
        col = "F" if scenario == "normalized" else "E"
    else:
        col = col_spec  # 'B' / 'C' / 'D' for IL/AL/MC splits, etc.
    return wb_analyzer[sheet][f"{col}{row}"].value


def _resolve_named_range_value(wb_analyzer, src: dict) -> Any:
    """Read a scalar value from a named range, e.g. Property_Name → Cover!$B$5."""
    name = src.get("name")
    if not name or name not in wb_analyzer.defined_names:
        return None
    qualified = wb_analyzer.defined_names[name].value
    sheet, addr = _split_qualified(qualified)
    if sheet not in wb_analyzer.sheetnames:
        return None
    return wb_analyzer[sheet][addr].value


def _resolve_cell_value(wb_analyzer, src: dict) -> Any:
    """Read a scalar value from a literal Sheet!Cell address."""
    sheet = src.get("sheet")
    addr = src.get("address")
    if not sheet or not addr or sheet not in wb_analyzer.sheetnames:
        return None
    return wb_analyzer[sheet][addr].value


def _resolve_rr_input_column(wb_analyzer, src: dict) -> list[Any]:
    """Read a full column from Rent Roll Input, rows 7..606.

    Returns a list of length 600, with None for empty cells. The writer
    truncates to populated rows at write time.
    """
    sheet = src.get("sheet", "Rent Roll Input")
    col = src.get("column", "")
    if not col or sheet not in wb_analyzer.sheetnames:
        return []
    ws = wb_analyzer[sheet]
    return [ws[f"{col}{r}"].value for r in range(7, 607)]


def _compute_derived(wb_analyzer, concept: dict, scenario: str) -> Any:
    """Compute a derived value for a concept whose source.system == 'derived'.

    The set of derived keys is small and hard-coded.
    """
    key = concept.get("key")
    if key == "licensed_beds_total":
        # SUM of UW Output B70 + C70 + D70 (IL + AL + MC).
        ws = wb_analyzer["UW Output"]
        parts = [ws[f"{c}70"].value for c in ("B", "C", "D")]
        return sum((p or 0) for p in parts if isinstance(p, (int, float)))
    if key == "opex_total_incl_mgmt":
        # SUM of UW Output row 63 (Total opex excl. mgmt) + row 64 (Mgmt fee)
        # in the active scenario column.
        col = "F" if scenario == "normalized" else "E"
        ws = wb_analyzer["UW Output"]
        a = ws[f"{col}63"].value or 0
        b = ws[f"{col}64"].value or 0
        return (a if isinstance(a, (int, float)) else 0) + (
            b if isinstance(b, (int, float)) else 0
        )
    if key == "second_person_revenue":
        # Source says "Computed elsewhere" — for now, return None and let
        # the writer skip. Could later sum Rent Roll Input col V × 12.
        return None
    return None


def _resolve_source(wb_analyzer, concept: dict, scenario: str) -> Any:
    """Dispatch on concept.source.system to read the source value."""
    src = concept.get("source") or {}
    system = src.get("system")
    if system == "uw_output":
        return _resolve_uw_output_value(wb_analyzer, src, scenario)
    if system == "named_range":
        return _resolve_named_range_value(wb_analyzer, src)
    if system == "cell":
        return _resolve_cell_value(wb_analyzer, src)
    if system == "rr_input":
        return _resolve_rr_input_column(wb_analyzer, src)
    if system == "derived":
        return _compute_derived(wb_analyzer, concept, scenario)
    if system == "gap":
        return None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Target write
# ──────────────────────────────────────────────────────────────────────────────

def _is_blank(value) -> bool:
    """Treat empty strings and pandas-NaN-likes as blank. Native None too."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _parse_target_addr(addr: str) -> tuple[str, int, bool]:
    """Return (col_letter, row, is_rowstride).

    Address forms:
      'N69'   → ('N', 69, False)
      'A211+' → ('A', 211, True)  — row-stride paste anchor
    """
    is_stride = addr.endswith("+")
    core = addr.rstrip("+")
    m = _ADDR_RE.match(core)
    if not m:
        raise ValueError(f"Unparseable target address: {addr!r}")
    return m.group(1), int(m.group(2)), is_stride


def _write_scalar(ws, addr: str, value: Any) -> None:
    """Write a scalar value to a single cell."""
    ws[addr] = value


def _write_column_stride(
    ws, col_letter: str, start_row: int, values: list[Any],
    max_rows: int = 600,
) -> int:
    """Write a column of values starting at (col_letter)(start_row).

    Returns the number of non-blank cells written. Blank source rows are
    skipped (not overwritten with None — preserves any cells the template
    might have pre-styled or pre-populated).
    """
    written = 0
    for i, v in enumerate(values):
        if i >= max_rows:
            break
        if _is_blank(v):
            continue
        ws[f"{col_letter}{start_row + i}"] = v
        written += 1
    return written


# ──────────────────────────────────────────────────────────────────────────────
# Main entry
# ──────────────────────────────────────────────────────────────────────────────

def _load_registry(path: str | Path | None) -> dict:
    p = Path(path) if path else DEFAULT_REGISTRY
    if not p.exists():
        raise UWTemplateWriterError(f"Registry not found: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def populate_uw_template(
    analyzer_bytes: bytes,
    template_bytes: bytes,
    *,
    template_version: str = "v5",
    scenario: str = "normalized",
    registry_path: str | Path | None = None,
    include_statuses: frozenset[str] | None = None,
    allow_special_keys: frozenset[str] | None = None,
) -> tuple[bytes, PopulateReport]:
    """Populate the UW Template from a populated Analyzer workbook.

    Parameters
    ----------
    analyzer_bytes : bytes
        Raw bytes of a populated `ALF_Financial_Analyzer_Only.xlsx`. The
        Analyzer must have been saved through Excel at least once so the
        UW Output formula values are cached.
    template_bytes : bytes
        Raw bytes of the UW Template (e.g. `ALF_UW_Template_v4.xlsx`).
        Formula cells on the template side are preserved.
    template_version : str, default 'v5'
        Which version-keyed target to use from the registry. v4 is still
        supported (pass `template_version='v4'`); v5 is the binding default
        as of 2026-05-26.
    scenario : str, default 'normalized'
        'normalized' (UW Output col F) or 't12_actual' (col E). Controls
        which annual column the t12-path writes.
    registry_path : str | Path | None
        Override the default registry location.
    include_statuses : frozenset[str] | None
        Statuses to INCLUDE. Defaults to `{'mapped', 'proposed'}`. Anything
        not in this set is skipped (along with the default skip set).
    allow_special_keys : frozenset[str] | None
        Concept keys to NOT special-skip even if they're in `_SPECIAL_SKIP_KEYS`.
        Default is None (honor all special-skips).

    Returns
    -------
    (populated_bytes, PopulateReport)
    """
    reg = _load_registry(registry_path)
    templates = reg.get("templates", {})
    if template_version not in templates:
        raise TemplateVersionMissing(
            f"Registry has no template version {template_version!r}. "
            f"Available: {sorted(templates.keys())}"
        )

    include = include_statuses or frozenset({"mapped", "proposed"})
    allow_special = allow_special_keys or frozenset()

    # ── Load workbooks ────────────────────────────────────────────────────────
    wb_analyzer = openpyxl.load_workbook(
        io.BytesIO(analyzer_bytes), data_only=True
    )
    wb_template = openpyxl.load_workbook(
        io.BytesIO(template_bytes), data_only=False
    )

    report = PopulateReport(template_version=template_version, scenario=scenario)

    # Pre-flight: confirm intake sheets exist on the template
    tv = templates[template_version]
    expected_intakes = tv.get("intake_sheets", [])
    for s in expected_intakes:
        if s not in wb_template.sheetnames:
            report.warnings.append(
                f"Template missing expected intake sheet: {s!r}"
            )

    # Per-template-version capacity for the rent_roll path. Defaults to a
    # high number when the registry doesn't pin it (legacy v4 fallback).
    rr_data_end_row = (
        tv.get("rent_roll_data_end_row")
        or tv.get("data_end_row")
        or 610
    )
    rr_paste_start = 211  # contract anchor — fixed across template versions
    rr_max_rows = rr_data_end_row - rr_paste_start + 1

    # Pre-flight: confirm Rent Roll Analysis header at row 210 if rent_roll
    # concepts will be written. The contract specifies paste at A211+ with
    # a header at row 210 — older / working-copy templates may not have
    # the header row, in which case the writer still writes (per the
    # registry's paste anchor) but flags a warning.
    rr_concepts = [c for c in reg.get("concepts", []) if c.get("path") == "rent_roll"]
    if rr_concepts and "Rent Roll Analysis" in wb_template.sheetnames:
        ra = wb_template["Rent Roll Analysis"]
        # Look at row 210 col A — should be "Unit/Bed" or similar per contract
        hdr = ra["A210"].value
        if not hdr:
            report.warnings.append(
                "Rent Roll Analysis!A210 is blank — the contract specifies "
                "a header row at 210 with paste anchor at 211. Writing to "
                "row 211+ anyway; the template may be a working copy that "
                "predates the contract's row layout."
            )

    # ── Iterate concepts ──────────────────────────────────────────────────────
    for concept in reg.get("concepts", []):
        key = concept.get("key", "")
        path = concept.get("path", "t12")
        status = concept.get("status", "")

        result = ConceptResult(
            key=key, path=path, status=status, outcome="skipped",
        )

        # Skip on status filter
        if status in _DEFAULT_SKIP_STATUSES:
            result.outcome = "skipped"
            result.notes = f"status={status} in default skip set"
            report.results.append(result)
            continue
        if status not in include:
            result.outcome = "skipped"
            result.notes = f"status={status} not in include set"
            report.results.append(result)
            continue

        # Skip on special-key list (e.g. opex_bad_debt_expense duplicate)
        if key in _SPECIAL_SKIP_KEYS and key not in allow_special:
            result.outcome = "skipped"
            result.notes = _SPECIAL_SKIP_KEYS[key]
            report.results.append(result)
            continue

        # Resolve target for this template version
        tgt = (concept.get("targets") or {}).get(template_version)
        if not tgt:
            result.outcome = "no_target"
            result.notes = f"no target for template version {template_version!r}"
            report.results.append(result)
            continue

        target_sheet = tgt.get("sheet")
        target_addr = tgt.get("address", "")
        result.target_address = f"{target_sheet}!{target_addr}"

        if target_sheet not in wb_template.sheetnames:
            result.outcome = "error"
            result.notes = f"target sheet {target_sheet!r} not in template"
            report.results.append(result)
            continue

        ws = wb_template[target_sheet]

        # Resolve source
        try:
            value = _resolve_source(wb_analyzer, concept, scenario)
        except Exception as e:  # defensive — never crash on a single concept
            result.outcome = "error"
            result.notes = f"source resolve failed: {e}"
            report.results.append(result)
            continue

        # Decide scalar vs row-stride
        try:
            col_letter, start_row, is_stride = _parse_target_addr(target_addr)
        except ValueError as e:
            result.outcome = "error"
            result.notes = f"unparseable target: {e}"
            report.results.append(result)
            continue

        if isinstance(value, list):
            # Rent-roll / column-stride source
            if not is_stride:
                result.outcome = "error"
                result.notes = (
                    "source returned a list but target is not a row-stride "
                    f"(target={target_addr!r}); registry inconsistency"
                )
                report.results.append(result)
                continue
            # Cap stride at the template version's data_end_row. Truncate
            # source if it would overflow the template's data block; surface
            # overflow as a warning so the analyst can see a deal-too-big
            # case clearly.
            effective_max = rr_max_rows
            populated_count = sum(1 for v in value if not _is_blank(v))
            if populated_count > effective_max:
                report.warnings.append(
                    f"{concept.get('key')!r}: source has {populated_count} "
                    f"populated rows but template {template_version!r} only "
                    f"holds {effective_max} ({rr_paste_start}..{rr_data_end_row}). "
                    f"Truncating."
                )
            written = _write_column_stride(
                ws, col_letter, start_row, value, max_rows=effective_max
            )
            result.outcome = "written" if written > 0 else "no_source"
            result.cells_written = written
            # sample value: first non-None
            sample = next((v for v in value if not _is_blank(v)), None)
            result.sample_value = sample
            if written == 0:
                result.notes = "source column is empty in Analyzer"
        else:
            # Scalar
            if _is_blank(value):
                result.outcome = "no_source"
                result.notes = "source resolved to blank/None"
                report.results.append(result)
                continue
            if is_stride:
                # Treat as scalar at start_row even though address ends in '+'
                target_addr_eff = f"{col_letter}{start_row}"
            else:
                target_addr_eff = f"{col_letter}{start_row}"
            _write_scalar(ws, target_addr_eff, value)
            result.outcome = "written"
            result.cells_written = 1
            result.sample_value = value

        report.results.append(result)

    # ── Summary ───────────────────────────────────────────────────────────────
    by = report.by_outcome()
    report.summary = {k: len(v) for k, v in by.items()}
    report.summary["total_concepts"] = len(report.results)
    report.summary["cells_written"] = report.write_count()

    # ── Serialize ─────────────────────────────────────────────────────────────
    out = io.BytesIO()
    wb_template.save(out)
    return out.getvalue(), report


# ──────────────────────────────────────────────────────────────────────────────
# CLI for ad-hoc runs
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Populate the ALF UW Template.")
    ap.add_argument("analyzer", help="path to populated Analyzer .xlsx")
    ap.add_argument("template", help="path to UW Template .xlsx")
    ap.add_argument("output", help="output path for populated template")
    ap.add_argument(
        "--scenario", default="normalized",
        choices=("normalized", "t12_actual"),
    )
    ap.add_argument("--template-version", default="v5")
    ap.add_argument("--registry", default=None)
    args = ap.parse_args()

    analyzer_bytes = Path(args.analyzer).read_bytes()
    template_bytes = Path(args.template).read_bytes()

    populated, report = populate_uw_template(
        analyzer_bytes, template_bytes,
        template_version=args.template_version,
        scenario=args.scenario,
        registry_path=args.registry,
    )

    Path(args.output).write_bytes(populated)

    print(f"\nPopulated → {args.output}")
    print(f"\n=== Summary ===")
    for k, v in sorted(report.summary.items()):
        print(f"  {k:25s}  {v}")
    if report.warnings:
        print(f"\n=== Warnings ({len(report.warnings)}) ===")
        for w in report.warnings:
            print(f"  ! {w}")

    written = [r for r in report.results if r.outcome == "written"]
    if written:
        print(f"\n=== First 10 written cells ===")
        for r in written[:10]:
            print(
                f"  {r.target_address:35s}  ← {r.key:30s}  "
                f"({r.cells_written} cell{'s' if r.cells_written != 1 else ''})  "
                f"sample={r.sample_value!r}"
            )

    sys.exit(0)
