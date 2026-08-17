# profile-scoring

Two rubrics and two harnesses for judging technical people from artifacts they have already
produced, plus the calibration runs that shaped both.

| System | Input | Question it answers |
|---|---|---|
| [Agent skill scoring](rubrics/agent-skill-rubric.md) | 3 agent skills an applicant submits | How good is this person at building, judged through their own work? |
| [GitHub coder scoring](rubrics/github-coder-rubric.md) | A whole public GitHub account | How good a coder is this person, and what are they actually expert in? |

Both are designed around one conviction: **score what is in the files.** A claim with no
mechanism behind it earns zero, not partial credit, and a README is not evidence.

## House judge

**codex `gpt-5.6-terra` at high reasoning effort.** Chosen over Claude Opus after a
160-skill head-to-head where both models read byte-identical inputs. They ranked the field
almost identically (Spearman 0.898) but codex ran 4.5 points colder with a wider spread
(mean 50.8 / sd 18.3 against 55.3 / 16.2) and was markedly stingier about calling a
well-argued document an insight. Opus is kept as a disagreement detector, not a vote: where
the two differ by 15 points or more, a human looks.

A consequence worth internalising: **the ordering is a property of the rubric, the level is a
property of the model.** Never write an absolute threshold like "must score 65" into a
process. Rank against the pool.

---

## 1. Agent skill scoring

Six criteria over 100 points: code quality and web craft (25), problem difficulty (20),
ingenuity (20), product judgment (20), craft and handoff (15), plus an integrity adjustment
of 0 to -15 and a `web_evidence` coverage flag that is reported but never folded into the
score.

### Run it

```bash
python3 skills/build_dossiers.py          # one identical dossier per skill
./skills/run_codex.sh                     # judge every batch with the house judge
python3 skills/analyze.py                 # agreement, redundancy, discrimination
python3 skills/make_report.py             # results/skills/report.html
```

### What the calibration run found

160 skills (124 from a public corpus, 36 written by one person), two judges, identical inputs.
[Full report](results/skills/report.html), [raw scores](results/skills/merged.json).

- **Code quality and difficulty correlated at 0.91.** Judges were scoring one thing twice, so
  45 of 100 points collapsed into "does it ship code at all". v2 keeps both criteria but adds
  an explicit orthogonality instruction: difficulty is a property of the problem, quality is a
  property of the execution.
- **Product judgment used 13% of its range.** It carried 18 points, had the second-worst
  inter-judge agreement (0.684), and deleting it entirely left the ranking unchanged at rho
  0.996, because "has a clear purpose" was being read as strong. v2 makes 9-13 the explicit
  default band and reserves the top for a citable second pass.
- **Organization and completeness both hugged their means** and correlated with each other, so
  v2 merges them into one hygiene criterion capped at 15.
- **Ingenuity was the only criterion doing real work**: best inter-judge agreement (0.802) and
  healthy spread. It is also where the two models diverged most, so v2 adds worked examples and
  the rule that a method with no mechanism in a file caps at 7.
- **`claims_exceed_code` fired on 29 of 160 skills**, more than every other flag combined. It
  is now a scored integrity deduction rather than a note, and applicants are told about it in
  the submission prompt.
- **98 of 160 skills gave no evidence of web ability at all.** If people freely pick three
  favourites, a strong candidate can hand you three excellent artifacts that say nothing about
  the axis you care about most. Require at least one web-facing submission.

---

## 2. GitHub coder scoring

Six criteria over 100 points: code quality (25), complexity ceiling (20), activity and
maintenance (15), pre-AI substance (15), traction (10), domain depth (15), plus a vibe-coded
deduction of 0 to -15, specialty tags with levels, and a separate exceptional flag.

### Run it

```bash
python3 github/gh_collect.py <login> [<login> ...]   # layered API collection
python3 github/gh_render.py  <login> [<login> ...]   # readable dossier
./github/gh_judge.sh         <login> [<login> ...]   # house judge, one run per account
python3 github/gh_report.py                          # results/github/gh_report.html
```

Requires `gh` authenticated and `codex` on the path.

### How it reads an account without reading everything

Never clone, never read a whole repo. Four widening layers, so expensive attention is spent
only where it can change a judgment:

| Layer | Cost | Settles |
|---|---|---|
| Account facts | 1 call | age, followers, repo counts |
| Repo inventory | 1-3 calls | breadth, timeline, abandonment pattern |
| Contribution timeline | 1 call per year | history length, pre-AI activity |
| Deep dive on up to 6 repos | ~10 calls each | code quality, complexity, authorship |

The six deep-dive repos are chosen as a **mix, not a top-N by stars**, because different repos
answer different questions: `most-starred` shows what the world rewarded, `largest` shows the
ambition ceiling, `oldest-substantial` is the pre-AI evidence, `most-recent-substantial` shows
current practice and is where generated work surfaces. Within each repo, nine source files are
selected by a weighting that prefers `src/` and entry points, credits tests, spreads across
directories, and excludes vendored paths.

### The three ideas that make it work

**Classify before scoring.** Every deep-dive repo is labelled `original-engineering`,
`original-small`, `coursework`, `tutorial-follow`, `fork-derivative`, `template-scaffold`,
`curation-docs` or `generated-oneshot`. Only the two original classes can raise complexity or
domain depth. A machine-learning class project proves the person attended the class; a fork of
someone's model proves they can run `git clone`. Coursework caps complexity at 9 and caps its
tag at L2; forks cap at L1.

**Separate reach from craft.** Stars measure distribution, not engineering, and a well-marketed
list outstars a compiler. Traction is worth only 10 points, and adoption is reported instead
through an `exceptional` flag with tiers (`notable` / `exceptional` / `landmark`) that records
the specific metric that earned it. Curation repos are disqualified from the flag and logged
separately as `reach_non_code`, so a 30,000-star prompt collection stays visible without
becoming an engineering credential.

**Date the evidence.** Nothing committed before Copilot's preview (June 2021) or ChatGPT
(November 2022) could have been generated, which makes pre-cutoff work the cleanest test that
the ability is the person's own. A fairness rule prevents this from punishing youth: accounts
that postdate the cutoffs are scored on substitute evidence of unassisted capability instead,
and the basis used is stated in the output.

### Known limits

- Public commit counts miss unlinked-email commits, all private and employer repositories, and
  non-default branches. A thin public account is a reason to ask for a code sample, not a
  verdict, which is what the `insufficient-evidence` tag exists to say out loud.
- Repo size is not code size. A 45MB repository at `vendored_fraction: 0.99` is a committed
  build directory: a hygiene finding, not a volume-of-work finding.
- The `insufficient-evidence` path is written but was not exercised by the calibration set.

---

## A note on the results in this repo

`results/` contains scored judgments of real, named people, derived entirely from their public
repositories and public GitHub metadata. They are calibration artifacts: their purpose is to
show how the rubrics behave across very different kinds of engineer, not to publish verdicts
about individuals. Treat them accordingly if this repository ever changes visibility.
