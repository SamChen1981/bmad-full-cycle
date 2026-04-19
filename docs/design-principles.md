# BMAD + Harness Engineering 设计原理

## 要解决什么问题

AI 编程助手（Cursor、Trae、Claude Code 等）在写单个函数时已经足够好，但面对一个完整的功能开发——从需求到代码到文档——会遇到三个根本问题：

**1. 没有记忆。** AI 每次对话是无状态的。你让它写完 PRD 后再让它做架构设计，它已经忘了 PRD 里写了什么。项目做到一半换一次对话窗口，上下文全部丢失。

**2. 没有纪律。** AI 会跳步。你让它做架构设计，它可能直接开始写代码。你让它按 Story 顺序开发，它可能挑自己觉得简单的先做。没有人盯着它确认"需求阶段真的做完了"再放它进入设计阶段。

**3. 做不长。** 一个功能如果有 15 个 Story，AI 做完第 3 个就会礼貌地停下来问"需要我继续吗？"。你说继续，做完第 5 个又停了。你得反复催它。

BMAD + Harness Engineering 就是为了系统性地解决这三个问题而设计的。

## 核心概念

### BMAD（Business Model-Aligned Development）

BMAD 是一套 AI 驱动的阶段式开发方法论。它把软件开发拆成严格的线性阶段，每个阶段有明确的输入、输出和质量关卡：

```
需求分析 → 架构设计 → API 契约 → Epic/Story 拆分 → 就绪检查 → Sprint 规划 → 自动编码 → 文档生成
```

关键词是"阶段"和"关卡"。每个阶段必须产出规定的文档或代码，通过关卡检查后才能进入下一个阶段。这不是建议，而是强制。

### Harness Engineering

Harness 是 BMAD 的运行时基础设施，负责三件事：

**状态持久化（State Persistence）**——把 AI 的"记忆"写到文件里。当前在哪个阶段、做了什么、产出了什么，全部序列化到 `bmad-state.json`。下次对话时从文件恢复，AI 不需要记住任何东西。

**关卡验证（Gatekeeper Validation）**——每次阶段切换前运行一个检查脚本。脚本会验证当前阶段的产出物是否存在、格式是否正确、代码是否能编译。只有全部通过，状态才允许前进。

**多代理路由（Agent Routing）**——不同阶段激活不同的 AI 角色。需求阶段用产品经理的提示词和工具集，编码阶段用开发工程师的，审查阶段用审查员的。每个角色有最适合自己任务的系统提示和技能组合。

## 架构设计

整个系统的架构分三层：

```
┌─────────────────────────────────────────────────────┐
│                    用户交互层                          │
│  用户在 AI IDE 的对话面板中输入自然语言指令              │
│  "我要做一个功能: 用户管理" / "暂停" / "继续开发"        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   编排层（Skills）                     │
│                                                     │
│  bmad-full-cycle ─── 端到端编排（8 个 Phase）          │
│       │                                             │
│       ├── Phase 1-6: 调用各规划 Skill                 │
│       │   (create-prd, create-architecture, ...)     │
│       │                                             │
│       └── Phase 7: bmad-autopilot ─── 开发循环编排    │
│               │                                     │
│               └── 循环调用:                           │
│                   create-story → dev-story →         │
│                   code-review → 更新状态 → 下一个     │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 Harness 基础设施层                     │
│                                                     │
│  bmad_harness.py ──── 状态控制器                      │
│       │                                             │
│       ├── bmad-state.json ──── 状态持久化             │
│       │   (当前阶段、时间戳、产出物清单、阻碍项)       │
│       │                                             │
│       ├── bmad-gatekeeper.sh ──── 关卡验证           │
│       │   (检查文件存在性、编译、测试)                 │
│       │                                             │
│       ├── bmad-harness-config.json ──── 配置         │
│       │   (阶段定义、Agent 映射、子项目信息)           │
│       │                                             │
│       └── sprint-status.yaml ──── Sprint 进度         │
│           (Story 状态: backlog → in-progress → done)  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 为什么分三层

**用户交互层**存在的意义是让用户不需要了解底层机制。用户不需要知道有 47 个 Skill、8 个 Phase、19 个 Story。他只需要说"我要做一个功能"和"暂停"。

**编排层**是"指挥官"。`bmad-full-cycle` 知道 8 个阶段的执行顺序和依赖关系，`bmad-autopilot` 知道 Story 的循环执行逻辑。它们调用下层的 Skill 来完成具体工作，但自己不写一行业务代码。

**Harness 基础设施层**是"基建"。它不关心你做的是用户管理还是 CRM，它只关心状态存了没有、关卡过了没有、下一个该激活哪个 Agent。

## 关键设计决策

### 1. 状态外置，不信任 AI 的记忆

AI 的上下文窗口是有限的，且每次新对话都从零开始。所以 BMAD 把所有状态写到文件系统：

```json
// bmad-state.json
{
  "project": "abeiya",
  "currentPhase": "implementation",
  "phases": {
    "design": {
      "status": "completed",
      "startedAt": "2026-04-19T21:19:26",
      "completedAt": "2026-04-19T21:42:01",
      "artifacts": [...]
    },
    "implementation": {
      "status": "in_progress",
      "startedAt": "2026-04-19T21:42:01",
      "artifacts": [
        {"path": "_bmad-output/planning-artifacts/epic-1-framework-upgrade.md"},
        {"path": "_bmad-output/implementation-artifacts/sprint-status.yaml"}
      ]
    }
  }
}
```

```yaml
# sprint-status.yaml
stories:
  - id: "1-1"
    title: "根 POM 版本升级"
    epic: "Epic 1: 框架升级"
    status: done
  - id: "1-2"
    title: "javax→jakarta 迁移"
    epic: "Epic 1: 框架升级"
    status: in-progress
  - id: "2-1"
    title: "通用模块升级"
    epic: "Epic 2: 共享模块"
    status: backlog
```

任何时候 AI 重新开始对话，只要读这两个文件，就能完全恢复上下文。这也是为什么"暂停"和"继续"能工作的原因——状态不在 AI 的脑子里，而在文件里。

### 2. 关卡即合同，不信任 AI 的判断

AI 说"架构设计完成了"不算数，Gatekeeper 说完成了才算数。Gatekeeper 是一个 Shell 脚本，做的是机械式检查：

```bash
case "${CURRENT}" in
    "design")
        # 架构文档存在？
        check_file_exists "docs/02_architecture_design.md" "架构设计文档"
        # 数据库设计存在？
        check_file_exists "docs/04_database_design.md" "数据库设计文档"
        # 至少一个子项目初始化了？
        for proj in ai-sales know-how-server zhixiao-cloud; do
            [ -f "${PROJECT_ROOT}/${proj}/pom.xml" ] && PROJ_INIT=1
        done
        ;;
    "implementation")
        # 代码目录有东西？
        check_dir_notempty "know-how-server/src" "源代码目录"
        # 能编译？
        cd know-how-server && mvn compile -q -DskipTests
        ;;
esac
```

这些检查看起来很朴素，但正是这种"不相信 AI 自己的判断"的设计哲学让流程变得可靠。AI 可以天马行空地说"我已经完成了设计"，但如果 `docs/02_architecture_design.md` 文件不存在，它就过不了关卡。

### 3. 自动驾驶覆盖规则（Override Rules）

这是整个设计中最反直觉但最关键的部分。

AI 有一个根深蒂固的"礼貌"倾向：它做完一件事后，本能地想停下来问你"需要我继续吗？"。在正常对话中这是好习惯，但在自动化流水线中这是灾难——19 个 Story 如果每个都停下来问一次，你就得确认 57 次（每个 Story 有创建、开发、审查三步）。

解决方案是在 Skill 的最顶部写一组优先级最高的覆盖规则：

```markdown
## ⚠️ 最高优先级：自动驾驶覆盖规则（OVERRIDE）

### 绝对禁止的行为
1. ❌ 禁止停下来问用户
2. ❌ 禁止在 Story 之间暂停
3. ❌ 禁止输出"下一步"清单
4. ❌ 禁止因为"已经做了很多工作"而停下来

### 必须执行的行为
5. ✅ 每个 Story 只输出一行进度
6. ✅ 唯一合法的停止条件：HALT 或用户说"暂停"

### 自检规则
在你输出每一段文字之前，检查：
- "我是否在问用户要不要继续？" → 删掉，直接执行
- "我是否在列出下一步建议？" → 删掉，直接执行
```

为什么要写得这么"粗暴"？因为 AI 的礼貌倾向非常顽固。如果你只是温和地说"请自动继续"，AI 做完 3-5 个 Story 后还是会停下来。必须用强制性的、带否定词的规则才能真正覆盖这个行为。

这组规则被标记为"高于所有被调用子 Skill 的指令"，确保即使子 Skill 有"完成后请用户确认"的内置逻辑，也会被覆盖。

### 4. HALT ≠ 暂停，两种停止语义

系统有两种停止机制，语义完全不同：

**HALT** 是系统发起的被迫停止。编译连续 3 次失败、代码审查严重问题 2 次修复不了、依赖冲突无法自动判断——这些是 AI 能力边界外的问题，需要人类介入。HALT 输出的是问题诊断：

```
🛑 HALT at Story [1-4]: Gateway 适配
   问题: spring-cloud-gateway 3.x 不兼容 WebMVC，需要 WebFlux
   已尝试: 切换到 spring-cloud-gateway-mvc starter（失败）
   需要: 确认是否将 gateway 模块改为 reactive 架构
```

**暂停** 是用户发起的主动停止。用户说"暂停"，系统在安全点停下来，输出的是进度报告：

```
⏸️ 开发已暂停
📊 Stories: 7/19 完成 | 当前: [2-3] Feign Client 改造
📋 已完成: [1-1] ~ [2-2]
📁 修改文件: zhixiao-cloud/pom.xml, zhixiao-common/src/...
▶️ 说"继续开发"恢复
```

两者的恢复方式也不同：HALT 需要用户解决问题后重试，暂停只需要说"继续"。

### 5. 配置与逻辑分离

Harness 的配置文件 `bmad-harness-config.json` 把"项目特定信息"和"流程逻辑"分离：

```json
{
  "subprojects": {
    "know-how-server": {
      "type": "backend",
      "tech": "Spring Boot 3.5 + Java 17"
    }
  },
  "phases": {
    "design": {
      "agent": "architect",
      "next": "implementation",
      "gatekeeper_checks": ["架构设计文档存在"]
    }
  },
  "agents": {
    "architect": {
      "role": "架构师",
      "system_prompt": "你是项目的架构师...",
      "trae_skills": ["bmad-agent-architect", "bmad-create-architecture"]
    }
  }
}
```

换一个项目时，只需要改配置文件里的子项目列表、技术栈和 Agent 提示词，流程逻辑（Controller、Gatekeeper）不用动。

### 6. Skill 分层编排

47 个 Skill 不是平级关系，而是分层的：

```
bmad-full-cycle          ← 顶层编排，串联 8 个 Phase
    │
    ├── bmad-create-prd         ← 原子 Skill，只做一件事
    ├── bmad-create-architecture
    ├── bmad-create-epics-and-stories
    ├── bmad-sprint-planning
    │
    └── bmad-autopilot          ← 中间层编排，循环调用下面三个
            │
            ├── bmad-create-story
            ├── bmad-dev-story
            └── bmad-code-review
```

这个分层让每个层次可以独立使用：想做完整流程用 `bmad-full-cycle`，已有需求只想编码用 `bmad-autopilot`，只想生成架构设计用 `bmad-create-architecture`。

### 7. IDE 无关的规范格式

BMAD Skill 的本质是一段 Markdown 格式的指令，告诉 AI 应该做什么。不同 IDE 加载这段指令的方式不同：

| IDE | 加载方式 | 文件格式 |
|-----|---------|---------|
| Trae | `.trae/skills/{name}/SKILL.md` | 目录 + Markdown |
| Cursor | `.cursor/rules/{name}.mdc` | frontmatter + Markdown |
| Windsurf | `.windsurf/rules/{name}.md` | Markdown |
| Claude Code | `.claude/commands/{name}.md` | 斜杠命令 |

但指令内容是通用的。`install.py` 做的就是格式转换——把同一份 Skill 内容适配到不同 IDE 的加载机制中。

## 实际执行流程（以迁移项目为例）

以 know-how-server（Spring Boot 3.5 单体）迁移到 zhixiao-cloud（Spring Cloud 微服务）为例，整个流程实际是这样运行的：

```
用户: "开始迁移"
  │
  ▼ bmad-migration-autopilot 激活
  │
  ├─ 读取 sprint-status.yaml → 找到第一个 backlog Story: [1-1]
  │
  ├─ Story [1-1]: 根 POM 版本升级
  │   ├─ create-story → 生成 Story 规格文件（输入、验收标准、技术约束）
  │   ├─ dev-story → 修改 pom.xml：Boot 2.7→3.5, Java 8→17, Cloud→2024
  │   ├─ code-review → 检查版本兼容性、依赖冲突
  │   ├─ 更新 sprint-status.yaml: [1-1] → done
  │   └─ 输出: ✅ [1-1] 根 POM 版本升级 (1/19)
  │
  ├─ 【自检：我是否想停下来？→ 不，继续】
  │
  ├─ Story [1-2]: javax→jakarta 迁移
  │   ├─ create-story → ...
  │   ├─ dev-story → 批量替换 javax.* → jakarta.*
  │   ├─ code-review → 检查是否有遗漏的 javax 引用
  │   ├─ 更新 sprint-status.yaml: [1-2] → done
  │   └─ 输出: ✅ [1-2] javax→jakarta 迁移 (2/19)
  │
  ├─ ... (19 个 Story 全部按同样的循环执行)
  │
  ├─ 文档生成（所有 Story 完成后自动触发）
  │   ├─ docs/architecture/ → 架构文档
  │   ├─ docs/api/openapi.yaml → API 规范
  │   ├─ docs/database/ → DDL 脚本 + 数据字典
  │   └─ docs/implementation/ → 实施文档
  │
  └─ 输出: 🎉 迁移完成 — 7 Epics / 19 Stories
```

中间如果用户说"暂停"：

```
用户: "暂停"
  │
  ▼ autopilot 在当前文件编辑完成后停止
  │
  └─ 输出暂停报告：
     ⏸️ 迁移已暂停
     📊 Stories: 7/19 完成 | 当前 Epic: Epic 3
     📁 修改文件: 15 个（列出清单）
     ▶️ 说"继续迁移"恢复
```

用户说"继续迁移"：

```
用户: "继续迁移"
  │
  ▼ autopilot 读取 sprint-status.yaml
  │
  ├─ 找到第一个非 done 的 Story: [3-2]
  └─ 从 [3-2] 继续循环
```

## 各组件的职责边界

| 组件 | 职责 | 不做什么 |
|------|------|---------|
| `bmad-full-cycle` | 串联 8 个 Phase 的顺序 | 不做任何具体的需求分析或编码 |
| `bmad-autopilot` | 循环执行 Story 的创建→开发→审查 | 不关心 Story 的内容是什么 |
| `bmad-create-story` | 根据 Epic 生成一个 Story 的详细规格 | 不写代码 |
| `bmad-dev-story` | 根据 Story 规格写代码 | 不做审查 |
| `bmad-code-review` | 审查代码质量并自动修复 | 不创建新功能 |
| `bmad_harness.py` | 管理阶段状态和转换 | 不知道项目业务逻辑 |
| `bmad-gatekeeper.sh` | 验证产出物是否存在 | 不判断产出物的质量 |
| `sprint-status.yaml` | 记录每个 Story 的状态 | 只是数据，没有逻辑 |
| `bmad-state.json` | 记录阶段级状态 | 只是数据，没有逻辑 |

## 设计原则总结

**1. 不信任 AI 的记忆，信任文件系统。** 所有状态持久化到文件，AI 是无状态的执行者。

**2. 不信任 AI 的自我评估，信任机械检查。** Gatekeeper 只做客观验证：文件存在吗？能编译吗？有测试吗？

**3. 不和 AI 的礼貌倾向做温和对抗，用强制覆盖。** Override 规则必须明确、重复、带否定词，放在 Skill 最顶部。

**4. 分层编排，单一职责。** 每个 Skill 只做一件事，编排逻辑和执行逻辑分离。

**5. 配置驱动，项目无关。** 换项目只改配置文件，不改流程代码。

**6. 两种停止语义。** HALT 是系统边界，暂停是用户控制。不混淆。

**7. IDE 无关的内容，IDE 相关的格式。** 指令内容是通用的 Markdown，安装脚本负责转换成各 IDE 的原生格式。
