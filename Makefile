APP ?= app

help:
	@echo "make add income=... debt=... savings=..."
	@echo "make report | make shell | make logs"

ensure-up:
	@docker compose up -d >/dev/null

add: ensure-up
	@if [ -z "$(income)" ] || [ -z "$(debt)" ] || [ -z "$(savings)" ]; then \
	  echo "Usage: make add income=200000 debt=800000 savings=150000"; exit 2; fi
	@docker compose exec $(APP) bash -lc "python finance_tracker.py add --income $(income) --debt $(debt) --savings $(savings)"

report: ensure-up
	@docker compose exec $(APP) bash -lc "python finance_tracker.py plot && python generate_report.py"
	@echo "✅ Report ready (PNG/PDF in data_analytics/reports)"

shell: ensure-up
	@docker compose exec $(APP) bash

logs:
	@docker compose logs -f $(APP)

.PHONY: email quick

email:
	docker compose exec app bash -lc "python send_report.py"



quick:
	$(MAKE) report
	$(MAKE) email

.PHONY: quick email offer

offer:
	docker compose up -d app
	docker compose exec app bash -lc "python offer_pdf.py"

# report + email + offer մեկ հրամանով (ցանկության դեպքում)
quick:
	$(MAKE) report
	$(MAKE) email

