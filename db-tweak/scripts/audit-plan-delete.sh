#!/usr/bin/env bash
# audit-plan-delete.sh — list all PLAN_DELETE_* pending review, showing the proposed date + days from now
#
# v0.7.5 restored: from the kb db-doctor archive (db-doctor.merged-into-project-doctor.20260902)
# moved into project-doctor/scripts/db/ (location aligned with kb@kb merge); work-note path generalized
# (same default as plan-delete.sh, override with WORKNOTE_DIR).

set -euo pipefail

WORKNOTE_DIR="${WORKNOTE_DIR:-$HOME/.cache/project-doctor/pending-drops}"

if [[ ! -d "$WORKNOTE_DIR" ]] || [[ -z "$(ls -A "$WORKNOTE_DIR" 2>/dev/null)" ]]; then
  echo "✓ no pending PLAN_DELETE_* awaiting review"
  exit 0
fi

echo "=== Pending PLAN_DELETE_* ==="
echo ""
printf "%-12s  %-40s  %-12s  %-10s\n" "PROPOSE_DATE" "TARGET" "DAYS_LEFT" "STATUS"
printf "%-12s  %-40s  %-12s  %-10s\n" "------------" "------" "---------" "------"

for f in "$WORKNOTE_DIR"/*.md; do
  [[ -f "$f" ]] || continue

  # Parse frontmatter (simple grep)
  KIND=$(grep -E "^kind:" "$f" | head -1 | awk '{print $2}')
  TARGET=$(grep -E "^target:" "$f" | head -1 | sed 's/^target: *//')
  PLAN_NAME=$(grep -E "^plan_name:" "$f" | head -1 | sed 's/^plan_name: *//')
  PROPOSE_DATE=$(grep -E "^propose_drop_date:" "$f" | head -1 | sed 's/^propose_drop_date: *//')
  STATUS=$(grep -E "^status:" "$f" | head -1 | awk '{print $2}')

  # Days left
  if [[ -n "$PROPOSE_DATE" ]]; then
    NOW=$(date -u +%s)
    PROPOSE_TS=$(date -u -d "$PROPOSE_DATE" +%s)
    DAYS_LEFT=$(( (PROPOSE_TS - NOW) / 86400 ))
  else
    DAYS_LEFT="-"
  fi

  printf "%-12s  %-40s  %-12s  %-10s\n" "$PROPOSE_DATE" "$TARGET" "${DAYS_LEFT}d" "$STATUS"
done

echo ""
echo "Total: $(ls "$WORKNOTE_DIR"/*.md 2>/dev/null | wc -l) pending"
echo ""
echo "Ready to DROP (DAYS_LEFT <= 0):"
for f in "$WORKNOTE_DIR"/*.md; do
  [[ -f "$f" ]] || continue
  PROPOSE_DATE=$(grep -E "^propose_drop_date:" "$f" | head -1 | sed 's/^propose_drop_date: *//')
  TARGET=$(grep -E "^target:" "$f" | head -1 | sed 's/^target: *//')
  [[ -z "$PROPOSE_DATE" ]] && continue
  NOW=$(date -u +%s)
  PROPOSE_TS=$(date -u -d "$PROPOSE_DATE" +%s)
  DAYS_LEFT=$(( (PROPOSE_TS - NOW) / 86400 ))
  if [[ $DAYS_LEFT -le 0 ]]; then
    echo "  ⏰ $TARGET — real DROP allowed after user approval"
  fi
done

echo ""
echo "Mandatory before DROP (iron rule 3):"
echo "  1. FK both directions (pg_constraint confrelid+conrelid)"
echo "  2. View dependencies (pg_depend)"
echo "  3. grep code for consumers + application error logs"
echo "  4. back up the DB (project-conventioned backup root, e.g. ~/backup/db/<date>)"