FROM debian:stretch

MAINTAINER Quentin COUMES <qcoumes@etud.u-pem.fr>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends\
    sudo\
    gnupg2\
    libasound2\
    libasound2-data\
    locales\
    wget\
    build-essential\
    libssl-dev\
    openssl\
    unzip\
    python3


# Installing pip
RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
RUN python3 /tmp/get-pip.py
RUN pip3 install jinja2 jsonpickle sympy matplotlib

# Adding sftp lib folder to pythonpath
ENV PYTHONPATH /var/lib/upem:$PYTHONPATH


# Installing Java 11
RUN wget --no-cookies --no-check-certificate \
    --header "Cookie: oraclelicense=accept-securebackup-cookie"\
    http://download.oracle.com/otn-pub/java/jdk/11.0.1+13/90cf5d8f270a4347a95050320eef3fb7/jdk-11.0.1_linux-x64_bin.deb
RUN dpkg -i jdk-11.0.1_linux-x64_bin.deb
RUN update-alternatives --install /usr/bin/java java  /usr/lib/jvm/jdk-11.0.1/bin/java 2
RUN update-alternatives --install /usr/bin/javac javac  /usr/lib/jvm/jdk-11.0.1/bin/javac 2
RUN mkdir /utils
RUN wget --no-check-certificate \
    https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.4.0-M1/junit-platform-console-standalone-1.4.0-M1.jar\
    -O- > /utils/junit-platform-console-standalone.jar

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV LC_TYPE en_US.UTF-8
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen "en_US.UTF-8" &&\
    dpkg-reconfigure locales

WORKDIR /home/docker

CMD ["bash"]
