# Superpowers 集成规则

本文档说明本项目如何使用 Superpowers。Superpowers 是通用工程技能层，本项目文档是项目级业务和协作规则来源。

## 优先级

固定优先级：

```text
用户明确要求 > AGENTS.md > docs/* > Superpowers skills > 默认模型习惯
```

如果 Superpowers skill 与本项目流程冲突，按本项目流程执行。

## 适用场景

### 需求澄清与方案探索

复杂或模糊需求可以参考 `brainstorming`。

本项目要求：

- 先明确业务边界和验收标准。
- 不直接进入编码。
- 输出方案、影响范围和测试计划。

### 计划编写

需要拆解大型功能、跨多层架构或存在明显风险时，可以参考 `writing-plans`。

本项目要求：

- 计划必须结合 `docs/architecture.md` 的分层边界。
- 计划必须说明 API、Application、Domain、Agent、Execution、Infrastructure、Persistence 的影响。
- 计划必须说明文档更新点。

### 执行计划

用户确认方案后，可以参考 `executing-plans`。

本项目要求：

- 变更范围只包含已确认需求。
- 不做无关重构。
- 编码、测试、文档一起完成。
- 执行到用户 review 前暂停。

### Bug 排查

Bug、异常、测试失败和线上问题分析可以参考 `systematic-debugging`。

本项目要求：

- 先复现或定位证据，再修复。
- 不凭猜测改代码。
- 修复后补充回归测试。

### 测试驱动开发

核心业务逻辑、SQL 校验、Agent 编排、Provider 协议等高风险逻辑可以参考 `test-driven-development`。

本项目要求：

- 外部服务使用 fake、mock 或本地替身。
- Domain 和 Application 层优先单元测试。
- API 层使用聚焦的集成风格测试。

### 完成前验证

非平凡变更完成后可以参考 `verification-before-completion`。

本项目必须运行：

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

如果改动涉及前端，还需要运行：

```bash
cd web
npm run build
```

### 代码评审

需要自 review 或请求 review 时，可以参考 `requesting-code-review` 和 `receiving-code-review`。

本项目要求：

- Codex 自 review 后仍必须等待用户 review。
- 用户明确 review 完成后才能 commit。
- commit 前确认工作区只包含已 review 变更。

## NL2SQL 和 Agent 服务开发补充

涉及 NL2SQL、SQL 执行、业务知识库、数据分析和风控分析时，除 Superpowers 外还必须读取：

- `docs/architecture.md`
- `docs/service-responsibilities.md`
- `database/mock_mysql/README.md`

相关实现应优先保持：

- API 层只负责 HTTP 契约和错误映射。
- Application 层负责编排用例。
- Agent 层负责规划、Prompt、上下文构建和生成策略。
- Infrastructure 层负责 MySQL、LLM Provider、SQL 解析、知识库适配。
- Domain 层不依赖框架、数据库或 LLM SDK。

## 更新策略

Superpowers 可以随插件升级变化。项目只记录稳定集成规则，不复制 Superpowers 全量内容。

当 Superpowers skill 行为发生变化时：

1. 读取当前安装版本的相关 `SKILL.md`。
2. 判断是否与本项目规则冲突。
3. 只把适合本项目的稳定实践沉淀到 `docs/workflows/`。
4. 不把外部插件内容原样复制进项目文档。
