---
name: bmad-java-code-standards
description: 'Java 代码质量守护规范（质量宪法）。在 dev-story 编码和 code-review 审查过程中自动生效，通过量化指标、设计模式约束、防御性编程规则和自动化检测保障生成代码的企业级生产质量。Use when developing Java projects — this skill is automatically referenced by dev-story and code-review.'
alwaysApply: true
---

# Java 代码质量守护规范（质量宪法）

**本规范的优先级高于一切编码习惯。生成的每一行 Java 代码都必须通过以下 10 条规则的检验。**

完整规范见 `./java-standards.md`，审查检查清单见 `./review-checklist.md`。

## 规则速查

| # | 规则 | 量化约束 |
|---|------|---------|
| R1 | 单一职责原则 (SRP) | 类 ≤300 行，方法 ≤50 行，参数 ≤5 个 |
| R2 | 开闭原则 (OCP) | if-else/switch 分支 ≤3 个，超过则强制策略模式 |
| R3 | 工厂 + 策略模式 | Spring 自动注入构建映射表，调用方零 if-else |
| R4 | Java 编程规范 | 阿里 Java 开发手册 + Google Java Style |
| R5 | 类头部注释 | @author + @since + @modified + 职责描述 |
| R6 | 方法注释 + 过程注释 + 日志 | Javadoc + 步骤注释 + 关键节点 SLF4J 日志 |
| R7 | 日志规格 | `[模块][操作][参数]` + TraceId + 占位符 `{}` |
| R8 | 代码复用 (DRY) | 优先 java.util / Apache Commons，禁止重复造轮子 |
| R9 | 防御性编程 | 空指针防护 + 参数校验前置 + try-with-resources |
| R10 | 依赖注入纪律 | 严禁业务类中 new 依赖对象，必须构造函数注入 |

## 输出前自审清单

**在输出每个 Java 文件前，AI 必须自问：**
- 是否有超过 3 层的 if-else？（如有 → 重构为策略模式）
- 方法是否超过 50 行？（如有 → 拆分）
- 类是否超过 300 行？（如有 → 拆分为内部类或独立文件）
- 是否包含 `System.out`？（如有 → 替换为 log）
- 是否捕获了 Exception 但没记录日志？（如有 → 修复）
- 是否有 `new` 创建的业务依赖？（如有 → 改为注入）
- IO/数据库连接是否用了 try-with-resources？（如否 → 修复）
- 集合返回值是否可能为 null？（如是 → 改为空集合）

## dev-story 集成点

在 dev-story 的 Step 5（实现任务）中，每个 Java 文件生成前必须：
1. 检查 R1 量化指标 — 类 ≤300 行、方法 ≤50 行、参数 ≤5 个
2. 检查 R2 — 新增分支 ≤3 个，超过则重构为接口 + 实现
3. 检查 R3 — 多类型调度必须使用工厂 + 策略
4. 执行 R5/R6 — 类头注释 + 方法 Javadoc + 步骤注释
5. 执行 R7 — SLF4J 日志，格式 `[模块][操作][参数]`
6. 执行 R8 — 搜索项目已有工具类/基类，优先复用
7. 执行 R9 — 参数校验、空值防护、资源管理
8. 执行 R10 — 依赖注入，禁止 new
9. 运行输出前自审清单

## code-review 集成点

在 code-review 的 Step 2（审查）中，额外增加一个 **Java Standards Auditor** 审查层，使用 `./review-checklist.md` 逐条检查。不满足的项一律标记为 `patch` 或 `critical` 级别。

## Gatekeeper 集成点

在 Gatekeeper 的 implementation 阶段检查中，自动运行 Java 静态质量检测：
- 扫描 `System.out.println` → 发现即阻断
- 扫描类头部是否有 `@author` 和 `@since` → 缺失即告警
- 扫描超过 300 行的 Java 类文件 → 发现即告警
- 扫描超过 80 行的方法 → 发现即告警
