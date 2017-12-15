# Scraper

Scraper is a tool for scraping and visualizing open source data from GitHub.

## Getting Started: Code.gov

[Code.gov](https://code.gov) is a newly launched website of the US Federal
Government to allow the People to access metadata from the governments custom
developed software. This site requires metadata to function, and this Python
library can help with that!

To get started, you will need a GitHub Personal Auth Token to make requests to
the GitHub API. This should be set in your environment or shell ``rc`` file with
the name ``GITHUB_API_TOKEN``:

    $ export GITHUB_API_TOKEN=XYZ

    $ echo "export GITHUB_API_TOKEN=XYZ" >> ~/.bashrc


To generate a ``code.json`` file for your GitHub organization:

    $ pip install -e .

    $ scraper --agency <agency_name> --github-orgs <list of github org usernames ...>

    # Example
    $ scraper --agency DOE --github-orgs llnl

A full example of the resulting ``code.json`` file can be [found
here](https://gist.github.com/IanLee1521/b7d7c0c2d8c24b10dd04edd5e8cab6c4).

## License

Scraper is released under an MIT license. For more details see the
[LICENSE](/LICENSE) file.

LLNL-CODE-705597
