# mangOH Software Configuration Management Makefile
#
# This codifies the rules for building and tagging mangOH release candidates and releases.
#
# TODO: Add tagging.
# TODO: Add Octave fetch commit ID or convert to using submodules.
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
#	MODEM_FIRMWARE  = file system path of the .spk or .cwe file containing the modem firmware to
#                     be packaged into the full factory .spk generated by this script.
#	                  WARNING: Do not use the full product release .spk. It contains too much stuff.
#	                  E.g., MODEM_FIRMWARE=~/firmware/9999999_9908788_SWI9X06Y_02.31.04.00_00_SIERRA_001.023_000.spk
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

  ifndef MODEM_FIRMWARE
    $(error MODEM_FIRMWARE not set. Set it to the path of the modem .spk or .cwe file)
  endif

endif

#TARGETS ?= wp76xx wp77xx
TARGETS ?= wp77xx

# Version of the WP77 Yocto release upon which the mangOH WP77 toolchain and linux image will
# be based.
export WP77_RELEASE_VER ?= SWI9X06Y_02.32.02.00

# Manifest branch to check out for the meta-mangoh Yocto layer.
# This is used by the fetch_yocto script when building for non-wp77 targets.
export MANGOH_YOCTO_BRANCH ?= master

# Git reference to check out in the mangOH project main source repository.
export MANGOH_REF ?= master

# The release version of Legato to use.
export LEGATO_VERSION ?= 19.07.0

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

#				$(OCTAVE_APPS_LEAF_PACKAGES) \
#				mangOH-src

LINUX_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target)-linux.leaf)
TOOLCHAIN_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target)-toolchain.leaf)
OCTAVE_APPS_LEAF_PACKAGES = $(foreach target,$(TARGETS),$(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD)-$(target)-octave.leaf)
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
MANGOH_SOURCES_FETCHED = $(BUILD_DIR)/.mangoh_sources_fetched
MANGOH_SPK_BUILT = $(foreach target,$(TARGETS),$(BUILD_DIR)/.mangoh_spk_$(target)_built)
LEAF_REMOTE_BUILT = $(BUILD_DIR)/.leaf_remote_built

# Rule for building a release candidate.
# NOTE: This is the default goal.
.PHONY: candidate
candidate: $(MANGOH_SPK_BUILT) $(LEAF_REMOTE_BUILT)

# Rule for building the mangOH leaf remote package repository.
$(LEAF_REMOTE_BUILT): $(LEAF_PACKAGES)
	leaf build index -o $(LEAF_PACKAGE_REPO)/mangOH-$(MANGOH_BOARD).json $(LEAF_PACKAGES)

# Rule for generating the factory .spk file.
$(MANGOH_SPK_BUILT): $(BUILD_DIR)/.mangoh_spk_%_built: $(MANGOH_SOURCES_FETCHED) $(OCTAVE_APPS_BUILT) $(LEGATO_BUILT)
	cd $(MANGOH_ROOT) && \
		source $(LEGATO_ROOT)/build/$*/config.sh && \
		$(MAKE) $(MANGOH_BOARD)_spk \
			LEGATO_TARGET=$* \
			OCTAVE_ROOT=$(OCTAVE_ROOT)/build \
			BOOTLOADER_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/appsboot_rw_$*.cwe \
			LINUX_IMAGE=$(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*/build_bin/tmp/deploy/images/swi-mdm9x28-wp/yocto_$*.4k.cwe
	cp $(MANGOH_ROOT)/build/$(MANGOH_BOARD)_$*.spk $(BUILD_DIR)/$(MANGOH_BOARD)_$*_$(RELEASE_VERSION).spk
	touch $@

# Rules for fetching the mangOH source code.
$(MANGOH_SOURCES_FETCHED):
	rm -rf $(MANGOH_ROOT)
	mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && git clone --recursive https://github.com/mangOH/mangOH
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
	# 49737 = size reduction by removing curl, zlib and openssl from apps.
	# 49773 = make symlinks in the bin directory relative instead of absolute.
	# 50657 = remove excessive warning messages in syslog due to failure to open an NMEA pipe
	cd $(LEGATO_ROOT) && \
		git fetch ssh://gerrit.legato:29418/Legato refs/changes/37/49737/1 && \
		git cherry-pick FETCH_HEAD && \
		git fetch ssh://gerrit.legato:29418/Legato refs/changes/73/49773/1 && \
		git cherry-pick FETCH_HEAD && \
		git fetch ssh://gerrit.legato:29418/Legato refs/changes/57/50657/1 && \
		git cherry-pick FETCH_HEAD
	touch $@

# Rules for building the Octave apps.
$(OCTAVE_APPS_BUILT): $(BUILD_DIR)/.octave_apps_%_built: $(OCTAVE_SOURCES_FETCHED) $(LEGATO_BUILT)
	cd $(BUILD_DIR)/brkedgepkg && \
		source $(LEGATO_ROOT)/build/$*/config.sh && \
		make DHUB_ROOT=$(MANGOH_ROOT)/apps/DataHub LEGATO_TARGET=$* PATH=$(PATH):$(LEGATO_ROOT)/bin
	touch $@

# Rules for fetching the Octave apps source code.
$(OCTAVE_SOURCES_FETCHED): $(LEAF_WORKSPACE_CREATED)
	rm -rf $(OCTAVE_ROOT)
	cd $(BUILD_DIR) && git clone --recursive https://github.com/flowthings/brkedgepkg
	touch $@

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
	VERSION=$(RELEASE_VERSION) TARGET=$* ./replaceVars $(MASTER_LEAF_DIR)/manifest.json
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

# Rule for building Yocto toolchains and .cwe files.
YOCTO_BUILD_DIR = $(BUILD_DIR)/yocto-$(MANGOH_BOARD)-$*
$(YOCTO_BUILT): $(BUILD_DIR)/.yocto_%_built:
	mkdir -p $(YOCTO_BUILD_DIR)
	./fetch_yocto $* $(YOCTO_BUILD_DIR)
	# NOTE: For some reason 'make -C' doesn't work for the Yocto build. Must cd && make.
	cd $(YOCTO_BUILD_DIR) && $(MAKE) image_bin
	cd $(YOCTO_BUILD_DIR) && $(MAKE) toolchain_bin
	touch $@

.PHONY: clean
clean:
	-chmod -R u+w $(TOOLCHAIN_INSTALL_DIR)
	rm -rf $(BUILD_DIR)
