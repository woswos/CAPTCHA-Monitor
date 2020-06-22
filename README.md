<!-- Unfortunately GitHub markdown doesn't suppor resizing and centering svg images-->
<div align="center"><p align="center"><img src="logo.svg" alt="CAPTCHA Monitor Logo" width="50%"></p></div>

Check if a website returns a Cloudflare CAPTCHA using the Tor Browser and other 
mainstream web browsers/tools. By default, this tool searches for *"Cloudflare"* 
text within the fetched page, but it is possible to customize the CAPTCHA sign, 
which this tool searches for.

## Installation Steps
* Clone this repository to your machine
* Change the working directory into the cloned repository and install the CAPTCHA 
Monitor via `$ pip install -e .`
* Install Tor via `$ apt install tor`
* Download the latest version of Tor Browser Bundle from 
[torproject.org](https://www.torproject.org/download/) website and extract the 
archive file
* Install Firefox via `$ apt install firefox`
* Install the `geckodriver` from the 
[geckodriver releases](https://github.com/mozilla/geckodriver/releases/) page, 
v0.23.0 version or newer. [Here](https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu) 
is a simple installation tutorial if you need one.
* Install Chromium via `$ apt install chromium-browser`
* Install the `ChromeDriver` from 
[chromium.org](https://chromedriver.chromium.org/downloads) website. Choose the 
one that matches the Chromium version you installed in the previous step.

### Installation Notes
* Depending on your computer setup, CAPTCHA Monitor might have trouble 
installing `PyCURL`. It possibly means that `curl` and/or its dev dependencies are 
not installed on your system. You might install them with 
`$ apt install libcurl4-openssl-dev libssl-dev` and try running `$ pip install -e .`
again.

## Configuring the CAPTCHA Monitor
You need to set some environment variables to use CAPTCHA Monitor. These 
environment variables are `CM_TBB_PATH` and `CM_DB_FILE_PATH`. 
`CM_TBB_PATH` is the path to the Tor Browser Bundle and `CM_DB_FILE_PATH` is the
path to the database file. You don't need to have a file at the location 
`CM_DB_FILE_PATH`, it will be created for you. Please use absolute paths for 
both. 

Here is are samples for the environment variables:
* `CM_TBB_PATH="/home/woswos/tor-browser_en-US"`
* `CM_DB_FILE_PATH="/home/woswos/captcha_monitor.sqlite"`

## Usage
CAPTCHA Monitor is designed to have a job queue and worker(s) that process the 
jobs in the queue. You can run the "worker" with `captchamonitor run` command. 
By default, it will process a single job from the queue and quit. 

If you want to make it run continously with multiple workers, you need to use 
`captchamonitor run -l -w [number of workers]` command. CAPTCHA Monitor will
start specified number of workers in parallel.

You can add new jobs to the queue with `captchamonitor add <details of the job>`
command. The added job will be processed once the worker runs on the system. 
The results will be available in the database you specified in the `CM_DB_FILE_PATH`
environment variable.

In order to specify the details of the job, you can use the following arguments:
- `-u` to specify the website URL
- `-m` to specify the method (see the methods section below)
- `-s` to specify the Tor Browser's security level (if using tor_browser)
- `-c` to specify a captcha sign other than *"Cloudflare"*
- `-a` to specify additional request headers in JSON format (the ones colliding will be overwritten with the ones you provided)
- `-e` to specify the Tor exit node IPv4 address (if fetching over Tor)
- `-x` using this flag will add the job you specified with all Tor exit nodes (if fetching over Tor)

### Methods
Currently, you can fetch a URL using 
Tor Browser (`tor_browser`), 
Chromium (`chromium`), 
Firefox (`firefox`), 
Python requests library (`requests`), 
Chromium over Tor (`chromium_over_tor`), 
Firefox (`firefox_over_tor`), and 
Python requests library over Tor (`requests_over_tor`).

## Examples
Let's say I want to check if I get a Cloudflare CAPTCHA when I browse 
`https://example.com` with Tor Browser. In that case, I need to add a new 
job with `captchamonitor add -u https://example.com -m tor_browser -c Cloudflare` 
and I need to run the worker afterward with `captchamonitor run`. 

What if I want to see if I get a CAPTCHA when exiting through a specific Tor 
exit Node? Then, I just need to add another job using 
`captchamonitor add -u https://example.com -m tor_browser -c Cloudflare -e [exit.node.IP.address]` 
and run the worker.

Finally, I want to compare these results with a case where I use Firefox without 
Tor. Then, I need to add another job using 
`captchamonitor add -u https://example.com -m firefox -c Cloudflare` and run 
the worker.

I could also leave the worker running in the background, and it would process 
jobs once they were added. The worker and the boss work asynchronously.

## Contributing
Please feel free to report and fix the issues you encounter while using this tool. 
Please check the [contributing file](CONTRIBUTING.md) to see how you can contribute.
