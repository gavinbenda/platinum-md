# Platinum-MD

> A Gui for NetMD

![Screenshot](https://i.imgur.com/GdmUdYP.png)

#### Dependancies

This is quite tricky, as there are a few extras needed.

Future releases will try and include a statically built binary for each included tool.

You will need to install homebrew: https://docs.brew.sh/Installation

`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

Then install the following:

`brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg && brew link --force qt5`

#### Installation

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases), and open the dmg.

Drag the file to the applications folder.

Upon opening the `platinum-md` app from the applications folder, it will show a warning.

Open OSX `Settings` and click `Security & Privacy` - click the `Open Anyway` button shown near the bottom of the panel.

## Overview

This project aims to make uploading audio files to NetMD players seamless and automatic.

## Features

Supports upload MP3/WAV/FLAC files direct to a compatible NetMD recorder.

Full quality SP recording.

LP2 with an experimental encoder


## Release Notes

This is a very alpha release, expect bugs.

## Known bugs / future Plans

* Some pre-recorded discs made with SonicStage may show as blank
* Best to start with a completely blank disc
* Bulk delete is not supported yet, but will be soon
* ~~Moving tracks is also not supported, but also will be very soon~~
* Sometimes a track or two may be missed, this is likely a race-condtion, will be fixed in the next release
* Automatic CLI tools for installing dependancies is highly desirable
* Linux release is imminent, starting with Ubuntu
* Windows release is a way off, sorry
* The USB interface sometimes just fails, this is hard to fix as it seems to be the device itself (just unplug/plug-in again)
* LP4 is unsupported (relies on support from a 3rd party library)
* LP2 is experimental, but works fairly well
* SP is full-quality PCM and is encoded by the NetMD device itself for best quality

## Thanks

The Linux-Minidisc project (this is the most up-to-date Fork I've found, but there are many contributers):

<https://github.com/vuori/linux-minidisc/>

The ATRAC Encoder by @dcherednik

<https://github.com/dcherednik/atracdenc>
