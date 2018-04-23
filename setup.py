#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='llnl-scraper',
    version='0.2.1',
    description='Package for extracting ',
    author='Ian Lee',
    author_email='lee1001@llnl.gov',
    url='https://github.com/llnl/scraper',
    packages=find_packages(),
    install_requires=[
        'github3.py>=1.0.0a4',
        'python-gitlab>=0.17',
        'stashy>=0.3',
    ],
    entry_points={
        'console_scripts': [
            'scraper = scraper.gen_code_gov_json:main',
        ]
    },
    scripts=['scripts/codegov_compute_hours.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
