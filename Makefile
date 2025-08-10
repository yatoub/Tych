# Makefile pour Tych - Compatible Windows/Unix
# Utilise uv pour le packaging et la gestion des dépendances

# Variables
UV := $(if $(shell where uv 2>nul),uv,$(if $(shell which uv 2>/dev/null),uv,.venv/Scripts/uv.exe))
PYTHON := python
PACKAGE_NAME := tych
VERSION := 0.1.0

# Aide par défaut
.DEFAULT_GOAL := help

.PHONY: help
help: ## Affiche l'aide
	@echo "Commandes disponibles pour $(PACKAGE_NAME):"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

.PHONY: install
install: ## Installe uv si nécessaire
	@echo "🔧 Installation d'uv..."
	@$(PYTHON) -m pip install uv

.PHONY: sync
sync: ## Synchronise les dépendances
	@echo "🔄 Synchronisation des dépendances..."
	@$(UV) sync

.PHONY: dev-install
dev-install: sync ## Installation en mode développement
	@echo "🔧 Installation en mode développement..."
	@$(UV) pip install -e .

.PHONY: clean
clean: ## Nettoie les fichiers temporaires
	@echo "🧹 Nettoyage..."
	@if exist dist rmdir /s /q dist 2>nul || rm -rf dist 2>/dev/null || true
	@if exist build rmdir /s /q build 2>nul || rm -rf build 2>/dev/null || true
	@if exist *.egg-info rmdir /s /q *.egg-info 2>nul || rm -rf *.egg-info 2>/dev/null || true
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

.PHONY: build
build: clean sync ## Construit le package
	@echo "📦 Construction du package..."
	@$(UV) build

.PHONY: test
test: ## Lance les tests
	@echo "🧪 Lancement des tests..."
	@$(PYTHON) run_tests.py

.PHONY: test-unit
test-unit: ## Lance les tests unitaires
	@echo "🧪 Tests unitaires..."
	@$(PYTHON) run_tests.py --unit

.PHONY: test-integration
test-integration: ## Lance les tests d'intégration
	@echo "🧪 Tests d'intégration..."
	@$(PYTHON) run_tests.py --integration

.PHONY: test-performance
test-performance: ## Lance les tests de performance
	@echo "🧪 Tests de performance..."
	@$(PYTHON) run_tests.py --performance

.PHONY: test-coverage
test-coverage: ## Lance les tests avec couverture
	@echo "🧪 Tests avec couverture..."
	@$(PYTHON) run_tests.py --coverage

.PHONY: test-fast
test-fast: ## Lance les tests rapides
	@echo "🧪 Tests rapides..."
	@$(PYTHON) run_tests.py --fast

.PHONY: format
format: ## Formate le code
	@echo "✨ Formatage du code..."
	@$(UV) run black tych/ || echo "⚠️ black non disponible"
	@$(UV) run ruff check tych/ --fix || echo "⚠️ ruff non disponible"

.PHONY: lint
lint: ## Vérifie le style du code
	@echo "🔍 Vérification du style..."
	@$(UV) run flake8 tych/ || echo "⚠️ flake8 non disponible"
	@$(UV) run mypy tych/ || echo "⚠️ mypy non disponible"

.PHONY: publish-test
publish-test: build ## Publie sur TestPyPI
	@echo "🚀 Publication sur TestPyPI..."
	@$(UV) publish --repository testpypi dist/*

.PHONY: publish
publish: build ## Publie sur PyPI
	@echo "🚀 Publication sur PyPI..."
	@$(UV) publish dist/*

.PHONY: version
version: ## Affiche la version
	@echo "$(PACKAGE_NAME) version $(VERSION)"
	@$(UV) --version

.PHONY: info
info: ## Affiche les informations du projet
	@echo "📋 Informations du projet:"
	@echo "  Nom: $(PACKAGE_NAME)"
	@echo "  Version: $(VERSION)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  UV: $(shell $(UV) --version 2>/dev/null || echo 'Non installé')"
	@echo "  Répertoire: $(shell pwd)"

.PHONY: dist-info
dist-info: ## Affiche les informations sur les packages construits
	@if exist dist (echo "📦 Packages dans dist/:") else (echo "❌ Aucun package trouvé")
	@if exist dist for %%f in (dist\*) do echo "  - %%~nxf (%%~zf bytes)"

.PHONY: run-example
run-example: ## Lance l'exemple
	@echo "🎯 Lancement de l'exemple..."
	@$(PYTHON) main.py generate -n 10

.PHONY: full-build
full-build: clean install sync dev-install test build ## Build complet (clean + install + test + build)
	@echo "🎉 Build complet terminé!"

# Alias pour compatibilité
.PHONY: all
all: full-build ## Alias pour full-build
