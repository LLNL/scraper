"""
A module for GitHub query and data management.

With this module, you will be able to send GraphQL and REST queries
to GitHub, as well as read and write JSON files to store data.
"""

import json
import os
import re
import time

from datetime import datetime
from subprocess import check_output, DEVNULL  # nosec

import pytz


def _vPrint(verbose, *args, **kwargs):
    """Easy verbosity-control print method.

    Args:
        verbose (bool): Normal print if True, do nothing otherwise.
        *args: Argument list for the 'print' method.
        **kwargs: Keyword arguments for the 'print' method.

    """
    if verbose:
        return print(*args, **kwargs)
    else:
        pass


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
            raise ValueError("GitHub API token is not valid.\n" + basicCheck["headDict"]["http"] + " " + basicCheck["result"])
        else:
            print("Token validated.")

        # Initialize private variables
        self.__retryDelay = 3  #: Number of seconds to wait between retries.
        self.__query = None  #: Cached query string
        self.__queryPath = None  #: Path to query file
        self.__queryTimestamp = None  #: When query file was last modified

        # Initialize public variables
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
        print("Auto-retry limit for requests set to %d." % (self.maxRetry))

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
        lastModified = os.path.getmtime(filePath)
        absPath = os.path.abspath(filePath)
        if absPath == self.__queryPath and lastModified == self.__queryTimestamp:
            _vPrint(verbose, "Using cached query '%s'" % (os.path.basename(self.__queryPath)))
            query_in = self.__query
        else:
            _vPrint(verbose, "Reading '%s' ... " % (filePath), end="", flush=True)
            with open(filePath, "r") as q:
                # Strip all comments and newlines.
                query_in = re.sub(r'#.*(\n|\Z)', '\n', q.read())
                # Condense extra whitespace.
                query_in = re.sub(r'\s+', ' ', query_in)
                # Remove any leading or trailing whitespace.
                query_in = re.sub(r'(\A\s+)|(\s+\Z)', '', query_in)
            _vPrint(verbose, "File read!")
            self.__queryPath = absPath
            self.__queryTimestamp = lastModified
            self.__query = query_in
        return query_in

    def queryGitHubFromFile(self, filePath, gitvars={}, verbosity=0, **kwargs):
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
                Defaults to empty.
                GraphQL Only.
            verbosity (Optional[int]): Changes output verbosity levels.
                If < 0, all extra printouts are suppressed.
                If == 0, normal print statements are displayed.
                If > 0, additional status print statements are displayed.
                Defaults to 0.
            **kwargs: Keyword arguments for the 'queryGitHub' method.

        Returns:
            Dict: A JSON style dictionary.

        """
        gitquery = self._readGQL(filePath, verbose=(verbosity >= 0))
        return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, **kwargs)

    def queryGitHub(self, gitquery, gitvars={}, verbosity=0, paginate=False, cursorVar=None, keysToList=[], rest=False, requestCount=0, pageNum=0):
        """Submit a GitHub query.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/user'
            gitvars (Optional[Dict]): All query variables.
                Defaults to empty.
                GraphQL Only.
            verbosity (Optional[int]): Changes output verbosity levels.
                If < 0, all extra printouts are suppressed.
                If == 0, normal print statements are displayed.
                If > 0, additional status print statements are displayed.
                Defaults to 0.
            paginate (Optional[bool]): Pagination will be completed
                automatically if True. Defaults to False.
            cursorVar (Optional[str]): Key in 'gitvars' that represents the
                pagination cursor. Defaults to None.
                GraphQL Only.
            keysToList (Optional[List[str]]): Ordered list of keys needed to
                retrieve the list in the query results to be extended by
                pagination. Defaults to empty.
                Example:
                    ['data', 'viewer', 'repositories', 'nodes']
                GraphQL Only.
            rest (Optional[bool]): If True, uses the REST API instead
                of GraphQL. Defaults to False.
            requestCount (Optional[int]): Counter for repeated requests.
            pageNum (Optional[int]): Counter for pagination.
                For user readable log messages only, does not affect data.

        Returns:
            Dict: A JSON style dictionary.

        """
        requestCount += 1
        if pageNum < 0:  # no negative page numbers
            pageNum = 0
        pageNum += 1

        if paginate:
            _vPrint((verbosity >= 0), "Page %d" % (pageNum))
        _vPrint((verbosity >= 0), "Sending %s query..." % ("REST" if rest else "GraphQL"))
        response = self._submitQuery(gitquery, gitvars=gitvars, verbose=(verbosity > 0), rest=rest)
        _vPrint((verbosity >= 0), "Checking response...")
        _vPrint((verbosity >= 0), response["headDict"]["http"])
        statusNum = response["statusNum"]

        # Decrement page count before error checks to properly reflect any repeated queries
        pageNum -= 1

        # Make sure the query limit didn't run out
        try:
            apiStatus = {
                "limit": int(response["headDict"]["X-RateLimit-Limit"]),
                "remaining": int(response["headDict"]["X-RateLimit-Remaining"]),
                "reset": int(response["headDict"]["X-RateLimit-Reset"])
            }
            _vPrint((verbosity >= 0), "API Status %s" % (json.dumps(apiStatus)))
            if not apiStatus["remaining"] > 0:
                _vPrint((verbosity >= 0), "API usage limit reached during query.")
                self._awaitReset(apiStatus["reset"])
                _vPrint((verbosity >= 0), "Repeating query...")
                return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=(requestCount - 1), pageNum=pageNum)
        except KeyError:
            # Handles error cases that don't return X-RateLimit data
            _vPrint((verbosity >= 0), "Failed to check API Status.")

        # Check for accepted but not yet processed, usually due to un-cached data
        if statusNum == 202:
            if requestCount >= self.maxRetry:
                raise RuntimeError("Query attempted but failed %d times.\n%s\n%s" % (self.maxRetry, response["headDict"]["http"], response["result"]))
            else:
                self._countdown(self.__retryDelay, printString="Query accepted but not yet processed. Trying again in %*dsec...", verbose=(verbosity >= 0))
                return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=requestCount, pageNum=pageNum)
        # Check for server error responses
        if statusNum == 502 or statusNum == 503:
            if requestCount >= self.maxRetry:
                raise RuntimeError("Query attempted but failed %d times.\n%s\n%s" % (self.maxRetry, response["headDict"]["http"], response["result"]))
            else:
                self._countdown(self.__retryDelay, printString="Server error. Trying again in %*dsec...", verbose=(verbosity >= 0))
                return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=requestCount, pageNum=pageNum)
        # Check for other error responses
        if statusNum >= 400 or statusNum == 204:
            raise RuntimeError("Request got an Error response.\n%s\n%s" % (response["headDict"]["http"], response["result"]))

        _vPrint((verbosity >= 0), "Data received!")
        outObj = json.loads(response["result"])

        # Check for GraphQL API errors (e.g. repo not found)
        if not rest and "errors" in outObj:
            if requestCount >= self.maxRetry:
                raise RuntimeError("Query attempted but failed %d times.\n%s\n%s" % (self.maxRetry, response["headDict"]["http"], response["result"]))
            elif len(outObj["errors"]) == 1 and len(outObj["errors"][0]) == 1:
                # Poorly defined error type, usually intermittent, try again.
                _vPrint((verbosity >= 0), "GraphQL API error.\n%s" % (json.dumps(outObj["errors"])))
                self._countdown(self.__retryDelay, printString="Unknown API error. Trying again in %*dsec...", verbose=(verbosity >= 0))
                return self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=requestCount, pageNum=pageNum)
            else:
                raise RuntimeError("GraphQL API error.\n%s" % (json.dumps(outObj["errors"])))

        # Re-increment page count before the next page query
        pageNum += 1

        # Pagination
        if paginate:
            if rest and response["linkDict"]:
                if "next" in response["linkDict"]:
                    nextObj = self.queryGitHub(response["linkDict"]["next"], gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=0, pageNum=pageNum)
                    outObj.extend(nextObj)
            elif not rest:
                if not cursorVar:
                    raise ValueError("Must specify argument 'cursorVar' to use GraphQL auto-pagination.")
                if not len(keysToList) > 0:
                    raise ValueError("Must specify argument 'keysToList' as a non-empty list to use GraphQL auto-pagination.")
                aPage = outObj
                for key in keysToList[0:-1]:
                    aPage = aPage[key]
                gitvars[cursorVar] = aPage["pageInfo"]["endCursor"]
                if aPage["pageInfo"]["hasNextPage"]:
                    nextObj = self.queryGitHub(gitquery, gitvars=gitvars, verbosity=verbosity, paginate=paginate, cursorVar=cursorVar, keysToList=keysToList, rest=rest, requestCount=0, pageNum=pageNum)
                    newPage = nextObj
                    for key in keysToList[0:-1]:
                        newPage = newPage[key]
                    aPage[keysToList[-1]].extend(newPage[keysToList[-1]])
                aPage.pop("pageInfo", None)

        return outObj

    def _submitQuery(self, gitquery, gitvars={}, verbose=False, rest=False):
        """Send a curl request to GitHub.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/user'
            gitvars (Optional[Dict]): All query variables.
                Defaults to empty.
            verbose (Optional[bool]): If False, stderr prints will be
                suppressed. Defaults to False.
            rest (Optional[bool]): If True, uses the REST API instead
                of GraphQL. Defaults to False.

        Returns:
            {
                'statusNum' (int): The HTTP status code.
                'headDict' (Dict[str]): The response headers.
                'linkDict' (Dict[int]): Link based pagination data.
                'result' (str): The body of the response.
            }

        """
        errOut = DEVNULL if not verbose else None
        authhead = 'Authorization: bearer ' + self.__githubApiToken

        bashcurl = 'curl -iH TMPauthhead -X POST -d TMPgitquery https://api.github.com/graphql' if not rest \
            else 'curl -iH TMPauthhead https://api.github.com' + gitquery
        bashcurl_list = bashcurl.split()
        bashcurl_list[2] = authhead
        if not rest:
            gitqueryJSON = json.dumps({'query': gitquery, 'variables': json.dumps(gitvars)})
            bashcurl_list[6] = gitqueryJSON

        fullResponse = check_output(bashcurl_list, stderr=errOut).decode()
        _vPrint(verbose, "\n" + fullResponse)
        fullResponse = fullResponse.split('\r\n\r\n')
        heads = fullResponse[0].split('\r\n')
        if len(fullResponse) > 1:
            result = fullResponse[1]
        else:
            result = ""
        http = heads[0].split()
        statusNum = int(http[1])

        # Parse headers into a useful dictionary
        headDict = {}
        headDict["http"] = heads[0]
        for header in heads[1:]:
            h = header.split(': ')
            headDict[h[0]] = h[1]

        # Parse any Link headers even further
        linkDict = None
        if "Link" in headDict:
            linkProperties = headDict["Link"].split(', ')
            propDict = {}
            for item in linkProperties:
                divided = re.split(r'<https://api.github.com|>; rel="|"', item)
                propDict[divided[2]] = divided[1]
            linkDict = propDict

        return {'statusNum': statusNum, 'headDict': headDict, 'linkDict': linkDict, 'result': result}

    def _awaitReset(self, utcTimeStamp, verbose=True):
        """Wait until the given UTC timestamp.

        Args:
            utcTimeStamp (int): A UTC format timestamp.
            verbose (Optional[bool]): If False, all extra printouts will be
                suppressed. Defaults to True.

        """
        resetTime = pytz.utc.localize(datetime.utcfromtimestamp(utcTimeStamp))
        _vPrint(verbose, "--- Current Timestamp")
        _vPrint(verbose, "      %s" % (time.strftime('%c')))
        now = pytz.utc.localize(datetime.utcnow())
        waitTime = round((resetTime - now).total_seconds()) + 1
        _vPrint(verbose, "--- Current UTC Timestamp")
        _vPrint(verbose, "      %s" % (now.strftime('%c')))
        _vPrint(verbose, "--- GITHUB NEEDS A BREAK Until UTC Timestamp")
        _vPrint(verbose, "      %s" % (resetTime.strftime('%c')))
        self._countdown(waitTime, printString="--- Waiting %*d seconds...", verbose=verbose)
        _vPrint(verbose, "--- READY!")

    def _countdown(self, waitTime=0, printString="Waiting %*d seconds...", verbose=True):
        """Makes a pretty countdown.

        Args:
            gitquery (str): The query or endpoint itself.
                Examples:
                       query: 'query { viewer { login } }'
                    endpoint: '/user'
            printString (Optional[str]): A counter message to display.
                Defaults to 'Waiting %*d seconds...'
            verbose (Optional[bool]): If False, all extra printouts will be
                suppressed. Defaults to True.

        """
        if waitTime <= 0:
            waitTime = self.__retryDelay
        for remaining in range(waitTime, 0, -1):
            _vPrint(verbose, "\r" + printString % (len(str(waitTime)), remaining), end="", flush=True)
            time.sleep(1)
        if verbose:
            _vPrint(verbose, "\r" + printString % (len(str(waitTime)), 0))


class DataManager:
    """JSON data manager."""

    def __init__(self, filePath=None, loadData=False):
        """Initialize the DataManager object.
        Args:
            filePath (Optional[str]): Relative or absolute path to a JSON
                data file. Defaults to None.
            loadData (Optional[bool]): Loads data from the given file path
                if True. Defaults to False.

        """
        self.data = {}
        """Dict: Working data."""
        self.filePath = filePath
        if loadData:
            self.fileLoad(updatePath=False)

    @property
    def filePath(self):
        """str: Absolute path to a JSON format data file.

        Can accept relative paths, but will always convert them to
        the absolute path.
        """
        if not self.__filePath:
            raise ValueError("Internal variable filePath has not been set.")
        return self.__filePath

    @filePath.setter
    def filePath(self, filePath):
        if filePath:
            if not os.path.isfile(filePath):
                print("Data file '%s' does not currently exist. Saving data will create a new file." % (filePath))
            self.__filePath = os.path.abspath(filePath)
            print("Stored new data file path '%s'" % (self.filePath))
        else:
            self.__filePath = None

    def dataReset(self):
        """Reset the internal JSON data dictionary."""
        self.data = {}
        print("Stored data has been reset.")

    def fileLoad(self, filePath=None, updatePath=True):
        """Load a JSON data file into the internal JSON data dictionary.

        Current internal data will be overwritten.
        If no file path is provided, the stored data file path will be used.

        Args:
            filePath (Optional[str]): A relative or absolute path to a
                '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update
                the stored data file path. Defaults to True.

        """
        if not filePath:
            filePath = self.filePath
        if not os.path.isfile(filePath):
            raise FileNotFoundError("Data file '%s' does not exist." % (filePath))
        else:
            print("Importing existing data file '%s' ... " % (filePath), end="", flush=True)
            with open(filePath, "r") as q:
                data_raw = q.read()
            print("Imported!")
            self.data = json.loads(data_raw)
            if updatePath:
                self.filePath = filePath

    def fileSave(self, filePath=None, updatePath=False):
        """Write the internal JSON data dictionary to a JSON data file.

        If no file path is provided, the stored data file path will be used.

        Args:
            filePath (Optional[str]): A relative or absolute path to a
                '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update
                the stored data file path. Defaults to False.

        """
        if not filePath:
            filePath = self.filePath
        if not os.path.isfile(filePath):
            print("Data file '%s' does not exist, will create new file." % (filePath))
            if not os.path.exists(os.path.split(filePath)[0]):
                os.makedirs(os.path.split(filePath)[0])
        dataJsonString = json.dumps(self.data, indent=4, sort_keys=True)
        print("Writing to file '%s' ... " % (filePath), end="", flush=True)
        with open(filePath, "w") as fileout:
            fileout.write(dataJsonString)
        print("Wrote file!")
        if updatePath:
            self.filePath = filePath
