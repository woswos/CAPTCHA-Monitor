# Cloudflare-CAPTCHA-Monitoring
Check if a web site returns a Cloudflare CAPTCHA using both the Tor Browser and Python's httplib. By default, this tool searches for *"Attention Required! | Cloudflare"* text within the fetched page, but it is possible to customize the CAPTCHA sign.

## Installation Steps
1. Clone this repository
1. Download the latest version of Tor browser from [torproject.org](https://www.torproject.org/download/) website and extract the archive file
1. Install the ```geckodriver``` from the [geckodriver releases page](https://github.com/mozilla/geckodriver/releases/) (v0.23.0 version or newer)
1. Install Tor via ```$ apt install tor```
1. Install Tor Browser with Selenium via ```pip install tbselenium```
1. Install Tor stem via ```$ apt install python-stem```


## Usage
```cloudflared_tor.py``` and ```cloudflared_httplib.py``` can be run directly from the command line. A website URL and the Tor browser bundle location needs to be specified. 

Use the following arguments
- ```-u``` to specify the website URL, 
- ```-c``` to specify a captcha sign other than *"Attention Required! | Cloudflare"*, 
- ```-t``` to specify to path to Tor browser bundle 
- ```--help``` to get further details.

Example usage for checking if a website returns Cloudflare CAPTCHA when fetched via Tor browser:
```
python cloudflared_tor.py -u http://google.com -t '/path/to/Tor/Browser/Bundle'
```

Example usage for checking if a website returns Cloudflare CAPTCHA when fetched via Python's httplib:
```
python cloudflared_httplib.py -u http://google.com
```

The script will return a result like below in the following format [method]:[tested URL]:[result]
```
httplib:http://google.com:0
```
If the result field is ```0``` then the tested URL didn't return a CAPTCHA. If the result field is ```1``` then the tested URL did return a CAPTCHA.

Alternatively, you can run ```automated_fetcher.py``` program to fetch a list of website URLs via both the Tor browser & httplib and record the results in a CSV file. Please look at the code for further details.
