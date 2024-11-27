run-dev:
	npm run dev

update-client:
	rm -f openapi.json
	wget http://localhost:8000/api/v1/openapi.json
	node modify-openapi-operationids.js
	npm run generate-client
