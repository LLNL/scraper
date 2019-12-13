test:
	bandit -r scraper/
	flake8 scraper/
	black --check scraper/

test_npm:
	markdownlint '**/*.md'

release: test
	test_npm
	python setup.py sdist bdist_wheel

upload:
	twine upload --skip-existing dist/*
