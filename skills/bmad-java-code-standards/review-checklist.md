# Java Code Standards — Review Checklist

**用途：** 在 code-review 的 Step 2 中，作为 **Java Standards Auditor** 审查层的检查清单。逐条检查，每个不通过的项生成一条 finding。

---

## R1: 单一职责原则 (SRP)

- [ ] 每个类是否只承担一个职责？Controller 中是否混入了业务逻辑？
- [ ] Service 中是否直接操作数据库（绕过 Repository/Mapper）？
- [ ] 每个方法是否只做一件事？是否存在超过 50 行的方法体？
- [ ] 方法参数是否超过 5 个？超过的是否已封装为请求对象？
- [ ] 方法内部是否存在混合抽象层次（高层编排逻辑和底层实现细节混在一起）？

**严重级别：** 违反 → `patch`（可拆分修复），严重混乱 → `critical`

---

## R2: 开闭原则 (OCP)

- [ ] 是否存在超过 3 个分支的 if-else / switch-case 用于类型判断？
- [ ] 新增业务类型时是否需要修改已有 Service 主逻辑？
- [ ] 是否有硬编码的配置值应该外部化？
- [ ] 扩展点是否通过接口/抽象类定义？

**严重级别：** 3-5 个分支 → `patch`（建议重构），>5 个分支 → `critical`（必须重构）

---

## R3: 设计模式 — 工厂 + 策略

- [ ] 多类型业务逻辑是否使用了策略接口 + 多实现类？
- [ ] 策略工厂是否通过 Spring 自动注入构建映射表？
- [ ] 调用方是否仍存在 if-else 进行类型路由？
- [ ] 新增策略实现后，工厂和调用方的代码是否无需修改？

**严重级别：** 缺少策略模式 → `patch`，工厂中硬编码 new → `patch`

---

## R4: Java 编程规范

### 命名
- [ ] 类名是否 UpperCamelCase？
- [ ] 方法名是否 lowerCamelCase 且动词开头？
- [ ] 常量是否 UPPER_SNAKE_CASE？
- [ ] 包名是否全小写？
- [ ] 布尔变量/方法是否 `is/has/can/should` 开头？

### 代码结构
- [ ] import 是否使用了通配符 `*`？
- [ ] 类内部顺序是否正确：常量 → 静态变量 → 实例变量 → 构造方法 → 公开方法 → 私有方法？

### 异常处理
- [ ] 是否存在空 catch 块 `catch (Exception e) {}`？
- [ ] 异常是否记录了日志或向上抛出？
- [ ] 业务异常是否使用了 BizException + 错误码？
- [ ] finally 中是否有 return 语句？

### 空值处理
- [ ] 方法返回集合时是否返回了 null（应返回空集合）？
- [ ] 外部输入是否做了 null 检查？

**严重级别：** 命名不规范 → `patch`，空 catch 块 → `critical`

---

## R5: 类头部注释

- [ ] 每个 Java 类是否有头部 Javadoc？
- [ ] 是否包含 `@author` 标签？
- [ ] 是否包含 `@since` 标签（创建日期 yyyy-MM-dd）？
- [ ] 新增/修改的类是否有 `@modified` 标签记录变更？
- [ ] 类描述是否一句话概述职责？
- [ ] 接口/抽象类是否说明了设计意图和扩展方式？
- [ ] 枚举值是否每个都有注释？

**严重级别：** 缺少头部注释 → `patch`（可自动生成）

---

## R6: 方法注释 + 过程注释 + 日志

### 方法头部 Javadoc
- [ ] 每个 public/protected 方法是否有 Javadoc？
- [ ] `@param` 是否对每个参数有描述？
- [ ] `@return` 是否描述了返回值含义？
- [ ] `@throws` 是否列出了可能的异常及触发条件？

### 过程注释
- [ ] 复杂业务方法内是否有步骤编号注释（// 1. xxx // 2. xxx）？
- [ ] 关键算法或非显而易见的逻辑是否有解释性注释？

### 关键节点日志
- [ ] 业务方法入口是否有 INFO 日志记录关键入参？
- [ ] 外部调用（数据库、远程接口、消息队列）前后是否有日志？
- [ ] 异常 catch 块中是否有 ERROR/WARN 日志？
- [ ] 重要业务方法出口是否有结果日志？

**严重级别：** 缺少 Javadoc → `patch`，关键节点无日志 → `patch`

---

## R7: 日志规格

- [ ] 日志格式是否统一使用 `[模块][操作][关键参数]` 模式？
- [ ] 是否使用了 `System.out.println` / `System.err.println` / `e.printStackTrace()`？
- [ ] 日志中是否打印了敏感信息（密码、身份证、银行卡号）？
- [ ] 循环内是否有大量 INFO 日志（应改为 DEBUG 或汇总）？
- [ ] ERROR 日志是否包含上下文参数和异常对象？
- [ ] 是否使用字符串拼接而非占位符 `{}`？
- [ ] 日志级别是否恰当（DEBUG/INFO/WARN/ERROR 区分是否正确）？
- [ ] 是否配置了 MDC TraceId（分布式环境下的链路追踪）？
- [ ] logback.xml 的 pattern 是否包含 `%X{traceId}`？

**严重级别：** 敏感信息泄露 → `critical`，格式不统一 → `patch`，`System.out.println` → `patch`，缺少 TraceId → `patch`

---

## R8: 代码复用 (DRY)

- [ ] 是否存在两处以上相似代码（>5 行重复）？（复制粘贴嫌疑）
- [ ] 通用逻辑（参数校验、分页、响应封装）是否使用了项目级工具类/基类？
- [ ] 是否按优先级使用工具类？（JDK → Apache Commons → Guava → 项目 Utils）
- [ ] 字符串判空是否使用 `StringUtils.isBlank()` 而非手写？
- [ ] 集合判空是否使用 `CollectionUtils.isEmpty()` 而非手写？
- [ ] 日期处理是否使用 `java.time`（严禁 `java.util.Date`）？
- [ ] 相似业务流程（>3 个子类相同骨架）是否使用了模板方法模式？
- [ ] 继承层次是否超过 3 层？
- [ ] 是否优先使用组合（依赖注入）而非继承？

**严重级别：** 重复代码 → `patch`（提取公共方法），深层继承 → `patch`，重复造轮子 → `patch`

---

## R9: 防御性编程

### 参数校验前置
- [ ] 所有 public 方法入口是否做了参数校验（卫语句 / early throw）？
- [ ] 必填参数是否使用 `Objects.requireNonNull()` 或 `@NotNull` 注解？
- [ ] 业务参数校验是否使用了 BizException + ErrorCode？

### 空指针防护
- [ ] 方法返回集合时是否返回了 null？（应返回 `Collections.emptyList()`）
- [ ] 返回可能为空的单个对象是否使用了 `Optional<T>`？
- [ ] 外部输入（Controller 参数、RPC 返回值）是否做了 null 检查？
- [ ] 字符串判空是否使用 `StringUtils.isBlank()`？
- [ ] 集合判空是否使用 `CollectionUtils.isEmpty()`？
- [ ] Map 取值是否使用 `map.getOrDefault()` 代替直接 get？

### 资源管理
- [ ] IO 流、数据库连接、HTTP 客户端是否使用了 **try-with-resources**？
- [ ] catch 块中是否只打印了 `e.getMessage()` 而吞掉异常栈？（必须传递完整异常对象）
- [ ] 创建 ArrayList/HashMap 时已知大小是否指定了初始容量？

**严重级别：** 缺少参数校验 → `patch`，返回 null 集合 → `patch`，未关闭资源 → `critical`，吞异常栈 → `critical`

---

## R10: 依赖注入纪律

- [ ] 业务类中是否使用了 `new` 创建依赖对象？（严禁，必须注入）
- [ ] 是否使用了构造函数注入（推荐，配合 `@RequiredArgsConstructor`）？
- [ ] 注入字段是否声明为 `private final`？
- [ ] 是否使用了字段注入 `@Autowired` on field？（禁止使用）
- [ ] 配置值是否使用 `@Value` 或 `@ConfigurationProperties`？（严禁硬编码 URL、端口、密码）
- [ ] 类的依赖注入数量是否超过 7 个？（超过说明职责过多，需拆分）

**严重级别：** new 依赖对象 → `critical`，字段注入 → `patch`，硬编码配置 → `patch`

---

## 审查结果汇总模板

```markdown
### Java Standards Auditor — 审查结果

**检查规则:** 10 条 | **通过:** X 条 | **不通过:** Y 条

| 规则 | 状态 | 严重级别 | 发现 | 位置 |
|------|------|---------|------|------|
| R1 SRP | PASS/FAIL | - / patch / critical | 具体问题描述 | 类名:行号 |
| R2 OCP | PASS/FAIL | ... | ... | ... |
| R3 模式 | PASS/FAIL | ... | ... | ... |
| R4 规范 | PASS/FAIL | ... | ... | ... |
| R5 类注释 | PASS/FAIL | ... | ... | ... |
| R6 方法注释 | PASS/FAIL | ... | ... | ... |
| R7 日志规格 | PASS/FAIL | ... | ... | ... |
| R8 DRY 复用 | PASS/FAIL | ... | ... | ... |
| R9 防御性编程 | PASS/FAIL | ... | ... | ... |
| R10 依赖注入 | PASS/FAIL | ... | ... | ... |

**总结:** [所有通过 / 存在 patch 级问题需修复 / 存在 critical 级问题需重构]
```
