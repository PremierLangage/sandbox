# utils.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


import io
import logging
import os
import subprocess
import tarfile
import time
import uuid
from typing import BinaryIO, Optional, Tuple

import humanfriendly
import psutil
from django.conf import settings
from django.http import HttpRequest
from django_http_exceptions import HTTPExceptions

from sandbox.containers import Sandbox


logger = logging.getLogger(__name__)


def merge_tar_gz(a: Optional[BinaryIO], b: Optional[BinaryIO]) -> Optional[BinaryIO]:
    """Merge <a> and <b>, returning a new tarfile.TarFile object.

    If two files in <a> and <b> have the same name, the one in <a> prevails.
    
    Both a and b can be safely closed after this function.
    
    Returns
        None       - If both arguments are None.
        a          - If <b> is None.
        b          - If <a> is None.
        io.BytesIO - A BytesIO, cursor set at the start, corresponding to the
                     merging of <a> into <b> (overwriting file with the same
                     name)."""
    if a is None:
        return None if b is None else io.BytesIO(b.read())
    if b is None:
        return io.BytesIO(a.read())
    
    destio = io.BytesIO()
    
    with tarfile.open(fileobj=a, mode="r:gz") as t1, \
            tarfile.open(fileobj=b, mode="r:gz") as t2, \
            tarfile.open(fileobj=destio, mode="w:gz") as dest:
        
        t1_members = [m for m in t1.getmembers()]
        t1_names = t1.getnames()
        t2_members = [m for m in t2.getmembers() if m.name not in t1_names]
        
        for member in t1_members:
            if member.isdir():
                dest.addfile(member)
            else:
                dest.addfile(member, t1.extractfile(member))
        
        for member in t2_members:
            if member.isdir():
                dest.addfile(member)
            else:
                dest.addfile(member, t2.extractfile(member))
    
    destio.seek(0)
    return destio


def get_asset(path: str) -> Optional[str]:
    """Returns the path of the assets <path>, None if it does not exists."""
    path = os.path.join(settings.ASSETS_ROOT, os.path.join(path, 'data/content.tgz'))
    return path if os.path.isfile(path) else None

def get_env(env: str) -> Optional[str]:
    """Returns the path of the environment <env>, None if it does not exists."""
    path = os.path.join(settings.ENVIRONMENT_ROOT, f"{env}.tgz")
    return path if os.path.isfile(path) else None


def extract(env: str, path: str) -> Optional[BinaryIO]:
    """Extract and returns the file at <path> inside <env>, returns None of either the environment
    or the file could not be found."""
    env_path = get_env(env)
    if env_path is None:
        raise HTTPExceptions.NOT_FOUND.with_content(f"No environment with UUID '{env}' found")
    
    try:
        with tarfile.open(env_path, mode="r:gz") as tar:
            buffer = tar.extractfile(tar.getmember(path))
            file = io.BytesIO(buffer.read())
    except KeyError:
        raise HTTPExceptions.NOT_FOUND.with_content(
            f"The file '{path}' could not be found in environment '{env}'"
        )
    
    return file


def execute_asset(request: HttpRequest, config: dict) -> str:

    body_env = request.FILES.get("environment")

    asset_path = config.get("path")
    if asset_path is None:
        raise HTTPExceptions.BAD_REQUEST.with_content("Missing argument 'path'")
    
    if not isinstance(asset_path, str):
        raise HTTPExceptions.BAD_REQUEST.with_content(
            f'result_path must be a string, not {type(asset_path)}')
    
    asset_env = get_asset(asset_path)
    if not asset_env:
        raise HTTPExceptions.NOT_FOUND.with_content(
                f"No asset on '{asset_path}' found"
            )

    asset_env = open(asset_env, "rb")

    env = merge_tar_gz(body_env, asset_env)

    if body_env is not None:
        body_env.close()
    if asset_env is not None:
        asset_env.close()

    path = os.path.join(settings.ASSETS_ROOT, os.path.join(asset_path, 'tmp/result.tgz'))
    if env is not None:
        with open(path, "w+b") as f:
            f.write(env.read())
    else:
        tarfile.open(path, "x:gz").close()
    
    return path

def executed_env(request: HttpRequest, config: dict) -> str:
    """Returns the UUID4 corresponding to the environment that will be used in the execution.
    
    If an environment is provided both in the body and the config, this function will do the merge
    through 'merge_tar_gz()'.
    
    raises:
        - django_http_exceptions.HTTPExceptions.NOT_FOUND if the environment asked in request's
          config cannot be found.
    """
    body_env = request.FILES.get("environment")
    
    sandbox_env = None
    sandbox_env_uuid = config.get("environment")
    if sandbox_env_uuid is not None:
        sandbox_env = get_env(sandbox_env_uuid)
        if not sandbox_env:
            raise HTTPExceptions.NOT_FOUND.with_content(
                f"No environment with UUID '{sandbox_env_uuid}' found"
            )
        sandbox_env = open(sandbox_env, "rb")
    
    env = merge_tar_gz(body_env, sandbox_env)
    
    if body_env is not None:
        body_env.close()
    if sandbox_env is not None:
        sandbox_env.close()
    
    uuid_env = str(uuid.uuid4())
    path = os.path.join(settings.ENVIRONMENT_ROOT, f"{uuid_env}.tgz")
    if env is not None:
        with open(path, "w+b") as f:
            f.write(env.read())
    else:
        tarfile.open(path, "x:gz").close()
    
    return uuid_env


def parse_environ(config: dict) -> dict:
    """Check the validity of 'environ' in the request and return it, returns an empty dictionnary
    if it is not present."""
    if "environ" in config:
        if not isinstance(config["environ"], dict):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'environ must be an object, not {type(config["environ"])}')
        return {k: str(v) for k, v in config["environ"].items()} if "environ" in config else dict()
    return {}


def parse_result_path(config: dict) -> Optional[str]:
    """Check the validity of 'result' in the request and return it, returns None if it is not
    present."""
    if "result_path" in config:
        if not isinstance(config["result_path"], str):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'result_path must be a string, not {type(config["result_path"])}')
        return config["result_path"]
    return None


def parse_save(config: dict) -> bool:
    """Check the validity of 'save' in the request and return it, returns False if it is not
    present."""
    if "save" in config:
        if not isinstance(config["save"], bool):
            raise HTTPExceptions.BAD_REQUEST.with_content(
                f'save must be a boolean, not {type(config["save"])}')
        return config["save"]
    return False


def container_cpu_count() -> int:
    """Return the number of cpu that a container can use."""
    cpu_count = settings.DOCKER_PARAMETERS["cpuset_cpus"]
    
    if "-" in cpu_count:
        lower, upper = cpu_count.split("-")
        cpu_count = int(upper) - int(lower) + 1
    else:
        cpu_count = len(cpu_count.split(","))
    
    return cpu_count


def container_ram_swap() -> Tuple[int, int]:
    """Return ram and swap available to a container.
    
    See https://docs.docker.com/config/containers/resource_constraints/#--memory-swap-details
    for mere details.
    """
    ram = settings.DOCKER_PARAMETERS.get("mem_limit", -1)
    if ram == "-1":
        ram = -1
    if ram != -1:
        ram = humanfriendly.parse_size(ram)
    
    swap = settings.DOCKER_PARAMETERS.get("memswap_limit", 0)
    if swap == "-1":
        swap = -1
    if swap != -1:
        swap = humanfriendly.parse_size(swap)
    
    if ram == -1 and swap == -1:
        return -1, -1
    if ram == swap:
        return ram, 0
    if ram >= 0 and swap == 0:
        return ram, ram
    
    return ram, swap - ram


def container_storage_opt() -> int:
    """Return the size for the 'storage_opt' options of the container.
    
    Return -1 if no option (or the default 'host') was given."""
    if "storage_opt" in settings.DOCKER_PARAMETERS:
        storage = settings.DOCKER_PARAMETERS["storage_opt"].get("size", -1)
        if storage == "host" or storage == "-1":
            storage = - 1
    else:
        storage = -1
    return humanfriendly.parse_size(storage) if storage != -1 else -1


def container_workind_dir_device() -> str:
    """Get the device name where the working point of the sandbox is mounted."""
    raw = subprocess.check_output(
        ["df", settings.DOCKER_VOLUME_HOST_BASEDIR], universal_newlines=True
    )
    return raw.split("\n")[1].split()[0]


def docker_version() -> str:
    """Return the version of Docker used by the sandbox."""
    docker_version = subprocess.check_output(["docker", "-v"], universal_newlines=True)
    return docker_version.strip()[15:].split(",")[0]


def specifications() -> dict:
    """Return the dictionary corresponding to the /specifications/ API endpoints."""
    _, freq_min, freq_max = psutil.cpu_freq()
    ram, swap = container_ram_swap()
    
    return {
        "host":      {
            "cpu":             {
                "core":     psutil.cpu_count(logical=False),
                "logical":  psutil.cpu_count(),
                "freq_min": freq_min,
                "freq_max": freq_max,
            },
            "memory":          {
                "ram":     psutil.virtual_memory()[0],
                "swap":    psutil.swap_memory()[0],
                "storage": {
                    p[0]: psutil.disk_usage(p[1])[0] for p in psutil.disk_partitions()
                }
            },
            "docker_version":  docker_version(),
            "sandbox_version": settings.SANDBOX_VERSION,
        },
        "container": {
            "count":              settings.DOCKER_COUNT,
            "cpu":                {
                "count":  container_cpu_count(),
                "period": settings.DOCKER_PARAMETERS.get("cpu_period", -1),
                "shares": settings.DOCKER_PARAMETERS.get("cpu_shares", -1),
                "quota":  settings.DOCKER_PARAMETERS.get("cpu_quota", -1)
            },
            "memory":             {
                "ram":     ram,
                "swap":    swap,
                "storage": container_storage_opt()
            },
            "io":                 {
                "read_iops":  settings.DOCKER_PARAMETERS.get("device_read_iops", {}),
                "read_bps":   settings.DOCKER_PARAMETERS.get("device_read_bps", {}),
                "write_iops": settings.DOCKER_PARAMETERS.get("device_write_iops", {}),
                "write_bps":  settings.DOCKER_PARAMETERS.get("device_write_bps", {})
            },
            "process":            settings.DOCKER_PARAMETERS.get("pids_limit", -1),
            "working_dir_device": container_workind_dir_device()
        }
    }


def usage_io_network() -> Tuple[dict, dict]:
    """Return current partitions I/O and network usage.
    
    Returned value is a tuple containing :
    
    - A dictionary corresponding to the io with the following keys : read_iops, read_bps, write_iops
    and write_bps. Each value are a dictionary mapping partitions to the corresponding statistics.
    
    - A dictionary corresponding to the io with the following keys : received_packets,
    received_bytes, sent_packets, and sent_bytes."""
    sleep_time = 2
    
    disks = {d[0].split('/')[-1]: d[0] for d in psutil.disk_partitions()}
    raw_io1 = {disks[k]: v for k, v in psutil.disk_io_counters(True).items() if k in disks}
    raw_network1 = psutil.net_io_counters()
    time.sleep(sleep_time)
    raw_io2 = {disks[k]: v for k, v in psutil.disk_io_counters(True).items() if k in disks}
    raw_network2 = psutil.net_io_counters()
    
    network_usage = {
        "sent_bytes":       (raw_network2[0] - raw_network1[0]) // sleep_time,
        "received_bytes":   (raw_network2[1] - raw_network1[1]) // sleep_time,
        "sent_packets":     (raw_network2[2] - raw_network1[2]) // sleep_time,
        "received_packets": (raw_network2[3] - raw_network1[3]) // sleep_time,
    }
    io_usage = {
        "read_iops":  dict(),
        "read_bps":   dict(),
        "write_iops": dict(),
        "write_bps":  dict(),
    }
    for p in raw_io1.keys():
        io_usage["read_iops"][p] = (raw_io2[p][0] - raw_io1[p][0]) // sleep_time
        io_usage["write_iops"][p] = (raw_io2[p][1] - raw_io1[p][1]) // sleep_time
        io_usage["read_bps"][p] = (raw_io2[p][2] - raw_io1[p][2]) // sleep_time
        io_usage["write_bps"][p] = (raw_io2[p][3] - raw_io1[p][3]) // sleep_time
    
    return io_usage, network_usage


def usage():
    """Return the dictionary corresponding to the /usage/ API endpoints."""
    
    io_usage, network_usage = usage_io_network()
    
    return {
        "cpu":       {
            "frequency": psutil.cpu_freq()[0],
            "usage":     psutil.cpu_percent() / 100,
            "usage_avg": [x / psutil.cpu_count() for x in psutil.getloadavg()]
        },
        "memory":    {
            "ram":     psutil.virtual_memory()[3],
            "swap":    psutil.swap_memory()[1],
            "storage": {
                p[0]: psutil.disk_usage(p[1])[1] for p in psutil.disk_partitions()
            }
        },
        "io":        io_usage,
        "network":   network_usage,
        "process":   len(psutil.pids()),
        "container": settings.DOCKER_COUNT - Sandbox.available(),
    }
