"""
Registry absorber — add OM (Offering-Memorandum) intake concepts.

Track 4-MF P3: the OM extractor (`mf_om_extractor.parse_mf_om`) + writer
(`mf_uw_model_writer.populate_mf_model(om=...)`) populate two new target regions
from a broker OM PDF — Prop Info property-details + market block (col B) and the
Rental Comps comp set (rows 8–22). This script registers those concepts against
`templates.v15`, retires the "OM intake NOT BUILT" open-question, narrows the
Prop Info manual-input note, and bumps the registry version.

Idempotent: re-running is a no-op (gates on the first OM concept already present).
Run:  python tools/mf_uw_template/_add_om_concepts.py
"""
import json
import pathlib

REG = pathlib.Path(__file__).parent / "registry.json"
NEW_VERSION = "0.2.0"

# (key, label, category, om_field, target_addr, label_at, target_label)
_PROP = [
    ("om_address", "Location / Address", "om_prop", "address", "B5", "A5", "Location / Address"),
    ("om_num_buildings", "# Buildings", "om_prop", "num_buildings", "B7", "A7", "# Buildings"),
    ("om_num_stories", "Height (stories)", "om_prop", "num_stories", "B8", "A8", "Height (stories)"),
    ("om_year_built", "Year Built", "om_prop", "year_built", "B9", "A9", "Year Built"),
    ("om_lot_acres", "Lot Size (acres)", "om_prop", "lot_acres", "B10", "A10", "Lot Size (acres)"),
    ("om_gross_sqft", "Gross Sq Ft", "om_prop", "gross_sqft", "B11", "A11", "Gross Sq Ft"),
    ("om_parking_spaces", "Parking Spaces", "om_prop", "parking_spaces", "B12", "A12", "Parking Spaces"),
    ("om_building_class", "Building Class (A/B/C)", "om_prop", "building_class", "B13", "A13", "Building Class (A/B/C)"),
    ("om_amenity_tier", "Amenity Tier", "om_prop", "amenity_tier", "B14", "A14", "Amenity Tier (Standard / Mid / Luxury)"),
    ("om_total_rentable_sf", "Total Rentable SF", "om_prop", "total_rentable_sf", "B15", "A15", "Total Rentable SF"),
    ("om_studio_units", "Studio Units", "om_prop", "studio_units", "B16", "A16", "Studio Units"),
    ("om_1br_units", "1BR Units", "om_prop", "br1_units", "B17", "A17", "1BR Units"),
    ("om_2br_units", "2BR Units", "om_prop", "br2_units", "B18", "A18", "2BR Units"),
    ("om_3br_units", "3BR Units", "om_prop", "br3_units", "B31", "A31", "3BR Units"),
    ("om_city_market", "City / Market", "om_market", "city_market", "B20", "A20", "City / Market"),
    ("om_msa_name", "MSA Name", "om_market", "msa_name", "B21", "A21", "MSA Name"),
    ("om_msa_population", "MSA Population", "om_market", "msa_population", "B22", "A22", "MSA Population"),
    ("om_city_population", "City Population", "om_market", "city_population", "B23", "A23", "City Population"),
    ("om_population_growth", "Population Growth Rate", "om_market", "population_growth_rate", "B24", "A24", "Population Growth Rate"),
    ("om_avg_household_income", "Avg Household Income", "om_market", "avg_household_income", "B27", "A27", "Avg Household Income"),
    ("om_median_income", "Median Income", "om_market", "median_income", "B28", "A28", "Median Income"),
    ("om_school_rating", "School District Rating", "om_market", "school_rating", "B29", "A29", "School District Rating (1-10)"),
    ("om_blended_rent", "Blended Avg Monthly Rent", "om_market", "(unit_mix weighted)", "B32", "A32", "Blended Avg Monthly Rent"),
    ("om_avg_unit_sf", "Avg Unit SF", "om_market", "avg_unit_sf", "B33", "A33", "Avg Unit SF"),
    ("om_market_vacancy", "Market Vacancy Rate", "om_market", "market_vacancy_rate", "B34", "A34", "Market Vacancy Rate"),
    ("om_market_rent_growth", "Market Rent Growth", "om_market", "market_rent_growth", "B35", "A35", "Market Rent Growth (Annual)"),
    ("om_new_supply", "New Supply (Units U/C)", "om_market", "new_supply_units", "B36", "A36", "New Supply — Units Under Construction"),
    ("om_renter_pct", "Renter Household %", "om_market", "renter_pct", "B37", "A37", "Renter Household % of Population"),
    ("om_electric_meter", "Electric Meter", "om_prop", "electric_meter", "B39", "A39", "Electric Meter"),
    ("om_water_meter", "Water Meter", "om_prop", "water_meter", "B40", "A40", "Water Meter"),
    ("om_gas", "Gas", "om_prop", "gas", "B41", "A41", "Gas"),
    ("om_trash", "Trash", "om_prop", "trash", "B42", "A42", "Trash"),
    ("om_value_add_thesis", "Value-Add Thesis", "om_prop", "value_add_thesis", "B47", "A47", "Value-Add Thesis"),
]

# (key, label, om_field, col) — Rental Comps row-stride, anchor row 8, up to 15.
_COMP = [
    ("om_comp_distance", "Comp Distance (mi)", "distance_mi", "Q"),
    ("om_comp_name", "Comp Property", "name", "R"),
    ("om_comp_class", "Comp Class (A/B/C)", "building_class", "S"),
    ("om_comp_vintage", "Comp Vintage", "year_built", "T"),
    ("om_comp_units", "Comp # Units", "units", "U"),
    ("om_comp_unit_type", "Comp Unit Type", "unit_type", "V"),
    ("om_comp_avg_sf", "Comp Avg SF", "avg_sf", "W"),
    ("om_comp_asking_rent", "Comp Asking Rent /mo", "asking_rent", "X"),
    ("om_comp_concession", "Comp Concession (wks)", "concession_weeks", "Y"),
    ("om_comp_occupancy", "Comp Occupancy %", "occupancy", "AB"),
    ("om_comp_comment", "Comp Comment", "comment", "AD"),
]


def _prop_concept(key, label, category, om_field, addr, label_at, target_label):
    return {
        "key": key, "label": label, "category": category, "path": "om",
        "source": {"system": "mf_om", "sheet": "OM (PDF)", "address": om_field,
                   "label": f"Extracted from the Offering Memorandum ({om_field})"},
        "targets": {"v15": {"sheet": "Prop Info", "address": addr,
                            "label_at": label_at, "target_label": target_label}},
        "status": "mapped",
        "notes": "Populated by mf_om_extractor (LLM engine) → "
                 "mf_uw_model_writer._write_prop_info. Manual-input cell; OM fills it.",
    }


def _comp_concept(key, label, om_field, col):
    return {
        "key": key, "label": label, "category": "om_comp", "path": "om",
        "source": {"system": "mf_om", "sheet": "OM (PDF)", "address": om_field,
                   "label": f"Rent comparable {om_field} from the OM comp set"},
        "targets": {"v15": {"sheet": "Rental Comps", "address": f"{col}8+",
                            "label_at": f"{col}6", "target_label": label}},
        "status": "mapped",
        "notes": "Row-stride: one comp per row 8–22 (15 max). Z/AA (eff-rent, $/SF) "
                 "and the SUBJECT row 7 are template formulas, never written.",
    }


def main():
    reg = json.loads(REG.read_text())
    keys = {c["key"] for c in reg["concepts"]}
    if "om_address" in keys:
        print("No-op: OM concepts already present.")
        return

    for row in _PROP:
        reg["concepts"].append(_prop_concept(*row))
    for row in _COMP:
        reg["concepts"].append(_comp_concept(*row))

    # source system + path legends
    reg.setdefault("category_legend", {}).update({
        "om_prop": "OM property physical details → Prop Info col B.",
        "om_market": "OM market / demographic data → Prop Info col B (overlaps the AI Market Research tool).",
        "om_comp": "OM submarket rent comparable → Rental Comps rows 8–22.",
    })

    # narrow the Prop Info manual-input note (most of it is now OM-mapped)
    for it in reg.get("intake_targets_unmapped", []):
        if it.get("sheet") == "Prop Info":
            it["rows_range"] = "rows 25-26, 43-46 (renter-age pop, other notes)"
            it["notes"] = ("Residual manual / AI-Market-Research cells: renter-age "
                           "population (B25/B26) and the free-text 'Other notes' block "
                           "(B43-B46). The rest of Prop Info is now OM-mapped (path=om).")

    # retire the OM open-question
    reg["open_questions"] = [
        q for q in reg["open_questions"]
        if not (isinstance(q, str) and q.startswith("OM (Offering Memorandum) intake — NOT BUILT"))
    ]
    reg["open_questions"].insert(0,
        "RESOLVED by the OM intake build (MF v0.5.0, mf_om_extractor + writer): "
        "OM property details + market block → Prop Info, rent comps → Rental Comps. "
        "Extraction defaults to an LLM engine (Claude structured output); a basic "
        "no-API labelled-facts engine is the fallback. Three OM formats validated "
        "(MMG/Blairstone, IPA/Avana, CBRE/Ascend). Remaining OM follow-ups: "
        "(a) demographics overlap the AI Market Research tool — OM wins when present; "
        "(b) broker pro-forma captured but intentionally NOT written (UW trusts the T-12).")

    reg["registry_version"] = NEW_VERSION
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    n_prop, n_comp = len(_PROP), len(_COMP)
    print(f"Added {n_prop} Prop Info + {n_comp} comp concepts. "
          f"registry_version -> {NEW_VERSION}. Total concepts: {len(reg['concepts'])}.")


if __name__ == "__main__":
    main()
