#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging

import github3
import gitlab
import stashy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

DOE_LAB_MAPPING = {
    'AMES': 'Ames Laboratory (AMES)',
    'ANL': 'Argonne National Laboratory (ANL)',
    'BNL': 'Brookhaven National Laboratory (BNL)',
    'INL': 'Idaho National Laboratory (INL)',
    'LANL': 'Los Alamos National Laboratory (LANL)',
    'LBNL': 'Lawrence Berkeley National Laboratory (LBNL)',
    'LLNL': 'Lawrence Livermore National Laboratory (LLNL)',
    'NETL': 'National Energy Technology Laboratory (NETL)',
    'NREL': 'National Renewable Energy Laboratory (NREL)',
    'ORNL': 'Oak Ridge National Laboratory (ORNL)',
    'OSTI': 'Office of Scientific and Technical Information (OSTI)',
    'PNNL': 'Pacific Northwest National Laboratory (PNNL)',
    'SNL': 'Sandia National Laboratories (SNL)',
    'TJNAF': 'Thomas Jefferson National Accelerator Facility (TJNAF)',
}


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
    elif license in ('Other'):
        obj = {
            'URL': 'https://doecode.osti.gov',
            'name': 'Other',
        }

    if obj is None:
        logger.warn('I dont understand the license: %s', license)
        raise ValueError('Aborting!')

    return obj


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
            'name': '',
            'URL': '',
            'phone': '',
        }

        # -- OPTIONAL FIELDS --

        # version: [string] The version for this release. For example, "1.0.0."
        self['version'] = ''

        # organization: [string] The organization or component within the agency that the releases listed belong to. For example, "18F" or "Navy."
        self['organization'] = ''

        # status: [string] The development status of the project
        #   "Ideation" - brainstorming phase.
        #   "Development" - a release is still in development.
        #   "Alpha" - initial prototyping phase and internal testing.
        #   "Beta" - a project is being tested in public.
        #   "Release Candidate" - a release is nearly ready for production.
        #   "Production" - finished project, with development and maintenance ongoing.
        #   "Archival" - finished project, but no longer actively maintained.
        self['status'] = ''

        # vcs: [string] A lowercase string with the name of the Version Control System in use on the project.
        self['vcs'] = ''

        # homepageURL: [string] The URL of the public release homepage.
        self['homepageURL'] = ''

        # downloadURL: [string] The URL where a distribution of the release can be found.
        self['downloadURL'] = ''

        # disclaimerText: [string] Short paragraph that includes disclaimer language to accompany the release.
        self['disclaimerText'] = ''

        # disclaimerURL: [string] The URL where disclaimer language regarding the release can be found.
        self['disclaimerURL'] = ''

        # languages: [array] A list of strings with the names of the programming languages in use on the release.
        self['languages'] = []

        # partners: [array] An array of objects including an acronym for each agency partnering on the release and the contact email at such agency.
        #   name: [string] The acronym describing the partner agency.
        #   email: [string] The email address for the point of contact at the partner agency.
        self['partners'] = []

        # relatedCode: [array] An array of affiliated government repositories that may be a part of the same project. For example, relatedCode for 'code-gov-web' would include 'code-gov-api' and 'code-gov-tools'.
        #   name: [string] The name of the code repository, project, library or release.
        #   URL: [string] The URL where the code repository, project, library or release can be found.
        #   isGovernmentRepo: [boolean] True or False. Is the code repository owned or managed by a federal agency?
        self['relatedCode'] = []

        # reusedCode: [array] An array of government source code, libraries, frameworks, APIs, platforms or other software used in this release. For example: US Web Design Standards, cloud.gov, Federalist, Digital Services Playbook, Analytics Reporter.
        #   name: [string] The name of the software used in this release.
        #   URL: [string] The URL where the software can be found.
        self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        self['date'] = {
            'created': '',
            'lastModified': '',
            'metadataLastUpdated': ''
        }

    @classmethod
    def from_github3(klass, repository):
        """
        Create CodeGovProject object from github3 Repository object
        """
        if not isinstance(repository, github3.repos.repo.Repository):
            raise TypeError('Repository must be a github3 Repository object')

        logger.info('Processing: %s', repository.full_name)

        project = klass()

        # -- REQUIRED FIELDS --

        project['name'] = repository.name

        project['repositoryURL'] = record.get('repository_link', '')

        project['description'] = record['description']

        licenses = set(record['licenses'])
        licenses.discard(None)
        logger.debug('DOECode: licenses=%s', licenses)
        if licenses:
            license_objects = [_license_obj(license) for license in licenses]
            project['permissions']['licenses'] = license_objects

        # TODO: Need to
        if record['open_source']:
            usage_type = 'openSource'
        elif record['accessibility'] in ('OS',):
            usage_type = 'openSource'
        else:
            logger.warn('DOECode: Unable to determine usage_type')
            logger.warn('DOECode: open_source=%s', record['open_source'])
            logger.warn('DOECode: accessibility=%s', record['accessibility'])
            logger.warn('DOECode: access_limitations=%s', record['access_limitations'])
            usage_type = ''
        project['permissions']['usageType'] = usage_type

        # TODO: Compute from git repo
        project['laborHours'] = 0

        project['tags'] = ['doecode']

        project['contact'] = {
            'email': record['owner'],
            'name': '',
            'URL': '',
            'phone': '',
        }

        # -- OPTIONAL FIELDS --

        # record['version'] = ''

        project['organization'] = record['site_ownership_code']

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project['status'] = 'Development'

        vcs = None
        link = project['repositoryURL']
        if 'github.com' in link:
            vcs = 'git'
        if vcs is None:
            logger.debug('Unable to determine vcs for: %s', link)
            vcs = ''
        project['vcs'] = vcs

        project['homepageURL'] = record.get('landing_page', '')

        # record['downloadURL'] = ''

        # self['disclaimerText'] = ''

        # self['disclaimerURL'] = ''

        # self['languages'] = []

        # self['partners'] = []
        logger.debug('DOECode: contributing_organizations=%s', record['contributing_organizations'])

        # self['relatedCode'] = []

        # self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        project['date'] = {
            'created': record['date_record_added'],
            'lastModified': '',
            'metadataLastUpdated': record['date_record_updated']
        }








        # *name: [string] The project name
        project['name'] = repository.name

        # *description: [string] A description of the project
        project['description'] = repository.description

        # *license: [null or string] The URL of the project license, if available. null should be used if not.
        project['license'] = None

        # *openSourceProject: [integer] A value indicating whether or not the project is open source.
        #   0: The project is not open source.
        #   1: The project is open source.
        project['openSourceProject'] = 1

        # *governmentWideReuseProject: [integer] A value indicating whether or not the project is built for government-wide reuse.
        #   0: The project is not built for government-wide reuse.
        #   1: The project is built for government-wide reuse.
        project['governmentWideReuseProject'] = 1

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
        project['repository'] = repository.html_url

        # homepage: [string] The URL of the public project homepage
        project['homepage'] = repository.homepage

        # downloadURL: [string] The URL where a distribution of the project can be found.
        project['downloadURL'] = ''

        # languages: [array] A list of strings with the names of the programming languages in use on the project.
        project['languages'] = [l for l, _ in repository.languages()]

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
        project['updated']['metadataLastUpdated'] = repository.updated_at.isoformat()
        project['updated']['lastCommit'] = repository.pushed_at.isoformat()

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
        Create CodeGovProject object from DOECode record

        Handles crafting Code.gov Project
        """
        if not isinstance(record, dict):
            raise TypeError('`record` must be a dict')

        project = klass()

        # -- REQUIRED FIELDS --

        project['name'] = record['software_title']
        logger.debug('Software Title: %s', project['name'])

        project['repositoryURL'] = record.get('repository_link', '')

        project['description'] = record['description']

        licenses = set(record['licenses'])
        licenses.discard(None)
        logger.debug('DOECode: licenses=%s', licenses)
        if licenses:
            license_objects = [_license_obj(license) for license in licenses]
            project['permissions']['licenses'] = license_objects

        # TODO: Need to
        if record['open_source']:
            usage_type = 'openSource'
        elif record['accessibility'] in ('OS',):
            usage_type = 'openSource'
        else:
            logger.warn('DOECode: Unable to determine usage_type')
            logger.warn('DOECode: open_source=%s', record['open_source'])
            logger.warn('DOECode: accessibility=%s', record['accessibility'])
            logger.warn('DOECode: access_limitations=%s', record['access_limitations'])
            usage_type = ''
        project['permissions']['usageType'] = usage_type

        # TODO: Compute from git repo
        project['laborHours'] = 0

        project['tags'] = ['doecode']
        site_code = record['site_ownership_code']
        if site_code in DOE_LAB_MAPPING:
            project['tags'].append(DOE_LAB_MAPPING[site_code])

        project['contact'] = {
            'email': record['owner'],
            'name': '',
            'URL': '',
            'phone': '',
        }

        # -- OPTIONAL FIELDS --

        # record['version'] = ''

        project['organization'] = record['site_ownership_code']

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project['status'] = 'Production'

        vcs = None
        link = project['repositoryURL']
        if 'github.com' in link:
            vcs = 'git'
        if vcs is None:
            logger.debug('Unable to determine vcs for: %s', link)
            vcs = ''
        project['vcs'] = vcs

        project['homepageURL'] = record.get('landing_page', '')

        # record['downloadURL'] = ''

        # self['disclaimerText'] = ''

        # self['disclaimerURL'] = ''

        # self['languages'] = []

        # self['partners'] = []
        logger.debug('DOECode: contributing_organizations=%s', record['contributing_organizations'])

        # self['relatedCode'] = []

        # self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        project['date'] = {
            'created': record['date_record_added'],
            'lastModified': '',
            'metadataLastUpdated': record['date_record_updated']
        }

        return project
