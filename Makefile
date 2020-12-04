# mangOH Software Configuration Management Makefile
#
# This codifies the rules for building, tagging and publishing mangOH release candidates and
# releases.
#
# TODO: Add tagging.
#
# The primary build output is a set of leaf packages, including factory programming image (.spk)
# files, toolchains, linux images, and Legato framework sources and pre-built binary images.
#
# Copyright (C) Sierra Wireless Inc.

# If we're not cleaning, make sure the required variables are specified.
ifneq ($(MAKECMDGOALS),clean)

  ifndef RELEASE_VERSION
    $(error RELEASE_VERSION not set)
  endif

endif

BUILD_DIR = build
BUILD_OUTPUT_DIR = $(BUILD_DIR)/leaf/remote
INDEX_STAGING_DIR = $(BUILD_DIR)/leaf/staging/index

# Builds the release.
.PHONY: build
build:
	./mangoh_release.py release_specs/$(RELEASE_VERSION).json

# Download the entire existing mangOH leaf remote from Akamai, add the new release to it, and
# re-generate the index.
.PHONY: index
index:
	mkdir -p $(INDEX_STAGING_DIR)
	scp -r 'sierra.upload.akamai.com:mangOH/leaf/*' "$(INDEX_STAGING_DIR)"
	@if [ -e "$(INDEX_STAGING_DIR)/$(RELEASE_VERSION)" ]; \
	then \
		echo "**ERROR: $(INDEX_STAGING_DIR)/$(RELEASE_VERSION) already exists."; \
		exit 1; \
	fi
	cp -r "$(BUILD_OUTPUT_DIR)" "$(INDEX_STAGING_DIR)/$(RELEASE_VERSION)"
	cd "$(INDEX_STAGING_DIR)" && find -name '*.leaf' | xargs leaf build index -o mangOH.json

# Publish the release's leaf packages and the new index to the mangOH leaf remote on Akamai.
.PHONY: publish
publish: index
	scp -r "$(INDEX_STAGING_DIR)/$(RELEASE_VERSION)" "sierra.upload.akamai.com:mangOH/leaf/$(RELEASE_VERSION)"
	scp "$(INDEX_STAGING_DIR)/mangOH.json" "sierra.upload.akamai.com:mangOH/leaf/"

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
