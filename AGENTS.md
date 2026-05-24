# Codex 协作入口

这个仓库是一个生产级学习项目。Codex 应像资深结对工程师一样工作：先理解边界，再提出方案，获得确认后实现、测试并自 review。

## 必守规则

- 非平凡变更默认先给方案、影响范围和测试计划，用户确认后再编码。
- 变更范围必须收敛在已评审通过的需求内。
- 行为、职责或架构变化必须同步更新对应文档。
- 项目文档和代码注释优先使用中文；标识符、API 字段、日志字段和错误码使用英文。

## Superpowers 集成

如果当前 Codex 环境安装了 Superpowers 插件，可以把 Superpowers 作为通用工程技能层使用，但不能覆盖本项目规则。

优先级固定为：

```text
用户明确要求 > AGENTS.md > docs/* > Superpowers skills > 默认模型习惯
```

使用场景：

- 复杂需求澄清、方案探索：参考 `brainstorming`。
- 大功能拆解和计划文档：参考 `writing-plans`。
- 执行已确认计划：参考 `executing-plans`。
- Bug 排查：参考 `systematic-debugging`。
- 高风险逻辑或核心算法：参考 `test-driven-development`。
- 完成前验证：参考 `verification-before-completion`。
- 请求或处理代码评审：参考 `requesting-code-review`、`receiving-code-review`。

Superpowers 只决定“怎么更好地工作”，本项目仍必须遵守“先方案、用户确认后编码、质量检查、自 review、更新职责文档、用户 review 后 commit”的流程。

## 按需读取项目知识

Codex 按需读取 `docs/`，不默认全量读取所有文档。

- 非平凡需求开始前：必须读取最新的 `AGENTS.md` 和 `docs/development-workflow.md`。
- 新功能需求：读取 `docs/architecture.md` 和 `docs/service-responsibilities.md`。
- 流程、质量门或协作方式调整：读取 `docs/development-workflow.md`。
- 架构调整或重要技术选型：读取 `docs/architecture.md`，必要时新增或更新 `docs/adr/`。
- 业务职责变化：读取并更新 `docs/service-responsibilities.md`。
- 小范围修复、纯测试调整或格式修复：不强制读取 `docs/`。

如果相关项目知识文件相比本轮已知上下文可能已经更新，必须读取最新内容；如果无法可靠判断是否更新，也必须读取最新内容。

## 文档索引

- `docs/architecture.md`：分层架构、依赖方向和架构边界。
- `docs/development-workflow.md`：研发流程、质量检查、测试和自 review 规则。
- `docs/service-responsibilities.md`：当前服务职责、规划职责和业务边界。
- `docs/workflows/superpowers-integration.md`：Superpowers 与本项目流程的集成规则。
- `docs/adr/`：重要架构决策记录。
