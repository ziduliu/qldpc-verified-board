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
RATE_MIN = 0.1   # the site and the README list codes with k/n above this rate; lower-rate entries stay in codes/ unlisted
entries = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json")))]
entries = [e for e in entries if e["k"] / e["n"] > RATE_MIN]
published = [r for r in json.load(open(os.path.join(ROOT, "data", "published_codes.json"))) if r["k"] / r["n"] > RATE_MIN]
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
    if e["family"] not in COL or "hand-designed" in e["source"]["reference"]:
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
                     status=STATUS[e["d_status"]], kind={"ours": "SCE", "board": "leaderboard, re-measured", "published": "published"}[kind],
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
<p>Codes with encoding rate k/n above 0.1. Every row states what is actually proven about the distance. <b>exact</b>: a certificate excludes all lighter logical operators
and an explicit operator of that weight is given. <b>search bound</b>: the lightest logical operator found by a long GPU search
(directed BP+OSD, 600 s to 3600 s per run, several runs), with the operator published so that anyone can check it; the true
distance may be smaller. <b>lower bound</b>: a certificate without a matching operator. Leaderboard rows are entries of the
Unitary Foundation qLDPC challenge re-measured with the same search; in the plot a dashed line runs from the claimed value
down to the lightest operator we found. Check matrices and operator supports are in the repository; <code>tools/check_all.py</code>
re-verifies everything.</p>
<div class="controls">
<label>family <select id="fam"><option value="">all</option><option>lifted-product</option><option>two-block</option><option>pair-partition</option></select></label>
<label>status <select id="st"><option value="">all</option><option>exact</option><option>search bound</option><option>lower bound</option></select></label>
<label>origin <select id="kd"><option value="">all</option><option>SCE</option><option>leaderboard, re-measured</option></select></label>
<label>check weight from <input id="wlo" type="number" value="4" min="3" max="20" style="width:4em"> to <input id="w" type="number" value="12" min="4" max="20" style="width:4em"></label>
<label>n ≤ <input id="n" type="number" value="2400" min="10" style="width:5em"></label>
<label><input id="pub" type="checkbox" checked> show published codes in the plot</label>
<span id="count" class="small"></span>
</div>
<div id="plotbox" style="margin:6px 0 14px"><svg id="plot" width="100%" viewBox="0 0 980 420" style="max-width:980px;display:block;font-family:inherit"></svg>
<p class="small">k d²/n against n for the rows that pass the filters (same markers as the table: circle lifted-product, diamond two-block, square pair-partition;
filled exact, open search bound, triangle lower bound; black edge SCE (this board), grey leaderboard with a thin line from the claimed value; small light markers published codes). Hover a point for its parameters.</p></div>
<div class="wrap"><table id="t"><thead><tr>
<th data-k="name">code</th><th data-k="n" class="num">n</th><th data-k="k" class="num">k</th><th data-k="d" class="num">d</th><th data-k="w" class="num">w</th>
<th data-k="fom" class="num">k d²/n</th><th data-k="family">family</th><th data-k="status">status</th><th data-k="kind">origin</th>
<th>construction</th><th>evidence</th><th>files</th></tr></thead><tbody>
"""
body = []
for r in rows:
    cls = {"exact": "exact", "search bound": "search", "lower bound": "lower", "bounded": "lower"}[r["status"]]
    body.append('<tr class="%s" data-fam="%s" data-st="%s" data-kd="%s" data-w="%d" data-n="%d" data-fom="%.2f" data-slug="%s">' % (cls, r["family"], r["status"], r["kind"], r["w"], r["n"], r["fom"], r["slug"]))
    body.append("<td><b>%s</b>%s</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%.1f</td><td>%s</td><td class=st>%s</td><td>%s</td>"
                % (html.escape(r["name"]), (' <span class="tag">%s</span>' % r["claimed"]) if r["claimed"] else "", r["n"], r["k"], r["d"], r["w"], r["fom"], r["family"], r["status"], r["kind"]))
    body.append('<td class="small">%s<br>%s</td><td class="small">%s</td><td class="small">%s</td></tr>' % (html.escape(r["construction"]), html.escape(r["source"]), html.escape(r["evidence"]), r["links"]))
tail = """</tbody></table></div>
<script>
const ENTRIES=__ENTRIES__;const PUB=__PUB__;
const rows=[...document.querySelectorAll('#t tbody tr')];
const SH={"lifted-product":"circle","two-block":"diamond","pair-partition":"square"};
const COL={"lifted-product":"#1f5fbf","two-block":"#5aa9c9","pair-partition":"#e07b00"};
function esc(t){return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;");}
function marker(x,y,r,shape,fill,stroke,sw,opacity,title){
  let body;
  if(shape==="tri") body=`<polygon points="${x},${y-r*1.2} ${x-r*1.1},${y+r*0.8} ${x+r*1.1},${y+r*0.8}"`;
  else if(shape==="circle") body=`<circle cx="${x}" cy="${y}" r="${r}"`;
  else if(shape==="diamond") body=`<polygon points="${x},${y-r*1.3} ${x+r*1.3},${y} ${x},${y+r*1.3} ${x-r*1.3},${y}"`;
  else body=`<rect x="${x-r}" y="${y-r}" width="${2*r}" height="${2*r}"`;
  const tag=body.slice(1,body.indexOf(" "));
  return body+` fill="${fill}" stroke="${stroke}" stroke-width="${sw}" opacity="${opacity}"><title>${esc(title)}</title></${tag}>`;
}
function plot(sel){
  const W=980,H=420,L=58,R=16,T=14,B=44;
  const pubOn=document.getElementById('pub').checked,wlo=+document.getElementById('wlo').value,wm=+w.value,nm=+n.value,f=fam.value;
  const pts=sel.map(e=>({x:e.n,y:e.kd2_over_n,fam:e.family,st:e.d_status,who:e.source.kind,name:e.name,w:e.w,claimed:e.claimed?e.k*e.claimed.d*e.claimed.d/e.n:null}));
  const pubs=pubOn?PUB.filter(r=>r.w>=wlo&&r.w<=wm&&r.n<=nm&&(!f||r.family===f)).map(r=>({x:r.n,y:r.k*r.d*r.d/r.n,fam:r.family,st:r.d_status,
    name:"[["+r.n+","+r.k+","+(r.d_status==="upper_bound"?"≤":r.d_status==="lower_bound"?"≥":"")+r.d+"]]  w="+r.w+(r.arxiv?"  arXiv:"+r.arxiv:"")})):[];
  const all=pts.concat(pubs);
  const xmax=Math.max(100,...all.map(p=>p.x))*1.04, ymax=Math.max(10,...all.map(p=>p.y),...pts.map(p=>p.claimed||0))*1.08;
  const X=v=>L+(W-L-R)*v/xmax, Y=v=>T+(H-T-B)*(1-v/ymax);
  const xt=xmax>1500?500:xmax>600?200:100, yt=ymax>400?100:ymax>150?50:ymax>60?20:10;
  let g="";
  for(let v=0;v<=xmax;v+=xt) g+=`<line x1="${X(v)}" y1="${T}" x2="${X(v)}" y2="${H-B}" stroke="#eee"/><text x="${X(v)}" y="${H-B+16}" text-anchor="middle" font-size="11" fill="#444">${v}</text>`;
  for(let v=0;v<=ymax;v+=yt) g+=`<line x1="${L}" y1="${Y(v)}" x2="${W-R}" y2="${Y(v)}" stroke="#eee"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="#444">${v}</text>`;
  g+=`<rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="none" stroke="#999"/>`;
  g+=`<text x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle" font-size="12" fill="#222">n (data qubits)</text>`;
  g+=`<text transform="translate(14,${(T+H-B)/2}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">k d²/n</text>`;
  for(const p of pubs){const c=COL[p.fam]||"#888";g+=marker(X(p.x),Y(p.y),3,p.st==="lower_bound"?"tri":SH[p.fam],p.st==="upper_bound"?"none":c,c,0.8,0.45,p.name);}
  for(const p of pts){if(p.claimed&&p.claimed>p.y){g+=`<line x1="${X(p.x)}" y1="${Y(p.claimed)}" x2="${X(p.x)}" y2="${Y(p.y)}" stroke="#777" stroke-width="1" stroke-dasharray="3,2"/>`;
    g+=`<text x="${X(p.x)+5}" y="${Y(p.claimed)+4}" font-size="9" fill="#777">claimed</text>`;}}
  for(const p of pts){const c=COL[p.fam]||"#888",board=p.who==="board",shape=p.st==="lower_bound"?"tri":SH[p.fam];
    g+=marker(X(p.x),Y(p.y),board?5:6,shape,p.st==="upper_bound"?"white":(board?"#bbb":c),board?"#555":"black",board?1.2:1.6,1,`${p.name}  w=${p.w}  k d²/n=${p.y.toFixed(1)}`);}
  document.getElementById('plot').innerHTML=g;
}
function apply(){
  const f=fam.value,s=st.value,k=kd.value,wm=+w.value,wlo=+document.getElementById('wlo').value,nm=+n.value;let c=0;const sel=new Set();
  for(const r of rows){const ok=(!f||r.dataset.fam===f)&&(!s||r.dataset.st===s)&&(!k||r.dataset.kd===k)&&(+r.dataset.w<=wm)&&(+r.dataset.w>=wlo)&&(+r.dataset.n<=nm);
    r.style.display=ok?'':'none';c+=ok;if(ok)sel.add(r.dataset.slug);}
  count.textContent=c+' of '+rows.length+' codes';plot(ENTRIES.filter(e=>sel.has(e.slug)));
}
for(const id of['fam','st','kd','w','wlo','n','pub']) document.getElementById(id).addEventListener('input',apply);
apply();
let dir={};document.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;dir[k]=!dir[k];const tb=document.querySelector('#t tbody');
const idx=[...th.parentNode.children].indexOf(th);const get=r=>{const t=r.children[idx].textContent;const v=parseFloat(t.replace(/[^0-9.\-]/g,''));return (k==='name'||k==='family'||k==='status'||k==='kind')?t:v;};
rows.sort((a,b)=>{const x=get(a),y=get(b);return (x>y?1:x<y?-1:0)*(dir[k]?1:-1);});rows.forEach(r=>tb.appendChild(r));}));
</script></body></html>"""
slim = [dict(slug=e["slug"], name=e["name"].replace("<=", "≤").replace(">=", "≥"), n=e["n"], k=e["k"], d=e["d"], w=e["w"], kd2_over_n=e["kd2_over_n"], family=e["family"],
             d_status=e["d_status"], source=dict(kind=e["source"]["kind"]), claimed=(dict(d=e["claimed"]["d"]) if e.get("claimed") else None)) for e in entries]
page = (head + "\n".join(body) + tail).replace("__ENTRIES__", json.dumps(slim)).replace("__PUB__", json.dumps(published))
open(os.path.join(ROOT, "docs", "index.html"), "w").write(page)

# ------------------------------------------------------------------ README tables (between the markers)
def md_name(e):
    return e["name"].replace("<=", "≤").replace(">=", "≥")


def md_links(e):
    out = []
    if e.get("matrices"):
        out.append("[H_X](%s) [H_Z](%s)" % (e["matrices"]["HX"], e["matrices"]["HZ"]))
    if e.get("witness"):
        out.append("[operators](%s)" % e["witness"])
    if e["source"]["kind"] == "board":
        out.append("[entry](%s)" % e["claimed"]["entry"])
    return " ".join(out)


def md_found(e):
    r = e["source"]["reference"]
    if "arXiv:2606.24808" in r:
        return "paper run (arXiv:2606.24808), " + ("level-1 refinement" if "refinement" in r else r.split("run ")[1].split(",")[0] if "run " in r else "")
    for key in ("line n700smoke", "line v5a", "line n700a", "line l8smoke1", "line l8a", "pp_scratch_opus_20261030", "pp_catalog_opus_20261030", "line n700a / v5a"):
        if key in r:
            return "evolution " + key.replace("pp_", "run pp_")
    return "evolution run"


evo = [e for e in entries if e["source"]["kind"] == "ours" and "hand-designed" not in e["source"]["reference"]]
STATUS_MD = {"exact": "exact", "upper_bound": "search bound", "lower_bound": "lower bound", "bounded": "bounded"}
big = sorted([e for e in evo if e["kd2_over_n"] >= 25], key=lambda e: -e["kd2_over_n"])
small = sorted([e for e in evo if e["kd2_over_n"] < 25], key=lambda e: -e["kd2_over_n"])
groups = []
for e in big:
    key = (e["name"], e["family"], e["w"], round(e["kd2_over_n"]), e["d_status"], md_found(e))
    for g in groups:
        if g["key"] == key:
            g["n"] += 1; g["links"].append(md_links(e)); break
    else:
        groups.append(dict(key=key, n=1, e=e, links=[md_links(e)]))
md = ["### Codes found by our evolution runs (%d)\n" % len(evo), "| code | family | w | k d²/n | distance | found by | files |", "|---|---|---|---|---|---|---|"]
for g in groups:
    e = g["e"]
    md.append("| %s%s | %s | %d | %.0f | %s | %s | %s |" % (md_name(e), " ×%d" % g["n"] if g["n"] > 1 else "", e["family"], e["w"], e["kd2_over_n"], STATUS_MD[e["d_status"]], md_found(e), " · ".join(g["links"])))
if small:
    md.append("| %d further codes of the high-rate cells (d 3–9, k d²/n below 25) | lifted-product | 8–12 | | exact | paper and weight-9 runs | see below |" % len(small))
    md += ["", "<details><summary>the %d small codes</summary>\n" % len(small), "| code | w | k d²/n | files |", "|---|---|---|---|"]
    for e in small:
        md.append("| %s | %d | %.1f | %s |" % (md_name(e), e["w"], e["kd2_over_n"], md_links(e)))
    md += ["", "</details>"]
board = sorted([e for e in entries if e["source"]["kind"] == "board"], key=lambda e: -(e["k"] * e["claimed"]["d"] ** 2 / e["n"]))
md += ["", "### Leaderboard entries re-measured (%d)\n" % len(board), "| entry | w | claimed d | lightest operator we found | k d²/n claimed → re-measured | files |", "|---|---|---|---|---|---|"]
for e in board:
    held = e["d"] >= e["claimed"]["d"]
    cl = e["k"] * e["claimed"]["d"] ** 2 / e["n"]
    md.append("| [[%d,%d]] | %d | ≤%d | %s | %s | %s |" % (e["n"], e["k"], e["w"], e["claimed"]["d"], "held (nothing lighter found)" if held else "%d" % e["d"],
                                                       ("%.0f" % cl) if held else "%.0f → %.0f" % (cl, e["kd2_over_n"]), md_links(e)))
readme = os.path.join(ROOT, "README.md")
r = open(readme).read()
a, b = "<!-- codes:start -->", "<!-- codes:end -->"
if a in r and b in r:
    r = r[:r.index(a) + len(a)] + "\n" + "\n".join(md) + "\n" + r[r.index(b):]
    open(readme, "w").write(r)
    print("README tables:", len(evo), "evolution codes,", len(board), "board rows")
