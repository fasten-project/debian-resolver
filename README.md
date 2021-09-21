debian-resolver
===============

This tool resolves Debian dependencies by using `apt-venv`.
It can be executed as a CLI tool, or it can be deployed as a Flask API.
It accepts as input any string that can be resolved by apt.

Command Line Arguments
----------------------
__You should always use at least one of -f or -i__

```
usage: Resolve dependencies of Debian packages [-h] [-i INPUT] [-o OUTPUT_FILE] [-r RELEASE]
                                               [-f]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input should be a string of a package name or the names of multiple
                        packages separated by spaces. Examples: 'debianutils' or
                        'debianutils=4.8.6.1' or 'debianutils zlib1g'
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        File to save the output
  -r RELEASE, --release RELEASE
                        Debian release (default: stable)
  -f, --flask           Deploy flask api
```

Output Format
-------------

The tool returns a JSON object.
If it managed to resolve the package successfully,
then it returns a JSON in the following format.
Note that in `packages` key, there is also the package that was given as input.

```json
{
    "input": "debianutils",
    "status": true,
    "packages": {
        "libc6": {
              "package": "libc6",
              "version": "2.28-10",
              "arch": "amd64",
              "release": "buster",
              "source": "glibc",
              "source_version": "2.28-10",
              "date": ""
            },
        "debianutils": {
              "package": "debianutils",
              "version": "4.8.6.1",
              "arch": "amd64",
              "release": "buster",
              "source": "debianutils",
              "source_version": "4.8.6.1",
              "date": ""
        }
    }
}
```

Otherwise, it produces a JSON with an error message.

```json
{
    "input": "buz",
    "status": false,
    "error": "E: Unable to locate package buz"
}
```

## Micro-service

Deploy a micro-service that exposes a REST API for resolving Debian dependencies.

```bash
docker build -f Dockerfile -t debian-resolver-api .
docker run -p 5001:5000 debian-resolver-api
```

* Request format

```
url: http://localhost:5001/dependencies/{packageName}/{version}
```
<b>Note:</b> The {version} path parameter is optional

* Example request using curl:

```bash
curl "http://localhost:5001/dependencies/debianutils/4.11.2"
```

* Output format:

 ```json
  {
    "product": "debianutils",
    "version": "4.11.2"
  },
  {
    "product": "libcap-ng0",
    "version": "0.7.9-2.2+b1"
  },
  {
    "product": "libgnutls30",
    "version": "3.7.1-5"
  },
  {
    "product": "libtext-wrapi18n-perl",
    "version": "0.06-9"
  },
  {
    "product": "debconf",
    "version": "1.5.77"
  },
   ...
]
```
