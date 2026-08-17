#!/usr/bin/env python3
# HOUSE JUDGE: codex gpt-5.6-terra, high reasoning effort (Xin's call).
import json, glob, os, html

SP = os.path.dirname(os.path.abspath(__file__))
CR = [("quality", "Code quality", 25), ("complexity", "Complexity ceiling", 20),
      ("activity", "Activity &amp; maintenance", 15), ("pre_ai", "Pre-AI substance", 15),
      ("traction", "Traction", 10), ("domain", "Domain depth", 15)]
CLS_ORDER = ["original-engineering", "original-small", "coursework", "tutorial-follow",
             "fork-derivative", "template-scaffold", "curation-docs", "generated-oneshot"]
GOOD = {"original-engineering", "original-small"}
TIER_RANK = {"none": 0, "notable": 1, "exceptional": 2, "landmark": 3}

rows = [json.load(open(f)) for f in sorted(glob.glob(f"{SP}/gh_out/*.json"))]
facts = {r["login"]: json.load(open(f"{SP}/gh/{r['login']}.json"))["facts"] for r in rows}
rows.sort(key=lambda r: -r["total"])


def e(s): return html.escape(str(s))


def band(v, mx):
    p = v / mx
    return "hi" if p >= .75 else ("mid" if p >= .45 else "lo")


cards = ""
for r in rows:
    f = facts[r["login"]]
    tags = "".join(
        f'<span class="tag {"vibe" if t["specialty"].startswith("vibe-coder") else ""}'
        f'{" insuf" if t["specialty"]=="insufficient-evidence" else ""}">'
        f'{e(t["specialty"])}<b>{e(t["level"])}</b></span>' for t in r["tags"])
    bars = "".join(
        f'<div class="cr"><span class="cl">{lbl}</span>'
        f'<span class="cbar"><i class="{band(r["scores"][k],mx)}" '
        f'style="width:{r["scores"][k]/mx*100:.0f}%"></i></span>'
        f'<span class="cv">{r["scores"][k]}<em>/{mx}</em></span></div>'
        for k, lbl, mx in CR)

    ex = r["exceptional"]
    exm = "".join(
        f'<li><code>{e(m["metric"])}</code> <b>{m["value"]:,}</b>'
        + (f' on <b>{e(m["repo"])}</b>' if m.get("repo") else " across original repos")
        + ("" if m["is_code"] else ' <span class="nc">(not code)</span>') + "</li>"
        for m in ex["metrics"])
    nonc = "".join(
        f'<li><b>{e(n["repo"])}</b> {n["stars"]:,} stars, excluded: {e(n["why"])}</li>'
        for n in ex["reach_non_code"])
    exblock = (
        f'<div class="exc t-{e(ex["tier"])}">'
        f'<div class="exh">exceptional flag: <b>{e(ex["tier"])}</b></div>'
        + (f"<ul>{exm}</ul>" if exm else "")
        + (f'<div class="exn">Reach that does not qualify as engineering:</div><ul class="nq">{nonc}</ul>' if nonc else "")
        + (f'<p class="exnote">{e(ex["note"])}</p>' if ex.get("note") else "")
        + "</div>")

    classes = "".join(
        f'<tr class="{"good" if c["class"] in GOOD else "bad"}">'
        f'<td class="cn">{e(c["repo"])}</td><td class="cc">{e(c["class"])}</td>'
        f'<td class="cw">{e(c["why"])}</td></tr>' for c in
        sorted(r["repo_classes"], key=lambda c: CLS_ORDER.index(c["class"])
               if c["class"] in CLS_ORDER else 9))

    ev = "".join(f"<li>{e(x)}</li>" for x in r["evidence"])
    ag = "".join(f"<li>{e(x)}</li>" for x in r["against"])
    pre = ("scored on substitute evidence, since the account postdates the cutoffs"
           if not r["pre_ai_applicable"] else "scored directly against the cutoffs")
    cards += f"""
<div class="card">
  <div class="chead">
    <div><a class="who" href="https://github.com/{e(r['login'])}">{e(r['login'])}</a>
      <span class="sub">{e(f.get('name') or '')}{' &middot; ' + e(f['company']) if f.get('company') else ''}</span></div>
    <div class="tot"><b>{r['total']}</b><span>/100</span></div>
  </div>
  <div class="tags">{tags}<span class="conf">confidence: {e(r['confidence'])}</span></div>
  <p class="head">{e(r['headline'])}</p>
  <div class="stats">
    <span><b>{f['account_age_years']}y</b> account</span>
    <span><b>{f['original_repos']}</b> original repos</span>
    <span><b>{f['total_stars']:,}</b> stars</span>
    <span><b>{f['total_forks']:,}</b> forks</span>
    <span><b>{f['commits_total_public']:,}</b> commits</span>
    <span><b>{f['commits_before_chatgpt']:,}</b> pre-ChatGPT</span>
    <span><b>{f['active_years']}</b> active years</span>
  </div>
  {bars}
  <div class="vibe"><b>{r['vibe_coded_pct']}%</b> of the footprint reads as one-shot generated
    work &nbsp;<span class="ded">{r['vibe_deduction']} pts</span></div>
  {exblock}
  <h4>Repos, classified before scoring</h4>
  <table class="cls"><tbody>{classes}</tbody></table>
  <h4>Evidence for</h4><ul class="ev">{ev}</ul>
  <h4>Against</h4><ul class="ev ag">{ag}</ul>
  <p class="ask"><b>To confirm or raise:</b> {e(r['ask_for'])}</p>
  <p class="pre"><b>Pre-AI:</b> {pre}.</p>
</div>"""

heads = "".join(f'<th class="n">{e(r["login"])}</th>' for r in rows)
cmp_rows = "".join(
    f'<tr><th>{lbl} <span class="mx">/{mx}</span></th>' + "".join(
        f'<td class="n {band(r["scores"][k],mx)}">{r["scores"][k]}</td>' for r in rows) + "</tr>"
    for k, lbl, mx in CR)
cmp_rows += ('<tr><th>Vibe deduction</th>' +
             "".join(f'<td class="n">{r["vibe_deduction"]}</td>' for r in rows) + "</tr>")
cmp_rows += ('<tr class="tot"><th>Total</th>' +
             "".join(f'<td class="n"><b>{r["total"]}</b></td>' for r in rows) + "</tr>")
cmp_rows += ('<tr><th>Exceptional</th>' + "".join(
    f'<td class="n tier t-{e(r["exceptional"]["tier"])}">{e(r["exceptional"]["tier"])}</td>'
    for r in rows) + "</tr>")
cmp_rows += ('<tr><th>Tags</th>' + "".join(
    '<td class="n tg">' + "<br>".join(f'{e(t["specialty"])} {e(t["level"])}' for t in r["tags"])
    + "</td>" for r in rows) + "</tr>")

fact_rows = ""
for key, lbl, fmt in [("account_age_years", "Account age (years)", "{:g}"),
                      ("original_repos", "Original repos", "{:,}"),
                      ("forked_repos", "Forked repos", "{:,}"),
                      ("total_stars", "Stars received", "{:,}"),
                      ("total_forks", "Forks received", "{:,}"),
                      ("max_stars", "Biggest single repo (stars)", "{:,}"),
                      ("commits_total_public", "Public commits", "{:,}"),
                      ("commits_before_copilot", "Commits before Copilot (Jun 2021)", "{:,}"),
                      ("commits_before_chatgpt", "Commits through ChatGPT (Nov 2022)", "{:,}"),
                      ("repos_created_before_chatgpt", "Repos created pre-ChatGPT", "{:,}"),
                      ("active_years", "Years with 20+ commits", "{:,}")]:
    fact_rows += f"<tr><th>{lbl}</th>" + "".join(
        f'<td class="n">{fmt.format(facts[r["login"]][key])}</td>' for r in rows) + "</tr>"

HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GitHub Coder Rubric v2: four profiles</title><style>
:root{{--ink:#1a1815;--dim:#6b645c;--faint:#9a9188;--line:#ddd6cb;--paper:#f7f3ec;
--card:#fffdf9;--green:#2f5d4f;--warn:#a4552e;--mid:#8a7a4e;--gold:#9a7b18}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:14px/1.55 "IBM Plex Sans",-apple-system,Segoe UI,Helvetica,Arial,sans-serif}}
.wrap{{max-width:1320px;margin:0 auto;padding:34px 26px 80px}}
h1{{font:600 27px/1.2 Georgia,serif;margin:0 0 6px}}
h2{{font:600 18px/1.3 Georgia,serif;margin:44px 0 4px;padding-bottom:7px;border-bottom:1px solid var(--line)}}
h4{{font:600 10.5px/1.3 "IBM Plex Sans";letter-spacing:.07em;text-transform:uppercase;
color:var(--dim);margin:16px 0 6px}}
p{{margin:8px 0;max-width:78ch;color:#3a352f}}
.lede{{color:var(--dim);margin:0 0 4px;max-width:84ch}}
table{{width:100%;border-collapse:collapse;font-size:13px;background:var(--card)}}
.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:3px;margin-top:12px}}
th,td{{padding:6px 10px;text-align:left;border-bottom:1px solid #eee7dc;vertical-align:top}}
thead th{{background:#efe9de;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
tr.tot td,tr.tot th{{background:#efe9de;font-size:15px}}
.mx{{color:var(--faint);font-weight:400}}
td.hi{{color:var(--green);font-weight:600}} td.mid{{color:var(--mid)}} td.lo{{color:var(--warn)}}
td.tg{{font-size:11px;color:var(--dim);line-height:1.5}}
.tier{{font-size:11px;letter-spacing:.05em;text-transform:uppercase}}
.t-exceptional,.t-landmark{{color:var(--gold);font-weight:600}}
.t-notable{{color:var(--mid)}} .t-none{{color:var(--faint)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:18px;margin-top:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:16px 18px}}
.chead{{display:flex;justify-content:space-between;align-items:baseline;gap:10px}}
.who{{font:600 19px/1.2 Georgia,serif;color:var(--ink);text-decoration:none}}
.who:hover{{color:var(--green)}}
.sub{{color:var(--dim);font-size:12px;margin-left:7px}}
.tot b{{font:600 26px/1 Georgia,serif;color:var(--green)}}
.tot span{{color:var(--faint);font-size:12px}}
.tags{{margin:9px 0 4px;display:flex;flex-wrap:wrap;gap:5px;align-items:center}}
.tag{{border:1px solid var(--line);background:#f2ece1;border-radius:2px;padding:2px 7px;font-size:11px}}
.tag b{{margin-left:5px;color:var(--green)}}
.tag.vibe{{border-color:var(--warn);color:var(--warn);background:#f7ece6}}
.tag.vibe b{{color:var(--warn)}}
.tag.insuf{{border-color:var(--warn);background:#f6e8e0;color:var(--warn)}}
.conf{{color:var(--faint);font-size:11px;margin-left:auto}}
.head{{font-style:italic;color:#3a352f;margin:8px 0 12px}}
.stats{{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:11.5px;color:var(--dim);
padding:9px 0;border-top:1px solid #eee7dc;border-bottom:1px solid #eee7dc;margin-bottom:11px}}
.stats b{{color:var(--ink);font-variant-numeric:tabular-nums}}
.cr{{display:flex;align-items:center;gap:9px;margin:4px 0;font-size:12px}}
.cl{{width:140px;color:var(--dim);flex:none}}
.cbar{{flex:1;height:7px;background:#ece5d8;border-radius:4px;overflow:hidden}}
.cbar i{{display:block;height:100%;border-radius:4px}}
.cbar .hi{{background:var(--green)}} .cbar .mid{{background:var(--mid)}} .cbar .lo{{background:var(--warn)}}
.cv{{width:46px;text-align:right;font-variant-numeric:tabular-nums;flex:none}}
.cv em{{color:var(--faint);font-style:normal;font-size:11px}}
.vibe{{margin:12px 0 0;padding:8px 11px;background:#f2ece1;border-radius:3px;font-size:12px;color:var(--dim)}}
.vibe b{{color:var(--ink)}} .ded{{color:var(--warn);font-weight:600}}
.exc{{margin-top:10px;padding:10px 12px;border-radius:3px;border:1px solid var(--line);font-size:12px}}
.exc.t-exceptional,.exc.t-landmark{{border-color:var(--gold);background:#faf4e2}}
.exc.t-notable{{background:#f6f1e6}}
.exc.t-none{{background:#f4f1ea;color:var(--dim)}}
.exh{{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--dim)}}
.exh b{{color:var(--gold)}}
.exc.t-none .exh b{{color:var(--faint)}}
.exc ul{{margin:6px 0 0;padding-left:18px}} .exc li{{margin:3px 0}}
.exc code{{background:#efe9de;padding:0 4px;border-radius:2px;font-size:11px}}
.exn{{margin-top:8px;color:var(--dim);font-size:11px}}
ul.nq li{{color:var(--dim)}}
.nc{{color:var(--warn);font-size:11px}}
.exnote{{margin:7px 0 0;font-size:11.5px;color:var(--dim)}}
table.cls{{font-size:11.5px}}
table.cls td{{padding:4px 8px 4px 0;border-bottom:1px solid #f2ece1}}
.cn{{font-weight:600;white-space:nowrap}}
.cc{{white-space:nowrap;font-size:10.5px;letter-spacing:.03em}}
tr.good .cc{{color:var(--green)}} tr.bad .cc{{color:var(--warn)}}
.cw{{color:var(--dim)}}
ul.ev{{margin:0;padding-left:18px;font-size:12.5px;color:#3a352f}}
ul.ev li{{margin:5px 0}} ul.ev.ag li{{color:var(--warn)}}
.ask,.pre{{font-size:12px;color:var(--dim);margin-top:10px}}
.note{{background:var(--card);border-left:3px solid var(--green);padding:11px 15px;margin:14px 0}}
.note b{{color:var(--green)}}
ul.plain{{max-width:80ch}} ul.plain li{{margin:6px 0}}
code{{background:#efe9de;padding:1px 4px;border-radius:2px;font-size:12px}}
</style></head><body><div class="wrap">

<h1>GitHub Coder Rubric v2: four profiles</h1>
<p class="lede">Judged by codex <code>gpt-5.6-terra</code> at high reasoning effort, the house
judge. Each account is collected in layers (facts, full inventory, then a deep dive on up to six
repos picked as a mix of most-starred, largest, oldest-substantial and most-recent-substantial)
and scored from real source files. v2 is deliberately harsher than v1: every deep-dive repo is
classified before scoring, coursework and forks cannot buy expertise, levels carry hard caps, and
reach is reported through a separate exceptional flag instead of being blended into the score.</p>

<h2>Side by side</h2>
<div class="scroll"><table><thead><tr><th>criterion</th>{heads}</tr></thead>
<tbody>{cmp_rows}</tbody></table></div>

<h2>Computed facts (exact, not judged)</h2>
<div class="scroll"><table><thead><tr><th>fact</th>{heads}</tr></thead>
<tbody>{fact_rows}</tbody></table></div>
<div class="note"><b>Read these with care.</b> Public commit counts miss anything committed with
an unlinked email, everything in private and employer repositories, and non-default branches. A
low number is weak evidence, not proof. Repo size is not code size either: a 45MB repo at a
vendored fraction of 0.99 is a committed build directory, which says something about hygiene and
nothing about volume of work.</div>

<h2>Profiles</h2>
<div class="cards">{cards}</div>

</div></body></html>"""
open(f"{SP}/gh_report.html", "w").write(HTML)
print("wrote gh_report.html", len(HTML), "chars")
