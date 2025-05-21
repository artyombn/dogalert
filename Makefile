filldb_users:
	python3 src/database/management/fill_db_user.py -count 2

filldb_pets:
	python3 src/database/management/fill_db_pet.py -count 2

filldb_reports:
	python3 src/database/management/fill_db_report.py -count 2

startlinters:
	mypy . && ruff check .

startpytest:
	pytest -s -v

run_ngrok:
	ngrok http 8001 --url https://merely-concise-macaw.ngrok-free.app

run_app:
	python3 src/app.py
