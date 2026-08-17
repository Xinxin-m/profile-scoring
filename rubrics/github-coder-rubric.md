# GitHub Coder Rubric v2 — judging a person from their whole account

**House judge: codex `gpt-5.6-terra` at high reasoning effort.**

The question is narrow and blunt: **how good a coder is this person?** Not how popular, not how
prolific, not how good the writing is. You are looking for evidence of engineering ability, for
evidence about how that ability was acquired, and for evidence that it is theirs.

**Be hard to impress.** v1 was too generous: it clustered four very different people into a
narrow band and handed out L5 for adoption rather than for engineering. The default posture is
skepticism. A repository is guilty of being unremarkable until its contents prove otherwise, and
the burden of proof sits on visible code, not on a star count or a README.

---

## Reading an account without reading everything

You get a dossier, not a checkout, assembled in widening layers so expensive attention goes only
where it can change a judgment:

| Layer | What it holds | What it settles |
|---|---|---|
| Account facts | age, followers, repo counts, stars, commits per year, pre-AI commit totals | proliferation, history length |
| Repo inventory | every repo with stars, size, language, created/pushed dates, fork flag | breadth, timeline, abandonment |
| Deep dive (up to 6 repos) | commit totals, first commit, recent commits with diff sizes, file tree, README, 9 real source files | quality, complexity, authorship |

The six deep-dive repos are a **mix**, each labelled `selected_because`: `most-starred` shows
what the world rewarded, `largest` shows the ambition ceiling, `oldest-substantial` is the pre-AI
evidence, `most-recent-substantial` shows current practice and is where generated work surfaces.

**Read the source files. That is the exercise.** Metadata tells you where to look; only code tells
you whether the person can write code.

### Facts that are computed, not judged

Exact in the dossier, do not re-derive: account age, commits per year, commits before Copilot
(Jun 2021) and ChatGPT (Nov 2022), repos created before each cutoff, total and max stars, forks
received, per-repo commit counts, first-commit date, lifespan in days, authored source files
against total blobs, vendored fraction, tests and CI presence.

### Three traps

1. **Public commit counts undercount.** They miss unlinked-email commits, all private and employer
   repos, and non-default branches. Low public commits is weak evidence, not proof. Say so.
2. **Repo size is not code size.** 45MB at `vendored_fraction: 0.99` is a committed build
   directory. That is a hygiene finding, not a volume-of-work finding.
3. **Stars measure distribution, not engineering.** A well-marketed list outstars a compiler.
   Weight forks, dependents and merged PRs into other people's repos far above raw stars.

---

## Step 1 (mandatory): classify every deep-dive repo

Before scoring anything, label each deep-dive repo with one class. This is the guard against
crediting expertise that was never demonstrated, and it is reported in your output.

| Class | What it means |
|---|---|
| `original-engineering` | A substantial system the person designed and built. |
| `original-small` | Original but small: a utility, a component, a single-purpose script done properly. |
| `coursework` | A class project, assignment, or homework repo, including capstones. |
| `tutorial-follow` | Built by following a tutorial, course, or published walkthrough. |
| `fork-derivative` | A fork, a clone, or someone else's project with modifications. |
| `template-scaffold` | Framework scaffolding with a thin custom layer on top. |
| `curation-docs` | Awesome-lists, guides, prompt collections, markdown. No engineering. |
| `generated-oneshot` | A complete artifact that appeared without a development process. |

**The hard rules that follow from the classification:**

- **Only `original-engineering` and `original-small` can raise complexity ceiling or domain depth.**
  A machine-learning class project demonstrates that the person attended the class. A fork of
  someone's model demonstrates that they can run `git clone`. Neither is expertise. Score them as
  the coursework and forks they are, and say so in the evidence.
- **`coursework` and `tutorial-follow` cap complexity at 9** no matter how sophisticated the
  subject matter looks. The difficulty belonged to whoever set the assignment.
- **`curation-docs` contributes nothing to any criterion except, at most, technical-education
  domain depth.** Stars on it do not count as engineering traction.
- **`fork-derivative` contributes only what the person visibly changed.** Read the diff evidence
  in the commit list. If their commits are configuration and README edits, it counts for nothing.
- If a repo's class is ambiguous, look for the tell: a README that names a course code or an
  instructor, an assignment spec, a submission deadline in the commit messages, a `data/` folder
  of provided inputs, or a first commit that already contains the finished project.

---

## 1. Code quality and engineering practice — max 25

From the source files, across repos. Judge the person's own code.

- **23-25** Code you would hire on the strength of, and would not need to review closely. Clear
  module boundaries; functions that do one thing; names that survive being read cold; errors
  handled at the boundary and never swallowed; tests that test behaviour, not implementation;
  types used to make illegal states unrepresentable; few, justified dependencies; comments that
  explain **why**.
- **18-22** Consistently professional with real soft spots: some long functions, thin coverage,
  occasional duplication, one or two leaky abstractions.
- **12-17** Maintainable but ordinary. Copy-paste that has diverged, shallow error handling,
  business logic tangled with I/O, few or no tests. This is where competent working code lands.
- **6-11** Fragile: hardcoded paths and secrets, silent catch-alls, 500-line files with mixed
  concerns, build artifacts committed, `any` everywhere, no structure that survives growth.
- **0-5** No readable original source, or code that cannot work as shipped.

Do not reward volume, polish of the UI, or a good README. Reward decisions.

## 2. Complexity ceiling — max 20

**The hardest thing they personally built**, counting only `original-engineering` and
`original-small`. v1 failed to separate anyone here, so the middle bands are now explicit about
what does *not* count.

- **18-20** Genuine invariants they had to maintain: a compiler or parser, a scheduler, a
  rendering or physics engine, distributed state or consensus, a storage engine, real
  concurrency, cryptographic implementation, a novel training or inference system, or measured
  performance work with a documented before and after.
- **14-17** Substantial multi-module systems of their own design: a real backend with data
  modelling, auth and migrations; a build tool or language server; an application with genuinely
  hard state; an integration layer handling failure, retries and consistency.
- **10-13** Competent applications assembled from known parts: CRUD on a framework, a dashboard,
  an API wrapper, a notebook that trains an off-the-shelf model on a provided dataset, an LLM
  wrapper with prompt plumbing. **A working product is not a hard problem.**
- **5-9** Single-purpose scripts, coursework, tutorial projects, template projects with the
  template still showing. **Hard cap for `coursework` and `tutorial-follow`.**
- **0-4** Configuration, notes, curation, or forks with a line changed.

Calibration: *where in this system would a strong engineer have had to stop and think, and what
would they have got wrong on the first attempt?* If you cannot name that place, it is 13 or below.

## 3. Activity and maintenance — max 15

Are they actually doing this, consistently, and do their projects survive their first push?

- **13-15** Sustained multi-year activity that is still current; projects receive follow-up commits
  months or years later; releases, versioning, issues handled, outside contributors managed.
- **9-12** Several genuinely active years, some projects maintained past their first week, and
  meaningful activity in the last twelve months.
- **5-8** Real but bursty: activity concentrated in a few windows, most repos pushed once and
  abandoned, or a solid history that has gone quiet.
- **2-4** One burst of activity, or a long-dormant account, or a recent flurry on an otherwise
  empty account.
- **0-1** No sustained record.

The clean tell for dumping rather than building: `lifespan_days` near zero beside a very large
first commit. A repo whose entire history is one commit was not developed on GitHub. That is
allowed, but it means the account cannot show you their process, and you must not credit process
you cannot see.

## 4. Pre-AI substance — max 15

Substantial original work before code generation was widely available. Cutoffs: Copilot preview
June 2021, ChatGPT November 2022. Nothing before those dates could have been generated, which
makes this the cleanest test that the ability is theirs.

- **13-15** Extensive substantial pre-2021 work: multi-year projects, real systems, sustained
  history in the hundreds or thousands of commits.
- **9-12** Solid pre-ChatGPT work: several real projects with genuine development history.
- **5-8** Some pre-cutoff activity, but small or coursework-shaped.
- **1-4** Almost nothing before the cutoffs.
- **0** No pre-cutoff footprint.

> **Fairness rule.** Nobody is penalized for having been too young or for joining GitHub late.
> Set `pre_ai_applicable: false` when the account postdates the cutoffs or the person was plainly
> a student then, and score instead on **substitute evidence of unassisted capability**:
> hand-written algorithmic work, visible debugging trails, low-level or performance-sensitive
> code, work in domains where current models are weak, or idiosyncrasies no model would emit.
> State which basis you used. Never let "young" silently become "vibe coder".

## 5. Traction — max 10

Cut from 15 in v1, where it was the widest-spread criterion and the one least about coding
ability. Reach is now mostly handled by the exceptional flag below; these ten points cover only
the engineering-relevant part of adoption.

- **9-10** Work with real dependents: widely forked tools, published packages in real use, merged
  contributions into significant third-party projects, repos where others ship code alongside them.
- **6-8** Meaningful adoption on at least one code project, with forks in proportion to stars.
- **3-5** Modest genuine interest, or good work that was simply never distributed.
- **1-2** Almost entirely self-contained.
- **0** No external signal.

Discount aggressively: stars on awesome-lists, tutorial repos, interview-prep collections, prompt
libraries, and anything whose value is curation. Followers are not traction. A fork count near
zero against many stars means people bookmarked it; a fork count that is a healthy fraction of
stars means people used it.

## 6. Domain depth — max 15

Raised from 10, and now the criterion that carries the user's real question: **does the body of
work justify a claim of expertise in a nameable area?**

- **13-15** Deep, coherent, demonstrated: repeated hard original work in one domain, with that
  domain's specific difficulties visibly handled in code a specialist would recognize.
- **9-12** Clear specialization with real competence across more than one original project.
- **5-8** A recognizable lean, but the work would not convince a specialist, or the depth rests on
  a single project.
- **2-4** Scattered, or breadth of shallow projects with no thread, or the domain evidence is
  coursework and forks.
- **0-1** No demonstrable domain.

**Coursework, tutorials and forks contribute nothing here.** Someone with four machine-learning
class repos and no original modelling work has demonstrated coursework completion, not machine
learning expertise. Say exactly that.

---

## Vibe-coded fraction — reported, and deducted 0 to -15

Estimate the share of the visible footprint that is a complete artifact with no development
process behind it. Report `vibe_coded_pct` with a reason.

**Tells:** an initial commit containing a complete working application (tens or hundreds of
thousands of lines); `lifespan_days` under about three with no return; build output and dependency
directories committed (`vendored_fraction` above ~0.9); a README whose feature list exceeds what
the code implements; framework scaffolding with a thin custom layer; no tests, no CI, no issues;
commit messages narrating features rather than describing changes, all in one uniform voice.

**Counter-evidence, which outweighs the tells:** incremental commits with bug fixes and reverts;
refactors; tests added alongside features; performance work; comments explaining a non-obvious
decision; idiosyncrasies no model would emit by default.

- **0 to -4** A minority of repos look generated; core work is clearly hand-built.
- **-5 to -9** Roughly half the footprint is one-shot artifacts.
- **-10 to -15** Essentially a portfolio of generated applications with no visible engineering
  process anywhere.

Using AI to write code is not the offence and must never be scored as one. The finding is the
**absence of engineering** around it: no iteration, no tests, no debugging, no judgment about what
belongs in a repository.

---

## Tags: specialty and level

Assign 1 to 3 specialty tags, each with a level. This is the headline output; the score is
supporting detail.

**Specialties:** `frontend`, `design-engineering`, `fullstack`, `backend`, `infra-devops`,
`systems-low-level`, `ml-research`, `ml-engineering`, `data-science`, `crypto-web3`, `security`,
`robotics`, `gaming-graphics`, `mobile`, `devtools`, `scientific-computing`,
`technical-education`, `insufficient-evidence`, and the vibe-coder family:

| Vibe-coder tag | What they generate |
|---|---|
| `vibe-coder-frontend` | Landing pages, marketing sites, UI-only apps with mock data |
| `vibe-coder-fullstack` | Apps with a real backend, auth and a database, assembled by prompt |
| `vibe-coder-ai-apps` | LLM wrappers, chatbots, agent demos |
| `vibe-coder-data` | Notebooks and analysis scripts generated end to end |
| `vibe-coder-tooling` | CLIs, scripts and automations produced in one shot |

`vibe-coder-*` is descriptive, not an insult, and carries its own level: an L3 vibe coder ships
more useful software than an L1 systems programmer. Use it **in addition to** a technical tag when
someone has both a real specialty and a generated-app habit.

### Levels, and be strict

| Level | Bar |
|---|---|
| **L1 dabbler** | Toy projects, tutorials, coursework, forks. Has touched the area. |
| **L2 hobbyist** | Builds things that work, small in scope, not production-shaped. No tests, no operations. |
| **L3 practitioner** | Production-grade original work. Employable at this today. Requires code someone else could maintain, and evidence it survived contact with users or with time. |
| **L4 senior** | Designs systems others build on. Requires **multi-year depth** plus a project with real external dependents or genuine architectural difficulty visible in the code. |
| **L5 recognized** | Field-visible: work a specialist in that domain would already know, through wide adoption of an engineering artifact or through genuine novelty. |

**Level caps, applied before anything else:**

- Coursework, tutorials and template projects cap the associated tag at **L2**.
- Forks and derivative work cap it at **L1**.
- A tag supported by exactly one project caps at **L3**, whatever its star count.
- `curation-docs` cannot support any tag above **L2**, and cannot support a technical tag at all.
  A widely starred prompt collection is a `technical-education` credential, not an engineering one.
- **L5 requires an engineering artifact, not a document.** If the adoption is on markdown, the
  person may still be L5 at `technical-education`, but their engineering tags are scored on code.
- Do not assign L4 or L5 to more than one tag unless each is independently justified in evidence.

## Insufficient evidence

When there is too little public code to judge (only forks, empty or config-only repos, fewer than
about three substantive original repos, or no readable source): set the tag to
`insufficient-evidence`, skip the level, set `confidence` to `low`, score honestly low, and
**state plainly that this is an absence of visible evidence, not a judgment of ability.** Most
working engineers keep their real work in private and employer repos. A thin public account is a
reason to ask for a code sample, not a verdict.

Report `confidence` on every profile: `high` (several repos of readable original source),
`medium` (limited but real source), `low` (little or nothing to read).

---

## The exceptional flag

Separate from the score, because reach and craft are different things and should not be blended.
Set `exceptional` and record **the specific metric that earned it**.

| Tier | Bar (must be met by a repo the person substantially authored) |
|---|---|
| `none` | Below the notable bar. |
| `notable` | 1,000+ stars on one repo, or 250+ forks on one repo, or 2,500+ stars across original repos. |
| `exceptional` | 10,000+ stars on one repo, or 1,000+ forks on one repo, or 25,000+ stars across original repos. |
| `landmark` | 50,000+ stars on one repo, or 5,000+ forks on one repo, or work that is infrastructure other projects depend on. |

**Qualifying rules, and apply them strictly:**

1. The repo must be **code**, not curation. A 30,000-star awesome-list, prompt collection or guide
   does **not** qualify at any tier. Record it separately as `reach_non_code` so the number is
   still visible without inflating the engineering claim.
2. The person must be a substantial author. If the dossier shows the implementation commits are
   mostly by others, downgrade one tier and say so.
3. Forks are the stronger signal. When stars and forks disagree, believe the forks.
4. Record every qualifying metric, not just the best one.

Output shape:

```json
"exceptional": {
  "tier": "none|notable|exceptional|landmark",
  "metrics": [
    {"metric": "stars_single_repo", "value": 12835, "repo": "sonner", "is_code": true},
    {"metric": "forks_total", "value": 2419, "repo": null, "is_code": true}
  ],
  "reach_non_code": [{"repo": "skills", "stars": 28728, "why": "markdown guidance, not engineering"}],
  "note": "One line on what the adoption actually demonstrates."
}
```

---

## Output

```json
{
  "login": "handle",
  "repo_classes": [{"repo": "name", "class": "original-engineering", "why": "one clause"}],
  "scores": {"quality": 0, "complexity": 0, "activity": 0, "pre_ai": 0, "traction": 0, "domain": 0},
  "vibe_deduction": 0,
  "total": 0,
  "vibe_coded_pct": 0,
  "pre_ai_applicable": true,
  "confidence": "high|medium|low",
  "tags": [{"specialty": "frontend", "level": "L3"}],
  "exceptional": {"tier": "none", "metrics": [], "reach_non_code": [], "note": ""},
  "headline": "One line: what kind of engineer this is.",
  "evidence": ["3 to 6 findings, each naming a repo, file, or number from the dossier"],
  "against": ["1 to 3 findings that cut the other way"],
  "ask_for": "What would raise or confirm the judgment."
}
```

`total` = sum of the six scores plus the (negative or zero) vibe deduction.
Maxima: quality 25, complexity 20, activity 15, pre_ai 15, traction 10, domain 15.
