SHELL := /bin/bash

PYTHON := python3.12
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip

UVICORN := $(BIN)/uvicorn
APP_MODULE := app.main:app
HOST := 0.0.0.0
PORT := 8000

BLACK := $(BIN)/black
PIPREQS := $(BIN)/pipreqs

ENV_FILE := .env
include $(ENV_FILE)

.PHONY: setup

setup:
	@echo "🔹 Checking virtual environment..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi

	@echo "🔹 Upgrading pip..."
	@$(PIP) install --upgrade pip

	@echo "🔹 Creating environment file..."
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "TOKEN_EXPIRE_MINUTES=1440" >> $(ENV_FILE); \
		echo "SECRET_KEY=" >> $(ENV_FILE); \
		echo "DB_USER=" >> $(ENV_FILE); \
		echo "DB_PWD=" >> $(ENV_FILE); \
		echo "DB_HOST=" >> $(ENV_FILE); \
		echo "DB_PORT=" >> $(ENV_FILE); \
		echo "DB_NAME=" >> $(ENV_FILE); \
	else \
		echo ".env file already exists, skipping"; \
	fi

	@echo "🔹 Installing dev tools (black, pipreqs)..."
	@$(PIP) install black pipreqs

	@echo "🔹 Installing requirements.txt (if present)..."
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "requirements.txt not found, skipping"; \
	fi

	@echo "🔹 Checking PostgreSQL client..."
	@if ! command -v psql >/dev/null 2>&1; then \
		echo "Installing PostgreSQL client..."; \
		sudo apt update && sudo apt install -y postgresql-client; \
	else \
		echo "PostgreSQL client already installed"; \
	fi

	@echo "✅ Setup complete"

db-setup:
	@echo "🔹 Setting up Postgres database and role..."
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "❌ .env file not found. Please create it first"; \
		exit 1; \
	fi
	@DB_NAME=$$(grep -E '^DB_NAME=' $(ENV_FILE) | cut -d '=' -f2); \
	DB_USER=$$(grep -E '^DB_USER=' $(ENV_FILE) | cut -d '=' -f2); \
	DB_PWD=$$(grep -E '^DB_PWD=' $(ENV_FILE) | cut -d '=' -f2); \
	if [ -z "$$DB_NAME" ] || [ -z "$$DB_USER" ] || [ -z "$$DB_PWD" ]; then \
		echo "❌ DB_NAME, DB_USER, and DB_PWD must be defined in .env"; \
		exit 1; \
	fi; \
	echo "Checking if role $$DB_USER exists..."; \
	ROLE_EXISTS=$$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$$DB_USER'"); \
	if [ "$$ROLE_EXISTS" != "1" ]; then \
		echo "Creating role $$DB_USER..."; \
		sudo -u postgres psql -c "CREATE ROLE $$DB_USER WITH LOGIN PASSWORD '$$DB_PWD';"; \
	else \
		echo "Role $$DB_USER already exists, skipping"; \
	fi; \
	echo "Checking if database $$DB_NAME exists..."; \
	DB_EXISTS=$$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$$DB_NAME'"); \
	if [ "$$DB_EXISTS" != "1" ]; then \
		echo "Creating database $$DB_NAME..."; \
		sudo -u postgres psql -c "CREATE DATABASE $$DB_NAME OWNER $$DB_USER;"; \
	else \
		echo "Database $$DB_NAME already exists, skipping"; \
	fi; \
	echo "Granting all privileges on database $$DB_NAME to $$DB_USER..."; \
	sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $$DB_NAME TO $$DB_USER;"
	echo "Creating extension LTREE database $$DB_NAME"; \
	sudo -u postgres $$DB_NAME -c "CREATE EXTENSION IF NOT EXISTS ltree;"

db-login:
	psql postgresql://$(DB_USER):$(DB_PWD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)

run:
	@$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

format:
	@$(BLACK) app/

reqs-gen-regen:
	@$(PIPREQS) . --ignore .venv/ --force
