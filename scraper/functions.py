""" functions to use the code as a project package """
from scraper import code_gov
import logging
import json

logger = logging.getLogger(__name__)


def scrape(configfile):
    """
    run the scraper using the config.json file

    Parameters
    __________
    configfile : path
        file path to the configuration file with format as outlined in README.md

    Returns
    _______
    json
        a JSON file of the scraped metadata
    """

    # open the config file
    f = open(configfile)
    config_json = json.load(f)

    # process
    code_json = code_gov.process_config(config_json)
    code_gov.force_attributes(code_json, config_json)
    logger.info("Number of Projects: %s", len(code_json["releases"]))

    # return
    return code_json.to_json()
