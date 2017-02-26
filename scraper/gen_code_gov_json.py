#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import json
import logging
import os

import github3

from scraper.code_gov import CodeGovMetadata, CodeGovProject
from scraper.code_gov.doe import to_doe_csv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# TODO: Might not really want this at global scope
token = os.environ['GITHUB_API_TOKEN']
gh = github3.login(token=token)

if gh is None:
    raise RuntimeError('Invalid GITHUB_API_TOKEN in environment')


def process_organization(org_name):
    """
    Returns a Code.gov standard JSON of GitHub organization projects
    """
    org = gh.organization(org_name)

    repos = org.repositories(type='public')
    projects = [CodeGovProject.from_github3(r) for r in repos]
    logger.debug('Number of projects: %d', len(projects))

    logger.info('Setting Contact Email...')
    for project in projects:
        project['contact']['email'] = org.email

    return projects


def process_repository(repository_name):
    """
    Returns a Code.gov standard JSON of GitHub organization projects
    """
    org, name = repository_name.split('/')
    repo = gh.repository(org, name)

    project = CodeGovProject.from_github3(repo)

    return project


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--agency', type=str, nargs='?', default='', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--organization', type=str, nargs='?', default='', help='Organization Name')

    parser.add_argument('--config', type=str, nargs='?', default='', help='Configuration File (*.json)')

    parser.add_argument('--github-orgs', type=str, nargs='+', default=[], help='GitHub Organizations')
    parser.add_argument('--github-repos', type=str, nargs='+', default=[], help='GitHub Repositories')

    parser.add_argument('--to-csv', action='store_true', help='Toggle output to CSV')

    args = parser.parse_args()

    try:
        config_json = json.load(open(args.config))
    except (FileNotFoundError, json.JSONDecodeError):
        if args.config:
            raise
        config_json = {}

    agency = config_json.get('agency', 'UNKNOWN')
    organization = config_json.get('organization', 'UNKNOWN')
    github_orgs = config_json.get('github_orgs', [])
    github_repos = config_json.get('github_repos', [])

    agency = args.agency or agency
    organization = args.organization or organization
    github_orgs.extend(args.github_orgs)
    github_repos.extend(args.github_repos)

    logger.debug('Agency: %s', agency)
    logger.debug('Organization: %s', organization)
    logger.debug('GitHub.com Organizations: %s', github_orgs)
    logger.debug('GitHub.com Repositories: %s', github_repos)

    code_json = CodeGovMetadata(agency, organization)

    for org_name in github_orgs:
        code_json['projects'].extend(process_organization(org_name))

    for repo_name in github_repos:
        code_json['projects'].append(process_repository(repo_name))

    str_org_projects = code_json.to_json()
    print(str_org_projects)
    with open('code.json', 'w') as fp:
        fp.write(str_org_projects)

    if args.to_csv:
        with open('code.csv', 'w') as fp:
            for project in code_json['projects']:
                fp.write(to_doe_csv(project) + '\n')

    logger.info('Agency: %s', agency)
    logger.info('Organization: %s', organization)
    logger.info('Number of Projects: %s', len(code_json['projects']))
