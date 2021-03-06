# mangOH Software Configuration Management Makefile
#
# This codifies the rules for building and tagging mangOH release candidates and releases.
#
# TODO: Add tagging.
# TODO: Do we need to fetch Legato sources separately? The correct version of Legato should already
#       be referenced by the manifest in the mangOH manifest repository.
# TODO: Automate Octave tag resolution or better yet, get Octave to tag the repository with their
#       apps in it.
#
# The primary build output is a set of leaf packages and a factory programming image (.spk) file.
# Other artifacts built along the way include toolchains and linux images.
#
# There are three mandatory variables that must be passed in via the command-line or the
# environment:
#
#	RELEASE_VERSION = the version identification string for the release (or release candidate).
#	                  E.g., RELEASE_VERSION=0.1.0.rc1
#
#	BSEC_DIR        = file system path to where the Bosch BSEC library sources can be found.
#	                  E.g., BSEC_DIR=~/BSEC_1.4.7.2_GCC_CortexA7_20190225/algo/bin/Normal_version/Cortex_A7
#
# Copyright (C) Sierra Wireless Inc.

# If we're not cleaning, make sure the required variables are specified.
ifneq ($(MAKECMDGOALS),clean)

  ifndef RELEASE_VERSION
    $(error RELEASE_VERSION not set)
  endif

  ifndef BSEC_DIR
    $(error BSEC_DIR is not specified. This must point to where the Bosch bsec library is located)
  endif

endif

TARGETS ?= wp77xx
#TARGETS ?= wp76xx wp77xx

# Manifest branch to check out for the meta-mangoh Yocto layer.
# This is used by the fetch_yocto script when building for non-wp77 targets.
export MANGOH_YOCTO_BRANCH ?= master

# Git reference to check out in the mangOH project main source repository.
export MANGOH_REF ?= master

# Modem firmware release version number.
wp76xx_MODEM_RELEASE_VERSION ?= 13.3
wp77xx_MODEM_RELEASE_VERSION ?= 12

# The leaf package identifier for the package containing the modem firmware image.
wp76xx_MODEM_LEAF_PACKAGE ?= wp76-modem-image_$(wp76xx_MODEM_RELEASE_VERSION)
wp77xx_MODEM_LEAF_PACKAGE ?= wp77-modem-image_$(wp77xx_MODEM_RELEASE_VERSION)

# The release version of Legato to use.
export LEGATO_VERSION ?= 20.04.0

# The reference to check out in the Octave edge package source repository.
# Octave tag their fork of the mangOH repository, not their brkedge repo, so do this:
# $ git clone https://github.com/flowthings/mangOH.git /tmp/mangOH_Octave
# $ pushd /tmp/mangOH_Octave
# $ git ls-tree [OCTAVE_TAG] apps/Brooklyn | cut -d " " -f 3 | cut -f 1
# $ popd
#
export OCTAVE_REF ?= f8ca3f7b19317f270a504a94708c29d4eab0c443
OCTAVE_VERSION = 3.0.0-pre23April2020-mangOH-0

# All build artifacts will appear under here, including source code that fetched from other
# repositories.
BUILD_DIR = $(CURDIR)/build

# Directory in which the built leaf remote repository will be put.
LEAF_PACKAGE_REPO = $(BUILD_DIR)/leaf/remote

# Directory in which leaf packages will be assembled in preparation for packing.
LEAF_STAGING_DIR = $(BUILD_DIR)/leaf/staging

# Directory under which toolchain leaf packages will be staged for packing.
LEAF_TOOLCHAIN_DIR = $(LEAF_STAGING_DIR)/toolchain

# Directory under which linux leaf packages will be staged for packing.
LEAF_LINUX_DIR = $(LEAF_STAGING_DIR)/linux

# Only works for yellow right now.
export MANGOH_BOARD ?= yellow

# The directory in which the Legato sources will be cloned and built.
export LEGATO_ROOT = $(BUILD_DIR)/legato/legato

# The directory in which the mangOH sources will be cloned and built.
export MANGOH_ROOT = $(BUILD_DIR)/mangOH

# The directory in which the Octave app sources will be cloned and built.
export OCTAVE_ROOT = $(BUILD_DIR)/brkedgepkg

# The directory in which the toolchain will be installed.
TOOLCHAIN_INSTALL_DIR = $(BUILD_DIR)/toolchain

export WP77XX_TOOLCHAIN_DIR=$(TOOLCHAIN_INSTALL_DIR)/wp77xx/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi
export WP77XX_SYSROOT=$(TOOLCHAIN_INSTALL_DIR)/wp77xx/sysroots/armv7a-neon-poky-linux-gnueabi
export WP77XX_TOOLCHAIN_PREFIX=arm-poky-linux-gnueabi-

export WP76XX_TOOLCHAIN_DIR=$(TOOLCHAIN_INSTALL_DIR)/wp76xx/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi
export WP76XX_SYSROOT=$(TOOLCHAIN_INSTALL_DIR)/wp76xx/sysroots/armv7a-neon-poky-linux-gnueabi
export WP76XX_TOOLCHAIN_PREFIX=arm-poky-linux-gnueabi-

# List of leaf packages that will be built and included in the remote repository that will be
# generated by the build.
LEAF_PACKAGES = \
				$(TOOLCHAIN_LEAF_PACKAGES) \
				$(LINUX_LEAF_PACKAGES) \
				$(TOP_LEVEL_LEAF_PACKAGES) \
				$(LEGATO_BIN_LEAF_PACKAGES) \
				$(OCTAVE_APPS_LEAF_PACKAGES)

LINUX_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target)-linux.leaf)
TOOLCHAIN_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target)-toolchain.leaf)
OCTAVE_APPS_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/Octave-mangOH-$(MANGOH_BOARD)-$(target).leaf)
TOP_LEVEL_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target).leaf)
LEGATO_BIN_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(target)-legato.leaf)

# Following are hidden files in the build directory each of whose existence is used to
# flag whether or not a given build was step successfully completed.
YOCTO_BUILT = $(foreach target,$(TARGETS),$(BUILD_DIR)/.yocto_$(target)_built)
TOOLCHAIN_INSTALLED = $(foreach target,$(TARGETS),$(BUILD_DIR)/.toolchain_$(target)_installed)
LEGATO_SOURCES_FETCHED = $(BUILD_DIR)/.legato_sources_fetched
LEGATO_BUILT = $(foreach target,$(TARGETS),$(BUILD_DIR)/.legato_$(target)_built)
OCTAVE_SOURCES_FETCHED = $(BUILD_DIR)/.octave_sources_fetched
OCTAVE_APPS_BUILT = $(foreach target,$(TARGETS),$(BUILD_DIR)/.octave_apps_$(target)_built)
MODEM_FIRMWARE_FETCHED = $(foreach target,$(TARGETS),$(BUILD_DIR)/.$(target)_modem_firmware_fetched)
MANGOH_SOURCES_FETCHED = $(BUILD_DIR)/.mangoh_sources_fetched
MANGOH_SPK_BUILT = $(foreach target,$(TARGETS),$(BUILD_DIR)/.mangoh_spk_$(target)_built)
LEAF_REMOTE_BUILT = $(BUILD_DIR)/.leaf_remote_built

# Variables that need to be set in the environment to "sandbox" leaf (i.e., to make sure
# leaf doesn't change the user's leaf configuration and to make sure that the user's leaf
# configuration doesn't contaminate the release).
export LEAF_CONFIG = $(BUILD_DIR)/leaf/config
export LEAF_CACHE = $(BUILD_DIR)/leaf/cache
export LEAF_USER_ROOT = $(BUILD_DIR)/leaf/installed-packages

# Rule for building a release candidate.
# NOTE: This is the default goal.
.PHONY: candidate
candidate: $(MANGOH_SPK_BUILT) $(LEAF_REMOTE_BUILT)

# Rule for building the mangOH leaf remote package repository.
$(LEAF_REMOTE_BUILT): $(LEAF_PACKAGES)
	leaf build index -o $(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD).json $(LEAF_PACKAGES)

# Rule for generating the factory .spk file.
$(MANGOH_SPK_BUILT): $(BUILD_DIR)/.mangoh_spk_%_built: $(MANGOH_SOURCES_FETCHED) $(OCTAVE_APPS_BUILT) $(LEGATO_BUILT) $(MODEM_FIRMWARE_FETCHED)
	# With Octave
	cd $(MANGOH_ROOT) && \
		source $(LEGATO_ROOT)/build/$*/config.sh && \
		$(MAKE) $(MANGOH_BOARD)_spk \
			LEGATO_TARGET=$* \
			OCTAVE_ROOT=$(OCTAVE_ROOT)/build \
			BOOTLOADER_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/appsboot_rw_$*.cwe \
			LINUX_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_$*.4k.cwe \
			MODEM_FIRMWARE=$(wildcard $(LEAF_USER_ROOT)/$($*_MODEM_LEAF_PACKAGE)/*SIERRA*)
	cp $(MANGOH_ROOT)/build/$(MANGOH_BOARD)_$*.spk $(BUILD_DIR)/$(MANGOH_BOARD)_$*_$(RELEASE_VERSION)-octave.spk
	# Without Octave
	cd $(MANGOH_ROOT) && \
		make clean && \
		source $(LEGATO_ROOT)/build/$*/config.sh && \
		$(MAKE) $(MANGOH_BOARD)_spk \
			LEGATO_TARGET=$* \
			OCTAVE=0 \
			BOOTLOADER_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/appsboot_rw_$*.cwe \
			LINUX_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_$*.4k.cwe \
			MODEM_FIRMWARE=$(wildcard $(LEAF_USER_ROOT)/$($*_MODEM_LEAF_PACKAGE)/*SIERRA*)
	cp $(MANGOH_ROOT)/build/$(MANGOH_BOARD)_$*.spk $(BUILD_DIR)/$(MANGOH_BOARD)_$*_$(RELEASE_VERSION).spk
	touch $@

# Rules for fetching the mangOH source code.
$(MANGOH_SOURCES_FETCHED):
	rm -rf $(MANGOH_ROOT)
	mkdir -p $(BUILD_DIR)
	git clone https://github.com/mangOH/mangOH $(MANGOH_ROOT)
	cd $(MANGOH_ROOT) && git checkout $(MANGOH_REF)
	cd $(MANGOH_ROOT) && git submodule update --init --recursive
	touch $@

# Rule for building the Legato sources.
$(LEGATO_BUILT): $(BUILD_DIR)/.legato_%_built: $(LEGATO_SOURCES_FETCHED) $(TOOLCHAIN_INSTALLED)
	make -C $(LEGATO_ROOT) $*
	touch $@

# Rule for fetching the Legato sources.
$(LEGATO_SOURCES_FETCHED):
	rm -rf $(BUILD_DIR)/legato
	mkdir -p $(BUILD_DIR)/legato
	cd $(BUILD_DIR)/legato && repo init -u ssh://gerrit.legato:29418/manifest.git -m legato/releases/$(LEGATO_VERSION).xml
	cd $(BUILD_DIR)/legato && repo sync
	# Cherry pick newer changes that we need.

	# LE-14509: [AVC] Incorrect fd closure order during disconnection from the AV server
	cd $(LEGATO_ROOT)/apps/platformServices/airVantageConnector && \
		git cherry-pick 3998b243fb0426e3ae667d3e7dd3d535b3b4154a
	# LE-14639: [Octave][CoAP]AV does not reply to CoAP retry on CoAP data for application
	cd $(LEGATO_ROOT)/3rdParty/Lwm2mCore && \
		git fetch ssh://gerrit.legato:29418/lwm2mCore refs/changes/62/60162/1 && \
		git cherry-pick FETCH_HEAD
	cd $(LEGATO_ROOT)/3rdParty/Lwm2mCore/3rdParty/wakaama && \
		git fetch ssh://gerrit.legato:29418/external/eclipse/wakaama refs/changes/63/60163/1 && \
		git cherry-pick FETCH_HEAD
	# LE-14672: [AVC][LwM2M] Server initiated is not working
	cd $(LEGATO_ROOT)/3rdParty/Lwm2mCore && \
		git fetch ssh://gerrit.legato:29418/lwm2mCore refs/changes/38/60738/2 && \
		git cherry-pick FETCH_HEAD
	cd $(LEGATO_ROOT)/3rdParty/Lwm2mCore/3rdParty/tinydtls && \
		git fetch ssh://gerrit.legato:29418/external/eclipse/tinydtls refs/changes/39/60739/1 && \
		git cherry-pick FETCH_HEAD
	touch $@

# Rules for building the Octave apps.
$(OCTAVE_APPS_BUILT): $(BUILD_DIR)/.octave_apps_%_built: $(OCTAVE_SOURCES_FETCHED) $(LEGATO_BUILT)
	cd $(BUILD_DIR)/brkedgepkg && \
		source $(LEGATO_ROOT)/build/$*/config.sh && \
		make DHUB_ROOT=$(MANGOH_ROOT)/apps/DataHub LEGATO_TARGET=$* PATH=$(PATH):$(LEGATO_ROOT)/bin VERSION=$(OCTAVE_VERSION)
	touch $@

# Rules for fetching the Octave apps source code.
# Unfortunately, this can only be done by someone inside Sierra Wireless. :(
$(OCTAVE_SOURCES_FETCHED):
	rm -rf $(OCTAVE_ROOT)
	git clone https://github.com/flowthings/brkedgepkg $(OCTAVE_ROOT)
	cd $(OCTAVE_ROOT) && git checkout $(OCTAVE_REF)
	cd $(OCTAVE_ROOT) && git submodule update --init --recursive
	touch $@

# Rules for fetching the modem firmware.
# NOTE: This uses leaf to install the leaf package under $(LEAF_USER_ROOT).
$(MODEM_FIRMWARE_FETCHED): $(BUILD_DIR)/.%_modem_firmware_fetched: leaf_sandbox
	yes | leaf package install $($*_MODEM_LEAF_PACKAGE)

# All leaf package builds depend on the remote repository directory being there first.
$(LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)

# Rule to create the leaf package repository directory.
$(LEAF_PACKAGE_REPO):
	mkdir -p $(LEAF_PACKAGE_REPO)

# Rule for installing toolchains.
$(TOOLCHAIN_INSTALLED): $(BUILD_DIR)/.toolchain_%_installed: $(TOOLCHAIN_LEAF_PACKAGES)
	-chmod -R u+w $(TOOLCHAIN_INSTALL_DIR)/$*
	rm -rf $(TOOLCHAIN_INSTALL_DIR)/$*
	mkdir -p $(TOOLCHAIN_INSTALL_DIR)/$*
	$(LEAF_TOOLCHAIN_DIR)/$*/toolChainExtractor.sh -y -d $(TOOLCHAIN_INSTALL_DIR)/$*/
	touch $@

# Rule for building the leaf packages for the toolchains.
$(TOOLCHAIN_LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-%-toolchain.leaf: $(BUILD_DIR)/.yocto_%_built
	rm -rf $(LEAF_TOOLCHAIN_DIR)/$*
	mkdir -p $(LEAF_TOOLCHAIN_DIR)/$*
	cp toolchainManifest.json $(LEAF_TOOLCHAIN_DIR)/$*/manifest.json
	VERSION=$(RELEASE_VERSION) TARGET=$* ./replaceVars $(LEAF_TOOLCHAIN_DIR)/$*/manifest.json
	cp $(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/sdk/poky-swi-ext-glibc-x86_64-meta-toolchain-swi-armv7a-neon-toolchain-swi-*.sh \
		$(LEAF_TOOLCHAIN_DIR)/$*/toolChainExtractor.sh
	leaf build pack -o $@ -i $(LEAF_TOOLCHAIN_DIR)/$*

# Rule for building the leaf packages for the linux images.
$(LINUX_LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-%-linux.leaf: $(BUILD_DIR)/.yocto_%_built
	rm -rf $(LEAF_LINUX_DIR)/$*
	mkdir -p $(LEAF_LINUX_DIR)/$*
	cp linuxManifest.json $(LEAF_LINUX_DIR)/$*/manifest.json
	VERSION=$(RELEASE_VERSION) TARGET=$* ./replaceVars $(LEAF_LINUX_DIR)/$*/manifest.json
	cp $(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_$*.4k.cwe \
		$(LEAF_LINUX_DIR)/$*/linux.cwe
	leaf build pack -o $@ -i $(LEAF_LINUX_DIR)/$*

# Rule for building the master (top-level) leaf package.
MASTER_LEAF_DIR = $(BUILD_DIR)/leaf/staging/master/mangOH-$(MANGOH_BOARD)-$*
$(TOP_LEVEL_LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-%.leaf:
	rm -rf $(MASTER_LEAF_DIR)
	mkdir -p $(MASTER_LEAF_DIR)
	cp mangOH-$(MANGOH_BOARD)-Manifest.json $(MASTER_LEAF_DIR)/manifest.json
	VERSION=$(RELEASE_VERSION) \
		TARGET=$* \
		OCTAVE_VERSION=$(OCTAVE_VERSION) \
		MODEM_LEAF_PACKAGE=$($*_MODEM_LEAF_PACKAGE) \
		MODEM_RELEASE_VERSION=$($*_MODEM_RELEASE_VERSION) \
		./replaceVars $(MASTER_LEAF_DIR)/manifest.json
	leaf build pack -o $@ -i $(MASTER_LEAF_DIR)

# Rule for building the pre-built Legato leaf package.
LEGATO_LEAF_DIR = $(BUILD_DIR)/leaf/staging/legato/mangOH-$*-legato
$(LEGATO_BIN_LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)/mangOH-%-legato.leaf:
	rm -rf $(LEGATO_LEAF_DIR)
	mkdir -p `dirname $(LEGATO_LEAF_DIR)`
	cp -r $(LEGATO_ROOT) $(LEGATO_LEAF_DIR)
	rm -rf $(LEGATO_LEAF_DIR)/.git
	cp legatoManifest.json $(LEGATO_LEAF_DIR)/manifest.json
	VERSION=$(RELEASE_VERSION) TARGET=$* ./replaceVars $(LEGATO_LEAF_DIR)/manifest.json
	leaf build pack -o $@ -i $(LEGATO_LEAF_DIR)

# Rule for building the pre-built Octave apps leaf package.
OCTAVE_BUILD_DIR = $(OCTAVE_ROOT)/build
OCTAVE_LEAF_FILE_NAME = $(shell dirname $@)
$(OCTAVE_APPS_LEAF_PACKAGES): $(LEAF_PACKAGE_REPO)/%:
	cp $(OCTAVE_BUILD_DIR)/$* $@
	cp $(OCTAVE_BUILD_DIR)/$*.info $@.info

# Rule for building Yocto toolchains and .cwe files.
YOCTO_BUILD_DIR = $(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*
$(YOCTO_BUILT): $(BUILD_DIR)/.yocto_%_built:
	mkdir -p $(YOCTO_BUILD_DIR)
	./fetch_yocto $* $(YOCTO_BUILD_DIR)
	# NOTE: For some reason 'make -C' doesn't work for the Yocto build. Must cd && make.
	cd $(YOCTO_BUILD_DIR) && $(MAKE) image_bin
	cd $(YOCTO_BUILD_DIR) && $(MAKE) toolchain_bin
	touch $@

# Rule to make the directories needed for leaf sandboxing.
.PHONY: leaf_sandbox
leaf_sandbox:
	mkdir -p $(LEAF_CACHE)
	mkdir -p $(LEAF_CONFIG)
	mkdir -p $(LEAF_USER_ROOT)

.PHONY: clean
clean:
	-chmod -R u+w $(TOOLCHAIN_INSTALL_DIR)
	rm -rf $(BUILD_DIR)
