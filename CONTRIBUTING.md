# Contributing

_First off, thanks for spending your time to contribute!_

This project was born from getting frustrated with CAPTCHAs while using the [Tor Browser](https://www.torproject.org/) and the ticket [#33010](https://trac.torproject.org/projects/tor/ticket/33010) on Tor's trac ticketing system. I created something quickly to get started with data collection based on the comments on the ticket [#33010](https://trac.torproject.org/projects/tor/ticket/33010). There is a huge room for contributions for various improvements and bug fixes.

## Ways to contribute
- Reporting bugs
- Pull requests
- Documentation
- Suggesting enhancements
- Developing new features for the new version of the CAPTCHA Monitor (see the details below)

## How does this thing work?
There are two main "webpage fetchers" `cloudflared_httplib.py` and `cloudflared_tor.py` that fetch website through the Tor Browser and the Python's httplib. These two programs check if there is a CAPTCHA in the fetched webpages. The programs in the example folder utilize these two "webpage fetchers" to fetch a given list of webpages and process the data in different forms like saving to a CSV file or uploading to a remote database.

## Developing new features
I can't say that the current system is modular or expandable. So, we should make some fundamental changes, and I think you can contribute to these changes if you are looking for different ways to contribute.

### Planned changes
Here is some of the planned changes are listed, please feel free to utilize the issues to report any comments and additions to these:
- We should make the project more modular by separating the webpage fetching, CAPTCHA detection, and result processing stages
- The whole system should work in a more pipelined fashion that the user only gives the list of parameters & the webpages and system does the rest. That being said, the modules within the should be expandable or integrate into other projects if the users want to go beyond the basic functionality.
- We should diversify the fetching methods by adding new browsers and options for changing the user-agent, HTTP headers, disabling cookies & JavaScript, etc
- We should add the ability to choose a specific Tor exit node
- An API is definitely needed to query the data collected and for interfacing other software like the [CollecTor](https://metrics.torproject.org/collector.html) for [Tor Metrics](https://metrics.torproject.org/)
