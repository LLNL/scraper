#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging

from dateutil.parser import parse as date_parse
import github3
import gitlab
from requests.utils import requote_uri

from scraper.github.util import _license_obj
from scraper.util import _prune_dict_null_str, labor_hours_from_url

logger = logging.getLogger(__name__)

POLICY_START_DATE = date_parse("2016-08-08T00:00:00Z")


class Metadata(dict):
    """
    Defines the entire contents of a Code.gov 's code.json file

    For details: https://code.gov/#/policy-guide/docs/compliance/inventory-code
    """

    def __init__(self, agency, method, other_method=""):
        # *version: [string] The Code.gov metadata schema version
        self["version"] = "2.0.0"

        # *agency: [string] The agency acronym for Clinger Cohen Act agency, e.g. "GSA" or "DOD"
        self["agency"] = agency.upper()

        # *measurementType: [object] The description of the open source measurement method
        #   *method [enum]: An enumerated list of methods for measuring the open source requirement
        #       cost: Cost of software development.
        #       systems: System certification and accreditation boundaries.
        #       projects: A complete software solution / project.
        #       modules: A self-contained module from a software solution.
        #       linesOfCode: Source lines of code.
        #       other: Another measurement method not referenced above.
        #   ifOther: [string] A one- or two- sentence description of the measurement type used, if 'other' is selected as the value of 'method' field.
        self["measurementType"] = {"method": method}
        if method == "other":
            self["measurementType"]["ifOther"] = other_method

        # The list of source code releases
        self["releases"] = []

    def to_json(self):
        return json.dumps(self, indent=4, sort_keys=True, ensure_ascii=False)


class Project(dict):
    """
    Python representation of Code.gov Metadata Schema

    For details: https://code.gov/#/policy-guide/docs/compliance/inventory-code
    """

    def __init__(self):
        # -- REQUIRED FIELDS --

        # *name: [string] The name of the release
        self["name"] = ""

        # repository: [string] The URL of the public project repository
        self["repositoryURL"] = ""

        # *description: [string] A description of the project
        self["description"] = ""

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
        self["permissions"] = {"licenses": None, "usageType": "", "exemptionText": None}

        # *laborHours: [number]: An estimate of total labor hours spent by your organization/component across all versions of this release. This includes labor performed by federal employees and contractors.
        self["laborHours"] = 0

        # *tags: [array] An array of keywords that will be helpful in discovering and searching for the release.
        self["tags"] = []

        # *contact: [object] Information about contacting the project.
        #   *email: [string] An email address to contact the project.
        #   name: [string] The name of a contact or department for the project
        #   twitter: [string] The username of the project's Twitter account
        #   phone: [string] The phone number to contact a project.
        self["contact"] = {"email": ""}
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
    def from_github3(klass, repository, labor_hours=True):
        """
        Create CodeGovProject object from github3 Repository object
        """
        if not isinstance(repository, github3.repos.repo._Repository):
            raise TypeError("Repository must be a github3 Repository object")

        logger.info("Processing: %s", repository.full_name)

        project = klass()

        logger.debug("GitHub3: repository=%s", repository)

        # -- REQUIRED FIELDS --

        project["name"] = repository.name
        project["repositoryURL"] = repository.clone_url
        project["description"] = repository.description

        try:
            repo_license = repository.license()
        except github3.exceptions.NotFoundError:
            logger.debug("no license found for repo=%s", repository)
            repo_license = None

        if repo_license:
            license_obj = repo_license.license
            if license_obj:
                logger.debug(
                    "license spdx=%s; url=%s", license_obj.spdx_id, license_obj.url
                )
                if license_obj.url is None:
                    project["permissions"]["licenses"] = [{"name": license_obj.spdx_id}]
                else:
                    project["permissions"]["licenses"] = [
                        {"URL": license_obj.url, "name": license_obj.spdx_id}
                    ]
            else:
                project["permissions"]["licenses"] = None

        public_server = repository.html_url.startswith("https://github.com")
        if not repository.private and public_server:
            project["permissions"]["usageType"] = "openSource"
        elif date_parse(repository.created_at) < POLICY_START_DATE:
            project["permissions"]["usageType"] = "exemptByPolicyDate"

        if labor_hours:
            project["laborHours"] = labor_hours_from_url(project["repositoryURL"])
        else:
            project["laborHours"] = 0

        project["tags"] = ["github"]
        old_accept = repository.session.headers["Accept"]
        repository.session.headers[
            "Accept"
        ] = "application/vnd.github.mercy-preview+json"
        topics = repository._get(repository.url + "/topics").json()
        project["tags"].extend(topics.get("names", []))
        repository.session.headers["Accept"] = old_accept

        # Hacky way to get an Organization object back with GitHub3.py >= 1.2.0
        owner_url = repository.owner.url
        owner_api_response = repository._get(owner_url)
        organization = repository._json(owner_api_response, 200)
        project["contact"]["email"] = organization["email"]
        project["contact"]["URL"] = organization["html_url"]

        # -- OPTIONAL FIELDS --

        # project['version'] = ''

        project["organization"] = organization["name"]

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project["status"] = "Development"

        project["vcs"] = "git"

        project["homepageURL"] = repository.html_url

        project["downloadURL"] = repository.downloads_url

        project["languages"] = [lang for lang, _ in repository.languages()]

        # project['partners'] = []

        # project['relatedCode'] = []

        # project['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        try:
            created_at = repository.created_at.date()
        except AttributeError:
            created_at = date_parse(repository.created_at).date()
        try:
            updated_at = repository.updated_at.date()
        except AttributeError:
            updated_at = date_parse(repository.updated_at).date()

        project["date"] = {
            "created": created_at.isoformat(),
            "lastModified": updated_at.isoformat(),
            "metadataLastUpdated": "",
        }

        _prune_dict_null_str(project)

        return project

    @classmethod
    def from_gitlab(klass, repository, labor_hours=True, fetch_languages=False):
        """
        Create CodeGovProject object from GitLab Repository
        """
        if not isinstance(repository, gitlab.v4.objects.Project):
            raise TypeError("Repository must be a gitlab Repository object")

        project = klass()

        logger.debug(
            "GitLab: repository_id=%d path_with_namespace=%s",
            repository.id,
            repository.path_with_namespace,
        )

        # -- REQUIRED FIELDS --

        project["name"] = repository.name
        project["repositoryURL"] = repository.http_url_to_repo
        project["description"] = repository.description

        # TODO: Update licenses from GitLab API
        project["permissions"]["licenses"] = None

        web_url = repository.web_url
        public_server = web_url.startswith("https://gitlab.com")

        if repository.visibility in ("public") and public_server:
            project["permissions"]["usageType"] = "openSource"
        elif date_parse(repository.created_at) < POLICY_START_DATE:
            project["permissions"]["usageType"] = "exemptByPolicyDate"

        if labor_hours:
            project["laborHours"] = labor_hours_from_url(project["repositoryURL"])
        else:
            project["laborHours"] = 0

        project["tags"] = ["gitlab"] + repository.tag_list

        project["contact"] = {"email": "", "URL": web_url}

        # -- OPTIONAL FIELDS --

        # project['version'] = ''

        project["organization"] = repository.namespace["name"]

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project["status"] = "Development"

        project["vcs"] = "git"

        project["homepageURL"] = repository.web_url

        api_url = repository.manager.gitlab._url
        archive_suffix = "/projects/%s/repository/archive" % repository.get_id()
        project["downloadURL"] = api_url + archive_suffix

        # project['languages'] = [lang for lang, _ in repository.languages()]

        if fetch_languages:
            project["languages"] = [*repository.languages()]

        # project['partners'] = []
        # project['relatedCode'] = []
        # project['reusedCode'] = []

        project["date"] = {
            "created": date_parse(repository.created_at).date().isoformat(),
            "lastModified": date_parse(repository.last_activity_at).date().isoformat(),
            "metadataLastUpdated": "",
        }

        _prune_dict_null_str(project)

        return project

    @classmethod
    def from_stashy(klass, repository, labor_hours=True):
        """
        Handles crafting Code.gov Project for Bitbucket Server repositories
        """
        # if not isinstance(repository, stashy.repos.Repository):
        #     raise TypeError('Repository must be a stashy Repository object')
        if not isinstance(repository, dict):
            raise TypeError("Repository must be a dict")

        project = klass()

        logger.debug(
            "Stashy: project_key=%s repository_slug=%s",
            repository["name"],
            repository["project"]["key"],
        )

        # -- REQUIRED FIELDS --

        project["name"] = repository["name"]

        clone_urls = [clone["href"] for clone in repository["links"]["clone"]]
        for url in clone_urls:
            # Only rely on SSH Urls for repository urls
            if url.startswith("ssh://"):
                project["repositoryURL"] = url
                break

        description = repository["project"].get("description", "")
        if description:
            project["description"] = "Project description: %s" % description

        project["permissions"]["licenses"] = None

        web_url = repository["links"]["self"][0]["href"]
        public_server = web_url.startswith("https://bitbucket.org")
        if repository["public"] and public_server:
            project["permissions"]["usageType"] = "openSource"

        if labor_hours:
            project["laborHours"] = labor_hours_from_url(project["repositoryURL"])
        else:
            project["laborHours"] = 0

        project["tags"] = ["bitbucket"]

        project["contact"]["email"] = ""
        project["contact"]["URL"] = repository["links"]["self"][0]["href"]

        # -- OPTIONAL FIELDS --

        # project['version'] = ''

        # project['organization'] = organization.name

        # TODO: Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        project["status"] = "Development"

        project["vcs"] = repository["scmId"]

        project["homepageURL"] = repository["links"]["self"][0]["href"]

        # project['downloadURL'] =

        # project['languages'] =

        # project['partners'] = []

        # project['relatedCode'] = []

        # project['reusedCode'] = []

        # date: [object] A date object describing the release. Empty if repo has no commits.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        if repository.get("created", None):
            project["date"] = {
                "created": repository["created"],
                "lastModified": repository["lastModified"],
            }

        _prune_dict_null_str(project)

        return project

    @classmethod
    def from_doecode(klass, record):
        """
        Create CodeGovProject object from DOE CODE record

        Handles crafting Code.gov Project
        """
        if not isinstance(record, dict):
            raise TypeError("`record` must be a dict")

        project = klass()

        # -- REQUIRED FIELDS --

        project["name"] = record["software_title"]
        logger.debug('DOE CODE: software_title="%s"', record["software_title"])

        link = record.get("repository_link", "")
        if not link:
            link = record.get("landing_page")
            logger.warning("DOE CODE: No repositoryURL, using landing_page: %s", link)

        project["repositoryURL"] = link

        project["description"] = record["description"]

        licenses = set(record["licenses"])
        licenses.discard(None)
        logger.debug("DOE CODE: licenses=%s", licenses)

        license_objects = []
        if "Other" in licenses:
            licenses.remove("Other")
            license_objects = [{"name": "Other", "URL": record["proprietary_url"]}]

        if licenses:
            license_objects.extend(
                [_license_obj(license_name) for license_name in licenses]
            )

        project["permissions"]["licenses"] = license_objects

        if record["open_source"]:
            usage_type = "openSource"
        else:
            usage_type = "exemptByLaw"
            project["permissions"][
                "exemptionText"
            ] = "This source code is restricted by patent and / or intellectual property law."

        project["permissions"]["usageType"] = usage_type

        labor_hours = record.get("labor_hours")
        if labor_hours is not None:
            project["laborHours"] = labor_hours
        else:
            project["laborHours"] = 0

        project["tags"] = ["DOE CODE"]
        lab_name = record.get("lab_display_name")
        if lab_name is not None:
            project["tags"].append(lab_name)

        project["contact"]["email"] = record["owner"]
        # project['contact']['URL'] = ''
        # project['contact']['name'] = ''
        # project['contact']['phone'] = ''

        # -- OPTIONAL FIELDS --

        if "version_number" in record and record["version_number"]:
            project["version"] = record["version_number"]

        if lab_name is not None:
            project["organization"] = lab_name

        # Currently, can't be an empty string, see: https://github.com/GSA/code-gov-web/issues/370
        status = record.get("ever_announced")
        if status is None:
            raise ValueError('DOE CODE: Unable to determine "ever_announced" value!')

        project["status"] = "Production" if status else "Development"

        vcs = None
        link = project["repositoryURL"]
        if "github.com" in link:
            vcs = "git"
        if vcs is None:
            logger.debug(
                'DOE CODE: Unable to determine vcs for: name="%s", repositoryURL=%s',
                project["name"],
                link,
            )
            vcs = ""
        if vcs:
            project["vcs"] = vcs

        url = record.get("landing_page", "")
        if url:
            project["homepageURL"] = url

        # record['downloadURL'] = ''

        # self['disclaimerText'] = ''

        # self['disclaimerURL'] = ''

        if "programming_languages" in record:
            project["languages"] = record["programming_languages"]

        # self['partners'] = []
        # TODO: Look into using record['contributing_organizations']

        # self['relatedCode'] = []

        # self['reusedCode'] = []

        # date: [object] A date object describing the release.
        #   created: [string] The date the release was originally created, in YYYY-MM-DD or ISO 8601 format.
        #   lastModified: [string] The date the release was modified, in YYYY-MM-DD or ISO 8601 format.
        #   metadataLastUpdated: [string] The date the metadata of the release was last updated, in YYYY-MM-DD or ISO 8601 format.
        if "date_record_added" in record and "date_record_updated" in record:
            project["date"] = {
                "created": record["date_record_added"],
                # 'lastModified': '',
                "metadataLastUpdated": record["date_record_updated"],
            }

        return project

    @classmethod
    def from_tfs(klass, tfs_project, labor_hours=True):
        """
        Creates CodeGovProject object from TFS/VSTS/AzureDevOps Instance
        """
        project = klass()
        project_web_url = ""

        # -- REQUIRED FIELDS --
        project["name"] = tfs_project.projectInfo.name

        if "web" in tfs_project.projectInfo._links.additional_properties:
            if "href" in tfs_project.projectInfo._links.additional_properties["web"]:
                # URL Encodes spaces that are in the Project Name for the Project Web URL
                project_web_url = requote_uri(
                    tfs_project.projectInfo._links.additional_properties["web"]["href"]
                )

        project["repositoryURL"] = project_web_url

        project["homepageURL"] = project_web_url

        project["description"] = tfs_project.projectInfo.description

        project["vcs"] = "TFS/AzureDevOps"

        project["permissions"]["license"] = None

        project["tags"] = []

        if labor_hours:
            logger.debug("Sorry labor hour calculation not currently supported.")
            # project['laborHours'] = labor_hours_from_url(project['repositoryURL'])
        else:
            project["laborHours"] = 0

        if tfs_project.projectCreateInfo.last_update_time < POLICY_START_DATE:
            project["permissions"]["usageType"] = "exemptByPolicyDate"
        else:
            project["permissions"]["usageType"] = "exemptByAgencyMission"
            project["permissions"][
                "exemptionText"
            ] = "This source code resides on a private server and has not been properly evaluated for releaseability."

        project["contact"] = {"email": "", "URL": project_web_url}

        project["date"] = {
            "lastModified": tfs_project.projectLastUpdateInfo.last_update_time.date().isoformat(),
            "created": tfs_project.projectCreateInfo.last_update_time.date().isoformat(),
            "metadataLastUpdated": "",
        }

        _prune_dict_null_str(project)

        return project
