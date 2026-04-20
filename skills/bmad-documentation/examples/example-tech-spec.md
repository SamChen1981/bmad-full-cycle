# 少样本示例：接口定义 + 数据库 DDL
# 用途: 作为 LLM 生成技术规格的参考范本, 展示"合格的接口定义和 DDL 长什么样"

---

## 示例 1: 完整接口定义（订单创建）

### POST /api/v1/orders

- **功能：** 创建订单
- **Content-Type：** `application/json`
- **认证：** Bearer Token (必须)
- **限流：** 单用户 10 次/分钟

**Request Body：**
```json
{
  "userId": "10001",
  "items": [
    {
      "productId": "P20260001",
      "skuId": "SKU001",
      "quantity": 2
    },
    {
      "productId": "P20260002",
      "skuId": null,
      "quantity": 1
    }
  ],
  "addressId": "ADDR_001",
  "couponId": "CPN_2026042001",
  "remark": "请在工作日送达"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| userId | string | Y | 非空 | 用户 ID |
| items | array | Y | minSize=1, maxSize=50 | 商品列表 |
| items[].productId | string | Y | 非空 | 商品 ID |
| items[].skuId | string | N | - | SKU ID，无规格商品传 null |
| items[].quantity | integer | Y | min=1, max=999 | 购买数量 |
| addressId | string | Y | 非空 | 收货地址 ID |
| couponId | string | N | - | 优惠券 ID |
| remark | string | N | maxLength=200 | 订单备注 |

**Response (200 OK) — 创建成功：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "orderId": "1234567890",
    "orderNo": "ORD20260420154532001",
    "totalAmount": 299.80,
    "payAmount": 269.80,
    "couponDiscount": 30.00,
    "status": "CREATED",
    "createdAt": "2026-04-20T15:45:32+08:00",
    "expireAt": "2026-04-20T16:15:32+08:00"
  }
}
```

**Response (400) — 库存不足：**
```json
{
  "code": 40001,
  "message": "商品库存不足",
  "data": {
    "productId": "P20260001",
    "availableStock": 1,
    "requestedQuantity": 2
  }
}
```

**Response (400) — 优惠券不可用：**
```json
{
  "code": 40002,
  "message": "优惠券不可用：已过期",
  "data": {
    "couponId": "CPN_2026042001",
    "reason": "EXPIRED",
    "expiredAt": "2026-04-19T23:59:59+08:00"
  }
}
```

**Response (500) — 系统异常：**
```json
{
  "code": 50001,
  "message": "订单创建失败，请稍后重试",
  "data": null
}
```

---

## 示例 2: 完整 SQL DDL（订单表）

```sql
-- ============================================
-- 订单主表
-- 业务说明: 存储用户订单核心信息
-- 创建时间: 2026-04-20
-- ============================================
CREATE TABLE `t_order` (
    `id`              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键 ID',
    `order_no`        VARCHAR(32)     NOT NULL                              COMMENT '订单编号，格式: ORDyyyyMMddHHmmssSSS + 3位随机数',
    `user_id`         BIGINT          NOT NULL                              COMMENT '用户 ID',
    `status`          TINYINT         NOT NULL DEFAULT 0                    COMMENT '订单状态: 0-待支付, 1-已支付, 2-已发货, 3-已完成, 4-已取消, 5-退款中, 6-已退款',
    `total_amount`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00                 COMMENT '商品总金额（优惠前）',
    `pay_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00                 COMMENT '实际支付金额（优惠后）',
    `coupon_id`       BIGINT          DEFAULT NULL                          COMMENT '优惠券 ID，未使用优惠券为 NULL',
    `coupon_discount` DECIMAL(10,2)   NOT NULL DEFAULT 0.00                 COMMENT '优惠券抵扣金额',
    `address_id`      BIGINT          NOT NULL                              COMMENT '收货地址 ID',
    `remark`          VARCHAR(200)    DEFAULT NULL                          COMMENT '订单备注',
    `pay_time`        DATETIME        DEFAULT NULL                          COMMENT '支付时间',
    `ship_time`       DATETIME        DEFAULT NULL                          COMMENT '发货时间',
    `complete_time`   DATETIME        DEFAULT NULL                          COMMENT '完成时间',
    `expire_at`       DATETIME        NOT NULL                              COMMENT '支付过期时间（创建后 30 分钟）',
    `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP    COMMENT '创建时间',
    `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`         TINYINT         NOT NULL DEFAULT 0                    COMMENT '逻辑删除: 0-未删除, 1-已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_expire_at` (`expire_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单主表';

-- ============================================
-- 订单明细表
-- 业务说明: 存储订单中的商品明细
-- ============================================
CREATE TABLE `t_order_item` (
    `id`              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键 ID',
    `order_id`        BIGINT          NOT NULL                              COMMENT '订单 ID',
    `order_no`        VARCHAR(32)     NOT NULL                              COMMENT '订单编号（冗余，便于查询）',
    `product_id`      BIGINT          NOT NULL                              COMMENT '商品 ID',
    `product_name`    VARCHAR(128)    NOT NULL                              COMMENT '商品名称（下单时快照）',
    `sku_id`          BIGINT          DEFAULT NULL                          COMMENT 'SKU ID',
    `sku_name`        VARCHAR(64)     DEFAULT NULL                          COMMENT 'SKU 名称（下单时快照）',
    `unit_price`      DECIMAL(10,2)   NOT NULL                              COMMENT '商品单价（下单时快照）',
    `quantity`        INT             NOT NULL                              COMMENT '购买数量',
    `subtotal`        DECIMAL(10,2)   NOT NULL                              COMMENT '小计金额 = unit_price * quantity',
    `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP    COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_order_no` (`order_no`),
    KEY `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单明细表';
```

---

## 示例 3: 完整异常错误码表

| 错误码 | HTTP 状态 | 错误常量 | 触发条件 | 处理建议 |
| :--- | :--- | :--- | :--- | :--- |
| 40001 | 400 | `ERR_STOCK_NOT_ENOUGH` | 商品库存不足（库存 < 请求数量） | 提示用户减少数量或选择其他商品 |
| 40002 | 400 | `ERR_COUPON_INVALID` | 优惠券不可用（过期/已使用/不满足门槛） | 提示用户移除优惠券，返回 reason 字段 |
| 40003 | 400 | `ERR_ADDRESS_NOT_FOUND` | 收货地址不存在或已被删除 | 提示用户重新选择地址 |
| 40004 | 400 | `ERR_PRODUCT_OFF_SHELF` | 商品已下架 | 提示用户移除该商品 |
| 40005 | 400 | `ERR_ORDER_LIMIT_EXCEED` | 单次下单数量超过限制（>50 种商品） | 提示用户拆分订单 |
| 40006 | 400 | `ERR_DUPLICATE_ORDER` | 幂等检测：重复提交（相同幂等 Token） | 返回已有订单信息，不重复创建 |
| 40101 | 401 | `ERR_TOKEN_EXPIRED` | JWT Token 已过期 | 客户端刷新 Token 后重试 |
| 40301 | 403 | `ERR_USER_BLOCKED` | 用户账号被冻结 | 提示用户联系客服 |
| 42901 | 429 | `ERR_RATE_LIMIT` | 单用户下单频率超限（>10次/分钟） | 提示用户稍后重试 |
| 50001 | 500 | `ERR_ORDER_CREATE_FAIL` | 订单创建数据库异常 | 系统重试 + 告警通知运维 |
| 50002 | 500 | `ERR_PRICE_CALC_FAIL` | 价格计算服务异常 | 系统重试 + 降级使用原价 |
| 50003 | 500 | `ERR_MQ_SEND_FAIL` | 消息发送失败（订单事件） | 本地消息表补偿 + 告警 |

---

## 示例 4: 伪代码 + 防御性编程标注

```
function createOrder(request):
    // ===== 1. 参数校验 (Guard Clause) =====
    Objects.requireNonNull(request, "request 不能为 null")
    if request.items is empty:
        throw BizException(ERR_INVALID_PARAM, "商品列表不能为空")
    if request.items.size > 50:
        throw BizException(ERR_ORDER_LIMIT_EXCEED, "单次最多下单 50 种商品")

    // ===== 2. 幂等检查 =====
    // 防御: 前端传幂等 Token, Redis SETNX 检查
    if redis.exists("order:idempotent:" + request.idempotentToken):
        return existingOrder  // 返回已有订单，不重复创建
    redis.setex("order:idempotent:" + request.idempotentToken, 600)  // 10分钟过期

    // ===== 3. 库存检查与锁定 =====
    for item in request.items:
        // 防御: 悲观锁 SELECT ... FOR UPDATE, 防止超卖
        stock = inventoryService.checkAndLock(item.productId, item.quantity)
        if stock.insufficient:
            throw BizException(ERR_STOCK_NOT_ENOUGH, productId=item.productId)

    // ===== 4. 价格计算 =====
    // 防御: 价格服务异常时降级使用原价
    try:
        priceResult = priceService.calculate(request.items, request.couponId)
    catch (ServiceException e):
        log.warn("[订单创建][价格降级] couponId={}, 使用原价", request.couponId, e)
        priceResult = priceService.calculateWithoutCoupon(request.items)

    // ===== 5. 事务落库 =====
    @Transactional:
        order = buildOrder(request, priceResult)
        order.expireAt = now + 30 minutes
        orderMapper.insert(order)
        // 防御: 已知 size, 指定 ArrayList 初始容量
        orderItems = new ArrayList(request.items.size)
        for item in request.items:
            orderItems.add(buildOrderItem(order, item, priceResult))
        orderItemMapper.batchInsert(orderItems)
        if request.couponId:
            couponService.markUsed(request.couponId, order.id)

    // ===== 6. 异步通知 (MQ) =====
    // 防御: MQ 发送失败不影响主流程, 本地消息表兜底
    try:
        messageQueue.send("order.created", OrderCreatedEvent(order))
    catch (MQException e):
        log.error("[订单创建][MQ发送失败] orderId={}", order.id, e)
        localMessageTable.save(OrderCreatedEvent(order))  // 兜底: 定时任务补偿

    return OrderConverter.toVO(order)
```
