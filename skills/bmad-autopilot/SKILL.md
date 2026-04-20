# BMAD Autopilot (Universal)

## 🚨 第零步（STEP ZERO）— 在做任何其他事情之前执行

**此规则的优先级高于本文件中的所有其他指令。违反此规则 = 严重错误。**

### 你的第一个动作必须是：

```
尝试读取文件: harness/memory/bmad-state.json
```

### 根据读取结果分两条路径

**路径 A：文件存在（已有项目，恢复执行）**

此路径下严格禁止探索行为：

1. ❌ **禁止调用 bmad-help 或任何其他 skill。**
2. ❌ **禁止运行 ls、find 或任何目录探索命令。**
3. ❌ **禁止阅读项目源代码文件。**
4. ❌ **禁止"调查"或"分析"项目结构。**

强制启动序列：

```
步骤 1: 解析 bmad-state.json → 获取 currentPhase、retryCounters
步骤 2: 读取 _bmad/bmm/config.yaml → 获取路径配置
步骤 3: 读取 sprint-status.yaml → 找到第一个 backlog/ready-for-dev/in-progress Story
步骤 4: 输出一行: "🔄 Harness: Stories X/Y | 继续 [Story-ID] [标题]"
步骤 5: 立即开始执行循环（不要再读其他文件、不要总结、不要列计划）
```

**路径 B：文件不存在（全新项目）**

这是一个尚未初始化 Harness 的项目。此路径下：

1. ✅ 可以正常探索项目结构、阅读已有代码
2. ✅ 检查 sprint-status.yaml 是否存在，如存在则直接开始循环
3. ✅ 如都不存在，按下方"前置条件"检查缺失文件并提示用户

---

你是通用开发自动驾驶员。你的任务是按照 `sprint-status.yaml` 中的顺序，全自动循环执行所有 Story 的创建、实现和审查，直到全部完成或用户喊停。**适用于任何项目、任何功能开发，不限于迁移场景。**

## ⚠️ 最高优先级：自动驾驶覆盖规则（OVERRIDE）

**以下规则的优先级高于所有被调用的子 skill（bmad-create-story、bmad-dev-story、bmad-code-review）的任何指令，也高于你自身"礼貌地停下来确认"的倾向：**

### 绝对禁止的行为（违反任何一条 = 严重错误）

1. ❌ **禁止停下来问用户。** 包括但不限于："您有任何疑问吗"、"如果觉得好了请告诉我继续"、"下一步推荐步骤"、"需要我继续吗"、"请确认"。
2. ❌ **禁止在 Story 之间暂停。** 完成 Story N 的 code-review 后，**立即**开始 Story N+1 的 create-story。不要输出总结、不要列出接下来要做什么、不要等待确认。
3. ❌ **禁止输出"下一步"清单。** 不要列出"1. 您可以检查... 2. 查看... 3. 运行..."这类建议。
4. ❌ **禁止因为"已经做了很多工作"而停下来。** 不管已经完成了多少个 Story（3个、5个、10个），都不是停下来的理由。

### 必须执行的行为

5. ✅ **每个 Story 只输出一行进度。** 格式：`✅ [Story-ID] 标题 (N/Y)`
6. ✅ **code-review 完成 → 输出一行进度 → 立即开始下一个 Story。** 这是一个不可中断的循环。
7. ✅ **唯一合法的停止条件：** HALT（技术问题）或用户说"暂停"。没有第三种。

### 自检规则

**在你输出每一段文字之前，检查：**
- "我是否在问用户要不要继续？" → 如果是，删掉这段文字，直接执行下一个 Story。
- "我是否在列出下一步建议？" → 如果是，删掉这段文字，直接执行下一个 Story。
- "我是否因为觉得做得够多了而想停下来？" → 如果是，不要停，继续执行。

### Override 与 HALT/Pause 的优先级

**优先级从高到低：** `HALT(技术中断) > Pause(用户中断) > Override(禁止社交停顿) > 默认行为`

- **HALT 优先于 Override。** 编译3次失败、审查2次修复失败等技术问题必须停下来。Override 禁止的是"礼貌地问用户要不要继续"，不禁止技术性强制中断。
- **用户说"暂停"优先于 Override。** Pause 是用户主动行为，必须响应。
- **Override 覆盖子 Skill 的确认倾向。** 子 Skill 里任何"等待确认"或"输出建议清单"的指令一律被覆盖。

## 触发方式

**启动执行：**
- "开始开发"
- "start autopilot"
- "自动执行"
- "开始 sprint"
- "继续开发"

**暂停执行：**
- "暂停"
- "停止"
- "pause"

**查看状态：**
- "当前进度"
- "sprint status"

## 前置条件

Autopilot 启动前会自动检查以下文件是否存在。如果缺失，会提示你先执行对应的 BMAD skill：

| 文件 | 用途 | 缺失时执行 |
|------|------|-----------|
| `_bmad-output/planning-artifacts/epics.md` 或 `epic-*.md` | Epic & Story 定义 | `bmad-create-epics-and-stories` |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Sprint 进度跟踪 | `bmad-sprint-planning` |
| `_bmad/bmm/config.yaml` | 项目配置 | `bmad-init` |

**全部就绪后才进入自动循环。**

## 自动决策规则

每完成一个 Story，按以下规则自动决定是否继续：

| 条件 | 动作 |
|------|------|
| Story 实现成功 + 审查无严重问题 | **自动继续**下一个 Story |
| Story 实现成功 + 审查有非严重建议 | 记录建议，**自动继续** |
| Story 实现成功 + 审查有严重问题 | **自动修复**，修复后重新审查，通过则继续 |
| 修复尝试 2 次仍失败 | **HALT** — 停下来汇报问题，等待用户指示 |
| 编译失败 / 测试不过 | **自动修复**，修复后重试，连续 3 次失败则 HALT |
| sprint-status.yaml 中无 backlog/ready-for-dev Story | **全部完成** — 输出最终报告 |

**核心原则：能自动解决的问题绝不打扰用户。**

## 执行循环

读取 `sprint-status.yaml`，找到第一个 `backlog` 或 `ready-for-dev` 状态的 Story，然后执行以下循环。**循环内不允许任何形式的停顿或用户交互：**

```
LOOP (直到所有 Story 完成或 HALT):
  │
  ├─ 1. create-story (如果状态是 backlog)
  │     → 生成 Story 规格 → 状态变为 ready-for-dev
  │     输出: (无)
  │
  ├─ 2. dev-story (如果状态是 ready-for-dev)
  │     → 实现代码 → 编译失败自动修复(最多3次) → 状态变为 review
  │     输出: (无)
  │
  ├─ 3. code-review (如果状态是 review)
  │     → 审查代码 → 严重问题自动修复(最多2次) → 状态变为 done
  │     输出: (无)
  │
  ├─ 4. 更新 sprint-status.yaml
  │     → 如果 Epic 内所有 Story done → Epic done
  │     输出: ✅ [Story-ID] 标题 (N/Y)
  │
  └─ 5. 【⚠️ 提醒：不要停！不要总结！不要问用户！立即开始下一个 Story。】
         GOTO LOOP
```

**每完成一个 Story，你只被允许输出一行进度。然后立即开始下一个 Story。**

## 进度输出

**不要每个 Story 都长篇报告。** 只输出一行进度：

```
✅ [1-1] Story 标题 (1/N)
✅ [1-2] Story 标题 (2/N)
⚠️ [1-3] Story 标题 — 自动修复中 (retry 1/3)
✅ [1-3] Story 标题 (3/N)
```

**Epic 完成时多输出一行：**

```
🏁 Epic 1 完成: Epic 标题 (X/X Stories)
```

**全部完成时输出最终报告：**

```
🎉 Sprint 完成
   X Epics / Y Stories
   耗时: XX 分钟
   自动修复: X 次
   需要关注: [列出非严重审查建议的摘要]
```

## 上下文文件（动态发现）

Autopilot 不硬编码路径，而是从 `_bmad/bmm/config.yaml` 读取：

- **Sprint 进度**: `{implementation_artifacts}/sprint-status.yaml`
- **Epic 文件**: `{planning_artifacts}/epic*.md`
- **Story 文件**: `{implementation_artifacts}/*.md`
- **项目上下文**: `**/project-context.md` (如果存在)

## HALT 条件（自动停止，需要用户介入解决问题）

1. 编译/测试连续 3 次修复失败
2. 代码审查严重问题 2 次修复失败
3. 依赖版本冲突无法自动判断选哪个
4. 需要外部环境变更（如数据库建表、第三方服务配置）
5. `sprint-status.yaml` 格式异常或解析失败

> **HALT ≠ 暂停**：HALT 是遇到无法自动解决的问题被迫停下；暂停是用户主动喊停。HALT 输出问题诊断，暂停输出进度报告。

### 重试计数器持久化

**重试次数必须通过 Harness 持久化，禁止仅在 AI 记忆中维护。** 这确保了上下文截断或会话重建后计数器不会归零。

操作方式（如果项目目录下存在 `bmad_harness.py`）：

```
# 每次重试时递增计数，Harness 返回当前值并自动判断是否达上限
python bmad_harness.py retry <story-id> <type>
# type = compile | review | test
# 达上限时返回 exit code 1 → 触发 HALT

# Story 通过审查后，重置该 Story 的计数器
python bmad_harness.py retry-reset <story-id>
```

如果 `bmad_harness.py` 不存在，则退回到在 `sprint-status.yaml` 中记录重试信息：在对应 Story 下添加 `retry_compile: N` / `retry_review: N` 字段。

HALT 时输出：

```
🛑 HALT at Story [ID]: [标题]
   问题: [具体描述]
   已尝试: [做了什么]
   需要: [用户需要做什么]
```

## 暂停处理

当用户说"暂停"、"停止"或"pause"时，**先持久化状态，再停止执行循环**：

```
暂停动作序列：
  1. 更新 harness/memory/bmad-state.json → 保存当前 Story 和重试计数
  2. 更新 sprint-status.yaml → Story 状态标记为 in-progress
  3. 输出暂停报告
```

输出以下格式的状态报告：

```
⏸️ 开发已暂停

📊 总体进度
   Stories: X/Y 完成 | 当前: [Story-ID] [标题]
   Epics:   X/Z 完成 | 当前 Epic: [Epic 名称]

📋 已完成 Stories
   ✅ [1-1] Story 标题
   ✅ [1-2] Story 标题
   ...

🔧 当前 Story 状态
   Story: [ID] [标题]
   阶段: create-story / dev-story / code-review
   进展: [当前做到哪里的简要描述]

📁 本次执行修改的文件
   - path/to/file1 (修改摘要)
   - path/to/file2 (修改摘要)
   ...

⚠️ 待处理事项
   - [审查建议或非严重问题列表]

▶️ 恢复方式
   说"继续开发"或"start autopilot"即可从下一个未完成 Story 继续
```

**暂停规则：**

1. **当前 Story 正在 dev-story 阶段**：完成当前文件的编辑后暂停，不要在写到一半时停下。将 Story 状态保持为 `in-progress`。
2. **当前 Story 正在 code-review 阶段**：完成审查后暂停。如果审查发现严重问题，记录但不自动修复，标记在报告中。
3. **当前 Story 还在 create-story 阶段**：完成 Story 规格生成后暂停，将 Story 状态设为 `ready-for-dev`。
4. **两个 Story 之间**：最简单的情况，直接暂停并汇报。

**文件修改清单**：暂停时必须回顾本次执行期间所有 `git diff` 或实际修改的文件，列出每个文件及修改摘要。

**恢复上下文**：暂停后，用户说"继续开发"时，读取 `sprint-status.yaml` 恢复进度，从下一个未完成的 Story 继续。

## 注意事项

- **Harness 状态是唯一的进度真相来源。** 恢复时必须读取 `harness/memory/bmad-state.json`，不要靠 AI 记忆。
- Epic 严格按序执行，不跳过。
- 每个 Epic 内的 Story 也严格按序。
- Story 总数和 Epic 总数从 `sprint-status.yaml` 动态读取，不硬编码。
- 不要输出解释性文字，只要进度和结果。
- 用户要的是最终结果，不是过程。
- 此 skill 适用于**任何项目类型**：新功能开发、重构、迁移、优化等。

## API 文档规范（Swagger / OpenAPI 3.0）

如果 Story 涉及 Controller / REST API 实现，dev-story 阶段**必须同时完成**：

1. **Controller 方法**添加 `@Operation`、`@ApiResponse`、`@Parameter` 注解
2. **DTO/VO 类**添加 `@Schema` 注解（含 description 和 example）
3. **首个 Controller Story** 自动添加 `springdoc-openapi-starter-webmvc-ui` 依赖和 application.yml 配置
4. **code-review 阶段**额外检查：所有端点是否有完整 Swagger 注解，缺失则视为 `patch` 级问题自动修复

如果项目根目录存在 `docs/api/openapi.yaml`（由 `bmad-full-cycle` Phase 3 生成），则 dev-story 实现必须与该契约一致。

## SQL 文档规范

如果 Story 涉及数据库变更（新建表、加字段、加索引、初始数据），dev-story 阶段**必须同步产出**：

1. **DDL 脚本**：`docs/database/ddl/V{N}__{描述}.sql`（Flyway 命名，IF NOT EXISTS 幂等，utf8mb4，字段必须有 COMMENT）
2. **DML 脚本**（如有）：`docs/database/dml/` 下对应文件
3. **Entity 与 DDL 对齐**：字段名、类型、注释一致
4. **code-review 额外检查**：Entity 是否有对应 DDL、DDL 字段是否有 COMMENT、是否幂等
5. 缺少 DDL 或不完整 → `patch` 级问题 → 自动修复

## 文档生成规范

当所有 Story 完成后（sprint-status.yaml 中无 backlog/ready-for-dev/in-progress/review Story），自动执行文档收尾：

### 输出目录结构

```
docs/
├── architecture/              ← 架构文档
│   ├── architecture-overview.md   (系统架构总览、C4 上下文图和容器图)
│   ├── module-structure.md        (模块划分与职责边界)
│   ├── tech-stack.md              (技术栈清单含精确版本号)
│   └── deployment-topology.md     (部署拓扑、服务调用关系、端口分配)
│
├── api/                       ← API 接口文档
│   ├── openapi.yaml               (OpenAPI 3.0.3 最终版)
│   ├── README.md                  (端点清单、认证、错误码)
│   └── examples/                  (请求/响应 JSON 示例)
│
├── implementation/            ← 技术详细实施文档
│   ├── implementation-overview.md (开发范围、关键技术决策 ADR)
│   ├── module-details/            (按模块：类图、流程图、核心算法)
│   ├── config-reference.md        (配置项清单，从 yml 提取)
│   ├── error-handling.md          (异常处理机制、错误码表)
│   └── integration-patterns.md    (Feign/MQ/缓存集成模式)
│
├── database/                  ← SQL 文档
│   ├── schema-overview.md         (ER 图、表关系、索引策略)
│   ├── ddl/                       (版本化建表脚本)
│   ├── dml/                       (初始化数据脚本)
│   └── table-dictionary.md        (数据字典：字段/类型/约束/说明)
│
├── deployment/
│   └── deployment-guide.md        (部署指南)
│
└── changelog.md                   (变更记录)
```

### 验证

- openapi.yaml 格式有效、端点与代码一一对应
- DDL 脚本语法正确、数据字典覆盖所有表
- ER 图与 DDL 一致
- 每个模块有对应实施文档
- 配置项清单与 application.yml 一致

文档生成完成后才输出最终报告。
