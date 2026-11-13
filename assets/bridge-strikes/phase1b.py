"""Phase 1b: site-level view, backtest by site, per-unit step-change test. Reads the clean CSV from phase1.py."""
import json
import numpy as np
import pandas as pd

d = pd.read_csv("bridge_strikes_clean.csv", dtype={"bin": str, "site": str}, parse_dates=["date"])
lab = pd.read_csv("bridge_labels.csv", dtype={"bin": str, "site": str}).set_index("bin")
YEARS = list(range(2013, 2026))
MINSEG = 2  # each side of the split must span at least 2 years, so one hot year is not called a step
import os
SEED = int(os.environ.get("SEED", 11))
out = {}

def unit_table(col):
    b = d[d[col].notna()]
    return b.groupby(["year", col]).size().unstack(fill_value=0).reindex(YEARS, fill_value=0)

def backtest(yc, window, Ns=(5, 10, 20), years=range(2016, 2026)):
    res = {N: [] for N in Ns}
    for Y in years:
        lo = 0 if window is None else Y - window
        hist = yc.loc[(yc.index < Y) & (yc.index >= lo)].sum()
        order = hist.sort_values(ascending=False, kind="stable").index  # ties: lower id first
        cur = yc.loc[Y]
        for N in Ns:
            res[N].append(cur[order[:N]].sum() / cur.sum())
    return {N: round(100 * float(np.mean(v)), 1) for N, v in res.items()}

for col in ("bin", "site"):
    yc = unit_table(col)
    tot = yc.sum().sort_values(ascending=False)
    out[col] = {
        "units": int(len(tot)),
        "coverage_all_time_in_sample": {n: round(100 * float(tot.head(n).sum() / tot.sum()), 1) for n in (5, 10, 20)},
        "backtest_2016_25": {"all_time": backtest(yc, None), "last3": backtest(yc, 3), "last1": backtest(yc, 1)},
        "top10": [{"id": k, "strikes": int(v)} for k, v in tot.head(10).items()],
    }

# site labels: use label of the largest ID in the site
sl = lab.reset_index()
sl["strikes"] = sl.bin.map(d.groupby("bin").size())
site_label = sl.sort_values("strikes", ascending=False).drop_duplicates("site").set_index("site").label
for r in out["site"]["top10"]:
    r["label"] = site_label[r["id"]] if r["id"] in site_label.index else ""
    r["ids"] = lab.index[lab.site == r["id"]].tolist()

# step-change test (one sudden change in yearly rate), simulation p-value that accounts for picking the best split year
def lr_max(counts):
    # counts: (B, 13) array
    N = counts.sum(axis=1)
    cs = np.cumsum(counts, axis=1)
    best = np.zeros(len(counts))
    base = N * np.log(np.where(N > 0, N / counts.shape[1], 1))
    for k in range(MINSEG, counts.shape[1] - MINSEG + 1):
        a1, a2 = cs[:, k - 1], N - cs[:, k - 1]
        t1 = np.where(a1 > 0, a1 * np.log(np.where(a1 > 0, a1 / k, 1)), 0)
        t2 = np.where(a2 > 0, a2 * np.log(np.where(a2 > 0, a2 / (counts.shape[1] - k), 1)), 0)
        best = np.maximum(best, 2 * (t1 + t2 - base))
    return best

def step_test(col, min_n=8, B=40000, seed=SEED):
    yc = unit_table(col)
    units = [u for u in yc.columns if yc[u].sum() >= min_n]
    rng = np.random.default_rng(seed)
    rows = []
    for u in units:
        x = yc[u].to_numpy()
        obs = lr_max(x[None, :])[0]
        sims = rng.multinomial(int(x.sum()), [1 / 13] * 13, size=B)
        p = (1 + (lr_max(sims) >= obs - 1e-9).sum()) / (B + 1)
        cs = np.cumsum(x); N = x.sum(); bestk, bestv = 1, -1
        for k in range(MINSEG, 13 - MINSEG + 1):
            a1, a2 = cs[k - 1], N - cs[k - 1]
            v = (a1 * np.log(a1 / k) if a1 else 0) + (a2 * np.log(a2 / (13 - k)) if a2 else 0)
            if v > bestv: bestv, bestk = v, k
        rows.append({"unit": u, "n": int(N), "p": p, "split_from": YEARS[bestk],
                     "rate_before": round(cs[bestk - 1] / bestk, 2), "rate_after": round((N - cs[bestk - 1]) / (13 - bestk), 2)})
    r = pd.DataFrame(rows).sort_values("p")
    m = len(r); r["q"] = (r.p * m / np.arange(1, m + 1)).iloc[::-1].cummin().iloc[::-1].clip(upper=1)
    return r

for col in ("bin", "site"):
    r = step_test(col)
    r["label"] = r.unit.map(lab.label if col == "bin" else site_label)
    out[col]["step_tested"] = int(len(r))
    out[col]["step_q_lt_0.05"] = r[r.q < 0.05].round(4).to_dict("records")
    out[col]["step_q_0.05_0.15"] = r[(r.q >= 0.05) & (r.q < 0.15)].round(4).to_dict("records")

json.dump(out, open("summary_sites.json", "w"), indent=1, default=str)
for col in ("bin", "site"):
    o = out[col]
    print(f"\n=== unit: {col} | units {o['units']} | in-sample coverage top5/10/20 {o['coverage_all_time_in_sample']}")
    print("backtest 2016-25:", o["backtest_2016_25"])
    print("tested", o["step_tested"], "units with >=8 strikes; q<0.05:")
    for x in o["step_q_lt_0.05"]: print("  ", x["unit"], x["label"], f"n={x['n']} from {x['split_from']} {x['rate_before']}->{x['rate_after']}/yr p={x['p']:.4f} q={x['q']:.3f}")
    print("borderline q<0.15:")
    for x in o["step_q_0.05_0.15"]: print("  ", x["unit"], x["label"], f"n={x['n']} from {x['split_from']} {x['rate_before']}->{x['rate_after']}/yr q={x['q']:.3f}")
print("\nsite top10:")
for r in out["site"]["top10"]: print("  ", r["id"], r["strikes"], r["label"], r["ids"])
