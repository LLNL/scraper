#! /usr/bin/env python3

from scraper.github import create_session

# Looks for an environment variable `GITHUB_API_TOKEN` with a valid GitHub API token
gh = create_session()


def print_org_members_without_2fa(org_name="llnl"):
    org = gh.organization(org_name)

    for user in org.members(filter="2fa_disabled"):
        emails = {
            c['author']['email']
            for e in user.events()
            if e.type == "PushEvent"
            for c in e.payload['commits']
        }
        emails = {e for e in emails if "@llnl.gov" in e}
        if emails:
            print(f"{user.login}: {','.join(emails)}")


if __name__ == "__main__":
    print_org_members_without_2fa()
