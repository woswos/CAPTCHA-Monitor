# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2020-07-19
### Added
- Relay nicknames
- Chromium and Chromium over Tor fetchers that use the HTTP Header Live extension (#36)
- CAPTCHA probability calculations for every relay (#34)

### Changed
- Moved the HTTP Header Live extension into this package, so users don't need to install
it seperately anymore (#32)

### Removed
- Unused imports


## [0.1.1] - 2020-07-08
### Added
- This CHANGELOG file
- Support for using multiple versions of the browsers (#2)
- Functionality to identify exit node's exitting capabilities through the IPv6Exit flag (#10)
- Checks for page integrity in addition to the CAPTCHA detection (#18)
- A submodule for getting md5 hash of the website at the given URL (#19)
- The first working version of the intelligent job dispatcher `compose` submodule (#23)
- GeoIP information to the relay information in the database (#25)
- Annotatations the dataset to indicate CAPTCHA Monitor version (#26)
- Ability to customize CAPTCHA sign for different pages (#31)
- More warning and error messages to cover more scenerios
- Timeouts to `webdriver` while fetching pages
- Proper `webdriver.quit()` statements to prevent memory leaks

### Changed
- Fixed the problem with JavaScript not being enabled all the time
- Switched to using [HTTP-Header-Live extension](https://gitlab.torproject.org/woswos/HTTP-Header-Live)
to capture HTTP headers (#16)
- Divided submodules `run`, `add`, `compose`, `md5`, etc. into different separate files (#22)
- Moved test types list to the database (#27)
  - Now new fetcher types, versions, and URls can be specified through the database
- Switched to using microdescriptors to save bandwidth
- Updated the README file to match v0.1.1 updates


## [0.1.0.1] - 2020-06-23
### Added
- Implemented #12 #15
- `-v` option to print all logs for debugging purposes
- `-c` option to clean existing cache files for Tor
- Heartbeat message


## [0.1.0] - 2020-06-22
### Added
- Implemented #8 #9 #11
- The ability to start many workers in parallel
- Proper Tor STEM integration to control exit nodes
- Tor Browser security level support
- curl and curl\_over\_tor fetchers
- Cloudflare API connection

### Changed
- Started using pytest
- Increased the modularity of the code
- Changed the way queue was implemented in the database
- Cleaned the code and comments
- Switched to using environment variables instead of config files


## [0.0.7] - 2020-06-02
### Added
- Bumped to python3
- The core fetcher with the requests library
- Typo fixes
- pep8 formatting


## [0.0.6] - 2020-05-25
### Added
- The first version of the Read the Docs documentation
- Typo fixes
- A new example for saving results to an SQLite database

### Changed
- Updated the folder structure of the repository
- Updated the example domain in the readme file


## [0.0.5] - 2020-05-25
### Added
- Contributing file
- Readme file updates


## [0.0.4] - 2020-04-22
### Added
- Logging
- New logo
- try-except blocks to catch errors and report with the new logger


## [0.0.3] - 2020-03-22
### Added
- Fixed typos in the readme.md and added more detailed instructions including the headless mode
- An example that submits results to a InfluxDB
- An explicit error when running the code with Python 3 or newer

### Changed
- Updated error messages
- Moved automation code to examples folder


## [0.0.2] - 2020-03-16
### Added
- Commanline argument support using 
- Examples for using the fetchers
- Comments


## [0.0.1] - 2020-03-08
### Added
- The very first experimental release of the CAPTCHA Monitor
- Two fetchers using Python's httplib and tor-browser-selenium
- The README file and instructions


[0.1.2]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/11/diffs
[0.1.1]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/10/diffs
[0.1.0.1]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/9/diffs
[0.1.0]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/8/diffs
[0.0.7]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/7
[0.0.6]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/6/diffs
[0.0.5]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/5/diffs
[0.0.4]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/3/diffs
[0.0.3]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/2/diffs
[0.0.2]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/1/diffs
[0.0.1]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/commit/60765867e394a4c4aa161031540ef42142b33e59