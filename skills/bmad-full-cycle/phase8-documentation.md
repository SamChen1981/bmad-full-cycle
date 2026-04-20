# Phase 8: 技术文档生成 & 收尾

所有 Story 完成后，自动执行文档收尾。最终交付 `docs/` 目录结构：

```
docs/
├── architecture/              ← 架构文档
│   ├── architecture-overview.md   (C4 上下文图+容器图、架构风格、设计原则)
│   ├── module-structure.md        (模块划分、职责边界、包结构)
│   ├── tech-stack.md              (框架精确版本、中间件、第三方服务)
│   └── deployment-topology.md     (服务调用图、网关路由、Nacos、端口)
│
├── api/                       ← API 接口文档
│   ├── openapi.yaml               (OpenAPI 3.0.3 最终版，与代码100%一致)
│   ├── README.md                  (端点清单、认证、错误码)
│   └── examples/                  (请求/响应 JSON 示例)
│
├── implementation/            ← 技术实施文档
│   ├── implementation-overview.md (开发范围、ADR、偏差说明)
│   ├── module-details/            (按模块：类图、流程图、算法)
│   ├── config-reference.md        (配置项清单)
│   ├── error-handling.md          (异常处理、错误码)
│   └── integration-patterns.md    (Feign/MQ/缓存)
│
├── database/                  ← SQL 文档
│   ├── schema-overview.md         (ER 图、表关系、索引策略)
│   ├── ddl/                       (版本化建表脚本)
│   ├── dml/                       (初始化数据)
│   └── table-dictionary.md        (数据字典)
│
├── deployment/
│   └── deployment-guide.md
│
└── changelog.md
```

## 验证清单

Phase 8 完成后必须验证：

- [ ] openapi.yaml 格式有效，端点与 Controller 一一对应
- [ ] DDL 脚本语法正确，数据字典覆盖所有表
- [ ] ER 图与 DDL 一致
- [ ] 每个模块有实施文档
- [ ] 配置项清单与 application.yml 一致
- [ ] Mermaid 图可正确渲染

不通过 → 自动修复后重新验证，连续 2 次失败则 HALT。
