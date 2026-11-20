.PHONY: run test lint install-dev

run:
	PYTHONPATH=src python3 -m dependency_visualizer --config config.toml --stage 5

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

lint:
	@python3 -m pycodestyle --version >/dev/null 2>&1 || { \
		echo "Install dev dependencies with: make install-dev"; \
		exit 1; \
	}
	python3 -m pycodestyle --max-line-length=79 src tests scripts

install-dev:
	python3 -m pip install -r requirements-dev.txt
