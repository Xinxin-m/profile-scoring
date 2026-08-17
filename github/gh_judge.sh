#!/bin/bash
# HOUSE JUDGE: codex gpt-5.6-terra at high reasoning effort (Xin's call, see
# judge/APPLICANT_RUBRIC.md). One codex run per GitHub account, each reading only that
# account's dossier so no profile is scored relative to whoever came before it.
SP="/private/tmp/claude-501/-Users-xin-Stanford-Research/90e0cf0d-748d-46a5-ae37-4d0f94f96b12/scratchpad"
RUBRIC="/Users/xin/Stanford/Research/Yzilabs/skill-pantheon/judge/GITHUB_CODER_RUBRIC.md"
mkdir -p "$SP/gh_out" "$SP/gh_log"

judge_one () {
  local login=$1
  local prompt="You are judging how good a coder a person is, from their entire public GitHub account, using the rubric below. Apply it exactly as written.

=== RUBRIC ===
$(cat "$RUBRIC")
=== END RUBRIC ===

The dossier for this account is at: $SP/gh/$login.dossier.md
READ IT COMPLETELY before scoring. It contains exact computed account facts, the full repo inventory, and for up to six selected repos: commit statistics, recent commit messages with diff sizes, file trees, READMEs, and the full text of real source files. The source files are the point: read them and judge the code.

Do not run anything and do not fetch anything from the network. Everything you need is in the dossier.

FIRST, before scoring anything, classify every deep-dive repo into one of the eight classes in Step 1 of the rubric and put that in repo_classes. The classification gates the scoring: coursework, tutorials, forks, templates and curation cannot raise complexity or domain depth, and they cap tag levels. A machine-learning class project is evidence of attending a class, not of machine-learning expertise. Apply that literally.

THEN score all six criteria, apply the vibe deduction, assign specialty tags with strictly-applied levels (respect every level cap in the rubric), set confidence, and set the exceptional flag with the specific metric that earned it.

Be hard to impress. This rubric was rewritten because its first version was too generous. Calibration: 85+ means a specialist in their field would already know this person's work; 70-84 a strong professional with real systems behind them; 50-69 a solid working engineer; 30-49 competent but thin, or a footprint dominated by coursework and one-shot apps; below 30 little demonstrated engineering. Most people are not in the top band. Do not round upward out of politeness.

Every item in \"evidence\" must name a specific repo, file path, commit, or number from the dossier. Generic praise is worthless here. At least one item in \"against\" must be a real limitation, never a compliment in disguise.

Return a single JSON object matching the required schema. No prose outside the JSON."

  echo "" | codex exec \
    -m gpt-5.6-terra \
    -c model_reasoning_effort=high \
    --sandbox read-only \
    --skip-git-repo-check \
    -C "$SP" \
    --output-schema "$SP/gh_schema.json" \
    -o "$SP/gh_out/$login.json" \
    "$prompt" > "$SP/gh_log/$login.log" 2>&1
  echo "done $login ($(wc -c < "$SP/gh_out/$login.json" 2>/dev/null || echo 0) bytes)"
}

for login in "$@"; do
  judge_one "$login" &
done
wait
echo "ALL PROFILES JUDGED"
