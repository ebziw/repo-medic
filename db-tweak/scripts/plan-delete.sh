#!/usr/bin/env bash
# plan-delete.sh — RENAME column/table to PLAN_DELETE_*, prevent accidental DROP
#
# Usage:
#   plan-delete.sh --table schema.old_table         # rename table
#   plan-delete.sh --column schema.table.old_column # rename column
#   plan-delete.sh --index schema.old_index          # rename index
#
# Flow: RENAME + write work-note reminder + schedule user review after 7 days
#
# v0.7.5 restored: from the kb db-doctor archive (db-doctor.merged-into-project-doctor.20260902)
# moved into project-doctor/scripts/db/ (location aligned with kb@kb merge); work-note path /
# backup hint generalized (override with WORKNOTE_DIR).

set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [--table schema.name | --column schema.table.column | --index schema.index]

RENAME the target to PLAN_DELETE_<orig_name>, and write a work-note reminder to request review after 7 days.

Examples:
  $0 --table crawler_urls.raw_urls        # RENAME raw_urls TO PLAN_DELETE_raw_urls
  $0 --column public.users.legacy_flag   # RENAME COLUMN legacy_flag TO PLAN_DELETE_legacy_flag
EOF
  exit 1
}

# Args
KIND=""
TARGET=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --table)   KIND=table;   TARGET="$2"; shift 2 ;;
    --column)  KIND=column;  TARGET="$2"; shift 2 ;;
    --index)   KIND=index;   TARGET="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $1"; usage ;;
  esac
done

[[ -z "$KIND" || -z "$TARGET" ]] && usage

# Parse schema.object (column: schema.table.column)
case "$KIND" in
  table)
    SCHEMA="${TARGET%.*}"; OBJ="${TARGET#*.}"
    PLAN_NAME="PLAN_DELETE_${OBJ}"
    SQL="ALTER TABLE ${SCHEMA}.${OBJ} RENAME TO ${PLAN_NAME};"
    ;;
  column)
    # schema.table.column -> schema.table + column
    PARTS=(${TARGET//./ })
    SCH="${PARTS[0]}.${PARTS[1]}"; COL="${PARTS[2]}"
    PLAN_NAME="PLAN_DELETE_${COL}"
    SQL="ALTER TABLE ${SCH} RENAME COLUMN ${COL} TO ${PLAN_NAME};"
    ;;
  index)
    SCHEMA="${TARGET%.*}"; IDX="${TARGET#*.}"
    PLAN_NAME="PLAN_DELETE_${IDX}"
    SQL="ALTER INDEX ${SCHEMA}.${IDX} RENAME TO ${PLAN_NAME};"
    ;;
esac

echo "=== plan-delete ==="
echo "kind:   $KIND"
echo "target: $TARGET"
echo "plan:   $PLAN_NAME"
echo "sql:    $SQL"
echo ""
read -p "Proceed? (y/N) " confirm && [[ "$confirm" =~ ^[Yy]$ ]] || { echo "aborted"; exit 1; }

# Lock wait + dual timeouts (iron rule 7)
set +e
psql -v ON_ERROR_STOP=1 <<EOF
SET lock_timeout = '2s';
SET idle_in_transaction_session_timeout = '30s';
$SQL
EOF
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  echo "✗ RENAME failed (rc=$RC), check whether lock_timeout is enough"
  exit $RC
fi

# Write work-note reminder
WORKNOTE_DIR="${WORKNOTE_DIR:-$HOME/.cache/project-doctor/pending-drops}"
AUDIT_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/audit-plan-delete.sh"
mkdir -p "$WORKNOTE_DIR"
TS=$(date -u +%Y%m%dT%H%M%SZ)
PROPOSE_DROP_DATE=$(date -u -d "+7 days" +%Y-%m-%d)
cat > "$WORKNOTE_DIR/${TS}-${PLAN_NAME}.md" <<EOF
---
kind: ${KIND}
target: ${TARGET}
plan_name: ${PLAN_NAME}
propose_drop_date: ${PROPOSE_DROP_DATE}
status: pending-review
---

# Pending DROP: ${PLAN_NAME}

RENAME time: ${TS}
Original object: ${TARGET}
Proposed DROP date: ${PROPOSE_DROP_DATE} (7 days from now)

## Flow
- [ ] day 1-7: full regression testing + watch application error logs
- [ ] day 7: request user review
- [ ] day 7+: user approves -> real DROP (iron rule 3: triple check + backup)

## Audit script
\`\`\`bash
bash ${AUDIT_SCRIPT}
\`\`\`
EOF

echo ""
echo "✓ RENAME done"
echo "✓ work-note reminder written: $WORKNOTE_DIR/${TS}-${PLAN_NAME}.md"
echo "✓ proposed DROP date: $PROPOSE_DROP_DATE"
echo ""
echo "Next steps:"
echo "  - monitor for 7 days (grep application logs for PLAN_DELETE_${OBJ})"
echo "  - day 7: run audit-plan-delete.sh + request user review"
echo "  - back up the DB before the real DROP (project-conventioned backup root, e.g. ~/backup/db/<date>) + triple-check FK/view/consumers"