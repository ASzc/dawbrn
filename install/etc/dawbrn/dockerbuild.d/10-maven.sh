#!/bin/bash

set -eEu

source_clone="${1:?Specify source clone directory path}"

docker run \
    --rm \
    -v "$source_clone:/tmp/build:z" \
    -v "/etc/dawbrn/maven-cache:/opt/apache-maven/conf/settings:Z" \
    --workdir /tmp/build \
    aszczucz/maven-centos:jdk8_mvn3.3.9
