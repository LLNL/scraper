#! /usr/bin/env python3

import argparse
import json

from scraper.util import compute_labor_hours, git_repo_to_sloc

parser = argparse.ArgumentParser(
    description="Scrape code repositories for Code.gov / DOECode"
)
parser.add_argument(
    "filename", type=str, help="Path to locally stored `code.json` file"
)
args = parser.parse_args()

code_gov_json = json.load(open(args.filename))
releases = code_gov_json["releases"]

repo_urls = {
    release["repositoryURL"].rstrip("/")
    for release in releases
    if release.get("vcs", "") == "git"
}

for url in repo_urls:
    # print(url)

    sloc = git_repo_to_sloc(url)
    # print(sloc)

    hours = compute_labor_hours(sloc)
    print("-- url=%s, sloc=%d, hours=%d" % (url, sloc, hours))
