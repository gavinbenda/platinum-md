[![Build Status](https://travis-ci.org/gavinbenda/platinum-md.svg?branch=master)](https://travis-ci.org/gavinbenda/platinum-md)

# Platinum-MD

> An easy-to-use, cross-platform, modern interface for managing NetMD Minidisc devices.
> This project aims to make transferring audio files to NetMD players seamless and automatic.
> Allowing for the highest possible quality SP transfers, Platinum-MD can convert your music from almost any format including FLAC.
> When using an MZ-RH1 - there is also the ability to transfer tracks back to your computer from MD.

![Screenshot](https://i.imgur.com/ZGFvO9p.png)


#### Download & Installation

---

##### OSX

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v1.2.1/platinum-md-1.2.1.dmg), and open the dmg.

Drag the file to the applications folder.

Upon opening the `platinum-md` app from the applications folder, it will show a warning.

Open OSX `Settings` and click `Security & Privacy` - click the `Open Anyway` button shown near the bottom of the panel.

IMPORTANT: When opening Platinum-MD for the first time, you must follow the instructions to install some further dependancies (look for the yellow alert icon).
Use `settings` -> `help` -> `troubleshooter` if you experience any other issues.

###### OSX Manual Installation

If you prefer to do this manually, you will need to install homebrew using Terminal (`Applications` -> `Utilities` -> `Terminal`): https://docs.brew.sh/Installation

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"`

Then run the following:

`brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg json-c && brew link --force qt5`

---

##### Windows

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v1.2.0/platinum-md.Setup.1.2.0.exe), and open the platinum-md .exe Setup file.

IMPORTANT: You will need to download and use a tool called [Zadig](https://zadig.akeo.ie/) to install the WinUSB Driver.
Connect your NetMD device, open the app and click the "Install Driver" button.
Please note, this will disable Sonic Stage from having access to the device, you'll need to run Zadig and 'reinstall' the old driver to use it again.

Download Here: https://zadig.akeo.ie/

---

##### Linux

Download the [latest release](https://github.com/gavinbenda/platinum-md/releases/download/v0.7.0-alpha/platinum-md-0.7.0.AppImage), and open the platinum-md AppImage Setup file.

Note: This has only been tested on Ubuntu, but is known to work on other distros.

From Terminal, run `apt-get install libgcrypt20-dev libglib2.0-dev libusb-1.0-0-dev qt4-qmake libid3tag0-dev libmad0-dev`

You will also likely need to give your current user the correct permissions to access the USB/NetMD Device.
This is a 'catch-all' but you may wish to add a specific deviceId/vendorId if you want to lock permissions down.
Run the following: `sudo nano /etc/udev/rules.d/50-device.rules` and add the following: `SUBSYSTEM=="usb", GROUP="YOURUSERGROUPHERE"`

Building: npm run-script build && npm run-script postinstall
Running: ./build/platinum-md-X.Y.Z.AppImage

---


## Features

* Supports transfer of any common audio format directly to a compatible NetMD recorder.
* Full quality SP recording (Sonic Stage uses an inferior 132Kbps (LP2) "SP Compatible" mode)
* Convert and transfer audio as LP2/LP4
* Erase/Move/Rename disc or tracks.
* Transer from MD to PC with an MZ-RH1
* Ability to read HiMD discs, and transfer MP3 files in HiMD mode (does not support other formats yet).


## Release Notes

Please report any feature requests or bug reports using the [Issues Tracker](https://github.com/gavinbenda/platinum-md/issues).


## Troubleshooting

* Use the Troubleshooter (click `settings` -> `help` -> `troubleshooter`) as a first step.
* Make sure you have a disk in the device before connecting.
* If the interface shows "Negotiating with device" but won't connect, click the `retry` button.
* If using Windows, ensure you've correctly installed the driver using Zadig (instructions above).
* Some discs origionally made with Sonic Stage may not allow for tracks to be deleted by Platinum-MD.
* Windows anti-virus software may sometimes incorrectly mark the app as a positive.
* Set disc mode to "MD" - on your MD device, this is ususally under `Options` -> `Disc Mode` -> set to `MD`. This is ususally only an issue when using a blank disc.
* Interfacing devices that are almost 20 years old will always be a little finnicky, so expect sometimes you may just have to un-plug/plug-in again or encounter odd USB issues.


## Known bugs / future Plans

* Some pre-recorded discs made with SonicStage may show as blank
* Transfering tracks to MZ-NH700 (and possibly other Hi-MD devices) in NetMD mode fails when using a blank disc formatted as MD using a Hi-MD device. This is a bug in linux-minidisc. To work around this issue, format the disc in a non-himd recorder, or record a short track onto the disc using the NH700 and hit stop to save TOC, eject and power off the device, then insert disc and connect to computer.
* Some devices sometimes incorrectly show no tracks on disc, if this occurs clic refresh on the netmd pane. If the issue persists unplug the device from the computer, eject the disk and power down the device, then retry.
* The USB interface sometimes just fails, this is hard to fix as it seems to be the device itself (just unplug/plug-in again).
* LP2/LP4 is an experimental implementation, it seems to be acceptable quality.


## Thanks

The Linux-Minidisc project (this is the most up-to-date Fork I've found, but there are many contributers):
<https://github.com/vuori/linux-minidisc/>

The ATRAC Encoder by @dcherednik
<https://github.com/dcherednik/atracdenc>

Massive thanks to all of the open source community who have contributed features/fixes to the project.


## Donate

I do this as a personal project, and a few people have expressed interested in donating to keep the project going, this will simply go back into buying test hardware and/or possibly coffee.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XVS44CZYFPCJJ)
