[![Python package](https://github.com/PremierLangage/sandbox/workflows/Python%20package/badge.svg)](https://github.com/PremierLangage/sandbox/actions/)
[![codecov](https://codecov.io/gh/PremierLangage/sandbox/branch/master/graph/badge.svg)](https://codecov.io/gh/PremierLangage/sandbox)
[![CodeFactor](https://www.codefactor.io/repository/github/PremierLangage/sandbox/badge)](https://www.codefactor.io/repository/github/PremierLangage/sandbox)
[![Documentation](https://img.shields.io/badge/docs-passing-brightgreen.svg)](https://documenter.getpostman.com/view/7955851/S1a915EG?version=latest)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](#)
[![License MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/qcoumes/sandbox/blob/master/LICENSE)
 
# Installation

## Requirements:

- [`3.8 <= python <= 3.9.10`](https://www.python.org/)
- [`pip3`](https://pip.pypa.io/en/stable/installing/)
- [`docker`](https://docs.docker.com/engine/installation/linux/docker-ce/debian/)

To deploy the sandbox, you also need [`apache2`](https://httpd.apache.org/).

## Installation

Installing the server is pretty straightforward, you just need to clone the repository and run
the install script :

```bash
git clone https://github.com/PremierLangage/sandbox.git
cd sanbox
./bin/install.sh  
```

The sandbox can now be run : `python3 manage.py runserver [port]`.

## Deploying

If you also want to deploy the server, run `./bin/deploy.sh`. You may want to check
the created config file at `/etc/apache2/sites-enabled/sandbox-auto.conf`.

You will then have to restart apache2 : `systemctl restart apache2` or `service apache2 restart`.

# Endpoints

## **POST** `/execute/`

Execute commands on the sandbox with the given environment, or an environment already present on the sandbox.

### Request

Body must be encoded in `form_data` and must contains a json containing informations about the execution:

```json
{
    "commands":[
        "<bash command 1>",
        { 
            "command": " -<bash command 2>",
             "timeout": 2
        },
        { 
            "command": "-<bash command 3>",
             "timeout": 5
        },
    ],
    "environ": {
            "var1": "value1",
            "var2": "value2"
    },
    "result_path":"file.json",
    "environment": "<UUID4>",
    "save": "<bool>",
}
```

**Mandatory fields** :
* `commands` - A list of bash command to be executed. A failing command (exit code different than **0**) will stop the sandbox, except if the command start with an hyphen `-`. Each command can also specify a timeout in seconds, like in the example.

**Optionnal fields** :
* `result_path` - Path to the file from which the `result` field of the response will be extracted. if `result_path` is absent from the request, `result` will not be present in the response.
* `environ` - A list of environments variables  as al ist of objects containing the var name and its value.
* `environment` - Use this environment stored in the sandbox as a base environment. File present in the body's tgz will be added to this environment (file with the same name are overwritten).
* `save` - Boolean indicating if the resulting environment should be saved. If `true`, the environment's *UUID* will be sent in the response in the field `environment`. It'll be kept on the sandbox for a time define in the sandbox's settings. That expiration date will be sent in the response  in the `expire` field (ISO 8601 format). If the field `save` is missing, it is assumed to be `false`.

The body can also contain an *Optionnal* tar archive compressed with gzip (`.tgz` or `.tar.gz`) of your environment of execution.
If field `environment` is present in the *JSON*, the file present in the body's environment will be added to the one in the sandbox, overwritting file with the same name.


### Response

The response is a `json` such as :

```json
{
  "status": 0,
  "execution": [
    {
      "command": "echo $((1+1)) > result.txt",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "time": 0.002222299575805664
    }
  ],
  "total_time": 0.004444599151611328,
  "result": "2",
  "environment": "e8c5995b-7049-4b04-8440-5d9d914360fc",
  "expire": "20190705T130535Z"
}
```

The `status` fields in the reponse indicate whether the execution succeeded or failed :

* `0` - The execution was successful, or the last command's failure was ignored (through the used of `-`).
* `> 0` - The last command exited failed, `status` will be set to this command's exit code.
* `< 0` - An error occurred on the sandbox :
	* `-1` - Unknown error.
	* `-2` - Execution timed out.
	* `-3` - Result file could not be found at the indicated path.
	* `-4` - Result file is not encoded in UTF-8.

`execution` contains the details of each executed commands.

The response's `total_time` is the total time taken by the whole execute request, it thus can be higher than the sum of each command's `time`.

for `environment`, `expire` and `result`, see the `result_path` and `save` keys of the request's config json.

## **GET** `/environments/:uuid4/`

Retrieve the environment (as a `.tgz`) corresponding to the uuid4.

## **GET** `/files/:uuid4/:path/`

Used to retrieve a file in a specific environment. Response's `Content-Type` will always be `application/octet-stream`.

## **GET** `/specifications/`

Retrieves informations about the sandbox, like the specifications of the containers, and the number of running containers.

Field `container` -> `memory` -> `storage` can be equal to `-1` if no limit was set.

CPU frenquencies are in MHz.

Memory values are in bytes.

## **GET** `/libraries/`

Returns the librairies installed in the containers.

## **GET** `/usages/`

Return current usage of the sandbox.

CPU frenquencies are in MHz.

Memory and I/O values are in bytes.
