#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging

import github3
import gitlab
import stashy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class CodeGovMetadata(dict):
    def __init__(self, agency, organization):
        self['agency'] = agency
        self['organization'] = organization
        self['projects'] = []

    def to_json(self):
        return json.dumps(self, indent=4, sort_keys=True)


class CodeGovProject(dict):
    """
    Python representation of Code.gov Metadata Schema

    See:

    https://github.com/presidential-innovation-fellows/code-gov-web/blob/master/_draft_content/02_compliance/05-metadata-schema-definition.md
    """

    def __init__(self):
        # *name: [string] The project name
        self['name'] = ''

        # *description: [string] A description of the project
        self['description'] = ''

        # *license: [null or string] The URL of the project license, if available. null should be used if not.
        self['license'] = None

        # *openSourceProject: [integer] A value indicating whether or not the project is open source.
        #   0: The project is not open source.
        #   1: The project is open source.
        self['openSourceProject'] = 0

        # *governmentWideReuseProject: [integer] A value indicating whether or not the project is built for government-wide reuse.
        #   0: The project is not built for government-wide reuse.
        #   1: The project is built for government-wide reuse.
        self['governmentWideReuseProject'] = 0

        # *tags: [array] A list of string alphanumeric keywords that identify the project.
        self['tags'] = []

        # *contact: [object] Information about contacting the project.
        #   *email: [string] An email address to contact the project.
        #   name: [string] The name of a contact or department for the project
        #   twitter: [string] The username of the project's Twitter account
        #   phone: [string] The phone number to contact a project.
        self['contact'] = {
            'email': '',
            'name': '',
            'twitter': '',
            'phone': '',
        }

        # status: [string] The development status of the project
        #   "Ideation" - brainstorming phase.
        #   "Alpha" - initial prototyping phase and internal testing.
        #   "Beta" - a project is being tested in public.
        #   "Production" - finished project, with development and maintenance ongoing.
        #   "Archival" - finished project, but no longer actively maintained.
        self['status'] = ''

        # vcs: [string] A lowercase string with the name of the Version Control System in use on the project.
        self['vcs'] = ''

        # repository: [string] The URL of the public project repository
        self['repository'] = ''

        # homepage: [string] The URL of the public project homepage
        self['homepage'] = ''

        # downloadURL: [string] The URL where a distribution of the project can be found.
        self['downloadURL'] = ''

        # languages: [array] A list of strings with the names of the programming languages in use on the project.
        self['languages'] = []

        # partners: [array] A list of strings containing the acronyms of agencies partnering on the project.
        self['partners'] = []

        # exemption: [integer] The exemption that excuses the project from government-wide reuse.
        #   1: The sharing of the source code is restricted by law or regulation, including—but not limited to—patent or intellectual property law, the Export Asset Regulations, the International Traffic in Arms Regulation, and the Federal laws and regulations governing classified information.
        #   2: The sharing of the source code would create an identifiable risk to the detriment of national security, confidentiality of Government information, or individual privacy.
        #   3: The sharing of the source code would create an identifiable risk to the stability, security, or integrity of the agency's systems or personnel.
        #   4: The sharing of the source code would create an identifiable risk to agency mission, programs, or operations.
        #   5: The CIO believes it is in the national interest to exempt sharing the source code.
        self['exemption'] = None

        # updated: [object] Dates that the project and metadata have been updated.
        #   metadataLastUpdated: [string] A date in YYYY-MM-DD or ISO 8601 format indicating when the metadata in this file was last updated.
        #   lastCommit: [string] A date in ISO 8601 format indicating when the last commit to the project repository was.
        #   sourceCodeLastModified: [string] A field intended for closed-source software and software outside of a VCS. The date in YYYY-MM-DD or ISO 8601 format that the source code or package was last updated.
        self['updated'] = {
            'metadataLastUpdated': '',
            'lastCommit': '',
            'sourceCodeLastModified': '',
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
            'twitter': '',
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
            'twitter': '',
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
            'twitter': '',
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
    def from_doecode(klass, repository):
        """
        Create CodeGovProject object from DOECode formatted json file

        Handles crafting Code.gov Project
        """
        if not isinstance(repository, dict):
            raise TypeError('Repository must be a dict')

        project = klass()

        # *name: [string] The project name
        project['name'] = repository['software_title']

        # *description: [string] A description of the project
        project['description'] = repository['description']

        # *license: [null or string] The URL of the project license, if available. null should be used if not.
        project['license'] = ', '.join(repository['licenses'])

        # *openSourceProject: [integer] A value indicating whether or not the project is open source.
        #   0: The project is not open source.
        #   1: The project is open source.
        project['openSourceProject'] = bool(repository['open_source'])

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
            'email': repository['owner'],
            'name': '',
            'twitter': '',
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
        project['repository'] = repository['repository_link']

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
