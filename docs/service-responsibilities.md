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
- `POST /api/v1/agent-sessions/{session_id}/messages/stream`：在指定会话下发送用户消息，并通过 SSE 返回 `user_message`、`assistant_delta`、`assistant_message`、`done` 等流式事件。
- `GET /api/v1/agent-sessions/{session_id}/messages`：查询指定会话的消息列表。

当前版本支持两种 Agent 回复模式：

- 默认使用确定性的 SimpleAgent，便于本地开发和测试。
- 配置 `X_AGENT_LLM_PROVIDER=qwen` 时，通过 OpenAI 兼容接口调用千问模型。

该能力用于打通 Web Client、API、Application、Agent、Execution、Infrastructure 和 Persistence 的完整执行链路。

### 自然语言转统计 SQL

服务支持通过 Agentic RAG 模式生成只读统计 SQL：

- `POST /api/v1/nl2sql/generate`：接收自然语言问题，返回检索计划、召回的业务知识、生成 SQL 和 SQL 校验结果。
- Agent 会按需检索表结构、指标定义、业务术语和历史相似查询样例，构建增强上下文。
- 当前版本只负责生成和校验 SQL，不执行真实业务数据库查询。
- 默认从 MySQL `information_schema` 读取真实表结构、字段注释、外键和索引信息，并与静态指标、术语、样例知识组合检索。
- 配置 `X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=memory` 后，可切回进程内静态知识库，方便无数据库环境临时运行。
- 配置 `X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=vector` 后，可使用 Qdrant 向量知识库召回上下文。向量库通过 `scripts/ingest_nl2sql_knowledge.py` 从 MySQL metadata 和静态业务知识构建，运行时按知识类型和 `X_AGENT_NL2SQL_VECTOR_SCORE_THRESHOLD` 过滤低相关召回。
- 当前 MySQL metadata 和 Qdrant 向量知识库都用于增强生成上下文，不负责执行 SQL 查询或管理业务数据库连接池。

### Mock 业务数据库

项目提供本地 MySQL 8.0 mock 业务库初始化脚本，供 NL2SQL 和后续数据分析能力测试：

- 默认库名为 `x_agent_mock_biz`。
- 当前包含用户、商户、商品、订单、支付、退款、行为、风控画像、风控规则命中和风控案件等 16 张表。
- 初始化脚本位于 `scripts/init_mock_mysql.sh`。
- 数据库脚本位于 `database/mock_mysql/`。
- NL2SQL MySQL metadata 检索默认读取该库的表、字段、索引和外键。

### Web Client

项目包含一个独立的前端 Web Client，用于验证客户端层和 API 层的交互：

- 使用 Vite、React 和 TypeScript 构建。
- 默认通过 CORS 访问后端 API。
- 当前版本支持创建 Agent 会话、发送用户消息、流式展示 assistant 回复和查询消息列表。

## 规划职责

### Agent 任务执行

接收用户任务、规划执行步骤、调用工具，并返回归一化结果。当前版本只完成确定性 SimpleAgent 回复，后续会接入真实 LLM Provider、任务状态和工具调用。

### 持久化会话状态

持久化消息、Agent 状态、工具调用、执行轨迹和审计记录。

### Provider 抽象

在稳定的应用端口后面支持多个 LLM Provider。当前已提供千问 OpenAI 兼容 Provider 的第一版适配：

- 使用 `X_AGENT_LLM_PROVIDER=qwen` 启用。
- 使用 `X_AGENT_QWEN_API_KEY` 或 `DASHSCOPE_API_KEY` 提供 API Key。
- 默认模型为 `qwen-plus`。
- 同步回复使用 OpenAI 兼容 Chat Completions；流式回复使用同一接口的 `stream` 模式。
- API Key 必须通过环境变量注入，不能写入代码、文档或提交历史。
