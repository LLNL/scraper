import os
import subprocess
import json
import re

"""Module for GitHub query and data management.

With this module, you will be able to send GraphQL and REST queries
to GitHub, as well as read and write JSON files to store data.

"""


class GitHubQueryManager:
    """GitHub query API manager."""

    def __init__(self, apiToken=None, maxRetry=10):
        """Initialize the GitHubQueryManager object.

        Note:
            If no apiToken argument is provided,
            the environment variable 'GITHUB_API_TOKEN' must be set.

        Args:
            apiToken (Optional[str]): A string representing a GitHub API
                token. Defaults to None.
            maxRetry (Optional[int]): A limit on how many times to
                automatically retry requests. Defaults to 10.

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
        self.maxRetry = maxRetry
        self.data = {}
        """Dict: Working data."""

    @property
    def maxRetry(self):
        """int: A limit on how many times to automatically retry requests.

        Must be a whole integer greater than 0.
        """
        return self.__maxRetry

    @maxRetry.setter
    def maxRetry(self, maxRetry):
        numIn = int(maxRetry)
        if not numIn > 0:
            numIn = 1
        self.__maxRetry = numIn
        print("Auto-retry limit for requests set to %i." % (self.maxRetry))

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

    def data_Reset(self):
        """Reset the internal JSON data dictionary."""
        self.data = {}
        print("Stored data has been reset.")

    def dataFile_Load(self, filePath=None, updatePath=True):
        """Load a JSON data file into the internal JSON data dictionary.

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

    def dataFile_Save(self, filePath=None, updatePath=False):
        """Write the internal JSON data dictionary to a JSON data file.

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

    def _readGQL(self, filePath, verbose=False):
        """Read a 'pretty' formatted GraphQL query file into a one-line string.

        Removes line breaks and comments. Condenses white space.

        Args:
            filePath (str): A relative or absolute path to a file containing
                a GraphQL query.
                File may use comments and multi-line formatting.
                .. _GitHub GraphQL Explorer:
                   https://developer.github.com/v4/explorer/
            verbose (Optional[bool]): If False, prints will be suppressed.
                Defaults to False.

        Returns:
            str: A single line GraphQL query.

        """
        if not os.path.isfile(filePath):
            raise RuntimeError("Query file '%s' does not exist." % (filePath))
        if verbose:
            print("Reading '%s' ... " % (filePath), end="", flush=True)
        with open(filePath, "r") as q:
            # Strip all comments and newlines.
            query_in = re.sub(r'#.*(\n|\Z)', '\n', q.read())
            # Condense etra whitespace.
            query_in = re.sub(r'\s+', ' ', query_in)
            # Remove any leading or trailing whitespace.
            query_in = re.sub(r'(\A\s+)|(\s+\Z)', '', query_in)
        if verbose:
            print("File read!")
        return query_in

    def queryGitHubFromFile(self, filePath, gitvars={}, verbosity=0):
        """Submit a GitHub GraphQL query from a file.

        Can only be used with GraphQL queries.
        For REST queries, see the 'queryGitHub' method.

        Args:
            filePath (str): A relative or absolute path to a file containing
                a GraphQL query.
                File may use comments and multi-line formatting.
                .. _GitHub GraphQL Explorer:
                   https://developer.github.com/v4/explorer/
            gitvars (Optional[Dict]): All query variables.
                Only for GraphQL queries. Defaults to empty.
            verbosity (Optional[int]): Changes output verbosity levels.
                If < 0, all extra printouts are suppressed.
                If == 0, normal print statements are displayed.
                If > 0, additional status print statements are displayed.
                Defaults to 0.

        Returns:
            Dict: A JSON style dictionary.

        """
        gitquery = self._readGQL(filePath, verbose=(verbosity >= 0))
        return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity)

    def queryGitHub(self, gitquery, gitvars={}, verbosity=0, rest=False, requestCount=0):
        """Submit a GitHub query.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/user'
            gitvars (Optional[Dict]): All query variables.
                Only for GraphQL queries. Defaults to empty.
            verbosity (Optional[int]): Changes output verbosity levels.
                If < 0, all extra printouts are suppressed.
                If == 0, normal print statements are displayed.
                If > 0, additional status print statements are displayed.
                Defaults to 0.
            rest (Optional[bool]): If True, uses the REST API instead
                of GraphQL. Defaults to False.
            requestCount (Optional[int]): Counter for repeated requests.

        Returns:
            Dict: A JSON style dictionary.

        """
        requestCount += 1

        if verbosity >= 0:
            print("Sending GraphQL query...")
        response = self._submitQuery(gitquery, gitvars=gitvars, verbose=(verbosity > 0), rest=rest)
        if verbosity >= 0:
            print("Checking response...")
            print(response["heads"][0])

        outObj = json.loads(response["result"])
        return outObj

    def _submitQuery(self, gitquery, gitvars={}, verbose=False, rest=False):
        """Send a curl request to GitHub.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/user'
            gitvars (Optional[Dict]): All query variables.
                Only for GraphQL queries. Defaults to empty.
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
            gitqueryJSON = json.dumps({'query': gitquery, 'variables': json.dumps(gitvars)})
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
