FROM debian:stretch

MAINTAINER Quentin COUMES <qcoumes@etud.u-pem.fr>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends sudo locales wget build-essential libssl-dev openssl unzip python3

RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
RUN python3 /tmp/get-pip.py
RUN pip3 install jinja2 jsonpickle sympy matplotlib

# Adding sftp lib folder to pythonpath
ENV PYTHONPATH /var/lib/upem:$PYTHONPATH

ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8 
ENV LC_TYPE en_US.UTF-8
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen "en_US.UTF-8" &&\
    dpkg-reconfigure locales

WORKDIR /home/docker

CMD ["bash"]
