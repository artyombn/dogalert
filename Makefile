startlinters:
	mypy . && ruff check .

startpytest:
	pytest -s -v

run_ngrok:
	ngrok http 8001 --url https://merely-concise-macaw.ngrok-free.app

run_app:
	python3 src/app.py
