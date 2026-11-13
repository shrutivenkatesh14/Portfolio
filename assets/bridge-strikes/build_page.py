"""Builds bridge-strikes.html (album shell + Plotly charts) from the clean data. Run phase1.py and phase1b.py first."""
import json, re
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

d = pd.read_csv("bridge_strikes_clean.csv", dtype={"bin": str, "site": str}, parse_dates=["date"])
lab = pd.read_csv("bridge_labels.csv", dtype={"bin": str, "site": str})
S = json.load(open("summary_sites.json"))
YEARS = list(range(2013, 2026)); T = len(d)
b = d[d.site.notna()]
yc = b.groupby(["year", "site"]).size().unstack(fill_value=0).reindex(YEARS, fill_value=0)
lab["n"] = lab["bin"].map(d.groupby("bin").size())
slabel = lab.sort_values("n", ascending=False).drop_duplicates("site").set_index("site")
near = lambda s: slabel.label[s] + ("" if (lab[lab.site == s].n_label_variants.max() == 1) else "")  # label text only
pct = lambda x: f"{100 * x:.0f}%"

# ---- backtest curves: rank on earlier years, score on the next year, for N = 1..30 ----
NS = list(range(1, 31)); YS = range(2016, 2026)
def curve(window):
    out = []
    for N in NS:
        v = []
        for Y in YS:
            lo = 0 if window is None else Y - window
            h = yc.loc[(yc.index < Y) & (yc.index >= lo)].sum().sort_values(ascending=False, kind="stable")
            v.append(yc.loc[Y, h.index[:N]].sum() / yc.loc[Y].sum())
        out.append(100 * float(np.mean(v)))
    return out
cur = {"all": curve(None), "l3": curve(3), "l1": curve(1)}
orc = [100 * float(np.mean([yc.loc[Y].nlargest(N).sum() / yc.loc[Y].sum() for Y in YS])) for N in NS]
chance = [100 * N / yc.shape[1] for N in NS]
fwd10 = cur["all"][9]
def _cov(Y, w, N=10):
    lo = 0 if w is None else Y - w
    h_ = yc.loc[(yc.index < Y) & (yc.index >= lo)].sum().sort_values(ascending=False, kind="stable")
    return yc.loc[Y, h_.index[:N]].sum() / yc.loc[Y].sum()
wins = sum(_cov(Y, None) > _cov(Y, 3) for Y in YS)

BRICK, BLUE, OCHRE, GREY = "#B4553E", "#5B7F95", "#9A8236", "#8A8072"
FONT = dict(family="Courier Prime, Courier New, monospace", size=12)
def base(h, **kw):
    return dict(height=h, margin=dict(l=10, r=10, t=30, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=FONT, **kw)
GRID = dict(gridcolor="rgba(138,128,114,0.28)", zeroline=False, linecolor="rgba(138,128,114,0.6)")

# chart 1: coverage curve + slider
f1 = go.Figure()
spec = [("all", "All history", BRICK, True), ("l3", "Last 3 years", BLUE, True), ("l1", "Last year", OCHRE, "legendonly")]
for k, nm, col, vis in spec:
    f1.add_scatter(x=NS, y=cur[k], name=nm, mode="lines", line=dict(color=col, width=2.5), visible=vis, legendgroup=k,
                   hovertemplate="top %{x}: %{y:.0f}%<extra>" + nm + "</extra>")
f1.add_scatter(x=NS, y=orc, name="Best possible (hindsight)", mode="lines", line=dict(color=GREY, dash="dot"), legendgroup="o",
               hovertemplate="top %{x}: %{y:.0f}%<extra>best possible</extra>")
f1.add_scatter(x=NS, y=chance, name="Picked at random", mode="lines", line=dict(color=GREY, dash="dash", width=1), legendgroup="r",
               hovertemplate="top %{x}: %{y:.0f}%<extra>random</extra>")
f1.add_scatter(x=[10, 10], y=[cur["all"][9], cur["l3"][9]], mode="markers", showlegend=False, hoverinfo="skip",
               marker=dict(color=[BRICK, BLUE], size=11, line=dict(color="#F3EEE3", width=1.5)))
steps = [dict(method="update", label=str(N), args=[{"x": [[N, N]], "y": [[cur["all"][N - 1], cur["l3"][N - 1]]]}, [5]]) for N in NS]
f1.update_layout(**base(420), sliders=[dict(active=9, steps=steps, currentvalue=dict(prefix="Fund the top ", suffix=" sites", font=dict(size=14)),
                 pad=dict(t=44, b=0), len=0.96, x=0.02, ticklen=0, font=dict(size=11))],
                 xaxis=dict(title="Sites funded, ranked from past years only", **GRID),
                 yaxis=dict(title="Share of next year's strikes at those sites (%)", range=[0, 100], **GRID),
                 legend=dict(orientation="h", y=1.12, x=0, font=dict(size=12)))

# chart 2: persistence heatmap for the top 10 sites
top = yc.sum().sort_values(ascending=False).head(10).index.tolist()
f2 = go.Figure(go.Heatmap(z=yc[top].T.values, x=YEARS, y=[f"{slabel.label[s]}  ({int(yc[s].sum())})" for s in top],
                          colorscale=[[0, "#EFE6D8"], [0.35, "#E3B79B"], [1, "#8F3B2A"]], showscale=False, xgap=2, ygap=2,
                          texttemplate="%{z}", hovertemplate="%{y}<br>%{x}: %{z} strikes<extra></extra>"))
f2.update_layout(**base(400), yaxis=dict(autorange="reversed", automargin=True),
                 xaxis=dict(dtick=1, side="bottom", showgrid=False))

# chart 3: truck route split by roadway
rd = b.assign(main=b.main_street.str.title().str.replace("Fdr", "FDR")).groupby("main").truck_route.agg(
    n="size", on=lambda s: (s == "YES").sum()).sort_values("n", ascending=False).head(10)
f3 = go.Figure()
f3.add_bar(y=rd.index, x=rd.n - rd.on, orientation="h", name="Not a truck route", marker_color=BRICK, hovertemplate="%{y}: %{x}<extra>not a truck route</extra>")
f3.add_bar(y=rd.index, x=rd.on, orientation="h", name="Truck route", marker_color=BLUE, hovertemplate="%{y}: %{x}<extra>truck route</extra>")
f3.update_layout(**base(360), barmode="stack", yaxis=dict(autorange="reversed", automargin=True), xaxis=dict(title="Strikes, 2013 to 2025", **GRID),
                 legend=dict(orientation="h", y=1.1, x=0))
cfg = {"displayModeBar": False, "responsive": True}
h = lambda f: f.to_html(full_html=False, include_plotlyjs=False, config=cfg)

# ---- numbers for the prose ----
off = (d.truck_route == "NO").mean(); wk = d.weekday.isin(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]).mean()
top6 = d.main_street.value_counts().head(6).sum() / T
tr_on = int((d.truck_route == "YES").sum())
trk_roads = rd.index.tolist()
sit = b.groupby("site").size(); in10 = sit.sort_values(ascending=False).head(10).sum() / len(b)
def maindir(s):
    v = b[b.site == s].direction.value_counts(); return v.index[0], v.iat[0] / v.sum(), int(v.sum())
rows_tbl = "".join(f"<tr><td>{slabel.label[s]}</td><td>{n}</td><td>{maindir(s)[0]}</td><td>{pct(maindir(s)[1])}</td></tr>"
                   for s, n in sit.sort_values(ascending=False).head(10).items())
last_2231290 = b[b.site == "2231290"].date.max().strftime("%b %-d, %Y")
nov = d.date.min().strftime("%Y"); known = len(b)
lic = d[(d.year.between(2019, 2024)) & d.license_state.notna()]

body = f'''
<section style="padding-bottom:8px;"><div class="wrap">
<p class="eyebrow"><a href="../../projects.html">← Back to the collection</a></p>
<h1 style="font-size:clamp(2.2rem,5vw,3.6rem);">Which low bridges should the city fix first?</h1>
<p class="max-w lede">Trucks hit low bridges on New York City roads {T} times between 2013 and 2025. Most of those roads are not truck routes.
I used the city's strike reports to decide where a limited budget does the most good.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">How much does the ranking cover?</h2>
<p class="max-w">Each year from 2016 to 2025 I ranked sites using only earlier years, then counted how many of that year's strikes fell at the top ones.
Drag the slider to change how many sites are funded. Click a name in the legend to hide or show a line.</p>
{h(f1)}
<p class="max-w">Ranking on all history is about as good as ranking on the last three years or the last year. In the ten test years the all-history ranking came out ahead of the last-three-years ranking in {wins}, by small margins, so I read it as a tie. The gap to the best possible ranking is the cost of not knowing next year.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Hotspots move</h2>
<p class="max-w">Strikes per year at the ten sites with the most strikes. Total strikes in brackets. A site is one bridge, or several bridge IDs within 30 m on the same road.</p>
{h(f2)}
<p class="max-w">Three sites changed in a way chance does not explain (a test that allows for picking the best year, with false discoveries controlled). Hutchinson River Parkway at Westchester Avenue fell from about 14 strikes a year to 3 from 2019. Belt Parkway at 17th Avenue had about 6 a year, then none from 2023; its last strike was {last_2231290}. Henry Hudson Parkway at West 239th Street went from none through 2016 to about 4 a year.
I do not know why. Sites picked for a spike often calm down by chance, so a drop is not proof that anything worked, and a jump from zero may be better reporting.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Two different problems</h2>
<p class="max-w">Parkways are almost never marked as truck routes, so most strikes there are trucks on roads they should not be on. That is a routing, signage or enforcement problem. The {tr_on} strikes on truck routes sit mostly on a few other roads and are a clearance or geometry problem.</p>
{h(f3)}
<p class="max-w">{pct(wk)} of strikes happen Monday to Friday, which fits commercial traffic. There is no strong seasonal pattern.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Strikes come from one direction</h2>
<p class="max-w">At most of the busiest sites nearly every strike is in one direction of travel, so detection or signage can go on one approach, upstream of the bridge. The file does not say exactly what the direction field records.</p>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Site</th><th>Strikes</th><th>Main direction</th><th>Share</th></tr></thead><tbody>{rows_tbl}</tbody></table></div>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">What the data cannot say</h2>
<ul class="limits max-w">
<li>The file has no clearance height, vehicle type, damage, cost or traffic volume. So there are no rates and no savings claims.</li>
<li>Reports are not guaranteed complete.</li>
<li>Time of day is always midnight, so only day of week and month can be studied.</li>
<li>The driver-license state is missing in 37% of rows and its reporting changed over time. I only looked at 2019 to 2024, where New York licenses were {pct((lic.license_state == "NY").mean())} of {len(lic)} known rows, and drew no conclusion from it.</li>
<li>{T - known} of {T} rows have no bridge ID and are left out of the site counts. Street labels in the file are inconsistent, so each site uses its most common street pair. Labels for a few sites, such as FDR Drive near East 61st Street, cover a stretch of road.</li>
<li>No machine learning: {T} rows and no features beyond location cannot support a credible model.</li>
</ul>
<p class="max-w">Data: NYC Open Data, NYC Bridge Strike Data (jdn9-td9w), downloaded Nov 6, 2026. Cleaning rules are logged in the code.
<a href="phase1.py">phase1.py</a> · <a href="phase1b.py">phase1b.py</a> · <a href="build_page.py">build_page.py</a> · <a href="bridge_strikes_clean.csv">clean data</a> · <a href="cleaning_log.txt">cleaning log</a></p>
</div></section>
'''
css = '''<style>
.lede{font-size:18px;color:var(--ink)} .brief{display:grid;grid-template-columns:max-content 1fr;gap:10px 22px;max-width:760px;margin:22px 0 14px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.brief dt{font-family:var(--font-mono);font-size:12px;letter-spacing:.06em;color:var(--accent-ink);font-weight:700;padding-top:3px}.brief dd{margin:0;font-family:'Newsreader',Georgia,serif;font-size:16.5px;line-height:1.55;color:var(--ink)}
@media(max-width:560px){.brief{grid-template-columns:1fr;gap:2px}.brief dd{margin-bottom:10px}}
.js-plotly-plot{margin:18px 0 6px}.limits{padding-left:18px;color:var(--ink-soft)}.limits li{margin-bottom:8px}
.tbl-wrap{overflow-x:auto;margin-top:14px}.tbl{border-collapse:collapse;width:100%;max-width:760px;font-family:var(--font-mono);font-size:13px}
.tbl th,.tbl td{text-align:left;padding:8px 14px 8px 0;border-bottom:1px dotted var(--line);color:var(--ink)}.tbl th{font-size:11px;letter-spacing:.06em;color:var(--accent-ink)}
.plotly .xtick text,.plotly .ytick text,.plotly .gtitle,.plotly .g-xtitle text,.plotly .g-ytitle text,.plotly .legendtext,.plotly .slider-container text{fill:var(--ink)!important}
.plotly .slider-rail-rect{fill:var(--line)!important}.plotly .slider-grip-rect{fill:var(--accent-ink)!important}
</style>
<script src="plotly.min.js"></script>'''

desc = "Which low NYC bridges should be fixed first? Live Python analysis of 943 truck strikes, with a backtested ranking."
head = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<script>(function(){try{var t=localStorage.getItem('theme');if(!t)t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Bridge Strikes, live analysis — Shruti Venkatesh</title>
<meta name="description" content="DESC">
<link rel="icon" type="image/svg+xml" href="../../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Newsreader:ital,wght@0,400;0,500;1,400&family=Caveat:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../styles.css?v=20261112">
""".replace("DESC", desc) + css + """
</head>
<body class="wash-projects"><div class="album"><div class="page-content"><main>"""
foot = """</main>
<footer class="site-footer"><div class="wrap footer-row"><span>© 2026 Shruti Venkatesh. Data: NYC Open Data.</span><a href="../../projects.html">Back to the collection</a></div></footer>
</div></div></body></html>"""
page = head + body + foot
open("index.html", "w", encoding="utf-8").write(page)
open("plotly.min.js", "w").write(get_plotlyjs())
print("ok", len(page) // 1024, "KB; fwd10", round(fwd10, 1), "known", known, "in10", round(in10, 3))
