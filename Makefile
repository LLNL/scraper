test:
	bandit -r scraper/
	flake8 --ignore=E501 scraper/

release:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*
