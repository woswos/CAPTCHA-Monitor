# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0.1] - 2020-06-23
### Added
- Implemented #12 #15
- `-v` option to print all logs for debugging purposes
- `-c` option to clean existing cache files for Tor

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

[0.1.0.1]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/9/diffs
[0.1.0]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/8/diffs
[0.0.7]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/7
[0.0.6]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/6/diffs
[0.0.5]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/5/diffs
[0.0.4]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/3/diffs
[0.0.3]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/2/diffs
[0.0.2]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/merge_requests/1/diffs
[0.0.1]: https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/commit/60765867e394a4c4aa161031540ef42142b33e59