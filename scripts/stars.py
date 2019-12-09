#!/usr/bin/env python

import logging
import os
import re

import requests

logging.basicConfig(level=logging.DEBUG)

github = requests.Session()

NEXT_LINK_REGEX = re.compile(r'<(\S+)>(?=; rel="next")')


def get_stargazers(url, session=None):
    """
    Return a list of the stargazers of a GitHub repo

    Includes both the 'starred_at' and 'user' data.

    param: url
        url is the 'stargazers_url' of the form:
            https://api.github.com/repos/LLNL/spack/stargazers
    """
    headers = {"Accept": "application/vnd.github.v3.star+json"}
    url = url + "?per_page=100&page=%s"
    page = 1
    gazers = []

    response = github.get(url % page, headers=headers)
    gazers.extend(response.json())

    # {rel: url for url, rel in LINK_REGEX.findall(r.headers['Link'])}
    while json_data:
        gazers.extend(json_data)
        page += 1
        json_data = github.get(url % page, headers=headers).json()

    return gazers


if __name__ == "__main__":
    if "GITHUB_API_TOKEN" in os.environ:
        auth = "token {}".format(os.environ["GITHUB_API_TOKEN"])
        github.headers["Authorization"] = auth
        logging.info("Using auth: %s", auth)

    orgs = ["llnl"]
    urls = ("https://api.github.com/orgs/%s/repos?per_page=100" % org for org in orgs)

    repos = []
    for url in urls:
        repos.extend(github.get(url).json())

    stargazers = {repo["name"]: [] for repo in repos}

    for repo in repos:
        stargazers[repo["name"]] = get_stargazers(repo["stargazers_url"])

        print(repo["name"], len(stargazers[repo["name"]]))
