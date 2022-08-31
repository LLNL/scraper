import logging
import os

import gitlab

logger = logging.getLogger(__name__)


def connect(url="https://gitlab.com", token=None):
    """
    Return a connected GitLab session

    ``token`` should be a ``private_token`` from Gitlab
    """

    if token is None:
        token = os.environ.get("GITLAB_API_TOKEN", None)

    gl_session = gitlab.Gitlab(url, token)

    try:
        gl_session.version()
    except gitlab.exceptions.GitlabAuthenticationError as exc:
        raise RuntimeError("Invalid or missing GITLAB_API_TOKEN") from exc

    logger.info("Connected to: %s", url)

    return gl_session


def query_repos(gl_session, repos=None):
    """
    Yields Gitlab project objects for all projects in Bitbucket
    """

    if repos is None:
        repos = []

    for repo in repos:
        yield gl_session.projects.get(repo)

    if not repos:
        for project in gl_session.projects.list(as_list=False):
            yield project
