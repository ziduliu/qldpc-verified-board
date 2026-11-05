#!/usr/bin/env python3
"""Builds the static site in docs/ and the tables of README.md from codes/*.json and data/published_codes.json.

    python tools/build_site.py

docs/index.html: a summary (best certified code per check weight, best search bound, re-measured claims), a point
plot of k d^2/n against n driven by the filters, and the table; rows with identical parameters are merged; internal
run names and archive hashes sit in a collapsed details cell. README.md: the same summary and tables between the
markers. Only codes with encoding rate k/n above RATE_MIN are listed."""
import glob
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/ziduliu/qldpc-verified-board/blob/main/"
RATE_MIN = 0.1
entries = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json")))]
entries = [e for e in entries if e["k"] / e["n"] > RATE_MIN]
published = [r for r in json.load(open(os.path.join(ROOT, "data", "published_codes.json"))) if r["k"] / r["n"] > RATE_MIN]
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
json.dump(entries, open(os.path.join(ROOT, "docs", "codes.json"), "w"), indent=0)

STATUS = {"exact": "exact", "upper_bound": "search bound", "lower_bound": "lower bound", "bounded": "bounded"}
ORIGIN = {"sce": "SCE", "board": "leaderboard, re-measured"}


def nm(e):
    return e["name"].replace("<=", "≤").replace(">=", "≥")


def band(w):
    return "≤ 8" if w <= 8 else ("9–10" if w <= 10 else "11–12")


def evidence_text(e):
    ev = e.get("evidence") or {}
    if ev.get("kind") == "certificate":
        c = ev.get("certificate") or {}
        t = "certificate: no logical operator of weight ≤ %s on either side" % c.get("complete_through")
        if c.get("parity_argument"):
            t += ", and all logical weights are even (all-ones vector in both row spaces), so d ≥ %d" % c.get("lower")
        if e.get("witness"):
            t += "; explicit operators of weight %d" % e["d_upper"]
        elif c.get("found"):
            t += "; an operator of weight %d was found by the certifier (operator file pending)" % c["found"]
        return t
    return ev.get("method", "")


# ------------------------------------------------------------------ merged rows (same parameters, status, origin)
groups = {}
for e in sorted(entries, key=lambda e: (e["w"], -e["kd2_over_n"], e["slug"])):
    key = (e["name"], e["family"], e["w"], e["d_status"], e["origin"], (e.get("claimed") or {}).get("d"))
    groups.setdefault(key, []).append(e)
rows = []
for key, es in groups.items():
    e = es[0]
    rows.append(dict(key=key, es=es, name=nm(e), n=e["n"], k=e["k"], d=e["d"], w=e["w"], fom=e["kd2_over_n"], family=e["family"],
                     status=STATUS[e["d_status"]], origin=ORIGIN[e["origin"]], construction=e["construction"],
                     evidence=evidence_text(e), pending=any(x.get("pending") for x in es),
                     claimed=(e.get("claimed") or {}).get("d"), count=len(es)))

# ------------------------------------------------------------------ summary
listed = [e for e in entries if not e.get("pending")]
sce_exact = [e for e in listed if e["origin"] == "sce" and e["d_status"] == "exact"]
best_exact = {}
for e in sce_exact:
    b = band(e["w"])
    if b not in best_exact or e["kd2_over_n"] > best_exact[b]["kd2_over_n"]:
        best_exact[b] = e
sce_bound = sorted([e for e in listed if e["origin"] == "sce" and e["d_status"] == "upper_bound" and e.get("witness")], key=lambda e: -e["kd2_over_n"])
refuted = sorted([e for e in listed if e["origin"] == "board" and e.get("claimed") and e["d"] < e["claimed"]["d"]], key=lambda e: -(e["k"] * e["claimed"]["d"] ** 2 / e["n"]))
held = [e for e in listed if e["origin"] == "board" and e.get("claimed") and e["d"] >= e["claimed"]["d"]]


def link(e):
    out = []
    if e.get("matrices"):
        out.append('<a href="%s">H_X</a> <a href="%s">H_Z</a>' % (REPO + e["matrices"]["HX"], REPO + e["matrices"]["HZ"]))
    if e.get("witness"):
        out.append('<a href="%s">operators</a>' % (REPO + e["witness"]))
    if e["origin"] == "board":
        out.append('<a href="%s">entry</a>' % e["claimed"]["entry"])
    return " ".join(out)


def md_link(e):
    out = []
    if e.get("matrices"):
        out.append("[H_X](%s) [H_Z](%s)" % (e["matrices"]["HX"], e["matrices"]["HZ"]))
    if e.get("witness"):
        out.append("[operators](%s)" % e["witness"])
    if e["origin"] == "board":
        out.append("[entry](%s)" % e["claimed"]["entry"])
    return " ".join(out)


summary_html = ["<ul class=sum>"]
summary_md = []
for b in ("≤ 8", "9–10", "11–12"):
    e = best_exact.get(b)
    if e:
        summary_html.append("<li><b>check weight %s, best certified code found by SCE:</b> %s, k d²/n = %.1f, %s (%s). %s</li>" % (b, nm(e), e["kd2_over_n"], e["family"], html.escape(e["construction"]), link(e)))
        summary_md.append("- check weight %s, best certified code found by SCE: **%s**, k d²/n = %.1f, %s (%s) %s" % (b, nm(e), e["kd2_over_n"], e["family"], e["construction"], md_link(e)))
if sce_bound:
    e = sce_bound[0]
    summary_html.append("<li><b>best search bound:</b> %s, k d²/n = %.1f, check weight %d; the lightest operators found by %s are published (%s). The true distance may be smaller.</li>" % (nm(e), e["kd2_over_n"], e["w"], html.escape((e["evidence"] or {}).get("method", "").split(":")[0]), link(e)))
    summary_md.append("- best search bound: **%s**, k d²/n = %.1f, check weight %d, lightest operators published %s; the true distance may be smaller" % (nm(e), e["kd2_over_n"], e["w"], md_link(e)))
if refuted:
    parts = ["%s claimed d ≤ %d, operator of weight %d found (%s)" % (nm(e).split(",≤")[0] + "]]", e["claimed"]["d"], e["d"], link(e)) for e in refuted]
    summary_html.append("<li><b>leaderboard claims not reproduced (%d of %d re-measured):</b> %s.</li>" % (len(refuted), len(refuted) + len(held), "; ".join(parts)))
    summary_md.append("- leaderboard claims not reproduced (%d of %d re-measured): %s" % (len(refuted), len(refuted) + len(held), "; ".join("%s claimed d ≤ %d, operator of weight %d found %s" % (nm(e).split(",≤")[0] + "]]", e["claimed"]["d"], e["d"], md_link(e)) for e in refuted)))
summary_html.append("</ul>")
cards = []
for b in ("≤ 8", "9–10", "11–12"):
    e = best_exact.get(b)
    if e:
        cards.append('<div class="card"><div class="lab">best certified code, check weight %s</div><div class="big">%s</div><div class="val">k d²/n = <b>%.1f</b> · %s</div><div class="sub">%s</div><div class="sub">%s</div></div>'
                     % (b, nm(e), e["kd2_over_n"], e["family"], html.escape(e["construction"]), link(e)))
if sce_bound:
    e = sce_bound[0]
    cards.append('<div class="card"><div class="lab">best search bound (operator published)</div><div class="big">%s</div><div class="val">k d²/n = <b>%.1f</b> · check weight %d</div><div class="sub">lightest operator found by the v5 search; the true distance may be smaller</div><div class="sub">%s</div></div>'
                 % (nm(e), e["kd2_over_n"], e["w"], link(e)))
if refuted or held:
    inner = "; ".join("%s claimed ≤%d, found %d (%s)" % (nm(e).split(",≤")[0] + "]]", e["claimed"]["d"], e["d"], link(e)) for e in refuted) or "none"
    cards.append('<div class="card"><div class="lab">leaderboard claims re-measured</div><div class="big">%d of %d not reproduced</div><div class="sub">%s</div><div class="sub">the other %d claims held under 600 s to 7200 s searches</div></div>'
                 % (len(refuted), len(refuted) + len(held), inner, len(held)))
summary_cards = '<div class="cards">' + "".join(cards) + '</div>' 

# ------------------------------------------------------------------ page
head = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verified qLDPC codes</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"></script>
<style>
:root{--ink:#1c2430;--muted:#5b6672;--line:#e4e8ee;--panel:#f6f8fa;--accent:#1f5fbf;--lp:#1f5fbf;--tb:#4a9cc0;--pp:#d9731a;--ok:#176b3a;--warn:#8a5a00}
*{box-sizing:border-box}body{font-family:"IBM Plex Sans",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;margin:0;color:var(--ink);background:#fff;font-size:15px;line-height:1.5}
header{border-bottom:1px solid var(--line);background:#fff}header .in{max-width:1400px;margin:0 auto;padding:22px 24px 16px}
h1{font-size:1.7em;font-weight:600;margin:0 0 6px;letter-spacing:-.01em}header p{margin:0;color:var(--muted);max-width:80em}
main{max-width:1400px;margin:0 auto;padding:8px 24px 48px}h2{font-size:1.15em;font-weight:600;margin:28px 0 10px;letter-spacing:-.005em}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:10px 0 4px}
.card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:#fff}.card .lab{font-size:.78em;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.card .big{font-family:"IBM Plex Mono",monospace;font-size:1.25em;font-weight:500;margin:4px 0 2px}.card .sub{font-size:.9em;color:var(--muted)}.card a{color:var(--accent)}
.card .val{font-size:.95em}.card .val b{font-weight:600}
dl{max-width:80em;margin:0}dt{font-weight:600;margin-top:8px}dd{margin:0 0 4px 1.2em;color:#2a3440}
.controls{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0;padding:10px 12px;background:var(--panel);border:1px solid var(--line);border-radius:8px;font-size:.92em;align-items:center}
select,input[type=number]{font:inherit;font-size:.95em;padding:3px 6px;border:1px solid #c9d0d8;border-radius:5px;background:#fff}
.plots{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0 12px}@media (max-width:1100px){.plots{grid-template-columns:1fr}}
.plot{border:1px solid var(--line);border-radius:8px;padding:8px;background:#fff}.plot h3{font-size:.95em;font-weight:600;margin:4px 6px 6px}
#plot3d{width:100%;height:440px}
table{border-collapse:collapse;font-size:.86em;width:100%}th,td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:var(--panel);cursor:pointer;white-space:nowrap;position:sticky;top:0;font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",monospace;font-size:.95em}
tbody tr:nth-child(even){background:#fafbfc}tr.exact td.st{color:var(--ok);font-weight:600}tr.search td.st{color:var(--warn)}tr.lower td.st{color:var(--accent)}
.small{color:var(--muted);font-size:.9em}.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px}details{font-size:.9em}summary{cursor:pointer;color:var(--accent)}
.tag{display:inline-block;padding:0 7px;border-radius:9px;background:#eef1f5;font-size:.82em;margin-left:4px;color:#2a3440}.pend{background:#fff1cc}
code{font-family:"IBM Plex Mono",monospace;font-size:.92em}a{color:var(--accent)}footer{color:var(--muted);font-size:.85em;margin-top:30px}
</style></head><body>
<header><div class="in"><h1>Verified quantum LDPC codes</h1>
<p>Codes found by structured concept evolution (SCE, <a href="https://arxiv.org/abs/2606.24808">arXiv:2606.24808</a>) and entries of the Unitary Foundation qLDPC
challenge re-measured with the same search; encoding rate k/n above 0.1. Every row says what is proven about the distance and links the files to check it.</p></div></header>
<main>
<h2>Summary</h2>
""" + summary_cards + """
<h2>Explore</h2>
<div class="controls">
<label>family <select id="fam"><option value="">all</option><option>lifted-product</option><option>two-block</option><option>pair-partition</option></select></label>
<label>status <select id="st"><option value="">all</option><option>exact</option><option>search bound</option><option>lower bound</option></select></label>
<label>origin <select id="kd"><option value="">all</option><option>SCE</option><option>leaderboard, re-measured</option></select></label>
<label>check weight <input id="wlo" type="number" value="4" min="3" max="20" style="width:4em"> to <input id="w" type="number" value="12" min="4" max="20" style="width:4em"></label>
<label>n ≤ <input id="n" type="number" value="2400" min="10" style="width:5.5em"></label>
<label><input id="pub" type="checkbox" checked> published codes</label>
<label><input id="showpend" type="checkbox"> rows with a pending operator file</label>
<label>3-D surface <select id="surf"><option value="proven">proven distances</option><option value="all">incl. search bounds</option><option value="none">none</option></select></label>
<span id="count" class="small"></span>
</div>
<div id="tip" style="display:none;position:absolute;background:#1c2430;color:#fff;padding:3px 7px;border-radius:4px;font-size:.85em;pointer-events:none;white-space:nowrap;z-index:5"></div>
<div class="plots">
<div class="plot"><h3>k d²/n against n</h3><svg id="plot" width="100%" viewBox="0 0 700 420" style="display:block;font-family:inherit"></svg>
<p class="small" style="margin:6px 6px 2px">Circle lifted-product, diamond two-block, square pair-partition; filled exact, open search bound, triangle lower bound; black edge SCE, grey leaderboard with a dashed line from the claimed value; small light markers published codes. Hover for [[n,k,d]].</p></div>
<div class="plot"><h3>Frontier in (n, w, k d²/n)</h3><div id="plot3d"></div>
<p class="small" style="margin:6px 6px 2px">Points as on the left (colour by family, SCE in dark edges). The surface is the frontier F(n, w) = largest k d²/n among the shown codes with at most n qubits and check weight at most w, from proven distances or including search bounds. Drag to rotate, scroll to zoom.</p></div>
</div>
<h2>Codes</h2>
<p class="small">Grouped by check weight, sorted by k d²/n inside a group; click a column head to sort differently. Rows with identical parameters are merged (×2 = two inequivalent codes, distinct spectra). Internal run names are in the provenance fold of each row.</p>
<div class="wrap"><table id="t"><thead><tr>
<th data-k="name">code</th><th data-k="n" class="num">n</th><th data-k="k" class="num">k</th><th data-k="d" class="num">d</th><th data-k="w" class="num">w</th>
<th data-k="fom" class="num">k d²/n</th><th data-k="family">family</th><th data-k="status">status</th><th data-k="kind">origin</th>
<th>construction</th><th>evidence</th><th>files</th></tr></thead><tbody>
"""
body = []
for r in rows:
    cls = {"exact": "exact", "search bound": "search", "lower bound": "lower", "bounded": "lower"}[r["status"]]
    es = r["es"]
    body.append('<tr class="%s%s" data-fam="%s" data-st="%s" data-kd="%s" data-w="%d" data-n="%d" data-fom="%.2f" data-slugs="%s" data-pend="%d">'
                % (cls, " pending" if r["pending"] else "", r["family"], r["status"], r["origin"], r["w"], r["n"], r["fom"], " ".join(x["slug"] for x in es), 1 if r["pending"] else 0))
    tags = ""
    if r["claimed"]:
        tags += ' <span class="tag">claimed ≤%d</span>' % r["claimed"]
    if r["count"] > 1:
        tags += ' <span class="tag">×%d</span>' % r["count"]
    if r["pending"]:
        tags += ' <span class="tag pend">operator file pending</span>'
    body.append("<td><b>%s</b>%s</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%.1f</td><td>%s</td><td class=st>%s</td><td>%s</td>"
                % (html.escape(r["name"]), tags, r["n"], r["k"], r["d"], r["w"], r["fom"], r["family"], r["status"], r["origin"]))
    det = "<br>".join("<b>%s</b>: %s" % (html.escape(x["slug"]), html.escape(x["provenance"])) for x in es)
    cite = html.escape(es[0].get("citation") or "")
    body.append('<td class="small">%s<details><summary>provenance</summary>%s%s</details></td>' % (html.escape(r["construction"]), det, ("<br><i>%s</i>" % cite) if cite else ""))
    body.append('<td class="small">%s</td><td class="small">%s</td></tr>' % (html.escape(r["evidence"]), " · ".join(link(x) for x in es)))
tail = r"""</tbody></table></div>
<footer>Data and tools: <a href="https://github.com/ziduliu/qldpc-verified-board">github.com/ziduliu/qldpc-verified-board</a>. Pair-partition construction: Okada and Kasai, arXiv:2607.14091; Lee et al., arXiv:2609.30069. Leaderboard: unitaryfoundation/qldpc-challenge.</footer>
</main>
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
  return body+` fill="${fill}" stroke="${stroke}" stroke-width="${sw}" opacity="${opacity}" data-t="${esc(title)}"/>`;
}
const tip=document.getElementById('tip');
document.getElementById('plot').addEventListener('mousemove',ev=>{const t=ev.target.getAttribute&&ev.target.getAttribute('data-t');
  if(t){tip.textContent=t;tip.style.display='block';tip.style.left=(ev.pageX+12)+'px';tip.style.top=(ev.pageY-28)+'px';}else tip.style.display='none';});
document.getElementById('plot').addEventListener('mouseleave',()=>{tip.style.display='none';});
function plot(sel){
  const W=700,H=420,L=58,R=16,T=14,B=44;
  const pubOn=document.getElementById('pub').checked,wlo=+document.getElementById('wlo').value,wm=+w.value,nm=+n.value,f=fam.value;
  const pts=sel.map(e=>({x:e.n,y:e.kd2_over_n,fam:e.family,st:e.d_status,who:e.origin,name:e.name,w:e.w,claimed:e.claimed?e.k*e.claimed.d*e.claimed.d/e.n:null}));
  const pubs=pubOn?PUB.filter(r=>r.w>=wlo&&r.w<=wm&&r.n<=nm&&(!f||r.family===f)).map(r=>({x:r.n,y:r.k*r.d*r.d/r.n,fam:r.family,st:r.d_status,
    w:r.w,name:"[["+r.n+","+r.k+","+(r.d_status==="upper_bound"?"≤":r.d_status==="lower_bound"?"≥":"")+r.d+"]]  w = "+r.w+(r.arxiv?"  arXiv:"+r.arxiv:"")})):[];
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
    g+=marker(X(p.x),Y(p.y),board?5:6,shape,p.st==="upper_bound"?"white":(board?"#bbb":c),board?"#555":"black",board?1.2:1.6,1,`${p.name}   w = ${p.w}   k d²/n = ${p.y.toFixed(1)}`);}
  document.getElementById('plot').innerHTML=g;
  plot3d(pts,pubs);
}
function plot3d(pts,pubs){
  const mode=document.getElementById('surf').value;
  const sym=f=>f==="lifted-product"?"circle":f==="two-block"?"diamond":"square";
  const tr=[];
  const mk=(arr,name,size,line,opacity)=>{if(!arr.length)return;tr.push({type:"scatter3d",mode:"markers",name:name,x:arr.map(p=>p.x),y:arr.map(p=>p.w),z:arr.map(p=>p.y),
    text:arr.map(p=>p.name),hovertemplate:"%{text}<br>n=%{x}, w=%{y}, k d²/n=%{z:.1f}<extra></extra>",
    marker:{size:size,symbol:arr.map(p=>sym(p.fam)+(p.st==="upper_bound"?"-open":"")),color:arr.map(p=>COL[p.fam]||"#888"),opacity:opacity,line:line}});};
  const sce=pts.filter(p=>p.who!=="board"),bd=pts.filter(p=>p.who==="board");
  mk(sce,"SCE",5,{color:"#111",width:1.5},0.95);mk(bd,"leaderboard, re-measured",4,{color:"#666",width:1},0.9);mk(pubs,"published",2.5,{width:0},0.45);
  if(mode!=="none"){const all=pts.concat(pubs).filter(p=>mode==="all"||p.st!=="upper_bound");
    if(all.length){const nmax=Math.max(...all.map(p=>p.x)),ws=[...new Set(all.map(p=>p.w))].sort((a,b)=>a-b),wmin=ws[0],wmax=ws[ws.length-1];
      const xs=[],ys=[],zs=[];for(let w=wmin;w<=wmax;w++)ys.push(w);for(let n=100;n<=nmax+50;n+=50)xs.push(n);
      for(const w of ys){const row=[];for(const n of xs){let m=0;for(const p of all)if(p.x<=n&&p.w<=w&&p.y>m)m=p.y;row.push(m);}zs.push(row);}
      tr.push({type:"surface",x:xs,y:ys,z:zs,name:"frontier",showscale:false,opacity:0.35,colorscale:[[0,"#dbe7f5"],[1,"#1f5fbf"]],hovertemplate:"n ≤ %{x}, w ≤ %{y}: best k d²/n %{z:.0f}<extra>frontier</extra>"});}}
  Plotly.react("plot3d",tr,{margin:{l:0,r:0,t:4,b:0},showlegend:true,legend:{orientation:"h",y:0,x:0,font:{size:11}},
    scene:{xaxis:{title:"n"},yaxis:{title:"check weight w",dtick:1},zaxis:{title:"k d²/n"},camera:{eye:{x:1.5,y:-1.6,z:0.9}}}},{displaylogo:false,responsive:true});
}
function apply(){
  const f=fam.value,s=st.value,k=kd.value,wm=+w.value,wlo=+document.getElementById('wlo').value,nm=+n.value,sp=document.getElementById('showpend').checked;let c=0;const sel=new Set();
  for(const r of rows){const ok=(!f||r.dataset.fam===f)&&(!s||r.dataset.st===s)&&(!k||r.dataset.kd===k)&&(+r.dataset.w<=wm)&&(+r.dataset.w>=wlo)&&(+r.dataset.n<=nm)&&(sp||r.dataset.pend==="0");
    r.style.display=ok?'':'none';c+=ok;if(ok)r.dataset.slugs.split(' ').forEach(x=>sel.add(x));}
  count.textContent=c+' rows shown';plot(ENTRIES.filter(e=>sel.has(e.slug)));
}
for(const id of['fam','st','kd','w','wlo','n','pub','showpend','surf']) document.getElementById(id).addEventListener('input',apply);
apply();
let dir={};document.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;dir[k]=!dir[k];const tb=document.querySelector('#t tbody');
const idx=[...th.parentNode.children].indexOf(th);const get=r=>{const t=r.children[idx].textContent;const v=parseFloat(t.replace(/[^0-9.\-]/g,''));return (k==='name'||k==='family'||k==='status'||k==='kind')?t:v;};
rows.sort((a,b)=>{const x=get(a),y=get(b);return (x>y?1:x<y?-1:0)*(dir[k]?1:-1);});rows.forEach(r=>tb.appendChild(r));}));
</script></body></html>"""
slim = [dict(slug=e["slug"], name=nm(e), n=e["n"], k=e["k"], d=e["d"], w=e["w"], kd2_over_n=e["kd2_over_n"], family=e["family"], d_status=e["d_status"],
             origin=e["origin"], claimed=(dict(d=e["claimed"]["d"]) if e.get("claimed") else None)) for e in entries]
page = (head + "\n".join(body) + tail).replace("__ENTRIES__", json.dumps(slim)).replace("__PUB__", json.dumps(published))
open(os.path.join(ROOT, "docs", "index.html"), "w").write(page)
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").write("")


# ------------------------------------------------------------------ static figure for the README (points only)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
COL = {"lifted-product": "#1f5fbf", "two-block": "#5aa9c9", "pair-partition": "#e07b00"}
MK = {"lifted-product": "o", "two-block": "D", "pair-partition": "s"}
fig, axes = plt.subplots(3, 1, figsize=(8.6, 12.2), sharex=True)
for ax, (lo, hi, title) in zip(axes, ((0, 8, "check weight ≤ 8"), (9, 10, "check weight 9–10"), (11, 12, "check weight 11–12"))):
    for r in published:
        if lo <= r["w"] <= hi and r["n"] <= 2400:
            ax.scatter([r["n"]], [r["k"] * r["d"] ** 2 / r["n"]], s=16, marker=("^" if r["d_status"] == "lower_bound" else MK[r["family"]]),
                       c=("none" if r["d_status"] == "upper_bound" else COL[r["family"]]), edgecolors=COL[r["family"]], linewidths=0.8, alpha=0.55, zorder=2)
    for e in listed:
        if lo <= e["w"] <= hi and e["n"] <= 2400:
            board = e["origin"] == "board"
            if board and e.get("claimed") and e["claimed"]["d"] > e["d"]:
                ax.plot([e["n"], e["n"]], [e["k"] * e["claimed"]["d"] ** 2 / e["n"], e["kd2_over_n"]], color="0.5", lw=0.9, ls="--", zorder=2)
            ax.scatter([e["n"]], [e["kd2_over_n"]], s=(34 if board else 52), marker=("^" if e["d_status"] == "lower_bound" else MK[e["family"]]),
                       c=("white" if e["d_status"] == "upper_bound" else ("#bbb" if board else COL[e["family"]])), edgecolors=("0.4" if board else "black"), linewidths=(1.1 if board else 1.5), zorder=4)
    ax.set_xlim(0, 2400); ax.set_ylim(0, 300); ax.grid(True, lw=0.4, alpha=0.5); ax.set_title(title, loc="left", fontsize=11); ax.set_ylabel("$k d^2 / n$")
axes[-1].set_xlabel("$n$ (data qubits)")
handles = [Line2D([], [], marker=MK[f], ls="", color=COL[f], ms=6, label=f) for f in COL]
handles += [Line2D([], [], marker="o", ls="", mfc="white", mec="0.3", ms=6, label="open: search upper bound"), Line2D([], [], marker="^", ls="", color="0.3", ms=6, label="triangle: lower bound only"),
            Line2D([], [], marker="o", ls="", mfc="0.6", mec="black", mew=1.4, ms=7, label="black edge: SCE"), Line2D([], [], marker="o", ls="", mfc="#bbb", mec="0.4", ms=6, label="grey, dashed line from the claim: leaderboard, re-measured"),
            Line2D([], [], marker="o", ls="", color="#999", ms=4, label="small: published codes")]
fig.legend(handles=handles, fontsize=7.5, loc="lower center", ncol=3, framealpha=0.95)
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(ROOT, "docs", "frontier.png"), dpi=170)

# ------------------------------------------------------------------ README (between the markers)
md = ["### Summary\n"] + summary_md + ["", "### Codes found by SCE (%d rows; ×2 = two inequivalent codes)\n" % sum(1 for r in rows if r["origin"] == "SCE"),
      "| code | w | k d²/n | family | status | construction | evidence | files |", "|---|---|---|---|---|---|---|---|"]
for r in rows:
    if r["origin"] != "SCE":
        continue
    md.append("| %s%s%s | %d | %.1f | %s | %s | %s | %s | %s |" % (r["name"], " ×%d" % r["count"] if r["count"] > 1 else "", " (operator file pending)" if r["pending"] else "",
                                                               r["w"], r["fom"], r["family"], r["status"], r["construction"].replace("|", "/"), r["evidence"].replace("|", "/"), " · ".join(md_link(x) for x in r["es"])))
md += ["", "### Leaderboard entries re-measured (%d)\n" % sum(1 for r in rows if r["origin"] != "SCE"), "| entry | w | claimed d | lightest operator we found | k d²/n claimed → re-measured | our search | files |", "|---|---|---|---|---|---|---|"]
for r in sorted([r for r in rows if r["origin"] != "SCE"], key=lambda r: (r["w"], -(r["k"] * r["claimed"] ** 2 / r["n"]))):
    e = r["es"][0]; cl = e["k"] * e["claimed"]["d"] ** 2 / e["n"]; heldrow = e["d"] >= e["claimed"]["d"]
    md.append("| [[%d,%d]] | %d | ≤%d | %s%s | %s | %s | %s |" % (e["n"], e["k"], e["w"], e["claimed"]["d"], "held (nothing lighter found)" if heldrow else "%d" % e["d"], " (operator file pending)" if r["pending"] else "",
                                                       ("%.0f" % cl) if heldrow else "%.0f → %.0f" % (cl, e["kd2_over_n"]), r["evidence"].replace("|", "/").split(": ", 1)[-1][:120], md_link(e)))
readme = os.path.join(ROOT, "README.md"); rd = open(readme).read()
a, b = "<!-- codes:start -->", "<!-- codes:end -->"
if a in rd and b in rd:
    rd = rd[:rd.index(a) + len(a)] + "\n" + "\n".join(md) + "\n" + rd[rd.index(b):]
    open(readme, "w").write(rd)
print("entries", len(entries), "rows", len(rows), "pending", sum(1 for r in rows if r["pending"]), "| summary lines", len(summary_md))
