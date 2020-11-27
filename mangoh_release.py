#!/usr/bin/env python3
#
# Release build script for mangOH Red and newer mangOH boards.
# The specification of what is to be included in the build is stored in JSON format
# in another file. The path to that file is passed as the first (and only) argument
# to this script.
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

# The mangOH release version identifier, taken from the release specification file name.
version = None


def yocto_build_dir(board, module):
    return f"{BUILD_DIR}/yocto-{board}-{module}"


def legato_build_dir(board, module):
    return f"{BUILD_DIR}/legato-{board}-{module}"


def toolchain_package_id(board, module):
    return f"mangOH-{board}-{module}-toolchain_{version}-linux64"


def linux_package_id(board, module):
    return f"mangOH-{board}-{module}-linux-image_{version}"


def legato_package_id(board, module):
    return f"mangOH-{board}-{module}-legato_{version}"


def octave_package_id(board, module):
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


def shell(cmd, cwd=None, check=True):
    """Run a shell command. Throw an exception if it fails."""
    subprocess.run(cmd, check=check, shell=True, cwd=cwd)


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
        self.packages = map(remove_latest, base_packages)

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
    depends = mangoh_spec["depends"] + module_spec.get("depends", [])
    yocto_spec = module_spec.get("yocto")
    if yocto_spec:
        depends.append(toolchain_package_id(board, module))
        depends.append(linux_package_id(board, module))
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

    def package_toolchain(board, module):
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
        create_leaf_package(toolchain_package_id(board, module), package_dir)

    def package_linux(board, module):
        """Build the leaf package for a linux distro .cwe (kernel, root file system, etc.)."""
        package_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-linux"
        prep_clean_dir(package_dir)
        manifest_file = f"{package_dir}/manifest.json"
        shutil.copy("linuxManifest.json", manifest_file)
        shell(f"MANGOH_BOARD={board} VERSION={version} TARGET={module} ./replaceVars {manifest_file}")
        shutil.copy(f"{yocto_build_dir(board, module)}/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_{module}.4k.cwe",
                f"{package_dir}/linux.cwe")
        create_leaf_package(linux_package_id(board, module), package_dir)

    yocto_spec = spec["boards"][board][module].get("yocto")
    if yocto_spec:
        build_dir = yocto_build_dir(board, module)
        # This can be slow, even when already built, so checkpoint it.
        checkpoint_file = f"{build_dir}/.built"
        if not os.path.exists(checkpoint_file):
            fetch_yocto(yocto_spec, board, module)
            print(f"Building Yocto distro for mangOH {board} with {module}...")
            #shell("USE_DOCKER=1 make image_bin", cwd=build_dir)
            #shell("USE_DOCKER=1 make toolchain_bin", cwd=build_dir)
            shell("make image_bin", cwd=build_dir)
            shell("make toolchain_bin", cwd=build_dir)
            package_toolchain(board, module)
            package_linux(board, module)
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
        package_id = legato_package_id(board, module)
        remove_leaf_package(package_id)
        # Clean the legato directory, because it may have been built for the same target
        # already but with a different toolchain for a different module.
        shell("make clean", cwd=LEGATO_ROOT)
        # Before we can run the build, we need to set up the leaf workspace with a profile that
        # contains all the required packages.
        with LeafProfile(get_depends(spec, board, module)):
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
    package_id = octave_package_id(board, module)
    remove_leaf_package(package_id)
    # It seems that it is necessary to clean the brkedgepkg between each
    # build for a different module. I suspect that the build system for
    # jerryscript isn't smart enough to know that it needs to re-build
    # certain artifacts when the toolchain is swapped out.
    force_clean_git_repo(OCTAVE_ROOT)
    shell("make clean", cwd=OCTAVE_ROOT)
    depends = get_depends(spec, board, module)
    depends.append(legato_package_id(board, module))
    with LeafProfile(depends):
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
    module_spec = spec["boards"][board][module]
    module_abbreviation = get_abbreviated_module(module)
    staging_dir = f"{LEAF_STAGING_DIR}/{board}-{module}-master"

    def get_requires_list():
        """
        Get a list of strings, each of which contains the ID of a leaf package that
        should be in the "requires" list of the master package.
        """
        return spec["mangoh"]["requires"] + module_spec.get("requires", [])

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
        shell("make clean", cwd=MANGOH_ROOT)
        make_cmd = (
            f"make {board}_spk "
            f"LEGATO_TARGET={module} "
            f"OCTAVE_ROOT={OCTAVE_ROOT}/build "
            f"MODEM_FIRMWARE={firmware_path}"
        )
        # With Octave
        shell(f"leaf shell -c '{make_cmd}'", cwd=MANGOH_ROOT)
        shutil.copy(f"{MANGOH_ROOT}/build/{board}_{module}.spk",
                    f"{staging_dir}/mangOH-{board}-{module}_{version}-octave.spk")
        # Without Octave
        shell("make clean", cwd=MANGOH_ROOT)
        make_cmd = make_cmd + " OCTAVE=0"
        shell(f"leaf shell -c '{make_cmd}'", cwd=MANGOH_ROOT)
        shutil.copy(f"{MANGOH_ROOT}/build/{board}_{module}.spk",
                    f"{staging_dir}/mangOH-{board}-{module}_{version}.spk")

    def package(depends, firmware_version):
        package_name = f"mangOH-{board}-{module}"
        package_id=f"{package_name}_{version}"
        print(f"Creating Leaf package '{package_id}'")
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

    prep_clean_dir(staging_dir)
    depends = get_depends(spec, board, module)
    depends.append(legato_package_id(board, module))
    depends.append(octave_package_id(board, module))
    with LeafProfile(depends):
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

    # Extract the release version from the specification file name.
    filename = os.path.basename(sys.argv[1].strip())
    assert filename.endswith('.json')
    version = filename[:-5]
    assert version
    print(f"Building mangOH release version {version}...");

    # Prepare the build directory tree and the process environment.
    os.makedirs(BUILD_DIR, exist_ok = True)
    sandbox_leaf()

    # Add a local file system directory as a leaf remote into which we will place leaf
    # packages as we create them.
    shell("leaf remote remove local 2> /dev/null", check=False)
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

    print(f"==== RELEASE {version} BUILD COMPLETE ====")
    print(f"The following leaf packages were generated in {LEAF_REMOTE}:")
    shell(f"ls {LEAF_REMOTE} --ignore='*.json' --ignore='*.info'")
