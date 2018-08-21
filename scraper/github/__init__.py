#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os

import requests
import github3
import time

logger = logging.getLogger(__name__)


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


def create_session(token=None):
    """
    Create a github3.py session for making requests
    """
    if token is None:
        token = os.environ.get('GITHUB_API_TOKEN')

    if token is None:
        raise RuntimeError('GITHUB_API_TOKEN not configured in environment')

    gh_session = github3.login(token=token)

    if gh_session is None:
        raise RuntimeError('Invalid GITHUB_API_TOKEN in environment')

    return gh_session


def _check_api_limits(gh_session, min_requests_remaining=250, sleep_time=15):
    """
    Simplified check for API limits

    If necessary, spin in place waiting for API to reset before returning.

    Returns two-tuple of: ``(# API requests remaining, unix time of reset)``

    See: https://developer.github.com/v3/#rate-limiting
    """
    api_rates = gh_session.rate_limit()

    api_remaining = api_rates['rate']['remaining']
    api_reset = api_rates['rate']['reset']
    logger.debug('Rate Limit - %d requests remaining', api_remaining)

    if api_remaining > min_requests_remaining:
        return

    now_time = time.time()
    time_to_reset = int(api_reset - now_time)
    logger.warn('Rate Limit Depleted - Sleeping for %d seconds', time_to_reset)

    while now_time < api_reset:
        time.sleep(10)
        now_time = time.time()

    return
