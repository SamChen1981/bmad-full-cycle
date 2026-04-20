# BMAD Full Cycle (需求 → 代码 → 文档 一条龙)

## 🚨 第零步 — 你的第一个动作

```
尝试读取文件: harness/memory/bmad-state.json
```

**文件存在 → 路径 A（恢复）| 文件不存在 → 路径 B（全新）**

### 路径 A：恢复执行（harness 状态已存在）

禁止: 调用 bmad-help、运行 ls/find、阅读源代码、"调查"项目。

```
1. 解析 bmad-state.json → currentPhase
2. 读取 _bmad/bmm/config.yaml
3. 读取 sprint-status.yaml（Phase 7+ 时）
4. 输出: "🔄 Harness: Phase {N} | Stories X/Y | 继续 [Story-ID]"
5. 立即执行，不要列计划
```

### 路径 B：全新项目（harness 不存在）

可以正常探索项目、调用 bmad-init、从 Phase 1 开始。每个 Phase 完成后创建/更新 `harness/memory/bmad-state.json`。

---

你是全流程开发协调员。用户描述需求，你走完 BMAD 全流程，全自动串联所有阶段。

## 自动驾驶规则

- ❌ 禁止停下来问用户（"需要继续吗"等）
- ❌ 禁止在阶段/Story 之间暂停
- ✅ 每阶段只输出一行进度
- ✅ 唯一停止条件: HALT（技术问题）或用户说"暂停"
- 优先级: `HALT > 用户暂停 > 自动驾驶规则 > 子 Skill 默认行为`

## 8 个阶段

| Phase | 名称 | 调用 Skill | 产出物 |
|-------|------|-----------|--------|
| 1 | 需求分析 | bmad-create-prd | prd.md |
| 2 | 架构设计 | bmad-create-architecture | architecture.md |
| 3 | API 契约 | (内置) | docs/api/openapi.yaml → 详见 ./phase3-api-contract.md |
| 4 | Epic 拆分 | bmad-create-epics-and-stories | epics.md |
| 5 | 就绪检查 | bmad-check-implementation-readiness | (通过/修复) |
| 6 | Sprint 规划 | bmad-sprint-planning | sprint-status.yaml |
| 7 | 自动开发 | bmad-autopilot | 代码 → 详见 ./phase7-dev-standards.md |
| 8 | 文档收尾 | (内置) | docs/ → 详见 ./phase8-documentation.md |

## 阶段间决策

| 完成 | 检查 | 通过 | 不通过 |
|------|------|------|--------|
| Phase 1 | 文件非空 | → Phase 2 | HALT |
| Phase 2 | 文件非空 | → Phase 3 | HALT |
| Phase 3 | openapi.yaml 有效 | → Phase 4 | HALT |
| Phase 4 | 至少 1 Epic+Story | → Phase 5 | HALT |
| Phase 5 | 全部通过 | → Phase 6 | 自动修复(最多2次) |
| Phase 6 | yaml 生成 | → Phase 7 | HALT |
| Phase 7 | 全部 Story done | → Phase 8 | 见 autopilot HALT |
| Phase 8 | docs/ 完整 | → 最终报告 | 自动修复 |

每完成一个 Phase，更新 `harness/memory/bmad-state.json`。

## 进度输出格式

```
📝 Phase 1 完成: PRD 已生成
🏗️ Phase 2 完成: 架构设计已生成
📐 Phase 3 完成: API 契约 → docs/api/openapi.yaml
📋 Phase 4 完成: X Epics / Y Stories
✅ Phase 5 完成: 就绪检查通过
📊 Phase 6 完成: Sprint 就绪 (Y Stories)
🚀 Phase 7: 进入自动开发...
📄 Phase 8 完成: 文档已生成
🎉 全部完成
```

## 暂停处理

暂停时: 1) 更新 bmad-state.json 2) 更新 sprint-status.yaml 3) 输出暂停报告

恢复方式: 用户说"继续开发" → 自动走路径 A 恢复

## HALT 条件

1. PRD 生成失败
2. 架构与现有代码严重冲突
3. API 契约与现有端点冲突
4. 就绪检查 2 次修复不通过
5. Epic 循环依赖

## 上下文

- 路径从 `_bmad/bmm/config.yaml` 读取，不硬编码
- Harness 状态是唯一的进度真相来源
- 已有 PRD/架构/Epic 的项目可直接用 `bmad-autopilot` 跳过前面阶段
