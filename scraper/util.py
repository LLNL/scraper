import functools
import json
import logging
import logging.config
import os
from subprocess import PIPE, Popen  # nosec
import tempfile

logger = logging.getLogger(__name__)

# These mirror the defaults in github3.py sessions per:
# https://github.com/sigmavirus24/github3.py/blob/ce43e6e5fdef6555f5a6b6602e2cc4b66c428aef/src/github3/session.py#L98
DEFAULT_REQUESTS_TIMEOUTS = (4, 10)


def execute(command, cwd=None):
    logger.debug("Forking command: %s", command)

    if cwd is None:
        cwd = os.getcwd()
    elif not os.path.isdir(cwd):
        raise ValueError("path does not exist: %s" % cwd)

    with Popen(
        command, cwd=cwd, stdout=PIPE, stderr=PIPE, shell=False
    ) as process:  # nosec
        out, err = process.communicate()

    if process.returncode:
        logging.error(
            "Error Executing: command=%s, returncode=%d",
            " ".join(command),
            process.returncode,
        )

    return out.decode("utf-8"), err.decode("utf-8")


def configure_logging(verbose=False):
    DEFAULT_LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                # 'format': '%(levelname)s: %(message)s'
                "format": "%(asctime)s - %(levelname)s: %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
            },
            "null": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
            "github3": {"handlers": ["null"], "level": "DEBUG", "propagate": False},
            "urllib3": {"handlers": ["null"], "level": "DEBUG", "propagate": False},
        },
    }

    if verbose:
        DEFAULT_LOGGING["handlers"]["default"]["level"] = "DEBUG"
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
        logger.debug("Cloning: url=%s tmp_dir=%s", url, tmp_dir)

        tmp_clone = os.path.join(tmp_dir, "clone-dir")

        cmd = ["git", "clone", "--depth=1", url, tmp_clone]
        execute(cmd)

        cmd = ["cloc", "--json", tmp_clone]
        out, err = execute(cmd)

        if err:
            logger.warning(
                "Error encountered while analyzing: url=%s stderr=%s", url, err
            )

        try:
            cloc_json = json.loads(out)
            sloc = cloc_json["SUM"]["code"]
        except json.decoder.JSONDecodeError:
            logger.error("Error Decoding: url=%s, out=%s", url, out)
            sloc = 0

    logger.debug("SLOC: url=%s, sloc=%d", url, sloc)

    return sloc


def compute_labor_hours(sloc, month_hours="cocomo_book"):
    """
    Compute the labor hours, given a count of source lines of code

    The intention is to use the COCOMO II model to compute this value.

    References:
    - http://csse.usc.edu/tools
    - http://softwarecost.org/tools/COCOMO/
    - https://www.rose-hulman.edu/class/csse/csse372/201310/Homework/CII_modelman2000.pdf
    """
    # Calculation of hours in a month
    if month_hours == "hours_per_year":
        # Use number of working hours in a year:
        # (40 Hours / week) * (52 weeks / year) / (12 months / year) ~= 173.33
        HOURS_PER_PERSON_MONTH = 40.0 * 52 / 12
    else:
        # Use value from COCOMO II Book (month_hours=='cocomo_book'):
        # Reference: https://dl.acm.org/citation.cfm?id=557000
        # This is the value used by the Code.gov team:
        # https://github.com/GSA/code-gov/blob/master/docs/labor_hour_calc.md
        HOURS_PER_PERSON_MONTH = 152.0

    # Coefficients for the COCOMO II model (only the two used for person-month
    # calculation)
    co_a = 2.94
    co_b = 0.91

    # These values represent a default of "Nominal" from the established
    # constant values for the COCOMO II model.
    scale_factors = [
        3.72,  # Precedentedness
        3.04,  # Development Flexibility
        4.24,  # Architecture / Risk Resolution
        3.29,  # Team Cohesion
        4.68,  # Process Maturity
    ]
    cost_drivers = [
        1.00,  # Required Software Reliability
        1.00,  # Data Base Size
        1.00,  # Product Complexity
        1.00,  # Developed for Reusability
        1.00,  # Documentation Match to Lifecycle Needs
        1.00,  # Analyst Capability
        1.00,  # Programmer Capability
        1.00,  # Personnel Continuity
        1.00,  # Application Experience
        1.00,  # Platform Experience
        1.00,  # Language and Toolset Experience
        1.00,  # Time Constraint
        1.00,  # Storage Constraint
        1.00,  # Platform Volatility
        1.00,  # Use of Software Tools
        1.00,  # Multisite Development
        1.00,  # Required Development Schedule
    ]

    # The summation (∑) of the scale factors is used in this calculation
    scale_factor_aggregate = co_b + 0.01 * functools.reduce(
        lambda x, y: x + y, scale_factors
    )
    # The product (∏) of the cost drivers
    effort_adjustment_factor = functools.reduce(lambda x, y: x * y, cost_drivers)
    # The calculation of person-months uses KSLOC for the size of a project
    size = sloc / 1000

    # Calculate PM = A * Size^E * EAF
    person_months = co_a * size**scale_factor_aggregate * effort_adjustment_factor

    labor_hours = round(person_months * HOURS_PER_PERSON_MONTH, 1)
    logger.debug("sloc=%d labor_hours=%d", sloc, labor_hours)

    return labor_hours


def labor_hours_from_url(url):
    sum_sloc = git_repo_to_sloc(url)
    logger.info("SLOC: %d", sum_sloc)

    labor_hours = compute_labor_hours(sum_sloc)
    logger.info("labor_hours: %d", labor_hours)

    return labor_hours


def _prune_dict_null_str(dictionary):
    """
    Prune the "None" or emptry string values from dictionary items
    """
    for key, value in list(dictionary.items()):
        if value is None or str(value) == "":
            del dictionary[key]

        if isinstance(value, dict):
            dictionary[key] = _prune_dict_null_str(dictionary[key])

    return dictionary
