# ====== ProPlus • Makefile (Pro+++) ======
# Կոնֆիգ
APP            ?= proplus_app
PNG            ?= app/data_analytics/reports/finance_report.png
PDF            ?= app/data_analytics/reports/finance_report.pdf

# ====== Օգնականներ
.PHONY: help ensure-up ensure-app wait-mongo add report shell logs ps up down rebuild clean

help:
	@echo "Targets:"
	@echo "  make add income=... debt=... savings=...   # գրանցում է գրառումը MongoDB-ում"
	@echo "  make report                                  # նկար + PDF հաշվետվություն"
	@echo "  make shell                                   # մտնել app կոնտեյներ"
	@echo "  make logs                                    # ցույց տալ լոգերը"
	@echo "  make ps|up|down|rebuild|clean                # docker կառավարում"

# Եթե compose չի աշխատում՝ բերում է վերև detached ռեժիմով
ensure-up:
	@docker compose ps >/dev/null 2>&1 || (echo "⚙️ docker compose not ready"; exit 1)
	@running=$$(docker compose ps -q $(APP)); \
	if [ -z "$$running" ]; then \
	  echo "🚀 Starting containers..."; \
	  docker compose up -d; \
	fi

# Ստուգում է, որ APP կոնտեյները առկա է
ensure-app: ensure-up
	@docker compose ps $(APP) | grep -q $(APP) || (echo "❌ app container '$(APP)' not running"; exit 1)

# Սպասում է Mongo-ին (մինչև 20վ)՝ ping-ով
wait-mongo: ensure-app
	@echo "⏳ Waiting for Mongo to be ready..."
	@for i in $$(seq 1 20); do \
	  docker exec -it $(APP) bash -lc "python - <<'PY'\nfrom pymongo import MongoClient,errors\nimport os,sys\nuri=os.getenv('MONGO_URI','mongodb://localhost:27017')\ntry:\n  c=MongoClient(uri, serverSelectionTimeoutMS=500)\n  c.admin.command('ping')\n  print('ok')\n  sys.exit(0)\nexcept errors.PyMongoError:\n  pass\nsys.exit(1)\nPY" >/dev/null 2>&1 && { echo "✅ Mongo is up"; exit 0; } || sleep 1; \
	done; echo "❌ Mongo not ready"; exit 1

# ====== Գործողություններ
add: ensure-app wait-mongo
	@if [ -z "$(income)" ] || [ -z "$(debt)" ] || [ -z "$(savings)" ]; then \
	  echo "❌ Usage: make add income=200000 debt=800000 savings=150000"; exit 2; fi
	@docker exec -it $(APP) bash -lc \
	  "python finance_tracker.py add --income $(income) --debt $(debt) --savings $(savings)"

report: ensure-app wait-mongo
	@docker exec -it $(APP) bash -lc "python finance_tracker.py plot && python generate_report.py"
	@echo "📈 PNG: $(PNG)"
	@echo "📄 PDF: $(PDF)"

shell: ensure-app
	@docker exec -it $(APP) bash

logs:
	@docker compose logs -f --tail=200 $(APP)

ps:
	@docker compose ps

up:
	@docker compose up -d

down:
	@docker compose down

rebuild:
	@docker compose down || true
	@docker compose build --no-cache
	@docker compose up -d

clean:
	@echo "🧹 Removing containers/images/volumes…"
	@docker compose down -v || true
	@docker system prune -af || true
