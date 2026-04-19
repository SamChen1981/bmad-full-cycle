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

Harness 是 BMAD 的运行时基础设施，负责五件事：

**状态持久化（State Persistence）**——把 AI 的"记忆"写到文件里。当前在哪个阶段、做了什么、产出了什么，全部序列化到 `bmad-state.json`。写入使用原子操作（tempfile + fcntl 排他锁 + os.replace），确保即使进程中断也不会损坏状态文件。每次写入前自动备份到 `.bak`，损坏时可自动恢复。

**关卡验证（Gatekeeper Validation）**——每次阶段切换前运行一个检查脚本。脚本会验证当前阶段的产出物是否存在、格式是否正确、代码是否能编译。只有全部通过，状态才允许前进。阶段跳转默认被阻断——如果当前阶段是 design，config 中 `next` 指向 implementation，那么直接跳到 testing 会被拒绝（除非使用 `--force`）。

**Git 集成（Git Integration）**——每次成功通过关卡后，控制器自动执行 `git add -A && git commit && git tag bmad/{phase}/{timestamp}`。回滚时先创建安全备份分支，再 `git reset --hard` 到目标 tag。这意味着每个阶段的成果都有可追溯的 git 快照，出问题可以精确回退。

**重试计数器（Retry Counters）**——持久化追踪每个 Story 的编译/测试/审查失败次数。当计数器达到阈值（compile/test = 3, review = 2），系统发出 HALT，要求人类介入。计数器包含完整的失败历史（时间、原因），用于事后诊断。

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
│       │   (当前阶段、时间戳、产出物、重试计数器)       │
│       │                                             │
│       ├── bmad-gatekeeper.sh ──── 关卡验证           │
│       │   (文件存在性、编译、测试、review 回归检查)    │
│       │                                             │
│       ├── bmad-harness-config.json ──── 配置         │
│       │   (阶段定义 + next 指针、Agent 映射、子项目)  │
│       │                                             │
│       ├── sprint-status.yaml ──── Sprint 进度         │
│       │   (Story 状态: backlog → in-progress → done)  │
│       │                                             │
│       └── Git 层 ──── 版本快照                        │
│           (每次转换: commit + tag bmad/{phase}/时间)   │
│           (回滚: safety branch + reset --hard)        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 为什么分三层

**用户交互层**存在的意义是让用户不需要了解底层机制。用户不需要知道有 47 个 Skill、8 个 Phase。他只需要说"我要做一个功能"和"暂停"。

**编排层**是"指挥官"。`bmad-full-cycle` 知道 8 个阶段的执行顺序和依赖关系，`bmad-autopilot` 知道 Story 的循环执行逻辑。它们调用下层的 Skill 来完成具体工作，但自己不写一行业务代码。

**Harness 基础设施层**是"基建"。它不关心你做的是用户管理还是 CRM，它只关心状态存了没有、关卡过了没有、下一个该激活哪个 Agent、git 打 tag 了没有。

## 关键设计决策

### 1. 状态外置，不信任 AI 的记忆

AI 的上下文窗口是有限的，且每次新对话都从零开始。所以 BMAD 把所有状态写到文件系统：

```json
// bmad-state.json
{
  "project": "my-project",
  "currentPhase": "implementation",
  "phases": {
    "design": {
      "status": "completed",
      "startedAt": "2026-04-19T21:19:26",
      "completedAt": "2026-04-19T21:42:01",
      "artifacts": [...],
      "sprintSummary": { ... },
      "sprintSyncedAt": "2026-04-19T21:42:01"
    },
    "implementation": {
      "status": "in_progress",
      "startedAt": "2026-04-19T21:42:01",
      "artifacts": [
        {"path": "_bmad-output/planning-artifacts/epic-1.md"},
        {"path": "_bmad-output/implementation-artifacts/sprint-status.yaml"}
      ],
      "blockers": []
    }
  },
  "retryCounters": {
    "1-4:compile": {
      "count": 2,
      "storyId": "1-4",
      "type": "compile",
      "lastRetryAt": "2026-04-19T22:15:00",
      "history": [
        {"attempt": 1, "reason": "spring-cloud-gateway 3.x incompatible with WebMVC", "at": "..."},
        {"attempt": 2, "reason": "gateway-mvc starter missing reactive dependency", "at": "..."}
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

状态的双向同步也很重要：sprint-status.yaml 是 Story 级的进度（由 autopilot 在编码循环中更新），bmad-state.json 是阶段级的进度（由 harness controller 更新）。`sync` 命令把前者的摘要写入后者，让两个视图保持一致。

### 2. 原子写入，不信任进程的稳定性

AI IDE 里的 AI 进程随时可能中断——用户关闭窗口、网络断开、token 耗尽。如果状态文件写到一半被中断，JSON 就会损坏，整个流程状态丢失。

解决方案是 `_atomic_write`：

```python
def _atomic_write(self, path, data):
    """原子写入：先写临时文件再 rename"""
    dir_path = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp', prefix='.bmad_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)    # 排他锁
            try:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())          # 强制刷盘
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp_path, path)            # 原子替换
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

三层保护：fcntl 排他锁防止并发写入、fsync 强制刷盘防止 OS 缓冲区丢数据、os.replace 做原子替换防止写入中断导致半写文件。临时文件和目标文件在同一目录（同一文件系统），保证 rename 是原子操作。

读取端使用 `fcntl.LOCK_SH`（共享锁），允许并发读取但阻止读写冲突。如果读取发现 JSON 损坏，自动从 `.bak` 恢复。

### 3. 关卡即合同，不信任 AI 的判断

AI 说"架构设计完成了"不算数，Gatekeeper 说完成了才算数。Gatekeeper 是一个 Shell 脚本，做的是机械式检查：

```bash
case "${CURRENT}" in
    "design")
        check_file_exists "docs/architecture_design.md" "架构设计文档"
        for proj in "${BACKEND_PROJECTS[@]}"; do
            [ -f "${PROJECT_ROOT}/${proj}/pom.xml" ] && PROJ_INIT=1
        done
        ;;
    "implementation")
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_dir_notempty "${proj}/src" "源代码目录"
            check_maven_compile "${proj}"
        done
        ;;
    "review")
        check_file_exists "_bmad-output/review-report.md" "代码审查报告"
        # 回归检查：审查可能引入修改，确认编译仍然通过
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_maven_compile "${proj}"
        done
        ;;
esac
```

这些检查看起来很朴素，但正是这种"不相信 AI 自己的判断"的设计哲学让流程变得可靠。AI 可以天马行空地说"我已经完成了设计"，但如果 `docs/architecture_design.md` 文件不存在，它就过不了关卡。

Gatekeeper 模板是通用的。项目特定的子项目列表（`BACKEND_PROJECTS`、`FRONTEND_PROJECTS`）和构建命令（Maven/Gradle/npm）由用户在 Shell 脚本顶部配置。review 阶段的回归检查确保审查修改没有引入新的编译错误。

### 4. 阶段跳转阻断

配置文件中每个阶段有一个 `next` 指针，定义了合法的阶段顺序：

```json
{
  "phases": {
    "requirements": { "next": "design" },
    "design": { "next": "implementation" },
    "implementation": { "next": "testing" },
    "testing": { "next": "review" },
    "review": { "next": null }
  }
}
```

如果当前阶段是 design，请求转换到 testing，控制器会拒绝：

```
[Harness] 非法跳转: 当前阶段 'design' 的下一阶段应为 'implementation'，但请求转换到 'testing'
   如需强制跳转，请使用: python bmad_harness.py transition testing --force
```

`--force` 参数存在是因为现实中确实有需要跳过阶段的场景（比如已有完整设计文档，想直接进入编码）。但默认行为是阻断，强制开发者有意识地做出跳过决策。

### 5. Git 集成——每个阶段一个快照

在关卡验证通过后、进入下一阶段前，控制器自动执行 git commit + tag：

```python
def transition_phase(self, next_phase_name, force=False):
    # ... 关卡验证通过后 ...
    
    # Git commit 当前阶段成果
    if current_phase:
        git_ok, git_info = self.git_commit_phase(current_phase)
    
    # 更新状态、初始化新阶段
    ...
```

Tag 命名规则是 `bmad/{phase}/{YYYYmmdd-HHMMSS}`，例如 `bmad/design/20260419-214201`。

回滚使用两步安全策略：先创建备份分支保存当前状态，再 reset 到目标 tag：

```python
def git_rollback_phase(self, phase_name=None):
    # 1. 创建安全分支
    safety_branch = f"bmad-rollback-backup/{timestamp}"
    self._run_git('branch', safety_branch)
    
    # 2. Reset 到目标 tag
    self._run_git('reset', '--hard', target_tag)
    
    # 3. 重新加载回滚后的 state 文件
    self.state = self._load_json(self.state_path)
```

这意味着即使回滚操作本身出了问题，原来的代码状态仍然保存在备份分支上。

### 6. 重试计数器——AI 的"耐心"是有限的

AI 在遇到编译错误时，会不断尝试修复。但有些错误（架构层面的不兼容、缺失的基础设施依赖）不是 AI 能解决的。让 AI 无限重试只会浪费 token 和时间。

重试计数器为每个 Story 和失败类型维护一个持久化计数：

```bash
# 编译失败一次
python bmad_harness.py retry 1-4 compile
# → [Harness] 重试计数 [1-4:compile] = 1

# 又失败了
python bmad_harness.py retry 1-4 compile
# → [Harness] 重试计数 [1-4:compile] = 2

# 第三次
python bmad_harness.py retry 1-4 compile
# → [Harness] HALT: [1-4:compile] 已达上限 3/3
# → exit code 1
```

阈值是可配置的，默认值基于经验：编译和测试允许 3 次（前两次可能是拼写错误或导入遗漏），代码审查允许 2 次（如果审查发现的问题两次修不好，通常意味着设计层面需要重新思考）。

### 7. 自动驾驶覆盖规则（Override Rules）

这是整个设计中最反直觉但最关键的部分。

AI 有一个根深蒂固的"礼貌"倾向：它做完一件事后，本能地想停下来问你"需要我继续吗？"。在正常对话中这是好习惯，但在自动化流水线中这是灾难——15 个 Story 如果每个都停下来问一次，你就得确认 45 次（每个 Story 有创建、开发、审查三步）。

解决方案是在 Skill 的最顶部写一组优先级最高的覆盖规则：

```markdown
## 最高优先级：自动驾驶覆盖规则（OVERRIDE）

### 绝对禁止的行为
1. 禁止停下来问用户
2. 禁止在 Story 之间暂停
3. 禁止输出"下一步"清单
4. 禁止因为"已经做了很多工作"而停下来

### 必须执行的行为
5. 每个 Story 只输出一行进度
6. 唯一合法的停止条件：HALT 或用户说"暂停"

### 自检规则
在你输出每一段文字之前，检查：
- "我是否在问用户要不要继续？" → 删掉，直接执行
- "我是否在列出下一步建议？" → 删掉，直接执行
```

为什么要写得这么"粗暴"？因为 AI 的礼貌倾向非常顽固。如果你只是温和地说"请自动继续"，AI 做完 3-5 个 Story 后还是会停下来。必须用强制性的、带否定词的规则才能真正覆盖这个行为。

### 8. 优先级链——四层停止语义

系统有一条明确的优先级链，控制什么时候应该停止、什么时候应该继续：

```
HALT > Pause > Override > sub-Skill default
```

**HALT** 是系统发起的被迫停止。编译连续 3 次失败、代码审查严重问题 2 次修复不了、依赖冲突无法自动判断——这些是 AI 能力边界外的问题，需要人类介入。HALT 输出的是问题诊断：

```
HALT at Story [1-4]: Gateway 适配
   问题: spring-cloud-gateway 3.x 不兼容 WebMVC，需要 WebFlux
   已尝试: 切换到 spring-cloud-gateway-mvc starter（失败）
   需要: 确认是否将 gateway 模块改为 reactive 架构
```

**Pause** 是用户发起的主动停止。用户说"暂停"，系统在安全点停下来，输出的是进度报告：

```
开发已暂停
Stories: 7/19 完成 | 当前: [2-3] Feign Client 改造
已完成: [1-1] ~ [2-2]
修改文件: zhixiao-cloud/pom.xml, zhixiao-common/src/...
说"继续开发"恢复
```

**Override** 是 Skill 顶部的覆盖规则，压制 AI 的停下来问用户的倾向。但 HALT 和 Pause 优先级更高——即使 Override 说"不要停"，HALT 仍然会停。

**sub-Skill default** 是子 Skill 的内置行为。比如 `bmad-code-review` 可能默认在审查完成后等待用户确认，但被上层 autopilot 的 Override 覆盖后会直接继续。

两者的恢复方式也不同：HALT 需要用户解决问题后重试，Pause 只需要说"继续"。

### 9. 配置与逻辑分离

Harness 的配置文件 `bmad-harness-config.json` 把"项目特定信息"和"流程逻辑"分离：

```json
{
  "project": "my-project",
  "subprojects": {
    "backend": {
      "type": "backend",
      "tech": "Spring Boot 3.5 + Java 17"
    },
    "frontend": {
      "type": "frontend",
      "tech": "Vue3 + TypeScript"
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

换一个项目时，只需要改配置文件里的子项目列表、技术栈和 Agent 提示词。流程逻辑（Controller 的 `transition_phase`、Gatekeeper 的检查框架）不用动。Gatekeeper 脚本顶部的 `BACKEND_PROJECTS` 和 `FRONTEND_PROJECTS` 数组也只需改一次。

### 10. Skill 分层编排

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

### 11. IDE 无关的规范格式

BMAD Skill 的本质是一段 Markdown 格式的指令，告诉 AI 应该做什么。不同 IDE 加载这段指令的方式不同：

| IDE | 加载方式 | 文件格式 |
|-----|---------|---------|
| Trae | `.trae/skills/{name}/SKILL.md` | 目录 + Markdown |
| Cursor | `.cursor/rules/{name}.mdc` | frontmatter + Markdown |
| Windsurf | `.windsurf/rules/{name}.md` | Markdown |
| Claude Code | `.claude/commands/{name}.md` | 斜杠命令 |

但指令内容是通用的。`install.py` 做的就是格式转换——把同一份 Skill 内容适配到不同 IDE 的加载机制中。安装时还会自动重写 supporting files 的路径引用，从绝对路径转换为相对于项目根目录的路径，并把 Trae 特有的 HTML 注释格式转换为显式 Markdown 引用。

`install.py` 支持完整的生命周期管理：首次安装、`--upgrade`（保留用户配置更新 Skill 内容）、`--uninstall`（清理所有 BMAD 文件但保留产出物）。

## 实际执行流程（以迁移项目为例）

以一个 Spring Boot 2.7 → 3.5 框架迁移为例，整个流程实际是这样运行的：

```
用户: "开始迁移"
  │
  ▼ bmad-migration-autopilot 激活
  │
  ├─ 读取 sprint-status.yaml → 找到第一个 backlog/ready-for-dev Story: [1-1]
  │
  ├─ Story [1-1]: 根 POM 版本升级
  │   ├─ create-story → 生成 Story 规格文件
  │   ├─ dev-story → 修改 pom.xml
  │   ├─ code-review → 检查版本兼容性
  │   ├─ 更新 sprint-status.yaml: [1-1] → done
  │   └─ 输出: [1-1] 根 POM 版本升级 (1/N)
  │
  ├─ 【自检：我是否想停下来？→ 不，Override 禁止，继续】
  │
  ├─ Story [1-2]: javax→jakarta 迁移
  │   ├─ create-story → ...
  │   ├─ dev-story → 批量替换 javax.* → jakarta.*
  │   ├─ code-review → 检查是否有遗漏的 javax 引用
  │   ├─ 更新 sprint-status.yaml: [1-2] → done
  │   └─ 输出: [1-2] javax→jakarta 迁移 (2/N)
  │
  ├─ ... (所有 Story 按同样的循环执行)
  │
  ├─ Story [1-4]: Gateway 适配（编译失败）
  │   ├─ dev-story → 尝试修改 gateway 配置
  │   ├─ 编译失败 → harness retry 1-4 compile → count=1
  │   ├─ 第二次尝试 → 编译失败 → count=2
  │   ├─ 第三次尝试 → 编译失败 → count=3 → HALT
  │   └─ 输出:
  │       HALT at Story [1-4]: Gateway 适配
  │       问题: spring-cloud-gateway 3.x 不兼容 WebMVC
  │       已尝试: 3 次编译修复均失败
  │       需要: 人工确认是否改为 reactive 架构
  │
  ├─ [用户解决问题后]
  │   ├─ harness retry-reset 1-4
  │   └─ 用户: "继续迁移"
  │
  ├─ ... (继续后续 Story)
  │
  ├─ 文档生成（所有 Story 完成后自动触发）
  │   ├─ docs/architecture/ → 架构文档
  │   ├─ docs/api/openapi.yaml → API 规范
  │   └─ docs/database/ → DDL + 数据字典
  │
  └─ 输出: 迁移完成 — N Epics / M Stories
```

中间如果用户说"暂停"：

```
用户: "暂停"
  │
  ▼ autopilot 在当前文件编辑完成后停止
  │
  └─ 输出暂停报告：
     迁移已暂停
     Stories: 7/N 完成 | 当前 Epic: Epic 3
     修改文件: 15 个
     说"继续迁移"恢复
```

用户说"继续迁移"：

```
用户: "继续迁移"
  │
  ▼ autopilot 读取 sprint-status.yaml
  │
  ├─ 找到第一个非 done 的 Story
  └─ 从该 Story 继续循环
```

## Harness 文件清单与职责边界

| 组件 | 文件 | 职责 | 不做什么 |
|------|------|------|---------|
| 状态控制器 | `bmad_harness.py` | 管理阶段状态、转换、git、重试计数 | 不知道项目业务逻辑 |
| 关卡脚本 | `bmad-gatekeeper.sh` | 验证产出物存在、编译通过、测试通过 | 不判断产出物的质量 |
| 配置文件 | `bmad-harness-config.json` | 定义阶段、Agent、子项目 | 不包含运行时状态 |
| 状态文件 | `memory/bmad-state.json` | 记录当前阶段、产出物、重试计数器 | 不包含配置信息 |
| Sprint 进度 | `sprint-status.yaml` | 记录每个 Story 的状态 | 由编排层更新，harness 只读 |

编排层组件：

| 组件 | 职责 | 不做什么 |
|------|------|---------|
| `bmad-full-cycle` | 串联 8 个 Phase 的顺序 | 不做任何具体的需求分析或编码 |
| `bmad-autopilot` | 循环执行 Story 的创建→开发→审查 | 不关心 Story 的内容是什么 |
| `bmad-create-story` | 根据 Epic 生成一个 Story 的详细规格 | 不写代码 |
| `bmad-dev-story` | 根据 Story 规格写代码 | 不做审查 |
| `bmad-code-review` | 审查代码质量并自动修复 | 不创建新功能 |

## 设计原则总结

**1. 不信任 AI 的记忆，信任文件系统。** 所有状态持久化到文件，AI 是无状态的执行者。sprint-status.yaml 和 bmad-state.json 双向同步，确保 Story 级和阶段级视图一致。

**2. 不信任进程的稳定性，用原子操作保护数据。** 所有状态写入使用 tempfile + fcntl 锁 + os.replace，损坏时自动从 .bak 恢复。

**3. 不信任 AI 的自我评估，信任机械检查。** Gatekeeper 只做客观验证：文件存在吗？能编译吗？有测试吗？review 后编译还通过吗？

**4. 不信任阶段顺序会被自觉遵守，用 next 指针强制。** 非法跳转默认阻断，--force 是有意识的覆盖。

**5. 不和 AI 的礼貌倾向做温和对抗，用强制覆盖。** Override 规则必须明确、重复、带否定词，放在 Skill 最顶部。

**6. 分层编排，单一职责。** 每个 Skill 只做一件事，编排逻辑和执行逻辑分离。

**7. 配置驱动，项目无关。** 换项目只改配置文件和 Gatekeeper 脚本头部，不改流程代码。

**8. 四层停止语义。** HALT > Pause > Override > sub-Skill default。不混淆。

**9. 每个阶段一个 git 快照。** 出问题可以精确回退到任意阶段的通过点，回滚前先备份。

**10. 有限容错，到点就停。** 重试计数器给 AI 有限的自修复机会（compile/test = 3, review = 2），超过就 HALT 让人类接手。

**11. IDE 无关的内容，IDE 相关的格式。** 指令内容是通用的 Markdown，install.py 负责转换成各 IDE 的原生格式，支持安装/升级/卸载全生命周期。
