.PHONY: pii-scan install install-train test lint validate-tools validate-datasets verify-release tool-conformance benchmark-help doctor

install:
	pip install -e ".[dev]"

install-train:
	pip install -e ".[train,eval]"

test:
	pytest -q

lint:
	ruff check src tests || true

doctor:
	python -m agentmujo_training.cli.main doctor

validate-tools:
	python -m agentmujo_training.cli.main tools validate --registry configs/tools.yaml

validate-datasets:
	python -m agentmujo_training.cli.main dataset validate --input datasets/canonical/function_calling_v0.1.jsonl
	python -m agentmujo_training.cli.main dataset validate --input datasets/canonical/agentic_terminal_v0.1.jsonl

pii-scan:
	python3 tools/pii_scan.py

manifests:
	python3 tools/refresh_manifests.py --check

verify-release:
	python -m agentmujo_training.cli.main dataset verify --version 0.4.0

tool-conformance:
	python -m agentmujo_training.cli.main dataset conformance

benchmark-help:
	python -m agentmujo_training.cli.main benchmark run --help
