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

# ------------------------------------------------------------------ page
head = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verified qLDPC codes</title>
<style>
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;margin:0 16px 40px;color:#1b1b1b;background:#fff;max-width:1400px}
h1{font-size:1.5em;margin:18px 0 4px}h2{font-size:1.15em;margin:22px 0 6px}p{max-width:78em;line-height:1.45}
ul.sum{max-width:78em;line-height:1.5;padding-left:1.2em}ul.sum li{margin:4px 0}
.controls{display:flex;flex-wrap:wrap;gap:10px 18px;margin:12px 0;font-size:.92em;align-items:center}
select,input{font:inherit;padding:2px 4px}
table{border-collapse:collapse;font-size:.86em;width:100%}th,td{padding:4px 7px;border-bottom:1px solid #e3e3e3;vertical-align:top;text-align:left}
th{background:#f3f4f6;cursor:pointer;white-space:nowrap;position:sticky;top:0}td.num{text-align:right;font-variant-numeric:tabular-nums}
tr.exact td.st{color:#0b6e2f;font-weight:600}tr.search td.st{color:#8a5a00}tr.lower td.st{color:#1f5fbf}
tr.bandhead td{background:#eef1f5;font-weight:600;padding:6px 7px}
.small{color:#555;font-size:.9em}.wrap{overflow-x:auto}details{font-size:.9em}summary{cursor:pointer;color:#1f5fbf}
.tag{display:inline-block;padding:0 6px;border-radius:9px;background:#eef1f5;font-size:.85em;margin-left:4px}.pend{background:#fff1cc}
dl{max-width:78em}dt{font-weight:600;margin-top:6px}dd{margin:0 0 4px 1.2em;line-height:1.45}
</style></head><body>
<h1>Verified quantum LDPC codes</h1>
<p>Codes with encoding rate k/n above 0.1, found by structured concept evolution (SCE, <a href="https://arxiv.org/abs/2606.24808">arXiv:2606.24808</a>),
and entries of the Unitary Foundation qLDPC challenge re-measured with the same search. Every row says what is actually proven about the
distance and links the files to check it.</p>
<h2>Summary</h2>
""" + "\n".join(summary_html) + """
<h2>How to read a row</h2>
<dl>
<dt>exact</dt><dd>a certificate (irreducible-cluster enumeration, Dumer, Kovalev and Pryadko 2017; for pair-partition codes together with the
even-weight argument: the all-ones vector lies in the row spaces of H_X and H_Z, so every logical operator has even weight) shows that no lighter
logical operator exists, and an explicit operator of weight d is given in the operator file.</dd>
<dt>search bound (d ≤ w)</dt><dd>the lightest logical operator found by a GPU search (directed BP+OSD, "v5": 600 s to 7200 s per run, several
seeds); the operator is published so anyone can check it. The true distance may be smaller.</dd>
<dt>lower bound (d ≥ w)</dt><dd>a certificate without a matching operator.</dd>
<dt>operator file pending</dt><dd>the certificate or search exists but the operator file has not been stored yet; the row is excluded from the summary until it is.</dd>
<dt>leaderboard, re-measured</dt><dd>an entry of <a href="https://github.com/unitaryfoundation/qldpc-challenge">unitaryfoundation/qldpc-challenge</a>
(snapshot eb2aeae, 2026-11-01), its matrices rebuilt from the entry's check lists (not copied here), searched with the same v5 runs; the row gives the
claimed distance, the lightest operator we found, and the operator file. Entry authors are the people named in the linked entry.</dd>
<dt>notation</dt><dd>C_n is the cyclic group of order n, × a direct product, C_m ⋊ C_r a semidirect product, D_m the dihedral group of order 2m;
"template (J, L)" is a pair-partition template with column weight J and row weight L (Okada and Kasai, <a href="https://arxiv.org/abs/2607.14091">arXiv:2607.14091</a>;
Lee et al., <a href="https://arxiv.org/abs/2609.30069">arXiv:2609.30069</a>), so the check weight is L; "protograph shapes (a,b) × (c,d)" are the
sizes of the two group-algebra matrices of a lifted-product code (arXiv:2606.24808). The check weight w is the largest row weight of H_X and H_Z.</dd>
<dt>checking</dt><dd><code>tools/check_all.py</code> verifies for every row with matrices: H_X H_Z^T = 0, n, k, the check weights, every listed
operator (commutes with the opposite checks, lies outside its stabilizer group, has the stated weight) and, where a certificate uses it, the
even-weight condition. It does not re-run the exact enumerations; their records are referenced in the evidence column.</dd>
</dl>
<h2>Codes</h2>
<div class="controls">
<label>family <select id="fam"><option value="">all</option><option>lifted-product</option><option>two-block</option><option>pair-partition</option></select></label>
<label>status <select id="st"><option value="">all</option><option>exact</option><option>search bound</option><option>lower bound</option></select></label>
<label>origin <select id="kd"><option value="">all</option><option>SCE</option><option>leaderboard, re-measured</option></select></label>
<label>check weight from <input id="wlo" type="number" value="4" min="3" max="20" style="width:4em"> to <input id="w" type="number" value="12" min="4" max="20" style="width:4em"></label>
<label>n ≤ <input id="n" type="number" value="2400" min="10" style="width:5em"></label>
<label><input id="pub" type="checkbox" checked> published codes in the plot</label>
<label><input id="showpend" type="checkbox"> rows with a pending operator file</label>
<span id="count" class="small"></span>
</div>
<div id="tip" style="display:none;position:absolute;background:#1b1b1b;color:#fff;padding:3px 7px;border-radius:4px;font-size:.85em;pointer-events:none;white-space:nowrap;z-index:5"></div>
<div id="plotbox" style="margin:6px 0 14px"><svg id="plot" width="100%" viewBox="0 0 980 420" style="max-width:980px;display:block;font-family:inherit"></svg>
<p class="small">k d²/n against n for the rows that pass the filters. Circle lifted-product, diamond two-block, square pair-partition; filled exact,
open search bound, triangle lower bound; black edge SCE, grey leaderboard with a dashed line from the claimed value; small light markers published codes
(parameters as printed, from the literature survey of 2026-10-18 and the pair-partition catalogue of arXiv:2609.30069). Move the mouse over a point for its [[n,k,d]].</p></div>
<p class="small">Rows are grouped by check weight and sorted by k d²/n inside a group; click a column head to sort differently. Rows with identical parameters are merged (×2 = two inequivalent codes, distinct spectra).</p>
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
  const W=980,H=420,L=58,R=16,T=14,B=44;
  const pubOn=document.getElementById('pub').checked,wlo=+document.getElementById('wlo').value,wm=+w.value,nm=+n.value,f=fam.value;
  const pts=sel.map(e=>({x:e.n,y:e.kd2_over_n,fam:e.family,st:e.d_status,who:e.origin,name:e.name,w:e.w,claimed:e.claimed?e.k*e.claimed.d*e.claimed.d/e.n:null}));
  const pubs=pubOn?PUB.filter(r=>r.w>=wlo&&r.w<=wm&&r.n<=nm&&(!f||r.family===f)).map(r=>({x:r.n,y:r.k*r.d*r.d/r.n,fam:r.family,st:r.d_status,
    name:"[["+r.n+","+r.k+","+(r.d_status==="upper_bound"?"≤":r.d_status==="lower_bound"?"≥":"")+r.d+"]]  w = "+r.w+(r.arxiv?"  arXiv:"+r.arxiv:"")})):[];
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
}
function apply(){
  const f=fam.value,s=st.value,k=kd.value,wm=+w.value,wlo=+document.getElementById('wlo').value,nm=+n.value,sp=document.getElementById('showpend').checked;let c=0;const sel=new Set();
  for(const r of rows){const ok=(!f||r.dataset.fam===f)&&(!s||r.dataset.st===s)&&(!k||r.dataset.kd===k)&&(+r.dataset.w<=wm)&&(+r.dataset.w>=wlo)&&(+r.dataset.n<=nm)&&(sp||r.dataset.pend==="0");
    r.style.display=ok?'':'none';c+=ok;if(ok)r.dataset.slugs.split(' ').forEach(x=>sel.add(x));}
  count.textContent=c+' rows shown';plot(ENTRIES.filter(e=>sel.has(e.slug)));
}
for(const id of['fam','st','kd','w','wlo','n','pub','showpend']) document.getElementById(id).addEventListener('input',apply);
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
