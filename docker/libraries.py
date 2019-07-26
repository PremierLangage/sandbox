import json
import os
import subprocess
import sys


devnull = open(os.devnull, "w")

python2 = subprocess.check_output(["python2", "--version"], stderr=subprocess.STDOUT).decode().split()[1].strip()
python3 = ".".join(map(str, sys.version_info[:3]))
java = " ".join(subprocess.check_output(["java", "--version"]).decode().split("\n")[0].split()[:2])
gcc = subprocess.check_output(["gcc", "--version"]).decode().split("\n")[0].split()[3]
perl = subprocess.check_output(["perl", "--version"]).decode().split("\n")[1].split()[8][2:-1]
postgres = subprocess.check_output(["psql", "--version"]).decode().split()[2]

system_packages = dict()
command = "dpkg --get-selections | awk '/php/{print $1}' | xargs dpkg-query --show $1"
for line in subprocess.check_output(command, shell=True, stderr=devnull).decode().split("\n")[:-1]:
    lib, version = [t for t in line.split() if t]
    system_packages[lib] = version

python_modules = dict()
for line in subprocess.check_output(["pip", "freeze"], stderr=devnull).decode().split("\n")[:-1]:
    lib, version = line.split("==")
    python_modules[lib] = version

c_libs = dict()
lines = filter(
    lambda l: l.startswith("\t"),
    subprocess.check_output(["/sbin/ldconfig", "-vN"], stderr=devnull).decode().split("\n")
)
for line in lines:
    lib, version = line.split()[2].split(".so")
    version = "?" if not version else version[1:]
    c_libs[lib] = version

perl_modules = dict()
subprocess.check_output("yes |cpan -l", stderr=devnull, shell=True)
for line in subprocess.check_output(["cpan", "-l"], stderr=devnull).decode().split("\n")[1:-1]:
    lib, version = line.split("\t")
    if version == "undef":
        version = "?"
    perl_modules[lib] = version

print(json.dumps({
    "python3":    python3,
    "python2":    python2,
    "java":       java,
    "gcc":        gcc,
    "perl":       perl,
    "postgres":   postgres,
    "librairies": {
        "system": system_packages,
        "python": python_modules,
        "perl":   perl_modules,
        "c":      c_libs,
    }
}))
