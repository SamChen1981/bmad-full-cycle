# BMAD Full Cycle

从需求到代码到文档的一键 AI 全自动开发。

在 AI IDE（Trae / Cursor / Windsurf）中输入一句功能描述，自动走完"需求分析 → 架构设计 → API 契约 → Epic/Story 拆分 → 就绪检查 → Sprint 规划 → 自动编码 → 文档生成"完整流程。你负责说要什么，AI 负责做完。

## 安装

### 前置要求

- Python 3.6+
- AI IDE（目前以 [Trae](https://trae.ai) 为例，也支持 Cursor、Windsurf）

### 一键安装

**在终端中执行：**

```bash
# 1. 克隆仓库
git clone https://gitee.com/chnj1981/bmad-full-cycle.git

# 2. 安装全部 skills 到你的项目（以 Trae 为例）
python bmad-full-cycle/install.py /path/to/your-project
```

安装完成后你会看到：

```
────────────────────────────────────────────────────────
  安装 BMAD Skills → Trae
────────────────────────────────────────────────────────

  → 目标项目: /path/to/your-project
  → Skills 目录: /path/to/your-project/.trae/skills
  → 待安装: 47 个 skills

  ✓ bmad-init
  ✓ bmad-create-prd
  ✓ bmad-autopilot
  ✓ bmad-full-cycle
  ... (共 47 个)

  完成！
  → 新安装: 47
```

脚本会自动完成以下操作：

1. 将 47 个 BMAD skills 复制到 `{你的项目}/.trae/skills/` 目录
2. 创建 `_bmad/bmm/config.yaml` 基础配置文件
3. 创建 `_bmad-output/` 输出目录结构

### 安装选项

```bash
# 安装到 Cursor 项目
python install.py /path/to/project --ide cursor

# 安装到 Windsurf 项目
python install.py /path/to/project --ide windsurf

# 交互式选择要安装的 skill 分组（不需要全部安装时）
python install.py /path/to/project --select

# 只安装 skills，不创建 _bmad 配置
python install.py /path/to/project --no-init

# 列出所有可用 skills（不安装）
python install.py /path/to/project --list
```

### 安装后的目录结构

```
your-project/
├── .trae/skills/              ← 47 个 BMAD skills（Trae 自动加载）
│   ├── bmad-full-cycle/       ← 全流程编排
│   ├── bmad-autopilot/        ← 自动开发循环
│   ├── bmad-create-prd/       ← PRD 生成
│   ├── bmad-init/             ← 项目初始化
│   └── ... (共 47 个)
├── _bmad/bmm/config.yaml      ← BMAD 项目配置
└── _bmad-output/               ← 产出物存放目录
    ├── planning-artifacts/
    └── implementation-artifacts/
```

## 使用

所有操作都在 **IDE 的 AI 对话面板**中以自然语言输入。

### 从零开发一个新功能（全流程）

打开 Trae → 右侧 AI 对话面板（`Cmd+L` / `Ctrl+L`）→ 输入：

```
我要做一个功能: 用户管理模块，支持注册登录、角色权限、组织架构
```

AI 会自动执行 8 个阶段，你会看到逐行进度输出：

```
📝 Phase 1 完成: PRD 已生成
🏗️ Phase 2 完成: 架构设计已生成
📐 Phase 3 完成: API 契约已生成 → docs/api/openapi.yaml
📋 Phase 4 完成: 3 Epics / 12 Stories 已拆分
✅ Phase 5 完成: 实现就绪检查通过
📊 Phase 6 完成: Sprint 规划就绪 (12 Stories in backlog)
🚀 Phase 7 开始: 进入自动开发模式...
   ✅ [1-1] 用户表设计与 Entity 创建 (1/12)
   ✅ [1-2] 用户注册接口 (2/12)
   ...
📄 Phase 8 完成: 文档已生成
🎉 全部完成
```

### 其他触发方式

| 在 AI 对话中输入 | 触发的 Skill | 适用场景 |
|-----------------|-------------|---------|
| `我要做一个功能: [描述]` | bmad-full-cycle | 从零开始，全自动 |
| `full cycle: [描述]` | bmad-full-cycle | 同上 |
| `开始开发` | bmad-autopilot | 已有 PRD/架构/Epic，只需编码 |
| `开始迁移` | bmad-migration-autopilot | 框架迁移场景 |
| `bmad-help` | bmad-help | 查看所有可用命令 |

### 运行中控制

| 在 AI 对话中输入 | 效果 |
|-----------------|------|
| `暂停` | 停止执行，输出详细进度报告（已完成 Story、修改的文件、待处理事项） |
| `继续开发` | 从上次暂停处恢复执行 |
| `当前进度` | 查看当前 Sprint 状态 |
| `full cycle 交互模式: [描述]` | 每个阶段完成后暂停确认，适合想检查中间产物的场景 |

## 8 个阶段

| 阶段 | 做什么 | 产出文件 |
|------|--------|---------|
| Phase 1 | 需求分析 → 生成 PRD | `_bmad-output/planning-artifacts/prd.md` |
| Phase 2 | 架构设计 | `_bmad-output/planning-artifacts/architecture.md` |
| Phase 3 | API 契约（OpenAPI 3.0） | `docs/api/openapi.yaml` |
| Phase 4 | Epic & Story 拆分 | `_bmad-output/planning-artifacts/epics.md` |
| Phase 5 | 实现就绪检查 | 通过或自动修复 |
| Phase 6 | Sprint 规划 | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Phase 7 | 自动编码（循环: 创建规格 → 实现 → 审查） | 源代码 + DDL + Swagger |
| Phase 8 | 技术文档生成 & 收尾 | `docs/` 完整文档 |

## Skill 分组

47 个 skills 按功能分为 9 组（`install.py --list` 查看完整清单）：

| 分组 | 说明 | 核心 Skills |
|------|------|------------|
| 核心 | BMAD 基础设施 | bmad-init, bmad-help, bmad-router |
| 规划 | 需求/架构/Sprint | bmad-create-prd, bmad-create-architecture, bmad-sprint-planning |
| 开发 | 编码/审查 | bmad-create-story, bmad-dev-story, bmad-code-review |
| 自动化 | 全自动编排 | bmad-full-cycle, bmad-autopilot, bmad-migration-autopilot |
| AI 代理 | 角色扮演 | bmad-agent-pm, bmad-agent-architect, bmad-agent-dev, bmad-agent-qa |
| 研究 | 调研分析 | bmad-domain-research, bmad-market-research, bmad-technical-research |
| 审查 | 质量保障 | bmad-review-edge-case-hunter, bmad-qa-generate-e2e-tests |
| 文档 | 文档生成 | bmad-document-project, bmad-generate-project-context |
| 创意 | 头脑风暴/UX | bmad-brainstorming, bmad-create-ux-design |

如果不需要全部安装，可以用 `--select` 只选需要的分组。

## 最终产出物

全流程完成后，项目中新增：

```
docs/
├── architecture/          ← 架构文档（系统总览、模块划分、技术栈、部署拓扑）
├── api/                   ← API 文档（OpenAPI 规范、端点清单、请求示例）
├── implementation/        ← 实施文档（技术决策、模块设计、配置项、异常处理）
├── database/              ← 数据库文档（ER 图、DDL/DML 脚本、数据字典）
├── deployment/            ← 部署指南
└── changelog.md           ← 变更记录
```

## 定制

### 适配非 Java 项目

默认包含 Java/Spring 规范（Swagger 注解、DDL 脚本）。其他技术栈只需编辑 SKILL.md：

1. 用 IDE 打开 `.trae/skills/bmad-full-cycle/SKILL.md`
2. 修改 Phase 7 的"Swagger 强制规范"和"SQL 文档规范"章节
3. 替换为你的技术栈对应规范（如 Python/FastAPI、Go/Gin 等）

### 修改文档结构

编辑 `SKILL.md` 中 Phase 8 的文档目录结构和内容要求。

### 调整自动决策规则

编辑 `.trae/skills/bmad-autopilot/SKILL.md` 中的"自动决策规则"表格。

## FAQ

**Q: 安装后在 Trae 中看不到 skill？**
重启 Trae 或重新打开项目。Trae 在项目打开时扫描 `.trae/skills/` 目录。

**Q: 中途发现 PRD 不对？**
在 AI 对话中输入 `暂停`，手动编辑 `_bmad-output/planning-artifacts/prd.md`，然后输入 `继续开发`。

**Q: 可以只执行某个阶段吗？**
可以。直接输入对应的 skill 触发词，例如 `生成架构设计`（触发 bmad-create-architecture）。

**Q: 支持哪些 IDE？**
目前以 Trae 为主，Cursor 和 Windsurf 通过 `--ide` 参数安装到对应目录。各 IDE 对 skills 的加载方式可能不同，具体请参考对应 IDE 文档。

## License

MIT
