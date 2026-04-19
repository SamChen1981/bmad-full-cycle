# BMAD Full Cycle — 从需求到代码到文档的一键开发

## 这是什么

`bmad-full-cycle` 是一个 **Trae IDE** 的 AI skill，串联 BMAD 体系的所有阶段，让你只需描述一个功能需求，AI 就能全自动走完"需求分析 → 架构设计 → API 契约 → Epic/Story 拆分 → 就绪检查 → Sprint 规划 → 自动开发 → 文档生成"的完整流程。

核心理念：**你负责说要什么，AI 负责做完**。中间不需要任何确认或干预，除非遇到技术问题。

## 前提条件

- **Trae IDE**（字节跳动出品的 AI 编程 IDE）已安装并可正常使用
- 项目已在 Trae 中打开（File → Open Folder）
- Trae 的 AI 对话面板可用（右侧 Chat 面板，或按 `Cmd+L` / `Ctrl+L` 打开）

## 快速开始

### 1. 安装 Skills

BMAD skills 以目录形式存放在项目根目录的 `.trae/skills/` 下。Trae 启动时会自动扫描并加载这些 skill。

**安装方法：在终端中执行（Trae 内置终端：菜单 Terminal → New Terminal，或快捷键 `` Ctrl+` ``）：**

```bash
# 进入你的项目根目录
cd /path/to/your-project

# 创建 skills 目录（如果不存在）
mkdir -p .trae/skills

# 方式 A: 从已有项目复制全部 BMAD skills
cp -r /path/to/source-project/.trae/skills/bmad-* .trae/skills/

# 方式 B: 如果你只有本仓库，先把 SKILL.md 放进去
mkdir -p .trae/skills/bmad-full-cycle
cp SKILL.md .trae/skills/bmad-full-cycle/
```

> **注意**：`bmad-full-cycle` 依赖其他 BMAD skills（见下方依赖表）。如果只安装了 `bmad-full-cycle` 而缺少依赖 skill，对应阶段会无法执行。建议用**方式 A** 一次性复制全部 `bmad-*` skills。

**依赖的 BMAD skills：**

| Skill | 用途 | 对应阶段 |
|-------|------|---------|
| `bmad-init` | 项目配置初始化 | 首次使用 |
| `bmad-create-prd` | 生成需求文档（PRD） | Phase 1 |
| `bmad-create-architecture` | 生成架构设计 | Phase 2 |
| `bmad-create-epics-and-stories` | Epic/Story 拆分 | Phase 4 |
| `bmad-check-implementation-readiness` | 就绪检查 | Phase 5 |
| `bmad-sprint-planning` | Sprint 规划 | Phase 6 |
| `bmad-autopilot` | 自动开发循环 | Phase 7 |
| `bmad-create-story` | 生成 Story 规格 | Phase 7 内部 |
| `bmad-dev-story` | 实现代码 | Phase 7 内部 |
| `bmad-code-review` | 代码审查 | Phase 7 内部 |

安装完成后，重启 Trae 或重新打开项目，skill 会自动被识别。

### 2. 项目初始化（仅首次）

如果项目还没有 `_bmad/` 目录（首次使用 BMAD），需要先初始化项目配置。

**操作方式：在 Trae 右侧 AI 对话面板中输入：**

```
初始化 bmad 项目
```

Trae 的 AI 会识别 `bmad-init` skill 并执行，自动在项目根目录创建 `_bmad/bmm/config.yaml` 等配置文件。初始化过程中 AI 可能会问你几个项目相关的问题（技术栈、模块划分等），按提示回答即可。

**初始化完成后的目录结构：**

```
your-project/
├── _bmad/
│   └── bmm/
│       └── config.yaml    ← 项目配置（技术栈、路径、模块信息）
├── .trae/
│   └── skills/
│       ├── bmad-full-cycle/
│       │   └── SKILL.md
│       ├── bmad-autopilot/
│       │   └── SKILL.md
│       └── ... (其他 bmad-* skills)
└── (你的项目源代码)
```

### 3. 一键启动全流程

**操作方式：在 Trae 右侧 AI 对话面板中，直接用自然语言描述你要开发的功能：**

```
我要做一个功能: 用户管理模块，支持注册登录、角色权限、组织架构
```

或者：

```
full cycle: 实现商品目录系统，包含分类管理、SKU 管理、库存查询
```

或者：

```
新功能: 客户 CRM 模块，含客户档案、跟进记录、销售漏斗
```

Trae 的 AI 会识别 `bmad-full-cycle` skill 并自动开始执行 8 个阶段。你会在对话面板中看到逐行的进度输出，无需任何操作，等待完成即可。

## 8 个阶段

| 阶段 | 做什么 | 产出文件 |
|------|--------|---------|
| Phase 1 | 需求分析 → 生成 PRD | `_bmad-output/planning-artifacts/prd.md` |
| Phase 2 | 架构设计 | `_bmad-output/planning-artifacts/architecture.md` |
| Phase 3 | API 契约设计（OpenAPI 3.0） | `docs/api/openapi.yaml` |
| Phase 4 | Epic & Story 拆分 | `_bmad-output/planning-artifacts/epics.md` |
| Phase 5 | 实现就绪检查 | 通过/自动修复 |
| Phase 6 | Sprint 规划 | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Phase 7 | 自动开发（循环执行所有 Story） | 源代码 + DDL/DML + Swagger 注解 |
| Phase 8 | 文档生成 & 收尾 | `docs/` 完整技术文档 |

## 运行中的控制

所有控制命令都在 **Trae 右侧 AI 对话面板**中输入。

### 暂停

在 AI 正在执行的过程中，直接在对话框输入：

```
暂停
```

AI 会在当前操作的安全点停下来，并输出一份详细的进度报告，包括：已完成的 Story 列表、当前进展、修改的文件清单、待处理事项。

### 恢复

暂停后，在对话框输入以下任意一种：

```
继续开发
```

```
start autopilot
```

AI 会读取 `sprint-status.yaml` 恢复进度，从上次中断处继续执行。

### 交互模式

如果你想在每个阶段完成后手动确认再继续（比如想先检查 PRD 是否符合预期），在对话框输入：

```
full cycle 交互模式: 用户管理模块
```

交互模式下，每个阶段完成后 AI 会暂停等你确认，你说"继续"后才进入下一阶段。

## 在其他项目中使用

### 方式一：复制全部 skills（推荐）

在 **终端**（Trae 内置终端或系统终端均可）中执行：

```bash
# 把全部 BMAD skills 从已有项目复制到新项目
cp -r /path/to/existing-project/.trae/skills/bmad-* /path/to/new-project/.trae/skills/
```

然后用 Trae 打开新项目，在 **AI 对话面板**中输入 `初始化 bmad 项目` 完成初始化。

### 方式二：只复制编排层

如果新项目已经通过 `bmad-init` 安装了 `_bmad/` 基础设施（包含大部分 skill），只需额外复制编排层 skill：

```bash
# 只复制 full-cycle 和 autopilot
cp -r /path/to/source/.trae/skills/bmad-full-cycle /path/to/new-project/.trae/skills/
cp -r /path/to/source/.trae/skills/bmad-autopilot /path/to/new-project/.trae/skills/
```

### 适配非 Java 项目

`bmad-full-cycle` 默认包含 Java/Spring 相关规范（Swagger 注解、DDL 脚本等）。如果你的项目是其他技术栈：

1. 用 Trae 打开 `.trae/skills/bmad-full-cycle/SKILL.md`
2. 修改或注释掉 "Phase 7: Swagger 强制规范" 和 "SQL 文档规范" 章节
3. 替换为你的技术栈对应的规范

## 产出物清单

全流程完成后，项目中会新增以下文件结构：

```
your-project/
├── docs/
│   ├── architecture/      ← 架构文档（系统总览、模块划分、技术栈、部署拓扑）
│   ├── api/               ← API 文档（OpenAPI 规范、端点清单、示例）
│   ├── implementation/    ← 实施文档（开发范围、模块详细设计、配置项、异常处理）
│   ├── database/          ← 数据库文档（ER 图、DDL/DML 脚本、数据字典）
│   ├── deployment/        ← 部署指南
│   └── changelog.md       ← 变更记录
│
├── _bmad-output/
│   ├── planning-artifacts/       ← PRD、架构设计、Epic/Story 定义
│   └── implementation-artifacts/ ← Sprint 状态、Story 规格文件
│
└── (新增/修改的源代码文件)
```

## 与 bmad-autopilot 的关系

`bmad-full-cycle` 是端到端的编排器，内部在 Phase 7 调用 `bmad-autopilot` 执行开发循环。

| 场景 | 在 Trae AI 对话中输入 | 使用的 Skill |
|------|---------------------|-------------|
| 从零开始开发新功能 | `我要做一个功能: [描述]` | `bmad-full-cycle` |
| 已有 PRD/架构/Epic，只需自动编码 | `开始开发` | `bmad-autopilot` |
| 迁移项目（有专门的迁移计划） | `开始迁移` | `bmad-migration-autopilot` |

## 常见问题

**Q: 如果中途发现 PRD 不对怎么办？**
在 Trae AI 对话面板输入 `暂停`，然后在 Trae 编辑器中手动修改 `_bmad-output/planning-artifacts/prd.md`，改好后在对话面板输入 `继续开发`。

**Q: 可以只执行其中某几个阶段吗？**
可以。在 Trae AI 对话面板中直接调用单独的 skill，例如输入 `生成架构设计` 会触发 `bmad-create-architecture`。

**Q: Phase 7 执行太慢？**
每个 Story 包含"创建规格 → 编码 → 审查"三步，复杂 Story 可能需要几分钟。可以在 Epic/Story 拆分阶段将 Story 拆得更细来加速。

**Q: 文档生成的格式可以定制吗？**
可以。用 Trae 编辑器打开 `.trae/skills/bmad-full-cycle/SKILL.md`，修改 Phase 8 的文档目录结构和内容要求即可。
