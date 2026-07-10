# Pupa Marketplace — validation + index generation.
# Pure python3 stdlib; no dependencies to install.

PYTHON ?= python3
BASE   ?= origin/main

.DEFAULT_GOAL := help

.PHONY: help validate index check-pr new-app self-test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

validate: ## Validate all apps + verify index.json is current (CI entry point)
	@$(PYTHON) scripts/validate.py --check

index: ## Regenerate index.json from apps/ + marketplace.json
	@$(PYTHON) scripts/validate.py --write

check-pr: ## validate + require version bumps vs BASE (default origin/main)
	@$(PYTHON) scripts/validate.py --check --base $(BASE)

new-app: ## Scaffold apps/$(SLUG)/ with a metadata.json stub
	@test -n "$(SLUG)" || { echo "usage: make new-app SLUG=my-app"; exit 1; }
	@$(PYTHON) scripts/validate.py --new-app $(SLUG)

self-test: ## Run the validator's built-in negative-path tests
	@$(PYTHON) scripts/validate.py --self-test
