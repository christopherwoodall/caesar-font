.PHONY: help build serve clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

build: ## Generate the 25 cipher fonts and pages
	uv run python build.py

serve: ## Start a local webserver for testing (docs/ directory)
	@echo "Starting server at http://localhost:8000"
	@echo "Generator: http://localhost:8000/"
	@echo "Demo:      http://localhost:8000/demo.html"
	@cd docs && python3 -m http.server 8000

clean: ## Remove generated docs/ directory
	rm -rf docs/
