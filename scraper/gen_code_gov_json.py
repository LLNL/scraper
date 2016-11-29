#! /usr/bin/env python

import argparse
import json
import logging
import os

import github3

from code_gov import CodeGovMetadata, CodeGovProject
from code_gov.doe import to_doe_csv

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

    repos = org.iter_repos(type='public')
    projects = [CodeGovProject.from_github3(r) for r in repos]
    logger.debug('Number of projects: %d', len(projects))

    logger.info('Setting Contact Email...')
    for project in projects:
        project['contact']['email'] = org.email

    # code_json = CodeGovMetadata(agency, org.name)
    # code_json['projects'] = projects
    #
    # logger.info('Converting to string...')
    # str_code_json = code_json.to_json()
    # print(str_code_json)
    #
    # logger.info('Writing to file...')
    # filename = 'github-%s-code.json' % (org_name)
    # with open(filename, 'w') as fp:
    #     fp.write(str_code_json)
    #
    # filename = 'github-%s-code.csv' % (org_name)
    # with open(filename, 'w') as fp:
    #     for project in projects:
    #         fp.write(to_doe_csv(project) + '\n')
    #
    # logger.info('Finished writing to: %s', filename)

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

    parser.add_argument('--agency', type=str, nargs='?', default='UNKNOWN', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--organization', type=str, nargs='?', default='UNKNOWN', help='Organization Name')

    parser.add_argument('--github-orgs', type=str, nargs='+', help='GitHub Organizations')
    parser.add_argument('--github-repos', type=str, nargs='+', help='GitHub Repositories')

    parser.add_argument('--to-csv', action='store_true', help='Toggle output to CSV')

    args = parser.parse_args()

    agency = args.agency
    organization = args.organization
    org_names = args.github_orgs or []
    repo_names = args.github_repos or []

    logger.debug('Agency: %s', agency)
    logger.debug('Organization: %s', organization)
    logger.debug('GitHub.com Organizations: %s', org_names)
    logger.debug('GitHub.com Repositories: %s', repo_names)

    code_json = CodeGovMetadata(agency, organization)

    for org_name in org_names:
        code_json['projects'].extend(process_organization(org_name))

    for repo_name in repo_names:
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
