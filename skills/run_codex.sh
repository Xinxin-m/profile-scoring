#!/bin/bash
# Judge every batch with codex gpt-5.6-terra at high reasoning effort.
# Concurrency 4 to stay clear of rate limits.
SP="/private/tmp/claude-501/-Users-xin-Stanford-Research/90e0cf0d-748d-46a5-ae37-4d0f94f96b12/scratchpad"
RUBRIC="/Users/xin/Stanford/Research/Yzilabs/skill-pantheon/judge/APPLICANT_RUBRIC.md"
mkdir -p "$SP/codex_out" "$SP/codex_log"

run_batch () {
  local b=$1
  local ids
  ids=$(python3 -c "
import json;print(chr(10).join('  - '+s['id']+'   (dossier: $SP/dossiers/'+s['id']+'.md)' for s in json.load(open('$SP/batches/$b.json'))))")
  local prompt="You are grading agent skills as EVIDENCE ABOUT THE PERSON WHO BUILT THEM, using the rubric below. Apply it exactly as written.

=== RUBRIC ===
$(cat "$RUBRIC")
=== END RUBRIC ===

Judge these ${#b} skills. Read EACH dossier file COMPLETELY before scoring it. Each dossier contains the skill's file inventory and the full text of its most important files.

$ids

Do not run any code. Read only.
Score every skill independently on all six criteria. Use the full range: most real skills land between 35 and 70, and a score above 85 should be rare. Do not cluster scores.

Return a single JSON object: {\"results\": [ ...one object per skill... ]} matching the required schema. No prose outside the JSON."

  echo "" | codex exec \
    -m gpt-5.6-terra \
    -c model_reasoning_effort=high \
    --sandbox read-only \
    --skip-git-repo-check \
    -C "$SP" \
    --output-schema "$SP/out_schema.json" \
    -o "$SP/codex_out/$b.json" \
    "$prompt" > "$SP/codex_log/$b.log" 2>&1
  echo "done $b ($(wc -c < "$SP/codex_out/$b.json" 2>/dev/null || echo 0) bytes)"
}

i=0
for b in b00 b01 b02 b03 b04 b05 b06 b07 b08 b09 b10 b11 b12 b13 b14 b15; do
  run_batch "$b" &
  i=$((i+1))
  if [ $((i % 4)) -eq 0 ]; then wait; fi
done
wait
echo "ALL CODEX BATCHES COMPLETE"
ls -la "$SP/codex_out"
