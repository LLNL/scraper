#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as fh:
    long_description = fh.read()

for line in open('requirements/production.txt').readlines():
    install_reqs = [x.strip() for x in line if line and not x.startswith('#')]

setup(
    name='llnl-scraper',
    version='0.6.0-dev',
    description='Package for extracting software repository metadata',
    long_description=long_description,
    author='Ian Lee',
    author_email='lee1001@llnl.gov',
    url='https://github.com/llnl/scraper',
    packages=find_packages(),
    install_requires=install_reqs,
    entry_points={
        'console_scripts': [
            'scraper = scraper.gen_code_gov_json:main',
        ]
    },
    scripts=[
        'scripts/codegov_compute_hours.py',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
