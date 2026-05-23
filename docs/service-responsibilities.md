# 服务职责

本文档记录服务当前负责什么，方便后续新需求基于已有业务边界进行评估。

## 当前职责

### 服务健康状态

服务暴露存活检查和就绪检查接口：

- `GET /healthz`：确认进程存活，并返回服务元数据。
- `GET /readyz`：确认服务已经准备好接收流量。

### 服务元数据

服务暴露 `GET /api/v1/service-info`，用于描述当前服务职责和支持的架构分层。

### Agent 会话管理

服务支持创建和查询 Agent 会话：

- `POST /api/v1/agent-sessions`：创建 Agent 会话。
- `GET /api/v1/agent-sessions/{session_id}`：查询指定 Agent 会话。

第一版使用进程内内存 repository，用于验证业务边界和 API 契约。该存储不是最终生产持久化方案，后续会替换为数据库 repository。

### Agent 消息管理

服务支持在 Agent 会话下发送和查询消息：

- `POST /api/v1/agent-sessions/{session_id}/messages`：在指定会话下发送用户消息，并返回本次新增的 user/assistant 消息。
- `GET /api/v1/agent-sessions/{session_id}/messages`：查询指定会话的消息列表。

当前版本使用确定性的 SimpleAgent 生成 assistant 回复，不触发真实 LLM 调用。该能力用于先打通 Web Client、API、Application、Agent、Execution 和 Persistence 的完整执行链路。

### Web Client

项目包含一个独立的前端 Web Client，用于验证客户端层和 API 层的交互：

- 使用 Vite、React 和 TypeScript 构建。
- 默认通过 CORS 访问后端 API。
- 当前版本支持创建 Agent 会话、发送用户消息、展示确定性 assistant 回复和查询消息列表。

## 规划职责

### Agent 任务执行

接收用户任务、规划执行步骤、调用工具，并返回归一化结果。当前版本只完成确定性 SimpleAgent 回复，后续会接入真实 LLM Provider、任务状态和工具调用。

### 持久化会话状态

持久化消息、Agent 状态、工具调用、执行轨迹和审计记录。

### Provider 抽象

在稳定的应用端口后面支持多个 LLM Provider。
