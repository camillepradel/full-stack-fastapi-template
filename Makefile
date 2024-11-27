up:
	docker compose up

up-db:
	docker compose up db

down:
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

run-kuzu-explorer:
	docker run -p 8000:8000 -v ./dataset:/database --rm kuzudb/explorer:0.6.0
