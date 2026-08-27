load:
	python scripts/run_sprint1_load.py

ratios:
	@echo "Ratio engine will be executed in Sprint 2."

test:
	pytest -q

report:
	python scripts/run_dq_validation.py

dashboard:
	@echo "Dashboard module will be executed in Sprint 4."

api:
	@echo "API module will be executed in Sprint 6."

clean:
	python -c "import shutil; from pathlib import Path; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '__pycache__']]"