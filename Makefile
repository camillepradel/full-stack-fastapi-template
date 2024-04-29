get-opentapioca-resources:
	mkdir ./backend/app/opentapioca_resources
	gsutil -m cp \
		"gs://dev-storage-geotrend/ml-models/opentapioca/2023_06_27/classifier.pkl" \
		"gs://dev-storage-geotrend/ml-models/opentapioca/2023_06_27/latest-all.bow.pkl" \
		"gs://dev-storage-geotrend/ml-models/opentapioca/2023_06_27/wikidata_graph.pgrank.npy" \
		./backend/app/opentapioca_resources

start-containers:
	docker compose up

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
