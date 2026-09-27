.PHONY: up seed refresh test demo-reset

up:
	docker compose up -d --build

seed:
	docker compose exec -T db psql -U postgres -d ner -f /data/seed.sql

refresh:
	python api/ingest/weather.py

test:
	pytest tests/

demo-reset:
	docker compose exec -T db psql -U postgres -d ner -c "TRUNCATE report, incident, segment_risk CASCADE;"
	docker compose exec -T db psql -U postgres -d ner -f /data/seed.sql
