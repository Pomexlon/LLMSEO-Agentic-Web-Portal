# weekly_lvi_update.py
import csv, datetime, json
from serp_agent import run_serp_queries
from pagespeed_agent import fetch_lighthouse_perf
from kpi_scoring import compute_kpis, serp_score_from_df, combine_lvi
import pandas as pd

PROJECT = "ASI-C"
DOMAIN = "www.asi-c.co.uk"
URL = "https://www.asi-c.co.uk"
KEYWORDS_FILE = "asi_c_seo_pack.json"
OUTPUT = "data/lvi_history.csv"

with open(KEYWORDS_FILE) as f:
    kw_pack = json.load(f)
keywords = kw_pack["keywords"][:5]

# 1️⃣ Run SERP
rows = run_serp_queries(DOMAIN, keywords, gl="uk")
serp_df = pd.DataFrame(rows)
serp_score = serp_score_from_df(serp_df, DOMAIN)

# 2️⃣ Get PSI speed score
psi_score, _ = fetch_lighthouse_perf(URL, strategy="mobile")

# 3️⃣ Compute KPI + LVI
res = {"title": "Automated Weekly Run"}
kpi = compute_kpis(res, serp_score)
kpi["speed_score"] = psi_score
kpi["lvi"] = combine_lvi(
    kpi["serp_score"],
    kpi["technical_score"],
    kpi["content_score"],
    kpi["eeat_score"],
    kpi["speed_score"],
)

# 4️⃣ Append to CSV
ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
row = {"timestamp": ts, "project": PROJECT, "domain": DOMAIN, "url": URL, **kpi}
try:
    df = pd.read_csv(OUTPUT)
    df = pd.concat([df, pd.DataFrame([row])])
except FileNotFoundError:
    df = pd.DataFrame([row])
df.to_csv(OUTPUT, index=False)
print(f"✅ Weekly LVI update saved → {OUTPUT}")

