# BMAD Full Cycle — 从需求到代码到文档的一键开发

## 这是什么

`bmad-full-cycle` 是一个 Trae skill，串联 BMAD 体系的所有阶段，让你只需描述一个功能需求，AI 就能全自动走完"需求分析 → 架构设计 → API 契约 → Epic/Story 拆分 → 就绪检查 → Sprint 规划 → 自动开发 → 文档生成"的完整流程。

核心理念：**你负责说要什么，AI 负责做完**。中间不需要任何确认或干预，除非遇到技术问题。

## 快速开始

### 1. 安装前置条件

本 skill 依赖以下已安装的 BMAD skills（如果缺失会导致某些阶段无法执行）：

| Skill | 用途 | 必需 |
|-------|------|------|
| `bmad-init` | 项目初始化 | 首次使用 |
| `bmad-create-prd` | 生成需求文档 | Phase 1 |
| `bmad-create-architecture` | 生成架构设计 | Phase 2 |
| `bmad-create-epics-and-stories` | Epic/Story 拆分 | Phase 4 |
| `bmad-check-implementation-readiness` | 就绪检查 | Phase 5 |
| `bmad-sprint-planning` | Sprint 规划 | Phase 6 |
| `bmad-autopilot` | 自动开发循环 | Phase 7 |
| `bmad-create-story` | 生成 Story 规格 | Phase 7 子步骤 |
| `bmad-dev-story` | 实现代码 | Phase 7 子步骤 |
| `bmad-code-review` | 代码审查 | Phase 7 子步骤 |

### 2. 项目初始化（仅首次）

如果项目还没有 `_bmad/` 目录，先运行 `bmad-init` 初始化：

```
初始化 bmad 项目
```

这会创建 `_bmad/bmm/config.yaml` 等基础配置文件。

### 3. 一键启动

在 Trae 对话中输入以下任意触发短语：

```
我要做一个功能: 用户管理模块，支持注册登录、角色权限、组织架构
```

```
full cycle: 实现商品目录系统，包含分类管理、SKU 管理、库存查询
```

```
新功能: 客户 CRM 模块，含客户档案、跟进记录、销售漏斗
```

然后等着看进度条即可。

## 8 个阶段

| 阶段 | 做什么 | 产出 |
|------|--------|------|
| Phase 1 | 需求分析 → 生成 PRD | `_bmad-output/planning-artifacts/prd.md` |
| Phase 2 | 架构设计 | `_bmad-output/planning-artifacts/architecture.md` |
| Phase 3 | API 契约设计（OpenAPI 3.0） | `docs/api/openapi.yaml` |
| Phase 4 | Epic & Story 拆分 | `_bmad-output/planning-artifacts/epics.md` |
| Phase 5 | 实现就绪检查 | 通过/自动修复 |
| Phase 6 | Sprint 规划 | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Phase 7 | 自动开发（循环执行所有 Story） | 源代码 + DDL/DML + Swagger 注解 |
| Phase 8 | 文档生成 & 收尾 | `docs/` 完整技术文档 |

## 运行中的控制

### 暂停

随时输入 `暂停` 即可停止执行并获取详细进度报告，包括已完成的 Story 列表、当前进展、修改的文件清单和待处理事项。

### 恢复

暂停后输入 `继续开发` 即可从上次中断处继续。

### 交互模式

如果你想在每个阶段完成后手动确认再继续（比如想检查 PRD 是否符合预期），可以用交互模式启动：

```
full cycle 交互模式: 用户管理模块
```

## 在其他项目中使用

### 方式一：复制 skill 目录

将 `.trae/skills/bmad-full-cycle/` 目录复制到你的项目中：

```bash
# 从 abeiya 项目复制到新项目
cp -r /path/to/abeiya/.trae/skills/bmad-full-cycle /path/to/your-project/.trae/skills/
```

同时需要复制依赖的 BMAD skills（上面表格中列出的）。最简单的方式是复制整个 `.trae/skills/bmad-*` 系列：

```bash
cp -r /path/to/abeiya/.trae/skills/bmad-* /path/to/your-project/.trae/skills/
```

### 方式二：从 _bmad 目录安装

如果项目已有 `_bmad/` 基础设施（通过 `bmad-init` 安装），只需要添加 `bmad-full-cycle` 和 `bmad-autopilot` 这两个"编排层" skill 即可，其他 skill 已经在 `_bmad/` 中了。

### 适配你的项目

`bmad-full-cycle` 是通用的，适用于任何 Spring Boot / Spring Cloud 项目，也适用于其他技术栈。它通过 `_bmad/bmm/config.yaml` 读取项目配置，不硬编码路径。

如果你的项目不是 Java / Spring，只需要确保：

1. `_bmad/bmm/config.yaml` 中正确配置了项目路径和技术栈信息
2. 自行调整 Swagger / DDL 相关规范（或在 SKILL.md 中注释掉不需要的部分）

## 产出物清单

开发完成后，你会获得以下目录结构：

```
docs/
├── architecture/          ← 架构文档（系统总览、模块划分、技术栈、部署拓扑）
├── api/                   ← API 文档（OpenAPI 规范、端点清单、示例）
├── implementation/        ← 实施文档（开发范围、模块详细设计、配置项、异常处理）
├── database/              ← 数据库文档（ER 图、DDL/DML 脚本、数据字典）
├── deployment/            ← 部署指南
└── changelog.md           ← 变更记录

_bmad-output/
├── planning-artifacts/    ← PRD、架构设计、Epic/Story 定义
└── implementation-artifacts/ ← Sprint 状态、Story 规格文件
```

## 与 bmad-autopilot 的关系

`bmad-full-cycle` 是端到端的编排器，内部在 Phase 7 调用 `bmad-autopilot` 来执行开发循环。如果你的项目已经有 PRD、架构设计和 Epic/Story（比如由产品经理手动编写的），可以直接用 `bmad-autopilot` 跳过 Phase 1-6，从开发阶段开始。

| 场景 | 使用 |
|------|------|
| 从零开始开发新功能 | `bmad-full-cycle` |
| 已有需求/设计文档，只需自动编码 | `bmad-autopilot` |
| 迁移项目（有专门的迁移计划） | `bmad-migration-autopilot` |

## 常见问题

**Q: 如果中途发现 PRD 不对怎么办？**
启动交互模式，或者暂停后手动编辑 `_bmad-output/planning-artifacts/prd.md`，然后说"继续开发"。

**Q: 可以只执行其中某几个阶段吗？**
可以直接调用单独的 skill，比如只想生成架构设计：`bmad-create-architecture`。

**Q: Phase 7 执行太慢？**
每个 Story 都包含创建规格 → 编码 → 审查三步，复杂 Story 可能需要几分钟。可以通过拆分更小的 Story 来加速。

**Q: 文档生成的格式可以定制吗？**
可以编辑 `SKILL.md` 中 Phase 8 的文档目录结构和内容要求来定制。
