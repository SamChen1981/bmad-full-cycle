# Phase 3: API 契约设计规范

在架构设计完成后、Epic 拆分之前，生成 **OpenAPI 3.0 规范文件**。

## 输出文件

```
docs/api/openapi.yaml          ← 主规范文件（OpenAPI 3.0.3）
docs/api/README.md             ← API 概览（端点清单、认证方式）
```

## openapi.yaml 必须包含

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

## 设计原则

- 所有端点从 PRD 的功能需求推导，确保覆盖全部用户操作
- 使用 `$ref` 引用 `components/schemas`，不在 path 内联定义
- 响应统一使用 `ApiResult<T>` 包装结构（code/message/data）
- 路径命名遵循 RESTful 规范：复数名词、层级嵌套
- 分页使用统一参数：`page`、`size`、`sort`
- 错误响应统一定义在 `components/responses`
