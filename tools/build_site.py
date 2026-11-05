#!/usr/bin/env python3
"""Builds the static site in docs/ and the tables of README.md from codes/*.json and data/published_codes.json.

    python tools/build_site.py

docs/index.html (English), docs/zh/index.html (Chinese) and docs/de/index.html (German): a summary (best certified code
per check weight, best search bound, re-measured claims), a point plot of k d^2/n against n driven by the filters, a 3-D
frontier and the table, sorted by k d^2/n; a language switch at the top links the three pages. The page texts and the
translation of the text fields of the data are in tools/i18n.py. Rows with identical parameters are merged; internal
run names and archive hashes sit in a collapsed details cell. README.md: the same summary and tables between the
markers (English). Only codes with encoding rate k/n above RATE_MIN are listed."""
import glob
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i18n  # noqa: E402

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


def evidence_text(e, lang="en"):
    t_ = i18n.T[lang]
    ev = e.get("evidence") or {}
    if ev.get("kind") == "certificate":
        c = ev.get("certificate") or {}
        t = t_["ev_cert"] % c.get("complete_through")
        if c.get("parity_argument"):
            t += t_["ev_parity"] % c.get("lower")
        if e.get("witness"):
            t += t_["ev_explicit"] % e["d_upper"]
        elif c.get("found"):
            t += t_["ev_found"] % c["found"]
        return t
    return i18n.method(ev.get("method", ""), lang)


# ------------------------------------------------------------------ merged rows (same parameters, status, origin), sorted by k d^2/n
groups = {}
for e in sorted(entries, key=lambda e: (-e["kd2_over_n"], e["w"], e["slug"])):
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


def link(e, lang="en"):
    t_ = i18n.T[lang]
    out = []
    if e.get("matrices"):
        out.append('<a href="%s">H_X</a> <a href="%s">H_Z</a>' % (REPO + e["matrices"]["HX"], REPO + e["matrices"]["HZ"]))
    if e.get("witness"):
        out.append('<a href="%s">%s</a>' % (REPO + e["witness"], t_["l_ops"]))
    if e["origin"] == "board":
        out.append('<a href="%s">%s</a>' % (e["claimed"]["entry"], t_["l_entry"]))
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


summary_md = []
for b in ("≤ 8", "9–10", "11–12"):
    e = best_exact.get(b)
    if e:
        summary_md.append("- check weight %s, best certified code found by SCE: **%s**, k d²/n = %.1f, %s (%s) %s" % (b, nm(e), e["kd2_over_n"], e["family"], e["construction"], md_link(e)))
if sce_bound:
    e = sce_bound[0]
    summary_md.append("- best search bound: **%s**, k d²/n = %.1f, check weight %d, lightest operators published %s; the true distance may be smaller" % (nm(e), e["kd2_over_n"], e["w"], md_link(e)))
if refuted:
    summary_md.append("- leaderboard claims not reproduced (%d of %d re-measured): %s" % (len(refuted), len(refuted) + len(held), "; ".join("%s claimed d ≤ %d, operator of weight %d found %s" % (nm(e).split(",≤")[0] + "]]", e["claimed"]["d"], e["d"], md_link(e)) for e in refuted)))


def summary_cards(lang):
    t_ = i18n.T[lang]
    cards = []
    for b in ("≤ 8", "9–10", "11–12"):
        e = best_exact.get(b)
        if e:
            cards.append('<div class="card"><div class="lab">%s</div><div class="big">%s</div><div class="val">%s</div><div class="sub">%s</div><div class="sub">%s</div></div>'
                         % (t_["card_exact_lab"] % b, nm(e), t_["card_val_family"] % (e["kd2_over_n"], e["family"]),
                            html.escape(i18n.construction(e["construction"], lang)), link(e, lang)))
    if sce_bound:
        e = sce_bound[0]
        cards.append('<div class="card"><div class="lab">%s</div><div class="big">%s</div><div class="val">%s</div><div class="sub">%s</div><div class="sub">%s</div></div>'
                     % (t_["card_bound_lab"], nm(e), t_["card_bound_val"] % (e["kd2_over_n"], e["w"]), t_["card_bound_sub"], link(e, lang)))
    if refuted or held:
        inner = "; ".join(t_["card_board_item"] % (nm(e).split(",≤")[0] + "]]", e["claimed"]["d"], e["d"], link(e, lang)) for e in refuted) or t_["card_board_none"]
        if lang == "zh":
            inner = inner.replace("; ", "；")
        cards.append('<div class="card"><div class="lab">%s</div><div class="big txt">%s</div><div class="sub">%s</div><div class="sub">%s</div></div>'
                     % (t_["card_board_lab"], t_["card_board_big"] % (len(refuted), len(refuted) + len(held)), inner, t_["card_board_held"] % len(held)))
    return '<div class="cards">' + "".join(cards) + '</div>'


# ------------------------------------------------------------------ pages
CSS = """:root{--brand:#00707f;--brand-d:#00525d;--brand-l:#e8f2f4;--brand-m:#9cc6cd;--ink:#1d2b30;--muted:#55666c;--line:#d8e3e6;--ok:#1a7340;--warn:#9a5b00}
*{box-sizing:border-box}
body{font-family:"Roboto",-apple-system,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans SC",Helvetica,Arial,sans-serif;margin:0;color:var(--ink);background:#fff;font-size:15px;line-height:1.55;border-top:8px solid var(--brand)}
.cond,h1,h2,.plot h3,.hero p,.lang a,footer{font-family:"Roboto Condensed","Roboto",-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans SC",Helvetica,Arial,sans-serif}
header .in{max-width:1400px;margin:0 auto;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px 28px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:16px;color:var(--brand);text-decoration:none}
.brand svg{width:60px;height:60px;flex:none}
.brand .b1{display:block;font-weight:700;font-size:1.12em;letter-spacing:.14em;text-transform:uppercase;line-height:1.3}
.brand .b2{display:block;font-size:.84em;letter-spacing:.14em;text-transform:uppercase;line-height:1.4}
.lang{display:inline-flex;border:1.5px solid var(--brand)}
.lang a{padding:6px 16px;color:var(--brand);text-decoration:none;font-size:1.02em;border-left:1.5px solid var(--brand)}.lang a:first-child{border-left:0}
.lang a:hover{background:var(--brand-l)}.lang a[aria-current=page]{background:var(--brand);color:#fff}
.lang a:focus-visible{outline:2px solid var(--brand-d);outline-offset:2px}
.hero{background:var(--brand);color:#fff}
.hero .in{max-width:1400px;margin:0 auto;padding:44px 24px 50px}
.hero h1{font-weight:400;font-size:clamp(2em,4.4vw,3.1em);line-height:1.12;text-transform:uppercase;margin:0 0 18px;letter-spacing:.005em;text-wrap:balance}
.hero p{font-size:clamp(1.08em,1.6vw,1.3em);line-height:1.45;max-width:58em;margin:0}.hero a{color:#fff}
main{max-width:1400px;margin:0 auto;padding:8px 24px 56px}
h2{font-weight:400;color:var(--brand);text-transform:uppercase;text-align:center;font-size:clamp(1.6em,3vw,2.1em);letter-spacing:.01em;margin:46px 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:10px 0 4px}
.card{border:1px solid var(--line);border-top:4px solid var(--brand);padding:14px 16px;background:#fff}
.card .lab{font-size:.76em;text-transform:uppercase;letter-spacing:.08em;color:var(--brand);font-weight:500}
.card .big{font-family:"Roboto Mono",monospace;font-size:1.28em;font-weight:500;margin:6px 0 2px}.card .sub{font-size:.9em;color:var(--muted)}
.card .val{font-size:.95em}.card .val b{font-weight:700}.card .big.txt{font-family:"Roboto Condensed","Roboto","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;font-size:1.4em;font-weight:400}
.cards,.controls,.wrap,.card{min-width:0}
.controls{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0;padding:12px 14px;background:var(--brand-l);border-left:4px solid var(--brand);font-size:.92em;align-items:center}
select,input[type=number]{font:inherit;font-size:.95em;padding:3px 6px;border:1px solid var(--brand-m);border-radius:0;background:#fff;color:var(--ink)}
input[type=checkbox]{accent-color:var(--brand)}
.plots{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin:10px 0 12px}@media (max-width:1100px){.plots{grid-template-columns:minmax(0,1fr)}}
.plot{border:1px solid var(--line);padding:10px;background:#fff;min-width:0;overflow:hidden}
.plot h3{font-weight:400;font-size:1.25em;letter-spacing:.01em;color:var(--brand);margin:2px 6px 8px}
#plot3d{width:100%;max-width:100%;height:440px}
table{border-collapse:collapse;font-size:.86em;width:100%}th,td{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:var(--brand);color:#fff;cursor:pointer;white-space:nowrap;position:sticky;top:0;font-weight:500}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:"Roboto Mono",monospace;font-size:.95em}
tbody tr:nth-child(even){background:#f5f9fa}tr.exact td.st{color:var(--ok);font-weight:700}tr.search td.st{color:var(--warn)}tr.lower td.st{color:var(--brand)}
.small{color:var(--muted);font-size:.9em}.wrap{overflow-x:auto;border:1px solid var(--line)}details{font-size:.9em}summary{cursor:pointer;color:var(--brand)}
.tag{display:inline-block;padding:0 7px;background:var(--brand-l);font-size:.82em;margin-left:4px;color:var(--brand-d)}.pend{background:#fff1cc;color:#5c4400}
code{font-family:"Roboto Mono",monospace;font-size:.92em}a{color:var(--brand)}a:hover{color:var(--brand-d)}
footer{background:var(--brand);color:#fff;font-size:1em}footer .in{max-width:1400px;margin:0 auto;padding:22px 24px 26px}footer a{color:#fff}
@media (max-width:640px){.brand svg{width:46px;height:46px}.brand .b1{font-size:.98em}.brand .b2{font-size:.74em}.lang a{padding:5px 12px}}"""


def rel(src, dst):
    """Link from the page of language src to the page of language dst (both under docs/)."""
    up = "../" if i18n.PAGE_DIR[src] else ""
    return (up + i18n.PAGE_DIR[dst]) or "./"


def head(lang):
    t_ = i18n.T[lang]
    alt = "".join('<link rel="alternate" hreflang="%s" href="%s">' % (i18n.HTML_LANG[l], rel(lang, l)) for l in i18n.LANGS)
    nav = "".join('<a href="%s" hreflang="%s"%s>%s</a>' % (rel(lang, l), i18n.HTML_LANG[l], ' aria-current="page"' if l == lang else "", i18n.LANG_NAME[l])
                  for l in i18n.LANGS)
    st, org = t_["status"], t_["origin"]
    return ("""<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>%s
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Condensed:wght@400;700&family=Roboto+Mono:wght@400;500&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.0/plotly.min.js"></script>
<style>
%s
</style></head><body>
<header><div class="in"><a class="brand cond" href="%s"><svg viewBox="0 0 60 60" aria-hidden="true"><circle cx="30" cy="30" r="28" fill="none" stroke="currentColor" stroke-width="1.5"/><g stroke="currentColor" stroke-width="1.1" fill="none"><path d="M18 21 L14 39 M18 21 L26 39 M18 21 L34 39 M30 21 L14 39 M30 21 L34 39 M30 21 L46 39 M42 21 L26 39 M42 21 L46 39 M42 21 L34 39"/></g><g fill="currentColor"><rect x="15" y="18" width="6" height="6"/><rect x="27" y="18" width="6" height="6"/><rect x="39" y="18" width="6" height="6"/><circle cx="14" cy="40" r="3"/><circle cx="26" cy="40" r="3"/><circle cx="34" cy="40" r="3"/><circle cx="46" cy="40" r="3"/></g></svg><span><span class="b1">%s</span><span class="b2">%s</span></span></a>
<nav class="lang" aria-label="Language · 语言 · Sprache">%s</nav></div></header>
<section class="hero"><div class="in"><h1>%s</h1>
<p>%s</p></div></section>
<main>
<h2>%s</h2>
""" % (i18n.HTML_LANG[lang], t_["title"], alt, CSS, rel(lang, lang), t_["brand1"], t_["brand2"], nav, t_["h1"], t_["intro"], t_["h_summary"])
        + summary_cards(lang) + """
<h2>%s</h2>
<div class="controls">
<label>%s <select id="fam"><option value="">%s</option><option>lifted-product</option><option>two-block</option><option>pair-partition</option></select></label>
<label>%s <select id="st"><option value="">%s</option><option value="exact">%s</option><option value="search bound">%s</option><option value="lower bound">%s</option></select></label>
<label>%s <select id="kd"><option value="">%s</option><option value="SCE">%s</option><option value="leaderboard, re-measured">%s</option></select></label>
<label>%s <input id="wlo" type="number" value="4" min="3" max="20" style="width:4em"> %s <input id="w" type="number" value="12" min="4" max="20" style="width:4em"></label>
<label>n ≤ <input id="n" type="number" value="2400" min="10" style="width:5.5em"></label>
<label><input id="pub" type="checkbox" checked> %s</label>
<label><input id="showpend" type="checkbox"> %s</label>
<label>%s <select id="surf"><option value="proven">%s</option><option value="all">%s</option><option value="none">%s</option></select></label>
<span id="count" class="small"></span>
</div>
<div id="tip" style="display:none;position:absolute;background:#00444d;color:#fff;padding:3px 7px;border-radius:4px;font-size:.85em;pointer-events:none;white-space:nowrap;z-index:5"></div>
<div class="plots">
<div class="plot"><h3>%s</h3><svg id="plot" width="100%%" viewBox="0 0 700 420" style="display:block;font-family:inherit"></svg>
<p class="small" style="margin:6px 6px 2px">%s</p></div>
<div class="plot"><h3>%s</h3><div id="plot3d"></div>
<p class="small" style="margin:6px 6px 2px">%s</p></div>
</div>
<h2>%s</h2>
<p class="small">%s</p>
<div class="wrap"><table id="t"><thead><tr>
<th data-k="name">%s</th><th data-k="n" class="num">%s</th><th data-k="k" class="num">%s</th><th data-k="d" class="num">%s</th><th data-k="w" class="num">%s</th>
<th data-k="fom" class="num">%s</th><th data-k="family">%s</th><th data-k="status">%s</th><th data-k="kind">%s</th>
<th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>
""" % ((t_["h_explore"], t_["f_family"], t_["f_all"], t_["f_status"], t_["f_all"], st["exact"], st["search bound"], st["lower bound"],
            t_["f_origin"], t_["f_all"], org["SCE"], org["leaderboard, re-measured"], t_["f_weight"], t_["f_to"], t_["f_pub"], t_["f_pend"],
            t_["f_surf"], t_["f_surf_proven"], t_["f_surf_all"], t_["f_surf_none"], t_["p1_title"], t_["p1_note"], t_["p2_title"], t_["p2_note"],
            t_["h_codes"], t_["codes_note"]) + tuple(t_["th"])))


def body(lang):
    t_ = i18n.T[lang]
    out = []
    for r in rows:
        cls = {"exact": "exact", "search bound": "search", "lower bound": "lower", "bounded": "lower"}[r["status"]]
        es = r["es"]
        out.append('<tr class="%s%s" data-fam="%s" data-st="%s" data-kd="%s" data-w="%d" data-n="%d" data-fom="%.2f" data-slugs="%s" data-pend="%d">'
                   % (cls, " pending" if r["pending"] else "", r["family"], r["status"], r["origin"], r["w"], r["n"], r["fom"], " ".join(x["slug"] for x in es), 1 if r["pending"] else 0))
        tags = ""
        if r["claimed"]:
            tags += ' <span class="tag">%s</span>' % (t_["tag_claimed"] % r["claimed"])
        if r["count"] > 1:
            tags += ' <span class="tag">×%d</span>' % r["count"]
        if r["pending"]:
            tags += ' <span class="tag pend">%s</span>' % t_["tag_pending"]
        out.append("<td><b>%s</b>%s</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%d</td><td class=num>%.1f</td><td>%s</td><td class=st>%s</td><td>%s</td>"
                   % (html.escape(r["name"]), tags, r["n"], r["k"], r["d"], r["w"], r["fom"], r["family"], t_["status"][r["status"]], t_["origin"][r["origin"]]))
        det = "<br>".join("<b>%s</b>: %s" % (html.escape(x["slug"]), html.escape(i18n.provenance(x["provenance"], lang))) for x in es)
        cite = html.escape(i18n.citation(es[0].get("citation") or "", lang))
        out.append('<td class="small">%s<details><summary>%s</summary>%s%s</details></td>'
                   % (html.escape(i18n.construction(r["construction"], lang)), t_["provenance"], det, ("<br><i>%s</i>" % cite) if cite else ""))
        out.append('<td class="small">%s</td><td class="small">%s</td></tr>' % (html.escape(evidence_text(r["es"][0], lang)), " · ".join(link(x, lang) for x in es)))
    return "\n".join(out)


TAIL = r"""</tbody></table></div>
</main>
<footer><div class="in">__FOOTER__</div></footer>
<script>
const ENTRIES=__ENTRIES__;const PUB=__PUB__;const I18N=__I18N__;
const rows=[...document.querySelectorAll('#t tbody tr')];
const SH={"lifted-product":"circle","two-block":"diamond","pair-partition":"square"};
const COL={"lifted-product":"#00707f","two-block":"#62aab6","pair-partition":"#e07b00"};
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
  for(let v=0;v<=xmax;v+=xt) g+=`<line x1="${X(v)}" y1="${T}" x2="${X(v)}" y2="${H-B}" stroke="#e3ecee"/><text x="${X(v)}" y="${H-B+16}" text-anchor="middle" font-size="11" fill="#444">${v}</text>`;
  for(let v=0;v<=ymax;v+=yt) g+=`<line x1="${L}" y1="${Y(v)}" x2="${W-R}" y2="${Y(v)}" stroke="#e3ecee"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="#444">${v}</text>`;
  g+=`<rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="none" stroke="#9fb5ba"/>`;
  g+=`<text x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle" font-size="12" fill="#222">${esc(I18N.xlab)}</text>`;
  g+=`<text transform="translate(14,${(T+H-B)/2}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">k d²/n</text>`;
  for(const p of pubs){const c=COL[p.fam]||"#888";g+=marker(X(p.x),Y(p.y),3,p.st==="lower_bound"?"tri":SH[p.fam],p.st==="upper_bound"?"none":c,c,0.8,0.45,p.name);}
  for(const p of pts){if(p.claimed&&p.claimed>p.y){g+=`<line x1="${X(p.x)}" y1="${Y(p.claimed)}" x2="${X(p.x)}" y2="${Y(p.y)}" stroke="#777" stroke-width="1" stroke-dasharray="3,2"/>`;
    g+=`<text x="${X(p.x)+5}" y="${Y(p.claimed)+4}" font-size="9" fill="#777">${esc(I18N.claimed)}</text>`;}}
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
  mk(sce,I18N.sce,5,{color:"#111",width:1.5},0.95);mk(bd,I18N.board,4,{color:"#666",width:1},0.9);mk(pubs,I18N.pub,2.5,{width:0},0.45);
  if(mode!=="none"){const all=pts.concat(pubs).filter(p=>mode==="all"||p.st!=="upper_bound");
    if(all.length){const nmax=Math.max(...all.map(p=>p.x)),ws=[...new Set(all.map(p=>p.w))].sort((a,b)=>a-b),wmin=ws[0],wmax=ws[ws.length-1];
      const xs=[],ys=[],zs=[];for(let w=wmin;w<=wmax;w++)ys.push(w);for(let n=100;n<=nmax+50;n+=50)xs.push(n);
      for(const w of ys){const row=[];for(const n of xs){let m=0;for(const p of all)if(p.x<=n&&p.w<=w&&p.y>m)m=p.y;row.push(m);}zs.push(row);}
      tr.push({type:"surface",x:xs,y:ys,z:zs,name:I18N.front,showscale:false,opacity:0.35,colorscale:[[0,"#e8f2f4"],[1,"#00707f"]],hovertemplate:I18N.fhover+"<extra>"+I18N.front+"</extra>"});}}
  Plotly.react("plot3d",tr,{margin:{l:0,r:0,t:4,b:0},showlegend:true,legend:{orientation:"h",y:0,x:0,font:{size:11}},
    scene:{xaxis:{title:"n"},yaxis:{title:I18N.waxis,dtick:1},zaxis:{title:"k d²/n"},camera:{eye:{x:1.5,y:-1.6,z:0.9}}}},{displaylogo:false,responsive:true});
}
function apply(){
  const f=fam.value,s=st.value,k=kd.value,wm=+w.value,wlo=+document.getElementById('wlo').value,nm=+n.value,sp=document.getElementById('showpend').checked;let c=0;const sel=new Set();
  for(const r of rows){const ok=(!f||r.dataset.fam===f)&&(!s||r.dataset.st===s)&&(!k||r.dataset.kd===k)&&(+r.dataset.w<=wm)&&(+r.dataset.w>=wlo)&&(+r.dataset.n<=nm)&&(sp||r.dataset.pend==="0");
    r.style.display=ok?'':'none';c+=ok;if(ok)r.dataset.slugs.split(' ').forEach(x=>sel.add(x));}
  count.textContent=I18N.rows.replace("{n}",c);plot(ENTRIES.filter(e=>sel.has(e.slug)));
}
for(const id of['fam','st','kd','w','wlo','n','pub','showpend','surf']) document.getElementById(id).addEventListener('input',apply);
apply();
let dir={};document.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;dir[k]=!dir[k];const tb=document.querySelector('#t tbody');
const idx=[...th.parentNode.children].indexOf(th);const get=r=>{const t=r.children[idx].textContent;const v=parseFloat(t.replace(/[^0-9.\-]/g,''));return (k==='name'||k==='family'||k==='status'||k==='kind')?t:v;};
rows.sort((a,b)=>{const x=get(a),y=get(b);return (x>y?1:x<y?-1:0)*(dir[k]?1:-1);});rows.forEach(r=>tb.appendChild(r));}));
</script></body></html>"""

slim = [dict(slug=e["slug"], name=nm(e), n=e["n"], k=e["k"], d=e["d"], w=e["w"], kd2_over_n=e["kd2_over_n"], family=e["family"], d_status=e["d_status"],
             origin=e["origin"], claimed=(dict(d=e["claimed"]["d"]) if e.get("claimed") else None)) for e in entries]
for lang in i18n.LANGS:
    t_ = i18n.T[lang]
    page = (head(lang) + body(lang) + "\n" + TAIL.replace("__FOOTER__", t_["footer"])).replace("__ENTRIES__", json.dumps(slim)).replace(
        "__PUB__", json.dumps(published)).replace("__I18N__", json.dumps(t_["js"], ensure_ascii=False))
    d = os.path.join(ROOT, "docs", i18n.PAGE_DIR[lang])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w").write(page)
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").write("")


# ------------------------------------------------------------------ static figure for the README (points only)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
COL = {"lifted-product": "#00707f", "two-block": "#62aab6", "pair-partition": "#e07b00"}
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
for r in sorted([r for r in rows if r["origin"] != "SCE"], key=lambda r: (-r["fom"], r["w"])):
    e = r["es"][0]; cl = e["k"] * e["claimed"]["d"] ** 2 / e["n"]; heldrow = e["d"] >= e["claimed"]["d"]
    md.append("| [[%d,%d]] | %d | ≤%d | %s%s | %s | %s | %s |" % (e["n"], e["k"], e["w"], e["claimed"]["d"], "held (nothing lighter found)" if heldrow else "%d" % e["d"], " (operator file pending)" if r["pending"] else "",
                                                       ("%.0f" % cl) if heldrow else "%.0f → %.0f" % (cl, e["kd2_over_n"]), r["evidence"].replace("|", "/").split(": ", 1)[-1][:120], md_link(e)))
readme = os.path.join(ROOT, "README.md"); rd = open(readme).read()
a, b = "<!-- codes:start -->", "<!-- codes:end -->"
if a in rd and b in rd:
    rd = rd[:rd.index(a) + len(a)] + "\n" + "\n".join(md) + "\n" + rd[rd.index(b):]
    open(readme, "w").write(rd)
print("entries", len(entries), "rows", len(rows), "pending", sum(1 for r in rows if r["pending"]), "| summary lines", len(summary_md))
