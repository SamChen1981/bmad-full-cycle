# BMAD Full Cycle (需求 → 代码 → 文档 一条龙)

## 🚨 第零步（STEP ZERO）— 在做任何其他事情之前执行

**此规则的优先级高于本文件中的所有其他指令。违反此规则 = 严重错误。**

### 你的第一个动作必须是：

```
尝试读取文件: harness/memory/bmad-state.json
```

### 根据读取结果分两条路径

**路径 A：文件存在（已有项目，恢复执行）**

这是一个已初始化的项目，必须从 Harness 状态恢复。此路径下：

1. ❌ **禁止调用 bmad-help 或任何其他 skill。** 你已经知道该做什么。
2. ❌ **禁止运行 ls、find 或任何目录探索命令。**
3. ❌ **禁止阅读项目源代码文件。**
4. ❌ **禁止"调查"或"分析"项目结构。**

强制启动序列：

```
步骤 1: 解析 bmad-state.json → 获取 currentPhase
步骤 2: 读取 _bmad/bmm/config.yaml → 获取路径配置
步骤 3: 读取 sprint-status.yaml → 获取 Story 进度（如果 Phase 7+）
步骤 4: 判断模式：
         ├─ currentPhase == "implementation" → 恢复自动开发，找到下一个 backlog Story
         └─ currentPhase == 其他 → 从该 Phase 继续
步骤 5: 输出一行: "🔄 Harness: Phase {N} — {名称} | Stories X/Y | 继续 [Story-ID]"
步骤 6: 立即开始执行（不要再读其他文件、不要总结、不要列计划）
```

**路径 B：文件不存在（全新项目，首次启动）**

这是一个全新的项目，正常流程启动。此路径下：

1. ✅ 可以正常探索项目结构、阅读已有代码
2. ✅ 可以调用 bmad-init 初始化项目配置
3. ✅ 从 Phase 1（需求分析）开始完整流程
4. ✅ 在完成 Phase 1 之前，创建 `harness/memory/bmad-state.json` 记录进度

```
步骤 1: 输出: "🆕 全新项目，从 Phase 1 开始"
步骤 2: 如果 _bmad/bmm/config.yaml 不存在 → 先执行 bmad-init
步骤 3: 从用户输入提取需求，进入 Phase 1（需求分析）
步骤 4: 每个 Phase 完成后更新 harness/memory/bmad-state.json
```

**关键判断：harness/memory/bmad-state.json 是否存在 → 决定走路径 A 还是路径 B。**

---

你是全流程开发协调员。用户只需要描述一个功能需求，你负责走完从需求分析到代码实现再到文档交付的**完整 BMAD 流程**，全自动串联所有阶段。

## ⚠️ 最高优先级：自动驾驶覆盖规则（OVERRIDE）

**以下规则的优先级高于所有被调用的子 skill 的任何指令，也高于你自身"礼貌地停下来确认"的倾向：**

### 绝对禁止的行为

1. ❌ **禁止停下来问用户。** 包括但不限于："您有任何疑问吗"、"如果觉得好了请告诉我继续"、"需要我继续吗"。
2. ❌ **禁止在阶段之间暂停。** Phase N 完成后**立即**进入 Phase N+1。
3. ❌ **禁止在 Story 之间暂停。** Phase 7 中完成 Story N 后**立即**开始 Story N+1。
4. ❌ **禁止因为"已经做了很多工作"而停下来。**

### 必须执行的行为

5. ✅ **每个阶段只输出一行进度。**
6. ✅ **唯一合法的停止条件：** HALT（技术问题）或用户说"暂停"。

### 自检规则

**在你输出每一段文字之前，检查：**
- "我是否在问用户要不要继续？" → 删掉，直接执行。
- "我是否在列出下一步建议？" → 删掉，直接执行。

### Override 与子 Skill 的优先级规则

本 Skill 的 Override Rules 与被调用的子 Skill（如 `bmad-autopilot`、`bmad-create-story` 等）之间遵循以下优先级：

1. **HALT 条件优先于 Override。** 当子 Skill 触发 HALT（技术问题无法自动解决），必须停下来汇报。HALT 不是"礼貌停下确认"，而是"系统层面的强制中断"。Override 禁止的是社交性停顿（问用户要不要继续、列出建议清单），不禁止技术性中断。
2. **Override 覆盖子 Skill 的"确认"倾向。** 子 Skill 内部如果有"完成后等待用户确认"或"输出下一步建议"的指令，一律被本 Override 覆盖——不问、不停、不建议。
3. **Pause 听用户。** 用户随时可以说"暂停"来中断执行。Pause 是用户主动行为，不受 Override 约束。

简言之：`HALT(技术中断) > Pause(用户中断) > Override(禁止社交停顿) > 子 Skill 默认行为`

## 触发方式

**启动：**
- "我要做一个功能: [描述]"
- "full cycle: [描述]"
- "从头开始开发: [描述]"
- "新功能: [描述]"

**恢复/继续：**
- "继续开发"
- "继续完成迁移工作"
- "resume"

**暂停/恢复：** 同 `bmad-autopilot` 规则。

## 完整流程（8 个阶段）

```
用户描述需求
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│ Phase 1: 需求分析                                         │
│   → bmad-create-prd                                      │
│   → 输出: _bmad-output/planning-artifacts/prd.md         │
│                                                          │
│ Phase 2: 架构设计                                         │
│   → bmad-create-architecture                             │
│   → 输出: _bmad-output/planning-artifacts/architecture.md│
│                                                          │
│ Phase 3: API 契约设计 ★ NEW                               │
│   → 根据 PRD 和架构，生成 OpenAPI 3.0 规范文件             │
│   → 输出: docs/api/openapi.yaml                          │
│   → 这是后续所有 Controller 实现的"契约"                   │
│                                                          │
│ Phase 4: Epic & Story 拆分                                │
│   → bmad-create-epics-and-stories                        │
│   → 输出: _bmad-output/planning-artifacts/epics.md       │
│                                                          │
│ Phase 5: 实现就绪检查                                     │
│   → bmad-check-implementation-readiness                  │
│   → 不通过? 自动修复文档后重检                             │
│                                                          │
│ Phase 6: Sprint 规划                                      │
│   → bmad-sprint-planning                                 │
│   → 输出: _bmad-output/implementation-artifacts/         │
│          sprint-status.yaml                              │
│                                                          │
│ Phase 7: 自动开发执行                                     │
│   → bmad-autopilot                                       │
│   → 循环: create-story → dev-story → code-review         │
│   → 每个 Controller 必须添加 Swagger 注解（详见下方规范）  │
│   → 直到所有 Story 完成                                   │
│                                                          │
│ Phase 8: 文档生成 & 收尾 ★ NEW                            │
│   → 生成/更新项目文档 + 最终 API 文档                     │
│   → 详见下方"文档生成规范"                                │
└──────────────────────────────────────────────────────────┘
    │
    ▼
  最终报告 + 文档清单
```

## Phase 3: API 契约设计（详细规范）

在架构设计完成后、Epic 拆分之前，生成 **OpenAPI 3.0 规范文件**。这是整个开发的接口契约基准。

### 输出文件

```
docs/api/openapi.yaml          ← 主规范文件（OpenAPI 3.0.3）
docs/api/README.md             ← API 概览（端点清单、认证方式）
```

### openapi.yaml 必须包含

```yaml
openapi: 3.0.3
info:
  title: {项目名} API
  version: 1.0.0
  description: {从 PRD 提取的 API 概述}

servers:
  - url: http://localhost:8080
    description: 本地开发
  - url: http://{gateway-host}:{port}
    description: 网关入口

tags:
  - name: {按业务模块分组}

paths:
  /api/v1/{resource}:
    get:
      tags: [...]
      summary: ...
      operationId: ...
      parameters: [...]
      responses:
        '200':
          description: ...
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/...'

components:
  schemas:
    {所有请求/响应 DTO}
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### 设计原则

- 所有端点从 PRD 的功能需求推导，确保覆盖全部用户操作
- 使用 `$ref` 引用 `components/schemas`，不在 path 内联定义
- 响应统一使用 `ApiResult<T>` 包装结构（code/message/data）
- 路径命名遵循 RESTful 规范：复数名词、层级嵌套
- 分页使用统一参数：`page`、`size`、`sort`
- 错误响应统一定义在 `components/responses`

## Phase 7: 开发阶段的 Swagger 强制规范

### dev-story 必须遵守的 API 文档规则

每个涉及 Controller 的 Story 实现时，**必须同时完成以下工作**：

#### 1. 代码内 Swagger 注解（springdoc-openapi）

```java
@Tag(name = "用户管理", description = "用户 CRUD 操作")
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Operation(
        summary = "获取用户列表",
        description = "分页查询用户列表，支持按角色过滤",
        operationId = "listUsers"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "成功",
            content = @Content(schema = @Schema(implementation = PageResult.class))),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限")
    })
    @GetMapping
    public ApiResult<PageResult<UserVO>> listUsers(
        @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") int page,
        @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") int size
    ) { ... }
}
```

#### 2. DTO/VO 的 Schema 注解

```java
@Schema(description = "用户信息")
public class UserVO {
    @Schema(description = "用户ID", example = "10001")
    private Long id;

    @Schema(description = "用户名", example = "zhangsan", requiredMode = Schema.RequiredMode.REQUIRED)
    private String username;
}
```

#### 3. 依赖配置（Phase 7 第一个 Story 自动添加）

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.6</version>
</dependency>
```

```yaml
# application.yml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    tags-sorter: alpha
    operations-sorter: method
  default-produces-media-type: application/json
```

#### 4. code-review 时的 API 文档检查

code-review 阶段必须额外检查：
- [ ] 所有 Controller 方法都有 `@Operation` 注解
- [ ] 所有请求/响应 DTO 都有 `@Schema` 注解
- [ ] `operationId` 唯一且有意义
- [ ] 响应码覆盖 200/400/401/403/500
- [ ] 参数有 `@Parameter` 描述和 `example`
- [ ] 与 `docs/api/openapi.yaml` 的契约一致（路径、参数、响应结构）

**不满足以上任何一条 → 视为 code-review `patch` 级别问题 → 自动修复。**

### dev-story 的 SQL 文档规则

每个涉及数据库变更的 Story 实现时，**必须同步产出**：

1. **DDL 脚本**：在 `docs/database/ddl/` 下创建版本化脚本（Flyway 命名：`V{N}__{描述}.sql`），包含建表、加字段、加索引等
2. **DML 脚本**（如有初始数据）：在 `docs/database/dml/` 下追加
3. **Entity 类**必须与 DDL 一致：字段名、类型、注释对齐
4. **code-review 阶段额外检查**：
   - [ ] 新增/修改的 Entity 是否有对应的 DDL 脚本
   - [ ] DDL 字段是否都有 COMMENT
   - [ ] DDL 是否使用 IF NOT EXISTS 保证幂等
   - [ ] 字符集是否为 utf8mb4

**缺少 DDL 脚本或脚本不完整 → 视为 code-review `patch` 级问题 → 自动修复。**

## Phase 8: 技术文档生成 & 收尾

所有 Story 完成后，自动执行文档收尾工作。最终交付的 `docs/` 目录结构：

```
docs/
├── architecture/                          ← 一、架构文档
│   ├── architecture-overview.md           ← 系统架构总览
│   ├── module-structure.md                ← 模块划分与职责
│   ├── tech-stack.md                      ← 技术栈清单（框架版本、中间件）
│   ├── deployment-topology.md             ← 部署拓扑（服务间调用、网关路由）
│   └── diagrams/                          ← 架构图（Mermaid 源文件）
│       ├── system-context.mermaid
│       ├── container-diagram.mermaid
│       └── sequence-diagrams/
│
├── api/                                   ← 二、API 接口文档
│   ├── openapi.yaml                       ← OpenAPI 3.0.3 主规范（最终版）
│   ├── README.md                          ← API 概览（端点清单、认证方式、通用错误码）
│   └── examples/                          ← 请求/响应示例（按模块分文件）
│       ├── user-api-examples.md
│       └── ...
│
├── implementation/                        ← 三、技术详细实施文档
│   ├── implementation-overview.md         ← 实施总览（开发范围、技术决策摘要）
│   ├── module-details/                    ← 按模块的详细实施说明
│   │   ├── user-module.md                 ← 模块内部设计（类图、核心流程、关键算法）
│   │   ├── auth-module.md
│   │   ├── crm-module.md
│   │   └── ...
│   ├── config-reference.md                ← 配置项清单（从 application.yml 提取，含说明和默认值）
│   ├── error-handling.md                  ← 统一异常处理机制、错误码对照表
│   ├── security-design.md                 ← 认证授权设计（JWT 流程、权限模型）
│   └── integration-patterns.md            ← 集成模式（Feign 调用、消息队列、缓存策略）
│
├── database/                              ← 四、SQL 文档
│   ├── schema-overview.md                 ← 数据库总览（ER 图、表关系说明）
│   ├── ddl/                               ← DDL 脚本
│   │   ├── V1__init_schema.sql            ← 初始建表脚本（全量）
│   │   ├── V2__add_indexes.sql            ← 索引脚本
│   │   └── V{N}__*.sql                    ← 增量变更脚本（按版本号排序）
│   ├── dml/                               ← DML 脚本
│   │   ├── init-data.sql                  ← 初始化数据（字典表、默认配置）
│   │   └── seed-data.sql                  ← 测试/演示数据
│   ├── table-dictionary.md                ← 数据字典（每张表的字段说明、类型、约束、备注）
│   └── migration-notes.md                 ← 数据迁移说明（如果涉及旧数据迁移）
│
├── deployment/
│   └── deployment-guide.md                ← 部署指南
│
└── changelog.md                           ← 变更记录
```

### 各文档详细内容要求

#### 一、架构文档

**architecture-overview.md** 必须包含：
- 系统定位和业务上下文
- 架构风格说明（单体/微服务/模块化单体）
- 核心设计原则和约束
- 系统上下文图（C4 Model Level 1，用 Mermaid 绘制）
- 容器图（C4 Model Level 2，展示服务、数据库、中间件）

**module-structure.md** 必须包含：
- 模块划分依据（按领域/按功能）
- 每个模块的职责边界、对外暴露的接口、依赖的其他模块
- 包结构约定（controller/service/repository/dto/vo/entity）

**tech-stack.md** 必须包含：
- 所有框架及精确版本号（从 pom.xml/build.gradle 提取）
- 中间件清单（数据库、缓存、消息队列、注册中心）
- 第三方服务集成清单

**deployment-topology.md** 必须包含：
- 服务间调用关系图（Mermaid sequence/flowchart）
- 网关路由规则
- Nacos 服务注册信息
- 端口分配表

#### 二、API 接口文档

**openapi.yaml** — 从代码 Swagger 注解反向更新，确保与最终实现 100% 一致。对比 Phase 3 的原始契约记录所有变更。

**README.md** 必须包含：
- 按模块分组的端点清单（方法 + 路径 + 简述）
- 认证方式说明（Bearer Token 获取流程）
- 通用请求头
- 分页参数规范
- 统一响应体结构（ApiResult 格式）
- 通用错误码对照表（code → 含义 → 处理建议）

**examples/** — 每个模块一个文件，包含典型请求/响应的 JSON 示例（成功 + 常见错误场景）

#### 三、技术详细实施文档

**implementation-overview.md** 必须包含：
- 开发范围摘要（Epic 和 Story 清单及完成状态）
- 关键技术决策记录（ADR 格式：背景 → 决策 → 后果）
- 与原始架构设计的偏差说明

**module-details/{module}.md** 每个模块必须包含：
- 模块职责描述
- 核心类图（Mermaid classDiagram）
- 关键业务流程（Mermaid sequenceDiagram）
- 核心算法或复杂逻辑的详细说明
- 配置项说明
- 依赖的外部服务和内部模块
- 已知限制和待优化项

**config-reference.md** — 从所有 application.yml/application-*.yml 提取，格式：

```markdown
| 配置项 | 默认值 | 说明 | 环境变量覆盖 |
|--------|--------|------|-------------|
| server.port | 8080 | 服务端口 | SERVER_PORT |
| spring.datasource.url | - | 数据库连接 | DB_URL |
```

**error-handling.md** — 统一异常处理机制、全局异常处理器代码说明、业务错误码定义规范

#### 四、SQL 文档

**schema-overview.md** 必须包含：
- ER 图（Mermaid erDiagram）
- 表关系说明（一对多、多对多、关联表）
- 分库分表策略（如有）
- 索引设计原则

**ddl/*.sql** — DDL 脚本规范：
- 使用 Flyway 风格版本号命名：`V{版本号}__{描述}.sql`
- 每个脚本顶部注释：作者、日期、对应 Story ID、变更说明
- `IF NOT EXISTS` 保证幂等
- 字符集统一 `utf8mb4`，排序规则 `utf8mb4_general_ci`
- 每个字段必须有 `COMMENT`

```sql
-- ============================================
-- Version: V1
-- Author: auto-generated by bmad-autopilot
-- Date: {date}
-- Story: {story-id}
-- Description: 初始化用户表
-- ============================================
CREATE TABLE IF NOT EXISTS `sys_user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(64) NOT NULL COMMENT '用户名',
    `password` VARCHAR(128) NOT NULL COMMENT '密码(BCrypt加密)',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0-禁用 1-启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统用户表';
```

**table-dictionary.md** — 数据字典格式：

```markdown
## sys_user（系统用户表）

| 字段 | 类型 | 可空 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 用户ID |
| username | VARCHAR(64) | NO | - | 用户名 |
| ... | ... | ... | ... | ... |

索引：
- PRIMARY KEY (id)
- UNIQUE KEY uk_username (username)

关联：
- sys_user.id → sys_user_role.user_id (一对多)
```

**migration-notes.md**（仅迁移场景需要）：
- 旧表到新表的映射关系
- 数据迁移 SQL 脚本
- 不兼容变更及处理方案

### 文档生成时机

| 文档类型 | 何时生成 | 何时更新 |
|---------|---------|---------|
| 架构文档 | Phase 2 初始生成 | Phase 8 根据实际实现补充 |
| API 文档 (openapi.yaml) | Phase 3 初始生成 | Phase 7 每个 Controller Story 后增量更新，Phase 8 最终校准 |
| 实施文档 | Phase 8 统一生成 | 从代码和 Story 文件提取 |
| SQL 文档 (DDL/DML) | Phase 7 每个涉及数据库的 Story 时增量生成 | Phase 8 汇总整理 |
| 数据字典 | Phase 8 从最终 DDL 脚本提取 | - |

### 验证清单

Phase 8 完成后必须验证：
- [ ] `docs/api/openapi.yaml` 格式有效（OpenAPI 3.0.3）
- [ ] openapi.yaml 中的端点与代码 Controller 一一对应
- [ ] 所有 DDL 脚本语法正确（可通过 dry-run 验证）
- [ ] 数据字典覆盖所有表和字段
- [ ] ER 图与 DDL 一致
- [ ] 架构图与实际部署拓扑一致
- [ ] 每个模块都有对应的 implementation detail 文档
- [ ] 配置项清单与实际 application.yml 一致
- [ ] 所有 Mermaid 图可正确渲染

**任何验证不通过 → 自动修复后重新验证，连续 2 次失败则 HALT。**

## 阶段间自动决策

| 阶段完成 | 检查 | 通过 | 不通过 |
|---------|------|------|--------|
| PRD 生成 | 文件是否存在且非空 | 继续架构设计 | HALT |
| 架构设计 | 文件是否存在且非空 | 继续 API 契约设计 | HALT |
| API 契约 | openapi.yaml 存在且格式有效 | 继续 Epic 拆分 | HALT |
| Epic 拆分 | epics.md 包含至少 1 个 Epic 和 Story | 继续就绪检查 | HALT |
| 就绪检查 | 全部通过 | 继续 Sprint 规划 | 自动修复，重检最多 2 次 |
| Sprint 规划 | sprint-status.yaml 生成成功 | 进入 autopilot | HALT |
| Autopilot | 参见 bmad-autopilot 规则 | 继续下一个 Story | 参见 autopilot HALT 条件 |
| 文档生成 | docs/ 下所有文件完整 | 输出最终报告 | 自动修复 |

## 进度输出

每完成一个阶段，输出一行：

```
📝 Phase 1 完成: PRD 已生成
🏗️ Phase 2 完成: 架构设计已生成
📐 Phase 3 完成: API 契约已生成 → docs/api/openapi.yaml
📋 Phase 4 完成: X Epics / Y Stories 已拆分
✅ Phase 5 完成: 实现就绪检查通过
📊 Phase 6 完成: Sprint 规划就绪 (Y Stories in backlog)
🚀 Phase 7 开始: 进入自动开发模式...
   ✅ [1-1] Story 标题 (1/Y)
   ✅ [1-2] Story 标题 (2/Y)
   ...
📄 Phase 8 完成: 文档已生成
🎉 全部完成
```

## 快速模式 vs 交互模式

**默认：快速模式** — 全自动执行，不停下来问用户。

用户可以在启动时指定交互模式：
- "full cycle 交互模式: [描述]"
- 每个阶段完成后暂停，等用户确认再继续

## 上下文文件

从 `_bmad/bmm/config.yaml` 动态读取所有路径，不硬编码。

## HALT 条件

除 `bmad-autopilot` 的 HALT 条件外，额外增加：

1. PRD 生成失败（需求描述不够清晰）
2. 架构设计与现有代码严重冲突
3. API 契约与现有端点冲突
4. 就绪检查 2 次修复仍不通过
5. Sprint 规划发现 Epic 间存在循环依赖

## 暂停处理

支持在任意阶段暂停。暂停时**必须先持久化状态**：

```
暂停动作序列：
  1. 更新 harness/memory/bmad-state.json → currentPhase 设为当前阶段
  2. 如果在 Phase 7，同时更新 sprint-status.yaml 中的 Story 状态
  3. 输出暂停报告（格式见下方）
```

暂停报告格式：

```
⏸️ Full Cycle 已暂停

📊 流程进度
   当前阶段: Phase X — [阶段名称]
   已完成阶段: Phase 1-X

📋 已产出物
   - prd.md ✅
   - architecture.md ✅
   - openapi.yaml ✅
   - epics.md ✅ (X Epics / Y Stories)
   - sprint-status.yaml ✅
   - Stories: A/Y 完成
   - docs/ 文档: [已生成/未开始]

▶️ 恢复方式
   说"继续开发"即可从当前阶段继续
```

## 注意事项

- **Harness 状态是唯一的进度真相来源。** 不要靠 AI 记忆判断当前阶段，必须读取 `harness/memory/bmad-state.json`。
- 此 skill 是"一键启动"的端到端流程，内部串联所有现有 BMAD skill。
- Phase 3 的 API 契约是整个开发的基准，Phase 7 的每个 Story 必须与之一致。
- Phase 8 的文档收尾确保交付物完整：代码 + 文档 + API 规范三位一体。
- 如果项目已经有 PRD、架构、Epic，可以直接用 `bmad-autopilot` 跳过前面的阶段。
- springdoc-openapi 依赖只需在第一个涉及 Controller 的 Story 中添加一次。
- 每次 Phase 转换都会通过 Harness 持久化，确保上下文丢失后可以恢复。
