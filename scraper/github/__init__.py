#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import time

import github3
import requests

from scraper.util import DEFAULT_REQUESTS_TIMEOUTS

logger = logging.getLogger(__name__)


def gov_orgs():
    """
    Returns a list of the names of US Government GitHub organizations

    Based on: https://government.github.com/community/

    Example return:
        {'llnl', '18f', 'gsa', 'dhs-ncats', 'spack', ...}
    """
    us_gov_github_orgs = set()

    gov_orgs_json = requests.get(
        "https://government.github.com/organizations.json",
        timeout=DEFAULT_REQUESTS_TIMEOUTS,
    ).json()

    us_gov_github_orgs.update(gov_orgs_json["governments"]["U.S. Federal"])
    us_gov_github_orgs.update(
        gov_orgs_json["governments"]["U.S. Military and Intelligence"]
    )
    us_gov_github_orgs.update(gov_orgs_json["research"]["U.S. Research Labs"])

    return list(us_gov_github_orgs)


def create_session(token=None, timeouts=None):
    """
    Create a github3.py session connected to GitHub.com

    If token is not provided, will attempt to use the GITHUB_API_TOKEN
    environment variable if present.
    """
    if token is None:
        token = os.environ.get("GITHUB_API_TOKEN", None)

    if timeouts is None:
        timeouts = {}

    custom_session = github3.session.GitHubSession(**timeouts)
    gh_session = github3.GitHub(token=token, session=custom_session)

    if gh_session is None:
        raise RuntimeError("Invalid or missing GITHUB_API_TOKEN")

    return gh_session


def create_enterprise_session(url, token=None, timeouts=None):
    """
    Create a github3.py session for a GitHub Enterprise instance

    If token is not provided, will attempt to use the GITHUB_API_TOKEN
    environment variable if present.
    """
    if timeouts is None:
        timeouts = {}

    custom_session = github3.session.GitHubSession(**timeouts)
    gh_session = github3.GitHubEnterprise(url=url, token=token, session=custom_session)

    if gh_session is None:
        msg = "Unable to connect to GitHub Enterprise (%s) with provided token."
        raise RuntimeError(msg, url)

    return gh_session


def _num_requests_needed(num_repos, factor=2, wiggle_room=100):
    """
    Helper function to estimate the minimum number of API requests needed
    """
    return num_repos * factor + wiggle_room


def _check_api_limits(gh_session, api_required=250):
    """
    Simplified check for API limits

    If necessary, spin in place waiting for API to reset before returning.

    See: https://developer.github.com/v3/#rate-limiting
    """
    api_rates = gh_session.rate_limit()

    api_remaining = api_rates["rate"]["remaining"]
    api_reset = api_rates["rate"]["reset"]
    logger.debug("Rate Limit - %d requests remaining", api_remaining)

    if api_remaining > api_required:
        return

    now_time = time.time()
    time_to_reset = int(api_reset - now_time)
    logger.warning("Rate Limit Depleted - Sleeping for %d seconds", time_to_reset)

    while now_time < api_reset:
        time.sleep(10)
        now_time = time.time()

    return


def connect(url="https://github.com", token=None, timeouts=None):
    """
    Create a GitHub session for making requests
    """

    if timeouts is None:
        timeouts = {}

    gh_session = None
    if url == "https://github.com":
        gh_session = create_session(token, timeouts)
    else:
        gh_session = create_enterprise_session(url, token, timeouts)

    if gh_session is None:
        msg = "Unable to connect to (%s) with provided token."
        raise RuntimeError(msg, url)

    logger.info("Connected to: %s", url)

    return gh_session


def query_repos(gh_session, orgs=None, repos=None, public_only=True):
    """
    Yields GitHub3.py repo objects for provided orgs and repo names

    If orgs and repos are BOTH empty, execute special mode of getting ALL
    repositories from the GitHub Server.

    If public_only is True, will return only those repos that are marked as
    public. Set this to false to return all organizations that the session has
    permissions to access.
    """

    if orgs is None:
        orgs = []
    if repos is None:
        repos = []
    if public_only:
        privacy = "public"
    else:
        privacy = "all"

    _check_api_limits(gh_session, 10)

    for org_name in orgs:
        org = gh_session.organization(org_name)
        num_repos = org.public_repos_count

        _check_api_limits(gh_session, _num_requests_needed(num_repos))

        for repo in org.repositories(type=privacy):
            _check_api_limits(gh_session, 10)
            yield repo

    for repo_name in repos:
        _check_api_limits(gh_session, 10)
        org, name = repo_name.split("/")
        yield gh_session.repository(org, name)

    if not (orgs or repos):
        for repo in gh_session.all_repositories():
            yield repo
