#!/usr/bin/env python3
"""Build a judging dossier for a GitHub account.

Parsing strategy: never clone, never read a whole repo. Work in widening layers,
cheapest first, and spend the expensive budget only on repos that can actually answer
a question the rubric asks.

  L0 account facts           1 call
  L1 full repo inventory     ~1-3 calls   -> proliferation, breadth, timeline
  L2 contribution timeline   1 call/year  -> history length, pre-AI activity
  L3 deep dive on <=6 repos  ~10 calls ea -> code quality, complexity, authorship

Repo selection is deliberately a MIX, not a top-N by stars, because different repos
answer different questions: the starred ones show traction, the biggest non-forks show
the ambition ceiling, the oldest substantial one is the pre-AI evidence, and the newest
substantial one shows current practice (and is where vibe-coding shows up).
"""
import json, subprocess, sys, os, base64, re, datetime as dt

OUT = "/private/tmp/claude-501/-Users-xin-Stanford-Research/90e0cf0d-748d-46a5-ae37-4d0f94f96b12/scratchpad/gh"
os.makedirs(OUT, exist_ok=True)

MAX_REPOS = 6
MAX_FILES = 9
FILE_CAP = 4500
COPILOT = dt.date(2021, 6, 29)      # Copilot technical preview
CHATGPT = dt.date(2022, 11, 30)     # ChatGPT public launch

SRC = {".py": 3, ".js": 3, ".mjs": 3, ".ts": 3, ".tsx": 3, ".jsx": 3, ".go": 3, ".rs": 3,
       ".java": 3, ".c": 3, ".h": 2, ".cpp": 3, ".cc": 3, ".hpp": 2, ".cs": 3, ".rb": 3,
       ".php": 3, ".swift": 3, ".kt": 3, ".scala": 3, ".sol": 3, ".m": 2, ".mm": 2,
       ".lua": 2, ".r": 2, ".jl": 2, ".sh": 2, ".vue": 3, ".svelte": 3, ".css": 1,
       ".scss": 1, ".html": 1, ".glsl": 2, ".wgsl": 2, ".ipynb": 1, ".sql": 2, ".zig": 3}
JUNK = re.compile(
    r"(^|/)(node_modules|vendor|third_party|dist|build|out|\.next|target|bower_components|"
    r"__pycache__|\.venv|venv|site-packages|coverage|fixtures?|snapshots?|migrations|"
    r"generated|gen|assets|public/static)(/|$)|\.min\.|\.lock$|-lock\.json$|\.map$|\.d\.ts$")


def gh(*args, raw=False):
    try:
        r = subprocess.run(["gh"] + list(args), capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    return r.stdout if raw else (json.loads(r.stdout) if r.stdout.strip() else None)


def graphql(q, **vars):
    args = ["api", "graphql", "-f", f"query={q}"]
    for k, v in vars.items():
        args += ["-F" if isinstance(v, int) else "-f", f"{k}={v}"]
    return gh(*args)


def days(a, b):
    return (dt.datetime.fromisoformat(b.replace("Z", "+00:00"))
            - dt.datetime.fromisoformat(a.replace("Z", "+00:00"))).days


def d(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()


# ---------------------------------------------------------------- L0 + L1
def account(login):
    u = gh("api", f"users/{login}")
    if not u:
        return None, []
    repos = gh("api", f"users/{login}/repos?per_page=100&sort=pushed", "--paginate") or []
    return u, repos


# ---------------------------------------------------------------- L2
def timeline(login, created):
    """Commits per calendar year. One GraphQL call per year (the API caps a window at 1y)."""
    y0, y1 = d(created).year, dt.date.today().year
    q = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
      contributionsCollection(from:$from,to:$to){
        totalCommitContributions restrictedContributionsCount
        totalPullRequestContributions totalIssueContributions
        totalRepositoriesWithContributedCommits}}}"""
    out = {}
    for y in range(y0, y1 + 1):
        r = graphql(q, login=login, **{"from": f"{y}-01-01T00:00:00Z",
                                       "to": f"{y}-12-31T23:59:59Z"})
        c = (((r or {}).get("data") or {}).get("user") or {}).get("contributionsCollection")
        if not c:
            continue
        out[y] = {"commits": c["totalCommitContributions"],
                  "private": c["restrictedContributionsCount"],
                  "prs": c["totalPullRequestContributions"],
                  "issues": c["totalIssueContributions"],
                  "repos_touched": c["totalRepositoriesWithContributedCommits"]}
    return out


# ---------------------------------------------------------------- selection
def pick(repos):
    live = [r for r in repos if not r["fork"] and not r.get("archived_at")
            and r["size"] > 40 and not r["name"].lower().endswith(".github.io")]
    live = live or [r for r in repos if not r["fork"]]
    chosen, why = [], {}

    def add(r, reason):
        if r and r["name"] not in why and len(chosen) < MAX_REPOS:
            chosen.append(r); why[r["name"]] = reason
        elif r and r["name"] in why:
            why[r["name"]] += " + " + reason

    for r in sorted(live, key=lambda x: -x["stargazers_count"])[:3]:
        add(r, "most-starred")
    for r in sorted(live, key=lambda x: -x["size"])[:2]:
        add(r, "largest")
    old = sorted([r for r in live if r["size"] > 150], key=lambda x: x["created_at"])
    if old:
        add(old[0], "oldest-substantial")
    new = sorted([r for r in live if r["size"] > 150], key=lambda x: x["pushed_at"])
    if new:
        add(new[-1], "most-recent-substantial")
    return chosen, why


# ---------------------------------------------------------------- L3
def first_commit(owner, name):
    """Walk to the last page of the commit list; the Link header gives its number."""
    r = subprocess.run(["gh", "api", "--include", f"repos/{owner}/{name}/commits?per_page=1"],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None, None
    m = re.search(r'page=(\d+)>;\s*rel="last"', r.stdout)
    if not m:                                   # single page: the only commit is the first
        try:
            body = json.loads(r.stdout.split("\n\n", 1)[1] if "\n\n" in r.stdout else "[]")
            return (body[0]["commit"]["author"]["date"], len(body)) if body else (None, None)
        except Exception:
            return None, None
    last = int(m.group(1))
    tail = gh("api", f"repos/{owner}/{name}/commits?per_page=1&page={last}")
    return ((tail[0]["commit"]["author"]["date"], last) if isinstance(tail, list) and tail
            else (None, last))


def repo_commits(owner, name):
    q = """query($o:String!,$n:String!){repository(owner:$o,name:$n){
      defaultBranchRef{target{... on Commit{
        history{totalCount}
        recent:history(first:30){nodes{committedDate messageHeadline additions deletions
          author{user{login}}}}}}}
      releases{totalCount} issues{totalCount} pullRequests{totalCount}
      languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}"""
    r = graphql(q, o=owner, n=name)
    rp = (((r or {}).get("data") or {}).get("repository")) or {}
    tgt = ((rp.get("defaultBranchRef") or {}).get("target")) or {}
    hist = tgt.get("history") or {}
    recent = (tgt.get("recent") or {}).get("nodes") or []
    langs = {e["node"]["name"]: e["size"] for e in (rp.get("languages") or {}).get("edges", [])}
    first, npages = first_commit(owner, name)
    return {
        "total_commits": hist.get("totalCount") or npages,
        "first_commit": first,
        "releases": (rp.get("releases") or {}).get("totalCount"),
        "issues": (rp.get("issues") or {}).get("totalCount"),
        "prs": (rp.get("pullRequests") or {}).get("totalCount"),
        "languages": langs,
        "recent_commits": [{"date": c["committedDate"][:10], "msg": c["messageHeadline"][:110],
                            "+": c["additions"], "-": c["deletions"],
                            "by": ((c.get("author") or {}).get("user") or {}).get("login")}
                           for c in recent],
    }


def tree(owner, name, branch):
    t = gh("api", f"repos/{owner}/{name}/git/trees/{branch}?recursive=1")
    if not t:
        return [], False
    files = [(b["path"], b.get("size", 0)) for b in t.get("tree", []) if b["type"] == "blob"]
    return files, t.get("truncated", False)


def choose_files(files):
    cand = []
    for p, sz in files:
        if JUNK.search(p) or sz > 400_000 or sz < 120:
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext not in SRC:
            continue
        depth = p.count("/")
        w = SRC[ext] * 10
        if re.search(r"(^|/)(src|lib|app|core|packages|server|engine)/", p): w += 22
        if re.search(r"(^|/)(index|main|app|server|cli)\.[a-z]+$", p): w += 16
        if re.search(r"test|spec", p, re.I): w += 8          # tests are strong evidence
        if depth > 5: w -= 10
        w += min(sz / 1000, 28)                              # size, but saturating
        cand.append((w, p, sz))
    cand.sort(reverse=True)
    out, seen_dir = [], {}
    for w, p, sz in cand:                                    # spread across directories
        dd = p.rsplit("/", 1)[0] if "/" in p else "."
        if seen_dir.get(dd, 0) >= 3:
            continue
        seen_dir[dd] = seen_dir.get(dd, 0) + 1
        out.append((p, sz))
        if len(out) >= MAX_FILES:
            break
    return out


def get_file(owner, name, path):
    t = gh("api", f"repos/{owner}/{name}/contents/{path}",
           "-H", "Accept: application/vnd.github.raw", raw=True)
    if t is None:
        return None
    return t[:FILE_CAP] + (f"\n... [truncated, {len(t)} chars total]" if len(t) > FILE_CAP else "")


# ---------------------------------------------------------------- assemble
def build(login):
    u, repos = account(login)
    if not u:
        return {"login": login, "error": "account not found"}
    tl = timeline(login, u["created_at"])
    orig = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in orig)
    forks = sum(r["forks_count"] for r in orig)

    facts = {
        "login": login, "name": u.get("name"), "bio": u.get("bio"),
        "company": u.get("company"), "blog": u.get("blog"), "location": u.get("location"),
        "created_at": u["created_at"][:10],
        "account_age_years": round(days(u["created_at"], dt.datetime.utcnow().isoformat() + "Z") / 365.25, 1),
        "followers": u["followers"], "following": u["following"],
        "public_repos": u["public_repos"],
        "original_repos": len(orig), "forked_repos": len(repos) - len(orig),
        "total_stars": stars, "total_forks": forks,
        "max_stars": max([r["stargazers_count"] for r in orig], default=0),
        "repos_with_10plus_stars": sum(1 for r in orig if r["stargazers_count"] >= 10),
        "languages_declared": {},
        "commits_by_year": {y: v["commits"] for y, v in tl.items()},
        "private_commits_by_year": {y: v["private"] for y, v in tl.items()},
        "prs_by_year": {y: v["prs"] for y, v in tl.items()},
        "commits_before_copilot": sum(v["commits"] for y, v in tl.items() if y < COPILOT.year),
        "commits_before_chatgpt": sum(v["commits"] for y, v in tl.items() if y <= CHATGPT.year),
        "commits_total_public": sum(v["commits"] for v in tl.values()),
        "active_years": sum(1 for v in tl.values() if v["commits"] >= 20),
        "repos_created_before_copilot": sum(1 for r in orig if d(r["created_at"]) < COPILOT),
        "repos_created_before_chatgpt": sum(1 for r in orig if d(r["created_at"]) < CHATGPT),
    }
    lang = {}
    for r in orig:
        if r.get("language"):
            lang[r["language"]] = lang.get(r["language"], 0) + 1
    facts["languages_declared"] = dict(sorted(lang.items(), key=lambda kv: -kv[1])[:10])

    inventory = sorted(
        [{"name": r["name"], "stars": r["stargazers_count"], "forks": r["forks_count"],
          "lang": r.get("language"), "size_kb": r["size"], "fork": r["fork"],
          "created": r["created_at"][:10], "pushed": r["pushed_at"][:10],
          "archived": r.get("archived", False), "topics": r.get("topics", [])[:6],
          "desc": (r.get("description") or "")[:160]}
         for r in repos], key=lambda x: -x["stars"])

    chosen, why = pick(repos)
    deep = []
    for r in chosen:
        o, n = login, r["name"]
        st = repo_commits(o, n)
        files, trunc = tree(o, n, r["default_branch"])
        picked = choose_files(files)
        blobs = []
        for p, sz in picked:
            c = get_file(o, n, p)
            if c:
                blobs.append({"path": p, "size": sz, "content": c})
        rd = gh("api", f"repos/{o}/{n}/readme", "-H", "Accept: application/vnd.github.raw", raw=True)
        span = days(st["first_commit"], r["pushed_at"]) if st["first_commit"] else None
        real = [p for p, _ in files if not JUNK.search(p)
                and os.path.splitext(p)[1].lower() in SRC]
        deep.append({
            "name": n, "selected_because": why[n], "desc": r.get("description"),
            "stars": r["stargazers_count"], "forks": r["forks_count"],
            "size_kb": r["size"], "created": r["created_at"][:10], "pushed": r["pushed_at"][:10],
            "topics": r.get("topics", []), "license": (r.get("license") or {}).get("spdx_id"),
            "homepage": r.get("homepage"),
            "commit_stats": st,
            "lifespan_days": span,
            "n_blobs_total": len(files), "n_source_files_authored": len(real),
            "tree_truncated": trunc,
            "has_tests": any(re.search(r"test|spec", p, re.I) for p in real),
            "has_ci": any(p.startswith(".github/workflows/") for p, _ in files),
            "has_types": any(p.endswith((".ts", ".tsx", ".pyi")) for p in real),
            "vendored_fraction": round(1 - len(real) / max(len(files), 1), 2),
            "top_dirs": sorted({p.split("/")[0] for p in real if "/" in p})[:14],
            "readme": (rd or "")[:6000],
            "files": blobs,
        })
    return {"facts": facts, "inventory": inventory[:60], "deep": deep}


if __name__ == "__main__":
    for login in sys.argv[1:]:
        print(f"collecting {login} ...", flush=True)
        data = build(login)
        json.dump(data, open(f"{OUT}/{login}.json", "w"), indent=1)
        if "error" in data:
            print(f"  ERROR {data['error']}"); continue
        f = data["facts"]
        print(f"  age {f['account_age_years']}y  repos {f['original_repos']}orig/"
              f"{f['forked_repos']}fork  stars {f['total_stars']}  "
              f"commits {f['commits_total_public']} (pre-chatgpt {f['commits_before_chatgpt']})  "
              f"deep {len(data['deep'])}  json {os.path.getsize(f'{OUT}/{login}.json')//1024}KB")
