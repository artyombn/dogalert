startlinters:
	ruff check . && mypy .

startpytest:
	pytest