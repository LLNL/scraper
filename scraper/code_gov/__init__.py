#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from scraper.code_gov.models import Metadata, Project
from scraper import github, gitlab, bitbucket

logger = logging.getLogger(__name__)


def process_config(config, compute_labor_hours=True):
    """
    Master function to process a Scraper config file

    Returns a Code.gov Metadata file
    """

    agency = config.get('agency', 'UNKNOWN')
    logger.debug('Agency: %s', agency)

    method = config.get('method', 'other')
    logger.debug('Inventory Method: %s', method)

    if config.get('contact_email', None) is None:
        # A default contact email is required to handle the (frequent) case
        # where a project / repository has no available contact email.
        raise RuntimeError('Config file must contain a "contact_email"')

    code_gov_metadata = Metadata(agency, method)

    # Parse config for GitHub repositories
    github_instances = config.get('GitHub', [])
    for instance in github_instances:
        url = instance.get('url', 'https://github.com')
        orgs = instance.get('orgs', [])
        repos = instance.get('repos', [])
        public_only = instance.get('public_only', True)
        token = instance.get('token', None)

        gh_session = github.connect(url, token)

        repos = github.query_repos(gh_session, orgs, repos, public_only)
        for repo in repos:
            code_gov_project = Project.from_github3(repo, labor_hours=compute_labor_hours)
            code_gov_metadata['releases'].append(code_gov_project)

    # Parse config for GitLab repositories
    gitlab_instances = config.get('Gitlab', [])
    for instance in gitlab_instances:
        url = instance.get('url')
        # orgs = instance.get('orgs', [])
        # repos = instance.get('repos', [])
        # public_only = instance.get('public_only', True)
        token = instance.get('token', None)

        gl_session = gitlab.connect(url, token)

        repos = gitlab.query_repos(gl_session)
        for repo in repos:
            code_gov_project = Project.from_gitlab(repo, labor_hours=compute_labor_hours)
            code_gov_metadata['releases'].append(code_gov_project)

    # Parse config for Bitbucket repositories
    bitbucket_instances = config.get('Bitbucket', [])
    for instance in bitbucket_instances:
        url = instance.get('url')
        # orgs = instance.get('orgs', None)
        # public_only = instance.get('public_only', True)
        # token = instance.get('token', None)
        username = instance.get('username')
        password = instance.get('password')

        bb_session = bitbucket.connect(url, username, password)

        repos = bitbucket.all_repos(bb_session)
        for repo in repos:
            code_gov_project = Project.from_stashy(repo, labor_hours=compute_labor_hours)
            code_gov_metadata['releases'].append(code_gov_project)

    return code_gov_metadata


def force_attributes(metadata, config):
    """
    Forces certain fields in the Code.gov Metadata json
    """

    organization = config.get('organization', '')
    logger.debug('Organization: %s', organization)

    contact_email = config.get('contact_email')
    logger.debug('Contact Email: %s', contact_email)

    permissions = config.get('permissions', {})
    default_usage = permissions.get('usageType', '')
    default_exemption_text = permissions.get('exemptionText', '')
    logger.debug('Default usageType: %s', default_usage)
    logger.debug('Default exemptionText: %s', default_exemption_text)

    # Force certain fields
    if organization:
        logger.debug('Forcing Organization to: %s', organization)

    if contact_email:
        logger.debug('Forcing Contact Email to: %s', contact_email)

    for release in metadata['releases']:
        if organization:
            release['organization'] = organization

        if contact_email:
            release['contact']['email'] = contact_email

        if 'licenses' not in release['permissions']:
            release['permissions']['licenses'] = None

        if 'description' not in release:
            release['description'] = 'No description available...'

        if 'usageType' not in release['permissions']:
            release['permissions']['usageType'] = default_usage
            release['permissions']['exemptionText'] = default_exemption_text

    return metadata
