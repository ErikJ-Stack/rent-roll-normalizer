"""Author the synthetic RealPage OneSite "RENT ROLL DETAIL" .xls fixture used by
tests/test_mf_rr_ar.py (OneSite format + legacy .xls support). Run once to
regenerate `onesite_synthetic.xls`; needs `xlwt` (authoring-only — the runtime
parser reads .xls via xlrd, which is in requirements.txt).

    python3 tests/fixtures/mf/_build_onesite_synthetic.py

Synthetic, no real resident/financial data. Mirrors the Ascend Brunswick export:
a banner band, the 31-col header at row 6, units that repeat across lease rows
(current + Applicant / Pending-renewal), and horizontal per-code charge columns.
"""
import datetime as dt
import os

import xlwt

HEADER = [
    "Resh ID", "Lease ID", "Unit", "Floorplan", "Unit \nDesignation", "SQFT",
    "Unit/Lease Status", "Name", "Move-In", "Move-Out", "Lease Start", "Lease End",
    "Market + Addl.", "Sub Journal", "Required\nDeposit", "Dep On Hand", "Balance",
    "Lease Rent", "RENT", "INTERNET", "TRASH", "PACKAGE", "PEST", "COMMFEE",
    "PETRENT", "GARAGE", "CONC/UP", "STORAGE", "EMPDISC", "CONC/CO", "Total Billing",
]

# col index -> value, per data row. Cols not set default to "".
def row(unit, status, sqft=None, name="", market=0, req_dep=0, dep=0, balance=0,
        lease_rent=0, rent=0, internet=0, trash=0, package=0, pest=0, commfee=0,
        petrent=0, garage=0, conc_up=0, storage=0, empdisc=0, conc_co=0,
        total=0, move_in=None):
    r = [""] * 31
    r[2], r[3], r[5], r[6], r[7] = unit, "FP1", sqft, status, name
    r[8] = move_in if move_in else ""
    r[12], r[14], r[15], r[16] = market, req_dep, dep, balance
    r[17], r[18] = lease_rent, rent
    r[19], r[20], r[21], r[22], r[23] = internet, trash, package, pest, commfee
    r[24], r[25], r[26], r[27], r[28], r[29] = petrent, garage, conc_up, storage, empdisc, conc_co
    r[30] = total
    return r


DATA = [
    # A-101 Occupied: base + ancillaries + a concession; one real date cell.
    row("A-101", "Occupied", 900, "Jane Doe", market=1500, req_dep=500, dep=500,
        balance=25.0, lease_rent=1400, rent=1400, internet=50, trash=20, petrent=30,
        conc_up=-100, total=1400, move_in=dt.datetime(2025, 4, 25)),
    # A-102 Occupied + Pending-renewal secondary -> one unit, charges from primary.
    row("A-102", "Occupied", 950, "Bob Roe", market=1600, dep=600,
        lease_rent=1500, rent=1500, garage=75, storage=25, total=1600),
    row("A-102", "Pending renewal", 950, "Bob Roe", lease_rent=1550, rent=1550, total=1550),
    # A-103 Vacant-Leased + Applicant -> committed rent from the applicant row,
    #       actual = 0 (not billing yet), ancillaries empty (no income yet).
    row("A-103", "Vacant-Leased", 1000, market=1700, total=0),
    row("A-103", "Applicant", 1000, "New Tenant", lease_rent=1650, rent=1650,
        internet=50, total=1700),
    # A-104 plain Vacant.
    row("A-104", "Vacant", 1000, market=1450, total=0),
    # A-105 Admin/Down.
    row("A-105", "Admin/Down", 1000, market=1500, total=0),
    # A-106 Occupied-NTV -> Occupied On Notice.
    row("A-106", "Occupied-NTV", 950, "Leaving Soon", market=1550,
        lease_rent=1480, rent=1480, total=1480),
]


def build(path):
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sheet1")
    date_style = xlwt.easyxf(num_format_str="MM/DD/YYYY")
    band = ["OneSite Report", "RENT ROLL DETAIL", "05/28/2026 12:00 PM",
            "As of Date: 04/30/2026", "Parameters: Property=Synthetic"]
    for i, txt in enumerate(band):
        ws.write(i, 0, txt)
    for c, h in enumerate(HEADER):
        ws.write(5, c, h)
    for ri, data in enumerate(DATA):
        for c, v in enumerate(data):
            if isinstance(v, dt.datetime):
                ws.write(6 + ri, c, v, date_style)
            elif v != "":
                ws.write(6 + ri, c, v)
    # trailing summary block that must stop the unit walk
    ws.write(6 + len(DATA), 2, "Future Residents")
    ws.write(7 + len(DATA), 2, "999-999")  # would be parsed if the break failed
    ws.write(7 + len(DATA), 6, "Applicant")
    wb.save(path)
    print("wrote", path)


if __name__ == "__main__":
    build(os.path.join(os.path.dirname(__file__), "onesite_synthetic.xls"))
