# Based on Selenium Docker Node
FROM selenium/node-base:latest

USER root

# Install requirements
RUN apt-get update -qqy \
    && apt-get -qqy --no-install-recommends install firefox libavcodec-extra xz-utils jq \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Tor Browser
ARG VERSION=latest
LABEL TOR_BROWSER_VERSION=$VERSION
ENV TOR_BROWSER_VERSION=$VERSION
RUN TOR_BROWSER_DOWNLOAD_URL=$(if [ $TOR_BROWSER_VERSION = "latest" ]; then echo $(curl -s "https://aus1.torproject.org/torbrowser/update_3/release/downloads.json" | jq -r '.downloads.linux64."en-US".binary'); else echo "https://archive.torproject.org/tor-package-archive/torbrowser/${TOR_BROWSER_VERSION}/tor-browser-linux64-${TOR_BROWSER_VERSION}_en-US.tar.xz"; fi) \
    && echo "Using Tor Browser version: "$TOR_BROWSER_VERSION \
    && echo "Downloading Tor Browser from: "$TOR_BROWSER_DOWNLOAD_URL \
    && curl $TOR_BROWSER_DOWNLOAD_URL -o /tmp/torbrowser.tar.xz \
    && echo "Installing Tor Browser" \
    && tar -C /opt -xf /tmp/torbrowser.tar.xz \
    && rm /tmp/torbrowser.tar.xz \
    && chmod -R 755 /opt/tor-browser_en-US \
    && apt-get -y purge firefox jq \
    && ln -fs /opt/tor-browser_en-US/Browser/firefox /usr/bin/firefox \
    && ln -fs /opt/tor-browser_en-US/Browser/firefox.real /usr/bin/firefox.real

# GeckoDriver
ARG GECKODRIVER_VERSION=latest
RUN GK_VERSION=$(if [ ${GECKODRIVER_VERSION:-latest} = "latest" ]; then echo "0.29.0"; else echo $GECKODRIVER_VERSION; fi) \
  && echo "Using GeckoDriver version: "$GK_VERSION \
  && wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v$GK_VERSION/geckodriver-v$GK_VERSION-linux64.tar.gz \
  && rm -rf /opt/geckodriver \
  && tar -C /opt -zxf /tmp/geckodriver.tar.gz \
  && rm /tmp/geckodriver.tar.gz \
  && chmod 755 /opt/geckodriver \
  && ln -fs /opt/geckodriver /usr/bin/geckodriver

USER 1200

COPY generate_config /opt/bin/generate_config

# Generating a default config during build time
RUN /opt/bin/generate_config > /opt/selenium/config.json

# Relaxing permissions for OpenShift and other non-sudo environments
RUN sudo chmod -R 777 ${HOME} \
  && sudo chgrp -R 0 ${HOME} \
  && sudo chmod -R g=u ${HOME}

################################################
# FROM selenium/node-firefox:3.141.59-20210311 #
################################################

USER 1200

# Scripts to run Selenium Standalone
COPY start-selenium-standalone.sh /opt/bin/start-selenium-standalone.sh

# Supervisor configuration file
COPY selenium.conf /etc/supervisor/conf.d/

EXPOSE 4444