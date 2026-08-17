#!/usr/bin/env python3
"""Render a collected GitHub account into a readable markdown dossier for the judge."""
import json, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
GH = f"{SP}/gh"


def render(login):
    d = json.load(open(f"{GH}/{login}.json"))
    if "error" in d:
        return f"# {login}\n\nERROR: {d['error']}\n"
    f, inv, deep = d["facts"], d["inventory"], d["deep"]
    L = []
    A = L.append
    A(f"# GITHUB DOSSIER: {login}")
    A("")
    A("## Account facts (computed, exact)")
    A(f"- name: {f.get('name')}   bio: {f.get('bio')}")
    A(f"- company: {f.get('company')}   location: {f.get('location')}   blog: {f.get('blog')}")
    A(f"- created: {f['created_at']}  (account age {f['account_age_years']} years)")
    A(f"- followers: {f['followers']}   following: {f['following']}")
    A(f"- repos: {f['original_repos']} original, {f['forked_repos']} forks")
    A(f"- stars across original repos: {f['total_stars']} total, {f['max_stars']} max, "
      f"{f['repos_with_10plus_stars']} repos with 10+ stars")
    A(f"- forks received: {f['total_forks']}")
    A(f"- languages by repo count: {f['languages_declared']}")
    A("")
    A("### Activity timeline (public commits attributed by GitHub)")
    A(f"- commits by year: {f['commits_by_year']}")
    A(f"- private contributions by year: {f['private_commits_by_year']}")
    A(f"- PRs opened by year: {f['prs_by_year']}")
    A(f"- total public commits: {f['commits_total_public']}")
    A(f"- commits before Copilot preview (Jun 2021): {f['commits_before_copilot']}")
    A(f"- commits through ChatGPT launch (Nov 2022): {f['commits_before_chatgpt']}")
    A(f"- years with 20+ commits: {f['active_years']}")
    A(f"- original repos created before Copilot: {f['repos_created_before_copilot']}; "
      f"before ChatGPT: {f['repos_created_before_chatgpt']}")
    A("")
    A("> Caveat: public commit counts miss commits made with an unlinked email, all private")
    A("> and employer repositories, and non-default branches. Treat a low number as weak")
    A("> evidence, not proof of inactivity.")
    A("")
    A(f"## Repo inventory (top {len(inv)} by stars)")
    A("```")
    A(f"{'stars':>6} {'forks':>6} {'sizeKB':>8}  {'lang':<14} {'created':<11} {'pushed':<11} "
      f"{'fork':<5} name")
    for r in inv:
        A(f"{r['stars']:>6} {r['forks']:>6} {r['size_kb']:>8}  {str(r['lang'])[:14]:<14} "
          f"{r['created']:<11} {r['pushed']:<11} {str(r['fork']):<5} {r['name']}"
          + (f"  :: {r['desc']}" if r['desc'] else ""))
    A("```")
    A("")
    A("## Deep dive")
    for r in deep:
        s = r["commit_stats"]
        A(f"### {login}/{r['name']}")
        A(f"selected because: **{r['selected_because']}**")
        A(f"- {r.get('desc') or '(no description)'}")
        A(f"- stars {r['stars']} | forks {r['forks']} | size {r['size_kb']}KB | "
          f"license {r.get('license')} | topics {r.get('topics')}")
        A(f"- created {r['created']} | last push {r['pushed']} | "
          f"first commit {str(s.get('first_commit'))[:10]} | lifespan {r['lifespan_days']} days")
        A(f"- commits {s.get('total_commits')} | releases {s.get('releases')} | "
          f"issues {s.get('issues')} | PRs {s.get('prs')}")
        A(f"- languages by bytes: {s.get('languages')}")
        A(f"- authored source files {r['n_source_files_authored']} of {r['n_blobs_total']} blobs "
          f"(vendored fraction {r['vendored_fraction']})"
          + ("  [tree truncated by API]" if r.get("tree_truncated") else ""))
        A(f"- tests {r['has_tests']} | CI {r['has_ci']} | typed {r['has_types']}")
        A(f"- top-level dirs: {r['top_dirs']}")
        if s.get("recent_commits"):
            A("- most recent commits (newest first), with diff size:")
            A("```")
            for c in s["recent_commits"]:
                A(f"  {c['date']}  +{c['+']:<7}-{c['-']:<7} {c['msg']}"
                  + (f"   [by {c['by']}]" if c.get("by") and c["by"] != login else ""))
            A("```")
        if r.get("readme"):
            A("<details><summary>README</summary>")
            A("```")
            A(r["readme"])
            A("```")
            A("</details>")
        A("")
        A(f"#### Source files from {r['name']}")
        for b in r["files"]:
            A(f"##### FILE: {b['path']}  ({b['size']} bytes)")
            A("```")
            A(b["content"])
            A("```")
        A("")
    return "\n".join(L)


if __name__ == "__main__":
    for login in sys.argv[1:]:
        t = render(login)
        open(f"{GH}/{login}.dossier.md", "w").write(t)
        print(f"{login}: {len(t)} chars -> {GH}/{login}.dossier.md")
