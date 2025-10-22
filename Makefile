.PHONY: help start stop restart backend frontend test clean install logs status

# Configuration
BACKEND_PORT := 8004
FRONTEND_PORT := 3004

# Colors
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Word Doc Chatbot - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

start: ## Start both backend and frontend services
	@./start.sh

stop: ## Stop both backend and frontend services
	@./stop.sh

restart: stop start ## Restart both services

backend: ## Start only the backend server
	@echo "$(BLUE)Starting backend on port $(BACKEND_PORT)...$(NC)"
	uvicorn backend.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

frontend: ## Start only the frontend server
	@echo "$(BLUE)Starting frontend on port $(FRONTEND_PORT)...$(NC)"
	streamlit run frontend/streamlit_app.py --server.port $(FRONTEND_PORT)

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ --cov=backend --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated at htmlcov/index.html$(NC)"

logs: ## Tail logs from both services
	@tail -f /tmp/word-doc-backend.log /tmp/word-doc-frontend.log

logs-backend: ## Tail backend logs only
	@tail -f /tmp/word-doc-backend.log

logs-frontend: ## Tail frontend logs only
	@tail -f /tmp/word-doc-frontend.log

status: ## Check if services are running
	@echo "$(BLUE)Service Status:$(NC)"
	@echo ""
	@if [ -f /tmp/word-doc-backend.pid ] && kill -0 $$(cat /tmp/word-doc-backend.pid) 2>/dev/null; then \
		echo "$(GREEN)✓ Backend running (PID: $$(cat /tmp/word-doc-backend.pid))$(NC)"; \
		echo "  URL: http://localhost:$(BACKEND_PORT)"; \
	else \
		echo "$(YELLOW)✗ Backend not running$(NC)"; \
	fi
	@echo ""
	@if [ -f /tmp/word-doc-frontend.pid ] && kill -0 $$(cat /tmp/word-doc-frontend.pid) 2>/dev/null; then \
		echo "$(GREEN)✓ Frontend running (PID: $$(cat /tmp/word-doc-frontend.pid))$(NC)"; \
		echo "  URL: http://localhost:$(FRONTEND_PORT)"; \
	else \
		echo "$(YELLOW)✗ Frontend not running$(NC)"; \
	fi
	@echo ""

clean: ## Clean up temporary files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache htmlcov .coverage
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

dev-backend: ## Run backend in development mode with auto-reload
	@echo "$(BLUE)Starting backend in development mode...$(NC)"
	uvicorn backend.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT) --log-level debug

dev-frontend: ## Run frontend in development mode
	@echo "$(BLUE)Starting frontend in development mode...$(NC)"
	streamlit run frontend/streamlit_app.py --server.port $(FRONTEND_PORT) --logger.level=debug

check-env: ## Verify environment configuration
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠ .env file not found!$(NC)"; \
		echo "  Create one from .env.example"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ .env file exists$(NC)"
	@python -c "from backend.config import AppConfig; print('✓ Backend config loads successfully')" || echo "$(YELLOW)⚠ Backend config has issues$(NC)"

urls: ## Display service URLs
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo ""
	@echo "  Backend:  http://localhost:$(BACKEND_PORT)"
	@echo "  Frontend: http://localhost:$(FRONTEND_PORT)"
	@echo "  API Docs: http://localhost:$(BACKEND_PORT)/docs"
	@echo ""
