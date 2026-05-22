# 架构设计

`x-agent` 被设计为一个分层的 AI Agent 服务。第一版实现会保持运行时足够小，但架构边界会按生产级服务来设计，避免后续增加 Agent、队列、持久化和外部 Provider 时大规模重构。

## 分层

### Client 层

表示服务调用方，例如 Web 应用、CLI、SDK、自动化任务或其他后端服务。

### API 层

负责 HTTP 路由、请求校验、响应 Schema、认证集成、限流集成，以及把应用层错误映射为 API 响应。

### Application 层

负责业务用例编排。它处理流程协调、事务边界，并调用领域服务或端口接口。Application 层不应该知道 HTTP 细节。

### Domain 层

包含业务概念和业务规则。领域对象应该独立于框架，便于单元测试。

### Agent 层

负责 AI Agent 相关概念：会话、上下文窗口、任务规划、工具选择、记忆策略和执行策略。

### Execution 层

代表 Agent 执行具体工作。该层后续会负责工具执行、重试、超时、并发控制、沙箱、队列和执行结果归一化。

### Persistence 层

负责持久化边界，例如会话、消息、任务、工具调用、审计日志，以及后续的向量索引元数据。

### Infrastructure 层

包含外部系统适配器：LLM Provider、数据库客户端、Redis、消息队列、对象存储、指标、链路追踪和日志。

## 依赖方向

依赖应指向内层：

```text
API -> Application -> Domain
Agent -> Domain
Execution -> Domain
Infrastructure -> Application ports / Persistence interfaces
```

框架和厂商 SDK 应留在系统边缘。

## 架构边界

- API 层不能包含核心业务逻辑。
- Domain 层不能依赖 FastAPI、数据库客户端、LLM SDK 或环境配置。
- Application 层负责编排用例，并在合适的位置依赖端口或接口。
- Infrastructure 层负责外部系统的具体适配器。
- Agent 层和 Execution 层应与 HTTP 细节隔离。
- 新增持久化行为时，需要定义 repository 边界并补充测试。

## 初始运行时

第一版基线只暴露健康检查、就绪检查和服务元数据接口。这些接口用于验证 Web 服务装配、配置加载、响应 Schema 和测试基础设施，同时避免过早提交复杂 Agent 行为。
