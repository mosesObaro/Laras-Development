.PHONY: seed scan digest daily-alert alert stats serve test bundle clean help

help:
	@echo "Pre-University Development System - Commands:"
	@echo "  make seed        - Populate SQLite database from verified seed datasets"
	@echo "  make scan        - Scan live opportunity feeds and purge expired entries"
	@echo "  make daily-alert - Generate and preview calendar-driven daily learning guide"
	@echo "  make digest      - Generate and preview this week's 10-part development digest"
	@echo "  make alert       - Generate and preview top immediate high-priority alert (85+)"
	@echo "  make stats       - Display overall student progress metrics"
	@echo "  make serve       - Launch local interactive web dashboard on http://localhost:8000"
	@echo "  make bundle      - Bundle data/*.json datasets into dashboard/data.js for GitHub Pages"
	@echo "  make test        - Run automated test suite"
	@echo "  make clean       - Remove temporary files and cached outputs"

seed:
	python3 -m preuni_system.cli seed

scan:
	python3 -m preuni_system.cli scan

daily-alert:
	python3 -m preuni_system.cli daily-alert --preview

digest:
	python3 -m preuni_system.cli digest --preview

alert:
	python3 -m preuni_system.cli alert --preview

stats:
	python3 -m preuni_system.cli stats

serve:
	python3 -m preuni_system.cli serve --port 8000

bundle:
	python3 -m preuni_system.bundle_dashboard

test:
	python3 -m unittest discover -s tests

clean:
	rm -rf preuni_system/__pycache__ tests/__pycache__ output/emails/*.html output/emails/*.txt
