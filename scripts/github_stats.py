import github3
import datetime
import os
import errno
import getpass
import time
import csv
import math
import my_repo
import json
from collections import defaultdict


class GitHub_LLNL_Stats:
    def __init__(self):
        print("Initalizing.")
        self.unique_contributors = defaultdict(list)
        self.languages = {}
        self.languages_size = {}
        self.all_repos = []
        self.total_repos = 0
        self.total_contributors = 0
        self.total_forks = 0
        self.total_stars = 0
        self.total_pull_reqs = 0
        self.total_pull_reqs_open = 0
        self.total_pull_reqs_closed = 0
        self.total_open_issues = 0
        self.total_closed_issues = 0
        self.total_issues = 0
        self.total_readmes = 0
        self.total_licenses = 0
        self.total_commits = 0
        self.search_limit = 0
        self.previous_language = ""

        # JSON vars
        self.repos_json = {}
        self.members_json = {}
        self.teams_json = {}
        self.contributors_json = defaultdict(list)
        self.pull_requests_json = defaultdict(list)
        self.issues_json = defaultdict(list)
        self.languages_json = defaultdict(dict)
        self.commits_json = defaultdict(list)

    def get_stats(
        self,
        username="",
        password="",
        organization="llnl",
        force=True,
        repo_type="public",
    ):
        """
        Retrieves the statistics from the given organization with the given
        credentials. Will not retreive data if file exists and force hasn't been
        set to True. This is to save GH API requests.
        """
        date = str(datetime.date.today())
        file_path = (
            "../github_stats_output/" + date[:4] + "/" + date[:7] + "/" + date + ".csv"
        )
        if force or not os.path.isfile(file_path):
            my_github.login(username, password)
            calls_beginning = self.logged_in_gh.ratelimit_remaining + 1
            print("Rate Limit: " + str(calls_beginning))
            my_github.get_org(organization)
            count_members = my_github.get_mems_of_org()
            count_teams = my_github.get_teams_of_org()
            my_github.repos(repo_type=repo_type, organization=organization)
            # Write JSON
            my_github.write_org_json(
                dict_to_write=self.members_json,
                path_ending_type="members",
                is_list=True,
            )
            my_github.write_org_json(
                dict_to_write={"singleton": self.org_retrieved.to_json()},
                path_ending_type="organization",
            )
            my_github.write_org_json(
                dict_to_write=self.teams_json, path_ending_type="teams", is_list=True
            )

            my_github.write_repo_json(
                dict_to_write=self.repos_json, path_ending_type="repo"
            )
            my_github.write_repo_json(
                dict_to_write=self.contributors_json,
                path_ending_type="contributors",
                is_list=True,
            )
            my_github.write_repo_json(
                dict_to_write=self.pull_requests_json,
                path_ending_type="pull-requests",
                is_list=True,
            )
            my_github.write_repo_json(
                dict_to_write=self.issues_json, path_ending_type="issues", is_list=True
            )
            my_github.write_repo_json(
                dict_to_write=self.languages_json,
                path_ending_type="languages",
                is_dict=True,
            )
            my_github.write_repo_json(
                dict_to_write=self.commits_json,
                path_ending_type="commits",
                is_list=True,
            )
            # Write CSV
            my_github.write_to_file(
                file_path, date, organization, count_members, count_teams
            )
            calls_remaining = self.logged_in_gh.ratelimit_remaining
            calls_used = calls_beginning - calls_remaining
            print(
                "Rate Limit Remaining: "
                + str(calls_remaining)
                + "\nUsed "
                + str(calls_used)
                + " API calls."
            )

    def login(self, username="", password=""):
        """
        Performs a login and sets the Github object via given credentials. If
        credentials are empty or incorrect then prompts user for credentials.
        Stores the authentication token in a CREDENTIALS_FILE used for future
        logins. Handles Two Factor Authentication.
        """
        try:

            self.token = ""
            id = ""
            if not os.path.isfile("CREDENTIALS_FILE"):
                if username == "" or password == "":
                    username = raw_input("Username: ")
                    password = getpass.getpass("Password: ")
                note = "GitHub Organization Stats App"
                note_url = "http://software.llnl.gov/"
                scopes = ["user", "repo"]
                auth = github3.authorize(
                    username,
                    password,
                    scopes,
                    note,
                    note_url,
                    two_factor_callback=self.prompt_2fa,
                )
                self.token = auth.token
                id = auth.id
                with open("CREDENTIALS_FILE", "w+") as fd:
                    fd.write(self.token + "\n")
                    fd.write(str(id))
                fd.close()
            else:
                with open("CREDENTIALS_FILE", "r") as fd:
                    self.token = fd.readline().strip()
                    id = fd.readline().strip()
                fd.close()
            print("Logging in.")
            self.logged_in_gh = github3.login(
                token=self.token, two_factor_callback=self.prompt_2fa
            )
            self.logged_in_gh.user().to_json()
        except (ValueError, AttributeError, github3.models.GitHubError):
            print("Bad credentials. Try again.")
            self.login()

    def prompt_2fa(self):
        """
        Taken from
        http://github3py.readthedocs.io/en/master/examples/two_factor_auth.html
        Prompts a user for their 2FA code and returns it.
        """
        code = ""
        while not code:
            code = raw_input("Enter 2FA code: ")
        return code

    def get_org(self, organization_name=""):
        """
        Retrieves an organization via given org name. If given
        empty string, prompts user for an org name.
        """
        if organization_name == "":
            organization_name = raw_input("Organization: ")
        print("Getting organization.")
        self.org_retrieved = self.logged_in_gh.organization(organization_name)

    def get_mems_of_org(self):
        """
        Retrieves the number of members of the organization.
        """
        print("Getting members.")
        counter = 0
        for member in self.org_retrieved.iter_members():
            self.members_json[member.id] = member.to_json()
            counter += 1
        return counter

    def get_teams_of_org(self):
        """
        Retrieves the number of teams of the organization.
        """
        print("Getting teams.")
        counter = 0
        for team in self.org_retrieved.iter_teams():
            self.teams_json[team.id] = team.to_json()
            counter += 1
        return counter

    def repos(self, repo_type="public", organization="llnl"):
        """
        Retrieves info about the repos of the current organization.
        """
        print("Getting repos.")
        for repo in self.org_retrieved.iter_repos(type=repo_type):
            # JSON
            json = repo.to_json()
            self.repos_json[repo.name] = json
            # CSV
            temp_repo = my_repo.My_Repo()
            temp_repo.name = repo.full_name
            self.total_repos += 1
            temp_repo.contributors = my_github.get_total_contributors(repo)
            self.total_contributors += temp_repo.contributors
            temp_repo.forks = repo.forks_count
            self.total_forks += temp_repo.forks
            temp_repo.stargazers = repo.stargazers
            self.total_stars += temp_repo.stargazers
            (
                temp_repo.pull_requests_open,
                temp_repo.pull_requests_closed,
            ) = my_github.get_pull_reqs(repo)
            temp_repo.pull_requests = (
                temp_repo.pull_requests_open + temp_repo.pull_requests_closed
            )
            self.total_pull_reqs += temp_repo.pull_requests_open
            self.total_pull_reqs += temp_repo.pull_requests_closed
            self.total_pull_reqs_open += temp_repo.pull_requests_open
            self.total_pull_reqs_closed += temp_repo.pull_requests_closed
            temp_repo.open_issues = repo.open_issues_count
            self.total_open_issues += temp_repo.open_issues
            temp_repo.closed_issues = my_github.get_issues(
                repo, organization=organization
            )
            temp_repo.issues = temp_repo.closed_issues + temp_repo.open_issues
            self.total_closed_issues += temp_repo.closed_issues
            self.total_issues += temp_repo.issues
            my_github.get_languages(repo, temp_repo)
            temp_repo.readme = my_github.get_readme(repo)
            # temp_repo.license = my_github.get_license(repo)
            temp_repo.commits = self.get_commits(repo=repo, organization=organization)
            self.total_commits += temp_repo.commits
            self.all_repos.append(temp_repo)

    def get_total_contributors(self, repo):
        """
        Retrieves the number of contributors to a repo in the organization.
        Also adds to unique contributor list.
        """
        repo_contributors = 0
        for contributor in repo.iter_contributors():
            repo_contributors += 1
            self.unique_contributors[contributor.id].append(repo.name)
            self.contributors_json[repo.name].append(contributor.to_json())
        return repo_contributors

    def get_pull_reqs(self, repo):
        """
        Retrieves the number of pull requests on a repo in the organization.
        """
        pull_reqs_open = 0
        pull_reqs_closed = 0
        for pull_request in repo.iter_pulls(state="all"):
            self.pull_requests_json[repo.name].append(pull_request.to_json())
            if pull_request.closed_at is not None:
                pull_reqs_closed += 1
            else:
                pull_reqs_open += 1
        return pull_reqs_open, pull_reqs_closed

    def get_issues(self, repo, organization="llnl"):
        """
        Retrieves the number of closed issues.
        """
        # JSON
        path = "../github-data/" + organization + "/" + repo.name + "/issues"
        is_only_today = False
        if not os.path.exists(path):  # no previous path, get all issues
            all_issues = repo.iter_issues(state="all")
            is_only_today = True
        else:
            files = os.listdir(path)
            date = str(files[-1][:-5])
            if date == str(datetime.date.today()):
                # most recent date is actually today, get previous most recent date
                if len(files) > 2:
                    date = str(files[-2][:-5])
                else:
                    # This means there is only one file, today. Retrieve every issue
                    all_issues = repo.iter_issues(state="all")
                    is_only_today = True
            if not is_only_today:  # there's a previous saved JSON that's not today
                all_issues = repo.iter_issues(since=date, state="all")
        for issue in all_issues:
            self.issues_json[repo.name].append(issue.to_json())
        # CSV
        closed_issues = 0
        for issue in repo.iter_issues(state="closed"):
            if issue is not None:
                closed_issues += 1
        return closed_issues

    def get_languages(self, repo, temp_repo):
        """
        Retrieves the languages used in the repo and increments the respective
        counts of those languages. Only increments languages that have names.
        Anything else is not incremented (i.e. numbers).
        """
        try:
            self.languages[repo.language] += 1
        except KeyError:
            count = self.languages[repo.language] = 1
        for repo_languages in repo.iter_languages():
            self.languages_json[repo.name][repo_languages[0]] = repo_languages[1]
            for language in repo_languages:
                if isinstance(language, basestring):  # is language
                    temp_repo.languages.append(language)
                    self.previous_language = language
                else:  # record size bytes of language
                    try:
                        self.languages_size[self.previous_language] += language
                    except KeyError:
                        size = self.languages_size[self.previous_language] = language

    def get_readme(self, repo):
        """
        Checks to see if the given repo has a ReadMe. MD means it has a correct
        Readme recognized by GitHub.
        """
        readme_contents = repo.readme()
        if readme_contents is not None:
            self.total_readmes += 1
            return "MD"
        if self.search_limit >= 28:
            print("Hit search limit. Sleeping for 60 sec.")
            time.sleep(60)
            self.search_limit = 0
        self.search_limit += 1
        search_results = self.logged_in_gh.search_code(
            "readme" + "in:path repo:" + repo.full_name
        )
        try:
            for result in search_results:
                path = result.path[1:]
                if "/" not in path and "readme" in path.lower():
                    self.total_readmes += 1
                    return path
            return "MISS"
        except (github3.models.GitHubError, StopIteration):
            return "MISS"

    def get_license(self, repo):
        """
        Checks to see if the given repo has a top level LICENSE file.
        """
        if self.search_limit >= 28:
            print("Hit search limit. Sleeping for 60 sec.")
            time.sleep(60)
            self.search_limit = 0
        self.search_limit += 1
        search_results = self.logged_in_gh.search_code(
            "license" + "in:path repo:" + repo.full_name
        )
        try:
            for result in search_results:
                path = result.path[1:]
                if "/" not in path and "license" in path.lower():
                    self.total_licenses += 1
                    return path
            return "MISS"
        except (StopIteration):
            return "MISS"

    def get_commits(self, repo, organization="llnl"):
        """
        Retrieves the number of commits to a repo in the organization. If it is
        the first time getting commits for a repo, it will get all commits and
        save them to JSON. If there are previous commits saved, it will only get
        commits that have not been saved to disk since the last date of commits.
        """
        # JSON
        path = "../github-data/" + organization + "/" + repo.name + "/commits"
        is_only_today = False
        if not os.path.exists(path):  # no previous path, get all commits
            all_commits = repo.iter_commits()
            is_only_today = True
        else:
            files = os.listdir(path)
            date = str(files[-1][:-5])
            if date == str(datetime.date.today()):
                # most recent date is actually today, get previous most recent date
                if len(files) > 2:
                    date = str(files[-2][:-5])
                else:
                    # This means there is only one file, today. Retrieve every commit
                    all_commits = repo.iter_commits()
                    is_only_today = True
            if not is_only_today:  # there's a previous saved JSON that's not today
                all_commits = repo.iter_commits(since=date)
        for commit in all_commits:
            self.commits_json[repo.name].append(commit.to_json())
        # for csv
        count = 0
        for commit in repo.iter_commits():
            count += 1
        return count

    def write_org_json(
        self,
        date=(datetime.date.today()),
        organization="llnl",
        dict_to_write={},
        path_ending_type="",
        is_list=False,
    ):
        """
        Writes stats from the organization to JSON.
        """
        path = (
            "../github-data/"
            + organization
            + "-org/"
            + path_ending_type
            + "/"
            + str(date)
            + ".json"
        )
        self.checkDir(path)
        with open(path, "w") as out_clear:  # clear old data
            out_clear.close()
        with open(path, "a") as out:
            if is_list:  # used for list of items
                out.write("[")
            for item in dict_to_write:
                out.write(
                    json.dumps(
                        dict_to_write[item],
                        sort_keys=True,
                        indent=4,
                        separators=(",", ": "),
                    )
                    + ","
                )
            out.seek(-1, os.SEEK_END)  # kill last comma
            out.truncate()
            if is_list:
                out.write("]")
        out.close()

    def write_repo_json(
        self,
        date=(datetime.date.today()),
        organization="llnl",
        dict_to_write={},
        path_ending_type="",
        is_list=False,
        is_dict=False,
    ):
        """
        #Writes repo specific data to JSON.
        """
        for repo in dict_to_write:
            path = (
                "../github-data/"
                + organization
                + "/"
                + repo
                + "/"
                + path_ending_type
                + "/"
                + str(date)
                + ".json"
            )
            self.checkDir(path)
            with open(path, "w") as out:
                if is_list:
                    out.write("[")
                    for value in dict_to_write[repo]:
                        if is_dict:
                            for inner_dict in value:
                                out.write(
                                    json.dumps(
                                        inner_dict,
                                        sort_keys=True,
                                        indent=4,
                                        separators=(",", ": "),
                                    )
                                    + ","
                                )
                        else:
                            out.write(
                                json.dumps(
                                    value,
                                    sort_keys=True,
                                    indent=4,
                                    separators=(",", ": "),
                                )
                                + ","
                            )
                    out.seek(-1, os.SEEK_END)  # kill last comma
                    out.truncate()
                    out.write("]")
                else:
                    out.write(
                        json.dumps(
                            dict_to_write[repo],
                            sort_keys=True,
                            indent=4,
                            separators=(",", ": "),
                        )
                    )
            out.close()

    def write_to_file(
        self,
        file_path="",
        date=str(datetime.date.today()),
        organization="N/A",
        members=0,
        teams=0,
    ):
        """
        Writes the current organization information to file (csv).
        """
        self.checkDir(file_path)
        with open(file_path, "w+") as output:
            output.write(
                "date,organization,members,teams,unique_contributors,"
                + "repository,contributors,forks,stargazers,pull_requests,"
                + "open_issues,has_readme,has_license,languages,pull_requests_open,"
                + "pull_requests_closed,commits,closed_issues,issues\n"
                + date
                + ","
                + organization
                + ","
                + str(members)
                + ","
                + str(teams)
                + ","
                + str(len(self.unique_contributors))
                + "\n"
            )
            for repo in self.all_repos:
                output.write(
                    ",,,,,"
                    + repo.name
                    + ","
                    + str(repo.contributors)
                    + ","
                    + str(repo.forks)
                    + ","
                    + str(repo.stargazers)
                    + ","
                    + str(repo.pull_requests)
                    + ","
                    + str(repo.open_issues)
                    + ","
                    + str(repo.readme)
                    + ","
                    + str(repo.license)
                    + ","
                    + " ".join(sorted(repo.languages))
                    + ","
                    + str(repo.pull_requests_open)
                    + ","
                    + str(repo.pull_requests_closed)
                    + ","
                    + str(repo.commits)
                    + ","
                    + str(repo.closed_issues)
                    + ","
                    + str(repo.issues)
                    + "\n"
                )
            output.write(
                ",,,,total,"
                + str(self.total_repos)
                + ","
                + str(self.total_contributors)
                + ","
                + str(self.total_forks)
                + ","
                + str(self.total_stars)
                + ","
                + str(self.total_pull_reqs)
                + ","
                + str(self.total_open_issues)
                + ","
                + str(self.total_readmes)
                + ","
                + str(self.total_licenses)
                + ",,"
                + str(self.total_pull_reqs_open)
                + ","
                + str(self.total_pull_reqs_closed)
                + ","
                + str(self.total_commits)
                + ","
                + str(self.total_closed_issues)
                + ","
                + str(self.total_issues)
            )
        output.close()
        # Update total
        self.write_totals(
            file_path="../github_stats_output/total.csv",
            date=date,
            organization=organization,
            members=members,
            teams=teams,
        )
        # Update language sizes
        self.write_languages(
            file_path="../github_stats_output/languages.csv", date=date
        )

    def write_totals(
        self,
        file_path="",
        date=str(datetime.date.today()),
        organization="N/A",
        members=0,
        teams=0,
    ):
        """
        Updates the total.csv file with current data.
        """

        total_exists = os.path.isfile(file_path)
        with open(file_path, "a") as out_total:
            if not total_exists:
                out_total.write(
                    "date,organization,repos,members,teams,"
                    + "unique_contributors,total_contributors,forks,"
                    + "stargazers,pull_requests,open_issues,has_readme,"
                    + "has_license,pull_requests_open,pull_requests_closed,"
                    + "commits,id,closed_issues,issues\n"
                )
            self.delete_last_line(date=date, file_path=file_path)
        out_total.close()
        with open(file_path, "r") as file_read:
            row_count = sum(1 for row in file_read) - 1
        file_read.close()
        with open(file_path, "a") as out_total:
            out_total.write(
                date
                + ","
                + organization
                + ","
                + str(self.total_repos)
                + ","
                + str(members)
                + ","
                + str(teams)
                + ","
                + str(len(self.unique_contributors))
                + ","
                + str(self.total_contributors)
                + ","
                + str(self.total_forks)
                + ","
                + str(self.total_stars)
                + ","
                + str(self.total_pull_reqs)
                + ","
                + str(self.total_open_issues)
                + ","
                + str(self.total_readmes)
                + ","
                + str(self.total_licenses)
                + ","
                + str(self.total_pull_reqs_open)
                + ","
                + str(self.total_pull_reqs_closed)
                + ","
                + str(self.total_commits)
                + ","
                + str(row_count)
                + ","
                + str(self.total_closed_issues)
                + ","
                + str(self.total_issues)
                + "\n"
            )
        out_total.close()

    def write_languages(self, file_path="", date=str(datetime.date.today())):
        """
        Updates languages.csv file with current data.
        """
        self.remove_date(file_path=file_path, date=date)
        languages_exists = os.path.isfile(file_path)
        with open(file_path, "a") as out_languages:
            if not languages_exists:
                out_languages.write("date,language,count,size,size_log\n")
            languages_sorted = sorted(self.languages_size)
            # self.delete_last_line(date=date, file_path=file_path)
            for language in languages_sorted:
                try:
                    out_languages.write(
                        date
                        + ","
                        + language
                        + ","
                        + str(self.languages[language])
                        + ","
                        + str(self.languages_size[language])
                        + ","
                        + str(math.log10(int(self.languages_size[language])))
                        + "\n"
                    )
                except (TypeError, KeyError):
                    out_languages.write(
                        date
                        + ","
                        + language
                        + ","
                        + str(0)
                        + ","
                        + str(self.languages_size[language])
                        + ","
                        + str(math.log10(int(self.languages_size[language])))
                        + "\n"
                    )

    def checkDir(self, file_path=""):
        """
        Checks if a directory exists. If not, it creates one with the specified
        file_path.
        """
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

    def remove_date(self, file_path="", date=str(datetime.date.today())):
        """
        Removes all rows of the associated date from the given csv file.
        Defaults to today.
        """
        languages_exists = os.path.isfile(file_path)
        if languages_exists:
            with open(file_path, "rb") as inp, open("temp.csv", "wb") as out:
                writer = csv.writer(out)
                for row in csv.reader(inp):
                    if row[0] != date:
                        writer.writerow(row)
            inp.close()
            out.close()
            os.remove(file_path)
            os.rename("temp.csv", file_path)

    def delete_last_line(self, file_path="", date=str(datetime.date.today())):
        """
        The following code was modified from
        http://stackoverflow.com/a/10289740 &
        http://stackoverflow.com/a/17309010
        It essentially will check if the total for the current date already
        exists in total.csv. If it does, it just removes the last line.
        This is so the script could be run more than once a day and not
        create many entries in the total.csv file for the same date.
        """
        deleted_line = False
        if os.path.isfile(file_path):
            with open(file_path, "r+") as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:
                    if date == row[0]:
                        file.seek(0, os.SEEK_END)
                        pos = file.tell() - 1
                        while pos > 0 and file.read(1) != "\n":
                            pos -= 1
                            file.seek(pos, os.SEEK_SET)
                        if pos > 0:
                            file.seek(pos, os.SEEK_SET)
                            file.truncate()
                            deleted_line = True
                            break
                if deleted_line:
                    file.write("\n")
            file.close()


if __name__ == "__main__":
    my_github = GitHub_LLNL_Stats()
    my_github.get_stats()
