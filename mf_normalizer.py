"""
MF rent-roll normalizer — parse an operator Rent Roll into per-unit records
mapped to the MF UW Model's `Rent Roll Analysis` grid (cols A–AK, anchor A273).

Slice scope (per SPEC-MF §2): the core per-unit grid from the basic operator RR
(Yardi-CIM "Rent Roll - Cim" shape, validated on Hidden Lakes). Header-driven
column mapping (fuzzy) so it tolerates column reordering. AR aging (cols Q–T)
is filled later by `mf_ar_parser` via a Bldg-Unit join; the W–AK ancillary
breakouts are best-effort from the redIQ Sortable-RR (decision §2.7.2) and are
left empty here.

Public API:
    parse_mf_rr(source) -> MFRRResult
        source: path str | pathlib.Path | bytes | file-like (BytesIO w/ .name)
"""
from __future__ import annotations

import datetime as _dt
import io
import re
from dataclasses import dataclass, field

import openpyxl

from mf_mappings import UNMAPPED_STATUS, normalize_status

# Header label -> canonical field. Matched case-insensitively on a normalized
# (lowercased, punctuation-stripped) header string; first containing match wins.
_HEADER_MAP = [
    ("bldg", "bldg_unit"), ("unit no", "bldg_unit"), ("unit id", "bldg_unit"),
    ("unit type", "unit_type"), ("floor plan", "unit_type"), ("type", "unit_type"),
    ("sqft", "sqft"), ("sq ft", "sqft"), ("net sf", "sqft"), ("square f", "sqft"),
    ("unit status", "status"), ("occupancy", "status"), ("status", "status"),
    ("resident", "resident"), ("tenant", "resident"),
    ("move in", "move_in"), ("move-in", "move_in"),
    ("lease start", "lease_start"), ("lease sign", "lease_start"),
    ("lease end", "lease_end"), ("lease exp", "lease_end"), ("expiration", "lease_end"),
    ("expected move", "exp_move_out"), ("move out", "exp_move_out"), ("move-out", "exp_move_out"),
    ("market rent", "market_rent"),
    ("actual charge", "actual_charges"), ("recurring", "actual_charges"),
    ("scheduled charge", "scheduled_charges"),
    ("balance", "balance"),
    ("deposit", "deposit"),
]


def unit_key(s: str) -> str:
    """Normalized Bldg-Unit join key (uppercase, alnum only). 'A1' / 'A-1' -> 'A1'."""
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


@dataclass
class MFUnit:
    bldg_unit: str = ""       # raw source Bldg-Unit (join key for AR)
    bldg: str = ""
    unit: str = ""
    unit_type: str = ""
    sqft: float | None = None
    status: str = ""
    resident: str = ""
    legal: bool = False
    move_in: _dt.datetime | None = None
    lease_start: _dt.datetime | None = None
    lease_end: _dt.datetime | None = None
    exp_move_out: _dt.datetime | None = None
    market_rent: float = 0.0
    actual_charges: float = 0.0
    scheduled_charges: float = 0.0
    balance: float = 0.0
    deposit: float = 0.0
    # filled later by mf_ar_parser (Q–T) + redIQ Source Data (W–AK)
    ar_0_30: float = 0.0
    ar_31_60: float = 0.0
    ar_61_90: float = 0.0
    ar_90_plus: float = 0.0
    notes: str = ""
    ancillary: dict = field(default_factory=dict)


@dataclass
class MFRRResult:
    units: list[MFUnit]
    period_hint: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def unit_count(self) -> int:
        return len(self.units)

    @property
    def occupied(self) -> int:
        return sum(1 for u in self.units if u.status.startswith("Occupied"))

    @property
    def vacant(self) -> int:
        return sum(1 for u in self.units if u.status.startswith("Vacant"))

    @property
    def legal_count(self) -> int:
        return sum(1 for u in self.units if u.legal)


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9 ]", "", str(s).strip().lower()) if s is not None else ""


def _num(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").replace("$", "").strip()
        neg = s.startswith("(") and s.endswith(")")
        s = s.strip("()")
        try:
            return -float(s) if neg else float(s)
        except ValueError:
            return 0.0
    return 0.0


def _date(v):
    return v if isinstance(v, (_dt.datetime, _dt.date)) else None


def _split_bldg_unit(raw: str) -> tuple[str, str]:
    s = str(raw).strip()
    if "-" in s:
        b, u = s.split("-", 1)
        return b.strip(), u.strip()
    m = re.match(r"^([A-Za-z]+)\s*(\d.*)$", s)
    if m:
        return m.group(1), m.group(2)
    return "", s


def _load_ws(source):
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)
    wb = openpyxl.load_workbook(source, data_only=True, read_only=True)
    return wb, wb.worksheets[0]


def parse_mf_rr(source) -> MFRRResult:
    wb, ws = _load_ws(source)
    rows = list(ws.iter_rows(values_only=True))
    maxc = ws.max_column

    # 1) header row = first row containing a Bldg-Unit-style label + a rent label
    header_row = None
    for i, row in enumerate(rows[:20]):
        norm = [_norm(c) for c in row]
        joined = " | ".join(norm)
        if ("bldg" in joined or "unit no" in joined or "unit id" in joined) and "rent" in joined:
            header_row = i
            break
    if header_row is None:
        wb.close()
        raise ValueError("Could not locate the rent-roll header row.")

    # 2) map columns by header label
    col: dict[str, int] = {}
    for c in range(maxc):
        h = _norm(rows[header_row][c])
        if not h:
            continue
        for needle, field_name in _HEADER_MAP:
            if needle in h and field_name not in col:
                col[field_name] = c
                break
    if "bldg_unit" not in col or "status" not in col:
        wb.close()
        raise ValueError(f"Rent-roll header missing Bldg-Unit/Status (found {sorted(col)}).")

    def g(row, fname):
        idx = col.get(fname)
        return row[idx] if idx is not None and idx < len(row) else None

    # 3) walk data rows; a unit row has a recognized status. Stop at the
    #    Charge-Code-Summary / Future-Resident blocks that follow the grid.
    units: list[MFUnit] = []
    warnings: list[str] = []
    unknown_status = 0
    for row in rows[header_row + 1:]:
        a = g(row, "bldg_unit")
        if a in (None, ""):
            continue
        a_norm = _norm(a)
        if a_norm.startswith(("future resident", "charge code", "total ", "resident total",
                              "ledger", "selected report")):
            break  # end of the unit grid
        status = normalize_status(g(row, "status"))
        if not status or status == UNMAPPED_STATUS:
            # not a unit row (charge-code summary line, blank, etc.)
            if g(row, "status") not in (None, ""):
                unknown_status += 1
            continue

        bldg, unit = _split_bldg_unit(a)
        resident = str(g(row, "resident") or "").strip()
        legal = resident.startswith("**")
        if legal:
            resident = resident.lstrip("*").strip()
        if "vacant" in resident.lower():
            resident = ""

        units.append(MFUnit(
            bldg_unit=str(a).strip(), bldg=bldg, unit=unit,
            unit_type=str(g(row, "unit_type") or "").strip(),
            sqft=(_num(g(row, "sqft")) or None),
            status=status, resident=resident, legal=legal,
            move_in=_date(g(row, "move_in")),
            lease_start=_date(g(row, "lease_start")),
            lease_end=_date(g(row, "lease_end")),
            exp_move_out=_date(g(row, "exp_move_out")),
            market_rent=_num(g(row, "market_rent")),
            actual_charges=_num(g(row, "actual_charges")),
            scheduled_charges=_num(g(row, "scheduled_charges")),
            balance=_num(g(row, "balance")),
            deposit=_num(g(row, "deposit")),
        ))
    wb.close()

    if not units:
        warnings.append("No unit rows parsed — check the rent-roll layout.")
    if unknown_status:
        warnings.append(f"{unknown_status} row(s) had an unrecognized status and were skipped "
                        "(likely charge-code-summary lines).")
    return MFRRResult(units=units, warnings=warnings)


if __name__ == "__main__":
    import sys
    r = parse_mf_rr(sys.argv[1])
    print(f"units={r.unit_count} | occupied={r.occupied} | vacant={r.vacant} | legal={r.legal_count}")
    for w in r.warnings:
        print("  WARN:", w)
    for u in r.units[:3]:
        print("  ", u.bldg, u.unit, u.unit_type, u.status, repr(u.resident),
              u.market_rent, u.scheduled_charges, u.balance)
