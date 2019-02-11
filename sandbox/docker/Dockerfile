FROM debian:stretch

MAINTAINER Quentin COUMES <qcoumes@etud.u-pem.fr>

ENV DEBIAN_FRONTEND noninteractive


# Installing base requirements
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    sudo \
    gnupg2 \
    libasound2 \
    libasound2-data \
    locales \
    wget \
    ca-certificates \
    build-essential \
    libssl-dev \
    openssl \
    unzip \
    python3 \
    git \
    ocaml-nox \
    ocaml \
    perl \
    perl-doc


# Installing pip3 and python's requirements
RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
RUN python3 /tmp/get-pip.py
RUN pip3 install wheel
RUN pip3 install \
    jinja2 \
    jsonpickle \
    sympy \
    matplotlib \
    psycopg2


# Installing Java 11
RUN wget \
    -P /tmp \
    --header "Cookie: oraclelicense=accept-securebackup-cookie"\
    https://download.oracle.com/otn-pub/java/jdk/11.0.2+7/f51449fcd52f4d52b93a989c5c56ed3c/jdk-11.0.2_linux-x64_bin.deb
RUN dpkg -i /tmp/jdk-11.0.2_linux-x64_bin.deb
RUN update-alternatives --install /usr/bin/java java  /usr/lib/jvm/jdk-11.0.2/bin/java 2
RUN update-alternatives --install /usr/bin/javac javac  /usr/lib/jvm/jdk-11.0.2/bin/javac 2
RUN mkdir /utils
RUN wget \
    https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.4.0-M1/junit-platform-console-standalone-1.4.0-M1.jar \
    -O- > /utils/junit-platform-console-standalone.jar
RUN export JAVA_HOME=/usr/lib/jvm/jdk-11.0.2/


# Installing PL-Java
RUN wget https://github.com/forax/first-language/releases/download/1.0.2/pl-java-jdk-11.tar.gz -P /tmp
RUN tar -xvzf /tmp/pl-java-jdk-11.tar.gz -C /utils/
RUN ln -s /utils/pl-java/bin/pl-java /usr/bin/pl-java
RUN ln -s /utils/pl-java/bin/pl-javac /usr/bin/pl-javac


# Cleaning /tmp
RUN rm -Rf /tmp/*



ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV LC_TYPE en_US.UTF-8
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen "en_US.UTF-8" && dpkg-reconfigure locales

WORKDIR /home/docker

CMD ["bash"]
