#!/usr/bin/env python3

import sys
import json
import subprocess
import os
import shutil
import pathlib

def fetch_git_repo(url, ref):
    repo = url.split("/")[-1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    subprocess.run("git clone {}".format(url), check=True, shell=True)
    subprocess.run("git checkout {}".format(ref), cwd=repo, check=True, shell=True)
    subprocess.run("git submodule update --recursive --init", cwd=repo, check=True, shell=True)


def force_clean_octave():
    for dir, subdirs, files in os.walk("brkedgepkg"):
        if '.git' in subdirs or '.git' in files:
            print("cleaning: {}".format(dir))
            subprocess.run("git clean -xfd", check=True, shell=True, cwd=dir)

def build_octave_packages(json_bs):
    fetch_git_repo("git@github.com:flowthings/brkedgepkg.git", json_bs["octave_git_ref"])
    fetch_git_repo("git@github.com:mangOH/mangOH.git", json_bs["mangoh_git_ref"])

    for module in json_bs["modules"]:
        force_clean_octave()
        subprocess.run(
            "leaf setup -p swi-{}_{} _tmp_red_release".format(
                module["casual_target"], module["master_package_version"]),
            check=True, shell=True)
        subprocess.run(
            "leaf shell -c \"make MANGOH_ROOT=\`pwd\`/../mangOH DHUB_ROOT=\`pwd\`/../mangOH/apps/DataHub MANGOH_BOARD=red VERSION={}\"".format(
                json_bs["octave_version"]),
            check=True, shell=True, cwd="brkedgepkg")
        subprocess.run("leaf profile delete _tmp_red_release", check=True, shell=True)

        pathlib.Path("leaf").mkdir(exist_ok=True)
        shutil.copy(
            "brkedgepkg/build/Octave-mangOH-red-{}.leaf".format(module["legato_target"]),
            "leaf/Octave-mangOH-red-{}_{}.leaf".format(
                module["legato_target"], json_bs["octave_version"]))
        shutil.copy(
            "brkedgepkg/build/Octave-mangOH-red-{}.leaf.info".format(module["legato_target"]),
            "leaf/Octave-mangOH-red-{}_{}.leaf.info".format(
                module["legato_target"], json_bs["octave_version"]))


def build_master_packages(json_bs):
    for module in json_bs["modules"]:
        pathlib.Path("manifests/{}".format(module["casual_target"])).mkdir(parents=True, exist_ok=True)
        subprocess.run(
            "leaf build manifest \
            -o manifests/{} \
            --name mangoh-red-{} \
            --version {} \
            --description \"mangOH Red {} - FW={}, Legato={}, Octave={}\" \
            --master true \
            --date \"`date --utc`\" \
            --tag mangOH \
            --tag red \
            --tag Octave \
            --tag {} \
            --depends swi-{}_{} \
            --depends Octave-mangOH-red-{}_{}".format(
                module["casual_target"],
                module["legato_target"],
                json_bs["mangoh_version"],
                module["casual_target"],
                module["firmware"],
                json_bs["legato_version"],
                json_bs["octave_version"],
                module["legato_target"],
                module["casual_target"],
                module["master_package_version"],
                module["legato_target"],
                json_bs["octave_version"]),
            check=True,
            shell=True)
        subprocess.run(
            "leaf build pack -i manifests/{} -o leaf/mangoh-red-{}_{}.leaf -- -J .".format(
                module["casual_target"], module["legato_target"], json_bs["mangoh_version"]),
            check=True,
            shell=True)


def build_index():
    subprocess.run("leaf build index -o mangOH-red.json *.leaf", check=True, shell=True, cwd="leaf")


def red_build(build_spec):
    json_bs = None
    with open(build_spec) as bs:
        json_bs = json.load(bs)
    build_octave_packages(json_bs)
    build_master_packages(json_bs)
    build_index()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Expected one argument, a JSON build spec\n")
        sys.exit(1)
    red_build(sys.argv[1])
