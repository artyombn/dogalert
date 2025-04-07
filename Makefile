startlinters:
	mypy . && ruff check .

startpytest:
	pytest -s -v