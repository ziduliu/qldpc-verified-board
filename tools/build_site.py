#!/usr/bin/env python3
"""Builds the static site in docs/ from codes/*.json and data/published_codes.json:
docs/codes.json (all entries), docs/index.html (sortable, filterable table) and docs/frontier.png (k d^2 / n against n
for the three check-weight bands, with the running maximum per family).

    python tools/build_site.py"""
import glob
import html
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/ziduliu/qldpc-verified-board/blob/main/"
entries = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json")))]
published = json.load(open(os.path.join(ROOT, "data", "published_codes.json")))
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
json.dump(entries, open(os.path.join(ROOT, "docs", "codes.json"), "w"), indent=0)

# ------------------------------------------------------------------ figure
COL = {"lifted-product": "#1f5fbf", "two-block": "#5aa9c9", "pair-partition": "#e07b00"}
MK = {"lifted-product": "o", "two-block": "D", "pair-partition": "s"}
BANDS = ((0, 8, "check weight ≤ 8"), (9, 10, "check weight 9–10"), (11, 12, "check weight 11–12"))
XMAX, YCAP = 2400, 300
pts = []
for r in published:
    pts.append(dict(fam=r["family"], who="pub", n=r["n"], k=r["k"], d=r["d"], w=r["w"], status=r["d_status"], fom=r["k"] * r["d"] ** 2 / r["n"]))
for e in entries:
    if e["family"] not in COL:
        continue
    st = {"exact": "exact", "upper_bound": "upper_bound", "lower_bound": "lower_bound", "bounded": "lower_bound"}[e["d_status"]]
    pts.append(dict(fam=e["family"], who=("board" if e["source"]["kind"] == "board" else "ours"), n=e["n"], k=e["k"], d=e["d"], w=e["w"], status=st,
                    fom=e["kd2_over_n"], name=e["name"], claimed=(e.get("claimed") or {}).get("d")))


def frontier(P, proven_only):
    Q = sorted([p for p in P if (p["status"] != "upper_bound" or not proven_only)], key=lambda p: (p["n"], p["fom"]))
    xs, ys, best = [], [], 0.0
    for p in Q:
        if p["fom"] > best:
            best = p["fom"]; xs.append(p["n"]); ys.append(best)
    return xs, ys


fig, axes = plt.subplots(3, 1, figsize=(8.6, 12.6), sharex=True)
for ax, (lo, hi, title) in zip(axes, BANDS):
    P = [p for p in pts if lo <= p["w"] <= hi and p["n"] <= XMAX]
    for fam, members in (("lifted-product", ("lifted-product", "two-block")), ("pair-partition", ("pair-partition",))):
        F = [p for p in P if p["fam"] in members and p["who"] != "board"]
        for proven, ls, lw in ((True, "-", 1.6), (False, "--", 0.9)):
            xs, ys = frontier(F, proven)
            if xs:
                ax.step(xs + [XMAX], [min(y, YCAP) for y in ys + [ys[-1]]], where="post", color=COL[fam], ls=ls, lw=lw, alpha=0.85 if proven else 0.6, zorder=2)
    for p in P:
        col, mk = COL[p["fam"]], MK[p["fam"]]
        if p["status"] == "lower_bound":
            mk = "^"
        y = min(p["fom"], YCAP)
        if p["who"] == "board":
            ax.scatter([p["n"]], [y], s=30, marker=mk, c="none", edgecolors="0.35", linewidths=1.1, zorder=3)
            if p["claimed"] and p["claimed"] > p["d"]:
                y0 = min(p["k"] * p["claimed"] ** 2 / p["n"], YCAP)
                ax.annotate("", (p["n"], y), (p["n"], y0), arrowprops=dict(arrowstyle="-|>", color="0.35", lw=0.8, shrinkA=0, shrinkB=0), zorder=2)
        else:
            ours = p["who"] == "ours"
            ax.scatter([p["n"]], [y], s=(58 if ours else 20), marker=mk, c=(col if p["status"] != "upper_bound" else "none"),
                       edgecolors=("black" if ours else col), linewidths=(1.3 if ours else 0.9), alpha=0.95 if ours else 0.7, zorder=4 if ours else 3)
    ax.set_xlim(0, XMAX); ax.set_ylim(0, YCAP); ax.grid(True, lw=0.4, alpha=0.5)
    placed = []
    labelled = set()
    for p in sorted([p for p in P if p["who"] == "ours"], key=lambda p: -p["fom"]):
        text = p["name"].replace("<=", "≤").replace(">=", "≥")
        if text in labelled or len(labelled) >= 4:
            continue
        px, py = ax.transData.transform((p["n"], min(p["fom"], YCAP)))
        wpx, hpx = len(text) * 4.0 * fig.dpi / 72, 8.5 * fig.dpi / 72
        for dx, dy in ((6, 4), (6, -11), (-wpx * 72 / fig.dpi - 6, 4), (-wpx * 72 / fig.dpi - 6, -11), (6, 16), (6, -23)):
            box = (px + dx * fig.dpi / 72 + wpx / 2, py + dy * fig.dpi / 72)
            if not any(abs(box[0] - b[0]) < wpx and abs(box[1] - b[1]) < hpx for b in placed):
                placed.append(box); labelled.add(text)
                ax.annotate(text, (p["n"], min(p["fom"], YCAP)), textcoords="offset points", xytext=(dx, dy), fontsize=7, color="0.15")
                break
    ax.set_title(title, loc="left", fontsize=11); ax.set_ylabel("$k d^2 / n$")
axes[-1].set_xlabel("$n$ (data qubits)")
handles = [Line2D([], [], marker=MK[f], ls="", color=COL[f], ms=6, label=f) for f in COL]
handles += [Line2D([], [], marker="o", ls="", mfc="white", mec="0.3", ms=6, label="open: search upper bound"),
            Line2D([], [], marker="^", ls="", color="0.3", ms=6, label="triangle: lower bound only"),
            Line2D([], [], marker="o", ls="", mfc="0.6", mec="black", mew=1.3, ms=7, label="black edge: this board"),
            Line2D([], [], marker="o", ls="", mfc="none", mec="0.35", ms=6, label="grey with arrow: leaderboard entry, claimed → re-measured"),
            Line2D([], [], ls="-", color="0.3", lw=1.6, label="running maximum, proven distances"),
            Line2D([], [], ls="--", color="0.3", lw=0.9, label="running maximum incl. search bounds")]
fig.legend(handles=handles, fontsize=7.5, loc="lower center", ncol=3, framealpha=0.95)
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(os.path.join(ROOT, "docs", "frontier.png"), dpi=170)

# ------------------------------------------------------------------ table
STATUS = {"exact": "exact", "upper_bound": "search bound", "lower_bound": "lower bound", "bounded": "bounded"}
rows = []
for e in sorted(entries, key=lambda e: -e["kd2_over_n"]):
    kind = e["source"]["kind"]
    ev = e.get("evidence") or {}
    if ev.get("kind") == "certificate":
        c = ev.get("certificate") or {}
        evidence = "certificate: no logical operator through weight %s on both sides%s" % (c.get("complete_through"), ", even weights" if c.get("parity_argument") else "")
        if e.get("witness"):
            evidence += "; operators of weight %d" % e["d_upper"]
        elif c.get("found"):
            evidence += "; operator of weight %d found by the certifier" % c["found"]
        if ev.get("records"):
            evidence += " (" + ev["records"] + ")"
    else:
        evidence = ev.get("method", "")
    links = []
    if e.get("matrices"):
        links.append('<a href="%s">H_X</a> <a href="%s">H_Z</a>' % (REPO + e["matrices"]["HX"], REPO + e["matrices"]["HZ"]))
    if e.get("witness"):
        links.append('<a href="%s">operators</a>' % (REPO + e["witness"]))
    if kind == "board":
        links.append('<a href="%s">board entry</a>' % e["claimed"]["entry"])
    claimed = ("claimed ≤%d" % e["claimed"]["d"]) if e.get("claimed") else ""
    rows.append(dict(name=e["name"].replace("<=", "≤").replace(">=", "≥"), n=e["n"], k=e["k"], d=e["d"], w=e["w"], fom=e["kd2_over_n"], family=e["family"],
                     status=STATUS[e["d_status"]], kind={"ours": "this board", "board": "leaderboard, re-measured", "published": "published"}[kind],
                     construction=e["construction"], source=e["source"]["reference"], evidence=evidence, links=" ".join(links), claimed=claimed, slug=e["slug"]))

head = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verified qLDPC codes</title>
<style>
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;margin:0 16px 40px;color:#1b1b1b;background:#fff;max-width:1400px}
h1{font-size:1.5em;margin:18px 0 4px}p{max-width:72em;line-height:1.45}
.controls{display:flex;flex-wrap:wrap;gap:10px 18px;margin:12px 0;font-size:.92em;align-items:center}
select,input{font:inherit;padding:2px 4px}
table{border-collapse:collapse;font-size:.86em;width:100%}th,td{padding:4px 7px;border-bottom:1px solid #e3e3e3;vertical-align:top;text-align:left}
th{background:#f3f4f6;cursor:pointer;white-space:nowrap;position:sticky;top:0}td.num{text-align:right;font-variant-numeric:tabular-nums}
tr.exact td.st{color:#0b6e2f;font-weight:600}tr.search td.st{color:#8a5a00}tr.lower td.st{color:#1f5fbf}
.small{color:#555;font-size:.9em}.wrap{overflow-x:auto}img{max-width:100%;height:auto}
.tag{display:inline-block;padding:0 6px;border-radius:9px;background:#eef1f5;font-size:.85em;margin-left:4px}
</style></head><body>
<h1>Verified quantum LDPC codes</h1>
<p>Every row states what is actually proven about the distance. <b>exact</b>: a certificate excludes all lighter logical operators
and an explicit operator of that weight is given. <b>search bound</b>: the lightest logical operator found by a long GPU search
(directed BP+OSD, 600 s to 3600 s per run, several runs), with the operator published so that anyone can check it; the true
distance may be smaller. <b>lower bound</b>: a certificate without a matching operator. Leaderboard rows are entries of the
Unitary Foundation qLDPC challenge re-measured with the same search; the arrow in the figure runs from the claimed distance to
the lightest operator we found. Check matrices and operator supports are in the repository; <code>tools/check_all.py</code>
re-verifies everything.</p>
<div class="controls">
<label>family <select id="fam"><option value="">all</option><option>lifted-product</option><option>two-block</option><option>pair-partition</option></select></label>
<label>status <select id="st"><option value="">all</option><option>exact</option><option>search bound</option><option>lower bound</option></select></label>
<label>origin <select id="kd"><option value="">all</option><option>this board</option><option>leaderboard, re-measured</option></select></label>
<label>check weight ≤ <input id="w" type="number" value="12" min="4" max="20" style="width:4em"></label>
<label>n ≤ <input id="n" type="number" value="2400" min="10" style="width:5em"></label>
<span id="count" class="small"></span>
</div>
<div class="wrap"><table id="t"><thead><tr>
<th data-k="name">code</th><th data-k="n" class="num">n</th><th data-k="k" class="num">k</th><th data-k="d" class="num">d</th><th data-k="w" class="num">w</th>
<th data-k="fom" class="num">k d²/n</th><th data-k="family">family</th><th data-k="status">status</th><th data-k="kind">origin</th>
<th>construction</th><th>evidence</th><th>files</th></tr></thead><tbody>
"""
body = []
for r in rows:
    cls = {"exact": "exact", "search bound": "search", "lower bound": "lower", "bounded": "lower"}[r["status"]]
    body.append('<tr class="%s" data-fam="%s" data-st="%s" data-kd="%s" data-w="%d" data-n="%d" data-fom="%.2f">' % (cls, r["family"], r["status"], r["kind"], r["w"], r["n"], r["fom"]))
    body.append("<td><b>%s</b>%s</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%.1f</td><td>%s</td><td class=st>%s</td><td>%s</td>"
                % (html.escape(r["name"]), (' <span class="tag">%s</span>' % r["claimed"]) if r["claimed"] else "", r["n"], r["k"], r["d"], r["w"], r["fom"], r["family"], r["status"], r["kind"]))
    body.append('<td class="small">%s<br>%s</td><td class="small">%s</td><td class="small">%s</td></tr>' % (html.escape(r["construction"]), html.escape(r["source"]), html.escape(r["evidence"]), r["links"]))
tail = """</tbody></table></div>
<h2 style="font-size:1.15em">k d²/n against n</h2>
<p class="small">Published codes (parameters as printed, from the literature survey of 2026-10-18 and the pair-partition catalogue of arXiv:2609.30069)
are small markers; entries of this board have black edges; leaderboard entries are grey with an arrow from the claim to the re-measured value.
Lines are the running maximum of k d²/n over n per family (solid: proven distances only; dashed: including search bounds).</p>
<img src="frontier.png" alt="k d^2/n against n for lifted-product and pair-partition codes">
<script>
const rows=[...document.querySelectorAll('#t tbody tr')];
function apply(){const f=fam.value,s=st.value,k=kd.value,wm=+w.value,nm=+n.value;let c=0;
for(const r of rows){const ok=(!f||r.dataset.fam===f)&&(!s||r.dataset.st===s)&&(!k||r.dataset.kd===k)&&(+r.dataset.w<=wm)&&(+r.dataset.n<=nm);r.style.display=ok?'':'none';c+=ok;}
count.textContent=c+' of '+rows.length+' codes';}
for(const id of['fam','st','kd','w','n'])document.getElementById(id).addEventListener('input',apply);apply();
let dir={};document.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;dir[k]=!dir[k];const tb=document.querySelector('#t tbody');
const idx=[...th.parentNode.children].indexOf(th);const get=r=>{const t=r.children[idx].textContent;const v=parseFloat(t.replace(/[^0-9.\\-]/g,''));return (k==='name'||k==='family'||k==='status'||k==='kind')?t:v;};
rows.sort((a,b)=>{const x=get(a),y=get(b);return (x>y?1:x<y?-1:0)*(dir[k]?1:-1);});rows.forEach(r=>tb.appendChild(r));}));
</script></body></html>"""
open(os.path.join(ROOT, "docs", "index.html"), "w").write(head + "\n".join(body) + tail)
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").write("")
print("entries", len(entries), "published refs", len(published))
