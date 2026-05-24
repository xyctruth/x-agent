# x-agent

`x-agent` 是一个用于学习并实践生产级 Python AI Agent 服务的项目。目标是构建一个高可用、可扩展、边界清晰的 Agent 服务。

这个项目从第一版开始就按照真实服务的方式组织：清晰分层、明确开发流程、类型化业务代码、测试、lint、类型检查，以及服务职责文档。

## 架构

初始架构包含以下层次：

- Client 层：SDK、CLI、Web 客户端和外部调用方。
- API 层：FastAPI 路由、请求校验、响应 Schema 和错误映射。
- Application 层：用例编排、事务边界和应用服务。
- Domain 层：不依赖框架或基础设施的业务概念。
- Agent 层：Agent 会话、规划、上下文管理和执行策略。
- Execution 层：工具运行时、重试、超时和后台执行。
- Persistence 层：repository 和持久化状态。
- Infrastructure 层：配置、日志、LLM Provider、数据库、队列和外部 API。

更多说明见 [docs/architecture.md](docs/architecture.md)。

## 开发

安装依赖：

```bash
uv sync --extra dev
```

启动服务：

```bash
uv run fastapi dev src/x_agent/main.py
```

也可以直接使用 `uvicorn`：

```bash
uv run uvicorn x_agent.main:create_app --factory --reload
```

运行检查：

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

启动前端：

```bash
cd web
npm install
npm run dev
```

前端默认连接 `http://127.0.0.1:8000`，可以通过 `VITE_X_AGENT_API_BASE_URL` 覆盖。

### 接入千问

默认使用确定性的 SimpleAgent。接入千问时通过环境变量启用，不要把 API Key 写入代码或文档：

```bash
export X_AGENT_LLM_PROVIDER=qwen
export X_AGENT_QWEN_API_KEY="你的百炼 API Key"
export X_AGENT_QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export X_AGENT_QWEN_MODEL="qwen-plus"
uv run fastapi dev src/x_agent/main.py
```

也兼容官方环境变量：

```bash
export DASHSCOPE_API_KEY="你的百炼 API Key"
```

### 初始化 Mock MySQL 业务库

项目提供本地 MySQL 8.0 mock 业务库，用于测试自然语言转统计 SQL、后续只读 SQL 执行和数据分析能力：

```bash
bash scripts/init_mock_mysql.sh
```

默认连接 `127.0.0.1:3306`，用户和密码均为 `root`，数据库名为 `x_agent_mock_biz`。可以通过 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE` 环境变量覆盖。

### 启用 NL2SQL MySQL metadata 检索

NL2SQL 默认从本地 mock MySQL 的 `information_schema` 读取真实表结构、字段注释、外键和索引信息：

```bash
export X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=mysql
export X_AGENT_MYSQL_HOST=127.0.0.1
export X_AGENT_MYSQL_PORT=3306
export X_AGENT_MYSQL_USER=root
export X_AGENT_MYSQL_PASSWORD=root
export X_AGENT_MYSQL_DATABASE=x_agent_mock_biz
uv run fastapi dev src/x_agent/main.py
```

启用后，服务会组合使用 MySQL metadata 和静态业务知识。MySQL metadata 负责真实表结构，静态知识库继续提供指标定义、业务术语和历史 SQL 样例。

如果需要在无数据库环境下临时运行，可以切回进程内静态知识库：

```bash
export X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=memory
```

## 当前 API

- `GET /healthz`：存活检查和基础服务元数据。
- `GET /readyz`：服务就绪检查。
- `GET /api/v1/service-info`：服务职责和支持的架构分层。
- `POST /api/v1/agent-sessions`：创建 Agent 会话。
- `GET /api/v1/agent-sessions/{session_id}`：查询 Agent 会话。
- `POST /api/v1/agent-sessions/{session_id}/messages`：在会话下发送用户消息，并返回本次新增的 user/assistant 消息。
- `POST /api/v1/agent-sessions/{session_id}/messages/stream`：在会话下发送用户消息，并通过 SSE 流式返回 assistant 生成过程和最终消息。
- `GET /api/v1/agent-sessions/{session_id}/messages`：查询会话消息列表。
- `POST /api/v1/nl2sql/generate`：基于 Agentic RAG 检索业务知识并生成只读统计 SQL，返回检索计划、上下文、SQL 和校验结果。
