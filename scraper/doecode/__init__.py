import json

import requests


def process_json(doecode_json_filename):
    """
    Converts a DOE CODE .json file into DOE CODE projects
    Yields DOE CODE records from a DOE CODE .json file
    """
    doecode_json = json.load(open(doecode_json_filename))

    for record in doecode_json['records']:
        yield record

    # projects = [CodeGovProject.from_doecode(p) for p in doecode_json['records']]
    #
    # return projects


def process_url(url, key):
    """
    Yields DOE CODE records from a DOE CODE .json URL response
    Converts a DOE CODE API .json URL response into DOE CODE projects
    """
    response = requests.get(url, headers={"Authorization": "Basic " + key})
    doecode_json = response.json()

    for record in doecode_json['records']:
        yield record

    # projects = [CodeGovProject.from_doecode(p) for p in doecode_json['records']]
    #
    # return projects
