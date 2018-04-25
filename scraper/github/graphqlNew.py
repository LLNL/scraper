import os.path
import json

"""Module for GitHub query and data management.

With this module, you will be able to send GraphQL queries to GitHub, as well as read and write JSON files to store data.

"""

class GitHubGraphQL:

    __githubApiToken = None
    data = {}
    dataFile = None

    def __init__(self, apiToken=None):
        """Initialize the GitHubGraphQL object.

        Note:
            If no apiToken argument is provided, the environment variable 'GITHUB_API_TOKEN' must be set.

        Args:
            apiToken (Optional[str]): A string representing a GitHub API token. Defaults to None.
        
        """
        if apiToken :
            self.__githubApiToken = apiToken
        else:
            try:
                self.__githubApiToken = os.environ['GITHUB_API_TOKEN']
            except KeyError as error:
                raise TypeError("Requires either a string argument or environment variable 'GITHUB_API_TOKEN'.") from error

    # def showToken(self):
    #     """Only for debugging."""
    #     print(self.__githubApiToken)

    def resetData(self):
        """Reset the internal JSON data object."""
        self.data = {}
        print("Stored data has been reset.")

    def setDataFile(self, filePath):
        """Set the data file path.
        
        The provided file path can be used automatically by the loadDataFile and saveDataFile methods.
        
        Args:
            filePath (str): A relative or absolute path to a '.json' file.
        
        """
        if not os.path.isfile(filePath):
            print("Data file '%s' does not currently exist. Saving data will create a new file." % (filePath))
        self.dataFile = os.path.abspath(filePath)
        print("Stored new data file path '%s'" % (self.dataFile))

    def loadDataFile(self, filePath=None, updatePath=True):
        """Load a JSON data file into the internal JSON data object.
        
        If no file path is provided, the stored data file path will be used.
        
        Args:
            filePath (Optional[str]): A relative or absolute path to a '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update the stored data file path. Defaults to True.
        
        """
        if not filePath:
            filePath = self.dataFile
        if not os.path.isfile(filePath):
            raise FileNotFoundError("Data file '%s' does not exist." % (filePath))
        else:
            print("Importing existing data file '%s' ..." % (filePath))
            with open(filePath, "r") as q:
                data_raw = q.read()
            self.data = json.loads(data_raw)
            self.setDataFile(filePath)

    def saveDataFile(self, filePath=None, updatePath=False):
        """Write the internal JSON data object to a JSON data file.
        
        If no file path is provided, the stored data file path will be used.
        
        Args:
            filePath (Optional[str]): A relative or absolute path to a '.json' file. Defaults to None.
            updatePath (Optional[bool]): Specifies whether or not to update the stored data file path. Defaults to False.
        
        """
        if not filePath:
            filePath = self.dataFile
        if not os.path.isfile(filePath):
            print("Data file '%s' does not exist, will create new file." % (filePath))
        dataJsonString = json.dumps(self.data, indent=4, sort_keys=True)
        print("Writing to file '%s' ..." % (filePath))
        with open(filePath, "w") as fileout:
            fileout.write(dataJsonString)
        print("Wrote file!")
