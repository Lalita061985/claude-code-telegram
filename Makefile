.PHONY: install dev test lint format clean help run run-infisical test-infisical-launcher test-macos-deploy-assets

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install production dependencies"
	@echo "  dev        - Install development dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code"
	@echo "  clean      - Clean up generated files"
	@echo "  run        - Run the bot"
	@echo "  run-infisical - Run Bot 2 with LifeOS Infisical injection"
	@echo "  test-infisical-launcher - Test the Infisical credential boundary"
	@echo "  test-macos-deploy-assets - Validate the secret-free Mac Mini service assets"

install:
	poetry install --no-dev

dev:
	poetry install
	poetry run pre-commit install --install-hooks || echo "pre-commit not configured yet"

test:
	poetry run pytest

lint:
	poetry run black --check src tests
	poetry run isort --check-only src tests
	poetry run flake8 src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

run:
	poetry run claude-telegram-bot

run-infisical:
	./run-infisical.sh

test-infisical-launcher:
	bash tests/test_run_infisical_launcher.sh

test-macos-deploy-assets:
	bash tests/test_macos_deploy_assets.sh

# For debugging
run-debug:
	poetry run claude-telegram-bot --debug
