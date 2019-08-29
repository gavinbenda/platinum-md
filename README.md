# Platinum-MD

> A Gui for NetMD

#### Build Setup

``` bash
# install dependencies
npm install

# build electron application for production
npm run build

```

#### Dependancies

This is quite tricky, as there are a few extras needed.
Future releases will try and include a statically build binary for each included tool.

You will need to install homebrew: https://docs.brew.sh/Installation
Then from the command line, install the following:

`# brew install libsndfile`

`# brew install ffmpeg`

You may also need to install (this can be a large download):

`xcode-select --install`


## Overview

This project aims to make uploading audio files to NetMD players seamless and automatic.

## Features

Supports upload MP3/WAV/FLAC files direct to a compatible NetMD recorder.


## Release Notes

This is a very alpha release, expect bugs.