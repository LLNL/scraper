# GitHub Organization Statistics
Maintainer: Joseph Eklund eklund7@llnl.gov

Github has a nice way for displaying statistics for individual repositories, but no way to visualize multiple repositories together. The purpose of this project is to scrape data from all repositories of a given [Github organization] and then create some simple graphs. It was designed for the [LLNL Organization], but should be able to be applied to any GitHub organization.
___
### github_stats.py

This script is the main scraper for getting the data for all the repositories of an organization.

##### Requirements
- [Github3.py]

##### How to run

Navigate to the `scripts` directory in terminal. Run the following command in terminal:
```sh
$ python github_scripts.py
```
If this is your first time running the script, it will prompt you for your GitHub username and password.
```sh
$ Username: octocat
$ Password:
```
It will also ask for a 2-factor authentication code if you have it enabled for your GitHub account.
```sh
$ Enter 2FA code: 123456
```
After you enter your credentials this time, it will save an authentication token to a `CREDENTIALS_FILE`, and no longer prompt you for a username and password for subsequent script runs.

It is important to give valid credentials because the script will not run without them. GitHub limits unauthenticated API requests to only 60 per hour, and several hundred are needed to retreive the data, depending on the size of the organization. With valid credentials, you get 5000 requests per hour.

##### Flags

You can specify what organization you would like to retrieve data from by modifying the `organization` value in the `github_stats.py` main method. This defaults to `llnl`.

You can force data retrieval by modifying the `force` value in the `github_stats.py` main method. This defaults to `True`. If `False` and data has already been retrieved for today then data will _not_ be retrieved.

##### Saved data
You can find the data in a series of `csv` files in the `github_stats_output` directory. `total.csv` is the file that data will get appended to each time the script is run and provides a quick overview of all the organization's repositories' data. The script will overwrite the latest entry if it is run multiple times per day, ensuring that only one entry per day is recorded. You can find a more in depth `csv` report for a particular day under `github_stats_output/<year>/<year-month>/<year-month-day.csv>`

___

### get_year_commits.py
This script retrieves the last year of commits for a given organization.

##### How to run
Navigate to the `scripts` directory in terminal. Run the following command in terminal:
```sh
$ python get_year_commits.py
```
It is run very similarly to `github_stats.py`, and follows the same login procedure. If you have already run `github_stats.py` with valid credentials, then you will not need to reenter them for this script. Please see above for the login procedure.

##### Saved data
You can find the data in `github_stats_output/last_year_commits.csv`.

___
### get_users_emails.py
This script retrieves the public emails for all members of a given organization.

##### How to run
Navigate to the `scripts` directory in terminal. Run the following command in terminal:
```sh
$ python get_users_emails.py
```
It is run very similarly to `github_stats.py`, and follows the same login procedure. If you have already run `github_stats.py` with valid credentials, then you will not need to reenter them for this script. Please see above for the login procedure.
##### Saved data
You can find the data in `github_stats_output/users_emails.csv`.

____

### get_traffic.py
This script retrieves the traffic for the repositories of a given organization. Administrator credentials are required to access this information. It currently uses the [preview developer API], which is subject to change. It gathers up to the previous two weeks of the following pieces of data: referrers, views, and clones.

##### How to run
Navigate to the `scripts` directory in terminal. Run the following command in terminal:
```sh
$ python get_traffic.py
```
Again, it uses the same login procedure. Requires admin credentials.

##### Saved data
You can find the data in `github_stats_output/referrers.csv`, `github_stats_output/views.csv`, and `github_stats_output/clones.csv`
___
### index.html

This html file displays graphs of the data collected using the above scripts. The scripts are written in JavaScript and it uses [D3] for visualization.

##### Requirements
- [D3 - Data-Driven Documents]
##### How to Run
You should be able to just open the index.html in any browser. It will dynamically pull from the data `csv` files created from the scripts. See the troubleshooting section if you only see a blank page.
___
### Troubleshooting

##### My `CREDENTIALS_FILE` is corrupt.

If your `CREDENTIALS_FILE` becomes corrupt or is lost, you will need to aquire a new token for the script. To do so, navigate to your GitHub settings page and then select Personal Access Tokens. There should be a token listed under the name, "GitHub Organization Stats App." Delete it. Make sure the `CREDENTIALS_FILE` is deleted from your local directory as well. Rerun the script and enter your credentials again.

##### My `index.html` page is blank when I open it in my browser.

When you open `index.html`, it could be blank because your browser is blocking access to local files. This is actually a security feature of many browsers (such as Chrome) and a good thing. To fix this you can do several things:

- Open `index.html` in a different browser. I've had success opening it in Firefox and having it display just fine.
- Run a small HTTP server by executing the following command in terminal in the top level directory of the project and then navigate to `localhost:8000`.

```sh
$ python -m SimpleHTTPServer
$ open http://localhost:8000
```
- Lastly, you can try running your browser with the `--allow-file-access-from-files` flag. _Note: I do NOT recommend this method because you are compromising the security of your browser. But it is here if no other method is working for you._

Windows
```sh
> .\chrome.exe --allow-file-access-from-files
```
MacOS
```sh
$ /Applications/Google\ Chrome.app/Contents/MacOS/rome --allow-file-access-from-files
```

If you are getting some security errors or other errors, make sure to exit all instances of Chrome before running the above commands.

##### I keep getting a  `Connection reset by peer` error.

If you keep getting some output like the following:
```sh
$ ...  
raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', error(54, 'Connection reset by peer'))
```
then you are most likely being blocked by the lab's firewall. Open a browser and attempt to access an external website (such as [github.com/llnl]). Login with your lab credentials and rerun the script.
___
### License

Copyright (c) 2016, Lawrence Livermore National Security, LLC.

Produced at the Lawrence Livermore National Laboratory.

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [GitHub organization]: https://github.com/blog/674-introducing-organizations
   [Github3.py]: https://github.com/sigmavirus24/github3.py
   [LLNL Organization]: https://github.com/LLNL/
   [D3]: https://d3js.org/
   [D3 - Data-Driven Documents]: https://d3js.org/
   [github.com/llnl]: https://github.com/llnl
   [preview developer API]:https://developer.github.com/changes/2016-08-15-traffic-api-preview/
