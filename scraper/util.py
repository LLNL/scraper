import json
import logging
import logging.config
import os
import re
import requests
import tempfile

from subprocess import Popen, PIPE, STDOUT  # nosec

logger = logging.getLogger(__name__)

EFFORT_REGEX = re.compile(r'Effort = ([\d\.]+) Person-months')


def execute(command, cwd=None):
    logger.debug('Forking command: %s', command)

    if cwd is None:
        cwd = os.getcwd()
    elif not os.path.isdir(cwd):
        raise ValueError('path does not exist: %s', cwd)

    process = Popen(
        command,
        cwd=cwd,
        stdout=PIPE,
        stderr=STDOUT,
        shell=False)  # nosec
    out, err = process.communicate()
    return str(out), str(err)


def configure_logging(verbose=False):
    DEFAULT_LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                # 'format': '%(levelname)s: %(message)s'
                'format': '%(asctime)s - %(levelname)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'null': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.NullHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'github3': {
                'handlers': ['null'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'urllib3': {
                'handlers': ['null'],
                'level': 'DEBUG',
                'propagate': False,
            },
        }
    }

    if verbose:
        DEFAULT_LOGGING['handlers']['default']['level'] = 'DEBUG'
        # DEFAULT_LOGGING['loggers']['']['level'] = 'DEBUG'

    logging.config.dictConfig(DEFAULT_LOGGING)


def git_repo_to_sloc(url):
    """
    Given a Git repository URL, returns number of lines of code based on cloc

    Reference:
    - cloc: https://github.com/AlDanial/cloc
    - https://www.omg.org/spec/AFP/
        - Another potential way to calculation effort

    Sample cloc output:
        {
            "header": {
                "cloc_url": "github.com/AlDanial/cloc",
                "cloc_version": "1.74",
                "elapsed_seconds": 0.195950984954834,
                "n_files": 27,
                "n_lines": 2435,
                "files_per_second": 137.78956000769,
                "lines_per_second": 12426.5769858787
            },
            "C++": {
                "nFiles": 7,
                "blank": 121,
                "comment": 314,
                "code": 371
            },
            "C/C++ Header": {
                "nFiles": 8,
                "blank": 107,
                "comment": 604,
                "code": 191
            },
            "CMake": {
                "nFiles": 11,
                "blank": 49,
                "comment": 465,
                "code": 165
            },
            "Markdown": {
                "nFiles": 1,
                "blank": 18,
                "comment": 0,
                "code": 30
            },
            "SUM": {
                "blank": 295,
                "comment": 1383,
                "code": 757,
                "nFiles": 27
            }
        }
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.debug('Cloning: url=%s tmp_dir=%s', url, tmp_dir)

        tmp_clone = os.path.join(tmp_dir, 'clone-dir')

        cmd = ['git', 'clone', '--depth=1', url, tmp_clone]
        execute(cmd)

        cmd = ['cloc', '--json', tmp_clone]
        out, _ = execute(cmd)

        try:
            json_start = out.find('{"header"')
            json_blob = out[json_start:].replace('\\n', '').replace('\'', '')
            cloc_json = json.loads(json_blob)
            sloc = cloc_json['SUM']['code']
        except json.decoder.JSONDecodeError:
            logger.debug('Error Decoding: url=%s, out=%s', url, out)
            sloc = 0

    logger.debug('SLOC: url=%s, sloc=%d', url, sloc)

    return sloc


def compute_labor_hours(sloc, month_hours='cocomo_book'):
    """
    Compute the labor hours, given a count of source lines of code

    The intention is to use the COCOMO II model to compute this value.

    References:
    - https://csse.usc.edu/tools/cocomoii.php
    - http://docs.python-guide.org/en/latest/scenarios/scrape/
    """
    # Calculation of hours in a month
    if month_hours == 'hours_per_year':
        # Use number of working hours in a year:
        # (40 Hours / week) * (52 weeks / year) / (12 months / year) ~= 173.33
        HOURS_PER_PERSON_MONTH = 40.0 * 52 / 12
    else:
        # Use value from COCOMO II Book (month_hours=='cocomo_book'):
        # Reference: https://dl.acm.org/citation.cfm?id=557000
        # This is the value used by the Code.gov team:
        # https://github.com/GSA/code-gov/blob/master/LABOR_HOUR_CALC.md
        HOURS_PER_PERSON_MONTH = 152.0

    cocomo_url = 'https://csse.usc.edu/tools/cocomoii.php'
    page = requests.post(cocomo_url, data={'new_size': sloc})

    try:
        person_months = float(EFFORT_REGEX.search(page.text).group(1))
    except AttributeError:
        logger.error('Unable to find Person Months in page text: sloc=%s', sloc)
        # If there is no match, and .search(..) returns None
        person_months = 0

    labor_hours = person_months * HOURS_PER_PERSON_MONTH
    logger.debug('sloc=%d labor_hours=%d', sloc, labor_hours)

    return labor_hours


def labor_hours_from_url(url):
    sum_sloc = git_repo_to_sloc(url)
    logger.info('SLOC: %d', sum_sloc)

    labor_hours = compute_labor_hours(sum_sloc)
    logger.info('labor_hours: %d', labor_hours)

    return labor_hours


def _prune_dict_null_str(dictionary):
    """
    Prune the "None" or emptry string values from dictionary items
    """
    for key, value in list(dictionary.items()):
        if value is None or str(value) == '':
            del dictionary[key]

        if isinstance(value, dict):
            dictionary[key] = _prune_dict_null_str(dictionary[key])

    return dictionary
