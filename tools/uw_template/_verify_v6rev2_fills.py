"""End-to-end verification of the v6 rev2 Prop Info + Scenarios col-B fills,
on the operator's actual Homestead RR v2 + March 2026 T12. Mirrors app.py's
parse -> compute -> populate flow. Read-only (no repo files written)."""
import io
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from normalizer import normalize_rent_roll, MappingSet  # noqa: E402
from t12_normalizer import parse_t12, read_descmap_descriptions  # noqa: E402
from uw_output_model import compute_uw_output_values, compute_uw_output_monthly  # noqa: E402
from uw_template_writer import populate_uw_template  # noqa: E402

RR = Path("/Users/erikjavellana/Library/CloudStorage/Dropbox/Erik Javellana - Deal Review/"
          "Deals under review/ALF_FL_Pensacola_HomesteadVillage/Broker Docs/"
          "Financials and Census/2026-04-24 Homestead Village Rent Roll v2.xlsx")
T12 = Path("/Users/erikjavellana/Library/CloudStorage/Dropbox/Erik Javellana - Deal Review/"
           "Deals under review/ALF_FL_Pensacola_HomesteadVillage/Broker Docs/"
           "Financials and Census/March 2026 T12.xlsx")
BUNDLED = ROOT / "ALF_Financial_Analyzer_Only.xlsx"
V6 = ROOT / "assets" / "ALF_UW_Template_v6.xlsx"


def money(v):
    return f"${v:,.0f}" if isinstance(v, (int, float)) else str(v)


def main() -> int:
    print("Parsing RR…")
    rr = normalize_rent_roll(str(RR), mappings=MappingSet())
    print(f"  {len(rr.condensed)} units")

    print("Parsing T12…")
    descmap = read_descmap_descriptions(openpyxl.load_workbook(BUNDLED, data_only=True))
    t12 = parse_t12(T12.read_bytes(), descmap)

    print("Computing UW values…")
    cv = compute_uw_output_values(rr, t12)
    mo = compute_uw_output_monthly(rr, t12)

    print("Populating UW Template v6 rev2…")
    out_bytes, report = populate_uw_template(
        BUNDLED.read_bytes(), V6.read_bytes(),
        template_version="v6", computed_values=cv, computed_monthly=mo,
    )
    wb = openpyxl.load_workbook(io.BytesIO(out_bytes), data_only=False)
    pi, sc, ta = wb["Prop Info"], wb["Scenarios"], wb["T-12 Analysis"]

    print("\n── Prop Info ──")
    for addr, lbl in [("B6", "# Units"), ("B11", "Gross Sq Ft"), ("B13", "Asset Class"),
                      ("B15", "Licensed total"), ("B21", "Occ IL"), ("B22", "Occ AL"), ("B23", "Occ MC")]:
        print(f"  {addr} {lbl:16}= {pi[addr].value}")

    print("\n── Scenarios col-B INCOME (Actuals) ──")
    for addr, lbl in [("B39", "Beds IL"), ("B40", "Rate IL"), ("B42", "Vac% IL"),
                      ("B45", "Beds AL"), ("B46", "Rate AL"),
                      ("B51", "Beds MC"), ("B52", "Rate MC"),
                      ("B72", "Care Fees%"), ("B74", "2nd Person"), ("B75", "Other Income")]:
        v = sc[addr].value
        print(f"  {addr} {lbl:12}= {v if not isinstance(v,float) else round(v,4)}")

    print("\n── Scenarios col-B EXPENSES (Actuals) ──")
    for addr, lbl in [("B81", "Care staff"), ("B89", "Total Labor(f)"), ("B99", "Food"),
                      ("B121", "Other/Misc"), ("B122", "Total Non-Labor(f)"), ("B123", "Mgmt Fee")]:
        print(f"  {addr} {lbl:18}= {money(sc[addr].value)}")

    print("\n── Reconciliation: Scenarios vs T-12 Analysis ──")
    # rebuild the scenario formula chain in python (openpyxl doesn't evaluate)
    def f(a):
        v = sc[a].value
        return v if isinstance(v, (int, float)) else 0
    gpr = sum(f(b) * f(r) * 12 for b, r in [("B39","B40"),("B45","B46"),("B51","B52"),("B57","B58")])
    care_fees = f("B72") * gpr
    egi_scn = gpr - (f("B66") if isinstance(sc["B66"].value,(int,float)) else 0) \
        + care_fees + f("B74") + f("B75")
    # simpler: net base = sum(occ*rate*12) since vac reconstructs it
    net_base = 0.0
    for bcode in ("il","al","mc"):
        net_base += cv[f"occupied_beds_{bcode}"] * cv[f"base_rent_{bcode}"]/max(cv[f"occupied_beds_{bcode}"],1)
    print(f"  T-12 actual EGI (cv['egi'])          = {money(cv['egi'])}")
    print(f"  Scenarios GPR (Σ licensed×rate×12)   = {money(gpr)}")
    print(f"  Σ T-12 base rent (il+al+mc)          = {money(cv['base_rent_il']+cv['base_rent_al']+cv['base_rent_mc'])}")
    print(f"  Scenarios care_fees (B72×GPR)        = {money(care_fees)}  vs T-12 total LOC {money(cv['loc_il']+cv['loc_al']+cv['loc_mc'])}")
    print(f"  Scenarios Other Income (B75)         = {money(f('B75'))}")

    print(f"\n  populate report: {report.summary.get('written')} written, "
          f"{report.summary.get('computed_in_python')} computed-in-python")
    # count how many of the new keys landed
    new_written = [r for r in report.results if r.key.startswith(('scn_','rr_unit','rr_gross','asset_class')) and r.outcome=='written']
    print(f"  new Prop Info/Scenarios concepts written: {len(new_written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
