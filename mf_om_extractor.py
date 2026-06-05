"""
MF Offering-Memorandum extractor — pull property facts, market data, rent comps,
and the broker pro-forma out of a marketing OM PDF and into the structures the
MF UW Model's `Prop Info` and `Rental Comps` tabs consume.

OMs are glossy, broker-specific PDFs (CBRE / IPA / MMG / local) with wildly
different layouts — the same datum (e.g. a rent-comp table) is laid out
transposed on one OM and nested-by-unit-type on the next. So unlike the RR /
T-12 / AR parsers (deterministic, single canonical shape per format), OM
extraction defaults to an **LLM engine**: the OM text is handed to Claude with a
structured-output tool schema and the model returns typed JSON. A **basic**
deterministic engine (labelled-facts scan, no API) is offered as a no-key
fallback — it reliably gets the labelled `PROPERTY DETAILS` block but not the
free-form comp tables.

Engine is caller-selectable (the app surfaces a radio):
    parse_mf_om(source, *, engine="llm"|"basic", api_key=..., model=...)

The LLM engine needs the `anthropic` SDK (lazy-imported) + an API key (passed
in, or `ANTHROPIC_API_KEY` in the env). Nothing here writes the model — that's
`mf_uw_model_writer.populate_mf_model(..., om=result)`.

Public API:
    parse_mf_om(source, *, engine="llm", api_key=None, model=DEFAULT_MODEL,
                max_chars=120_000) -> MFOMResult
    extract_pdf_text(source) -> str
"""
from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

DEFAULT_MODEL = "claude-opus-4-8"


class MFOMExtractorError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Data structures (mirror the Prop Info / Rental Comps targets)
# --------------------------------------------------------------------------- #
@dataclass
class MFUnitMixRow:
    unit_type: str = ""            # "1BR", "2BR/2BA", "Studio", "Casita", ...
    count: int | None = None
    avg_sf: float | None = None
    in_place_rent: float | None = None   # current/effective avg rent /mo
    market_rent: float | None = None     # asking/market avg rent /mo


@dataclass
class MFPropInfo:
    property_name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county: str = ""
    units_total: int | None = None
    num_buildings: int | None = None
    num_stories: int | None = None
    year_built: int | None = None
    year_renovated: int | None = None
    lot_acres: float | None = None
    gross_sqft: float | None = None
    total_rentable_sf: float | None = None
    avg_unit_sf: float | None = None
    parking_spaces: int | None = None
    parking_ratio: float | None = None
    building_class: str = ""        # A / B / C
    amenity_tier: str = ""          # Standard / Mid / Luxury
    density: float | None = None    # units/acre
    studio_units: int | None = None
    br1_units: int | None = None
    br2_units: int | None = None
    br3_units: int | None = None
    construction: str = ""
    # utilities (metering / responsibility)
    electric_meter: str = ""
    water_meter: str = ""
    gas: str = ""
    trash: str = ""
    amenities: list[str] = field(default_factory=list)
    value_add_thesis: str = ""
    unit_mix: list[MFUnitMixRow] = field(default_factory=list)


@dataclass
class MFMarketData:
    city_market: str = ""
    msa_name: str = ""
    submarket: str = ""
    msa_population: float | None = None
    city_population: float | None = None
    population_growth_rate: str = ""      # keep as stated ("57% / 10yr", "2.1%")
    avg_household_income: float | None = None
    median_income: float | None = None
    market_vacancy_rate: str = ""
    market_rent_growth: str = ""
    new_supply_units: float | None = None
    renter_pct: str = ""
    school_rating: str = ""
    notes: str = ""


@dataclass
class MFRentComp:
    name: str = ""
    address: str = ""
    distance_mi: float | None = None
    building_class: str = ""
    year_built: str = ""             # "1985" or "1975/2005" (built/renovated)
    units: int | None = None
    unit_type: str = ""              # blended "" or a specific "1BR" row
    avg_sf: float | None = None
    asking_rent: float | None = None
    rent_psf: float | None = None
    concession_weeks: float | None = None
    occupancy: str = ""              # keep as stated ("96%")
    comment: str = ""


@dataclass
class MFProForma:
    """Broker-stated economics — reference only (UW trusts the T-12, not this)."""
    asking_price: float | None = None
    units: int | None = None
    price_per_unit: float | None = None
    cap_rate: str = ""
    gpr: float | None = None
    egi: float | None = None
    opex: float | None = None
    noi: float | None = None
    notes: str = ""


@dataclass
class MFOMResult:
    prop_info: MFPropInfo = field(default_factory=MFPropInfo)
    market: MFMarketData = field(default_factory=MFMarketData)
    comps: list[MFRentComp] = field(default_factory=list)
    proforma: MFProForma | None = None
    engine: str = ""
    page_count: int = 0
    warnings: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)   # raw LLM json, for traceability


# --------------------------------------------------------------------------- #
# PDF text
# --------------------------------------------------------------------------- #
def _open_pdf(source) -> fitz.Document:
    if isinstance(source, (bytes, bytearray)):
        return fitz.open(stream=bytes(source), filetype="pdf")
    if hasattr(source, "read"):
        data = source.read()
        return fitz.open(stream=data, filetype="pdf")
    return fitz.open(source)


def extract_pdf_text(source) -> tuple[str, int]:
    """Return (full_text, page_count). Pages joined with form-feed markers."""
    doc = _open_pdf(source)
    try:
        parts = []
        for i in range(doc.page_count):
            parts.append(f"\n===== PAGE {i + 1} =====\n" + doc[i].get_text())
        return "".join(parts), doc.page_count
    finally:
        doc.close()


# --------------------------------------------------------------------------- #
# Number coercion helpers
# --------------------------------------------------------------------------- #
def _num(s) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r"-?[\d,]+(?:\.\d+)?", str(s).replace("$", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _int(s) -> int | None:
    v = _num(s)
    return int(round(v)) if v is not None else None


def _year(s) -> int | None:
    """First 4-digit year in a string ('1975/2005' -> 1975)."""
    m = re.search(r"(19|20)\d{2}", str(s or ""))
    return int(m.group(0)) if m else None


# --------------------------------------------------------------------------- #
# Engine: LLM (Claude structured output)
# --------------------------------------------------------------------------- #
_OM_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "prop_info": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string"},
                "address": {"type": "string", "description": "street address"},
                "city": {"type": "string"},
                "state": {"type": "string", "description": "2-letter state"},
                "zip_code": {"type": "string"},
                "county": {"type": "string"},
                "units_total": {"type": ["integer", "null"]},
                "num_buildings": {"type": ["integer", "null"]},
                "num_stories": {"type": ["integer", "null"]},
                "year_built": {"type": ["integer", "null"]},
                "year_renovated": {"type": ["integer", "null"]},
                "lot_acres": {"type": ["number", "null"]},
                "gross_sqft": {"type": ["number", "null"]},
                "total_rentable_sf": {"type": ["number", "null"]},
                "avg_unit_sf": {"type": ["number", "null"]},
                "parking_spaces": {"type": ["integer", "null"]},
                "parking_ratio": {"type": ["number", "null"]},
                "building_class": {"type": "string", "description": "A, B, or C"},
                "amenity_tier": {"type": "string",
                                 "description": "Standard, Mid, or Luxury"},
                "density": {"type": ["number", "null"]},
                "studio_units": {"type": ["integer", "null"]},
                "br1_units": {"type": ["integer", "null"]},
                "br2_units": {"type": ["integer", "null"]},
                "br3_units": {"type": ["integer", "null"]},
                "construction": {"type": "string"},
                "electric_meter": {"type": "string"},
                "water_meter": {"type": "string"},
                "gas": {"type": "string"},
                "trash": {"type": "string"},
                "amenities": {"type": "array", "items": {"type": "string"}},
                "value_add_thesis": {"type": "string",
                                     "description": "1-3 sentence value-add summary"},
                "unit_mix": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "unit_type": {"type": "string"},
                            "count": {"type": ["integer", "null"]},
                            "avg_sf": {"type": ["number", "null"]},
                            "in_place_rent": {"type": ["number", "null"]},
                            "market_rent": {"type": ["number", "null"]},
                        },
                    },
                },
            },
        },
        "market": {
            "type": "object",
            "properties": {
                "city_market": {"type": "string"},
                "msa_name": {"type": "string"},
                "submarket": {"type": "string"},
                "msa_population": {"type": ["number", "null"]},
                "city_population": {"type": ["number", "null"]},
                "population_growth_rate": {"type": "string"},
                "avg_household_income": {"type": ["number", "null"]},
                "median_income": {"type": ["number", "null"]},
                "market_vacancy_rate": {"type": "string"},
                "market_rent_growth": {"type": "string"},
                "new_supply_units": {"type": ["number", "null"]},
                "renter_pct": {"type": "string"},
                "school_rating": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
        "comps": {
            "type": "array",
            "description": "Submarket rent comparables. One row per comp "
                           "property (use the blended/total line, not per-unit-type).",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {"type": "string"},
                    "distance_mi": {"type": ["number", "null"]},
                    "building_class": {"type": "string"},
                    "year_built": {"type": "string"},
                    "units": {"type": ["integer", "null"]},
                    "unit_type": {"type": "string"},
                    "avg_sf": {"type": ["number", "null"]},
                    "asking_rent": {"type": ["number", "null"]},
                    "rent_psf": {"type": ["number", "null"]},
                    "concession_weeks": {"type": ["number", "null"]},
                    "occupancy": {"type": "string"},
                    "comment": {"type": "string"},
                },
            },
        },
        "proforma": {
            "type": "object",
            "description": "Broker-stated economics if present (reference only).",
            "properties": {
                "asking_price": {"type": ["number", "null"]},
                "units": {"type": ["integer", "null"]},
                "price_per_unit": {"type": ["number", "null"]},
                "cap_rate": {"type": "string"},
                "gpr": {"type": ["number", "null"]},
                "egi": {"type": ["number", "null"]},
                "opex": {"type": ["number", "null"]},
                "noi": {"type": ["number", "null"]},
                "notes": {"type": "string"},
            },
        },
    },
    "required": ["prop_info", "market", "comps"],
}

_SYSTEM_PROMPT = (
    "You are a multifamily acquisitions analyst extracting structured data from a "
    "broker Offering Memorandum (OM). Extract ONLY facts stated in the document — "
    "never invent or estimate. Use null for anything not stated. Rules:\n"
    "- Numbers: strip $, commas, units ('32.18 Acres' -> 32.18; '$1,330' -> 1330).\n"
    "- Rent comps: emit ONE row per comp property using its blended / "
    "total-weighted-average line (ignore per-bedroom sub-rows unless that is the "
    "only line for that comp). Do NOT include the subject property as a comp.\n"
    "- unit_mix: one row per floorplan with its unit count, avg SF, and the "
    "in-place vs market/asking rent if both are shown.\n"
    "- building_class / amenity_tier: only if explicitly stated; else \"\".\n"
    "- value_add_thesis: 1-3 sentences summarizing the stated upside/business plan.\n"
    "Call the emit_om_data tool exactly once with everything you found."
)


def _extract_llm(text: str, *, api_key: str | None, model: str,
                 max_chars: int) -> tuple[dict, list[str]]:
    try:
        import anthropic
    except ImportError as e:
        raise MFOMExtractorError(
            "LLM engine needs the 'anthropic' package — `pip install anthropic`, "
            "or choose the Basic (no-API) engine."
        ) from e

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise MFOMExtractorError(
            "LLM engine needs an Anthropic API key (pass api_key= or set "
            "ANTHROPIC_API_KEY), or choose the Basic (no-API) engine."
        )

    warnings: list[str] = []
    if len(text) > max_chars:
        warnings.append(
            f"OM text {len(text):,} chars exceeds {max_chars:,}; truncated. "
            "Data sections are usually early, but verify late-page comps."
        )
        text = text[:max_chars]

    client = anthropic.Anthropic(api_key=key)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=8000,
            system=[{
                "type": "text", "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=[{
                "name": "emit_om_data",
                "description": "Return the structured OM data.",
                "input_schema": _OM_TOOL_SCHEMA,
            }],
            tool_choice={"type": "tool", "name": "emit_om_data"},
            messages=[{"role": "user",
                       "content": f"OFFERING MEMORANDUM TEXT:\n\n{text}"}],
        )
    except Exception as e:  # network / auth / api errors
        raise MFOMExtractorError(f"Anthropic API call failed: {e}") from e

    for block in resp.content:
        if getattr(block, "type", None) == "tool_use":
            return block.input, warnings
    raise MFOMExtractorError("LLM returned no structured tool output.")


def _result_from_json(data: dict, *, engine: str, page_count: int,
                      warnings: list[str]) -> MFOMResult:
    """Map the (LLM) JSON dict onto the typed dataclasses, coercing numbers."""
    pi = data.get("prop_info") or {}
    prop = MFPropInfo(
        property_name=pi.get("property_name", "") or "",
        address=pi.get("address", "") or "",
        city=pi.get("city", "") or "",
        state=pi.get("state", "") or "",
        zip_code=pi.get("zip_code", "") or "",
        county=pi.get("county", "") or "",
        units_total=_int(pi.get("units_total")),
        num_buildings=_int(pi.get("num_buildings")),
        num_stories=_int(pi.get("num_stories")),
        year_built=_int(pi.get("year_built")),
        year_renovated=_int(pi.get("year_renovated")),
        lot_acres=_num(pi.get("lot_acres")),
        gross_sqft=_num(pi.get("gross_sqft")),
        total_rentable_sf=_num(pi.get("total_rentable_sf")),
        avg_unit_sf=_num(pi.get("avg_unit_sf")),
        parking_spaces=_int(pi.get("parking_spaces")),
        parking_ratio=_num(pi.get("parking_ratio")),
        building_class=(pi.get("building_class", "") or "").strip(),
        amenity_tier=(pi.get("amenity_tier", "") or "").strip(),
        density=_num(pi.get("density")),
        studio_units=_int(pi.get("studio_units")),
        br1_units=_int(pi.get("br1_units")),
        br2_units=_int(pi.get("br2_units")),
        br3_units=_int(pi.get("br3_units")),
        construction=pi.get("construction", "") or "",
        electric_meter=pi.get("electric_meter", "") or "",
        water_meter=pi.get("water_meter", "") or "",
        gas=pi.get("gas", "") or "",
        trash=pi.get("trash", "") or "",
        amenities=[a for a in (pi.get("amenities") or []) if a],
        value_add_thesis=pi.get("value_add_thesis", "") or "",
        unit_mix=[
            MFUnitMixRow(
                unit_type=r.get("unit_type", "") or "",
                count=_int(r.get("count")),
                avg_sf=_num(r.get("avg_sf")),
                in_place_rent=_num(r.get("in_place_rent")),
                market_rent=_num(r.get("market_rent")),
            )
            for r in (pi.get("unit_mix") or [])
        ],
    )

    mk = data.get("market") or {}
    market = MFMarketData(
        city_market=mk.get("city_market", "") or "",
        msa_name=mk.get("msa_name", "") or "",
        submarket=mk.get("submarket", "") or "",
        msa_population=_num(mk.get("msa_population")),
        city_population=_num(mk.get("city_population")),
        population_growth_rate=str(mk.get("population_growth_rate", "") or ""),
        avg_household_income=_num(mk.get("avg_household_income")),
        median_income=_num(mk.get("median_income")),
        market_vacancy_rate=str(mk.get("market_vacancy_rate", "") or ""),
        market_rent_growth=str(mk.get("market_rent_growth", "") or ""),
        new_supply_units=_num(mk.get("new_supply_units")),
        renter_pct=str(mk.get("renter_pct", "") or ""),
        school_rating=str(mk.get("school_rating", "") or ""),
        notes=mk.get("notes", "") or "",
    )

    comps = [
        MFRentComp(
            name=c.get("name", "") or "",
            address=c.get("address", "") or "",
            distance_mi=_num(c.get("distance_mi")),
            building_class=(c.get("building_class", "") or "").strip(),
            year_built=str(c.get("year_built", "") or ""),
            units=_int(c.get("units")),
            unit_type=c.get("unit_type", "") or "",
            avg_sf=_num(c.get("avg_sf")),
            asking_rent=_num(c.get("asking_rent")),
            rent_psf=_num(c.get("rent_psf")),
            concession_weeks=_num(c.get("concession_weeks")),
            occupancy=str(c.get("occupancy", "") or ""),
            comment=c.get("comment", "") or "",
        )
        for c in (data.get("comps") or [])
        if (c.get("name") or "").strip()
    ]

    proforma = None
    pf = data.get("proforma")
    if pf and any(pf.get(k) for k in pf):
        proforma = MFProForma(
            asking_price=_num(pf.get("asking_price")),
            units=_int(pf.get("units")),
            price_per_unit=_num(pf.get("price_per_unit")),
            cap_rate=str(pf.get("cap_rate", "") or ""),
            gpr=_num(pf.get("gpr")),
            egi=_num(pf.get("egi")),
            opex=_num(pf.get("opex")),
            noi=_num(pf.get("noi")),
            notes=pf.get("notes", "") or "",
        )

    return MFOMResult(prop_info=prop, market=market, comps=comps,
                      proforma=proforma, engine=engine, page_count=page_count,
                      warnings=list(warnings), raw=data)


# --------------------------------------------------------------------------- #
# Engine: basic (deterministic labelled-facts scan, no API)
# --------------------------------------------------------------------------- #
# label-needle (normalized, lowercased) -> (field, coercer). The value is the
# next non-empty line after a line that *equals* the label (OMs lay facts out as
# label\nvalue pairs). First match in document order wins per field.
_BASIC_LABELS = [
    ("total units", "units_total", _int),
    ("units", "units_total", _int),
    ("number of units", "units_total", _int),
    ("year completed", "year_built", _year),
    ("year built", "year_built", _year),
    ("site acreage", "lot_acres", _num),
    ("site area", "lot_acres", _num),
    ("lot size", "lot_acres", _num),
    ("average unit size", "avg_unit_sf", _num),
    ("avg unit size", "avg_unit_sf", _num),
    ("total rentable sf", "total_rentable_sf", _num),
    ("total rentable sf (residential)", "total_rentable_sf", _num),
    ("rentable sf", "total_rentable_sf", _num),
    ("no. of residential buildings", "num_buildings", _int),
    ("no. of buildings", "num_buildings", _int),
    ("number of buildings", "num_buildings", _int),
    ("of buildings", "num_buildings", _int),
    ("no. of stories", "num_stories", _int),
    ("of stories", "num_stories", _int),
    ("number of stories", "num_stories", _int),
    ("parking spaces", "parking_spaces", _int),
    ("parking ratio", "parking_ratio", _num),
    ("density", "density", _num),
    ("county", "county", str),
    ("zoning", None, None),  # skip — placeholder to keep county from grabbing it
]

_NORM = lambda s: re.sub(r"\s+", " ", str(s).strip().lower()).rstrip(":")


def _basic_plausible(fieldname: str, val) -> bool:
    """Reject obviously-wrong basic-engine matches (e.g. a year as a unit count)."""
    looks_year = isinstance(val, (int, float)) and 1900 <= val <= 2100
    if fieldname == "units_total":
        return 4 <= val <= 10000 and not looks_year
    if fieldname == "num_buildings":
        return 1 <= val <= 500 and not looks_year
    if fieldname == "num_stories":
        return 1 <= val <= 60
    if fieldname == "year_built":
        return 1900 <= val <= 2035
    if fieldname == "avg_unit_sf":
        return 200 <= val <= 5000
    if fieldname == "parking_spaces":
        return 1 <= val <= 20000 and not looks_year
    if fieldname == "lot_acres":
        return 0.1 <= val <= 2000
    return True


def _extract_basic(text: str, page_count: int) -> MFOMResult:
    lines = [ln.strip() for ln in text.splitlines()]
    nonempty = [ln for ln in lines if ln]
    # collect ALL label->next-line candidates per field (in document order), then
    # pick the first that coerces to a plausible value — a bad early match no
    # longer shadows a good later one.
    candidates: dict[str, list[str]] = {}
    for pos, ln in enumerate(nonempty):
        key = _NORM(ln)
        val = nonempty[pos + 1] if pos + 1 < len(nonempty) else ""
        for needle, fieldname, _coerce in _BASIC_LABELS:
            if fieldname and key == needle:
                candidates.setdefault(fieldname, []).append(val)

    prop = MFPropInfo()
    coercers = {f: c for n, f, c in _BASIC_LABELS if f}
    for fieldname, raws in candidates.items():
        coerce = coercers.get(fieldname, str)
        for raw in raws:
            try:
                val = coerce(raw) if coerce is not str else raw
            except Exception:
                continue
            if val in (None, "") or (coerce is not str
                                     and not _basic_plausible(fieldname, val)):
                continue
            setattr(prop, fieldname, val)
            break

    warnings = [
        "Basic engine: extracted the labelled PROPERTY DETAILS block only. "
        "Rent comps, market data, unit mix, and pro-forma are NOT parsed "
        "deterministically — use the LLM engine for those.",
    ]
    if prop.units_total is None:
        warnings.append("Basic engine could not find a unit count — this OM's "
                        "facts block may be image-based or unlabelled.")
    return MFOMResult(prop_info=prop, market=MFMarketData(), comps=[],
                      proforma=None, engine="basic", page_count=page_count,
                      warnings=warnings, raw={"candidates": candidates})


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def parse_mf_om(source, *, engine: str = "llm", api_key: str | None = None,
                model: str = DEFAULT_MODEL, max_chars: int = 120_000) -> MFOMResult:
    """Extract an OM into an MFOMResult.

    source: path | bytes | file-like PDF.
    engine: "llm" (Claude structured output, default) or "basic" (no-API).
    """
    engine = (engine or "llm").lower()
    if engine not in ("llm", "basic"):
        raise MFOMExtractorError(f"Unknown engine {engine!r} (use 'llm' or 'basic').")

    text, page_count = extract_pdf_text(source)
    if len(text.strip()) < 200:
        raise MFOMExtractorError(
            "PDF yielded almost no text — it is likely scanned/image-only and "
            "needs OCR before extraction."
        )

    if engine == "basic":
        return _extract_basic(text, page_count)

    data, warnings = _extract_llm(text, api_key=api_key, model=model,
                                  max_chars=max_chars)
    return _result_from_json(data, engine="llm", page_count=page_count,
                             warnings=warnings)
