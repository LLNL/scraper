#! /usr/bin/env python3

import pathlib
import subprocess
from timeit import default_timer as timer

import requests

INPUT_FILE = "https://raw.githubusercontent.com/LLNL/llnl.github.io/main/visualize/github-data/intReposInfo.json"


def main():
    repo_info = requests.get(INPUT_FILE).json()["data"]

    BACKUP_PATH = "github_backup"
    pathlib.Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)

    start = timer()

    for slug, data in repo_info.items():
        url = data["url"]
        clone_path = f"{BACKUP_PATH}/{slug}"
        if pathlib.Path(clone_path).exists():
            print(f"... updating: {url}")
            subprocess.run(["time", "git", "fetch"], cwd=clone_path)
        else:
            print(f"... cloning: {url}")
            subprocess.run(["time", "git", "clone", "--mirror", url, clone_path])
        if not pathlib.Path(clone_path).exists():
            print("Something went wrong with the clone, don't try to lfs fetch...")
            continue
        subprocess.run(["time", "git", "lfs", "fetch", "--all"], cwd=clone_path)

    end = timer()

    print(end - start)  # Time in seconds, e.g. 5.38091952400282


if __name__ == "__main__":
    main()
