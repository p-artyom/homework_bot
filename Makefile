style:
	black -S -l 79 homework.py
	isort homework.py
	flake8 homework.py

run:
	python homework.py
