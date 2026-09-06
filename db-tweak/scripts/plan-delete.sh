#!/usr/bin/env bash
# plan-delete.sh — RENAME 字段/表为 PLAN_DELETE_*, 防误删
#
# Usage:
#   plan-delete.sh --table schema.old_table         # rename table
#   plan-delete.sh --column schema.table.old_column # rename column
#   plan-delete.sh --index schema.old_index          # rename index
#
# 流程: RENAME + 写 work-note 提醒 + 设 7 天后提请 user 审
#
# v0.7.5 恢复: 自 kb db-doctor 归档 (db-doctor.merged-into-project-doctor.20260902)
# 迁入 project-doctor/scripts/db/ (位置对齐 kb@kb merge), work-note 路径 / 备份提示已泛化
# (可用 WORKNOTE_DIR 覆盖).

set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [--table schema.name | --column schema.table.column | --index schema.index]

RENAME 目标为 PLAN_DELETE_<原名>, 记录 work-note 提醒 7 天后提请审。

示例:
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
    *) echo "未知参数: $1"; usage ;;
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
    # schema.table.column → schema.table column
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
read -p "确认执行? (y/N) " confirm && [[ "$confirm" =~ ^[Yy]$ ]] || { echo "aborted"; exit 1; }

# 锁查双时钟 (铁律 7)
set +e
psql -v ON_ERROR_STOP=1 <<EOF
SET lock_timeout = '2s';
SET idle_in_transaction_session_timeout = '30s';
$SQL
EOF
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  echo "✗ RENAME 失败 (rc=$RC), 检查 lock_timeout 是否够"
  exit $RC
fi

# 写 work-note 提醒
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

RENAME 时间: ${TS}
原对象: ${TARGET}
提议 DROP 日期: ${PROPOSE_DROP_DATE} (7 天后)

## 流程
- [ ] day 1-7: 完整回归测试 + 监控应用错误日志
- [ ] day 7: 提请 user 审
- [ ] day 7+: user 审通过 → 真 DROP (铁律 3 三核对 + 备份)

## 审计脚本
\`\`\`bash
bash ${AUDIT_SCRIPT}
\`\`\`
EOF

echo ""
echo "✓ RENAME 完成"
echo "✓ work-note 提醒写入: $WORKNOTE_DIR/${TS}-${PLAN_NAME}.md"
echo "✓ 提议 DROP 日期: $PROPOSE_DROP_DATE"
echo ""
echo "后续:"
echo "  - 监控 7 天 (应用日志找 PLAN_DELETE_${OBJ})"
echo "  - day 7 跑 audit-plan-delete.sh + 提请 user 审"
echo "  - 真 DROP 前备份 DB (项目约定备份根, 如 ~/backup/db/<date>) + 三核对 FK/view/消费者"