import logging
import logging.config
import os

from subprocess import Popen, PIPE, STDOUT  # nosec

logger = logging.getLogger(__name__)


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
                'format': '%(levelname)s: %(message)s'
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
