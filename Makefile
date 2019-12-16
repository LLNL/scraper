test:
	bandit -r scraper/
	flake8 scraper/
	black --check scraper/
	markdownlint '**/*.md'

release: test
	python setup.py sdist bdist_wheel

upload:
	twine upload --skip-existing dist/*
