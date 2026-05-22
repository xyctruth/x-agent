# 开发流程

本项目采用“先评审，后编码”的开发流程。

## 需求流程

1. 明确需求和验收标准。
2. Codex 提出设计方案、影响范围和测试计划。
3. 用户评审并确认方案。
4. Codex 实现变更。
5. Codex 编写或更新测试。
6. Codex 运行质量检查。
7. Codex 执行自 review。
8. Codex 更新服务职责文档。
9. 用户进行review确认。
10. git commit

## 变更范围

- 变更范围必须收敛在已评审通过的需求内。
- 不做无关重构，不回滚用户已有改动。
- 生产代码和测试代码应一起实现。
- 如果依赖不可用或检查无法执行，需要在结果中明确说明。

## 本地检查

变更完成前应运行全部本地检查：

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

使用以下命令格式化代码：

```bash
uv run ruff format .
```

## 文档规则

- 架构变化更新 `docs/architecture.md`。
- 行为或职责变化更新 `docs/service-responsibilities.md`。
- 重要设计决策记录到 `docs/adr/`。

## Python 规范

- 使用 Python 3.13+。
- 业务代码必须提供类型标注。
- API Schema 和配置 Schema 优先使用 Pydantic。
- 使用结构化日志，不使用 `print` 输出业务日志。
- 异常需要显式建模，并映射成稳定的 API 响应。
- 避免全局可变运行时状态。

## 测试规范

- Domain 层和 Application 层行为必须有单元测试。
- API 行为需要有聚焦的集成风格测试。
- 外部服务必须在测试中使用 mock、fake 或本地替身。

## 语言规范

- 项目文档优先使用中文。
- 代码注释优先使用中文，但只在能解释复杂意图时添加注释。
- 对外暴露的 API 字段、包名、模块名、类名、函数名仍使用英文。
- 日志字段名和错误码使用英文，便于机器处理和跨系统集成。
