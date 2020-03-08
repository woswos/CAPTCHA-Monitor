#!/usr/bin/env python

import subprocess
import time

tbb_dir = "/home/woswos/tor-browser_en-US/"

def main():

    while True:

        domain = "captcha.wtf"
        port = 80

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)


        domain = "bypass.captcha.wtf"
        port = 80

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)


        domain = "exit11.online"
        port = 80

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)



        domain = "captcha.wtf"
        port = 443

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)


        domain = "bypass.captcha.wtf"
        port = 443

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)


        domain = "exit11.online"
        port = 443

        tor_result = tor(domain, port, tbb_dir)
        http_result = http(domain, port)

        print(str(int(time.time()))+":"+ tor_result)
        print(str(int(time.time()))+":"+ http_result)

        time.sleep(30)


def tor(domain, port, tbb_dir):
    proc = subprocess.Popen(['python', 'cloudflared_tor.py', '-d', domain, '-p',
                            str(port), '-t', tbb_dir],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    out = proc.stdout.read()

    return out[0:-1].decode()


def http(domain, port):
    proc = subprocess.Popen(['python', 'cloudflared_http.py', '-d', domain, '-p',
                            str(port)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    out = proc.stdout.read()

    return out[0:-1].decode()


if __name__ == '__main__':
    main()
