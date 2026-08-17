#!/usr/bin/env python3
import json, os, statistics as st, math, html

SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(f"{SP}/merged.json"))
CRIT = ["code", "difficulty", "ingenuity", "product", "organization", "completeness"]
LBL = {"code": "Code", "difficulty": "Difficulty", "ingenuity": "Ingenuity",
       "product": "Product", "organization": "Organiz.", "completeness": "Complete"}
MAXC = {"code": 22, "difficulty": 20, "ingenuity": 18, "product": 18, "organization": 12, "completeness": 10}


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: -v[i]); r = [0.0]*len(v); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2+1
        i = j+1
    return r


def pearson(a, b):
    n = len(a); ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((x-mb)**2 for x in b)
    return sum((a[i]-ma)*(b[i]-mb) for i in range(n))/math.sqrt(va*vb) if va and vb else float("nan")


def spearman(a, b): return pearson(ranks(a), ranks(b))


ot = [r["o"] for r in rows]; ct = [r["c"] for r in rows]
xin = [r for r in rows if r["set"] == "xin"]

crit_stats = []
for c in CRIT:
    a = [r["so"][c] for r in rows]; b = [r["sc"][c] for r in rows]
    full_o = [r["o"] for r in rows]; drop_o = [r["o"]-r["so"][c] for r in rows]
    crit_stats.append({
        "c": c, "max": MAXC[c],
        "mu_o": st.mean(a), "mu_c": st.mean(b),
        "sd_o": st.pstdev(a), "sd_c": st.pstdev(b),
        "sd_pct": st.pstdev(a)/MAXC[c]*100,
        "rho": spearman(a, b), "rho_wo": spearman(full_o, drop_o),
    })

redund = [[pearson([r["so"][c1] for r in rows], [r["so"][c2] for r in rows]) for c2 in CRIT] for c1 in CRIT]

byauth = {}
for r in rows: byauth.setdefault(r["author"], []).append(r)
auth = []
for a, rs in byauth.items():
    if len(rs) < 3: continue
    d = {}
    for k in ("o", "c"):
        v = sorted((x[k] for x in rs), reverse=True)
        d[k] = (0.5*v[0] + 0.3*st.median(v) + 0.2*v[-1], v[0], st.median(v), v[-1])
    auth.append({"a": a, "n": len(rs), "o": d["o"], "c": d["c"],
                 "agg": (d["o"][0]+d["c"][0])/2})
auth.sort(key=lambda x: -x["agg"])

disagree = sorted(rows, key=lambda r: -abs(r["o"]-r["c"]))[:15]


def bar(v, mx, cls=""):
    return f'<span class="bar {cls}"><i style="width:{v/mx*100:.0f}%"></i></span>'


def esc(s): return html.escape(str(s))


tr = []
for r in rows:
    cells = "".join(f'<td class="n sc">{r["so"][c]}<sub>{r["sc"][c]}</sub></td>' for c in CRIT)
    fl = "".join(f'<span class="flag">{esc(f)}</span>' for f in r["flags"])
    mine = " mine" if r["set"] == "xin" else ""
    tr.append(
        f'<tr class="row{mine}" data-set="{r["set"]}" data-web="{r["web_o"]}" '
        f'data-o="{r["o"]}" data-c="{r["c"]}" data-avg="{r["avg"]}" data-rank="{r["rank"]}" '
        f'data-name="{esc(r["name"]).lower()}" data-author="{esc(r["author"]).lower()}">'
        f'<td class="n rk">{r["rank"]}</td>'
        f'<td class="nm">{esc(r["name"])}{fl}</td>'
        f'<td class="au">{esc(r["author"])}</td>'
        f'<td class="n big">{r["o"]}</td><td class="n big">{r["c"]}</td>'
        f'<td class="n big avg">{r["avg"]:.1f}</td>'
        f'<td class="n d {"warn" if abs(r["o"]-r["c"])>=15 else ""}">{r["o"]-r["c"]:+d}</td>'
        f'{cells}'
        f'<td class="web w-{r["web_o"]}">{r["web_o"]}</td>'
        f'<td class="note"><div>{esc(r["note_o"])}</div></td></tr>')

redund_rows = ""
for i, c1 in enumerate(CRIT):
    tds = ""
    for j, c2 in enumerate(CRIT):
        v = redund[i][j]
        hot = "hot" if (v >= 0.75 and i != j) else ("warm" if (v >= 0.6 and i != j) else "")
        tds += f'<td class="n {hot}">{"&middot;" if i==j else f"{v:.2f}"}</td>'
    redund_rows += f"<tr><th>{LBL[c1]}</th>{tds}</tr>"

crit_rows = ""
for s in crit_stats:
    weak = "weak" if s["sd_pct"] < 18 else ""
    crit_rows += (
        f'<tr class="{weak}"><th>{LBL[s["c"]]}</th><td class="n">{s["max"]}</td>'
        f'<td class="n">{s["mu_o"]:.1f}</td><td class="n">{s["mu_c"]:.1f}</td>'
        f'<td class="n">{s["sd_o"]:.2f}</td><td class="n">{s["sd_c"]:.2f}</td>'
        f'<td class="n">{s["sd_pct"]:.0f}%</td>'
        f'<td class="n">{s["rho"]:.3f}</td><td class="n">{s["rho_wo"]:.3f}</td></tr>')

auth_rows = ""
for a in auth:
    mine = ' class="mine"' if a["a"].startswith("Xin") else ""
    auth_rows += (
        f'<tr{mine}><th>{esc(a["a"])}</th><td class="n">{a["n"]}</td>'
        f'<td class="n big">{a["o"][0]:.1f}</td><td class="n big">{a["c"][0]:.1f}</td>'
        f'<td class="n dim">{a["o"][1]}/{a["o"][2]:.0f}/{a["o"][3]}</td>'
        f'<td class="n dim">{a["c"][1]}/{a["c"][2]:.0f}/{a["c"][3]}</td>'
        f'<td class="n">{a["o"][1]-a["o"][3]}</td></tr>')

dis_rows = ""
for r in disagree:
    d = {c: r["so"][c]-r["sc"][c] for c in CRIT}
    w = max(d, key=lambda k: abs(d[k]))
    dis_rows += (f'<tr><th>{esc(r["name"])}</th><td class="au">{esc(r["author"])}</td>'
                 f'<td class="n">{r["o"]}</td><td class="n">{r["c"]}</td>'
                 f'<td class="n warn">{r["o"]-r["c"]:+d}</td><td>{LBL[w]} {d[w]:+d}</td>'
                 f'<td class="note">{esc(r["note_c"])}</td></tr>')

from collections import Counter
flagc = Counter(f for r in rows for f in r["flags"])
flag_rows = "".join(f'<tr><th>{esc(f)}</th><td class="n">{n}</td></tr>' for f, n in flagc.most_common())

web_none = sum(1 for r in rows if r["web_o"] == "none")
web_agree = sum(1 for r in rows if r["web_o"] == r["web_c"])

HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Applicant Rubric v1: 160 skills, two judges</title>
<style>
:root{{--ink:#1a1815;--dim:#6b645c;--faint:#9a9188;--line:#ddd6cb;--paper:#f7f3ec;
--card:#fffdf9;--green:#2f5d4f;--warn:#a4552e;--mine:#f0e6d2;--bar:#c8bfae}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:14px/1.55 "IBM Plex Sans",-apple-system,Segoe UI,Helvetica,Arial,sans-serif}}
.wrap{{max-width:1500px;margin:0 auto;padding:34px 26px 80px}}
h1{{font:600 27px/1.2 Georgia,serif;margin:0 0 6px}}
h2{{font:600 18px/1.3 Georgia,serif;margin:44px 0 4px;padding-bottom:7px;border-bottom:1px solid var(--line)}}
h3{{font:600 14px/1.3 "IBM Plex Sans",sans-serif;margin:22px 0 6px;letter-spacing:.02em}}
p{{margin:8px 0;max-width:74ch;color:#3a352f}}
.lede{{color:var(--dim);margin:0 0 4px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:10px;margin:20px 0 6px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:11px 13px}}
.kpi b{{display:block;font:600 23px/1.15 Georgia,serif;color:var(--green)}}
.kpi span{{font-size:11px;color:var(--dim);letter-spacing:.03em;text-transform:uppercase}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;background:var(--card)}}
.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:3px;margin-top:12px}}
th,td{{padding:5px 8px;text-align:left;border-bottom:1px solid #eee7dc;vertical-align:top}}
thead th{{position:sticky;top:0;background:#efe9de;font-size:10.5px;letter-spacing:.05em;
text-transform:uppercase;color:var(--dim);font-weight:600;cursor:pointer;white-space:nowrap;z-index:2}}
thead th:hover{{color:var(--ink)}}
tbody tr:hover{{background:#faf6ee}}
tr.mine{{background:var(--mine)}}
tr.mine:hover{{background:#e9dcc3}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
.rk{{color:var(--faint);width:38px}}
.nm{{font-weight:600;min-width:170px}}
.au{{color:var(--dim);white-space:nowrap;font-size:11.5px}}
.big{{font-weight:600}}
.avg{{color:var(--green)}}
.sc{{color:var(--dim);white-space:nowrap;font-size:11.5px}}
.sc sub{{color:var(--faint);font-size:9.5px;margin-left:1px}}
.d.warn{{color:var(--warn);font-weight:600}}
.note{{color:var(--dim);font-size:11.5px;min-width:330px;max-width:520px}}
.note div{{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;cursor:pointer}}
.note div.open{{-webkit-line-clamp:unset}}
.web{{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em}}
.w-strong{{color:var(--green);font-weight:600}}.w-partial{{color:#8a7a4e}}.w-none{{color:var(--faint)}}
.flag{{display:inline-block;margin-left:5px;padding:0 4px;border:1px solid var(--warn);
color:var(--warn);border-radius:2px;font-size:9px;letter-spacing:.03em;vertical-align:1px}}
.controls{{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 0;align-items:center}}
input,select{{font:13px "IBM Plex Sans",sans-serif;padding:6px 9px;border:1px solid var(--line);
border-radius:3px;background:var(--card);color:var(--ink)}}
input{{min-width:210px}}
.small{{font-size:12px;color:var(--dim)}}
td.hot{{background:#f3ddd2;font-weight:600;color:var(--warn)}}
td.warm{{background:#f6ecdd}}
tr.weak th{{color:var(--warn)}}
tr.weak td{{color:var(--warn)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:26px}}
@media(max-width:1000px){{.two{{grid-template-columns:1fr}}}}
.finding{{background:var(--card);border-left:3px solid var(--green);padding:11px 15px;margin:12px 0}}
.finding b{{color:var(--green)}}
ul{{max-width:74ch;padding-left:19px}} li{{margin:5px 0}}
code{{background:#efe9de;padding:1px 4px;border-radius:2px;font-size:12px}}
</style></head><body><div class="wrap">

<h1>Applicant Rubric v1: stress test</h1>
<p class="lede">160 skills (124 from the Pantheon corpus + 36 of your own) scored independently by
Claude Opus and Codex <code>gpt-5.6-terra</code> at high reasoning effort. Both judges read
byte-identical dossiers, so every difference below is the model, not the input.</p>

<div class="kpis">
<div class="kpi"><b>{spearman(ot,ct):.3f}</b><span>rank correlation</span></div>
<div class="kpi"><b>{st.mean([abs(a-b) for a,b in zip(ot,ct)]):.1f}</b><span>mean abs gap</span></div>
<div class="kpi"><b>{st.mean(ot)-st.mean(ct):+.1f}</b><span>opus minus codex</span></div>
<div class="kpi"><b>{sum(1 for r in rows if abs(r["o"]-r["c"])>=15)}</b><span>splits &ge; 15 pts</span></div>
<div class="kpi"><b>{web_none}</b><span>no web evidence</span></div>
<div class="kpi"><b>{flagc.get("claims_exceed_code",0)}</b><span>claims &gt; code</span></div>
</div>

<h2>Does the rubric survive a change of judge?</h2>
<p>Yes for ordering, no for level. The two models rank the field almost identically
(&rho; = {spearman(ot,ct):.3f}) but codex sits {st.mean(ot)-st.mean(ct):.1f} points lower and spreads
wider (sd {st.pstdev(ct):.1f} vs {st.pstdev(ot):.1f}). Practical consequence: never write an absolute
cutoff like &ldquo;must score 65&rdquo; into the process. Score against the pool, or average two judges.</p>
<div class="scroll"><table><thead><tr>
<th>judge</th><th class="n">mean</th><th class="n">sd</th><th class="n">min</th><th class="n">p25</th>
<th class="n">median</th><th class="n">p75</th><th class="n">max</th><th class="n">&gt;85</th></tr></thead><tbody>
<tr><th>Opus</th><td class="n">{st.mean(ot):.1f}</td><td class="n">{st.pstdev(ot):.1f}</td>
<td class="n">{min(ot)}</td><td class="n">{sorted(ot)[len(ot)//4]}</td><td class="n">{st.median(ot):.0f}</td>
<td class="n">{sorted(ot)[3*len(ot)//4]}</td><td class="n">{max(ot)}</td><td class="n">{sum(1 for x in ot if x>85)}</td></tr>
<tr><th>Codex terra</th><td class="n">{st.mean(ct):.1f}</td><td class="n">{st.pstdev(ct):.1f}</td>
<td class="n">{min(ct)}</td><td class="n">{sorted(ct)[len(ct)//4]}</td><td class="n">{st.median(ct):.0f}</td>
<td class="n">{sorted(ct)[3*len(ct)//4]}</td><td class="n">{max(ct)}</td><td class="n">{sum(1 for x in ct if x>85)}</td></tr>
</tbody></table></div>

<h2>Which criteria are earning their weight?</h2>
<p><b>sd/max</b> is how much of a criterion's range actually gets used. <b>&rho; judges</b> is how much
the two models agree on that criterion alone. <b>&rho; without</b> is the rank correlation between the
full total and the total with this criterion deleted (the closer to 1.000, the less that
criterion changes anyone's position). Rows in red use under a fifth of their range.</p>
<div class="scroll"><table><thead><tr><th>criterion</th><th class="n">max</th>
<th class="n">mean O</th><th class="n">mean C</th><th class="n">sd O</th><th class="n">sd C</th>
<th class="n">sd/max</th><th class="n">&rho; judges</th><th class="n">&rho; without</th></tr></thead>
<tbody>{crit_rows}</tbody></table></div>

<div class="finding"><b>Finding 1.</b> Product judgment, organization and completeness carry 40 of the
100 points but barely move the ranking. Deleting product judgment leaves the order essentially
unchanged (&rho; = {[s for s in crit_stats if s["c"]=="product"][0]["rho_wo"]:.3f}), because judges hand out
{[s for s in crit_stats if s["c"]=="product"][0]["mu_o"]:.1f}/18 to almost everything. The weight is real; the
discrimination is not. The anchors are too generous, not the concept.</div>

<h3>Criterion redundancy (Opus scores; are any two criteria secretly one?)</h3>
<div class="scroll"><table><thead><tr><th></th>
{"".join(f'<th class="n">{LBL[c]}</th>' for c in CRIT)}</tr></thead><tbody>{redund_rows}</tbody></table></div>
<div class="finding"><b>Finding 2.</b> Code quality and difficulty correlate at
<b>{redund[0][1]:.2f}</b>. Judges are not separating &ldquo;how hard was the problem&rdquo; from &ldquo;how well was it built&rdquo;; 42 of 100 points are measuring one thing, which is why the whole
ranking is dominated by whether a skill ships real code at all. Ingenuity and product judgment are
also entangled ({redund[2][3]:.2f}).</div>

<h2>The finding that matters most for a web-coding screen</h2>
<p><b>{web_none} of 160 skills give you no evidence of web ability at all</b>, and the two judges agree
on that call {web_agree}/160 of the time ({web_agree/160*100:.0f}%). If applicants pick three favourites
freely, a strong candidate can hand you three excellent skills that tell you nothing about the axis you
care about most. Require at least one web-facing submission, and keep reporting the flag separately so a
high total cannot disguise an absent signal.</p>

<h2>Where the two judges split (this is where the rubric is vague)</h2>
<div class="scroll"><table><thead><tr><th>skill</th><th>author</th><th class="n">opus</th>
<th class="n">codex</th><th class="n">&Delta;</th><th>widest criterion</th><th>codex reasoning</th>
</tr></thead><tbody>{dis_rows}</tbody></table></div>
<div class="finding"><b>Finding 3.</b> Every one of the largest splits runs the same direction: Opus is
more generous ({st.mean([r["so"]["ingenuity"] for r in rows]):.1f} vs
{st.mean([r["sc"]["ingenuity"] for r in rows]):.1f} on ingenuity). The disputes concentrate on
prose-heavy skills, where one judge reads a well-argued method as insight and the other reads it as a
document. Ingenuity needs concrete worked examples in the rubric, not adjectives.</div>

<h2>Flags raised</h2>
<div class="two"><div class="scroll"><table><thead><tr><th>flag</th><th class="n">count</th></tr></thead>
<tbody>{flag_rows}</tbody></table></div>
<div><p><code>claims_exceed_code</code> fired {flagc.get("claims_exceed_code",0)} times, far more than
anything else, and it is exactly the signal a hiring screen wants, the gap between what someone says
they built and what is in the files. It is currently a side-channel note. It should be scored.</p></div></div>

<h2>Author aggregate</h2>
<p>Applied as the rubric specifies: <code>0.5&times;best + 0.3&times;median + 0.2&times;worst</code>, authors with
3 or more skills. The <b>spread</b> column (best minus worst) is the consistency signal: a wide
spread means the person has range but no floor.</p>
<div class="scroll"><table><thead><tr><th>author</th><th class="n">n</th><th class="n">opus agg</th>
<th class="n">codex agg</th><th class="n">opus hi/med/lo</th><th class="n">codex hi/med/lo</th>
<th class="n">spread</th></tr></thead><tbody>{auth_rows}</tbody></table></div>

<h2>Your own skills in the field</h2>
<p>Your 36 skills average {st.mean([r["avg"] for r in xin]):.1f} against a field average of
{st.mean([r["avg"] for r in rows]):.1f}, with a median rank of
{st.median([r["rank"] for r in xin]):.0f} of 160, and {sum(1 for r in xin if r["rank"]<=25)} land in the
top 25 land there. The distribution is the interesting part: the tooling skills that ship real Python
(extract-web-content, ingest-web-feeds, gemini, slide-making, chatgpt) sit at the top, and the
prose-only research procedures cluster in the bottom third. Under the &ldquo;pick 3 favourites&rdquo;
format this matters enormously: your best three score
{st.mean(sorted([r["avg"] for r in xin],reverse=True)[:3]):.1f} while your median three score
{st.median([r["avg"] for r in xin]):.1f}.</p>

<h2>Full table</h2>
<p class="small">Each criterion cell shows <b>Opus</b> with codex as the small subscript. Your own
skills are highlighted. Click any header to sort; &Delta; above 15 points is flagged.</p>
<div class="controls">
<input id="q" placeholder="filter by skill or author...">
<select id="setf"><option value="">all skills</option><option value="xin">mine only</option>
<option value="portal">corpus only</option></select>
<select id="webf"><option value="">any web evidence</option><option value="strong">web: strong</option>
<option value="partial">web: partial</option><option value="none">web: none</option></select>
<span class="small" id="cnt"></span></div>
<div class="scroll"><table id="main"><thead><tr>
<th class="n" data-k="rank">#</th><th data-k="name">skill</th><th data-k="author">author</th>
<th class="n" data-k="o">opus</th><th class="n" data-k="c">codex</th><th class="n" data-k="avg">avg</th>
<th class="n" data-k="d">&Delta;</th>
{"".join(f'<th class="n" data-k="{c}">{LBL[c]}<br><span style="font-weight:400">/{MAXC[c]}</span></th>' for c in CRIT)}
<th data-k="web">web</th><th>opus reasoning</th></tr></thead>
<tbody>{"".join(tr)}</tbody></table></div>

<script>
const tb=document.querySelector('#main tbody'), rows=[...tb.rows];
const q=document.getElementById('q'), sf=document.getElementById('setf'),
      wf=document.getElementById('webf'), cnt=document.getElementById('cnt');
function apply(){{
  const t=q.value.trim().toLowerCase(), s=sf.value, w=wf.value; let n=0;
  rows.forEach(r=>{{
    const ok=(!t||r.dataset.name.includes(t)||r.dataset.author.includes(t))
      &&(!s||r.dataset.set===s)&&(!w||r.dataset.web===w);
    r.style.display=ok?'':'none'; if(ok)n++;
  }});
  cnt.textContent=n+' of '+rows.length+' shown';
}}
[q,sf,wf].forEach(e=>e.addEventListener('input',apply)); apply();
tb.addEventListener('click',e=>{{const d=e.target.closest('.note div'); if(d)d.classList.toggle('open');}});
let dir={{}};
document.querySelectorAll('#main thead th[data-k]').forEach((th,i)=>{{
  th.addEventListener('click',()=>{{
    const k=th.dataset.k; dir[k]=!dir[k]; const sign=dir[k]?1:-1;
    const idx=[...th.parentNode.children].indexOf(th);
    const num=th.classList.contains('n');
    rows.sort((a,b)=>{{
      let x=a.cells[idx].textContent.trim(), y=b.cells[idx].textContent.trim();
      if(num){{x=parseFloat(x)||0;y=parseFloat(y)||0;return (x-y)*sign;}}
      return x.localeCompare(y)*sign;
    }});
    rows.forEach(r=>tb.appendChild(r));
  }});
}});
</script>
</div></body></html>"""

open(f"{SP}/report.html", "w").write(HTML)
print("wrote report.html", len(HTML), "chars")
