import github3, datetime, os, errno, getpass, time, csv, math, my_repo, json
import requests, urllib2, calendar
from collections import defaultdict


class GitHub_Traffic:
    def __init__(self):
        self.referrers = {}
        self.referrers_lower = {}
        self.views = {}
        self.clones = {}

        self.referrers_json = {}
        self.views_json = {}
        self.clones_json = {}
        self.releases_json = {}

    def get_stats(self, username="", password="", organization="llnl", force=True):
        """
        Retrieves the traffic for the users of the given organization.
        Requires organization admin credentials token to access the data.
        """
        date = str(datetime.date.today())
        referrers_file_path = "../github_stats_output/referrers.csv"
        views_file_path = "../github_stats_output/views.csv"
        clones_file_path = "../github_stats_output/clones.csv"
        if force or not os.path.isfile(file_path):
            my_github.login(username, password)
            calls_beginning = self.logged_in_gh.ratelimit_remaining + 1
            print "Rate Limit: " + str(calls_beginning)
            my_github.get_org(organization)
            my_github.get_traffic()
            views_row_count = my_github.check_data_redundancy(
                file_path=views_file_path, dict_to_check=self.views
            )
            clones_row_count = my_github.check_data_redundancy(
                file_path=clones_file_path, dict_to_check=self.clones
            )
            my_github.write_to_file(
                referrers_file_path=referrers_file_path,
                views_file_path=views_file_path,
                clones_file_path=clones_file_path,
                views_row_count=views_row_count,
                clones_row_count=clones_row_count,
            )
            my_github.write_json(
                dict_to_write=self.referrers_json,
                path_ending_type="traffic_popular_referrers",
            )
            my_github.write_json(
                dict_to_write=self.views_json, path_ending_type="traffic_views"
            )
            my_github.write_json(
                dict_to_write=self.clones_json, path_ending_type="traffic_clones"
            )
            my_github.write_json(
                dict_to_write=self.releases_json, path_ending_type="releases"
            )
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
            if not os.path.isfile("CREDENTIALS_FILE_ADMIN"):
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
                with open("CREDENTIALS_FILE_ADMIN", "w+") as fd:
                    fd.write(self.token + "\n")
                    fd.write(str(id))
                fd.close()
            else:
                with open("CREDENTIALS_FILE_ADMIN", "r") as fd:
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

    def get_traffic(self):
        """
        Retrieves the traffic for the repositories of the given organization.
        """
        print "Getting traffic."
        # Uses the developer API. Note this could change.
        headers = {
            "Accept": "application/vnd.github.spiderman-preview",
            "Authorization": "token " + self.token,
        }
        headers_release = {"Authorization": "token " + self.token}
        for repo in self.org_retrieved.iter_repos(type="public"):
            url = (
                "https://api.github.com/repos/"
                + self.organization_name
                + "/"
                + repo.name
            )
            self.get_referrers(url=url, headers=headers, repo_name=repo.name)
            self.get_paths(url=url, headers=headers)
            self.get_data(
                url=url,
                headers=headers,
                dict_to_store=self.views,
                type="views",
                repo_name=repo.name,
            )
            self.get_data(
                url=url,
                headers=headers,
                dict_to_store=self.clones,
                type="clones",
                repo_name=repo.name,
            )
            self.get_releases(url=url, headers=headers_release, repo_name=repo.name)

    def get_releases(self, url="", headers={}, repo_name=""):
        """
        Retrieves the releases for the given repo in JSON.
        """
        url_releases = url + "/releases"
        r = requests.get(url_releases, headers=headers)
        self.releases_json[repo_name] = r.json()

    def get_referrers(self, url="", headers={}, repo_name=""):
        """
        Retrieves the total referrers and unique referrers of all repos in json
        and then stores it in a dict.
        """
        # JSON
        url_referrers = url + "/traffic/popular/referrers"
        r1 = requests.get(url_referrers, headers=headers)
        referrers_json = r1.json()
        self.referrers_json[repo_name] = referrers_json
        # CSV
        for referrer in referrers_json:
            ref_name = referrer["referrer"]
            try:
                tuple_in = (referrer["count"], referrer["uniques"])  # curr vals
                tuple = (
                    self.referrers[ref_name][0] + tuple_in[0],  # cal new vals
                    self.referrers[ref_name][1] + tuple_in[1],
                )
                self.referrers[ref_name] = tuple  # record new vals
            except KeyError:
                tuple = self.referrers[ref_name] = (
                    referrer["count"],
                    referrer["uniques"],
                )
                self.referrers_lower[ref_name.lower()] = ref_name

    def get_paths(self, url="", headers={}):
        """
        Retrieves the popular paths information in json and then stores it in a
        dict.
        """
        url_paths = url + "/traffic/popular/paths"
        # r2 = requests.get(url_paths, headers=headers)
        # print 'PATHS ' + str(r2.json())

    def get_data(
        self,
        url="",
        headers={},
        date=str(datetime.date.today()),
        dict_to_store={},
        type="",
        repo_name="",
    ):
        """
        Retrieves data from json and stores it in the supplied dict. Accepts
        'clones' or 'views' as type.
        """
        # JSON
        url = url + "/traffic/" + type
        r3 = requests.get(url, headers=headers)
        json = r3.json()
        if type == "views":
            self.views_json[repo_name] = json
        elif type == "clones":
            self.clones_json[repo_name] = json
        # CSV
        for day in json[type]:
            timestamp_seconds = day["timestamp"] / 1000
            try:
                date_timestamp = datetime.datetime.utcfromtimestamp(
                    timestamp_seconds
                ).strftime("%Y-%m-%d")
                # do not add todays date, some views might not be recorded yet
                if date_timestamp != date:
                    tuple_in = (day["count"], day["uniques"])
                    tuple = (
                        dict_to_store[timestamp_seconds][0] + tuple_in[0],
                        dict_to_store[timestamp_seconds][1] + tuple_in[1],
                    )
                    dict_to_store[timestamp_seconds] = tuple
            except KeyError:
                tuple = dict_to_store[timestamp_seconds] = (
                    day["count"],
                    day["uniques"],
                )

    def write_json(
        self,
        date=(datetime.date.today()),
        organization="llnl",
        dict_to_write={},
        path_ending_type="",
    ):
        """
        Writes all traffic data to file in JSON form.
        """
        for repo in dict_to_write:
            if len(dict_to_write[repo]) != 0:  # don't need to write out empty lists
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
        referrers_file_path="",
        views_file_path="",
        clones_file_path="",
        date=(datetime.date.today()),
        organization="llnl",
        views_row_count=0,
        clones_row_count=0,
    ):
        """
        Writes all traffic data to file.
        """
        self.write_referrers_to_file(file_path=referrers_file_path)
        self.write_data_to_file(
            file_path=views_file_path,
            dict_to_write=self.views,
            name="views",
            row_count=views_row_count,
        )
        self.write_data_to_file(
            file_path=clones_file_path,
            dict_to_write=self.clones,
            name="clones",
            row_count=clones_row_count,
        )

    def check_data_redundancy(self, file_path="", dict_to_check={}):
        """
        Checks the given csv file against the json data scraped for the given
        dict. It will remove all data retrieved that has already been recorded
        so we don't write redundant data to file. Returns count of rows from
        file.
        """
        count = 0
        exists = os.path.isfile(file_path)
        previous_dates = {}
        if exists:
            with open(file_path, "r") as input:
                input.readline()  # skip header line
                for row in csv.reader(input):
                    timestamp = calendar.timegm(time.strptime(row[0], "%Y-%m-%d"))
                    if timestamp in dict_to_check:  # our date is already recorded
                        del dict_to_check[timestamp]
                    # calc current id max
                    count += 1
            input.close()
        return count

    def write_data_to_file(
        self,
        file_path="",
        date=str(datetime.date.today()),
        organization="llnl",
        dict_to_write={},
        name="",
        row_count=0,
    ):
        """
        Writes given dict to file.
        """
        exists = os.path.isfile(file_path)
        with open(file_path, "a") as out:
            if not exists:
                out.write("date,organization," + name + ",unique_" + name + ",id\n")
            sorted_dict = sorted(dict_to_write)
            for day in sorted_dict:
                day_formatted = datetime.datetime.utcfromtimestamp(day).strftime(
                    "%Y-%m-%d"
                )
                out.write(
                    day_formatted
                    + ","
                    + organization
                    + ","
                    + str(dict_to_write[day][0])
                    + ","
                    + str(dict_to_write[day][1])
                    + ","
                    + str(row_count)
                    + "\n"
                )
                row_count += 1

    def write_referrers_to_file(
        self, file_path="", date=str(datetime.date.today()), organization="llnl"
    ):
        """
        Writes the referrers data to file.
        """
        self.remove_date(file_path=file_path, date=date)
        referrers_exists = os.path.isfile(file_path)
        with open(file_path, "a") as out:
            if not referrers_exists:
                out.write(
                    "date,organization,referrer,count,count_log,uniques,"
                    + "uniques_logged\n"
                )
            sorted_referrers = sorted(self.referrers_lower)  # sort based on lowercase
            for referrer in sorted_referrers:
                ref_name = self.referrers_lower[referrer]  # grab real name from
                count = self.referrers[ref_name][0]
                uniques = self.referrers[ref_name][1]
                if count == 1:  # so we don't display 0 for count of 1
                    count = 1.5
                if uniques == 1:
                    uniques = 1.5
                count_logged = math.log(count)
                uniques_logged = math.log(uniques)
                out.write(
                    date
                    + ","
                    + organization
                    + ","
                    + ref_name
                    + ","
                    + str(count)
                    + ","
                    + str(count_logged)
                    + ","
                    + str(uniques)
                    + ","
                    + str(uniques_logged)
                    + "\n"
                )
        out.close()

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


if __name__ == "__main__":
    my_github = GitHub_Traffic()
    my_github.get_stats()
