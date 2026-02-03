install:
	uv sync

lint:
	uv run ruff check .
	uv run black --check .
	uv run mypy .

format:
	uv run ruff check . --fix
	uv run black .

check:
	uv run pytest .

test-coverage:
	 uv run pytest --cov --cov-report=xml:coverage.xml --cov-config=.coveragerc --cov-branch