"""ECI lookups for the figures (see fetch_eci.py)."""
import csv
from pathlib import Path

ECI = {}
for r in csv.DictReader(open(Path(__file__).with_name("eci.csv"))):
    if r["eci"]:
        lo, hi = r["eci_ci_low"], r["eci_ci_high"]
        ECI[r["model"]] = (float(r["eci"]), (float(lo), float(hi)) if lo and hi else None)
