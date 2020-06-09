FROM python:3-alpine

ENV TOR_VERSION=10.0a1
ENV GECKO_VERSION=v0.26.0
ENV CHROMEDRIVER_VERSION=84.0.4147.30

ENV TB_RELEASE_FILE=tor-browser-linux64-${TOR_VERSION}_en-US.tar.xz
ENV TB_RELEASE_URL=https://dist.torproject.org/torbrowser/${TOR_VERSION}/${TB_RELEASE_FILE}

ENV GECKO_RELEASE_FILE=geckodriver-${GECKO_VERSION}-linux64.tar.gz
ENV GECKO_RELEASE_URL=https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/${GECKO_RELEASE_FILE}

ENV CHROMEDRIVER_RELEASE_FILE=chromedriver_linux64.zip
ENV CHROMEDRIVER_RELEASE_URL=https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/${CHROMEDRIVER_RELEASE_FILE}

ENV CM_TBB_PATH="/usr/local/bin/tor-browser_en-US"
ENV CM_TOR_HOST="127.0.0.1"
ENV CM_TOR_PORT="9090"
ENV CM_DB_FILE_PATH="/db/captchamonitor.db"

ENV PYCURL_SSL_LIBRARY=openssl

WORKDIR /usr/local/bin

# For geckodriver setup details, see https://stackoverflow.com/a/58771365/10216991
# For pycurl setup details, see https://stackoverflow.com/a/50974082/10216991
RUN apk add --no-cache libcurl tor firefox-esr chromium unzip git && \
    echo "SocksPort 0.0.0.0:9050" >> /etc/tor/torrc && \
    wget ${TB_RELEASE_URL} && \
    tar -xJf ${TB_RELEASE_FILE} && \
    rm -v ${TB_RELEASE_FILE}* && \
    wget ${GECKO_RELEASE_URL} && \
    tar -xzf ${GECKO_RELEASE_FILE} -C /usr/bin && \
    rm -v ${GECKO_RELEASE_FILE}* && \
    wget ${CHROMEDRIVER_RELEASE_URL} && \
    unzip ${CHROMEDRIVER_RELEASE_FILE} -d /usr/bin && \
    rm -v ${CHROMEDRIVER_RELEASE_FILE}* && \
    apk add --no-cache --virtual .build-dependencies build-base curl-dev && \
    pip install pycurl && \
    git clone https://github.com/woswos/CAPTCHA-Monitor && \
    cd CAPTCHA-Monitor && \
    git checkout dev && \
    pip install -e . && \
    apk del .build-dependencies

CMD ["captchamonitor","run","-l"]
