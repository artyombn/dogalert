startlinters:
	mypy . && ruff check .

startpytest:
	pytest