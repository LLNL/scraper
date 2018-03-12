import logging
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
