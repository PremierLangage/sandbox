import json
import os
import stat
import subprocess


devnull = open(os.devnull, "w")

system_packages = dict()
command = "dpkg --get-selections | awk '{print $1}' | xargs dpkg-query --show $1"
commands = ["/bin/bash", "-c", command]
for line in subprocess.check_output(commands, stderr=devnull).decode().split("\n")[:-1]:
    lib, version = [t for t in line.split() if t]
    system_packages[lib] = version

python_modules = dict()
for line in (
    subprocess.check_output(["/usr/local/bin/pip", "freeze"], stderr=devnull)
    .decode()
    .split("\n")[:-1]
):
    lib, version = line.split("==")
    python_modules[lib] = version

c_libs = dict()
lines = filter(
    lambda line: line.startswith("\t"),
    subprocess.check_output(["/sbin/ldconfig", "-vN"], stderr=devnull)
    .decode()
    .split("\n"),
)
for line in lines:
    lib, version = line.split()[2].split(".so")
    version = "?" if not version else version[1:]
    c_libs[lib] = version

perl_modules = dict()
commands = ["/bin/bash", "-c", "yes | /usr/bin/cpan -l"]
subprocess.check_output(commands, stderr=devnull)
for line in (
    subprocess.check_output(["/usr/bin/cpan", "-l"], stderr=devnull)
    .decode()
    .split("\n")[1:-1]
):
    lib, version = line.split("\t")
    if version == "undef":
        version = "?"
    perl_modules[lib] = version

bins = []
executable = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
for path in os.environ["PATH"].split(":"):
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if os.path.isfile(file_path) and os.stat(file_path).st_mode & executable:
            bins.append(name)

print(
    json.dumps(
        {
            "libraries": {
                "system": dict(sorted(system_packages.items())),
                "python": dict(sorted(python_modules.items())),
                "perl": dict(sorted(perl_modules.items())),
                "c": dict(sorted(c_libs.items())),
            },
            "bin": sorted(bins),
        }
    )
)
