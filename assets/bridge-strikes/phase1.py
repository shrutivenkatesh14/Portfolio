"""Phase 1: clean NYC bridge strike data and run the analysis. Every rule is logged."""
import json, re
import numpy as np
import pandas as pd

RAW = "NYC_Bridge_Strike_Data_20261106.csv"
log = []  # cleaning log, written to cleaning_log.txt

# explicit missing tokens: only blank and "N/A" (license column) count as missing
d = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=["", "N/A"])
d.columns = ["date", "borough", "direction", "main_street", "cross_street", "type",
             "truck_route", "struck_overpass", "license_state", "bin", "lat", "lon"]
log.append(f"Loaded {len(d)} rows, nothing dropped. Missing = blank or the text N/A only (343 N/A + 2 blank in license).")

# dates: keep the date part, time is a midnight placeholder
d["date"] = pd.to_datetime(d["date"], format="%m/%d/%Y %I:%M:%S %p")
log.append(f"Dates parsed. Time-of-day always midnight: {(d.date.dt.hour==0).all()}. Range {d.date.min().date()} to {d.date.max().date()}.")
d["year"] = d.date.dt.year
d["weekday"] = d.date.dt.day_name()

# bridge id stays text
d["bin"] = d["bin"].str.strip()
log.append(f"Bridge ID kept as text. Missing: {d['bin'].isna().sum()}.")

# coordinates: malformed values flagged, not guessed
lat = pd.to_numeric(d["lat"], errors="coerce")
d["lat_malformed"] = lat.isna() & d["lat"].notna()
d["lat"] = lat
d["lon"] = pd.to_numeric(d["lon"], errors="coerce")
log.append(f"Malformed latitude set to missing and flagged: {int(d.lat_malformed.sum())} row(s).")
# plausibility box for NYC
out = d[(d.lat.notna()) & ~d.lat.between(40.4, 41.0)]
log.append(f"Latitudes outside NYC box: {len(out)}.")


# ---- bridge ID repairs (decisions: fix conflicting IDs, recover missing IDs by coordinates) ----
d["bin_original"] = d["bin"]
d["bin_source"] = np.where(d["bin"].notna(), "original", "missing")
def _med(df):
    g = df[df["bin"].notna() & df.lat.notna() & (df.lon < 0)].groupby("bin")
    return g.lat.median(), g.lon.median(), g.main_street.agg(lambda s: s.mode().iat[0])
def _m(la0, lo0, la, lo):
    return np.hypot((la - la0) * 111_000, (lo - lo0) * 111_000 * np.cos(np.radians(la0)))
def _nearest(r, mlat, mlon):
    dist = _m(r.lat, r.lon, mlat, mlon).sort_values()
    return dist.index[0], float(dist.iat[0]), float(dist.iat[1])
mlat, mlon, mmain = _med(d)
fixed = cleared = 0
for i, r in d[d["bin"].notna() & d.lat.notna() & (d.lon < 0)].iterrows():
    off = float(_m(r.lat, r.lon, mlat[r["bin"]], mlon[r["bin"]]))
    if off > 1000 and r.main_street != mmain[r["bin"]]:   # street name AND location both contradict the ID
        cand = mlat.drop(r["bin"])
        nb, m1, m2 = _nearest(r, cand, mlon.drop(r["bin"]))
        if m1 <= 25 and m2 > 3 * max(m1, 1):
            d.at[i, "bin"], d.at[i, "bin_source"] = nb, "reassigned_by_coords"; fixed += 1
        else:
            d.at[i, "bin"], d.at[i, "bin_source"] = np.nan, "cleared_conflict"; cleared += 1
log.append(f"Rows whose street name and location both contradict their bridge ID: {fixed + cleared}. "
           f"{fixed} reassigned to the one bridge within 25 m, {cleared} set to missing. Original ID kept in bin_original.")
mlat, mlon, mmain = _med(d)
rec = 0
for i, r in d[d["bin"].isna() & d.lat.notna() & (d.lon < 0)].iterrows():
    nb, m1, m2 = _nearest(r, mlat, mlon)
    if m1 <= 25 and m2 > 3 * max(m1, 1):
        d.at[i, "bin"], d.at[i, "bin_source"] = nb, "recovered_by_coords"; rec += 1
log.append(f"Missing bridge IDs recovered from coordinates (one bridge within 25 m, next bridge at least 3x farther): {rec}. "
           f"Rows still without a bridge ID: {int(d['bin'].isna().sum())}.")

# flags for gaps, nothing filled
d["no_bin"] = d["bin"].isna()
d["no_license"] = d["license_state"].isna()
d["no_direction"] = d["direction"].isna()
d["no_cross"] = d["cross_street"].isna()
d["no_coords"] = d.lat.isna() | d.lon.isna()
log.append("TYPE is STRIKE in all rows: %s. Column kept, ignored in analysis." % (d.type == "STRIKE").all())

# duplicates (kept by default)
key = ["date", "bin", "main_street", "cross_street", "direction"]
d["dup_of_earlier"] = d.duplicated(key, keep="first")
log.append(f"Exact repeats on {key}: {int(d.dup_of_earlier.sum())} extra rows. Kept; sensitivity check below.")

def nice(t):
    if pd.isna(t): return t
    t = t.title()
    t = re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1)+m.group(2).lower(), t)
    for a, b_ in (("Fdr", "FDR"), ("Brooklyn Queens", "Brooklyn-Queens")):
        t = t.replace(a, b_)
    return t

# canonical label per bridge id: most common street pair
b = d[~d.no_bin].copy()
pair = (b.groupby(["bin", "main_street", "cross_street"], dropna=False).size()
          .reset_index(name="n").sort_values(["bin", "n"], ascending=[True, False]))
canon = pair.drop_duplicates("bin").set_index("bin")
coord = b.groupby("bin")[["lat", "lon"]].median()
labels = pd.DataFrame({
    "main_street": canon.main_street.map(nice),
    "cross_street": canon.cross_street.fillna("(missing)").map(nice),
    "n_label_variants": pair.groupby("bin").size(),
}).join(coord)
labels["label"] = labels.main_street + " at " + labels.cross_street
bor = b.groupby("bin").borough.agg(lambda s: s.mode().iat[0])
labels["borough"] = bor
log.append(f"Canonical label built for {len(labels)} bridge IDs from the most common street pair. "
           f"{int((labels.n_label_variants>1).sum())} IDs have more than one street pair.")


# coordinate sanity: wrong-sign longitude and rows far from their own bridge's median point
d["coord_off_m"] = np.nan
med = d["bin"].map(labels["lat"]), d["bin"].map(labels["lon"])
ok_ = d.lat.notna() & d.lon.notna() & d["bin"].notna()
d.loc[ok_, "coord_off_m"] = np.hypot((d.lat[ok_] - med[0][ok_]) * 111_000,
                                     (d.lon[ok_] - med[1][ok_]) * 111_000 * np.cos(np.radians(med[0][ok_])))
d["lon_wrong_sign"] = d.lon > 0
d["coord_suspect"] = (d.coord_off_m > 1000) | d.lon_wrong_sign
log.append(f"Rows with suspect coordinates (wrong-sign longitude, or over 1,000 m from the median point of their own bridge ID): "
           f"{int(d.coord_suspect.sum())}. Flagged, values kept; counts unaffected. Exclude from any map.")

# site id: bridge IDs within 30 m of each other on the same roadway are one physical site
ids = labels.dropna(subset=["lat", "lon"]).index.tolist()
parent = {i: i for i in ids}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for i, a in enumerate(ids):
    for c in ids[i + 1:]:
        if labels.main_street[a].lower() != labels.main_street[c].lower():
            continue
        dist = np.hypot((labels.lat[a] - labels.lat[c]) * 111_000,
                        (labels.lon[a] - labels.lon[c]) * 111_000 * np.cos(np.radians(labels.lat[a])))
        if dist <= 30:
            parent[find(a)] = find(c)
site_of = {i: min(j for j in ids if find(j) == find(i)) for i in ids}
labels["site"] = labels.index.map(site_of)
d["site"] = d["bin"].map(site_of)
log.append(f"Site id: bridge IDs within 30 m of each other on the same roadway are merged. "
           f"{len(ids)} bridge IDs become {labels.site.nunique()} sites. Raw bridge ID kept alongside.")

d.to_csv("bridge_strikes_clean.csv", index=False)
labels.to_csv("bridge_labels.csv")

# ---------- analysis ----------
S = {}
S["rows"] = len(d)
S["per_year"] = d.groupby("year").size().to_dict()
S["truck_route_share_no"] = float((d.truck_route == "NO").mean())
S["weekday_share"] = float(d.weekday.isin(["Monday","Tuesday","Wednesday","Thursday","Friday"]).mean())
S["top6_roadway_share"] = float(d.main_street.value_counts().head(6).sum() / len(d))
S["roadway_top"] = d.main_street.value_counts().head(12).to_dict()

# coverage curve (all-time, rows with bin)
cnt = b.groupby("bin").size().sort_values(ascending=False)
S["unique_bridges"] = int(len(cnt))
S["coverage_all_time"] = {int(n): float(cnt.head(n).sum() / cnt.sum()) for n in (5, 10, 20, 30, 50)}

# backtest: rank on earlier years, score on year Y
rng = np.random.default_rng(42)
all_bins = cnt.index.to_numpy()
yc = b.groupby(["year", "bin"]).size().unstack(fill_value=0)
def backtest(window, years=range(2016, 2026), Ns=(5, 10, 20)):
    res = {N: [] for N in Ns}
    for Y in years:
        lo = 0 if window is None else Y - window
        hist = yc.loc[(yc.index < Y) & (yc.index >= lo)].sum().sort_values(kind="stable", ascending=False)
        cur = yc.loc[Y]
        for N in Ns:
            res[N].append(cur[hist.head(N).index].sum() / cur.sum())
    return {N: float(np.mean(v)) for N, v in res.items()}
def oracle(years=range(2016, 2026), Ns=(5, 10, 20)):
    return {N: float(np.mean([yc.loc[Y].nlargest(N).sum() / yc.loc[Y].sum() for Y in years])) for N in Ns}
def rand(years=range(2016, 2026), Ns=(5, 10, 20)):
    return {N: float(np.mean([yc.loc[Y].sum() and yc.loc[Y][rng.choice(all_bins, N, replace=False)].sum()/yc.loc[Y].sum() for Y in years for _ in range(200)])) for N in Ns}
S["backtest"] = {"all_time": backtest(None), "last3": backtest(3), "last1": backtest(1),
                 "oracle": oracle(), "random": rand()}
S["backtest_2023_25"] = {"all_time": backtest(None, range(2023, 2026)), "last3": backtest(3, range(2023, 2026)),
                         "last1": backtest(1, range(2023, 2026))}

# direction split at top bridges
top = cnt.head(10).index
dirs = []
for t in top:
    s = b[b["bin"] == t].direction.value_counts()
    dirs.append({"bin": t, "label": labels.loc[t, "label"], "strikes": int(cnt[t]),
                 "main_dir": s.index[0], "main_dir_n": int(s.iat[0])})
S["top10_direction"] = dirs

# truck route by roadway
tr = d.groupby("main_street").truck_route.agg(n="size", on_route=lambda s: int((s == "YES").sum()))
S["truck_by_roadway"] = tr.sort_values("n", ascending=False).head(12).to_dict("index")

# license 2019-2024 known only
L = d[(d.year.between(2019, 2024)) & d.license_state.notna()]
S["license_2019_24"] = {"n": len(L), "ny_share": float((L.license_state == "NY").mean())}

# duplicate sensitivity
nd = d[~d.dup_of_earlier & ~d.no_bin]
cnt2 = nd.groupby("bin").size().sort_values(ascending=False)
S["dup_sensitivity"] = {
    "top10_same_set": bool(set(cnt2.head(10).index) == set(cnt.head(10).index)),
    "top10_overlap": len(set(cnt2.head(10).index) & set(cnt.head(10).index)),
    "coverage10_with": float(cnt.head(10).sum()/cnt.sum()),
    "coverage10_without": float(cnt2.head(10).sum()/cnt2.sum())}

# recover missing bin by coordinates: nearest known bridge within 25 m
from math import radians, cos
miss = d[d.no_bin & ~d.no_coords]
known = labels.dropna(subset=["lat", "lon"])
rec = []
for i, r in miss.iterrows():
    dy = (known.lat - r.lat) * 111_000
    dx = (known.lon - r.lon) * 111_000 * cos(radians(r.lat))
    dist = np.sqrt(dx**2 + dy**2).sort_values()
    rec.append({"row": int(i), "nearest_bin": dist.index[0], "meters": float(dist.iat[0]),
                "second_m": float(dist.iat[1])})
rec = pd.DataFrame(rec)
S["bin_recovery"] = {"missing_bin_with_coords": len(miss),
                     "within_25m": int((rec.meters <= 25).sum()),
                     "within_25m_and_unambiguous": int(((rec.meters <= 25) & (rec.second_m > 3*rec.meters.clip(lower=1))).sum())}

with open("summary.json", "w") as f:
    json.dump(S, f, indent=1, default=str)
open("cleaning_log.txt", "w").write("\n".join(log))
print("\n".join(log))
print(json.dumps(S, indent=1, default=str)[:6000])
