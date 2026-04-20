# Java 代码质量强制规范 — 完整版

本文档定义了 BMAD 开发流程中所有 Java 代码必须遵守的 8 条强制规则。dev-story 在生成代码时必须逐条执行，code-review 在审查时必须逐条验证。

---

## R1: 单一职责原则 (SRP)

### 类级别

每个类只承担一个职责，只有一个引起它变化的原因。

**强制要求：**
- Controller 只做参数校验和路由分发，不包含业务逻辑
- Service 只处理业务编排，不包含数据访问细节
- Repository/Mapper 只做数据持久化，不包含业务判断
- DTO/VO/Entity 只做数据承载，不包含业务方法
- 工具类（Util）只做无状态的通用计算，不依赖 Spring Bean

**违规判定：** 一个类中出现两种以上职责（如 Service 里直接写 SQL、Controller 里写业务逻辑）→ 必须拆分。

### 方法级别

每个方法只做一件事，方法名精确描述这件事。

**强制要求：**
- 方法体不超过 50 行（不含注释和空行）
- 方法参数不超过 5 个，超过则封装为对象
- 方法只有一个抽象层次 — 高层方法调用低层方法，不混合抽象层次
- 方法命名使用动词开头：`createOrder`、`validateUser`、`calculateAmount`

**违规示例：**
```java
// 错误：一个方法里既做校验又做创建又做通知
public void handleOrder(OrderDTO dto) {
    // 校验 (职责1)
    if (dto.getAmount() <= 0) throw new BizException(...);
    // 创建 (职责2)
    Order order = new Order(); ...
    orderMapper.insert(order);
    // 通知 (职责3)
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

**强制要求：**
- 业务类型分支（if-else / switch）不超过 3 个。超过时必须抽象为接口 + 多实现
- 新增功能通过实现接口或继承抽象类完成，不修改已有 Service 主逻辑
- 配置项变化通过外部化配置实现，不硬编码在代码中

**模式应用：**
```java
// 定义扩展点接口
public interface PaymentStrategy {
    PaymentResult pay(PaymentRequest request);
    String getPaymentType();
}

// 新增支付方式 = 新增一个实现类，不改任何已有代码
@Component
public class AlipayStrategy implements PaymentStrategy {
    @Override
    public String getPaymentType() { return "ALIPAY"; }
    @Override
    public PaymentResult pay(PaymentRequest request) { ... }
}
```

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
        // 发送逻辑
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

**4. 业务调用方 — 无 if-else**
```java
public SendResult sendMessage(String type, Message message) {
    // 工厂路由 + 策略执行，调用方无需知道具体实现
    MessageStrategy strategy = messageStrategyFactory.getStrategy(type);
    return strategy.send(message);
}
```

**强制要求：**
- 出现 3 个以上类型分支时必须使用此模式
- 工厂使用 Spring 依赖注入自动收集所有实现，禁止手动 new
- 新增类型只需要新增实现类，禁止修改工厂或调用方代码

---

## R4: Java 编程规范

严格遵守以下规范，优先级从高到低。

### 命名规范
- 类名：UpperCamelCase，如 `OrderService`、`PaymentStrategyFactory`
- 方法名：lowerCamelCase，动词开头，如 `createOrder`、`validateUser`
- 常量：UPPER_SNAKE_CASE，如 `MAX_RETRY_COUNT`
- 包名：全小写，如 `com.example.order.service`
- 布尔变量/方法：`is/has/can/should` 开头，如 `isValid`、`hasPermission`
- 枚举值：UPPER_SNAKE_CASE，如 `OrderStatus.PAID`

### 代码结构
- 类内部顺序：常量 → 静态变量 → 实例变量 → 构造方法 → 公开方法 → 私有方法
- import 不使用通配符 `*`
- 每个类一个文件
- 方法之间空一行
- 大括号不换行（K&R 风格）

### 异常处理
- 禁止 `catch (Exception e) {}` 空处理
- 异常必须记录日志或向上抛出
- 业务异常使用自定义 BizException，携带错误码
- 禁止在 finally 中 return

### 空值处理
- 方法返回集合时返回空集合，不返回 null
- 使用 `Optional` 处理可能为空的单值返回
- 外部输入（参数、接口返回值）必须做 null 检查

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
 * @modified 2026-05-10 lisi 修复并发下单时库存扣减竞态问题
 */
public class OrderService {
```

**强制要求：**
- `@author` — 创建者姓名（从项目配置 user_name 读取）
- `@since` — 创建日期，格式 yyyy-MM-dd
- `@modified` — 每次重大变更添加一行，格式：`日期 作者 变更说明`
- 类描述第一行是一句话概述，后续用 `<p>` 补充职责边界
- 接口/抽象类额外说明设计意图和扩展方式

**枚举类额外要求：**
```java
/**
 * 订单状态枚举
 *
 * @author zhangsan
 * @since 2026-04-20
 */
public enum OrderStatus {
    /** 待支付 */
    PENDING_PAYMENT,
    /** 已支付 */
    PAID,
    /** 已发货 */
    SHIPPED;
}
```

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
 * @author zhangsan
 * @since 2026-04-20
 */
public OrderVO createOrder(CreateOrderRequest request) {
```

### 过程注释

复杂逻辑的关键步骤必须添加行内注释：

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
- **方法入口** — INFO 级别，记录关键入参
- **关键分支决策** — INFO/DEBUG 级别，记录走了哪个分支
- **外部调用前后** — INFO 级别，记录调用参数和返回结果
- **异常捕获** — ERROR/WARN 级别，记录完整异常信息
- **方法出口** — INFO 级别（仅对重要业务方法），记录关键结果

```java
public OrderVO createOrder(CreateOrderRequest request) {
    log.info("[订单创建][入参] userId={}, itemCount={}, totalAmount={}",
             request.getUserId(), request.getItems().size(), request.getTotalAmount());

    validateCreateRequest(request);

    // 库存预占
    log.info("[订单创建][库存扣减] 开始扣减, items={}", request.getItems().size());
    lockAndDeductStock(request.getItems());
    log.info("[订单创建][库存扣减] 扣减成功");

    Order order = buildOrder(request);
    orderRepository.save(order);
    log.info("[订单创建][持久化] 订单已保存, orderId={}, orderNo={}",
             order.getId(), order.getOrderNo());

    asyncNotifyOrderCreated(order);

    log.info("[订单创建][完成] orderId={}, orderNo={}, status={}",
             order.getId(), order.getOrderNo(), order.getStatus());
    return OrderConverter.toVO(order);
}
```

---

## R7: 日志规格

### 格式规范

统一日志格式：`[模块名][操作名][关键参数]` + 描述

```
[订单创建][库存扣减][orderId=12345] 开始扣减库存, itemCount=3
[用户认证][登录校验][userId=10001] 密码校验通过, 生成 token
[支付回调][状态更新][tradeNo=PAY2026042012345] 支付成功, 更新订单状态为 PAID
```

### 级别划分

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| **ERROR** | 系统异常、不可恢复的错误、需要人工干预 | 数据库连接失败、第三方接口超时 |
| **WARN** | 可恢复的异常、潜在问题、降级处理 | 缓存穿透、重试成功、兜底逻辑触发 |
| **INFO** | 关键业务节点、状态变化、外部调用 | 订单创建/支付、用户登录、接口调用结果 |
| **DEBUG** | 开发调试信息、中间计算结果 | SQL 参数、缓存命中情况、条件判断细节 |

### 强制禁止

- 禁止使用 `System.out.println` 输出日志
- 禁止在日志中打印完整密码、身份证号、银行卡号等敏感信息
- 禁止在循环内打印大量 INFO 日志（改用 DEBUG 或汇总后打印）
- 禁止 `log.error("error")` 无上下文信息 — 必须包含关键参数和异常栈
- 异常日志必须使用 `log.error("[模块][操作] 描述, param={}", value, exception)` 传递异常对象

```java
// 错误
log.error("创建订单失败");
log.error("创建订单失败: " + e.getMessage());

// 正确
log.error("[订单创建][持久化失败] userId={}, itemCount={}", request.getUserId(), request.getItems().size(), e);
```

---

## R8: 代码复用

### 强制要求

- **禁止复制粘贴**：发现两处以上相似代码，必须提取公共方法或工具类
- **通用逻辑提取**：参数校验、分页处理、统一响应封装等使用项目级基类或工具类
- **模板方法模式**：相似业务流程使用模板方法抽象公共骨架，子类实现差异步骤
- **继承/组合复用**：优先使用组合（持有引用），避免深层继承（超过 3 层）

### 复用层次

```
项目级工具类 (xxxUtils)         ← 无状态通用方法
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

        // 1. 参数校验（公共逻辑）
        validateRequest(request);

        // 2. 查询数据（子类实现）
        List<T> data = queryData(request);
        log.info("[数据导出][{}][查询完成] dataSize={}", getExportType(), data.size());

        // 3. 转换格式（子类实现）
        byte[] content = convertToBytes(data, request.getFormat());

        // 4. 上传文件（公共逻辑）
        String url = uploadFile(content, request.getFileName());
        log.info("[数据导出][{}][完成] fileUrl={}", getExportType(), url);

        return ExportResult.success(url);
    }

    protected abstract String getExportType();
    protected abstract List<T> queryData(ExportRequest request);
    protected abstract byte[] convertToBytes(List<T> data, String format);

    // 公共方法供所有子类复用
    private void validateRequest(ExportRequest request) { ... }
    private String uploadFile(byte[] content, String fileName) { ... }
}
```

---

## 在 BMAD 流程中的执行时机

| 阶段 | 检查内容 |
|------|---------|
| **dev-story Step 5** | 生成每个 Java 文件前，按 R1-R8 逐条执行 |
| **dev-story Step 7** | 验证生成代码符合 R4 命名规范和 R7 日志规格 |
| **code-review Step 2** | Java Standards Auditor 使用 review-checklist.md 逐条审查 |
| **code-review Step 3** | 不满足 R1-R8 的项标记为 patch（可自动修复）或 critical（需重构） |
