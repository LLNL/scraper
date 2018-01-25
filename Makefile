test:
	bandit -r scraper/
	flake8 --ignore=E501 scraper/
