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
	rm ./database || true
	ln -s ./kuzu_data/2024-11-11_23:09:44.319478_test_dglke_dataset ./database
	docker run -p 8001:8000 -v ./kuzu_data/database:/database --rm kuzudb/explorer:0.6.0
