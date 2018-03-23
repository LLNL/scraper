#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import requests


def gov_orgs():
    """
    Returns a list of US Government GitHub orgs

    Based on: https://government.github.com/community/
    """
    us_gov_github_orgs = set()

    gov_orgs = requests.get('https://government.github.com/organizations.json').json()

    us_gov_github_orgs.update(gov_orgs['governments']['U.S. Federal'])
    us_gov_github_orgs.update(gov_orgs['governments']['U.S. Military and Intelligence'])
    us_gov_github_orgs.update(gov_orgs['research']['U.S. Research Labs'])

    return list(us_gov_github_orgs)
