# Download base image Ubuntu 20.04
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true

ENV TOR_VERSION=10.0a1
ENV GECKO_VERSION=v0.26.0
ENV CHROMEDRIVER_VERSION=84.0.4147.30

ENV GECKO_RELEASE_FILE=geckodriver-${GECKO_VERSION}-linux64.tar.gz
ENV GECKO_RELEASE_URL=https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/${GECKO_RELEASE_FILE}
ENV CHROMEDRIVER_RELEASE_FILE=chromedriver_linux64.zip
ENV CHROMEDRIVER_RELEASE_URL=https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/${CHROMEDRIVER_RELEASE_FILE}

# Update software repository
RUN apt update

# Install dependencies
RUN apt install -y python3-pip python3-dev git gnupg libcurl4-openssl-dev libssl-dev tor unzip wget xvfb apt-transport-https curl xdotool && \
    # Add Chromium PPA and Brave PPA
    apt-key adv --fetch-keys "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xea6e302dc78cc4b087cfc3570ebea9b02842f111" && \
    echo 'deb http://ppa.launchpad.net/chromium-team/beta/ubuntu bionic main ' >> /etc/apt/sources.list.d/chromium-team-beta.list && \
    curl -s https://brave-browser-apt-release.s3.brave.com/brave-core.asc | apt-key --keyring /etc/apt/trusted.gpg.d/brave-browser-release.gpg add - && \
    echo 'deb [arch=amd64] https://brave-browser-apt-release.s3.brave.com/ stable main ' >> /etc/apt/sources.list.d/brave-browser-release.list && \
    apt update

# Install Firefox and Chromium
# Here Firefox is installed to install the Firefox dependencies but the installed
#   Firefox is not used in the experiments
RUN apt install -y firefox chromium-browser brave-browser --no-install-recommends && \
    # Install captchamonitor, geckodriver, chromedriver
    wget ${GECKO_RELEASE_URL} && \
    tar -xzf ${GECKO_RELEASE_FILE} -C /usr/local/bin && \
    rm -v ${GECKO_RELEASE_FILE}* && \
    wget ${CHROMEDRIVER_RELEASE_URL} && \
    unzip ${CHROMEDRIVER_RELEASE_FILE} -d /usr/local/bin && \
    rm -v ${CHROMEDRIVER_RELEASE_FILE}* 

# Create the nonroot user
RUN useradd -m cm && \
    chown -R cm /home/cm

# Switch to captchamonitor user home directory
WORKDIR /home/cm

# Copy CAPTCHA Monitor
ADD / /home/cm/CAPTCHA-Monitor

# Change the owner of the code
RUN chown -R cm /home/cm/CAPTCHA-Monitor

# Clean the unused packages
RUN apt remove -y git wget && \
    apt autoremove -y && \
    apt clean -y && \
    rm -rf /var/lib/apt/lists/*

# Switch to captchamonitor user
USER cm

# Update path for using CAPTCHA Monitor
ENV PATH "$PATH:/home/cm/.local/bin"

# Install CAPTCHA Monitor
RUN cd CAPTCHA-Monitor && \
    pip3 install -e .
