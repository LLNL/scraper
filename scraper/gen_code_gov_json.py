#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import getpass
import json
import logging
import os

import stashy

from scraper import code_gov
from scraper.code_gov.doe import to_doe_csv
from scraper.util import configure_logging
from scraper import doecode


logger = logging.getLogger(__name__)


def connect_to_bitbucket(server_url):
    username = getpass.getuser()
    password = getpass.getpass('%s Password: ' % (server_url))
    return stashy.connect(server_url, username, password)


def process_bitbucket(bitbucket):
    if not isinstance(bitbucket, stashy.client.Stash):
        raise TypeError('argument must be a Stash Client object')

    repos = bitbucket.repos.all()
    projects = [code_gov.Project.from_stashy(r) for r in repos]

    return projects


def main():
    parser = argparse.ArgumentParser(description='Scrape code repositories for Code.gov / DOE CODE')

    parser.add_argument('--agency', type=str, nargs='?', default='', help='Agency Label, e.g. "DOE"')
    parser.add_argument('--method', type=str, nargs='?', default='', help='Method of measuring open source')
    parser.add_argument('--organization', type=str, nargs='?', default='', help='Force all repos to report a particular organzation')
    parser.add_argument('--contact-email', type=str, nargs='?', default='', help='Force all repos to report a particular contact email')

    parser.add_argument('--config', type=str, nargs='?', default='', help='Configuration File (*.json)')

    # parser.add_argument('--github-orgs', type=str, nargs='+', default=[], help='GitHub Organizations')
    # parser.add_argument('--github-repos', type=str, nargs='+', default=[], help='GitHub Repositories')
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

    # TODO: Will want to re-work this in as a special demo case
    # if args.github_gov_orgs:
    #     github_orgs.extend(gov_orgs())

    code_json = code_gov.process_config(config_json)

    if doecode_json is not None:
        logger.debug('Queuing DOE CODE JSON: %s', doecode_json)

        if os.path.isfile(doecode_json):
            records = doecode.process_json(doecode_json)
            projects = [code_gov.Project.from_doecode() for r in records]
            code_json['releases'].extend(projects)
        elif doecode_json:
            raise FileNotFoundError('Unable to find DOE CODE json file: %s' % doecode_json)

    elif doecode_url is not None:
        logger.debug('Fetching DOE CODE JSON: %s', doecode_url)

        if doecode_url_key is None:
            raise ValueError('DOE CODE: API Key "doecode_url_key" value is missing!')

        records = doecode.process_url(doecode_url, doecode_url_key)
        projects = [code_gov.Project.from_doecode() for r in records]
        code_json['releases'].extend(projects)

    code_gov.force_attributes(code_json, config_json)

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
