init:
    poetry install

test:
    poetry run pytest tests/

.PHONY: init test