# Platinum-MD

> A Gui for NetMD

![Screenshot](https://i.imgur.com/GdmUdYP.png)

#### Dependancies

##### OSX

You will need to install homebrew: https://docs.brew.sh/Installation

`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

Then install the following:

`brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg && brew link --force qt5`

##### Windows

You will need to use Zadig to install the WinUSB Driver.
Connect your NetMD device, open the app and click the "Install Driver" button.
Please note, this will disable Sonic Stage from having access to the device, you'll need to run Zadig and 'reinstall' the old driver to use it again.

https://zadig.akeo.ie/

##### Linux

Note: This has only been tested on Ubuntu.

Run `apt-get install libgcrypt20-dev libglib2.0-dev libusb-1.0-0-dev qt4-qmake libid3tag0-dev libmad0-dev`

You will also likely need to allow your user permissions to the USB/NetMD Device.
This is a 'catch-all' but you may wish to add a specific deviceId/vendorId if you want to lock permissions down.
`sudo nano /etc/udev/rules.d/50-device.rules` and add `SUBSYSTEM=="usb", GROUP="YOURUSERGROUPHERE"`

#### Installation

##### OSX

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v0.7.0-alpha/platinum-md-0.7.0.dmg), and open the dmg.

Drag the file to the applications folder.

Upon opening the `platinum-md` app from the applications folder, it will show a warning.

Open OSX `Settings` and click `Security & Privacy` - click the `Open Anyway` button shown near the bottom of the panel.

##### Windows

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v0.7.0-alpha/platinum-md.Setup.0.7.0.exe), and open the platinum-md .exe Setup file.

Run the installer, don't forget to run Zadig above.

##### Linux

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v0.7.0-alpha/platinum-md-0.7.0.AppImage), and open the platinum-md AppImage Setup file.


## Overview

This project aims to make uploading audio files to NetMD players seamless and automatic.

## Features

Supports upload MP3/WAV/FLAC files direct to a compatible NetMD recorder.

Full quality SP recording.

LP2/LP4 with an experimental encoder


## Release Notes

This is a very alpha release, expect bugs.

## FAQ / Troubleshooting

* Make sure you have a disk in the device before connecting.
* If the interface shows "Negotiating with device" but won't connect, click the `retry` button.
* To access debug information, click `settings` and click the `debug window` button.
* Some discs origionally made with SonicStage may not allow for tracks to be deleted by Platinum-MD.
* Windows anti-virus software may sometimes incorrectly mark the app as a positive.
* If using a Hi-MD device, ensure that the device is set to `MD` mode (mainly if using a blank disc) `Option` then `Disc Mode` and select `md`.

## Known bugs / future Plans

* Some pre-recorded discs made with SonicStage may show as blank
* ~~Bulk delete is not supported yet, but will be soon~~
* ~~Moving tracks is also not supported, but also will be very soon~~
* ~~Sometimes a track or two may be missed, this is likely a race-condtion, will be fixed in the next release~~
* Automatic CLI tools for installing dependancies is highly desirable
* ~~Linux release is imminent, starting with Ubuntu~~
* ~~Windows release is a way off, sorry~~
* The USB interface sometimes just fails, this is hard to fix as it seems to be the device itself (just unplug/plug-in again)
* ~~LP4 is unsupported (relies on support from a 3rd party library)~~
* LP2 is experimental, in my experience some tracks may have a slight hiss... this is an upstream issue.

## Troubleshooting

Interfacing devices that are almost 20 years old will always be a little finnicky, so expect sometimes you may just have to plug it out/in again.

### Stuck on "Negotiating" for more than 30 seconds

* Press the retry button, feel free to press it a few times. This is often caused by a slow startup time of the device.
* Ensure that there is a disc in the device. It must be a standard formatted disc, not Hi-MD, etc.
* Set disc mode to "MD" - on your MD device, this is ususally under `Options` -> `Disc Mode` -> set to `MD`. This is ususally only an issue when using a blank disc.

### Debugging

* There may be some useful information in the Platinum-MD debug window. To access, click `Settings` and then click the `Debug Window` button.

## Thanks

The Linux-Minidisc project (this is the most up-to-date Fork I've found, but there are many contributers):

<https://github.com/vuori/linux-minidisc/>

The ATRAC Encoder by @dcherednik

<https://github.com/dcherednik/atracdenc>

## Donate

I do this as a personal project, and a few people have expressed interested in donating to keep the project going, this will simply go back into buying test hardware and/or possibly coffee.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XVS44CZYFPCJJ)

