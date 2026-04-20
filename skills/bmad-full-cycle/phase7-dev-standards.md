# Phase 7: 开发阶段规范（Swagger + SQL）

## Swagger 强制规范

每个涉及 Controller 的 Story 实现时，**必须同时完成**：

### 1. 代码内 Swagger 注解（springdoc-openapi）

```java
@Tag(name = "用户管理", description = "用户 CRUD 操作")
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Operation(summary = "获取用户列表", operationId = "listUsers")
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

### 2. DTO/VO 的 Schema 注解

```java
@Schema(description = "用户信息")
public class UserVO {
    @Schema(description = "用户ID", example = "10001")
    private Long id;
    @Schema(description = "用户名", example = "zhangsan", requiredMode = Schema.RequiredMode.REQUIRED)
    private String username;
}
```

### 3. 依赖配置（首个 Controller Story 自动添加）

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.6</version>
</dependency>
```

### 4. code-review 检查清单

- [ ] 所有 Controller 方法有 `@Operation` 注解
- [ ] 所有 DTO 有 `@Schema` 注解
- [ ] `operationId` 唯一且有意义
- [ ] 响应码覆盖 200/400/401/403/500
- [ ] 与 `docs/api/openapi.yaml` 契约一致

不满足 → `patch` 级问题 → 自动修复。

## SQL 文档规范

涉及数据库变更的 Story，**必须同步产出**：

1. **DDL 脚本**: `docs/database/ddl/V{N}__{描述}.sql`（Flyway 命名，IF NOT EXISTS，utf8mb4，字段必须 COMMENT）
2. **DML 脚本**（如有）: `docs/database/dml/`
3. **Entity 与 DDL 对齐**: 字段名、类型、注释一致

DDL 模板:

```sql
-- Version: V1 | Story: {story-id} | Date: {date}
CREATE TABLE IF NOT EXISTS `sys_user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(64) NOT NULL COMMENT '用户名',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统用户表';
```

缺少 DDL → `patch` 级问题 → 自动修复。
