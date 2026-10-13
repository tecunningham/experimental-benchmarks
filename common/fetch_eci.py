"""Fetch Epoch Capabilities Index (ECI) scores for the models in common/models.py -> common/eci.csv.

Source: Epoch AI benchmark data (https://epoch.ai/data/benchmark_data.zip, epoch_capabilities_index/eci_scores.csv).
"""
import csv
import io
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.models import MODELS

URL = "https://epoch.ai/data/benchmark_data.zip"
with urllib.request.urlopen(URL, timeout=120) as r:
    z = zipfile.ZipFile(io.BytesIO(r.read()))
rows = {r["Model"]: r for r in csv.DictReader(io.TextIOWrapper(z.open("epoch_capabilities_index/eci_scores.csv")))}
out = Path(__file__).with_name("eci.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "epoch_name", "eci", "eci_ci_low", "eci_ci_high", "release_date", "fetched"])
    for m, name, _ in MODELS:
        r = rows.get(f"Claude {name}")
        w.writerow([m, r["Model"] if r else "", r["eci"] if r else "", r.get("eci_ci_low", "") if r else "",
                    r.get("eci_ci_high", "") if r else "", r["date"] if r else "", date.today().isoformat()])
        print(f"{name:12s} {r['eci'] if r else 'no ECI score'}")
