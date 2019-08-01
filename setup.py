#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as fh:
    long_description = fh.read()

with open('requirements/production.txt') as fp:
    lines = [x.strip() for x in fp.readlines() if x]
    install_reqs = [x for x in lines if not x.startswith('#')]

setup(
    name='llnl-scraper',
    version='0.8.1',
    description='Package for extracting software repository metadata',
    long_description=long_description,
    long_description_content_type='text/markdown',
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
