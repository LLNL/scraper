# Scraper

Scraper is a tool for scraping and visualizing open source data from various
code hosting platforms, such as: GitHub.com, GitHub Enterprise, GitLab.com,
hosted GitLab, and Bitbucket Server.

## Getting Started: Code.gov

[Code.gov](https://code.gov) is a newly launched website of the US Federal
Government to allow the People to access metadata from the governments custom
developed software. This site requires metadata to function, and this Python
library can help with that!

To get started, you will need a [GitHub Personal Auth
Token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
to make requests to the GitHub API. This should be set in your environment or
shell `rc` file with the name `GITHUB_API_TOKEN`:

```shell
    $ export GITHUB_API_TOKEN=XYZ

    $ echo "export GITHUB_API_TOKEN=XYZ" >> ~/.bashrc
```

Additionally, to perform the labor hours estimation, you will need to install
`cloc` into your environment. This is typically done with a [Package
Manager](https://github.com/AlDanial/cloc#install-via-package-manager) such as
`npm` or `homebrew`.

Then to generate a `code.json` file for your agency, you will need a
`config.json` file to coordinate the platforms you will connect to and scrape
data from. An example config file can be found in [demo.json](/demo.json). Once
you have your config file, you are ready to install and run the scraper!

```shell
    # Install Scraper from a local copy of this repository
    $ pip install -e .
    # OR
    # Install Scraper from PyPI
    $ pip install llnl-scraper

    # Run Scraper with your config file ``config.json``
    $ scraper --config config.json
```

A full example of the resulting `code.json` file can be [found
here](https://gist.github.com/IanLee1521/b7d7c0c2d8c24b10dd04edd5e8cab6c4).

## Config File Options

The configuration file is a json file that specifies what repository platforms
to pull projects from as well as some settings that can be used to override
incomplete or inaccurate data returned via the scraping.

The basic structure is:

```jsonc
{
    // REQUIRED
    "contact_email": "...",  // Used when the contact email cannot be found otherwise

    // OPTIONAL
    "agency": "...",         // Your agency abbreviation here
    "organization": "...",   // The organization within the agency
    "permissions": { ... },  // Object containing default values for usageType and exemptionText

    // Platform configurations, described in more detail below
    "GitHub": [ ... ],
    "GitLab": [ ... ],
    "Bitbucket": [ ... ],
}
```

```jsonc
"GitHub": [
    {
        "url": "https://github.com",  // GitHub.com or GitHub Enterprise URL to inventory
        "token": null,                // Private token for accessing this GitHub instance
        "public_only": true,          // Only inventory public repositories

        "connect_timeout": 4,  // The timeout in seconds for connecting to the server
        "read_timeout": 10,    // The timeout in seconds to wait for a response from the server

        "orgs": [ ... ],    // List of organizations to inventory
        "repos": [ ... ],   // List of single repositories to inventory
        "exclude": [ ... ]  // List of organizations / repositories to exclude from inventory
    }
],
```

```jsonc
"GitLab": [
    {
        "url": "https://gitlab.com",  // GitLab.com or hosted GitLab instance URL to inventory
        "token": null,                // Private token for accessing this GitHub instance
        "fetch_languages": false,     // Include individual calls to API for language metadata. Very slow, so defaults to false. (eg, for 191 projects on internal server, 5 seconds for False, 12 minutes, 38 seconds for True)

        "orgs": [ ... ],    // List of organizations to inventory
        "repos": [ ... ],   // List of single repositories to inventory
        "exclude": [ ... ]  // List of groups / repositories to exclude from inventory
    }
]
```

```jsonc
"Bitbucket": [
    {
        "url": "https://bitbucket.internal",  // Base URL for a Bitbucket Server instance
        "username": "",                       // Username to authenticate with
        "password": "",                       // Password to authenticate with
        "token": "",                          // Token to authenticate with, if supplied username and password are ignored

        "exclude": [ ... ]  // List of projects / repositories to exclude from inventory
    }
]
```

```jsonc
"TFS": [
    {
        "url": "https://tfs.internal",  // Base URL for a Team Foundation Server (TFS) or Visual Studio Team Services (VSTS) or Azure DevOps instance
        "token": null,                  // Private token for accessing this TFS instance

        "exclude": [ ... ]  // List of projects / repositories to exclude from inventory
    }
]
```

## License

Scraper is released under an MIT license. For more details see the
[LICENSE](/LICENSE) file.

LLNL-CODE-705597
