PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
UVICORN ?= $(VENV)/bin/uvicorn
TEST_PYTHON := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))
PYTHONPATH := apps/candidate-mining/src:apps/annotation-tool/backend/src:.:scripts
INPUT ?= data/raw/sample.mp4
EVENTS ?= data/samples/candidate-events.sample.json
RUN_ID ?= local-dev
MANIFEST ?= data/samples/candidate-manifest.sample.json
ANNOTATIONS ?= data/samples/annotation-export.sample.json
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
API_BASE ?= http://$(API_HOST):$(API_PORT)
FRONTEND_PORT ?= 5173
TRIAGE_INPUT ?= data/raw/catalog.json

.PHONY: setup lint test validate-schemas validate-samples candidate-mining annotation-api annotation-tool app frontend-build fetch-videos mine-all fetch-person-model triage-person fetch-eval-videos eval-person validate-dataset coverage-report release

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	cd apps/annotation-tool/frontend && npm install

lint:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) -m compileall -q apps scripts tests
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/check_markdown_links.py

test:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) -m unittest discover -s tests -v

validate-schemas:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/validate_json.py --schemas

validate-samples:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/validate_json.py --samples

candidate-mining:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m candidate_mining.cli --input $(INPUT) --events $(EVENTS) --output outputs/runs/$(RUN_ID) --random-seed 42

annotation-api:
	PYTHONPATH=$(PYTHONPATH) $(UVICORN) annotation_api.app:app --host $(API_HOST) --port $(API_PORT)

annotation-tool:
	cd apps/annotation-tool/frontend && VITE_API_BASE=$(API_BASE) npm run dev -- --host 127.0.0.1 --port $(FRONTEND_PORT)

frontend-build:
	cd apps/annotation-tool/frontend && npm run build

app: frontend-build
	PYTHONPATH=$(PYTHONPATH) $(UVICORN) annotation_api.app:app --host $(API_HOST) --port $(API_PORT)

fetch-videos:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/fetch_sample_videos.py --output data/raw

mine-all:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/mine_all.py

fetch-person-model:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/fetch_person_model.py

triage-person:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/triage_person.py --input $(TRIAGE_INPUT)

fetch-eval-videos:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/fetch_eval_videos.py

eval-person:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/eval_person_detector.py

validate-dataset:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/validate_dataset.py --manifest $(MANIFEST) --annotations $(ANNOTATIONS)

coverage-report:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/coverage_report.py --manifest $(MANIFEST) --annotations $(ANNOTATIONS) --output outputs/reports/coverage-report.json

release:
	PYTHONPATH=$(PYTHONPATH) $(TEST_PYTHON) scripts/release.py --manifest $(MANIFEST) --annotations $(ANNOTATIONS) --coverage outputs/reports/coverage-report.json --output outputs/releases/v0.1.0
