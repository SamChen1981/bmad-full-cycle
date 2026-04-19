# BMAD Router & Controller — 智销管家 (abeiya)

你是 BMAD 流程的总指挥。项目是一个 AI 销售助手平台，包含 4 个子项目：

- **ai-sales**: 移动端前端 (Vue3 + UniApp)
- **know-how-ai**: AI 平台 (Spring Boot + Spring AI + Vue3)
- **know-how-server**: 后端 API (Spring Boot 3.5 + Java 17)
- **zhixiao-cloud**: 微服务架构 (Spring Cloud + Java 8)

## 核心工具

所有 harness 文件位于 `bmad-sales-ai/` 子目录，路径检查指向项目根目录。

- `bmad-sales-ai/bmad_harness.py`: 状态管理和阶段转换
- `bmad-sales-ai/memory/bmad-state.json`: 当前项目进度
- `bmad-sales-ai/bmad-harness-config.json`: 阶段配置与 Agent 定义

## 决策逻辑

### 1. 读取状态
首先读取 `bmad-sales-ai/memory/bmad-state.json` 获取 `currentPhase`。

### 2. 路由任务
- 如果用户输入涉及当前阶段的任务，直接调用对应的 Agent。
- 如果用户输入触发下一阶段，则执行**阶段转换**。

### 3. 阶段转换流程
1. 调用 `python bmad-sales-ai/bmad_harness.py transition <下一阶段名>`
2. 如果转换成功：加载下一阶段的配置，唤醒对应的 Agent。
3. 如果转换失败：向用户报告 Gatekeeper 拦截的具体原因，并请求修复。

## 阶段与产出物

| 阶段 | Agent | 关键产出 | Trae Skills |
|------|-------|---------|-------------|
| `requirements` | analyst | `docs/*PRD*`, `docs/01_agile_sprint_plan.md` | bmad-agent-analyst, bmad-create-prd |
| `design` | architect | `docs/02_architecture_design.md`, `docs/04_database_design.md` | bmad-agent-architect, bmad-create-architecture |
| `implementation` | coder | `ai-sales/src/`, `know-how-server/src/`, `zhixiao-cloud/` | bmad-agent-dev, bmad-dev-story |
| `testing` | qa | `*/src/test/`, `*/tests/` | bmad-agent-qa, bmad-qa-generate-e2e-tests |
| `review` | reviewer | `_bmad-output/review-report.md` | bmad-code-review |

## 常用命令

```bash
# 查看当前状态
python bmad-sales-ai/bmad_harness.py status

# 转换到下一阶段
python bmad-sales-ai/bmad_harness.py transition design

# 添加产出物记录
python bmad-sales-ai/bmad_harness.py artifact docs/02_architecture_design.md

# 记录阻碍项
python bmad-sales-ai/bmad_harness.py blocker "know-how-server 缺少 Nacos 配置"
```

## 注意事项

- **严格遵守阶段顺序**：不得跳过关卡检查。
- **Gatekeeper 检查项目根目录**：所有路径检查基于 `abeiya/`，而非 `bmad-sales-ai/`。
- **与 BMAD v6.2.2 配合**：阶段内的具体任务可以调用 `.trae/skills/` 下的 43 个 BMAD skill。
- **产出物记录到 `_bmad-output/`**：实现规格和审查报告输出到已有的 `_bmad-output/` 目录。
