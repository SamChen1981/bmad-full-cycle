# Java 代码质量守护规范 — 完整版

本文档定义了 BMAD 开发流程中所有 Java 代码必须遵守的 10 条强制规则。相比通用描述，每条规则都给出了量化指标和具体技术约束，让 AI 可以精准执行而非模糊判断。

dev-story 在生成代码时必须逐条执行，code-review 在审查时必须逐条验证。

---

## R1: 单一职责原则 (SRP)

### 量化硬限制

| 指标 | 上限 | 超过后处理 |
|------|------|-----------|
| 类文件行数（含注释） | 300 行 | 必须拆分为内部类或独立文件 |
| 方法体行数（不含注释和空行） | 50 行 | 必须提取子方法 |
| 方法参数个数 | 5 个 | 必须封装为 Request/Param 对象 |
| 类的依赖注入数量 | 7 个 | 超过说明职责过多，必须拆分 |

### 层级职责边界

| 层级 | 允许做的事 | 严禁做的事 |
|------|-----------|-----------|
| Controller | 参数校验、路由分发、响应封装 | 业务逻辑、数据访问、事务管理 |
| Service | 业务编排、事务控制、调用其他 Service | 直接写 SQL、操作 HttpServletRequest |
| Repository/Mapper | 数据持久化、SQL 映射 | 业务判断、调用其他 Service |
| DTO/VO/Entity | 数据承载 | 业务方法（getter/setter/builder 除外） |
| Util | 无状态通用计算 | 依赖 Spring Bean、维护可变状态 |

### 方法级别

每个方法只做一件事，方法名精确描述这件事。方法只有一个抽象层次 — 高层方法调用低层方法，不混合抽象层次。

```java
// 错误：一个方法里既做校验又做创建又做通知
public void handleOrder(OrderDTO dto) {
    if (dto.getAmount() <= 0) throw new BizException(...);
    Order order = new Order(); ...
    orderMapper.insert(order);
    messageSender.send(...);
}

// 正确：拆分为三个单一职责方法
public void handleOrder(OrderDTO dto) {
    validateOrder(dto);
    Order order = createOrder(dto);
    notifyOrderCreated(order);
}
```

---

## R2: 开闭原则 (OCP)

对扩展开放，对修改关闭。新增业务类型时，不修改已有代码，而是新增实现类。

### 量化约束

| 代码异味 | 阈值 | 处理 |
|---------|------|------|
| 同一方法中 if-else 类型判断分支 | ≤3 个 | 允许 |
| 同一方法中 if-else 类型判断分支 | 4-5 个 | `patch`：建议重构为策略模式 |
| 同一方法中 if-else 类型判断分支 | >5 个 | `critical`：强制重构为策略模式 |
| switch-case 用于类型路由 | ≤3 个 case | 允许 |
| switch-case 用于类型路由 | >3 个 case | 强制重构为工厂 + 策略 |
| if-else 嵌套层级 | >3 层 | 强制用卫语句（early return）拍平 |

**强制要求：**
- 新增功能通过实现接口或继承抽象类完成，不修改已有 Service 主逻辑
- 配置项变化通过外部化配置（application.yml / Nacos）实现，不硬编码在代码中
- 魔法数字（magic number）必须提取为常量或枚举

---

## R3: 设计模式组合 — 工厂 + 策略

当业务中存在"按类型执行不同逻辑"的场景时，强制使用工厂模式 + 策略模式的组合。

### 标准实现模板

**1. 策略接口**
```java
/**
 * 消息发送策略接口
 *
 * @author {developer}
 * @since {date}
 */
public interface MessageStrategy {
    /**
     * 执行消息发送
     * @param message 消息内容
     * @return 发送结果
     */
    SendResult send(Message message);

    /**
     * 返回本策略支持的消息类型
     */
    String getType();
}
```

**2. 策略实现（每种类型一个类 — 符合 SRP + OCP）**
```java
/**
 * 短信消息发送策略
 *
 * @author {developer}
 * @since {date}
 */
@Slf4j
@Component
public class SmsMessageStrategy implements MessageStrategy {
    @Override
    public String getType() { return "SMS"; }

    @Override
    public SendResult send(Message message) {
        log.info("[消息发送][SMS][messageId={}] 开始发送短信", message.getId());
        // 发送逻辑...
        log.info("[消息发送][SMS][messageId={}] 发送完成, result={}", message.getId(), result);
        return result;
    }
}
```

**3. 策略工厂（Spring 自动注入所有实现）**
```java
/**
 * 消息策略工厂 — 根据类型路由到对应策略实现
 *
 * <p>新增消息类型只需新增 MessageStrategy 实现类并加 @Component，
 * 工厂自动收集，无需修改本类。</p>
 *
 * @author {developer}
 * @since {date}
 */
@Slf4j
@Component
public class MessageStrategyFactory {
    private final Map<String, MessageStrategy> strategyMap;

    /**
     * Spring 自动注入所有 MessageStrategy 实现，构建类型映射表
     */
    public MessageStrategyFactory(List<MessageStrategy> strategies) {
        this.strategyMap = strategies.stream()
            .collect(Collectors.toMap(MessageStrategy::getType, Function.identity()));
        log.info("[消息策略工厂][初始化] 已注册策略类型: {}", strategyMap.keySet());
    }

    /**
     * 根据消息类型获取对应策略
     * @param type 消息类型
     * @return 对应的策略实现
     * @throws UnsupportedOperationException 类型不支持时抛出
     */
    public MessageStrategy getStrategy(String type) {
        MessageStrategy strategy = strategyMap.get(type);
        if (strategy == null) {
            log.error("[消息策略工厂][路由失败] 不支持的消息类型: {}", type);
            throw new UnsupportedOperationException("不支持的消息类型: " + type);
        }
        return strategy;
    }
}
```

**4. 业务调用方 — 零 if-else**
```java
public SendResult sendMessage(String type, Message message) {
    MessageStrategy strategy = messageStrategyFactory.getStrategy(type);
    return strategy.send(message);
}
```

**强制要求：**
- 出现 3 个以上类型分支时必须使用此模式
- 工厂使用 Spring 构造函数注入自动收集所有实现，严禁手动 new
- 新增类型只需要新增实现类 + @Component，禁止修改工厂或调用方代码

---

## R4: Java 编程规范

基准标准：**《阿里巴巴 Java 开发手册》（嵩山版）** + **Google Java Style Guide**。以下为关键条目。

### 命名规范
- 类名：UpperCamelCase — `OrderService`、`PaymentStrategyFactory`
- 方法名：lowerCamelCase，动词开头 — `createOrder`、`validateUser`
- 常量：UPPER_SNAKE_CASE — `MAX_RETRY_COUNT`、`DEFAULT_PAGE_SIZE`
- 包名：全小写 — `com.example.order.service`
- 布尔变量/方法：`is/has/can/should` 开头 — `isValid`、`hasPermission`
- 枚举值：UPPER_SNAKE_CASE — `OrderStatus.PAID`
- 抽象类：`Abstract` 开头 — `AbstractExportTemplate`
- 异常类：`Exception` 结尾 — `BizException`、`OrderNotFoundException`
- 测试类：`Test` 结尾 — `OrderServiceTest`

### 代码结构
- 类内部顺序：常量 → 静态变量 → 实例变量 → 构造方法 → 公开方法 → 私有方法
- import 不使用通配符 `*`
- 每个类一个文件
- 方法之间空一行
- 大括号不换行（K&R 风格）

### 异常处理
- 严禁 `catch (Exception e) {}` 空处理
- 异常必须记录日志或向上抛出，二者必取其一
- 业务异常使用自定义 BizException，携带 ErrorCode 枚举
- 严禁在 finally 中 return
- 严禁用异常做流程控制（如用 catch 代替 if 判断）

### 魔法值禁令
- 严禁在代码中直接使用数字或字符串字面量做判断
- 必须提取为常量或枚举：`if (status == OrderStatus.PAID)` 而非 `if (status == 1)`

---

## R5: 类头部注释规范

每个 Java 类文件必须包含以下格式的头部注释：

```java
/**
 * 订单服务 — 处理订单创建、查询和状态流转的核心业务逻辑
 *
 * <p>职责边界：只负责订单领域的业务编排，数据持久化委托给 OrderRepository，
 * 消息通知委托给 NotificationService。</p>
 *
 * @author zhangsan
 * @since 2026-04-20
 * @modified 2026-04-25 zhangsan 增加批量创建订单功能
 */
public class OrderService {
```

**强制要求：**
- `@author` — 创建者（从项目配置 user_name 读取，AI 生成时标注 `AI Assistant`）
- `@since` — 创建日期，格式 yyyy-MM-dd
- `@modified` — 仅在修改核心逻辑时添加（不是每次 format 都加），格式：`日期 作者 变更说明`
- 类描述第一行是一句话概述，后续用 `<p>` 补充职责边界
- 接口/抽象类额外说明设计意图和扩展方式
- 枚举的每个值必须有单行 Javadoc

**注意：** 常规重构（rename、移动代码位置）不需要添加 `@modified`，变更历史交给 Git。只有修改类的业务语义时才加。

---

## R6: 方法注释 + 过程注释 + 关键节点日志

### 方法头部注释（Javadoc）

每个 public/protected 方法必须有 Javadoc：

```java
/**
 * 创建订单并扣减库存
 *
 * <p>执行流程：参数校验 → 库存预占 → 创建订单 → 发送通知</p>
 *
 * @param request 订单创建请求，包含商品列表和收货地址
 * @return 创建成功的订单信息
 * @throws BizException 库存不足(ERROR_STOCK_INSUFFICIENT) 或参数无效(ERROR_INVALID_PARAM)
 */
public OrderVO createOrder(CreateOrderRequest request) {
```

### 过程注释

复杂逻辑的关键步骤（>10 行的逻辑块）前必须添加编号注释：

```java
public OrderVO createOrder(CreateOrderRequest request) {
    // 1. 参数校验
    validateCreateRequest(request);

    // 2. 库存预占（悲观锁，防止超卖）
    lockAndDeductStock(request.getItems());

    // 3. 生成订单（含订单号生成、金额计算）
    Order order = buildOrder(request);
    orderRepository.save(order);

    // 4. 异步通知（不阻塞主流程）
    asyncNotifyOrderCreated(order);

    return OrderConverter.toVO(order);
}
```

### 关键节点日志

每个业务方法在以下节点必须输出日志：

| 节点 | 级别 | 内容 |
|------|------|------|
| 方法入口 | INFO | 关键入参（脱敏） |
| 关键分支决策 | INFO/DEBUG | 走了哪个分支 |
| 外部调用前后 | INFO | 调用参数 + 返回结果/耗时 |
| 异常捕获 | ERROR/WARN | 完整异常 + 上下文参数 |
| 方法出口（重要业务方法） | INFO | 关键结果 + 耗时 |

```java
public OrderVO createOrder(CreateOrderRequest request) {
    long startTime = System.currentTimeMillis();
    log.info("[订单创建][入参] userId={}, itemCount={}, totalAmount={}",
             request.getUserId(), request.getItems().size(), request.getTotalAmount());

    validateCreateRequest(request);

    log.info("[订单创建][库存扣减] 开始扣减, items={}", request.getItems().size());
    lockAndDeductStock(request.getItems());

    Order order = buildOrder(request);
    orderRepository.save(order);
    log.info("[订单创建][持久化] orderId={}, orderNo={}", order.getId(), order.getOrderNo());

    asyncNotifyOrderCreated(order);

    log.info("[订单创建][完成] orderId={}, cost={}ms",
             order.getId(), System.currentTimeMillis() - startTime);
    return OrderConverter.toVO(order);
}
```

---

## R7: 日志规格

### 技术选型

- **日志框架：** 强制使用 `org.slf4j.Logger`（SLF4J 门面 + Logback 实现）
- **日志声明：** `private static final Logger log = LoggerFactory.getLogger(Xxx.class);` 或使用 Lombok `@Slf4j`
- **严禁：** `System.out.println`、`System.err.println`、`e.printStackTrace()`

### 格式规范

统一日志格式：`[模块名][操作名][关键参数]` + 描述

```
[订单创建][库存扣减][orderId=12345] 开始扣减库存, itemCount=3
[用户认证][登录校验][userId=10001] 密码校验通过, 生成 token
[支付回调][状态更新][tradeNo=PAY2026042012345] 支付成功, 更新订单状态
```

### TraceId 规范

在分布式环境中，通过 MDC 传递 TraceId，确保链路可追踪：

```java
// 在拦截器/过滤器中设置
MDC.put("traceId", UUID.randomUUID().toString().replace("-", ""));

// logback.xml pattern 包含 traceId
// %d{yyyy-MM-dd HH:mm:ss.SSS} [%X{traceId}] [%-5level] [%thread] %logger{36} - %msg%n
```

### 占位符规范

- 正确：`log.info("用户下单成功, orderId: {}", orderId);`
- 错误：`log.info("用户下单成功, orderId: " + orderId);` （字符串拼接浪费性能）

### 级别划分

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| **ERROR** | 系统异常、不可恢复的错误、需要人工干预 | 数据库连接失败、第三方接口持续超时 |
| **WARN** | 可恢复的异常、潜在问题、降级处理 | 缓存穿透、重试后成功、兜底逻辑触发 |
| **INFO** | 关键业务节点、状态变化、外部调用 | 订单创建/支付、用户登录、接口调用结果 |
| **DEBUG** | 开发调试信息、中间计算结果 | SQL 参数、缓存命中情况、条件判断细节 |

### 强制禁止

- 严禁在日志中打印完整密码、身份证号、银行卡号等敏感信息（必须脱敏）
- 严禁在循环内打印大量 INFO 日志（改用 DEBUG 或循环结束后汇总）
- 严禁 `log.error("error")` 无上下文信息 — 必须包含关键参数和异常对象
- 异常日志必须传递异常对象作为最后一个参数：

```java
// 错误
log.error("创建订单失败");
log.error("创建订单失败: " + e.getMessage());

// 正确
log.error("[订单创建][持久化失败] userId={}, itemCount={}", userId, itemCount, e);
```

---

## R8: 代码复用 (DRY — Don't Repeat Yourself)

### 工具类优先级

在编写通用逻辑前，必须按以下优先级寻找已有实现：

```
1. java.util / java.time (JDK 自带)          ← 最优先
2. org.apache.commons (commons-lang3, commons-collections4, commons-io)
3. com.google.common (Guava)
4. 项目级工具类 (XxxUtils)                    ← 如果以上都不满足才新建
```

**强制禁止重复造轮子的场景：**
- 字符串判空 → 用 `StringUtils.isBlank()` 而非手写 `s == null || s.trim().isEmpty()`
- 集合判空 → 用 `CollectionUtils.isEmpty()` 而非手写
- 日期处理 → 用 `java.time` (LocalDateTime/LocalDate)，严禁使用 `java.util.Date`
- Bean 拷贝 → 用 `BeanUtils.copyProperties()` 或 MapStruct，严禁逐字段手写赋值
- JSON 处理 → 统一用项目已有的 Jackson/Fastjson 工具类

### 复用层次

```
项目级工具类 (XxxUtils)         ← 无状态通用方法
    ↓
基类/抽象类 (AbstractXxxService) ← 模板方法 + 公共逻辑
    ↓
接口 + 策略实现                   ← 工厂 + 策略模式复用结构
    ↓
Spring Bean 组合                  ← 通过依赖注入复用已有 Bean
```

### 模板方法示例

```java
/**
 * 数据导出模板 — 定义导出流程骨架，子类实现具体数据查询和格式转换
 *
 * @author {developer}
 * @since {date}
 */
public abstract class AbstractExportTemplate<T> {

    /**
     * 导出流程模板（骨架不可修改）
     */
    public final ExportResult export(ExportRequest request) {
        log.info("[数据导出][{}][开始] params={}", getExportType(), request);
        long startTime = System.currentTimeMillis();

        // 1. 参数校验（公共逻辑）
        validateRequest(request);

        // 2. 查询数据（子类实现）
        List<T> data = queryData(request);
        log.info("[数据导出][{}][查询完成] dataSize={}", getExportType(), data.size());

        // 3. 转换格式（子类实现）
        byte[] content = convertToBytes(data, request.getFormat());

        // 4. 上传文件（公共逻辑）
        String url = uploadFile(content, request.getFileName());
        log.info("[数据导出][{}][完成] fileUrl={}, cost={}ms",
                 getExportType(), url, System.currentTimeMillis() - startTime);

        return ExportResult.success(url);
    }

    protected abstract String getExportType();
    protected abstract List<T> queryData(ExportRequest request);
    protected abstract byte[] convertToBytes(List<T> data, String format);
}
```

### 量化约束

- 发现两处以上相似代码（>5 行重复）→ 必须提取公共方法或工具类
- 继承层次不超过 3 层，优先使用组合（依赖注入）而非继承
- 相似业务流程（>3 个子类有相同骨架）→ 使用模板方法模式

---

## R9: 防御性编程

### 参数校验前置

所有 public 方法的入口处必须做参数校验，使用卫语句（early return / early throw）：

```java
public OrderVO createOrder(CreateOrderRequest request) {
    // 卫语句：先排除非法情况
    Objects.requireNonNull(request, "request 不能为 null");
    if (CollectionUtils.isEmpty(request.getItems())) {
        throw new BizException(ErrorCode.INVALID_PARAM, "商品列表不能为空");
    }
    if (request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
        throw new BizException(ErrorCode.INVALID_PARAM, "金额必须大于零");
    }
    // 正常业务逻辑...
}
```

### 空指针防护

| 场景 | 强制做法 |
|------|---------|
| 方法返回集合 | 返回 `Collections.emptyList()` 而非 null |
| 方法返回单个对象（可能不存在） | 使用 `Optional<T>` |
| 外部输入（Controller 参数、RPC 返回值） | 使用 `Objects.requireNonNull()` 或 `@NotNull` 注解 |
| 字符串判空 | 使用 `StringUtils.isBlank()` |
| 集合判空 | 使用 `CollectionUtils.isEmpty()` |
| Map 取值 | 使用 `map.getOrDefault(key, defaultValue)` |

### 资源管理

- IO 流、数据库连接、HTTP 客户端等必须使用 **try-with-resources** 语法
- 严禁在 catch 块中只打印 `e.getMessage()` 而吞掉异常栈

```java
// 正确
try (InputStream is = new FileInputStream(file);
     BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
    // 处理逻辑
} catch (IOException e) {
    log.error("[文件读取][失败] filePath={}", file.getPath(), e);
    throw new BizException(ErrorCode.FILE_READ_ERROR, "文件读取失败", e);
}
```

### 集合初始化

创建 ArrayList/HashMap 时必须指定初始容量（已知大小时），避免频繁扩容：

```java
// 正确
List<OrderVO> result = new ArrayList<>(orderList.size());
Map<String, User> userMap = new HashMap<>(userList.size() * 4 / 3 + 1);

// 错误
List<OrderVO> result = new ArrayList<>();  // 未知大小时可以，已知大小时不行
```

---

## R10: 依赖注入纪律

### 严禁在业务类中 new 依赖对象

```java
// 错误：手动创建依赖
@Service
public class OrderService {
    private UserService userService = new UserServiceImpl();  // 严禁!
}

// 正确：构造函数注入
@Service
@RequiredArgsConstructor
public class OrderService {
    private final UserService userService;
    private final OrderRepository orderRepository;
    private final MessageStrategyFactory messageStrategyFactory;
}
```

### 注入方式优先级

1. **构造函数注入**（推荐，配合 `@RequiredArgsConstructor`）— 字段声明为 `private final`
2. **方法注入** `@Autowired` on setter — 仅用于可选依赖
3. **字段注入** `@Autowired` on field — 禁止使用（无法写单元测试）

### 配置值注入

- 从 application.yml 读取的配置使用 `@Value` 或 `@ConfigurationProperties`
- 严禁在代码中硬编码 URL、端口、密码、阈值等可变配置

---

## 在 BMAD 流程中的执行时机

| 阶段 | 检查内容 |
|------|---------|
| **dev-story Step 5** | 生成每个 Java 文件前，按 R1-R10 逐条执行 + 输出前自审清单 |
| **dev-story Step 7** | 验证生成代码符合 R4 命名规范、R7 日志规格、R9 防御性编程 |
| **code-review Step 2** | Java Standards Auditor 使用 review-checklist.md 逐条审查 |
| **code-review Step 3** | 不满足 R1-R10 的项标记为 patch（可自动修复）或 critical（需重构） |
| **Gatekeeper** | implementation 阶段结束时自动运行静态检测脚本 |
