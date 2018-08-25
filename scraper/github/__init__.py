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
    Returns a list of the names of US Government GitHub organizations

    Based on: https://government.github.com/community/

    Exmample return:
        {'llnl', '18f', 'gsa', 'dhs-ncats', 'spack', ...}
    """
    us_gov_github_orgs = set()

    gov_orgs = requests.get('https://government.github.com/organizations.json').json()

    us_gov_github_orgs.update(gov_orgs['governments']['U.S. Federal'])
    us_gov_github_orgs.update(gov_orgs['governments']['U.S. Military and Intelligence'])
    us_gov_github_orgs.update(gov_orgs['research']['U.S. Research Labs'])

    return list(us_gov_github_orgs)


def create_session(token=None):
    """
    Create a github3.py session connected to GitHub.com

    If token is not provided, will attempt to use the GITHUB_API_TOKEN
    environment variable if present.
    """
    if token is None:
        token = os.environ.get('GITHUB_API_TOKEN')

    gh_session = github3.login(token=token)

    if gh_session is None:
        raise RuntimeError('Invalid or missing GITHUB_API_TOKEN')

    return gh_session


def create_enterprise_session(url, token=None):
    """
    Create a github3.py session for a GitHub Enterprise instance

    If token is not provided, will attempt to use the GITHUB_API_TOKEN
    environment variable if present.
    """

    gh_session = github3.enterprise_login(url=url, token=token)

    if gh_session is None:
        msg = 'Unable to connect to GitHub Enterprise (%s) with provided token.'
        raise RuntimeError(msg, url)

    return gh_session


def _check_api_limits(gh_session, min_requests_remaining=250, sleep_time=15):
    """
    Simplified check for API limits

    If necessary, spin in place waiting for API to reset before returning.

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


def connect_to_github(url, token=None):
    """
    Create a GitHub session for making requests
    """

    gh_session = None
    if url == 'https://github.com':
        gh_session = create_session(token)
    else:
        gh_session = create_enterprise_session(url, token)

    if gh_session is None:
        msg = 'Unable to connect to (%s) with provided token.'
        raise RuntimeError(msg, url)

    return gh_session
