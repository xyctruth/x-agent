SHELL := /usr/bin/env bash

PYTHON ?= uv run python
FASTAPI ?= uv run fastapi

MYSQL_HOST ?= 127.0.0.1
MYSQL_PORT ?= 3306
MYSQL_USER ?= root
MYSQL_PASSWORD ?= root
MYSQL_DATABASE ?= x_agent_mock_biz

QDRANT_URL ?= http://127.0.0.1:6333

.PHONY: help sync check format lint type test start-mysql start-qdrant init-mysql up ingest-nl2sql dev

help:
	@echo "x-agent 常用命令"
	@echo ""
	@echo "  make sync          安装 Python 依赖"
	@echo "  make check         运行格式、lint、类型检查和测试"
	@echo "  make start-mysql   启动 Docker MySQL, 数据挂载到 .data/mysql"
	@echo "  make start-qdrant  启动 Docker Qdrant, 数据挂载到 .data/qdrant"
	@echo "  make init-mysql    初始化 mock MySQL 业务库"
	@echo "  make up            启动 MySQL/Qdrant 并初始化 MySQL"
	@echo "  make ingest-nl2sql 将 NL2SQL 知识写入 Qdrant"
	@echo "  make dev           启动 FastAPI 开发服务"

sync:
	uv sync --extra dev

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

type:
	uv run mypy src tests scripts/ingest_nl2sql_knowledge.py

test:
	X_AGENT_LLM_PROVIDER=simple \
	X_AGENT_QWEN_API_KEY= \
	X_AGENT_NL2SQL_KNOWLEDGE_SOURCE=mysql \
	uv run pytest

check: lint type test

start-mysql:
	MYSQL_PORT="$(MYSQL_PORT)" \
	MYSQL_PASSWORD="$(MYSQL_PASSWORD)" \
	MYSQL_DATABASE="$(MYSQL_DATABASE)" \
	bash scripts/start_mysql.sh

start-qdrant:
	bash scripts/start_qdrant.sh

init-mysql:
	MYSQL_HOST="$(MYSQL_HOST)" \
	MYSQL_PORT="$(MYSQL_PORT)" \
	MYSQL_USER="$(MYSQL_USER)" \
	MYSQL_PASSWORD="$(MYSQL_PASSWORD)" \
	MYSQL_DATABASE="$(MYSQL_DATABASE)" \
	bash scripts/init_mock_mysql.sh

up: start-mysql start-qdrant init-mysql

ingest-nl2sql:
	X_AGENT_MYSQL_HOST="$(MYSQL_HOST)" \
	X_AGENT_MYSQL_PORT="$(MYSQL_PORT)" \
	X_AGENT_MYSQL_USER="$(MYSQL_USER)" \
	X_AGENT_MYSQL_PASSWORD="$(MYSQL_PASSWORD)" \
	X_AGENT_MYSQL_DATABASE="$(MYSQL_DATABASE)" \
	X_AGENT_QDRANT_URL="$(QDRANT_URL)" \
	$(PYTHON) scripts/ingest_nl2sql_knowledge.py

dev:
	$(FASTAPI) dev src/x_agent/main.py
