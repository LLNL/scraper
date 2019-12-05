import github3, datetime, os, errno, getpass, time, csv, math, my_repo
from collections import defaultdict


class GitHub_LLNL_Year_Commits:
    def __init__(self):
        self.commits_dict_list = []
        self.commits = {}
        self.sorted_weeks = []

    def get_year_commits(
        self, username="", password="", organization="llnl", force=True
    ):
        """
        Does setup such as login, printing API info, and waiting for GitHub to
        build the commit statistics. Then gets the last year of commits and
        prints them to file.
        """
        date = str(datetime.date.today())
        file_path = "year_commits.csv"
        if force or not os.path.isfile(file_path):
            my_github.login(username, password)
            calls_beginning = self.logged_in_gh.ratelimit_remaining + 1
            print "Rate Limit: " + str(calls_beginning)
            my_github.get_org(organization)
            my_github.repos(building_stats=True)
            print "Letting GitHub build statistics."
            time.sleep(30)
            print "Trying again."
            my_github.repos(building_stats=False)
            my_github.calc_total_commits(starting_commits=35163)
            my_github.write_to_file()
            calls_remaining = self.logged_in_gh.ratelimit_remaining
            calls_used = calls_beginning - calls_remaining
            print (
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

            token = ""
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
                token = auth.token
                id = auth.id
                with open("CREDENTIALS_FILE", "w+") as fd:
                    fd.write(token + "\n")
                    fd.write(str(id))
                fd.close()
            else:
                with open("CREDENTIALS_FILE", "r") as fd:
                    token = fd.readline().strip()
                    id = fd.readline().strip()
                fd.close()
            print "Logging in."
            self.logged_in_gh = github3.login(
                token=token, two_factor_callback=self.prompt_2fa
            )
            self.logged_in_gh.user().to_json()
        except (ValueError, AttributeError, github3.models.GitHubError) as e:
            print "Bad credentials. Try again."
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
        print "Getting organization."
        self.org_retrieved = self.logged_in_gh.organization(organization_name)

    def repos(self, building_stats=False):
        """
        Retrieves the last year of commits for the organization and stores them
        in weeks (UNIX time) associated with number of commits that week.
        """
        print "Getting repos."
        for repo in self.org_retrieved.iter_repos():
            for activity in repo.iter_commit_activity():
                if not building_stats:
                    self.commits_dict_list.append(activity)

    def calc_total_commits(self, starting_commits=0):
        """
        Uses the weekly commits and traverses back through the last
        year, each week subtracting the weekly commits and storing them. It
        needs an initial starting commits number, which should be taken from
        the most up to date number from github_stats.py output.
        """
        for week_of_commits in self.commits_dict_list:
            try:
                self.commits[week_of_commits["week"]] -= week_of_commits["total"]
            except KeyError:
                total = self.commits[week_of_commits["week"]] = -week_of_commits[
                    "total"
                ]
        self.sorted_weeks = sorted(self.commits)

        # reverse because lower numbered weeks are older in time.
        # we traverse from most recent to oldest
        for week in reversed(self.sorted_weeks):
            self.commits[week] = self.commits[week] + starting_commits
            starting_commits = self.commits[week]

    def write_to_file(self):
        """
        Writes the weeks with associated commits to file.
        """
        with open("../github_stats_output/last_year_commits.csv", "w+") as output:
            output.write(
                "date,organization,repos,members,teams,"
                + "unique_contributors,total_contributors,forks,"
                + "stargazers,pull_requests,open_issues,has_readme,"
                + "has_license,pull_requests_open,pull_requests_closed,"
                + "commits\n"
            )
            # no reverse this time to print oldest first
            previous_commits = 0
            for week in self.sorted_weeks:
                if str(self.commits[week]) != previous_commits:  # delete dups
                    week_formatted = datetime.datetime.utcfromtimestamp(week).strftime(
                        "%Y-%m-%d"
                    )
                    output.write(
                        week_formatted
                        + ",llnl,0,0,0,0,0,0,0,0,0,0,0,0,0,"
                        + str(self.commits[week])
                        + "\n"
                    )
                    previous_commits = str(self.commits[week])


if __name__ == "__main__":
    my_github = GitHub_LLNL_Year_Commits()
    my_github.get_year_commits()
