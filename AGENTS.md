# Codex 协作入口

这个仓库是一个生产级学习项目。Codex 应像资深结对工程师一样工作：先理解边界，再提出方案，获得确认后实现、测试并自 review。

## 必守规则

- 非平凡变更默认先给方案、影响范围和测试计划，用户确认后再编码。
- 变更范围必须收敛在已评审通过的需求内。
- 行为、职责或架构变化必须同步更新对应文档。
- 项目文档和代码注释优先使用中文；标识符、API 字段、日志字段和错误码使用英文。

## 按需读取项目知识

Codex 按需读取 `docs/`，不默认全量读取所有文档。

- 新功能需求：读取 `docs/architecture.md` 和 `docs/service-responsibilities.md`。
- 流程、质量门或协作方式调整：读取 `docs/development-workflow.md`。
- 架构调整或重要技术选型：读取 `docs/architecture.md`，必要时新增或更新 `docs/adr/`。
- 业务职责变化：读取并更新 `docs/service-responsibilities.md`。
- 小范围修复、纯测试调整或格式修复：不强制读取 `docs/`。

## 文档索引

- `docs/architecture.md`：分层架构、依赖方向和架构边界。
- `docs/development-workflow.md`：研发流程、质量检查、测试和自 review 规则。
- `docs/service-responsibilities.md`：当前服务职责、规划职责和业务边界。
- `docs/adr/`：重要架构决策记录。

