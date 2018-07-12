#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging
import os
import re
import tempfile

import github3
import gitlab
import requests

from scraper.util import execute

logger = logging.getLogger(__name__)

EFFORT_REGEX = re.compile(r'Effort = ([\d\.]+) Person-months')


def _license_obj(license):
    """
    A helper function to look up license object information

    Use names from: https://api.github.com/licenses
    """
    obj = None

    if license in ('MIT', 'MIT License'):
        obj = {
            'URL': 'https://api.github.com/licenses/mit',
            'name': 'MIT'
        }
    elif license in ('BSD 2-clause "Simplified" License'):
        obj = {
            'URL': 'https://api.github.com/licenses/bsd-2-clause',
            'name': 'BSD-2-Clause'
        }
    elif license in ('BSD 3-clause "New" or "Revised" License'):
        obj = {
            'URL': 'https://api.github.com/licenses/bsd-3-clause',
            'name': 'BSD-3-Clause'
        }
    elif license in ('Apache License 2.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/apache-2.0',
            'name': 'Apache-2.0'
        }
    elif license in ('GNU General Public License v2.1'):
        obj = {
            'URL': 'https://api.github.com/licenses/gpl-2.1',
            'name': 'GPL-2.1'
        }
    elif license in ('GNU General Public License v2.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/gpl-2.0',
            'name': 'GPL-2.0'
        }
    elif license in ('GNU Lesser General Public License v2.1'):
        obj = {
            'URL': 'https://api.github.com/licenses/lgpl-2.1',
            'name': 'LGPL-2.1'
        }
    elif license in ('GNU General Public License v3.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/gpl-3.0',
            'name': 'GPL-3.0'
        }
    elif license in ('GNU Lesser General Public License v3.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/lgpl-3.0',
            'name': 'LGPL-3.0'
        }
    elif license in ('Eclipse Public License 1.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/epl-1.0',
            'name': 'EPL-1.0',
        }
    elif license in ('Mozilla Public License 2.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/mpl-2.0',
            'name': 'MPL-2.0',
        }
    elif license in ('The Unlicense'):
        obj = {
            'URL': 'https://api.github.com/licenses/unlicense',
            'name': 'Unlicense',
        }
    elif license in ('GNU Affero General Public License v3.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/agpl-3.0',
            'name': 'AGPL-3.0',
        }
    elif license in ('Eclipse Public License 2.0'):
        obj = {
            'URL': 'https://api.github.com/licenses/epl-2.0',
            'name': 'EPL-2.0',
        }

    if obj is None:
        logger.warn('I dont understand the license: %s', license)
        raise ValueError('Aborting!')

    return obj


def _prune_dict_null_str(dictionary):
    """
    Prune the "None" or emptry string values from dictionary items
    """
    for key, value in list(dictionary.items()):
        if value is None or str(value) == '':
            del dictionary[key]

        if isinstance(value, dict):
            dictionary[key] = _prune_dict_null_str(dictionary[key])

    return dictionary


def git_repo_to_sloc(url):
    """
    Given a Git repository URL, returns number of lines of code based on cloc

    Reference:
        - cloc: https://github.com/AlDanial/cloc

    Sample cloc output:
        {
            "header": {
                "cloc_url": "github.com/AlDanial/cloc",
                "cloc_version": "1.74",
                "elapsed_seconds": 0.195950984954834,
                "n_files": 27,
                "n_lines": 2435,
                "files_per_second": 137.78956000769,
                "lines_per_second": 12426.5769858787
            },
            "C++": {
                "nFiles": 7,
                "blank": 121,
                "comment": 314,
                "code": 371
            },
            "C/C++ Header": {
                "nFiles": 8,
                "blank": 107,
                "comment": 604,
                "code": 191
            },
            "CMake": {
                "nFiles": 11,
                "blank": 49,
                "comment": 465,
                "code": 165
            },
            "Markdown": {
                "nFiles": 1,
                "blank": 18,
                "comment": 0,
                "code": 30
            },
            "SUM": {
                "blank": 295,
                "comment": 1383,
                "code": 757,
                "nFiles": 27
            }
        }
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.debug('Cloning: url=%s tmp_dir=%s', url, tmp_dir)

        tmp_clone = os.path.join(tmp_dir, 'clone-dir')

        cmd = ['git', 'clone', '--depth=1', url, tmp_clone]
        execute(cmd)

        cmd = ['cloc', '--json', tmp_clone]
        out, _ = execute(cmd)

        try:
            cloc_json = json.loads(out[1:].replace('\\n', '').replace('\'', ''))
            sloc = cloc_json['SUM']['code']
        except json.decoder.JSONDecodeError:
            logger.debug('Error Decoding: url=%s, out=%s', url, out)
            sloc = 0

    logger.debug('SLOC: url=%s, sloc=%d', sloc)

    return sloc


def compute_labor_hours(sloc):
    """
    Compute the labor hours, given a count of source lines of code

    The intention is to use the COCOMO II model to compute this value.

    References:
    - http://csse.usc.edu/tools/cocomoii.php
    - http://docs.python-guide.org/en/latest/scenarios/scrape/
    """
    # (40 Hours / week) * (52 weeks / year) / (12 months / year) ~= 173.33
    HOURS_PER_PERSON_MONTH = 40.0 * 52 / 12

    cocomo_url = 'http://csse.usc.edu/tools/cocomoii.php'
    page = requests.post(cocomo_url, data={'new_size': sloc})

    try:
        person_months = float(EFFORT_REGEX.search(page.text).group(1))
    except AttributeError:
        # If there is no match, and .search(..) returns None
        person_months = 0

    labor_hours = person_months * HOURS_PER_PERSON_MONTH
    logger.debug('sloc=%d labor_hours=%d', sloc, labor_hours)

    return labor_hours


class CodeGovMetadata(dict):
    """
    Defines the entire contents of a Code.gov 's code.json file

    For details: https://code.gov/#/policy-guide/docs/compliance/inventory-code
    """
    def __init__(self, agency, method, other_method=''):
        # *version: [string] The Code.gov metadata schema version
        self['version'] = '2.0.0'

        # *agency: [string] The agency acronym for Clinger Cohen Act agency, e.g. "GSA" or "DOD"
        self['agency'] = agency.upper()

        # *measurementType: [object] The description of the open source measurement method
        #   *method [enum]: An enumerated list of methods for measuring the open source requirement
        #       cost: Cost of software development.
        #       systems: System certification and accreditation boundaries.
        #       projects: A complete software solution / project.
        #       modules: A self-contained module from a software solution.
        #       linesOfCode: Source lines of code.
        #       other: Another measurement method not referenced above.
        #   ifOther: [string] A one- or two- sentence description of the measurement type used, if 'other' is selected as the value of 'method' field.
        self['measurementType'] = {
            'method': method
        }
        if method == 'other':
            self['measurementType']['ifOther'] = other_method

        # The list of source code releases
        self['releases'] = []

    def to_json(self):
        return json.dumps(self, indent=4, sort_keys=True)


class CodeGovProject(dict):
    """
    Python representation of Code.gov Metadata Schema

    For details: https://code.gov/#/policy-guide/docs/compliance/inventory-code
    """

    def __init__(self):
        # -- REQUIRED FIELDS --

        # *name: [string] The name of the release
        self['name'] = ''

        # repository: [string] The URL of the public project repository
        self['repositoryURL'] = ''

        # *description: [string] A description of the project
        self['description'] = ''

        # *permissions: [object] A description of the usage/restrictions regarding the release
        #   * licenses: [null or array of objects] An object containing license details, if available. If not, null should be used.
        #       URL: [string] The URL of the release license, if available
        #       name: [string] An abbreviation for the name of the license
        #   * usageType: [enum]
        #       openSource: Open source
        #       governmentWideReuse: Government-wide reuse.
        #       exemptByLaw: The sharing of the source code is restricted by law or regulation, including—but not limited to—patent or intellectual property law, the Export Asset Regulations, the International Traffic in Arms Regulation, and the Federal laws and regulations governing classified information.
        #       exemptByNationalSecurity: The sharing of the source code would create an identifiable risk to the detriment of national security, confidentiality of Government information, or individual privacy.
        #       exemptByAgencySystem: The sharing of the source code would create an identifiable risk to the stability, security, or integrity of the agency’s systems or personnel.
        #       exemptByAgencyMission: The sharing of the source code would create an identifiable risk to agency mission, programs, or operations.
        #       exemptByCIO: The CIO believes it is in the national interest to exempt sharing the source code.
        #       exemptByPolicyDate: The release was created prior to the M-16-21 policy (August 8, 2016).
        #   exemptionText: [null or string]
        self['permissions'] = {
            'licenses': None,
            'usageType': '',
            'exemptionText': None
        }

        # *laborHours: [number]: An estimate of total labor hours spent by your organization/component across all versions of this release. This includes labor performed by federal employees and contractors.
        self['laborHours'] = 0

        # *tags: [array] An array of keywords that will be helpful in discovering and searching for the release.
        self['tags'] = []

        # *contact: [object] Information about contacting the project.
        #   *email: [string] An email address to contact the project.
        #   name: [string] The name of a contact or department for the project
        #   twitter: [string] The username of the project's Twitter account
        #   phone: [string] The phone number to contact a project.
        self['contact'] = {
            'email': '',
        }
        # TODO: Currently, the GSA Harvester requires these fields to not be present if they are empty
        #     'name': '',
        #     'URL': '',
        #     'phone': '',
        # }

        # -- OPTIONAL FIELDS --

        # version: [string] The version for this release. For example, "1.0.0."
        # self['version'] = ''

        # organization: [string] The organization or component within the agency that the releases listed belong to. For example, "18F" or "Navy."
        # self['organization'] = ''

        # status: [string] The development status of the project
        #   "Ideation" - brainstorming phase.
        #   "Development" - a release is still in development.
        #   "Alpha" - initial prototyping phase and internal testing.
        #   "Beta" - a project is being tested in public.
        #   "Release Candidate" - a release is nearly ready for production.
        #   "Production" - finished project, with development and maintenance ongoing.
        #   "Archival" - finished project, but no longer actively maintained.
        # self['status'] = ''

        # vcs: [string] A lowercase string with the name of the Version Control System in use on the project.
        # self['vcs'] = ''

        # homepageURL: [string] The URL of the public release homepage.
        # self['homepageURL'] = ''

        # downloadURL: [string] The URL where a distribution of the release can be found.
        # self['downloadURL'] = ''

        # disclaimerText: [string] Short paragraph that includes disclaimer language to accompany the release.
        # self['disclaimerText'] = ''

        # disclaimerURL: [string] The URL where disclaimer language regarding the release can be found.
        # self['disclaimerURL'] = ''

        # languages: [array] A list of strings with the names of the programming languages in use on the release.
        # self['languages'] = []

        # partners: [array] An array of objects including an acronym for each agency partnering on the release and the contact email at such agency.
        #   name: [string] The acronym describing the partner agency.
        #   email: [string] The email address for the point of contact at the partner agency.
        # self['partners'] = []

        # relatedCode: [array] An array of affiliated government repositories that may be a part of the same project. For example, relatedCode for 'code-gov-web' would include 'code-gov-api' and 'code-gov-tools'.
        #   name: [string] The name of the code repository, project, library or release.
        #   URL: [string] The URL where the code repository, project, library or release can be found.
        #   isGovernmentRepo: [boolean] True or False. Is the code repository owned or managed by a federal agency?
        # self['relatedCode'] = []

        # reusedCode: [array] An array of government source code, libraries, frameworks, APIs, platforms or other software used in this release. For example: US Web Design Standards, cloud.gov, Federalist, Digital Services Playbook, Analytics Reporter.
        #   name: [string] The name of the software used in this release.
        #   URL: [string] The URL where the software can be found.
        # self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        # self['date'] = {
        #     'created': '',
        #     'lastModified': '',
        #     'metadataLastUpdated': ''
        # }

    @classmethod
    def from_github3(klass, repository, organization=None):
        """
        Create CodeGovProject object from github3 Repository object
        """
        if not isinstance(repository, github3.repos.repo.Repository):
            raise TypeError('Repository must be a github3 Repository object')

        logger.info('Processing: %s', repository.full_name)

        organization = repository.owner

        project = klass()

        logger.debug('GitHub3: repository=%s', repository)

        # -- REQUIRED FIELDS --

        project['name'] = repository.name

        project['repositoryURL'] = repository.html_url

        project['description'] = repository.description

        # TODO: Update licenses from GitHub API
        project['permissions']['licenses'] = None
        project['permissions']['usageType'] = 'openSource'

        sum_sloc = git_repo_to_sloc(project['repositoryURL'])
        laborHours = compute_labor_hours(sum_sloc)
        project['laborHours'] = laborHours

        # TODO: Compute from GitHub
        project['tags'] = ['github']
        old_accept = repository.session.headers['Accept']
        repository.session.headers['Accept'] = 'application/vnd.github.mercy-preview+json'
        topics = repository._get(repository.url + '/topics').json()
        project['tags'].extend(topics['names'])
        repository.session.headers['Accept'] = old_accept

        project['contact']['email'] = organization.email
        project['contact']['URL'] = organization.html_url

        # -- OPTIONAL FIELDS --

        # project['version'] = ''

        project['organization'] = organization.name

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project['status'] = 'Development'

        project['vcs'] = 'git'

        project['homepageURL'] = repository.html_url

        project['downloadURL'] = repository.download_url

        project['languages'] = [l for l, _ in repository.languages()]

        # project['partners'] = []

        # project['relatedCode'] = []

        # project['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        project['date'] = {
            'created': repository.pushed_at.isoformat(),
            'lastModified': repository.updated_at.isoformat(),
            'metadataLastUpdated': '',
        }

        _prune_dict_null_str(project)

        return project

    @classmethod
    def from_gitlab(klass, repository):
        """
        Create CodeGovProject object from GitLab Repository
        """
        if not isinstance(repository, gitlab.objects.Project):
            raise TypeError('Repository must be a gitlab Repository object')

        project = klass()
        project['name'] = repository.name
        project['description'] = repository.description
        project['license'] = None
        project['openSourceProject'] = 1
        project['governmentWideReuseProject'] = 1
        project['tags'] = repository.tag_list
        project['contact'] = {
            'email': '',
            'name': '',
            'URL': '',
            'phone': '',
        }
        project['status'] = ''
        project['vcs'] = 'git'
        project['repository'] = repository.web_url
        project['homepage'] = ''
        project['downloadURL'] = ''
        project['languages'] = []
        project['partners'] = []
        project['exemption'] = None
        project['updated']['metadataLastUpdated'] = repository.last_activity_at
        # project['updated']['lastCommit'] = repository.pushed_at.isoformat()

        return project

    @classmethod
    def from_stashy(klass, repository):
        """
        Create CodeGovProject object from stashy Repository

        Handles crafting Code.gov Project for Bitbucket Server repositories
        """
        # if not isinstance(repository, stashy.repos.Repository):
        #     raise TypeError('Repository must be a stashy Repository object')
        if not isinstance(repository, dict):
            raise TypeError('Repository must be a dict')

        project = klass()

        # *name: [string] The project name
        project['name'] = repository['name']

        # *description: [string] A description of the project
        description = repository['project'].get('description', 'Unknown')
        project['description'] = 'Project Description: {}'.format(description)

        # *license: [null or string] The URL of the project license, if available. null should be used if not.
        project['license'] = None

        # *openSourceProject: [integer] A value indicating whether or not the project is open source.
        #   0: The project is not open source.
        #   1: The project is open source.
        project['openSourceProject'] = 0

        # *governmentWideReuseProject: [integer] A value indicating whether or not the project is built for government-wide reuse.
        #   0: The project is not built for government-wide reuse.
        #   1: The project is built for government-wide reuse.
        project['governmentWideReuseProject'] = 0

        # *tags: [array] A list of string alphanumeric keywords that identify the project.
        project['tags'] = []

        # *contact: [object] Information about contacting the project.
        #   *email: [string] An email address to contact the project.
        #   name: [string] The name of a contact or department for the project
        #   twitter: [string] The username of the project's Twitter account
        #   phone: [string] The phone number to contact a project.
        project['contact'] = {
            'email': '',
            'name': '',
            'URL': '',
            'phone': '',
        }

        # status: [string] The development status of the project
        #   "Ideation" - brainstorming phase.
        #   "Alpha" - initial prototyping phase and internal testing.
        #   "Beta" - a project is being tested in public.
        #   "Production" - finished project, with development and maintenance ongoing.
        #   "Archival" - finished project, but no longer actively maintained.
        project['status'] = ''

        # vcs: [string] A lowercase string with the name of the Version Control System in use on the project.
        project['vcs'] = 'git'

        # repository: [string] The URL of the public project repository
        project['repository'] = repository['links']['self'][0]['href']

        # homepage: [string] The URL of the public project homepage
        project['homepage'] = ''

        # downloadURL: [string] The URL where a distribution of the project can be found.
        project['downloadURL'] = ''

        # languages: [array] A list of strings with the names of the programming languages in use on the project.
        project['languages'] = []

        # partners: [array] A list of strings containing the acronyms of agencies partnering on the project.
        project['partners'] = []

        # exemption: [integer] The exemption that excuses the project from government-wide reuse.
        #   1: The sharing of the source code is restricted by law or regulation, including—but not limited to—patent or intellectual property law, the Export Asset Regulations, the International Traffic in Arms Regulation, and the Federal laws and regulations governing classified information.
        #   2: The sharing of the source code would create an identifiable risk to the detriment of national security, confidentiality of Government information, or individual privacy.
        #   3: The sharing of the source code would create an identifiable risk to the stability, security, or integrity of the agency's systems or personnel.
        #   4: The sharing of the source code would create an identifiable risk to agency mission, programs, or operations.
        #   5: The CIO believes it is in the national interest to exempt sharing the source code.
        project['exemption'] = None

        # updated: [object] Dates that the project and metadata have been updated.
        #   metadataLastUpdated: [string] A date in YYYY-MM-DD or ISO 8601 format indicating when the metadata in this file was last updated.
        #   lastCommit: [string] A date in ISO 8601 format indicating when the last commit to the project repository was.
        #   sourceCodeLastModified: [string] A field intended for closed-source software and software outside of a VCS. The date in YYYY-MM-DD or ISO 8601 format that the source code or package was last updated.
        # project['updated']['metadataLastUpdated'] = None
        # project['updated']['lastCommit'] = None

        return project

    @classmethod
    def from_doecode(klass, record):
        """
        Create CodeGovProject object from DOE CODE record

        Handles crafting Code.gov Project
        """
        if not isinstance(record, dict):
            raise TypeError('`record` must be a dict')

        project = klass()

        # -- REQUIRED FIELDS --

        project['name'] = record['software_title']
        logger.debug('DOE CODE: software_title="%s"', record['software_title'])

        link = record.get('repository_link', '')
        if not link:
            link = record.get('landing_page')
            logger.warning('DOE CODE: No repositoryURL, using landing_page: %s', link)

        project['repositoryURL'] = link

        project['description'] = record['description']

        licenses = set(record['licenses'])
        licenses.discard(None)
        logger.debug('DOE CODE: licenses=%s', licenses)

        license_objects = []
        if 'Other' in licenses:
            licenses.remove('Other')
            license_objects = [{
                'name': 'Other',
                'URL': record['proprietary_url']
            }]

        if licenses:
            license_objects.extend([_license_obj(license) for license in licenses])

        project['permissions']['licenses'] = license_objects

        if record['open_source']:
            usage_type = 'openSource'
        else:
            usage_type = 'exemptByLaw'
            project['permissions']['exemptionText'] = 'This source code is restricted by patent and / or intellectual property law.'

        project['permissions']['usageType'] = usage_type

        # TODO: Compute from git repo
        project['laborHours'] = 0

        project['tags'] = ['DOE CODE']
        lab_name = record.get('lab_display_name')
        if lab_name is not None:
            project['tags'].append(lab_name)

        project['contact']['email'] = record['owner']
        # project['contact']['URL'] = ''
        # project['contact']['name'] = ''
        # project['contact']['phone'] = ''

        # -- OPTIONAL FIELDS --

        if 'version_number' in record and record['version_number']:
            project['version'] = record['version_number']

        if lab_name is not None:
            project['organization'] = lab_name

        # Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        status = record.get('ever_announced')
        if status is None:
            raise ValueError('DOE CODE: Unable to determine "ever_announced" value!');
        elif status:
            status = 'Production'
        else:
            status = 'Development'

        project['status'] = status

        vcs = None
        link = project['repositoryURL']
        if 'github.com' in link:
            vcs = 'git'
        if vcs is None:
            logger.debug('DOE CODE: Unable to determine vcs for: name="%s", repositoryURL=%s', project['name'], link)
            vcs = ''
        if vcs:
            project['vcs'] = vcs

        url = record.get('landing_page', '')
        if url:
            project['homepageURL'] = url

        # record['downloadURL'] = ''

        # self['disclaimerText'] = ''

        # self['disclaimerURL'] = ''

        if 'programming_languages' in record:
            project['languages'] = record['programming_languages']

        # self['partners'] = []
        #TODO: Look into using record['contributing_organizations']

        # self['relatedCode'] = []

        # self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        project['date'] = {
            'created': record['date_record_added'],
            # 'lastModified': '',
            'metadataLastUpdated': record['date_record_updated']
        }

        return project
