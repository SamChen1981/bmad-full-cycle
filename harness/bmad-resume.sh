#!/bin/bash
# ============================================
# BMAD Resume — 读取 Harness 状态并生成恢复 prompt
#
# 使用方式:
#   bash harness/bmad-resume.sh              ← 输出恢复 prompt（复制到 Trae 聊天框）
#   bash harness/bmad-resume.sh --clipboard  ← 直接复制到剪贴板（macOS）
#   bash harness/bmad-resume.sh --skill      ← 输出带 /bmad-full-cycle 前缀
#
# 此脚本解决的问题:
#   Trae SOLO Coder 模型经常忽略 SKILL.md 中的 Harness 状态加载指令，
#   而是自行"调查"项目。此脚本将状态信息直接注入到用户 prompt 中，
#   让模型无法绕过。
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STATE_FILE="${SCRIPT_DIR}/memory/bmad-state.json"
CONFIG_FILE="${PROJECT_ROOT}/_bmad/bmm/config.yaml"

# ---- 参数解析 ----
CLIPBOARD=false
SKILL_PREFIX=""
for arg in "$@"; do
    case "$arg" in
        --clipboard|-c) CLIPBOARD=true ;;
        --skill|-s)     SKILL_PREFIX="/bmad-full-cycle " ;;
        --help|-h)
            echo "Usage: bash harness/bmad-resume.sh [--clipboard] [--skill]"
            echo "  --clipboard, -c   Copy prompt to clipboard (macOS)"
            echo "  --skill, -s       Add /bmad-full-cycle prefix"
            exit 0
            ;;
    esac
done

# ---- 检查状态文件 ----
if [ ! -f "$STATE_FILE" ]; then
    echo "⚠️  harness/memory/bmad-state.json 不存在"
    echo "   这是一个全新项目，直接使用: /bmad-full-cycle 我要做一个功能: [描述]"
    exit 0
fi

# ---- 解析 bmad-state.json ----
# 使用 python 解析 JSON（macOS 自带）
PHASE=$(python3 -c "
import json, sys
with open('${STATE_FILE}') as f:
    state = json.load(f)
print(state.get('currentPhase', 'null'))
" 2>/dev/null || echo "null")

PROJECT_NAME=$(python3 -c "
import json
with open('${STATE_FILE}') as f:
    state = json.load(f)
print(state.get('project', 'unknown'))
" 2>/dev/null || echo "unknown")

# ---- 解析 sprint-status.yaml ----
# 找到 sprint-status.yaml 的路径
SPRINT_FILE=""
for candidate in \
    "${PROJECT_ROOT}/_bmad-output/implementation-artifacts/sprint-status.yaml" \
    "${PROJECT_ROOT}/_bmad-output/sprint-status.yaml" \
    "${PROJECT_ROOT}/sprint-status.yaml"; do
    if [ -f "$candidate" ]; then
        SPRINT_FILE="$candidate"
        break
    fi
done

STORIES_DONE=0
STORIES_TOTAL=0
NEXT_STORY_ID=""
NEXT_STORY_NAME=""

if [ -n "$SPRINT_FILE" ]; then
    # 用 python 解析 YAML
    eval "$(python3 -c "
import sys
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

if not HAS_YAML:
    # Fallback: grep-based parsing
    import re
    done = 0
    total = 0
    next_id = ''
    next_name = ''
    with open('${SPRINT_FILE}') as f:
        lines = f.readlines()
    in_stories = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if 'stories:' in stripped:
            in_stories = True
            continue
        if in_stories and stripped.endswith(':') and not stripped.startswith('#') and not stripped.startswith('status'):
            # This is a story key
            story_key = stripped.rstrip(':').strip()
            total += 1
            # Check next line for status
            for j in range(i+1, min(i+5, len(lines))):
                if 'status:' in lines[j]:
                    status = lines[j].split('status:')[1].strip()
                    if status == 'done':
                        done += 1
                    elif not next_id and status in ('backlog', 'ready-for-dev', 'in-progress'):
                        next_id = story_key
                    break
        if stripped.startswith('epic-') and stripped.endswith(':'):
            in_stories = False
    print(f'STORIES_DONE={done}')
    print(f'STORIES_TOTAL={total}')
    print(f'NEXT_STORY_ID=\"{next_id}\"')
else:
    with open('${SPRINT_FILE}') as f:
        data = yaml.safe_load(f)
    dev = data.get('development_status', data)
    done = 0
    total = 0
    next_id = ''
    for epic_key, epic_val in dev.items():
        if not isinstance(epic_val, dict) or 'stories' not in epic_val:
            continue
        for story_key, story_val in epic_val['stories'].items():
            total += 1
            status = story_val.get('status', 'backlog') if isinstance(story_val, dict) else story_val
            if status == 'done':
                done += 1
            elif not next_id and status in ('backlog', 'ready-for-dev', 'in-progress'):
                next_id = story_key
    print(f'STORIES_DONE={done}')
    print(f'STORIES_TOTAL={total}')
    print(f'NEXT_STORY_ID=\"{next_id}\"')
" 2>/dev/null)" || true
fi

# ---- Phase 名称映射 ----
case "$PHASE" in
    requirements)     PHASE_NAME="Phase 1 需求分析" ;;
    design)           PHASE_NAME="Phase 2 架构设计" ;;
    api-contract)     PHASE_NAME="Phase 3 API 契约" ;;
    epic-breakdown)   PHASE_NAME="Phase 4 Epic 拆分" ;;
    readiness-check)  PHASE_NAME="Phase 5 就绪检查" ;;
    sprint-planning)  PHASE_NAME="Phase 6 Sprint 规划" ;;
    implementation)   PHASE_NAME="Phase 7 自动开发" ;;
    documentation)    PHASE_NAME="Phase 8 文档收尾" ;;
    null|"")          PHASE_NAME="未开始" ;;
    *)                PHASE_NAME="Phase: $PHASE" ;;
esac

# ---- 生成 prompt ----
PROMPT=""

if [ "$PHASE" = "null" ] || [ -z "$PHASE" ]; then
    PROMPT="${SKILL_PREFIX}这是一个全新项目，从 Phase 1 开始完整流程。

项目: ${PROJECT_NAME}
请从需求分析开始。"
else
    PROMPT="${SKILL_PREFIX}继续完成开发工作。以下是当前 Harness 状态，直接从此处恢复，不要重新调查项目。

【Harness 状态 — 不要忽略】
项目: ${PROJECT_NAME}
当前阶段: ${PHASE_NAME}
Stories 进度: ${STORIES_DONE}/${STORIES_TOTAL} 完成"

    if [ -n "$NEXT_STORY_ID" ]; then
        PROMPT="${PROMPT}
下一个 Story: ${NEXT_STORY_ID}"
    fi

    PROMPT="${PROMPT}

【指令】
1. 读取 harness/memory/bmad-state.json 确认以上状态
2. 读取 _bmad-output/implementation-artifacts/sprint-status.yaml 获取详细进度
3. 从 ${NEXT_STORY_ID:-当前位置} 直接开始执行
4. 不要调用 bmad-help，不要探索项目结构，不要列计划"
fi

# ---- 输出 ----
if $CLIPBOARD; then
    echo "$PROMPT" | pbcopy 2>/dev/null && echo "✅ 已复制到剪贴板！直接在 Trae 聊天框中粘贴即可。" || {
        echo "⚠️  pbcopy 不可用，请手动复制以下内容："
        echo ""
        echo "────────────────────────────"
        echo "$PROMPT"
        echo "────────────────────────────"
    }
else
    echo ""
    echo "────── 复制以下内容到 Trae 聊天框 ──────"
    echo ""
    echo "$PROMPT"
    echo ""
    echo "──────────────────────────────────────────"
    echo ""
    echo "💡 提示: 使用 --clipboard 参数可直接复制到剪贴板"
fi
