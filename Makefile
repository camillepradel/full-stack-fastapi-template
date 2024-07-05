up:
	docker compose up

start-db-container:
	docker compose up db

stop-containers:
	docker compose down

clean-restart-containers:
	docker compose down -v
	docker compose build
	docker compose up

bash-inside-backend:
	docker compose exec backend bash

see-all-logs:
	docker compose logs

see-backend-logs:
	docker compose logs backend
