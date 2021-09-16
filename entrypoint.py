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
import json
import argparse
import re
import subprocess as sp
import flask
from flask import request, jsonify, make_response


DEBIAN_RELEASES = {
    'stable': "buster",
    'testing': "bullseye",
    'unstable': "sid",
    'oldstable': "stretch",
    'oldoldstable': "jessie"
}


##### RESOLVER ######

class Package():
    def __init__(self, regex_match):
        self.string = regex_match.group(0)
        self.name = regex_match.group(1)
        self.version = regex_match.group(2)
        self.release_version = regex_match.group(3)
        self.release_name = regex_match.group(4)
        self.release = DEBIAN_RELEASES[self.release_name]
        self.architecture = regex_match.group(5)
        self.source = get_source(self.name, self.release_name)
        self.source_version = self.version if self.source != '' else ''

    def to_json(self):
        return {
            'package': self.name,
            'version': self.version,
            'arch': self.architecture,
            'release': self.release,
            'source': self.source,
            'source_version': self.source_version,
            'date': ''
        }

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string

    def __eq__(self, other):
        if not isinstance(other, Package):
            return NotImplemented
        return self.string == other.string

    def __hash__(self):
        return hash(self.string)


def get_source(package, release):
    apt_options = [
        'apt-venv',
        '-c',
        'apt-cache showsrc {}'.format(package),
        release
    ]
    cmd = sp.Popen(apt_options, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = cmd.communicate()
    stdout = stdout.decode("utf-8").split("\n")
    if stdout[0].startswith('Package:'):
        return stdout[0][8:].strip()
    return ''


def get_response(input_string, resolution_status, resolution_result):
    res = {"input": input_string, "status": resolution_status}
    if resolution_status:
        res['packages'] = {}
        for pkg in resolution_result:
            res['packages'][pkg.name] = pkg.to_json()
    else:
        res['error'] = resolution_result
    return res


def get_response_for_api(resolution_status, resolution_result):
    res = {}
    if resolution_status:
        list1 = []
        for package in resolution_result:
            if package:
                list1.append( {
                    "product": package.name,
                    "version": package.version
                })
        res = list1
    else:
        res['error'] = resolution_result
    return res

def run_apt_venv(input_string, release):
    res = set()
    apt_options = [
        'apt-venv',
        '-c',
        'apt -s install {}'.format(input_string),
        release
    ]
    cmd = sp.Popen(apt_options, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = cmd.communicate()
    stdout = stdout.decode("utf-8").split("\n")
    for line in stdout:
        search = re.search(
            r'^Inst ([a-z\-0-9\+\.]*) \(([a-zA-Z0-9\~\+\-\.]*) (.*)/(.*) \[(.*)\]\)',
            line
        )
        if search:
            res.add(Package(search))
    if stdout[-2].startswith("E:"):
        err = stdout[-2]
        return False, err
    return True, res

###### FLASK API ######
app = flask.Flask("api")
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Debian Resolver</h1>
    <p>An API for resolving Debian dependencies.</p>
    <p>API Endpoint: /dependencies/{packageName}/{version}<p>
    <p><b>Note</b>: The {version} path parameter is optional <p>
    '''


@app.errorhandler(404)
def page_not_found(e):
    return '''<h1>404</h1><p>The resource could not be found.</p>
    <p>API Endpoint: /dependencies/{packageName}/{version}<p>''', 404

@app.route('/dependencies/<packageName>', methods=['GET'])
def resolver_api_without_version(packageName):
    
    if not packageName:
        return make_response(
            jsonify({"Error": "You should provide a mandatory {packageName}"}),
            400)
    
    release = 'stable'
    
    status, res = run_apt_venv(packageName, release)

    return jsonify(get_response_for_api(status, res))

@app.route('/dependencies/<packageName>/<version>', methods=['GET'])
def resolver_api_with_version(packageName, version):
    
    if not packageName:
        return make_response(
            jsonify({"Error": "You should provide a mandatory {packageName}"}),
            400)
    
    release = 'stable'
    packageName = packageName + "=" + version
    status, res = run_apt_venv(packageName, release)

    return jsonify(get_response_for_api(status, res))

def deploy(host='0.0.0.0', port=5000):
    app.run(threaded=True, host=host, port=port)

###### CLI ######

def get_parser():
    parser = argparse.ArgumentParser(
        "Resolve dependencies of Debian packages"
    )
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        help=(
            "Input should be a string of a package name or the names of "
            "multiple packages separated by spaces. Examples: "
            "'debianutils' or 'debianutils=4.8.6.1' or 'debianutils zlib1g'"
        )
    )
    parser.add_argument(
        '-o',
        '--output-file',
        type=str,
        help="File to save the output"
    )
    parser.add_argument(
        '-r',
        '--release',
        type=str,
        help="Debian release (default: stable)"
    )
    parser.add_argument(
        '-f',
        '--flask',
        action='store_true',
        help="Deploy flask api"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    input_string = args.input
    output_file = args.output_file
    release = args.release
    cli_args = (input_string, output_file, release)
    flask = args.flask

    # Handle options
    if (flask and any(x for x in cli_args)):
        message = "You cannot use any other argument with --flask option."
        raise parser.error(message)
    if (not flask and not input_string):
        message = "You should always use --input option when you want to run the cli."
        raise parser.error(message)

    if flask:
        deploy()
        return

    release = release if release else "stable"

    status, res = run_apt_venv(input_string, release)
    if output_file:
        with open(output_file, 'w') as outfile:
            json.dump(get_response(input_string, status, res), outfile)
    else:
        print(json.dumps(get_response(input_string, status, res)))


if __name__ == "__main__":
    main()
