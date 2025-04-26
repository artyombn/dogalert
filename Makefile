startlinters:
	mypy . && ruff check .

startpytest:
	pytest -s -v

filldb_users:
	python3 src/database/management/fill_db_user.py

filldb_pets:
	python3 src/database/management/fill_db_pet.py

filldb_reports:
	python3 src/database/management/fill_db_report.py

run_ngrok:
	ngrok http 8001 --url https://merely-concise-macaw.ngrok-free.app