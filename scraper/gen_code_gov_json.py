#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import json
import logging
import os

from scraper import code_gov
from scraper.util import configure_logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape code repositories for Code.gov / DOE CODE"
    )

    parser.add_argument(
        "--agency", type=str, nargs="?", default="", help='Agency Label, e.g. "DOE"'
    )
    parser.add_argument(
        "--method",
        type=str,
        nargs="?",
        default="",
        help="Method of measuring open source",
    )
    parser.add_argument(
        "--organization",
        type=str,
        nargs="?",
        default="",
        help="Force all repos to report a particular organization",
    )
    parser.add_argument(
        "--contact-email",
        type=str,
        nargs="?",
        default="",
        help="Force all repos to report a particular contact email",
    )

    parser.add_argument(
        "--config", type=str, nargs="?", default="", help="Configuration File (*.json)"
    )

    parser.add_argument(
        "--github-gov-orgs",
        action="store_true",
        help="Use orgs from government.github.com/community",
    )
    parser.add_argument(
        "--skip-labor-hours",
        action="store_true",
        help='Skip calculation of labor hours, assume "0"',
    )

    parser.add_argument(
        "--doecode-json",
        type=str,
        nargs="?",
        default=None,
        help="Path to DOE CODE .json file",
    )
    parser.add_argument(
        "--doecode-url",
        type=str,
        nargs="?",
        default=None,
        help="URL to DOE CODE .json data",
    )
    parser.add_argument(
        "--doecode-api-key",
        type=str,
        nargs="?",
        default=None,
        help="DOE CODE API key for accessing --doecode-url",
    )

    parser.add_argument(
        "--output-path",
        type=str,
        nargs="?",
        default="",
        help="Output path for .json file",
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        nargs="?",
        default="code.json",
        help="Output filename for .json file",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    configure_logging(args.verbose)

    try:
        with open(args.config, encoding="utf-8") as fd:
            config_json = json.load(fd)
    except (FileNotFoundError, json.JSONDecodeError):
        if args.config:
            raise
        config_json = {}

    # Update config based on commandline arguments
    if args.agency:
        config_json["agency"] = args.agency
    if args.method:
        config_json["method"] = args.method
    if args.organization:
        config_json["organization"] = args.organization
    if args.contact_email:
        config_json["contact_email"] = args.contact_email
    if args.output_path:
        config_json["output_path"] = args.output_path
    if args.skip_labor_hours:
        config_json["compute_labor_hours"] = False
    if args.github_gov_orgs:
        config_json["github_gov_orgs"] = True

    config_json["DOE CODE"] = {}
    config_json["DOE CODE"]["json"] = args.doecode_json
    config_json["DOE CODE"]["url"] = args.doecode_url
    config_json["DOE CODE"]["api_key"] = args.doecode_api_key

    output_path = config_json.get("output_path", None)
    output_path = args.output_path or output_path
    logger.debug("Output Path: %s", output_path)

    if output_path is not None and not os.path.exists(output_path):
        raise RuntimeError(
            "Invalid output path argument provided!  Make sure the output path exists and try again."
        )

    code_json = code_gov.process_config(config_json)

    code_gov.force_attributes(code_json, config_json)

    logger.info("Number of Projects: %s", len(code_json["releases"]))

    output_filepath = args.output_filename

    if output_path is not None:
        output_filepath = os.path.join(output_path, output_filepath)

    with open(output_filepath, "w", encoding="utf-8") as fp:
        logger.info("Writing output to: %s", output_filepath)
        fp.write(code_json.to_json())


if __name__ == "__main__":
    main()
