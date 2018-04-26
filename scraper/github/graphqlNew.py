import os
import json
import subprocess

"""Module for GitHub query and data management.

With this module, you will be able to send GraphQL queries to GitHub,
as well as read and write JSON files to store data.

"""


class GitHubGraphQL:
    """GitHub GraphQL API manager."""

    def __init__(self, apiToken=None):
        """Initialize the GitHubGraphQL object.

        Note:
            If no apiToken argument is provided,
            the environment variable 'GITHUB_API_TOKEN' must be set.

        Args:
            apiToken (Optional[str]): A string representing a GitHub API
                token. Defaults to None.

        Raises:
            TypeError: If no GitHub API token is provided either via
            argument or environment variable 'GITHUB_API_TOKEN'.

        """

        # Get GitHub API token
        if apiToken:
            self.__githubApiToken = apiToken
        else:
            try:
                self.__githubApiToken = os.environ['GITHUB_API_TOKEN']
            except KeyError as error:
                raise TypeError("Requires either a string argument or environment variable 'GITHUB_API_TOKEN'.") from error

        # Check token validity
        print("Checking GitHub API token... ", end="", flush=True)
        basicCheck = self._submitQuery('query { viewer { login } }')
        if basicCheck["statusNum"] == 401:
            print("FAILED.")
            raise ValueError("GitHub API token is not valid.\n" + basicCheck["heads"][0] + " " + basicCheck["result"])
        else:
            print("Token validated.")

        # Initialize other variables
        self.data = {}
        self.__maxRequests = 10  # Limit auto re-sending a request

    @property
    def dataFilePath(self):
        """str: Absolute path to a JSON format data file.

        Can accept relative paths, but will always convert them to
        the absolute path.
        """
        return self.__dataFilePath

    @dataFilePath.setter
    def dataFilePath(self, dataFilePath):
        if dataFilePath:
            if not os.path.isfile(dataFilePath):
                print("Data file '%s' does not currently exist. Saving data will create a new file." % (dataFilePath))
        self.__dataFilePath = os.path.abspath(dataFilePath)
        print("Stored new data file path '%s'" % (self.dataFilePath))

    def resetData(self):
        """Reset the internal JSON data object."""
        self.data = {}
        print("Stored data has been reset.")

    def loadDataFile(self, filePath=None, updatePath=True):
        """Load a JSON data file into the internal JSON data object.

        If no file path is provided, the stored data file path will be used.

        Args:
            filePath (Optional[str]): A relative or absolute path to a
                '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update
                the stored data file path. Defaults to True.

        """
        if not filePath:
            filePath = self.dataFilePath
        if not os.path.isfile(filePath):
            raise FileNotFoundError("Data file '%s' does not exist." % (filePath))
        else:
            print("Importing existing data file '%s' ..." % (filePath))
            with open(filePath, "r") as q:
                data_raw = q.read()
            self.data = json.loads(data_raw)
            if updatePath:
                self.dataFilePath(filePath)

    def saveDataFile(self, filePath=None, updatePath=False):
        """Write the internal JSON data object to a JSON data file.

        If no file path is provided, the stored data file path will be used.

        Args:
            filePath (Optional[str]): A relative or absolute path to a
                '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update
                the stored data file path. Defaults to False.

        """
        if not filePath:
            filePath = self.dataFilePath
        if not os.path.isfile(filePath):
            print("Data file '%s' does not exist, will create new file." % (filePath))
        dataJsonString = json.dumps(self.data, indent=4, sort_keys=True)
        print("Writing to file '%s' ..." % (filePath))
        with open(filePath, "w") as fileout:
            fileout.write(dataJsonString)
        print("Wrote file!")
        if updatePath:
            self.dataFilePath(filePath)

    def queryGitHub(self, gitquery, verbosity=0, requestCount=0):
        """Submit a GitHub query.

        Args:
            gitquery (str): The query itself.
            verbosity (Optional[int]): Changes output verbosity levels.
                If < 0, all extra printouts are suppressed.
                If == 0, normal print statements are displayed.
                If > 0, additional status print statements are displayed.
                Defaults to 0.
            requestCount (Optional[int]): Counter for repeated requests.

        Returns:
            Dict: A JSON style data object.

        """
        # apiError = False
        requestCount += 1

        if verbosity >= 0:
            print("Sending GraphQL query...")
        response = self._submitQuery(gitquery, verbose=(verbosity > 0))
        if verbosity >= 0:
            print("Checking response...")
            print(response["heads"][0])

        outObj = json.loads(response["result"])
        return outObj

    def _submitQuery(self, gitquery, verbose=False, rest=False):
        """Send a curl request to GitHub.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/users/defunkt'
            verbose (Optional[bool]): If False, stderr prints will be
                suppressed. Defaults to False.
            rest (Optional[bool]): If True, uses the REST API instead
                of GraphQL. Defaults to False.

        Returns:
            {
                'result' (str): The body of the response.
                'heads' (List[str]): The response headers.
                'statusNum' (int): The HTTP status code.
            }

        """
        errOut = subprocess.DEVNULL if not verbose else None
        authhead = 'Authorization: bearer ' + self.__githubApiToken

        bashcurl = 'curl -iH TMPauthhead -X POST -d TMPgitquery https://api.github.com/graphql' if not rest \
            else 'curl -iH TMPauthhead https://api.github.com' + gitquery
        bashcurl_list = bashcurl.split()
        bashcurl_list[2] = authhead
        if not rest:
            gitqueryJSON = json.dumps({'query': gitquery})
            bashcurl_list[6] = gitqueryJSON

        fullResponse = subprocess.check_output(bashcurl_list, stderr=errOut).decode().split('\r\n\r\n')
        heads = fullResponse[0].split('\r\n')
        if len(fullResponse) > 1:
            result = fullResponse[1]
        else:
            result = ""
        http = heads[0].split()
        statusNum = int(http[1])

        return {'result': result, 'heads': heads, 'statusNum': statusNum}
