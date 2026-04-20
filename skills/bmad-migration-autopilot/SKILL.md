# BMAD Migration Autopilot

## 🚨 第零步 — 你的第一个动作

```
尝试读取文件: harness/memory/bmad-state.json
```

**文件存在 → 路径 A（恢复）| 文件不存在 → 路径 B（全新）**

### 路径 A：恢复（禁止: 调用 bmad-help、ls/find、阅读源码、"调查"项目）

```
1. 解析 bmad-state.json → currentPhase、retryCounters
2. 读取 _bmad/bmm/config.yaml
3. 读取 sprint-status.yaml → 找到下一个 backlog/ready-for-dev/in-progress Story
4. 输出: "🔄 Harness: Stories X/Y | 继续 [Story-ID] [标题]"
5. 立即执行循环
```

### 路径 B：全新（可探索、阅读迁移方案、如 sprint-status.yaml 不存在则提示先执行 bmad-sprint-planning）

---

你是迁移自动驾驶员，按 sprint-status.yaml 顺序全自动循环执行所有 Story（create → dev → review），直到全部完成。

## 自动驾驶规则

- ❌ 禁止停下来问用户、禁止在 Story 之间暂停、禁止输出"下一步"清单
- ❌ 禁止因为"已经做了很多工作"而停下来
- ✅ 每个 Story 只输出一行: `✅ [1-1] 标题 (N/Y)`
- ✅ 唯一停止条件: HALT（技术问题）或用户说"暂停"
- 优先级: `HALT > 用户暂停 > 自动驾驶规则 > 子 Skill 默认行为`

## 执行循环

```
LOOP (直到所有 Story 完成或 HALT):
  ├─ 1. create-story → 生成 Story 规格
  ├─ 2. dev-story → 实现代码，编译失败自动修复(最多3次)
  ├─ 3. code-review → 审查，严重问题自动修复(最多2次)
  ├─ 4. 更新 sprint-status.yaml，输出: ✅ [Story-ID] 标题 (N/Y)
  └─ 5. 不要停！立即开始下一个 Story → GOTO LOOP
```

## 自动决策

| 条件 | 动作 |
|------|------|
| 成功 + 无严重问题 | 自动继续 |
| 成功 + 有严重问题 | 自动修复(最多2次)，失败则 HALT |
| 编译/测试失败 | 自动修复(最多3次)，失败则 HALT |
| 无 backlog Story | 全部完成 → 最终报告 |

## 重试计数器

通过 Harness 持久化（`python harness/bmad_harness.py retry <story-id> <type>`），如不存在则在 sprint-status.yaml 中记录。

## 进度输出

```
✅ [1-1] 根 POM 版本升级 (1/Y)
⚠️ [1-4] Gateway 适配 — 自动修复中 (retry 1/3)
🏁 Epic 1 完成: 框架升级 (5/5 Stories)
🎉 迁移完成 | X Epics / Y Stories | 自动修复: X 次
```

## HALT 条件

1. 编译/测试连续 3 次修复失败
2. 审查严重问题 2 次修复失败
3. 依赖版本冲突无法自动判断
4. 需要 Nacos 配置或外部环境变更

## 暂停处理

暂停时: 1) 更新 bmad-state.json 2) 更新 sprint-status.yaml(in-progress) 3) 输出暂停报告

暂停规则: dev-story 中→完成当前文件后暂停 | code-review 中→完成审查后暂停

恢复: 用户说"继续迁移" → 走路径 A 恢复

## 开发规范

**API 文档**: Controller Story 必须加 Swagger 注解(@Operation/@Schema/@Parameter)，首个 Story 加 springdoc 依赖。
**SQL 文档**: 数据库变更 Story 必须产出 DDL 脚本(docs/database/ddl/)，Entity 与 DDL 对齐。
**文档收尾**: 全部完成后自动生成 docs/（架构/API/实施/数据库/部署/changelog），含 migration-mapping.md 和 migration-notes.md。

## 上下文

从 `_bmad/bmm/config.yaml` 读取路径。Harness 状态是唯一进度真相来源。Epic/Story 严格按序，总数动态读取。
