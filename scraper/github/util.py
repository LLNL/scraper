import logging

logger = logging.getLogger(__name__)


def _license_obj(license_name):
    """
    A helper function to look up license object information

    Use names from: https://api.github.com/licenses
    """
    obj = None

    if license_name in ("MIT", "MIT License"):
        obj = {"URL": "https://api.github.com/licenses/mit", "name": "MIT"}
    elif license_name in ('BSD 2-clause "Simplified" License'):
        obj = {
            "URL": "https://api.github.com/licenses/bsd-2-clause",
            "name": "BSD-2-Clause",
        }
    elif license_name in ('BSD 3-clause "New" or "Revised" License'):
        obj = {
            "URL": "https://api.github.com/licenses/bsd-3-clause",
            "name": "BSD-3-Clause",
        }
    elif license_name in ("Apache License 2.0"):
        obj = {
            "URL": "https://api.github.com/licenses/apache-2.0",
            "name": "Apache-2.0",
        }
    elif license_name in ("GNU General Public License v2.1"):
        obj = {"URL": "https://api.github.com/licenses/gpl-2.1", "name": "GPL-2.1"}
    elif license_name in ("GNU General Public License v2.0"):
        obj = {"URL": "https://api.github.com/licenses/gpl-2.0", "name": "GPL-2.0"}
    elif license_name in ("GNU Lesser General Public License v2.1"):
        obj = {"URL": "https://api.github.com/licenses/lgpl-2.1", "name": "LGPL-2.1"}
    elif license_name in ("GNU General Public License v3.0"):
        obj = {"URL": "https://api.github.com/licenses/gpl-3.0", "name": "GPL-3.0"}
    elif license_name in ("GNU Lesser General Public License v3.0"):
        obj = {"URL": "https://api.github.com/licenses/lgpl-3.0", "name": "LGPL-3.0"}
    elif license_name in ("Eclipse Public License 1.0"):
        obj = {"URL": "https://api.github.com/licenses/epl-1.0", "name": "EPL-1.0"}
    elif license_name in ("Mozilla Public License 2.0"):
        obj = {"URL": "https://api.github.com/licenses/mpl-2.0", "name": "MPL-2.0"}
    elif license_name in ("The Unlicense"):
        obj = {"URL": "https://api.github.com/licenses/unlicense", "name": "Unlicense"}
    elif license_name in ("GNU Affero General Public License v3.0"):
        obj = {"URL": "https://api.github.com/licenses/agpl-3.0", "name": "AGPL-3.0"}
    elif license_name in ("Eclipse Public License 2.0"):
        obj = {"URL": "https://api.github.com/licenses/epl-2.0", "name": "EPL-2.0"}

    if obj is None:
        logger.warning("I don't understand the license: %s", license_name)
        raise ValueError("Aborting!")

    return obj
