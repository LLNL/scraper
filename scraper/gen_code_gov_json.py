#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import getpass
import json
import logging
import os

import github3
import stashy

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
    projects = [CodeGovProject.from_github3(r, org) for r in repos]
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


def connect_to_bitbucket(server_url):
    username = getpass.getuser()
    password = getpass.getpass('%s Password: ' % (server_url))
    return stashy.connect(server_url, username, password)


def process_bitbucket(bitbucket):
    if not isinstance(bitbucket, stashy.client.Stash):
        raise TypeError('argument must be a Stash Client object')

    repos = bitbucket.repos.all()
    projects = [CodeGovProject.from_stashy(r) for r in repos]

    return projects


def process_doecode(doecode_json_filename):
    """
    Converts a DOECode .json file into DOECode projects
    """
    doecode_json = json.load(open(doecode_json_filename))
    projects = [CodeGovProject.from_doecode(p) for p in doecode_json['records']]

    return projects


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--agency', type=str, nargs='?', default='', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--method', type=str, nargs='?', default='', help='Method of measuring open source')

    parser.add_argument('--config', type=str, nargs='?', default='', help='Configuration File (*.json)')

    parser.add_argument('--github-orgs', type=str, nargs='+', default=[], help='GitHub Organizations')
    parser.add_argument('--github-repos', type=str, nargs='+', default=[], help='GitHub Repositories')

    parser.add_argument('--to-csv', action='store_true', help='Toggle output to CSV')

    parser.add_argument('--doecode-json', type=str, nargs='?', default='', help='Path to DOECode .json file')

    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    try:
        config_json = json.load(open(args.config))
    except (FileNotFoundError, json.JSONDecodeError):
        if args.config:
            raise
        config_json = {}

    agency = config_json.get('agency', 'UNKNOWN')
    agency = args.agency or agency

    method = config_json.get('method', 'other')
    method = args.method or method

    github_orgs = config_json.get('github_orgs', [])
    github_orgs.extend(args.github_orgs)

    github_repos = config_json.get('github_repos', [])
    github_repos.extend(args.github_repos)

    bitbucket_servers = config_json.get('bitbucket_servers', [])
    bitbucket_servers = [connect_to_bitbucket(s) for s in bitbucket_servers]

    doecode_json = args.doecode_json

    logger.debug('Agency: %s', agency)
    logger.debug('GitHub.com Organizations: %s', github_orgs)
    logger.debug('GitHub.com Repositories: %s', github_repos)

    code_json = CodeGovMetadata(agency, method)

    for org_name in github_orgs:
        code_json['releases'].extend(process_organization(org_name))

    for repo_name in github_repos:
        code_json['releases'].append(process_repository(repo_name))

    for bitbucket in bitbucket_servers:
        code_json['releases'].extend(process_bitbucket(bitbucket))

    if os.path.isfile(doecode_json):
        code_json['releases'].extend(process_doecode(doecode_json))
    elif doecode_json:
        logger.warning('Unbale to find DOECode json file: %s', doecode_json)


    str_org_projects = code_json.to_json()

    if args.verbose:
        print(str_org_projects)

    with open('code.json', 'w') as fp:
        fp.write(str_org_projects)

    if args.to_csv:
        with open('code.csv', 'w') as fp:
            for project in code_json['releases']:
                fp.write(to_doe_csv(project) + '\n')

    logger.info('Agency: %s', agency)
    logger.info('Number of Projects: %s', len(code_json['releases']))
