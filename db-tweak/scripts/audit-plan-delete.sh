#!/usr/bin/env bash
# audit-plan-delete.sh — 列所有待审 PLAN_DELETE_*, 显示提议日期 + 距今多少天
#
# v0.7.5 恢复: 自 kb db-doctor 归档 (db-doctor.merged-into-project-doctor.20260902)
# 迁入 project-doctor/scripts/db/ (位置对齐 kb@kb merge), work-note 路径已泛化
# (与 plan-delete.sh 同默认, 可用 WORKNOTE_DIR 覆盖).

set -euo pipefail

WORKNOTE_DIR="${WORKNOTE_DIR:-$HOME/.cache/project-doctor/pending-drops}"

if [[ ! -d "$WORKNOTE_DIR" ]] || [[ -z "$(ls -A "$WORKNOTE_DIR" 2>/dev/null)" ]]; then
  echo "✓ 无 pending PLAN_DELETE_* 待审"
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
    echo "  ⏰ $TARGET — user 审通过后可真 DROP"
  fi
done

echo ""
echo "DROP 前必做 (铁律 3):"
echo "  1. FK 双向 (pg_constraint confrelid+conrelid)"
echo "  2. View 依赖 (pg_depend)"
echo "  3. 消费者 grep 代码 + 应用错误日志"
echo "  4. 备份 DB (项目约定备份根, 如 ~/backup/db/<date>)"