#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from scraper import bitbucket, doecode, github, gitlab, tfs
from scraper.code_gov.models import Metadata, Project
from scraper.github import gov_orgs

logger = logging.getLogger(__name__)


def process_config(config):
    """
    Master function to process a Scraper config file

    Returns a Code.gov Metadata file
    """

    agency = config.get("agency", "UNKNOWN")
    logger.debug("Agency: %s", agency)

    method = config.get("method", "other")
    logger.debug("Inventory Method: %s", method)

    compute_labor_hours = config.get("compute_labor_hours", True)

    if config.get("contact_email", None) is None:
        # A default contact email is required to handle the (frequent) case
        # where a project / repository has no available contact email.
        logger.warning('Config file should contain a "contact_email"')

    logger.debug("Creating inventory from config: %s", config)
    code_gov_metadata = Metadata(agency, method)

    # Parse config for GitHub repositories
    github_instances = config.get("GitHub", [])
    if config.get("github_gov_orgs", False):
        github_instances.append({"url": "https://github.com", "orgs": gov_orgs()})
    for instance in github_instances:
        timeouts = {}
        url = instance.get("url", "https://github.com")
        orgs = instance.get("orgs", [])
        repos = instance.get("repos", [])
        public_only = instance.get("public_only", True)
        excluded = instance.get("exclude", [])
        token = instance.get("token", None)
        connect_timeout = instance.get("connect_timeout", None)
        read_timeout = instance.get("read_timeout", None)

        if connect_timeout is not None:
            timeouts["default_connect_timeout"] = connect_timeout
        if read_timeout is not None:
            timeouts["default_read_timeout"] = read_timeout

        gh_session = github.connect(url, token, timeouts)

        for repo in github.query_repos(gh_session, orgs, repos, public_only):
            if repo.owner.login in excluded or repo.full_name in excluded:
                logger.info("Excluding: %s", repo.full_name)
                continue

            code_gov_project = Project.from_github3(
                repo, labor_hours=compute_labor_hours
            )
            code_gov_metadata["releases"].append(code_gov_project)

    # Parse config for GitLab repositories
    gitlab_instances = config.get("GitLab", [])
    for instance in gitlab_instances:
        url = instance.get("url")
        # orgs = instance.get('orgs', [])
        repos = instance.get("repos", [])
        # public_only = instance.get('public_only', True)
        excluded = instance.get("exclude", [])
        token = instance.get("token", None)
        fetch_languages = instance.get("fetch_languages", False)

        gl_session = gitlab.connect(url, token)

        for repo in gitlab.query_repos(gl_session, repos):
            namespace = repo.namespace["path"]
            path_with_namespace = repo.path_with_namespace
            if namespace in excluded or path_with_namespace in excluded:
                logger.info("Excluding: %s", repo.path_with_namespace)
                continue

            code_gov_project = Project.from_gitlab(
                repo, labor_hours=compute_labor_hours, fetch_languages=fetch_languages
            )
            code_gov_metadata["releases"].append(code_gov_project)

    # Parse config for Bitbucket repositories
    bitbucket_instances = config.get("Bitbucket", [])
    for instance in bitbucket_instances:
        url = instance.get("url")
        # orgs = instance.get('orgs', None)
        # public_only = instance.get('public_only', True)
        username = instance.get("username", None)
        password = instance.get("password", None)
        token = instance.get("token", None)
        excluded = instance.get("exclude", [])

        bb_session = bitbucket.connect(url, username, password, token)

        for repo in bitbucket.all_repos(bb_session):
            project = repo["project"]["key"]
            project_repo = "%s/%s" % (project, repo["slug"])
            if project in excluded or project_repo in excluded:
                logger.info("Excluding: %s", project_repo)
                continue

            code_gov_project = Project.from_stashy(
                repo, labor_hours=compute_labor_hours
            )
            code_gov_metadata["releases"].append(code_gov_project)

    # Parse config for TFS repositories
    tfs_instances = config.get("TFS", [])
    for instance in tfs_instances:
        url = instance.get("url")
        token = instance.get("token", None)

        projects = tfs.get_projects_metadata(url, token)
        for project in projects:
            code_gov_project = Project.from_tfs(
                project, labor_hours=compute_labor_hours
            )
            code_gov_metadata["releases"].append(code_gov_project)

    # Handle parsing of DOE CODE records

    doecode_config = config.get("DOE CODE", {})
    doecode_json = doecode_config.get("json", None)
    doecode_url = doecode_config.get("url", None)
    doecode_key = doecode_config.get("api_key", None)

    for record in doecode.process(doecode_json, doecode_url, doecode_key):
        code_gov_project = Project.from_doecode(record)
        code_gov_metadata["releases"].append(code_gov_project)

    return code_gov_metadata


def force_attributes(metadata, config):
    """
    Forces certain fields in the Code.gov Metadata json
    """

    organization = config.get("organization", "")
    logger.debug("Organization: %s", organization)

    contact_email = config.get("contact_email")
    logger.debug("Contact Email: %s", contact_email)

    permissions = config.get("permissions", {})
    default_usage = permissions.get("usageType", "")
    default_exemption_text = permissions.get("exemptionText", "")
    logger.debug("Default usageType: %s", default_usage)
    logger.debug("Default exemptionText: %s", default_exemption_text)

    # Force certain fields
    if organization:
        logger.debug("Forcing Organization to: %s", organization)

    if contact_email:
        logger.debug("Forcing Contact Email to: %s", contact_email)

    for release in metadata["releases"]:
        if organization:
            release["organization"] = organization

        if contact_email:
            release["contact"]["email"] = contact_email

        if "licenses" not in release["permissions"]:
            release["permissions"]["licenses"] = None

        if "description" not in release:
            release["description"] = "No description available..."

        if "usageType" not in release["permissions"]:
            release["permissions"]["usageType"] = default_usage
            release["permissions"]["exemptionText"] = default_exemption_text

    return metadata
