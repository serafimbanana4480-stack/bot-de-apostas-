# Makefile - Sistema VBQ-UNIFIED
# Comandos úteis para desenvolvimento, teste e deploy

.PHONY: help install test test-unit test-integration test-e2e lint format build up down shell db-setup db-reset db-migrate ingest train backtest deploy logs clean

# Variáveis de ambiente
ENV_FILE := .env
PYTHON := python3.11
VENV := venv
DOCKER_COMPOSE := docker-compose

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostrar ajuda
	@echo "$(GREEN)Comandos disponíveis:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instalar dependências em ambiente virtual
	@echo "$(YELLOW)Criando ambiente virtual...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/python -m spacy download en_core_web_sm
	@echo "$(GREEN)Instalação completa. Ative com: source $(VENV)/bin/activate$(NC)"

test: ## Executar todos os testes
	@echo "$(YELLOW)Executando testes...$(NC)"
	$(VENV)/bin/pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Testes concluídos. Ver relatório em htmlcov/$(NC)"

test-unit: ## Executar apenas testes unitários
	$(VENV)/bin/pytest tests/unit/ -v

test-integration: ## Executar testes de integração (require infra)
	$(VENV)/bin/pytest tests/integration/ -v

test-e2e: ## Executar testes end-to-end
	$(VENV)/bin/pytest tests/e2e/ -v

lint: ## Executar linting (black, flake8, mypy, isort)
	@echo "$(YELLOW)Linting com black...$(NC)"
	$(VENV)/bin/black src/ tests/ --check
	@echo "$(YELLOW)Linting com flake8...$(NC)"
	$(VENV)/bin/flake8 src/ tests/ --max-line-length=100
	@echo "$(YELLOW)Linting com mypy...$(NC)"
	$(VENV)/bin/mypy src/ --ignore-missing-imports
	@echo "$(YELLOW)Linting com isort...$(NC)"
	$(VENV)/bin/isort src/ tests/ --check-only

format: ## Formatar código com black e isort
	@echo "$(YELLOW)Formatando com black...$(NC)"
	$(VENV)/bin/black src/ tests/
	@echo "$(YELLOW)Formatando com isort...$(NC)"
	$(VENV)/bin/isort src/ tests/

build: ## Construir imagem Docker
	docker build -t vbq-system:latest .

up: ## Iniciar todos os serviços (docker-compose)
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Serviços iniciados. Grafana em http://localhost:3000$(NC)"

down: ## Parar todos os serviços
	$(DOCKER_COMPOSE) down
	@echo "$(YELLOW)Serviços parados.$(NC)"

up-dev: ## Iniciar em modo desenvolvimento (rebuild)
	$(DOCKER_COMPOSE) up -d --build
	$(DOCKER_COMPOSE) logs -f api

logs: ## Ver logs de todos os serviços
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Ver logs apenas da API
	$(DOCKER_COMPOSE) logs -f api

shell: ## Abrir shell no container da API
	$(DOCKER_COMPOSE) exec api bash

db-setup: ## Criar base de dados e schema
	@echo "$(YELLOW)Criando schema da base de dados...$(NC)"
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/001_schema_raw.sql
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/002_schema_clean.sql
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/003_schema_features.sql
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/004_schema_meta.sql
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/005_indexes.sql
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/006_seed_data.sql
	@echo "$(GREEN)Schema criado.$(NC)"

db-reset: ## Apagar e recriar base de dados (CUIDADO: perde dados)
	@echo "$(RED)ATENÇÃO: Isto vai apagar TODOS os dados.$(NC)"
	@read -p "Continuar? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec -T postgres psql -U vb_admin -d valuebetting -c "DROP SCHEMA IF EXISTS bronze CASCADE;"; \
		docker-compose exec -T postgres psql -U vb_admin -d valuebetting -c "DROP SCHEMA IF EXISTS silver CASCADE;"; \
		docker-compose exec -T postgres psql -U vb_admin -d valuebetting -c "DROP SCHEMA IF EXISTS gold CASCADE;"; \
		docker-compose exec -T postgres psql -U vb_admin -d valuebetting -c "DROP SCHEMA IF EXISTS meta CASCADE;"; \
		$(MAKE) db-setup; \
	else \
		echo "Cancelado."; \
	fi

db-migrate: ## Executar migrações pendentes (Alembic)
	docker-compose exec api alembic upgrade head

ingest-nba: ## Ingestão manual de dados NBA (data de hoje)
	docker-compose exec api python -m src.ingestion.orchestrator

ingest-historical: ## Backfill de dados históricos (últimos 5 anos)
	docker-compose exec api python scripts/backfill_data.sh

train-model: ## Treinar modelo com dados atuais
	docker-compose exec api python -m src.models.ensemble

backtest: ## Executar backtest completo
	docker-compose exec api python -m src.backtest.walk_forward

deploy: ## Deploy para produção
	@echo "$(YELLOW)Deploy para produção...$(NC)"
	git pull
	$(MAKE) build
	$(DOCKER_COMPOSE) up -d
	$(MAKE) db-migrate
	@echo "$(GREEN)Deploy concluído.$(NC)"

logs-clean: ## Limpar logs antigos (> 30 dias)
	docker-compose exec api find ./logs -name "*.log" -mtime +30 -delete

clean: ## Limpar artefactos de build e cache
	@echo "$(YELLOW)Limpando...$(NC)"
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	rm -rf $(VENV)
	docker-compose down -v
	@echo "$(GREEN)Limpeza concluída.$(NC)"

check-env: ## Verificar se .env existe
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(RED)ERRO: $(ENV_FILE) não existe. Copie .env.example para .env e preencha.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN).env existe.$(NC)"

seed-data: ## Inserir dados de seed (equipas, épocas)
	docker-compose exec -T postgres psql -U vb_admin -d valuebetting -f /docker-entrypoint-initdb.d/006_seed_data.sql

backup-db: ## Backup da base de dados
	docker-compose exec postgres pg_dump -U vb_admin valuebetting > backups/vbq_backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restaurar backup (uso: make restore-db FILE=backup.sql)
	docker-compose exec -T postgres psql -U vb_admin valuebetting < $(FILE)

status: ## Verificar status de todos os serviços
	$(DOCKER_COMPOSE) ps