# How to set up Platinum MD for testing

Make sure you have git installed: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

Clone this repo:
`git clone https://github.com/deenine/platinum-md`

Checkout the rh1 development branch:
`git checkout rh1-upload`

## OSX

Make sure you have git installed.

You will need to install homebrew: https://docs.brew.sh/Installation

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"`

Then install the following:

`brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg json-c node yarn && brew link --force qt5`

Open a terminal where you cloned this repo, then run `yarn && yarn run dev` to launch the development platinum-md. 

If you plug in a RH1, it should show the green `<< Transfer` button above the netmd pane, and you should see the download options in the settings menu.


## Windows

Windows install sucks, sorry.

Install python2: https://www.python.org/downloads/release/python-2718/

Go to the python2 install directory (probably `C:\python27`) and copy and paste python.exe, and rename the copy to `python2.exe`.

Open the windows system environment settings and make sure that the python directory above is on the system PATH (not the user path).

Go find the repo that you cloned, browse to `platinum-md\resources\win\bin\` and copy `libusb-1.0.dll` into your python directory, or if you are using a 64bit system, copy  `libusb-1.0-64.dll` into the python directory and rename it to `libusb-1.0.dll`.

Open a terminal for the directory where you cloned this repo, and run:
`yarn`
`yarn run dev` to launch the development platinum-md.

If you plug in a RH1, it should show the green `<< Transfer` button above the netmd pane, and you should see the download options in the settings menu.
