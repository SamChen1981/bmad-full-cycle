# 少样本示例：Mermaid 图表
# 用途: 作为 LLM 生成架构图表的参考范本, 展示各类 Mermaid 图表的标准写法

---

## 示例 1: 系统组件图（分层架构）

```mermaid
graph TD
    Client[客户端 / 小程序 / H5] --> Gateway[API 网关<br/>Spring Cloud Gateway]
    Gateway --> Auth[认证服务<br/>JWT + Redis]
    Gateway --> OrderSvc[订单服务]
    Gateway --> ProductSvc[商品服务]
    Gateway --> UserSvc[用户服务]

    OrderSvc --> OrderDB[(订单库<br/>MySQL)]
    OrderSvc --> Cache[(Redis 缓存)]
    OrderSvc --> MQ[RocketMQ]

    ProductSvc --> ProductDB[(商品库<br/>MySQL)]
    ProductSvc --> Cache
    ProductSvc --> ES[(Elasticsearch<br/>商品搜索)]

    UserSvc --> UserDB[(用户库<br/>MySQL)]

    MQ --> PaySvc[支付服务]
    MQ --> NotifySvc[通知服务]

    style Gateway fill:#4ECDC4,stroke:#333,color:#000
    style MQ fill:#FFE66D,stroke:#333,color:#000
    style Cache fill:#FF6B6B,stroke:#333,color:#fff
```

---

## 示例 2: 核心业务时序图（订单创建）

```mermaid
sequenceDiagram
    participant C as 客户端
    participant G as API 网关
    participant O as 订单服务
    participant I as 库存服务
    participant P as 价格服务
    participant DB as 订单数据库
    participant MQ as RocketMQ

    C->>G: POST /api/v1/orders
    G->>G: JWT 认证 + 限流检查
    G->>O: 转发请求

    O->>O: 1. 参数校验 (Guard Clause)

    O->>I: 2. 检查并锁定库存
    I->>I: SELECT ... FOR UPDATE
    I-->>O: 库存锁定结果

    alt 库存不足
        O-->>C: 400 ERR_STOCK_NOT_ENOUGH
    end

    O->>P: 3. 计算最终价格 (含优惠券)
    P-->>O: PriceResult

    O->>DB: 4. @Transactional 保存订单
    DB-->>O: orderId

    O->>MQ: 5. 发送 order.created 事件
    O-->>C: 200 OK {orderId, orderNo}

    Note over MQ: 异步消费
    MQ->>PaySvc: 生成待支付记录
    MQ->>NotifySvc: 发送下单通知
```

---

## 示例 3: ER 图（核心实体关系）

```mermaid
erDiagram
    USER ||--o{ ORDER : "下单"
    USER {
        bigint id PK
        varchar name
        varchar phone
        tinyint status
        datetime created_at
    }

    ORDER ||--|{ ORDER_ITEM : "包含"
    ORDER {
        bigint id PK
        varchar order_no UK
        bigint user_id FK
        tinyint status
        decimal total_amount
        decimal pay_amount
        bigint address_id
        datetime created_at
    }

    ORDER_ITEM }|--|| PRODUCT : "关联"
    ORDER_ITEM {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        int quantity
        decimal unit_price
        decimal subtotal
    }

    PRODUCT ||--o{ PRODUCT_SKU : "规格"
    PRODUCT {
        bigint id PK
        varchar name
        tinyint status
        decimal base_price
        int stock
    }

    PRODUCT_SKU {
        bigint id PK
        bigint product_id FK
        varchar sku_name
        decimal price
        int stock
    }
```

---

## 示例 4: 状态机流程图（订单状态流转）

```mermaid
stateDiagram-v2
    [*] --> CREATED: 用户下单
    CREATED --> PAID: 支付成功
    CREATED --> CANCELLED: 超时未支付 / 用户取消
    PAID --> SHIPPED: 商家发货
    PAID --> REFUNDING: 用户申请退款
    SHIPPED --> COMPLETED: 用户确认收货
    SHIPPED --> REFUNDING: 用户申请退货
    REFUNDING --> REFUNDED: 退款完成
    REFUNDING --> PAID: 退款被拒绝
    COMPLETED --> [*]
    CANCELLED --> [*]
    REFUNDED --> [*]
```

---

## 示例 5: 部署架构图

```mermaid
graph LR
    subgraph 用户端
        App[移动端 App]
        H5[H5 / 小程序]
    end

    subgraph CDN
        CDN_Node[静态资源 CDN]
    end

    subgraph K8s集群
        LB[负载均衡<br/>Nginx Ingress]
        subgraph 业务服务
            GW[API 网关 x2]
            SVC1[订单服务 x3]
            SVC2[商品服务 x2]
            SVC3[用户服务 x2]
        end
    end

    subgraph 中间件
        Redis[(Redis Cluster)]
        RMQ[RocketMQ Cluster]
        Nacos[Nacos 注册中心]
    end

    subgraph 数据层
        MySQL_M[(MySQL 主)]
        MySQL_S[(MySQL 从)]
        ES[(Elasticsearch)]
    end

    App --> CDN_Node
    H5 --> CDN_Node
    App --> LB
    H5 --> LB
    LB --> GW
    GW --> SVC1 & SVC2 & SVC3
    SVC1 & SVC2 & SVC3 --> Redis
    SVC1 --> RMQ
    SVC1 & SVC2 & SVC3 --> Nacos
    SVC1 & SVC2 & SVC3 --> MySQL_M
    MySQL_M --> MySQL_S
    SVC2 --> ES
```
