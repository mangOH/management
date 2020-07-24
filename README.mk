Usage
=====

To build a full release including all supported combinations of boards and modules,

1.	Create a new release JSON file under `release_specs/<version>.json`.
2. 	Run `./mangoh_release.py release_specs/<version>.json`

When complete, the output will be found under `build/leaf/remote`.

It will have an index file called `mangOH.json`, so you can add that as a leaf remote
and test the packages.

	leaf remote add release_1.2.3-rc1_test file://$HOME/release_build/1.2.3-rc1/build/leaf/remote/mangOH.json
	mkdir test_dir
	cd test_dir
	leaf setup -p mangOH-yellow-wp76xx_1.2.3-rc1
	leaf shell
	git clone --recursive https://github.com/mangOH/mangOH
	cd mangOH
	make yellow

Specification File Format
=========================

The specification format is a JSON object.  Each subsection below describes a member of
that object.

mangoh
------

Specifies details of the mangOH release.

	"mangoh": {
		"ref": "646592902e6d5d748560a60da7e3db0c0f57b360",
		"wget": [
			{
				"url": "https://community.bosch-sensortec.com/varuj77995/attachments/varuj77995/bst_community-mems-forum/44/1/BSEC_1.4.7.2_GCC_CortexA7_20190225.zip",
				"dir": "components/boschBsec",
				"unpack": "unzip"
			}
		],
		"requires": [
			"swi-license_1.2",
			"swi-verify-license_latest"
		],
		"depends": [
			"swi-legato_latest",
			"swi-vscode-support_latest"
		]
	}

"ref" contains the git ref to be checked out from the main mangOH repository (MANGOH_MAIN_REPO)
when fetching the mangOH source code.

"wget" is an optional member, which directs the build to use wget to download
a list of files under the MANGOH_ROOT directory and optionally unpack them.
The "wget" member is an array of objects. Each of those objects must have a "url" member
and a "dir" member (which is a relative path from MANGOH_ROOT of a directory into which
the file will be downloaded. If an "unpack" member is present, it specifies the method to
be used to unpack the downloaded file. Presently, only "unzip" is supported.

"requires" is a list of leaf packages to be added to the "requires" section of all generated
SDK master leaf packages.

"depends" is a list of leaf packages to be added to the "depends" section of all generated
SDK master leaf packages.

legato
------

Specifies the Legato source to fetch using Google's "repo" tool, as well as optional patches to
apply to the Legato source code before building it.

	"legato": {
		"manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
		"base_manifest": "legato/releases/20.04.0/legato.xml",
		"patches": [
			{
				"purpose": "LE-14705: Fix SecStore to enable recovery from corrupted keys file.",
				"dir": ".",
				"cherry_pick": "f9cc1f29d4b36e9999d3365a2ecf85e358eb4efd"
			},
			{
				"purpose": "LE-14639: [Octave][CoAP]AV does not reply to CoAP retry on CoAP data for application",
				"dir": "3rdParty/Lwm2mCore/3rdParty/wakaama",
				"gerrit_review": {
					"project": "external/eclipse/wakaama",
					"patch_set": "63/60163/1"
				}
			}
		]
	}

"manifest_repo" is a string containing the URL of the repo manifest repository.

"base_manifest" is the path to the manifest XML file within the manifest repository.

"patches" is an array of objects. All such objects must have a "dir" member containing a
the path to the directory under LEGATO_ROOT at which the patch should be applied.
The "purpose" member is an optional string used as a human-readable comment to document
the reason why the patch is being applied.

In addition to "dir", all objects in the "patches" array must have either a "cherry_pick"
member or a "gerrit_review" member.

The "cherry_pick" member is used when a fix is needed that has passed review and been submitted
to the Legato master, but that was not included in the version of Legato that is checked out
by the base manifest. This is typically needed to patch up known issues that have been fixed
but have not yet made it into a Legato release. If the "cherry_pick" member is used, it must
contain the git commit ID of a commit to be git cherry-picked into the HEAD from the same
repository.

The "gerrit_review" member is used when the patch required has not yet even passed review in
Sierra Wireless's internal Gerrit instance. This is intended for emergency use only.
The "gerrit_review" member is an object with two members:
 - "project" specifies the Gerrit project name to fetch from within Sierra Wireless's internal
   Gerrit.
 - "patch_set" identifies the Gerrit patch set to fetch and cherry-pick.

octave
------

	"octave": {
		"ref": "BROOKLYN-2626_fix_makefile",
		"version": "3.0.0.pre03Jun2020-mangOH-1"
	}

Specifies the Octave Edge Package git repository ref to fetch and checkout when building Octave
into the release. Also specifies the version string that is to be reported to the Octave cloud
to ensure that the Octave cloud knows (and uses) the correct set of capabilities of the
device's Octave Edge Package apps.

boards
------

Specifies all board + module combinations to be built for, and what component parts need to
be included in those builds.

	"boards": {
		"yellow": {
			"wp76xx": {
				"depends": [
					"wp76-modem-image_13.3"
				],
				"modem_firmware": "9999999_9908787_SWI9X07Y_02.28.03.05_00_SIERRA_001.032_000.spk",
				"yocto": {
					"manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
					"base_manifest": "mdm9x28/tags/SWI9X07Y_02.37.07.00.xml",
					"add": [
						{
							"url": "https://github.com/mangOH/meta-mangoh",
							"ref": "mdev_update_for_ecm",
							"dir": "meta-mangoh"
						}
					]
				}
			},
			"wp77xx": {
			   "depends": [
				   "wp77-modem-image_12"
			   ],
			   "modem_firmware": "9999999_9908788_SWI9X06Y_02.32.02.00_00_SIERRA_001.027_000.spk",
				"yocto": {
					"manifest_repo": "https://github.com/mangOH/manifest.git",
					"base_manifest": "mangOH/releases/v0.6.0/wp77xx.xml"
				}
			}
		},
		"red": {
			"wp85": {
				"depends": [
					"wp85-toolchain_SWI9X15Y_07.14.01.00-linux64",
					"wp85-linux-image_SWI9X15Y_07.14.01.00",
					"wp85-modem-image_17"
				],
				"modem_firmware": "9999999_9904559_SWI9X15Y_07.14.01.00_00_GENERIC_001.042_000.spk"
			}
		}
	}

"boards" is an object in which each member it an object that represents a single board, such
as "red" or "yellow". The name of the member is the name of the board, and the value of the
member is an object whose members represent modules, such as Sierra Wireless WP76xx.

The name of the module member must be the legato build "target" name, such as "wp85" or "wp76xx".

### depends

All modules must have a "depends" member, which is a list of all the leaf packages to be
installed in the workspace when building for this module on this board. These leaf packages
will also be added to the "depends" list within the mangOH SDK master leaf package for this
particular board + module combination.

	"depends": [
		"wp85-toolchain_SWI9X15Y_07.14.01.00-linux64",
		"wp85-linux-image_SWI9X15Y_07.14.01.00",
		"wp85-modem-image_17"
	],

### modem_firmware

The "modem_firmware" member specifies the name of the modem firmware SPK file from which
the modem firmware files will be extracted for inclusion in the final release SPK file.

    "modem_firmware": "9999999_9908787_SWI9X07Y_02.28.03.05_00_SIERRA_001.032_000.spk",

### yocto

A "yocto" member can (optionally) be added when a custom Yocto linux distribution must be
built for this module on this board.  It specifies the Gerrit manifest repository URL and
the path to the manifest XML file within that repository that is to be used to fetch the
Yocto sources.

    "yocto": {
        "manifest_repo": "ssh://master.gerrit.legato:29418/manifest.git",
        "base_manifest": "mdm9x28/tags/SWI9X07Y_02.37.07.00.xml",
        "add": [
            {
                "url": "https://github.com/mangOH/meta-mangoh",
                "ref": "mdev_update_for_ecm",
                "dir": "meta-mangoh"
            }
        ]
    }

The "add" member within the "yocto" object is optional. It can be used to specify a list
of other Git repositories that need to be cloned and checked out into the Yocto source tree
before it is built. The "dir" path is relative to the root of the Yocto source tree.
