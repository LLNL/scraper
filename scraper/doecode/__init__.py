import json
import logging

import requests

from scraper.util import DEFAULT_REQUESTS_TIMEOUTS

logger = logging.getLogger(__name__)


def process_json(filename):
    """
    Converts a DOE CODE .json file into DOE CODE projects
    Yields DOE CODE records from a DOE CODE .json file
    """

    logger.debug("Processing DOE CODE json: %s", filename)

    with open(filename, encoding="utf-8") as fd:
        doecode_json = json.load(fd)

    for record in doecode_json["records"]:
        yield record


def process_url(url, key):
    """
    Yields DOE CODE records from a DOE CODE .json URL response
    Converts a DOE CODE API .json URL response into DOE CODE projects
    """

    logger.debug("Fetching DOE CODE JSON: %s", url)

    if key is None:
        raise ValueError("DOE CODE API Key value is missing!")

    response = requests.get(
        url,
        headers={"Authorization": "Basic " + key},
        timeout=DEFAULT_REQUESTS_TIMEOUTS,
    )
    doecode_json = response.json()

    for record in doecode_json["records"]:
        yield record


def process(filename=None, url=None, key=None):
    """
    Yields DOE CODE records based on provided input sources

    param:
        filename (str): Path to a DOE CODE .json file
        url (str): URL for a DOE CODE server json file
        key (str): API Key for connecting to DOE CODE server
    """

    if filename is not None:
        yield from process_json(filename)
    elif url and key:
        yield from process_url(url, key)
