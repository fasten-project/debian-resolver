# vim:set ft=dockerfile:
# Copyright (c) 2018-2020 FASTEN.
#
# This file is part of FASTEN
# (see https://www.fasten-project.eu/).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
FROM debian:buster

# INSTALL git, python3, python, wget, pip3
RUN apt -yqq update && apt -yqq upgrade && apt install -yqq git python3 python wget python3-pip

# Pip and pyxdg are required for installing apt-venv
RUN wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
RUN python get-pip.py
RUN pip install pyxdg

RUN git clone https://github.com/LeoIannacone/apt-venv.git
RUN cd apt-venv && python setup.py install

RUN mkdir -p /api
COPY requirements.txt /api/requirements.txt
COPY ./entrypoint.py api/entrypoint.py

RUN pip3 install -r api/requirements.txt

WORKDIR /api

# Setup environments
RUN apt-venv stable -c "apt update -yqq && apt upgrade -yqq"
ENTRYPOINT ["python3", "entrypoint.py", "-f"]
