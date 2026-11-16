#!make

.DEFAULT_GOAL := help
.PHONY: clean help install lint lint-markdown test

# Put it first so that "make" without argument is like "make help".
help: ## Display available commands
	@echo "Available commands:"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-20s\033[0m %s\n", $$1, $$2}'

########## COLOR CODES FOR OUTPUT ##########
BLUE := $(shell tput setaf 4 2>/dev/null)
GREEN := $(shell tput setaf 2 2>/dev/null)
RESET := $(shell tput sgr0 2>/dev/null)

########## GLOBALS ##########
PROJECT_NAME = pydelity
SHELL := /bin/bash

########## CLEAN UP ##########
clean: ## Remove caches, build output, and testing artifacts
	@echo "$(BLUE)Cleaning project files...$(RESET)"
	@+rm -rf \
		.cache \
		.eslintcache \
		.next \
		.stylelintcache \
		.turbo \
		.vite \
		.vitest \
		build \
		coverage \
		dist \
		node_modules/.vitest
	@pnpm store prune
	@echo "$(GREEN)Cleanup complete.$(RESET)"

########## ENVIRONMENT ##########
install: ## Create the dev environment from uv.lock (fails if the lock is out of date)
	@echo "$(BLUE)Syncing the dev environment from uv.lock...$(RESET)"
	@uv sync --locked
	@echo "$(GREEN)Dev environment ready in .venv.$(RESET)"

########## TESTS ##########
test: ## Run the test suite
	@uv run --locked pytest

########## LINTING ##########
lint: lint-markdown ## Run all linters and formatters

lint-markdown: ## Format Markdown with Prettier (write)
	@echo "$(BLUE)Running prettier...$(RESET)"
	@npx prettier --write --prose-wrap always --print-width 80 --ignore-path .gitignore --ignore-path .prettierignore "**/*.md" "!CHANGELOG.md"
	@echo "$(GREEN)Markdown formatting complete.$(RESET)"
