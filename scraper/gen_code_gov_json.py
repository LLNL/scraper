#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import getpass
import json
import logging
import os

import github3
import stashy
import requests
import yaml

from scraper.code_gov import CodeGovMetadata, CodeGovProject
from scraper.code_gov.doe import to_doe_csv

logger = logging.getLogger(__name__)

# TODO: Might not really want this at global scope
token = os.environ['GITHUB_API_TOKEN']
gh = github3.login(token=token)

if gh is None:
    raise RuntimeError('Invalid GITHUB_API_TOKEN in environment')


def _configure_logging(verbose=False):
    # logging.basicConfig(level=logging.INFO)

    # logging.getLogger('github3').propogate = False

    handler = logging.StreamHandler()
    if verbose:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)

    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)


def process_organization(org_name):
    """
    Returns a Code.gov standard JSON of GitHub organization projects
    """
    org = gh.organization(org_name)
    repos = org.repositories(type='public')
    num_repos = org.public_repos_count

    logger.info('Processing GitHub Org: %s (%d public repos)', org_name, num_repos)

    projects = [CodeGovProject.from_github3(r) for r in repos]

    logger.debug('Setting Contact Email to: %s', org.email)
    for project in projects:
        project['contact']['email'] = org.email

    return projects


def process_repository(repository_name):
    """
    Returns a Code.gov standard JSON of GitHub organization projects
    """
    logger.info('Processing GitHub Repo: %s', repository_name)

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


def government_at_github():
    """
    Returns a list of US Government GitHub orgs

    Based on: https://government.github.com/community/
    """
    us_gov_github_orgs = set()

    gov_yml = requests.get('https://raw.githubusercontent.com/github/government.github.com/gh-pages/_data/governments.yml')
    gov_yml_json = yaml.load(gov_yml.text)
    us_gov_github_orgs.update(gov_yml_json['U.S. Federal'])
    us_gov_github_orgs.update(gov_yml_json['U.S. Military and Intelligence'])

    gov_labs_yml = requests.get('https://raw.githubusercontent.com/github/government.github.com/gh-pages/_data/research.yml')
    gov_labs_yml_json = yaml.load(gov_labs_yml.text)
    us_gov_github_orgs.update(gov_labs_yml_json['U.S. Research Labs'])

    return list(us_gov_github_orgs)


def main():
    parser = argparse.ArgumentParser(description='Scrape code repositories for Code.gov / DOECode')

    parser.add_argument('--agency', type=str, nargs='?', default='', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--method', type=str, nargs='?', default='', help='Method of measuring open source')
    parser.add_argument('--organization', type=str, nargs='?', default='', help='Force all repos to report a particular organzation')
    parser.add_argument('--contact-email', type=str, nargs='?', default='', help='Force all repos to report a particular contact email')

    parser.add_argument('--config', type=str, nargs='?', default='', help='Configuration File (*.json)')

    parser.add_argument('--github-orgs', type=str, nargs='+', default=[], help='GitHub Organizations')
    parser.add_argument('--github-repos', type=str, nargs='+', default=[], help='GitHub Repositories')
    parser.add_argument('--github-gov-orgs', action='store_true', help='Use orgs from government.github.com/community')

    parser.add_argument('--to-csv', action='store_true', help='Toggle output to CSV')

    parser.add_argument('--doecode-json', type=str, nargs='?', default='', help='Path to DOECode .json file')

    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    _configure_logging(args.verbose)

    try:
        config_json = json.load(open(args.config))
    except (FileNotFoundError, json.JSONDecodeError):
        if args.config:
            raise
        config_json = {}

    agency = config_json.get('agency', 'UNKNOWN')
    agency = args.agency or agency
    logger.debug('Agency: %s', agency)

    method = config_json.get('method', 'other')
    method = args.method or method
    logger.debug('Inventory Method: %s', method)

    organization = config_json.get('organization', '')
    organization = args.organization or organization
    logger.debug('Organization: %s', organization)

    contact_email = config_json.get('contact_email', '')
    contact_email = args.contact_email or contact_email
    logger.debug('Contact Email: %s', contact_email)

    github_orgs = config_json.get('github_orgs', [])
    github_orgs.extend(args.github_orgs)
    logger.debug('GitHub.com Organizations: %s', github_orgs)

    if args.github_gov_orgs:
        github_orgs.extend(government_at_github())

    github_repos = config_json.get('github_repos', [])
    github_repos.extend(args.github_repos)
    logger.debug('GitHub.com Repositories: %s', github_repos)

    bitbucket_servers = config_json.get('bitbucket_servers', [])
    bitbucket_servers = [connect_to_bitbucket(s) for s in bitbucket_servers]
    logger.debug('Bitbucket Servers: %s', bitbucket_servers)

    doecode_json = args.doecode_json
    logger.debug('Queuing DOE Code JSON: %s', doecode_json)

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

    # Force certain fields
    if organization:
        logger.debug('Forcing Organiation to: %s', organization)
        for release in code_json['releases']:
            release['organization'] = organization

    if contact_email:
        logger.debug('Forcing Contact Email to: %s', contact_email)
        for release in code_json['releases']:
            release['contact']['email'] = contact_email

    str_org_projects = code_json.to_json()

    # -- I don't believe we need to be outputing to JSON to the console
    #   -- Maybe if "very verbose" ?
    # if args.verbose:
    #     print(str_org_projects)

    logger.info('Number of Projects: %s', len(code_json['releases']))

    json_filename = 'code.json'
    logger.info('Writing output to: %s', json_filename)

    with open(json_filename, 'w') as fp:
        logger.info
        fp.write(str_org_projects)

    if args.to_csv:
        csv_filename = 'code.csv'
        with open(csv_filename, 'w') as fp:
            for project in code_json['releases']:
                fp.write(to_doe_csv(project) + '\n')


if __name__ == '__main__':
    main()
