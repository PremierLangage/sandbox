FROM debian:buster

LABEL maintainer="coumes.quentin@gmail.com"

ENV DEBIAN_FRONTEND noninteractive

# Installing base requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    gnupg2 \
    libasound2 \
    libasound2-data \
    locales \
    wget \
    ca-certificates \
    build-essential \
    nasm \
    libssl-dev \
    openssl \
    unzip \
    python3 \
    git \
    ghc \
    clang \
    ocaml-nox \
    ocaml \
    perl \
    perl-doc \
    openjdk-11-jdk \
    python3-distutils \
    python3-dev \
    python2 \
    postgresql \
    libbsd-dev \
    sqlite \
    r-base \
    lua5.3 \
    golang-go \
    scala \
    ghc ghc-prof ghc-doc \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*
    
# Installing rust
RUN wget --quiet --method GET --output-document --ciphers="NORMAL:+VERS-TLS1.3" --https-only -O - https://sh.rustup.rs/  | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set python3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 2

# Installing pip3 and python's requirements
ADD requirements.txt .
RUN wget --progress=dot:giga --no-check-certificate https://bootstrap.pypa.io/pip/3.7/get-pip.py -O /tmp/get-pip.py &&\
    python3 /tmp/get-pip.py &&\
    pip3 --no-cache-dir install wheel &&\
    pip3 --no-cache-dir install -r requirements.txt

# Installing Java 11
RUN update-alternatives --install /usr/bin/java java  /usr/lib/jvm/java-11-openjdk-$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/)/bin/java 2
RUN update-alternatives --install /usr/bin/javac javac  /usr/lib/jvm/java-11-openjdk-$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/)/bin/javac 2
RUN mkdir /utils
RUN mkdir /utils/libs/
ENV PATH="/utils/libs/:${PATH}"
ENV PYTHONPATH="/utils/libs/:${PYTHONPATH}"
RUN export JAVA_HOME=/usr/lib/jvm/jdk-11.0.2/

# Copying libraries script
COPY libraries.py /utils/libraries.py

# Installing nvm, node and npm
ENV NODE_VERSION v20.13.1
ADD package.json .
RUN mkdir -p /usr/local/nvm
ENV NVM_DIR /usr/local/nvm
RUN wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && npm i -D @swc/cli @swc/core \
    && npm i --save-dev -g

ENV PATH="/usr/local/nvm/versions/node/${NODE_VERSION}/bin:${PATH}"

# Installing Java 22 
RUN wget --progress=dot:giga https://download.oracle.com/java/22/latest/jdk-22_linux-$(arch | sed s/x86_64/x64/)_bin.tar.gz -O /tmp/jdk-22_linux_bin.targz &&\
    mkdir jdk-22-oracle &&\
    tar -xzvf /tmp/jdk-22_linux_bin.targz -C jdk-22-oracle --strip-components=1 &&\
    cp -r jdk-22-oracle /usr/lib/jvm/ &&\
    rm /tmp/jdk-22_linux_bin.targz
RUN update-alternatives --install /usr/bin/java java  /usr/lib/jvm/jdk-22-oracle/bin/java 3
RUN update-alternatives --install /usr/bin/javac javac  /usr/lib/jvm/jdk-22-oracle/bin/javac 3

# Download Junit standalone jar
RUN wget --progress=dot:giga https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.3/junit-platform-console-standalone-1.10.3.jar -O /utils/junit-platform-console-standalone.jar

# Cleaning /tmp
RUN rm -Rf /tmp/*

RUN yes | cpan -l > /dev/null 2>&1

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV LC_TYPE en_US.UTF-8
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN echo "fr_FR.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen "en_US.UTF-8" && locale-gen "fr_FR.UTF-8" && dpkg-reconfigure locales

WORKDIR /home/student
RUN chmod -R a+rwx /home/student

CMD ["bash"]
