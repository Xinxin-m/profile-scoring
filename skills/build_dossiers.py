#!/usr/bin/env python3
"""Build one identical dossier per skill so both judges read the same bytes."""
import json, os, re, sys

ROOT = "/Users/xin/Stanford/Research/Yzilabs/skill-pantheon"
OUT = "/private/tmp/claude-501/-Users-xin-Stanford-Research/90e0cf0d-748d-46a5-ae37-4d0f94f96b12/scratchpad/dossiers"
os.makedirs(OUT, exist_ok=True)

SKIP_DIR = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
            ".next", ".cache", "site-packages", ".pytest_cache", ".vercel", "target"}
BIN_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".mp4", ".mov",
           ".woff", ".woff2", ".ttf", ".otf", ".ico", ".svg", ".mp3", ".wav", ".bin",
           ".so", ".dylib", ".pyc", ".jar", ".gz", ".tar", ".webm", ".avif"}
CODE_EXT = [".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh",
            ".rb", ".go", ".rs", ".html", ".css", ".scss", ".sql", ".applescript",
            ".scpt", ".toml", ".yaml", ".yml", ".json", ".jq", ".pl", ".lua", ".r"]

SKILL_CAP   = 12000
FILE_CAP    = 4200
BODY_BUDGET = 22000


def inventory(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIR and not d.startswith(".venv")]
        for fn in fns:
            p = os.path.join(dp, fn)
            if os.path.islink(p) and not os.path.exists(p):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext in BIN_EXT or fn.startswith("."):
                continue
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz > 900_000:
                continue
            out.append((os.path.relpath(p, root), sz))
    return sorted(out)


def read(p, cap):
    try:
        t = open(p, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return f"<<unreadable: {e}>>"
    if len(t) > cap:
        t = t[:cap] + f"\n... [truncated, file is {len(t)} chars]"
    return t


def rank_key(rel):
    ext = os.path.splitext(rel)[1].lower()
    base = os.path.basename(rel).lower()
    if base == "skill.md":
        return (0, 0, rel)
    if ext in CODE_EXT:
        return (1, CODE_EXT.index(ext), rel)          # code first, in listed order
    if ext in (".md", ".markdown", ".txt"):
        return (2, 0, rel)
    return (3, 0, rel)


def build(sid, name, author, source, srcdir):
    files = inventory(srcdir)
    if not files:
        return None
    total_bytes = sum(s for _, s in files)
    lines = []
    lines.append(f"# SKILL DOSSIER: {sid}")
    lines.append(f"name: {name}")
    lines.append(f"author: {author}")
    lines.append(f"source: {source}")
    lines.append(f"files: {len(files)}   text bytes: {total_bytes}")
    lines.append("")
    lines.append("## File inventory")
    for rel, sz in files[:120]:
        lines.append(f"  {sz:>8}  {rel}")
    if len(files) > 120:
        lines.append(f"  ... and {len(files)-120} more files")
    lines.append("")

    ordered = sorted(files, key=lambda f: rank_key(f[0]))
    used = 0
    shown = []
    for rel, sz in ordered:
        if used >= BODY_BUDGET and os.path.basename(rel).lower() != "skill.md":
            break
        cap = SKILL_CAP if os.path.basename(rel).lower() == "skill.md" else FILE_CAP
        body = read(os.path.join(srcdir, rel), cap)
        used += len(body)
        shown.append(rel)
        lines.append(f"## FILE: {rel}")
        lines.append("```")
        lines.append(body)
        lines.append("```")
        lines.append("")
    omitted = [f[0] for f in files if f[0] not in shown]
    if omitted:
        lines.append(f"## Not shown ({len(omitted)} files, budget reached)")
        lines.append(", ".join(omitted[:60]))
    txt = "\n".join(lines)
    open(os.path.join(OUT, sid + ".md"), "w").write(txt)
    return {"id": sid, "name": name, "author": author, "source": source,
            "dir": srcdir, "n_files": len(files), "bytes": total_bytes,
            "dossier_chars": len(txt)}


manifest = []
seen = set()

# ---- portal skills ----
sk = json.load(open(f"{ROOT}/site/data/skills.json"))["skills"]
corpus = os.listdir(f"{ROOT}/corpus")
for s in sk:
    p = s["repo"].rstrip("/").split("github.com/")[-1]
    owner, repo = p.split("/")[:2]
    srcdir = None
    for cand in (f"{owner}_{repo}", repo):
        d = os.path.join(ROOT, "corpus", cand, s["path"])
        if os.path.isdir(d):
            srcdir = d
            break
    if not srcdir:
        print("UNRESOLVED", s["id"]); continue
    m = build(s["id"], s["name"], s.get("author", owner), s["repo"] + "/" + s["path"], srcdir)
    if m:
        m["set"] = "portal"
        manifest.append(m); seen.add(s["id"])

# ---- Xin's own skills ----
OWN = []
g = "/Users/xin/.claude/skills"
for d in sorted(os.listdir(g)):
    full = os.path.join(g, d)
    if os.path.islink(full) or not os.path.isdir(full):
        continue                     # gws-* are symlinks to auto-generated CLI skills
    if os.path.exists(os.path.join(full, "SKILL.md")):
        OWN.append((f"xin-{d}", d, full, "~/.claude/skills/" + d))

LIT = "/Users/xin/Stanford/Research/Hyperliquid/Hyperliquid paper/Literature Review/.claude/skills"
for d in sorted(os.listdir(LIT)):
    full = os.path.join(LIT, d)
    if os.path.isdir(full) and os.path.exists(os.path.join(full, "SKILL.md")):
        OWN.append((f"xin-{d}", d, full, "LiteratureReview/.claude/skills/" + d))

EA = "/Users/xin/Stanford/Research/Yzilabs/easy-agent/skills"
for grp in sorted(os.listdir(EA)):
    gp = os.path.join(EA, grp)
    if not os.path.isdir(gp):
        continue
    for d in sorted(os.listdir(gp)):
        full = os.path.join(gp, d)
        if os.path.isdir(full) and os.path.exists(os.path.join(full, "SKILL.md")):
            OWN.append((f"xin-{d}", d, full, f"easy-agent/skills/{grp}/{d}"))

SM = "/Users/xin/Stanford/Research/tools/slide-making-skill/slide-making"
if os.path.exists(os.path.join(SM, "SKILL.md")):
    OWN.append(("xin-slide-making", "slide-making", SM, "tools/slide-making-skill/slide-making"))

for sid, name, full, label in OWN:
    if sid in seen:
        sid = sid + "-2"
    m = build(sid, name, "Xin (applicant)", label, full)
    if m:
        m["set"] = "xin"
        manifest.append(m); seen.add(sid)

json.dump(manifest, open(os.path.join(OUT, "..", "manifest.json"), "w"), indent=1)
print("dossiers:", len(manifest),
      "portal:", sum(1 for m in manifest if m["set"] == "portal"),
      "xin:", sum(1 for m in manifest if m["set"] == "xin"))
print("total dossier chars:", sum(m["dossier_chars"] for m in manifest))
print("median chars:", sorted(m["dossier_chars"] for m in manifest)[len(manifest)//2])
