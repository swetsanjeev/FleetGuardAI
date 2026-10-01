.PHONY: up down stop logs ps migrate seed test-database

up:
	python scripts/dev.py up

down:
	python scripts/dev.py down

stop:
	python scripts/dev.py stop

logs:
	python scripts/dev.py logs

ps:
	python scripts/dev.py ps

migrate:
	python scripts/dev.py migrate

seed:
	python scripts/dev.py seed $(SEED_VEHICLE_COUNT)

test-database:
	python -m pytest tests/test_postgres_integration.py tests/test_mongodb_integration.py tests/test_redis_integration.py