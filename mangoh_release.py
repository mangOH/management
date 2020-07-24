#!/usr/bin/env python3
#
# Release build script for mangOH Red and newer mangOH boards.
# The specification of what is to be included in the build is stored in JSON format
# in another file. The path to that file is passed as the first (and only) argument
# to this script.
#
# = Manifest Format +
#
# The specification format is a JSON object.  Each subsection below describes a member of
# that object.
#
# == mangoh ==
#
# Specifies details of the mangOH release.
#
# "mangoh": {
#     "version": "0.7.0-beta01",
#     "ref": "646592902e6d5d748560a60da7e3db0c0f57b360",
#     "wget": [
#         {
#             "url": "https://community.bosch-sensortec.com/varuj77995/attachments/varuj77995/bst_community-mems-forum/44/1/BSEC_1.4.7.2_GCC_CortexA7_20190225.zip",
#             "dir": "components/boschBsec",
#             "unpack": "unzip"
#         }
#     ],
#     "requires": [
#         "swi-license_1.2",
#         "swi-verify-license_latest"
#     ],
#     "depends": [
#         "swi-legato_latest",
#         "swi-vscode-support_latest"
#     ]
# }
#
# "version" contains the release version identifier to be used for all leaf packages generated
# by the build.
#
# "ref" contains the git ref to be checked out from the main mangOH repository (MANGOH_MAIN_REPO)
# when fetching the mangOH source code.
#
# "wget" is an optional member, which directs the build to use wget to download
# a list of files under the MANGOH_ROOT directory and optionally unpack them.
# The "wget" member is an array of objects. Each of those objects must have a "url" member
# and a "dir" member (which is a relative path from MANGOH_ROOT of a directory into which
# the file will be downloaded. If an "unpack" member is present, it specifies the method to
# be used to unpack the downloaded file. Presently, only "unzip" is supported.
#
# "requires" is a list of leaf packages to be added to the "requires" section of all generated
# SDK master leaf packages.
#
# "depends" is a list of leaf packages to be added to the "depends" section of all generated
# SDK master leaf packages.
#
# == legato ==
#
# Specifies the Legato source to fetch using Google's "repo" tool, as well as optional patches to
# apply to the Legato source code before building it.
#
# "legato": {
#     "manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
#     "base_manifest": "legato/releases/20.04.0/legato.xml",
#     "patches": [
#         {
#             "purpose": "LE-14705: Fix SecStore to enable recovery from corrupted keys file.",
#             "dir": ".",
#             "cherry_pick": "f9cc1f29d4b36e9999d3365a2ecf85e358eb4efd"
#         },
#         {
#             "purpose": "LE-14639: [Octave][CoAP]AV does not reply to CoAP retry on CoAP data for application",
#             "dir": "3rdParty/Lwm2mCore/3rdParty/wakaama",
#             "gerrit_review": {
#                 "project": "external/eclipse/wakaama",
#                 "patch_set": "63/60163/1"
#             }
#         }
#     ]
# }
#
# "manifest_repo" is a string containing the URL of the repo manifest repository.
#
# "base_manifest" is the path to the manifest XML file within the manifest repository.
#
# "patches" is an array of objects. All such objects must have a "dir" member containing a
# the path to the directory under LEGATO_ROOT at which the patch should be applied.
# The "purpose" member is an optional string used as a human-readable comment to document
# the reason why the patch is being applied.
#
# In addition to "dir", all objects in the "patches" array must have either a "cherry_pick"
# member or a "gerrit_review" member.
#
# The "cherry_pick" member is used when a fix is needed that has passed review and been submitted
# to the Legato master, but that was not included in the version of Legato that is checked out
# by the base manifest. This is typically needed to patch up known issues that have been fixed
# but have not yet made it into a Legato release. If the "cherry_pick" member is used, it must
# contain the git commit ID of a commit to be git cherry-picked into the HEAD from the same
# repository.
#
# The "gerrit_review" member is used when the patch required has not yet even passed review in
# Sierra Wireless's internal Gerrit instance. This is intended for emergency use only.
# The "gerrit_review" member is an object with two members:
#  - "project" specifies the Gerrit project name to fetch from within Sierra Wireless's internal
#    Gerrit.
#  - "patch_set" identifies the Gerrit patch set to fetch and cherry-pick.
#
# == octave ==
#
# "octave": {
#     "ref": "BROOKLYN-2626_fix_makefile",
#     "version": "3.0.0.pre03Jun2020-mangOH-1"
# }
#
# Specifies the Octave Edge Package git repository ref to fetch and checkout when building Octave
# into the release. Also specifies the version string that is to be reported to the Octave cloud
# to ensure that the Octave cloud knows (and uses) the correct set of capabilities of the
# device's Octave Edge Package apps.
#
# == boards ==
#
# Specifies all board + module combinations to be built for, and what component parts need to
# be included in those builds.
#
# "boards": {
#     "yellow": {
#         "wp76xx": {
#             "depends": [
#                 "wp76-modem-image_13.3"
#             ],
#             "modem_firmware": "9999999_9908787_SWI9X07Y_02.28.03.05_00_SIERRA_001.032_000.spk",
#             "yocto": {
#                 "manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
#                 "base_manifest": "mdm9x28/tags/SWI9X07Y_02.37.07.00.xml",
#                 "add": [
#                     {
#                         "url": "https://github.com/mangOH/meta-mangoh",
#                         "ref": "mdev_update_for_ecm",
#                         "dir": "meta-mangoh"
#                     }
#                 ]
#             }
#         },
#         "wp77xx": {
#            "depends": [
#                "wp77-modem-image_12"
#            ],
#            "modem_firmware": "9999999_9908788_SWI9X06Y_02.32.02.00_00_SIERRA_001.027_000.spk",
#             "yocto": {
#                 "manifest_repo": "https://github.com/mangOH/manifest.git",
#                 "base_manifest": "mangOH/releases/v0.6.0/wp77xx.xml"
#             }
#         }
#     },
#     "red": {
#         "wp85": {
#             "depends": [
#                 "wp85-toolchain_SWI9X15Y_07.14.01.00-linux64",
#                 "wp85-linux-image_SWI9X15Y_07.14.01.00",
#                 "wp85-modem-image_17"
#             ],
#             "modem_firmware": "9999999_9904559_SWI9X15Y_07.14.01.00_00_GENERIC_001.042_000.spk"
#         }
#     }
# }
#
# "boards" is an object in which each member it an object that represents a single board, such
# as "red" or "yellow". The name of the member is the name of the board, and the value of the
# member is an object whose members represent modules, such as Sierra Wireless WP76xx.
#
# The name of the module member must be the legato build "target" name, such as "wp85" or "wp76xx".
#
# All modules must have a "depends" member, which is a list of all the leaf packages to be
# installed in the workspace when building for this module on this board. These leaf packages
# will also be added to the "depends" list within the mangOH SDK master leaf package for this
# particular board + module combination.
#
#     "depends": [
#         "wp85-toolchain_SWI9X15Y_07.14.01.00-linux64",
#         "wp85-linux-image_SWI9X15Y_07.14.01.00",
#         "wp85-modem-image_17"
#     ],
#
# The "modem_firmware" member specifies the name of the modem firmware SPK file from which
# the modem firmware files will be extracted for inclusion in the final release SPK file.
#
#     "modem_firmware": "9999999_9908787_SWI9X07Y_02.28.03.05_00_SIERRA_001.032_000.spk",
#
# A "yocto" member can (optionally) be added when a custom Yocto linux distribution must be
# built for this module on this board.  It specifies the Gerrit manifest repository URL and
# the path to the manifest XML file within that repository that is to be used to fetch the
# Yocto sources.
#
#     "yocto": {
#         "manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
#         "base_manifest": "mdm9x28/tags/SWI9X07Y_02.37.07.00.xml",
#         "add": [
#             {
#                 "url": "https://github.com/mangOH/meta-mangoh",
#                 "ref": "mdev_update_for_ecm",
#                 "dir": "meta-mangoh"
#             }
#         ]
#     }
# }
#
# The "add" member within the "yocto" object is optional. It can be used to specify a list
# of other Git repositories that need to be cloned and checked out into the Yocto source tree
# before it is built. The "dir" path is relative to the root of the Yocto source tree.
#
# Copyright (C) Sierra Wireless Inc.

import sys
import json
import subprocess
import os
import shutil
import pathlib
import glob

# All build artifacts will appear under here, including source code.
# This makes it easy to clean up or to archive the entire results of a release build.
BUILD_DIR = f"{os.getcwd()}/build"

# The BUILD_DIR is the root of the leaf workspace used to build, so the leaf-data for the
# workspace's current profile will be found there.
LEAF_DATA = f"{BUILD_DIR}/leaf-data"

# Variables that need to be set in the environment to "sandbox" leaf (i.e., to make sure
# leaf doesn't change the user's leaf configuration and to make sure that the user's leaf
# configuration doesn't contaminate the release).
LEAF_CONFIG = f"{BUILD_DIR}/leaf/config"
LEAF_CACHE = f"{BUILD_DIR}/leaf/cache"
LEAF_USER_ROOT = f"{BUILD_DIR}/leaf/installed-packages"

# Directory in which the built leaf packages will be placed and indexed to form a "remote"
# that we can use to install those packages and add them to profiles.
LEAF_REMOTE = f"{BUILD_DIR}/leaf/remote"

# Directory in which leaf packages will be assembled in preparation for packing.
LEAF_STAGING_DIR = f"{BUILD_DIR}/leaf/staging"

# The directory in which the Legato sources will be cloned and built.
LEGATO_REPO_ROOT = f"{BUILD_DIR}/legato"
LEGATO_ROOT = f"{LEGATO_REPO_ROOT}/legato"

# The directory in which the mangOH sources will be cloned and built.
MANGOH_ROOT = f"{BUILD_DIR}/mangOH"

# The directory in which the Octave app sources will be cloned and built.
OCTAVE_ROOT = f"{BUILD_DIR}/brkedgepkg"

# The directory in which the Data Hub sources can be found.
DHUB_ROOT = f"{MANGOH_ROOT}/apps/DataHub"

# Repository URLs.
MANGOH_MAIN_REPO = "https://github.com/mangOH/mangOH"


def yocto_build_dir(board, module):
    return f"{BUILD_DIR}/yocto-{board}-{module}"


def legato_build_dir(board, module):
    return f"{BUILD_DIR}/legato-{board}-{module}"


def toolchain_package_id(board, module, version):
    return f"mangOH-{board}-{module}-toolchain_{version}-linux64"


def linux_package_id(board, module, version):
    return f"mangOH-{board}-{module}-linux-image_{version}"


def legato_package_id(board, module, version):
    return f"mangOH-{board}-{module}-legato_{version}"


def octave_package_id(board, module, version):
    return f"Octave-mangOH-{board}-{module}_{version}"


def get_abbreviated_module(module):
    # So far, the abbreviated module name is always the module name with trailing 'x' and '0'
    # characters removed. E.g., wp76xx -> wp76 and wp750x -> wp75.
    return module.rstrip('x0')


def sandbox_leaf():
    """Set the the process environment variables needed to sandbox leaf."""
    os.environ["LEAF_CONFIG"] = LEAF_CONFIG
    os.environ["LEAF_CACHE"] = LEAF_CACHE
    os.environ["LEAF_USER_ROOT"] = LEAF_USER_ROOT


def shell(cmd, cwd=None):
    """Run a shell command. Throw an exception if it fails."""
    subprocess.run(cmd, check=True, shell=True, cwd=cwd)


def fetch_git_repo(url, ref, dest=None):
    """Clone the repository specified by url into the directory dest and checkout ref

    The repository is cloned recursively, so submodules will also be retrieved. Note that the
    repository is cloned into the current working directory and that the name of the directory will
    be derived from the URL.
    """
    if dest is None:
        dest = url.split("/")[-1]
        if dest.endswith('.git'):
            dest = dest[:-4]
    shell(f"git clone {url} {dest}")
    shell(f"git checkout {ref}", cwd=dest)
    shell("git submodule update --recursive --init", cwd=dest)


def force_clean_git_repo(repo_path):
    """
    Recursively find all git repositories under repo_path and remove untracked files;
    excluding the ".fetched" checkpoint file.
    """
    for directory, subdirs, files in os.walk(repo_path):
        if '.git' in subdirs or '.git' in files:
            print(f"cleaning: {directory}")
            shell("git clean -xfd -e /.fetched", cwd=directory)


def fetch_mangoh(spec):
    """Clone the mangOH repository and all submodules."""
    fetch_git_repo(MANGOH_MAIN_REPO, spec["mangoh"]["ref"], dest=MANGOH_ROOT);


def prep_clean_dir(build_dir):
    """If the directory is there already, delete it. Then create an empty one."""
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)


def index_leaf_remote():
    """Build the leaf remote's index"""
    shell("leaf build index -o mangOH.json *.leaf", cwd=LEAF_REMOTE)


def create_leaf_package(package_id, staging_dir):
    """
    Create a package file in the leaf remote with a given package_id whose files are waiting
    in the staging_dir. The package_id should include the version, but NOT the '.leaf' suffix.
    """
    os.makedirs(LEAF_REMOTE, exist_ok = True)
    package_file = f"{LEAF_REMOTE}/{package_id}.leaf"
    shell(f"leaf build pack -o {package_file} -i {staging_dir} -- -J .")
    index_leaf_remote()


def remove_leaf_package(package_id):
    """
    Remove a package from the leaf remote and the installed packages, and clean the leaf cache.
    The package_id should include the version, but NOT the '.leaf' suffix.
    """
    shell(f"rm -f {package_id}.leaf*", cwd=LEAF_REMOTE)
    shell(f"rm -rf {LEAF_CACHE}/*")
    shell(f"rm -rf {package_id}", cwd=LEAF_USER_ROOT)
    index_leaf_remote()


class LeafProfile:
    """
    Used to create a leaf profile based on the base_package using a "with" block, so it gets
    deleted on exit from the with block.
    """
    def __init__(self, base_packages):
        self.packages = base_packages

    def __enter__(self):
        shell("leaf remote fetch", cwd=BUILD_DIR)
        package_args = ' '.join([f'-p {pkg} ' for pkg in self.packages])
        shell(f"yes | leaf setup profile {package_args}", cwd=BUILD_DIR)
        return self

    def __exit__(self, exception_type, value, traceback):
        shell("leaf profile delete profile", cwd=BUILD_DIR)


def get_depends(spec, board, module):
    """
    Get a list of strings, each of which contains the ID of a leaf package that
    the spec says a given board and module depends on.
    """
    mangoh_spec = spec["mangoh"]
    module_spec = spec["boards"][board][module]
    depends = mangoh_spec["depends"] + (module_spec.get("depends") or [])
    yocto_spec = module_spec.get("yocto")
    if yocto_spec:
        version = spec["mangoh"]["version"]
        depends.append(toolchain_package_id(board, module, version))
        depends.append(linux_package_id(board, module, version))
    return depends


def remove_latest(s):
    """Remove the '_latest' from the end of a string, if present."""
    if s.endswith("_latest"):
        s = s[:-7]
    return s


def build_yocto(spec, board, module):
    """
    Build a custom Yocto-based distro.
    The output of this, if any, is a set of leaf packages for the toolchain, kernel,
    root file system, etc., added to the leaf "remote".
    """
    def fetch_yocto(yocto_spec, board, module):
        """Fetch the source code for the Yocto toolchain, if it hasn't already been fetched."""
        build_dir = yocto_build_dir(board, module)
        # This can be very time consuming and requires a fast Internet connection,
        # so checkpoint this.
        checkpoint_file = f"{build_dir}/.fetched"
        if not os.path.exists(checkpoint_file):
            print(f"Fetching Yocto sources for mangOH {board} with {module}...")
            prep_clean_dir(build_dir)
            manifest_repo = yocto_spec["manifest_repo"]
            base_manifest = yocto_spec["base_manifest"]
            shell(f"repo init -u {manifest_repo} -m {base_manifest} && repo sync", cwd=build_dir)
            for add_on in yocto_spec.get("add", []):
                fetch_git_repo(add_on["url"], add_on["ref"], dest=f"{build_dir}/{add_on['dir']}")
            # Checkpoint reached.
            pathlib.Path(checkpoint_file).touch()

    def package_toolchain(board, module, version):
        """Build the leaf package for a module's toolchain."""
        package_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-toolchain"
        prep_clean_dir(package_dir)
        manifest_file = f"{package_dir}/manifest.json"
        shutil.copy("toolchainManifest.json", manifest_file)
        shell(f"MANGOH_BOARD={board} VERSION={version} TARGET={module} ./replaceVars {manifest_file}")
        self_extracting_toolchain = glob.glob(
            f"{yocto_build_dir(board, module)}/build_bin/tmp/deploy/sdk/"
            "poky-swi-ext-glibc-x86_64-meta-toolchain-swi-armv7a-neon-toolchain-swi-*.sh")
        assert len(self_extracting_toolchain) is 1
        shutil.copy(self_extracting_toolchain[0], f"{package_dir}/toolChainExtractor.sh")
        create_leaf_package(toolchain_package_id(board, module, version), package_dir)

    def package_linux(board, module, version):
        """Build the leaf package for a linux distro .cwe (kernel, root file system, etc.)."""
        package_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-linux"
        prep_clean_dir(package_dir)
        manifest_file = f"{package_dir}/manifest.json"
        shutil.copy("linuxManifest.json", manifest_file)
        shell(f"MANGOH_BOARD={board} VERSION={version} TARGET={module} ./replaceVars {manifest_file}")
        shutil.copy(f"{yocto_build_dir(board, module)}/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_{module}.4k.cwe",
                f"{package_dir}/linux.cwe")
        create_leaf_package(linux_package_id(board, module, version), package_dir)

    yocto_spec = spec["boards"][board][module].get("yocto")
    if yocto_spec:
        build_dir = yocto_build_dir(board, module)
        version = spec["mangoh"]["version"]
        # This can be slow, even when already built, so checkpoint it.
        checkpoint_file = f"{build_dir}/.built"
        if not os.path.exists(checkpoint_file):
            fetch_yocto(yocto_spec, board, module)
            print(f"Building Yocto distro for mangOH {board} with {module}...")
            #shell("USE_DOCKER=1 make image_bin", cwd=build_dir)
            #shell("USE_DOCKER=1 make toolchain_bin", cwd=build_dir)
            shell("make image_bin", cwd=build_dir)
            shell("make toolchain_bin", cwd=build_dir)
            package_toolchain(board, module, version)
            package_linux(board, module, version)
            # Checkpoint reached.
            pathlib.Path(checkpoint_file).touch()


def fetch_legato(spec):
    """
    Fetch and patch up the Legato sources in LEGATO_ROOT.
    """
    legato_spec = spec.get("legato")
    if legato_spec:
        # Fetching all Legato sources takes a while and requires a solid Internet connection,
        # so checkpoint it.
        checkpoint_file = f"{LEGATO_REPO_ROOT}/.fetched"
        if not os.path.exists(checkpoint_file):
            prep_clean_dir(LEGATO_REPO_ROOT)
            manifest_repo = legato_spec["manifest_repo"]
            base_manifest = legato_spec["base_manifest"]
            # Get the Legato sources
            shell(f"repo init -u {manifest_repo} -m {base_manifest} && repo sync",
                  cwd=LEGATO_REPO_ROOT)
            # Checkpoint reached.
            pathlib.Path(checkpoint_file).touch()


# Cached legato version string.
# Don't use this directly. Call get_legato_version().
_legato_version = None

def get_legato_version():
    """
    Get the legato version string.
    """
    global _legato_version
    # If we've fetched it already, don't re-fetch it.
    if not _legato_version:
        # Extract the version string from Legato's "version" file.
        with open(f"{LEGATO_ROOT}/version", "r") as f:
            _legato_version = f.readline().strip()
        assert _legato_version
    return _legato_version

def build_legato(spec, board, module):
    """
    Build the custom Legato framework for a specific module using the appropriate toolchain
    for the board and module. The output of this is a leaf package for Legato.
    """
    legato_spec = spec.get("legato")
    if legato_spec:
        print(f"Building the Legato Framework for {module} on {board}...")
        # If there's a Legato leaf package for this board+module in the remote already,
        # remove it.
        version = spec["mangoh"]["version"]
        package_id = legato_package_id(board, module, version)
        remove_leaf_package(package_id)
        # Clean the legato directory, because it may have been built for the same target
        # already but with a different toolchain for a different module.
        shell("make clean", cwd=LEGATO_ROOT)
        # Before we can run the build, we need to set up the leaf workspace with a profile that
        # contains all the required packages.
        with LeafProfile(map(remove_latest, get_depends(spec, board, module))):
            shell(f"leaf shell -c 'make {module}'", cwd=LEGATO_ROOT)
            # Package as leaf package and add to remote.
            legato_version = get_legato_version()
            package_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-legato"
            if os.path.exists(package_dir):
                shutil.rmtree(package_dir)
            shell(f"cp -r {LEGATO_ROOT} {package_dir}")
            shutil.rmtree(f"{package_dir}/.git")
            shutil.copy("legatoManifest.json", f"{package_dir}/manifest.json")
            shell(f"MANGOH_BOARD={board} VERSION={version} TARGET={module} "
                  f"LEGATO_VERSION={legato_version} ./replaceVars {package_dir}/manifest.json")
            create_leaf_package(package_id, package_dir)


def fetch_octave(spec):
    """Fetch the Octave Edge Package sources."""
    checkpoint_file = f"{OCTAVE_ROOT}/.fetched"
    if not os.path.exists(checkpoint_file):
        prep_clean_dir(OCTAVE_ROOT)
        fetch_git_repo("git@github.com:flowthings/brkedgepkg.git",
                       spec["octave"]["ref"],
                       dest=OCTAVE_ROOT)
        # Checkpoint reached.
        pathlib.Path(checkpoint_file).touch()


def build_octave(spec, board, module):
    """
    Build the Octave Edge Package apps and create a Leaf package containing them.
    """
    print(f"Building the Octave Edge Package for {module} on {board}...")
    # If there's an Octave leaf package for this board+module in the remote already, remove it.
    version = spec["mangoh"]["version"]
    package_id = octave_package_id(board, module, version)
    remove_leaf_package(package_id)
    # It seems that it is necessary to clean the brkedgepkg between each
    # build for a different module. I suspect that the build system for
    # jerryscript isn't smart enough to know that it needs to re-build
    # certain artifacts when the toolchain is swapped out.
    force_clean_git_repo(OCTAVE_ROOT)
    depends = get_depends(spec, board, module)
    depends.append(legato_package_id(board, module, version))
    with LeafProfile(map(remove_latest, depends)):
        shell('leaf shell -c leaf profile', cwd=BUILD_DIR)
        shell('leaf shell -c leaf env', cwd=BUILD_DIR)
        cmd = (
            f"leaf shell -c 'make MANGOH_ROOT={MANGOH_ROOT} DHUB_ROOT={DHUB_ROOT}"
            f" MANGOH_BOARD={board} VERSION={version}'"
        )
        shell(cmd, cwd=OCTAVE_ROOT)
    # The Octave build already creates the leaf packages, so they just need to be
    # copied into remote.
    shutil.copy(
        f"{OCTAVE_ROOT}/build/Octave-mangOH-{board}-{module}.leaf",
        f"{LEAF_REMOTE}/{package_id}.leaf")
    shutil.copy(
        f"{OCTAVE_ROOT}/build/Octave-mangOH-{board}-{module}.leaf.info",
        f"{LEAF_REMOTE}/{package_id}.leaf.info")
    index_leaf_remote()


def fetch_mangoh(spec):
    """Fetch the mangOH sources."""
    checkpoint_file = f"{MANGOH_ROOT}/.fetched"
    if not os.path.exists(checkpoint_file):
        prep_clean_dir(MANGOH_ROOT)
        fetch_git_repo("git@github.com:mangOH/mangOH.git",
                       spec["mangoh"]["ref"],
                       dest=MANGOH_ROOT)
        for download in spec["mangoh"]["wget"]:
            url = download["url"]
            dest_dir = f"{MANGOH_ROOT}/{download['dir']}"
            shell(f"wget {url}", cwd=dest_dir)
            if download.get("unpack") == "unzip":
                shell(f"unzip {os.path.basename(url)}", cwd=dest_dir)
        # Checkpoint reached.
        pathlib.Path(checkpoint_file).touch()


def build_mangoh(spec, board, module):
    """
    Build the factory .spk files for both the Octave and non-Octave versions for a particular
    mangOH board and module. Generate the master leaf package and add it to the leaf remote.
    """
    mangoh_spec = spec["mangoh"]
    module_spec = spec["boards"][board][module]
    version = mangoh_spec["version"]
    module_abbreviation = get_abbreviated_module(module)

    def get_requires_list():
        """
        Get a list of strings, each of which contains the ID of a leaf package that
        should be in the "requires" list of the master package.
        """
        return mangoh_spec["requires"] + (module_spec.get("requires") or [])

    def get_modem_firmware():
        """
        Return a tuple containing:
        1. the file system path to the modem firmware file to be used to build the SPK,
        2. a string containing the modem firmware version number (e.g., "13.3").
        """
        path = f"{LEAF_DATA}/current/{module_abbreviation}-modem-image/{module_spec['modem_firmware']}"
        # The firmware version number can be found in the leaf manifest for the firmware package.
        firmware_manifest = None
        with open(f"{os.path.dirname(path)}/manifest.json") as json_file:
            firmware_manifest = json.load(json_file)
        release = firmware_manifest["info"]["version"]
        return path, release

    def build(firmware_path):
        make_cmd = (
            f"make {board}_spk "
            f"LEGATO_TARGET={module} "
            f"OCTAVE_ROOT={OCTAVE_ROOT}/build "
            f"MODEM_FIRMWARE={firmware_path}"
        )
        # With Octave
        shell(f"leaf shell -c '{make_cmd}'", cwd=MANGOH_ROOT)
        shutil.copy(f"{MANGOH_ROOT}/build/{board}_{module}.spk",
                    f"{BUILD_DIR}/mangOH-{board}-{module}_{version}-octave.spk")
        # Without Octave
        shell("make clean", cwd=MANGOH_ROOT)
        make_cmd = make_cmd + " OCTAVE=0"
        shell(f"leaf shell -c '{make_cmd}'", cwd=MANGOH_ROOT)
        shutil.copy(f"{MANGOH_ROOT}/build/{board}_{module}.spk",
                    f"{BUILD_DIR}/mangOH-{board}-{module}_{version}.spk")

    def package(depends, firmware_version):
        package_name = f"mangOH-{board}-{module}"
        version = mangoh_spec["version"]
        package_id=f"{package_name}_{version}"
        print(f"Creating Leaf package '{package_id}'")
        staging_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-master"
        prep_clean_dir(staging_dir)
        octave_version = spec["octave"]["version"]
        legato_version = get_legato_version()
        description = (
            f"mangOH {board} {module} "
            f"(Modem=R{firmware_version}, Legato={legato_version}, Octave={octave_version})"
        )
        cmd = (
            f"leaf build manifest "
            f"-o {staging_dir} "
            f"--name {package_name} "
            f"--version {version} "
            f"--description '{description}' "
            f"--master true "
            f"--tag mangOH "
            f"--tag {board} "
            f"--tag Octave "
            f"--tag {module} ")
        cmd += ' '.join([f"--depends {pkg}" for pkg in depends])
        requires = get_requires_list()
        cmd += ' ' + ' '.join([f"--requires {pkg}" for pkg in requires])
        shell(cmd)
        create_leaf_package(package_id, staging_dir)

    depends = get_depends(spec, board, module)
    depends.append(legato_package_id(board, module, version))
    depends.append(octave_package_id(board, module, version))
    with LeafProfile(map(remove_latest, depends)):
        firmware_path, firmware_version = get_modem_firmware()
        build(firmware_path)
        package(depends, firmware_version)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Expected one argument, a JSON build spec\n")
        sys.exit(1)
    spec = None
    with open(sys.argv[1]) as json_file:
        spec = json.load(json_file)

    # Prepare the build directory tree and the process environment.
    os.makedirs(BUILD_DIR, exist_ok = True)
    sandbox_leaf()

    # Add a local file system directory as a leaf remote into which we will place leaf
    # packages as we create them.
    subprocess.run("leaf remote remove local 2> /dev/null", shell=True, check=False)
    shell(f"leaf remote add local file://{LEAF_REMOTE}/mangOH.json")

    # Fetch the Octave, Legato, and mangOH sources. These are common to all boards and modules.
    fetch_legato(spec)
    fetch_octave(spec)
    fetch_mangoh(spec)

    # For each board+module combination, build Yocto (if needed), Legato, the Octave apps, and
    # finally the mangOH system and SPK.
    # Each step produces leaf packages, which are added to the leaf remote for use by subsequent
    # steps.
    boards = spec["boards"]
    for board, board_spec in boards.items():
        for module in board_spec:
            build_yocto(spec, board, module)
            build_legato(spec, board, module)
            build_octave(spec, board, module)
            build_mangoh(spec, board, module)
