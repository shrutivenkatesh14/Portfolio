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
def base(h, t=30, **kw):
    return dict(height=h, margin=dict(l=10, r=10, t=t, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=FONT, **kw)
GRID = dict(gridcolor="rgba(138,128,114,0.28)", zeroline=False, linecolor="rgba(138,128,114,0.6)")

# chart 1: coverage curve, a rule at the chosen N, and a readout of every line at that N
f1 = go.Figure()
spec = [("all", "Every past year", BRICK, True), ("l3", "Last 3 years", BLUE, True), ("l1", "Last year only", OCHRE, "legendonly")]
for k, nm, col, vis in spec:
    f1.add_scatter(x=NS, y=cur[k], name=nm, mode="lines", line=dict(color=col, width=2.5), visible=vis,
                   hovertemplate="top %{x}: %{y:.0f}%<extra>" + nm + "</extra>")
f1.add_scatter(x=NS, y=orc, name="Best possible", mode="lines", line=dict(color=GREY, dash="dot"),
               hovertemplate="top %{x}: %{y:.0f}%<extra>best possible</extra>")
f1.add_scatter(x=NS, y=chance, name="At random", mode="lines", line=dict(color=GREY, dash="dash", width=1),
               hovertemplate="top %{x}: %{y:.0f}%<extra>random</extra>")
def r0(x):
    return int(x + 0.5)  # round half up, same as the page's JavaScript
def sentence(N):
    return ("Fix %d %s and you would have covered %d%% of next year's strikes, picking by every past year. Last 3 years: %d%%. Last year only: %d%%. At random: %d%%. Best possible: %d%%."
            % (N, "bridge" if N == 1 else "bridges", r0(cur["all"][N-1]), r0(cur["l3"][N-1]), r0(cur["l1"][N-1]), r0(chance[N-1]), r0(orc[N-1])))
f1.update_layout(**base(380, t=84), shapes=[dict(type="line", x0=10, x1=10, y0=0, y1=100, layer="below", line=dict(color=BRICK, width=1.5, dash="dot"))],
                 xaxis=dict(title="Bridges fixed", **GRID),
                 yaxis=dict(title="% of next year's strikes covered", range=[0, 100], **GRID),
                 legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, font=dict(size=12), itemclick=False, itemdoubleclick=False))
DATA_JS = json.dumps({k: [r0(v) for v in cur[k]] for k in cur} | {"o": [r0(v) for v in orc], "r": [r0(v) for v in chance]})
ctl = ("<div class='ctl' id='ctl' hidden><label for='nsites'>Bridges fixed: <b id='nv'>10</b></label>"
       "<input id='nsites' type='range' min='1' max='30' step='1' value='10' aria-controls='cov-chart' aria-describedby='readout' aria-valuetext='10 bridges. Covers %d%% of next year&#39;s strikes.'>" % r0(cur["all"][9]) +
       "<div class='ends' aria-hidden='true'><span>1</span><span>30</span></div>"
       "<p id='readout' class='readout'>" + sentence(10) + "</p>"
       "<div class='lines' role='group' aria-labelledby='lg'><span id='lg'>Lines shown:</span>"
       "<label><input type='checkbox' data-t='0' checked> Every past year</label><label><input type='checkbox' data-t='1' checked> Last 3 years</label>"
       "<label><input type='checkbox' data-t='2'> Last year only</label></div></div>")
js = ("<script>(function(){var D=" + DATA_JS + ";var g=document.getElementById('cov-chart'),r=document.getElementById('nsites'),"
      "o=document.getElementById('readout'),v=document.getElementById('nv');if(!g||!r||!window.Plotly)return;var c=document.getElementById('ctl');c.hidden=false;"
      "function upd(){var n=+r.value,i=n-1,u=n==1?'bridge':'bridges';"
      "o.textContent='Fix '+n+' '+u+' and you would have covered '+D.all[i]+'% of next year\\'s strikes, picking by every past year. Last 3 years: '+D.l3[i]+'%. Last year only: '+D.l1[i]+'%. At random: '+D.r[i]+'%. Best possible: '+D.o[i]+'%.';"
      "v.textContent=n;r.setAttribute('aria-valuetext',n+' '+u+'. Covers '+D.all[i]+'% of next year\\'s strikes.');"
      "Plotly.relayout(g,{'shapes[0].x0':n,'shapes[0].x1':n});}"
      "r.addEventListener('input',upd);c.querySelectorAll('input[type=checkbox]').forEach(function(x){x.addEventListener('change',function(){"
      "Plotly.restyle(g,{visible:x.checked?true:'legendonly'},[+x.getAttribute('data-t')]);});});})();</script>")
rows_cov = "".join("<tr><th scope='row'>%d</th><td>%d%%</td><td>%d%%</td><td>%d%%</td><td>%d%%</td><td>%d%%</td></tr>"
                   % (N, r0(cur["all"][N-1]), r0(cur["l3"][N-1]), r0(cur["l1"][N-1]), r0(orc[N-1]), r0(chance[N-1])) for N in (1, 3, 5, 10, 15, 20, 30))
cov_table = ("<details class='alt'><summary>Same numbers as a table</summary><div class='tbl-wrap'><table class='tbl'><thead><tr><th scope='col'>Bridges fixed</th>"
             "<th scope='col'>Every past year</th><th scope='col'>Last 3 years</th><th scope='col'>Last year only</th><th scope='col'>Best possible</th>"
             "<th scope='col'>At random</th></tr></thead><tbody>" + rows_cov + "</tbody></table></div></details>")
alt1 = ("Line chart: the share of next year's strikes covered by the bridges with the most strikes so far. With 10 bridges: every past year %d%%, last 3 years %d%%, "
        "best possible %d%%, at random %d%%. A table with the same numbers follows." % (r0(cur["all"][9]), r0(cur["l3"][9]), r0(orc[9]), r0(chance[9])))

# chart 2: persistence as a real HTML table (scrolls on phones, readable by screen readers)
top = yc.sum().sort_values(ascending=False).head(10).index.tolist()
def _lum(rgb):
    c = [x / 255 for x in rgb]; c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def _cr(a_, b_):
    la, lb = sorted((_lum(a_), _lum(b_)), reverse=True); return (la + 0.05) / (lb + 0.05)
INK, CREAM = (37, 31, 25), (247, 240, 228)
def shade(v, vmax):
    f = v / vmax
    lo, mid, hi = (239, 230, 216), (227, 183, 155), (143, 59, 42)
    a_, b_, t_ = (lo, mid, f / 0.35) if f < 0.35 else (mid, hi, (f - 0.35) / 0.65)
    rgb = tuple(round(a_[i] + (b_[i] - a_[i]) * t_) for i in range(3))
    fg = INK if _cr(rgb, INK) >= _cr(rgb, CREAM) else CREAM   # whichever text color has more contrast
    return "#%02X%02X%02X" % rgb, "#%02X%02X%02X" % fg
vmax = int(yc[top].values.max())
head_row = "<th scope='col'>Bridge (total strikes)</th>" + "".join("<th scope='col'>%d</th>" % y for y in YEARS)
body_rows = ""
for s in top:
    cells = ""
    for y in YEARS:
        v = int(yc.loc[y, s]); bg, fg = shade(v, vmax)
        cells += "<td style='background:%s;color:%s' title='%s, %d: %d'>%d</td>" % (bg, fg, slabel.label[s], y, v, v)
    body_rows += "<tr><th scope='row'>%s <span>(%d)</span></th>%s</tr>" % (slabel.label[s], int(yc[s].sum()), cells)
heat_html = ("<div class='tbl-wrap heat'><table class='heat-tbl'><caption>Strikes per year. Darker boxes mean more strikes.</caption><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>"
             % (head_row, body_rows))

# chart 3: truck route split by roadway
rd = b.assign(main=b.main_street.str.title().str.replace("Fdr", "FDR")).groupby("main").truck_route.agg(
    n="size", on=lambda s: (s == "YES").sum()).sort_values("n", ascending=False).head(10)
f3 = go.Figure()
f3.add_bar(y=rd.index, x=rd.n - rd.on, orientation="h", name="Not a truck route", marker_color=BRICK, hovertemplate="%{y}: %{x}<extra>not a truck route</extra>")
f3.add_bar(y=rd.index, x=rd.on, orientation="h", name="Marked truck route", marker_color=BLUE, hovertemplate="%{y}: %{x}<extra>marked truck route</extra>")
f3.update_layout(**base(360, t=64), barmode="stack", yaxis=dict(autorange="reversed", automargin=True), xaxis=dict(title="Strikes, 2013 to 2025", **GRID),
                 legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, itemclick=False, itemdoubleclick=False))
alt3 = "Bar chart: bridge strikes on each road, split by whether the road is a marked truck route. " + "; ".join("%s: %d not a truck route, %d marked truck route" % (r, n - on, on) for r, (n, on) in rd.iterrows()) + "."
cfg = {"displayModeBar": False, "responsive": True}
h = lambda f, alt, div_id=None: "<figure class='chart' role='img' aria-label=\"%s\">%s</figure>" % (alt.replace('"', "&quot;"), f.to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id=div_id))

# ---- numbers for the prose ----
off = (d.truck_route == "NO").mean(); wk = d.weekday.isin(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]).mean()
top6 = d.main_street.value_counts().head(6).sum() / T
tr_on = int((d.truck_route == "YES").sum())
trk_roads = rd.index.tolist()
sit = b.groupby("site").size(); in10 = sit.sort_values(ascending=False).head(10).sum() / len(b)
DIRW = {'S/B': 'Southbound', 'N/B': 'Northbound', 'E/B': 'Eastbound', 'W/B': 'Westbound'}
def maindir(s):
    v = b[b.site == s].direction.value_counts(); return DIRW.get(v.index[0], v.index[0]), v.iat[0] / v.sum(), int(v.sum())
rows_tbl = "".join(f"<tr><td>{slabel.label[s]}</td><td>{n}</td><td>{maindir(s)[0]}</td><td>{pct(maindir(s)[1])}</td></tr>"
                   for s, n in sit.sort_values(ascending=False).head(10).items())
last_2231290 = b[b.site == "2231290"].date.max().strftime("%b %-d, %Y")
nov = d.date.min().strftime("%Y"); known = len(b)
lic = d[(d.year.between(2019, 2024)) & d.license_state.notna()]
pk = d.main_street.str.contains("PARKWAY", na=False).mean()
t4 = d[d.truck_route == "YES"].main_street.value_counts().head(4)
t4n = [s.title().replace("Brooklyn Queens", "Brooklyn-Queens") for s in t4.index]
t4_text = ", ".join(t4n[:-1]) + " and " + t4n[-1]; t4_share = t4.sum() / tr_on

body = f'''
<section style="padding-bottom:8px;"><div class="wrap">
<nav class="crumb" aria-label="Breadcrumb"><a href="../../projects.html">← Back to the collection</a></nav>
<h1 style="font-size:clamp(2.2rem,5vw,3.6rem);">Which low bridges should the city fix first?</h1>
<p class="max-w lede">Trucks hit low bridges on New York City roads {T} times between 2013 and 2025. {pct(off)} of those hits were on roads that are not marked as truck routes.
I wanted to find where a small budget would help the most.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Do past strikes point to the next ones?</h2>
<p class="max-w">For each year from 2016 to 2025, I pretended I only knew the years before it. I picked the bridges with the most strikes so far, then counted how many of that year's strikes happened at them.
Use the slider, or the arrow keys, to change how many bridges get fixed. You can also tick which lines to show.</p>
{h(f1, alt1, "cov-chart")}{ctl}{js}{cov_table}
<p class="max-w">Picking by every past year works about as well as picking by the last 3 years or just last year. It did better in {wins} of the 10 years I tested, but only by a little, so I call it a tie.
The best possible line is out of reach, because it needs to know next year already.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Hot spots change over time</h2>
<p class="max-w">Strikes per year at the 10 bridges hit most often. On a phone, scroll sideways.
Some bridges have two ID numbers in the data. When two IDs sat within 30 meters of each other on the same road, I counted them as one bridge.</p>
{heat_html}
<p class="max-w">Three bridges changed by more than luck would explain. Hutchinson River Parkway at Westchester Avenue went from about 14 strikes a year to 3, starting in 2019.
Belt Parkway at 17th Avenue had about 6 a year, then none from 2023. Its last strike was {last_2231290}.
Henry Hudson Parkway at West 239th Street had none through 2016, then about 4 a year.
I do not know why any of this happened. A bridge that jumps up one year often calms down on its own, so a drop does not prove a fix worked. A jump from zero might just mean better reporting.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Most strikes are off the truck routes</h2>
<p class="max-w">{pct(pk)} of strikes were on parkways, and parkways are almost never marked as truck routes.
The data cannot say why trucks are there, so I would first look at how trucks end up on these roads, at signs and at enforcement, before taller bridges.
Only {tr_on} strikes were on marked truck routes. About half were on four roads: {t4_text}. For those, the bridge or the road itself may need a closer look.</p>
{h(f3, alt3)}
<p class="max-w">{pct(wk)} of strikes happen Monday to Friday, which fits trucks that are working. I found no clear season.</p>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">Strikes come from one direction</h2>
<p class="max-w">At most of the busiest bridges, nearly all strikes happen in one direction of travel. A sign or a sensor could go on that side, before the bridge.
The data does not say exactly what the direction column means.</p>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Bridge</th><th>Strikes</th><th>Main direction</th><th>Share in that direction</th></tr></thead><tbody>{rows_tbl}</tbody></table></div>
</div></section>

<section><div class="wrap">
<h2 class="mt-0">What the data cannot tell you</h2>
<ul class="limits max-w">
<li>The file has no bridge height, truck type, damage, cost or traffic count. So I cannot give rates or savings.</li>
<li>Some reports may be missing.</li>
<li>Every report is dated at midnight, so I could look at the day of the week and the month, but not the time of day.</li>
<li>The driver's license state is blank in 37% of reports, and how often it was filled in changed over the years. I only looked at 2019 to 2024, when New York licenses were {pct((lic.license_state == "NY").mean())} of the {len(lic)} reports that had one. I did not draw any conclusion from that.</li>
<li>{T - known} of {T} reports have no bridge ID, so they are not in the bridge counts. Street names in the file are not consistent, so I used the most common pair for each bridge. A few labels, like FDR Drive near East 61st Street, cover a stretch of road, not one spot.</li>
<li>I did not use machine learning. With {T} reports and only a location to go on, a model would not be trustworthy.</li>
</ul>
<p class="max-w">Data: NYC Open Data, NYC Bridge Strike Data (jdn9-td9w), downloaded Nov 6, 2026. Every cleaning step is written down in the code.
<a href="phase1.py">phase1.py</a> · <a href="phase1b.py">phase1b.py</a> · <a href="build_page.py">build_page.py</a> · <a href="bridge_strikes_clean.csv">clean data</a> · <a href="cleaning_log.txt">cleaning log</a></p>
</div></section>
'''
css = '''<style>
.lede{font-size:18px;color:var(--ink)}
.crumb{margin:0 0 6px}.crumb a{font-family:var(--font-mono);font-size:13px}
.chart{margin:0}.js-plotly-plot{margin:14px 0 6px}.limits{padding-left:18px;color:var(--ink-soft)}.limits li{margin-bottom:8px}
.tbl-wrap{overflow-x:auto;margin-top:14px}.tbl{border-collapse:collapse;width:100%;max-width:760px;font-family:var(--font-mono);font-size:13px}
.tbl th,.tbl td{text-align:left;padding:8px 14px 8px 0;border-bottom:1px dotted var(--line);color:var(--ink)}.tbl th{font-size:12px;color:var(--accent-ink)}
.alt{margin:4px 0 18px;font-family:var(--font-mono);font-size:12.5px}.alt summary{cursor:pointer;color:var(--accent-ink);padding:6px 0}
.heat{margin:16px 0 6px}.heat-tbl{border-collapse:separate;border-spacing:2px;font-family:var(--font-mono);font-size:12px;min-width:700px}
.heat-tbl caption{caption-side:top;text-align:left;font-size:12px;color:var(--ink-soft);padding-bottom:6px}
.heat-tbl thead th{font-size:12px;font-weight:400;color:var(--ink-soft);text-align:center;padding:0 0 4px}
.heat-tbl thead th:first-child{text-align:left}
.heat-tbl tbody th{position:sticky;left:0;background:var(--paper);text-align:left;font-weight:400;font-size:12px;line-height:1.3;color:var(--ink);padding:3px 10px 3px 0;min-width:170px;max-width:210px;z-index:1}
.heat-tbl tbody th span{color:var(--ink-soft)}
.heat-tbl td{width:36px;height:30px;text-align:center;font-variant-numeric:tabular-nums}
.plotly .xtick text,.plotly .ytick text,.plotly .gtitle,.plotly .g-xtitle text,.plotly .g-ytitle text,.plotly .legendtext,.plotly .slider-container text,.plotly .annotation-text{fill:var(--ink)!important}
.ctl{max-width:640px;margin:18px 0 0}.ctl label{display:block;font-family:var(--font-mono);font-size:14px;color:var(--ink)}
.ctl input[type=range]{display:block;width:100%;height:44px;margin:2px 0 0;background:transparent;accent-color:var(--accent-ink);cursor:pointer}
.ctl input[type=range]:focus-visible{outline:2px solid var(--accent-ink);outline-offset:4px;border-radius:3px}
.ctl .ends{display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:12px;color:var(--ink-soft);margin-top:-6px}
.readout{font-family:var(--font-mono);font-size:13px;line-height:1.5;color:var(--ink);margin:10px 0 0;min-height:3em}
.ctl .lines{display:flex;flex-wrap:wrap;align-items:center;gap:2px 18px;margin-top:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink)}
.ctl .lines label{display:inline-flex;align-items:center;gap:8px;min-height:36px;cursor:pointer;font-size:13px}
.ctl .lines input{width:18px;height:18px;margin:0;accent-color:var(--accent-ink)}
.ctl .lines input:focus-visible{outline:2px solid var(--accent-ink);outline-offset:3px}
</style>
<script src="plotly.min.js"></script>'''

desc = "Which low NYC bridges should be fixed first? A Python look at 943 truck strikes, tested against past years."
head = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<script>(function(){try{var t=localStorage.getItem('theme');if(!t)t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Bridge Strikes, live analysis — Shruti Venkatesh</title>
<meta name="description" content="DESC">
<link rel="icon" type="image/svg+xml" href="../../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Newsreader:ital,wght@0,400;0,500;1,400&family=Caveat:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../styles.css?v=20261114">
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
