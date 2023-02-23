#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os

from msrest.authentication import BasicAuthentication
from vsts.vss_connection import VssConnection

from scraper.tfs.models import TFSProject

logger = logging.getLogger(__name__)

HARD_CODED_TOP = 10000


def get_projects_metadata(baseurl, token):
    logger.debug("Retrieving TFS Metdata.....")
    return get_all_projects(baseurl, token)


def create_tfs_connection(url, token):
    """
    Creates the TFS Connection Context
    """
    if token is None:
        token = os.environ.get("TFS_API_TOKEN", None)

    tfs_credentials = BasicAuthentication("", token)
    tfs_connection = VssConnection(base_url=url, creds=tfs_credentials)
    return tfs_connection


def create_tfs_project_analysis_client(url, token=None):
    """
    Create a project_analysis_client.py client for a Team Foundation Server Enterprise connection instance.
    This is helpful for understanding project languages, but currently blank for all our test conditions.

    If token is not provided, will attempt to use the TFS_API_TOKEN
    environment variable if present.
    """
    if token is None:
        token = os.environ.get("TFS_API_TOKEN", None)

    tfs_connection = create_tfs_connection(url, token)
    project_analysis_client = tfs_connection.get_client(
        "vsts.project_analysis.v4_1.project_analysis_client.ProjectAnalysisClient"
    )

    if project_analysis_client is None:
        raise RuntimeError(
            "Unable to connect to TFS Enterprise (%s) with provided token." % url
        )

    return project_analysis_client


def create_tfs_core_client(url, token=None):
    """
    Create a core_client.py client for a Team Foundation Server Enterprise connection instance

    If token is not provided, will attempt to use the TFS_API_TOKEN
    environment variable if present.
    """
    if token is None:
        token = os.environ.get("TFS_API_TOKEN", None)

    tfs_connection = create_tfs_connection(url, token)
    tfs_client = tfs_connection.get_client("vsts.core.v4_1.core_client.CoreClient")

    if tfs_client is None:
        raise RuntimeError(
            "Unable to connect to TFS Enterprise (%s) with provided token." % url
        )

    return tfs_client


def create_tfs_git_client(url, token=None):
    """
    Creates a TFS Git Client to pull Git repo info
    """
    if token is None:
        token = os.environ.get("TFS_API_TOKEN", None)

    tfs_connection = create_tfs_connection(url, token)
    tfs_git_client = tfs_connection.get_client("vsts.git.v4_1.git_client.GitClient")

    if tfs_git_client is None:
        raise RuntimeError(
            "Unable to create TFS Git Client, failed to connect to TFS Enterprise (%s) with provided token."
            % url
        )

    return tfs_git_client


def create_tfs_tfvc_client(url, token=None):
    """
    Creates a TFS TFVC Client to pull TFVC repo info
    """
    if token is None:
        token = os.environ.get("TFS_API_TOKEN", None)

    tfs_connection = create_tfs_connection(url, token)
    tfs_tfvc_client = tfs_connection.get_client("vsts.tfvc.v4_1.tfvc_client.TfvcClient")

    if tfs_tfvc_client is None:
        raise RuntimeError(
            "Unable to create TFS Git Client, failed to connect to TFS Enterprise (%s) with provided token."
            % url
        )

    return tfs_tfvc_client


def get_all_projects(url, token, top=HARD_CODED_TOP):
    """
    Returns a list of all projects with their collection info from the server. Currently limited functionality to only return the first 1000 projects.
    #TODO refactor to add multiple calls to api to retrieve all projects if more exist beyond top.
    """
    project_list = []
    tfs_client = create_tfs_core_client(url, token)

    collections = tfs_client.get_project_collections(top=top)

    for collection in collections:
        collection_client = create_tfs_core_client(
            "{url}/{collection_name}".format(url=url, collection_name=collection.name),
            token,
        )

        logger.debug("Retrieving Projects for Project Collection: %s", collection.name)
        # Retrieves all projects in the project collection
        projects = collection_client.get_projects(top=HARD_CODED_TOP)
        # get_projects only gets the project references, have to call get_project_history_entries to get last update info for projects
        # Only calling this once per collection as its an expensive API call, wil refactor later if there is a better API call to use
        collection_history_list = collection_client.get_project_history_entries()
        for project in projects:
            # get_projects only gets team project ref objects,
            # have to call get_project to get the team project object which includes the TFS Web Url for the project
            logger.debug("Retrieving Team Project for Project: %s", project.name)
            projectInfo = collection_client.get_project(project.id, True, True)

            tfsProject = TFSProject(projectInfo, collection)

            logger.debug(
                "Retrieving Last Updated and Created Info for Project: %s", project.name
            )
            tfsProject.projectLastUpdateInfo = get_project_last_update_time(
                collection_history_list, project.id
            )
            tfsProject.projectCreateInfo = get_project_create_time(
                collection_history_list, project.id
            )
            project_list.append(tfsProject)

    return project_list


def get_git_repos(url, token, collection, project):
    """
    Returns a list of all git repos for the supplied project within the supplied collection
    """
    git_client = create_tfs_git_client(
        "{url}/{collection_name}".format(url=url, collection_name=collection.name),
        token,
    )
    logger.debug("Retrieving Git Repos for Project: %s", project.name)
    return git_client.get_repositories(project.id)


def get_tfvc_repos(url, token, collection, project):
    """
    Returns a list of all tfvc branches for the supplied project within the supplied collection
    """
    branch_list = []
    tfvc_client = create_tfs_tfvc_client(
        "{url}/{collection_name}".format(url=url, collection_name=collection.name),
        token,
    )

    logger.debug("Retrieving Tfvc Branches for Project: %s}", project.name)
    branches = tfvc_client.get_branches(project.id, True, True, False, True)
    if branches:
        branch_list.extend(branches)
    else:
        logger.debug("No Tfvc Branches in Project: %s", project.name)

    return branch_list


def get_project_last_update_time(collection_history_list, projectId):
    sorted_history_list = sorted(
        collection_history_list, key=lambda x: x.last_update_time, reverse=True
    )
    return next((x for x in sorted_history_list if x.id == projectId))


def get_project_create_time(collection_history_list, projectId):
    sorted_history_list = sorted(
        collection_history_list, key=lambda x: x.last_update_time, reverse=False
    )
    return next((x for x in sorted_history_list if x.id == projectId))
