startlinters:
	mypy . && ruff check .

startpytest:
	pytest -s -v

filldb_users:
	python3 src/database/management/fill_db_user.py

filldb_pets:
	python3 src/database/management/fill_db_pet.py