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

    $ export GITHUB_API_TOKEN=1234567890abcdef1234567890abcdef

    $ echo "export GITHUB_API_TOKEN=1234567890abcdef1234567890abcdef" >> ~/.bashrc


To generate a ``code.json`` file for your GitHub organization:

    $ pip install -r requirements.txt

    $ ./scraper/gen_code_gov_json.py --agency <agency_name> --organization <organzation full name> --github-orgs <list of github org usernames ...>

    # Example
    $ ./scraper/gen_code_gov_json.py --agency DOE --organization "Lawrence Livermore National Laboratory" --github-orgs chaos esgf flux-framework glvis llnl mfem rose-compiler zfsonlinux


## License

Scraper is released under an MIT license. For more details see the
[LICENSE](/LICENSE) file.

LLNL-CODE-705597
