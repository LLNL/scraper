#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import logging

import github3

from scraper import github
from scraper.util import configure_logging

logger = logging.getLogger(__name__)

LLNL_NOTICE = None


def repo_has_license(repo):
    """
    Check that repository has a detectable LICENSE file
    """
    license = repo.license
    if not license:
        logger.error('LICENSE missing: repo=%s', repo.full_name)
        return False

    logger.debug('repo=%s license=%s', repo.full_name, license)

    return True


def repo_has_readme(repo):
    """
    Check that repository has a detectable README file
    """
    if not repo.readme:
        logger.error('README missing: repo=%s', repo.full_name)
        return False

    logger.debug('repo=%s readme=%s', repo.full_name, repo.readme)

    return True


def repo_has_notice(repo, notice):
    """
    Check that repository has the proper LLNL NOTICE file
    """
    if not isinstance(notice, github3.repos.contents.Contents):
        raise TypeError('Invalid notice provided: %s', notice)

    repo_notice = repo.file_contents('NOTICE')

    if repo_notice != notice:
        logger.error('NOTICE file missing: repo=%s', repo.full_name)
        return False

    return True


def all_repo_checks(repo):
    """
    Perform all repository level checks
    """
    license = repo_has_license(repo)
    readme = repo_has_readme(repo)
    notice = repo_has_notice(repo, LLNL_NOTICE)

    logger.info('repo=%s license=%s readme=%s notice=%s', repo.full_name, license, readme, notice)


def check_2fa(org):
    """
    Check to ensure all organization members have 2FA enabled
    """
    mfa_disabled = org.members_filters('2fa_disabled')

    for user in mfa_disabled:
        logger.info('2FA disabled: user=%s email=%s', user.name, user.email)


def main():
    parser = argparse.ArgumentParser(description='Script for auditing specific requirements for GitHub.com Repositories')
    parser.add_argument('--organization', type=str, default='llnl', help='GitHub Organization to Audit')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    configure_logging(args.verbose)

    gh_session = github.connect()
    llnl_github_io = gh_session.repository('llnl', 'llnl.github.io')
    global LLNL_NOTICE
    LLNL_NOTICE = llnl_github_io.file_contents('about/licenses/NOTICE')

    orgs = [gh_session.organization(args.organization)]

    user = gh_session.me
    for org in orgs:
        admins = org.member_roles('admin')
        if user not in admins:
            logger.error('You are not an owner of %s', org)
            logger.error('Aborting!')
            return -1

        check_2fa(org)

    for repo in github.query_repos(gh_session, orgs, public_only=False):
        all_repo_checks(repo)


if __name__ == '__main__':
    main()
