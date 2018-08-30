test:
	bandit -r scraper/
	flake8 --ignore=E501 scraper/

release: test
	python setup.py sdist bdist_wheel

upload:
	twine upload --skip-existing dist/*
