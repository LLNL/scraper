import stashy


def connect(url, username, password):
    """
    Return a connected Bitbucket session
    """

    return stashy.connect(url, username, password)


def all_repos(bb_session):
    """
    Yields Stashy repo objects for all projects in Bitbucket
    """

    for repo in bb_session.repos.all():
        yield repo
