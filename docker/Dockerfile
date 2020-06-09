FROM ubuntu:18.04

ENV TOR_VERSION=10.0a1
ENV GECKO_VERSION=v0.26.0
ENV CHROMEDRIVER_VERSION=83.0.4103.39

ENV TB_RELEASE_FILE=tor-browser-linux64-${TOR_VERSION}_en-US.tar.xz
ENV TB_RELEASE_URL=https://dist.torproject.org/torbrowser/${TOR_VERSION}/${TB_RELEASE_FILE}

ENV GECKO_RELEASE_FILE=geckodriver-${GECKO_VERSION}-linux64.tar.gz
ENV GECKO_RELEASE_URL=https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/${GECKO_RELEASE_FILE}

ENV CHROMEDRIVER_RELEASE_FILE=chromedriver_linux64.zip
ENV CHROMEDRIVER_RELEASE_URL=https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/${CHROMEDRIVER_RELEASE_FILE}

ENV CM_TBB_PATH="/root/tor-browser_en-US"
ENV CM_TOR_HOST="127.0.0.1"
ENV CM_TOR_PORT="9050"
ENV CM_DB_FILE_PATH="/root/db/captcha-monitor.db"

ENV CHROME_BIN=/usr/local/bin/chromium-browser
ENV CHROME_PATH=/usr/local/lib/chromium/

# Install dependencies
RUN apt-get update \
    && apt-get install -y python3-pip python3-dev git libcurl4-openssl-dev libssl-dev tor unzip wget firefox chromium-browser=83.0.4103.61-0ubuntu0.18.04.1 \
    && cd /usr/local/bin \
    && ln -s /usr/bin/python3 python

WORKDIR /root/

# Install captchamonitor, geckodriver, and chromedriver
RUN wget ${TB_RELEASE_URL} \
    && tar -xJf ${TB_RELEASE_FILE} \
    && rm -v ${TB_RELEASE_FILE}* \
    && wget ${GECKO_RELEASE_URL} \
    && tar -xzf ${GECKO_RELEASE_FILE} -C /usr/bin \
    && rm -v ${GECKO_RELEASE_FILE}* \
    && wget ${CHROMEDRIVER_RELEASE_URL} \
    && unzip ${CHROMEDRIVER_RELEASE_FILE} -d /usr/bin \
    && rm -v ${CHROMEDRIVER_RELEASE_FILE}* \
    && git clone https://github.com/woswos/CAPTCHA-Monitor \
    && cd /root/CAPTCHA-Monitor \
    && git checkout dev \
    && pip3 install -e .

# Remove unused packages
RUN apt-get purge -y wget unzip \
    && apt-get autoremove \
    && apt-get clean

WORKDIR /root/CAPTCHA-Monitor

# Uncomment for running the tests
#RUN pip3 install pytest
#CMD ["pytest", "-v", "-l", "-x"]

CMD ["captchamonitor","run"]
