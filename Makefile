.PHONY: run test lint

run:
	PYTHONPATH=src python3 -m dependency_visualizer --config config.toml --stage 5

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

lint:
	python3 -m pycodestyle --max-line-length=79 src tests
