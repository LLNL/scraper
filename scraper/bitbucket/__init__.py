import datetime
import logging

import stashy
from stashy.client import Stash

logger = logging.getLogger(__name__)


def connect(url, username=None, password=None, token=None):
    """
    Return a connected Bitbucket session
    """
    if token is not None:
        bb_session = Stash(url, token=token)
        logger.info("Connected to: %s with token", url)
    else:
        bb_session = stashy.connect(url, username, password)
        logger.info("Connected to: %s as username %s", url, username)

    return bb_session


def all_repos(bb_session):
    """
    Yields Stashy repo dictionary objects for all repos in Bitbucket
    """

    for repo in bb_session.repos.all():
        all_commits = sorted(
            bb_session.projects[repo["project"]["key"]]
            .repos[repo["name"]]
            .commits(None),
            key=lambda x: x["authorTimestamp"],
        )
        if all_commits:
            repo["created"] = (
                datetime.datetime.fromtimestamp(
                    all_commits[0]["authorTimestamp"] / 1000
                )
                .date()
                .isoformat()
            )
            repo["lastModified"] = (
                datetime.datetime.fromtimestamp(
                    all_commits[-1]["authorTimestamp"] / 1000
                )
                .date()
                .isoformat()
            )
        yield repo
