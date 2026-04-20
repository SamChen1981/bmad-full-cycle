---
name: bmad-java-code-standards
description: 'Java 代码质量强制规范。在 dev-story 编码和 code-review 审查过程中自动生效，约束生成代码必须遵守 SOLID 原则、设计模式、注释规范、日志规格和复用要求。Use when developing Java projects — this skill is automatically referenced by dev-story and code-review.'
alwaysApply: true
---

# Java 代码质量强制规范

**本规范的优先级高于一切编码习惯。生成的每一行 Java 代码都必须通过以下 8 条规则的检验。**

完整规范见 `./java-standards.md`，审查检查清单见 `./review-checklist.md`。

## 规则速查

| # | 规则 | 一句话要求 |
|---|------|-----------|
| R1 | 单一职责原则 (SRP) | 一个类只有一个变化的原因，一个方法只做一件事 |
| R2 | 开闭原则 (OCP) | 对扩展开放，对修改关闭 — 用接口/抽象类约束扩展点 |
| R3 | 设计模式组合 | 工厂 + 策略模式结合：工厂按类型创建策略实例，业务调用方无 if-else |
| R4 | Java 编程规范 | 严格遵守阿里 Java 开发手册 + Google Java Style |
| R5 | 类头部注释 | 必须包含 @author、@since（创建时间）、@modified（修改时间）、变更说明 |
| R6 | 方法注释 + 过程注释 + 日志 | 方法头 Javadoc + 关键步骤行内注释 + 关键节点 log 输出 |
| R7 | 日志规格 | 统一格式 `[模块][操作][关键参数]`，区分 DEBUG/INFO/WARN/ERROR 级别 |
| R8 | 代码复用 | 禁止重复代码，提取工具类/基类/模板方法 |

## dev-story 集成点

在 dev-story 的 Step 5（实现任务）中，每个 Java 文件生成前必须：
1. 检查是否符合 R1 — 类/方法职责是否单一
2. 检查是否符合 R2 — 新增逻辑是否通过扩展而非修改已有类实现
3. 检查是否符合 R3 — 涉及多种类型/策略时必须使用工厂 + 策略模式
4. 执行 R5/R6 — 为每个类和方法添加规范注释
5. 执行 R7 — 在每个关键节点添加日志输出
6. 检查 R8 — 在当前项目中搜索是否已有类似逻辑可复用

## code-review 集成点

在 code-review 的 Step 2（审查）中，额外增加一个 **Java Standards Auditor** 审查层，使用 `./review-checklist.md` 逐条检查。不满足的项一律标记为 `patch` 或 `critical` 级别。
