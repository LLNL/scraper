import github3, datetime, os, errno, getpass, time, csv, math, my_repo, json
import requests, urllib2, calendar
from collections import defaultdict


class GitHub_Stargazers:
    def __init__(self):
        self.repos = {}
        self.stargazers = {}
        self.total_count = 0

    def get_stats(self, username="", password="", organization="llnl", force=True):
        """
        Retrieves the traffic for the users of the given organization.
        Requires organization admin credentials token to access the data.
        """
        date = str(datetime.date.today())
        stargazers_file_path = "../github_stats_output/stargazers.csv"
        if force or not os.path.isfile(file_path):
            my_github.login(username, password)
            calls_beginning = self.logged_in_gh.ratelimit_remaining + 1
            print "Rate Limit: " + str(calls_beginning)
            my_github.get_org(organization)
            my_github.get_repos()
            my_github.write_to_file(file_path=stargazers_file_path)
            # my_github.write_to_file(file_path=stargazers_file_path)
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
            print "Logging in."
            self.logged_in_gh = github3.login(
                token=self.token, two_factor_callback=self.prompt_2fa
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
        self.organization_name = organization_name
        if organization_name == "":
            self.organization_name = raw_input("Organization: ")
        print "Getting organization."
        self.org_retrieved = self.logged_in_gh.organization(organization_name)

    def get_repos(self):
        """
        Gets the repos for the organization and builds the URL/headers for
        getting timestamps of stargazers.
        """
        print "Getting repos."
        # Uses the developer API. Note this could change.

        headers = {
            "Accept": "application/vnd.github.v3.star+json",
            "Authorization": "token " + self.token,
        }
        temp_count = 0
        for repo in self.org_retrieved.iter_repos():
            temp_count += 1
            url = (
                "https://api.github.com/repos/"
                + self.organization_name
                + "/"
                + repo.name
            )
            self.repos[repo.name] = self.get_stargazers(url=url, headers=headers)
        self.calc_stargazers(start_count=650)
        print "total count: \t" + str(self.total_count)
        print str(temp_count) + " repos"

    def get_stargazers(self, url, headers={}):
        """
        Return a list of the stargazers of a GitHub repo

        Includes both the 'starred_at' and 'user' data.

        param: url
            url is the 'stargazers_url' of the form:
                https://api.github.com/repos/LLNL/spack/stargazers
        """
        url = url + "/stargazers?per_page=100&page=%s"
        page = 1
        gazers = []

        json_data = requests.get(url % page, headers=headers).json()
        while json_data:
            gazers.extend(json_data)
            page += 1
            json_data = requests.get(url % page, headers=headers).json()
        return gazers

    def calc_stargazers(self, date=(datetime.date.today()), start_count=0):
        for repo_json in self.repos:
            for stargazer in self.repos[repo_json]:
                print stargazer
                date = stargazer["starred_at"][:10]
                try:
                    self.stargazers[date] += 1
                except KeyError:
                    count = self.stargazers[date] = 1

        sorted_stargazers = sorted(self.stargazers)
        for stargazer in reversed(sorted_stargazers):
            number_starred = self.stargazers[stargazer]
            self.stargazers[stargazer] = start_count - number_starred
            start_count = start_count - number_starred

    def write_to_file(
        self, file_path="", date=(datetime.date.today()), organization="llnl"
    ):
        """
        Writes stargazers data to file.
        """
        with open(file_path, "w+") as out:
            out.write("date,organization,stargazers\n")
            sorted_stargazers = sorted(self.stargazers)  # sort based on lowercase
            for star in sorted_stargazers:
                out.write(star + "," + str(self.stargazers[star]) + "\n")
        out.close()


if __name__ == "__main__":
    my_github = GitHub_Stargazers()
    my_github.get_stats()
