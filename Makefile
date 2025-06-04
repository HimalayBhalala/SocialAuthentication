# Development/Testing Makefile with Uvicorn

.PHONY: help test-build test-up test-down test-logs test-shell test-clean quick-test

# Default target
help:
	@echo "Django Docker Development/Testing Commands (Uvicorn)"
	@echo ""
	@echo "Quick Testing:"
	@echo "  make quick-test     - Run full test setup (recommended)"
	@echo "  make test-build     - Build development images only"
	@echo "  make test-up        - Start development services with Uvicorn"
	@echo "  make test-down      - Stop development services"
	@echo ""
	@echo "Development:"
	@echo "  make test-logs      - View development logs"
	@echo "  make test-shell     - Access Django shell (dev mode)"
	@echo "  make test-bash      - Access container bash (dev mode)"
	@echo "  make test-migrate   - Run migrations (dev mode)"
	@echo "  make test-super     - Create superuser (dev mode)"
	@echo ""
	@echo "Uvicorn Specific:"
	@echo "  make uvicorn-dev    - Start Uvicorn with hot reload"
	@echo "  make uvicorn-prod   - Start Uvicorn in production mode"
	@echo "  make uvicorn-logs   - View Uvicorn server logs"
	@echo "  make uvicorn-reload - Restart Uvicorn server"
	@echo ""
	@echo "Testing:"
	@echo "  make test-django    - Run Django tests"
	@echo "  make test-api       - Test API endpoints"
	@echo "  make test-health    - Check service health"
	@echo ""
	@echo "Cleanup:"
	@echo "  make test-clean     - Clean development containers"
	@echo "  make test-reset     - Reset everything (clean + rebuild)"

# Quick test - recommended for first time
quick-test:
	@echo "Running quick development test with Uvicorn..."
	chmod +x test-docker.sh
	./test-docker.sh

# Development commands
test-build:
	@echo "Building development images..."
	docker-compose -f docker-compose.yml build

test-up:
	@echo "Starting development services with Uvicorn..."
	docker-compose -f docker-compose.yml up -d
	@echo "Development services started!"
	@echo "Hot reload enabled for development"
	@echo "View logs with: make test-logs"

test-down:
	@echo "Stopping development services..."
	docker-compose -f docker-compose.yml down

test-logs:
	@echo "Viewing development logs..."
	docker-compose -f docker-compose.yml logs -f

test-shell:
	@echo "Accessing Django shell..."
	docker-compose -f docker-compose.yml exec backend python manage.py shell

test-bash:
	@echo "Accessing container bash..."
	docker-compose -f docker-compose.yml exec backend bash

test-migrate:
	@echo "Running migrations in development mode..."
	docker-compose -f docker-compose.yml exec backend python manage.py migrate

test-super:
	@echo "Creating superuser in development mode..."
	docker-compose -f docker-compose.yml exec backend python manage.py createsuperuser

uvicorn-dev:
	@echo "Starting Uvicorn with hot reload..."
	docker-compose -f docker-compose.yml exec backend uvicorn backend.asgi:application --host 0.0.0.0 --port 8000 --reload --log-level debug

uvicorn-prod:
	@echo "Starting Uvicorn in production mode..."
	docker-compose -f docker-compose.yml exec backend uvicorn backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4

uvicorn-logs:
	@echo "Viewing Uvicorn server logs..."
	docker-compose -f docker-compose.yml logs -f backend

uvicorn-reload:
	@echo "Restarting Uvicorn server..."
	docker-compose -f docker-compose.yml restart backend
	@echo "Uvicorn server restarted!"

# Testing commands
test-django:
	@echo "Running Django tests..."
	docker-compose -f docker-compose.yml exec backend python manage.py test

test-api:
	@echo "Testing basic API endpoints..."
	@echo "Waiting for Uvicorn to be ready..."
	@sleep 3
	@curl -s http://localhost:8000/admin/ > /dev/null && echo "Admin page accessible" || echo "Admin page not accessible"
	@curl -s http://localhost:8000/ > /dev/null && echo "Root page accessible" || echo "Root page not accessible"
	@echo "Testing Uvicorn health..."
	@curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" http://localhost:8000/

test-health:
	@echo "Checking service health..."
	@echo "Database:"
	@docker-compose -f docker-compose.yml exec db mysqladmin ping -h localhost -u root -p0000 --silent && echo "MySQL is healthy" || echo "MySQL is not healthy"
	@echo "Uvicorn Backend:"
	@curl -s http://localhost:8000/ > /dev/null && echo "Uvicorn backend is healthy" || echo "Uvicorn backend is not healthy"

# Performance testing
test-performance:
	@echo "⚡ Running basic performance test on Uvicorn..."
	@echo "Testing concurrent requests..."
	@curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:8000/ &
	@curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:8000/ &
	@curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:8000/ &
	@wait

# Cleanup commands
test-clean:
	@echo "Cleaning development environment..."
	docker-compose -f docker-compose.yml down -v
	docker system prune -f

test-reset: test-clean test-build test-up
	@echo "Development environment reset complete!"

# Celery commands (optional)
test-celery:
	@echo "Starting Celery worker for testing..."
	docker-compose -f docker-compose.yml --profile celery up -d

test-celery-logs:
	@echo "Viewing Celery logs..."
	docker-compose -f docker-compose.yml logs -f celery

# Database commands  
test-db-shell:
	@echo "Accessing test database..."
	docker-compose -f docker-compose.yml exec db mysql -u root -p0000 ${DB_NAME}

test-db-backup:
	@echo "Creating database backup..."
	docker-compose -f docker-compose.yml exec db mysqldump -u root -p0000 ${DB_NAME} > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created!"

# Status check
test-status:
	@echo "Development environment status:"
	docker-compose -f docker-compose.yml ps
	@echo ""
	@echo "Service URLs:"
	@echo "  Backend (Uvicorn): http://localhost:8000"
	@echo "  Admin Panel: http://localhost:8000/admin/"
	@echo "  Database: localhost:3307"
	@echo "  Redis: localhost:6379"

# Development workflow helpers
dev-setup: test-build test-up test-migrate
	@echo "Development environment setup complete!"
	@echo "Next steps:"
	@echo "  1. Create superuser: make test-super"
	@echo "  2. View logs: make test-logs"
	@echo "  3. Access admin: http://localhost:8000/admin/"

dev-restart: test-down test-up
	@echo "Development environment restarted!"

# Debugging helpers
debug-uvicorn:
	@echo "Starting Uvicorn in debug mode..."
	docker-compose -f docker-compose.yml exec backend uvicorn backend.asgi:application --host 0.0.0.0 --port 8000 --reload --log-level debug --access-log

debug-shell:
	@echo "Starting debug shell with Uvicorn context..."
	docker-compose -f docker-compose.yml exec backend python manage.py shell_plus