FROM pretix/standalone

USER root

ADD . /pretix/mrmcd

WORKDIR /pretix/mrmcd
RUN python3 setup.py develop

WORKDIR /pretix/src
USER pretixuser
