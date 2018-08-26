import logging
import stashy

logger = logging.getLogger(__name__)


def connect(url, username, password):
    """
    Return a connected Bitbucket session
    """

    bb_session = stashy.connect(url, username, password)

    logger.info('Connected to: %s as %s', url, username)

    return bb_session


def all_repos(bb_session):
    """
    Yields Stashy repo objects for all projects in Bitbucket
    """

    for repo in bb_session.repos.all():
        yield repo
