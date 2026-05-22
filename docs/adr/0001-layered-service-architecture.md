# ADR 0001：分层服务架构

## 状态

已接受

## 背景

这个项目是学习环境，但从一开始就应该按照生产级习惯构建。AI Agent 系统如果把 HTTP Handler、Provider SDK 调用、持久化和 Agent 编排混在同一批模块里，后续会很难维护。

## 决策

采用分层架构，并为 API、Application、Domain、Agent、Execution、Persistence 和 Infrastructure 代码建立明确边界。

## 影响

- 初始代码目录会比最小 FastAPI 应用更多。
- 业务行为更容易在不依赖框架或厂商 SDK 的情况下测试。
- 后续 Provider、队列、数据库和工具运行时的变更可以被隔离。

