import github3, datetime, os, errno, getpass, time, csv, math, my_repo, requests
from collections import defaultdict


class GitHub_Users_Emails:
    def __init__(self):
        self.emails = {}
        self.logins_lower = {}

    def get_stats(self, username="", password="", organization="llnl", force=True):
        """
        Retrieves the emails for the users of the given organization.
        """
        date = str(datetime.date.today())
        file_path = "../github_stats_output/users_emails.csv"
        if force or not os.path.isfile(file_path):
            my_github.login(username, password)
            calls_beginning = self.logged_in_gh.ratelimit_remaining + 1
            print "Rate Limit: " + str(calls_beginning)
            my_github.get_org(organization)
            count_members = my_github.get_mems_of_org()
            my_github.write_to_file(file_path)
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

    def get_mems_of_org(self):
        """
        Retrieves the emails of the members of the organization. Note this Only
        gets public emails. Private emails would need authentication for each
        user.
        """
        print "Getting members' emails."
        for member in self.org_retrieved.iter_members():
            login = member.to_json()["login"]
            user_email = self.logged_in_gh.user(login).to_json()["email"]
            if user_email is not None:
                self.emails[login] = user_email
            else:  # user has no public email
                self.emails[login] = "none"
            # used for sorting regardless of case
            self.logins_lower[login.lower()] = login

    def write_to_file(self, file_path=""):
        """
        Writes the user emails to file.
        """
        with open(file_path, "w+") as out:
            out.write("user, email\n")
            sorted_names = sorted(self.logins_lower)  # sort based on lowercase
            for login in sorted_names:
                out.write(
                    self.logins_lower[login]
                    + ","
                    + self.emails[self.logins_lower[login]]
                    + "\n"
                )
        out.close()


if __name__ == "__main__":
    my_github = GitHub_Users_Emails()
    my_github.get_stats()
