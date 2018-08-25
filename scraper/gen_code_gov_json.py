#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import getpass
import json
import logging
import os
import requests

import stashy

from scraper.code_gov import CodeGovMetadata, CodeGovProject
from scraper.code_gov.doe import to_doe_csv
from scraper.github import gov_orgs, create_session, _check_api_limits
from scraper.util import configure_logging


logger = logging.getLogger(__name__)

# TODO: Might not really want this at global scope
gh = None


def process_organization(org_name):
    """
    Returns a Code.gov standard JSON of GitHub organization projects
    """
    org = gh.organization(org_name)
    repos = org.repositories(type='public')
    num_repos = org.public_repos_count

    WIGGLE_ROOM = 100
    num_requests_needed = 2 * num_repos + WIGGLE_ROOM

    _check_api_limits(gh, min_requests_remaining=num_requests_needed)

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
    Converts a DOE CODE .json file into DOE CODE projects
    """
    doecode_json = json.load(open(doecode_json_filename))
    projects = [CodeGovProject.from_doecode(p) for p in doecode_json['records']]

    return projects


def process_doecode_url(url, key):
    """
    Converts a DOE CODE API .json URL response into DOE CODE projects
    """
    doecode_json = requests.get(url, headers={"Authorization": "Basic " + key}).json()
    projects = [CodeGovProject.from_doecode(p) for p in doecode_json['records']]

    return projects


def main():
    global gh

    parser = argparse.ArgumentParser(description='Scrape code repositories for Code.gov / DOE CODE')

    parser.add_argument('--agency', type=str, nargs='?', default='', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--method', type=str, nargs='?', default='', help='Method of measuring open source')
    parser.add_argument('--organization', type=str, nargs='?', default='', help='Force all repos to report a particular organzation')
    parser.add_argument('--contact-email', type=str, nargs='?', default='', help='Force all repos to report a particular contact email')

    parser.add_argument('--config', type=str, nargs='?', default='', help='Configuration File (*.json)')

    parser.add_argument('--github-orgs', type=str, nargs='+', default=[], help='GitHub Organizations')
    parser.add_argument('--github-repos', type=str, nargs='+', default=[], help='GitHub Repositories')
    parser.add_argument('--github-gov-orgs', action='store_true', help='Use orgs from government.github.com/community')

    parser.add_argument('--to-csv', action='store_true', help='Toggle output to CSV')

    parser.add_argument('--doecode-json', type=str, nargs='?', default=None, help='Path to DOE CODE .json file')

    parser.add_argument('--doecode-url', type=str, nargs='?', default=None, help='URL to DOE CODE .json data')

    parser.add_argument('--doecode-url-key', type=str, nargs='?', default=None, help='DOE CODE API key for accessing --doecode-url')

    parser.add_argument('--output-path', type=str, nargs='?', default='', help='Output path for .json and .csv files')

    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    configure_logging(args.verbose)

    doecode_json = args.doecode_json
    doecode_url = args.doecode_url
    doecode_url_key = args.doecode_url_key

    # DOE CODE JSON parsing does not currently require GitHub connectivity.
    if doecode_json is None and doecode_url is None:
        gh = create_session()

    try:
        config_json = json.load(open(args.config))
    except (FileNotFoundError, json.JSONDecodeError):
        if args.config:
            raise
        config_json = {}

    output_path = config_json.get('output_path', None)
    output_path = args.output_path or output_path
    logger.debug('Output Path: %s', output_path)

    if (output_path is not None and not os.path.exists(output_path)):
        raise RuntimeError('Invalid output path argument provided!  Make sure the output path exists and try again.')

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
        github_orgs.extend(gov_orgs())

    github_repos = config_json.get('github_repos', [])
    github_repos.extend(args.github_repos)
    logger.debug('GitHub.com Repositories: %s', github_repos)

    bitbucket_servers = config_json.get('bitbucket_servers', [])
    bitbucket_servers = [connect_to_bitbucket(s) for s in bitbucket_servers]
    logger.debug('Bitbucket Servers: %s', bitbucket_servers)

    code_json = CodeGovMetadata(agency, method)

    for org_name in sorted(github_orgs, key=str.lower):
        code_json['releases'].extend(process_organization(org_name))

    for repo_name in sorted(github_repos, key=str.lower):
        code_json['releases'].append(process_repository(repo_name))

    for bitbucket in sorted(bitbucket_servers, key=str.lower):
        code_json['releases'].extend(process_bitbucket(bitbucket))

    if doecode_json is not None:
        logger.debug('Queuing DOE CODE JSON: %s', doecode_json)

        if os.path.isfile(doecode_json):
            code_json['releases'].extend(process_doecode(doecode_json))
        elif doecode_json:
            raise FileNotFoundError('Unable to find DOE CODE json file: %s' % doecode_json)

    elif doecode_url is not None:
        logger.debug('Fetching DOE CODE JSON: %s', doecode_url)

        if doecode_url_key is None:
            raise ValueError('DOE CODE: API Key "doecode_url_key" value is missing!')

        code_json['releases'].extend(process_doecode_url(doecode_url, doecode_url_key))

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

    if output_path is not None:
        json_filename = os.path.join(output_path, json_filename)

    logger.info('Writing output to: %s', json_filename)

    with open(json_filename, 'w') as fp:
        logger.info
        fp.write(str_org_projects)

    if args.to_csv:
        csv_filename = 'code.csv'

        if output_path is not None:
            csv_filename = os.path.join(output_path, csv_filename)

        logger.info('Writing output to: %s', csv_filename)

        with open(csv_filename, 'w') as fp:
            for project in code_json['releases']:
                fp.write(to_doe_csv(project) + '\n')


if __name__ == '__main__':
    main()
