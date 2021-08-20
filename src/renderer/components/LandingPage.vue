<template>
  <div id="wrapper" class="p-3">

    <b-modal @ok="saveSettings" ref="settings-modal" title="Settings" size="lg">
      <b-tabs content-class="mt-3" v-model="settingsTabIndex" card>
        <b-tab title="Device Mode">
          <b>Mode:</b>
          <b-form-group>
            <b-form-radio v-model="mode" name="mode-md" value='md'>MD</b-form-radio>
            <b-form-radio v-model="mode" name="mode-himd" value='himd'>Hi-MD</b-form-radio>
          </b-form-group>
          <hr />
          <p><b>HiMD Path:</b> <b-badge>{{ himdPath }}</b-badge></p>
          <b-button variant="primary" @click="chooseHiMDPath">Choose Hi-MD Path <font-awesome-icon icon="folder-open"></font-awesome-icon></b-button>
          <b-alert variant="info" show class="mt-3">
            The Hi-MD recorder appears as a usb drive when connected to computer, select that drive below, e.g. <pre class="badge badge-dark mb-0">'E:'</pre> or <pre class="badge badge-dark mb-0">'/Volumes/NO NAME/'</pre>
          </b-alert>
          <b-alert variant="danger" show class="mt-3" v-if="mode==='himd'">
            <b>Hi-MD functionality is experimental - ONLY USE FOR DISCS YOU ARE PREPARED TO ERASE</b><br />
            In some cases Hi-MD functionality can corrupt the disc which prevents reading of any tracks.<br />
            Hi-SP/Hi-LP/MP3 transfers are supported from Hi-MD to computer, only MP3 transfers are supported to Hi-MD.<br >
            Renaming/erasing tracks/discs is not supported for Hi-MD.
          </b-alert>
        </b-tab>
        <b-tab title="MD Options">
          <b>Transfer Mode</b>
          <b-form-group>
            <b-form-radio v-model="conversionMode" name="mode-sp" value="SP">SP (Best quality)</b-form-radio>
            <b-form-radio v-model="conversionMode" name="mode-lp2" value="LP2">LP2 (Acceptable Quality)</b-form-radio>
            <b-form-radio v-model="conversionMode" name="mode-lp4" value="LP4">LP4 (Lower Quality)</b-form-radio>
          </b-form-group>
          <b-alert variant="info" show><b>Please note:</b> LP2/LP4 is implemented using an experimental encoder.</b-alert>
        </b-tab>
        <b-tab title="Hi-MD Options">
          <p><b>Download directory:</b> <b-badge>{{ downloadDir }}</b-badge></p>
          <b-button variant="primary" @click="chooseDownloadDir">Choose Download Directory <font-awesome-icon icon="folder-open"></font-awesome-icon></b-button>
          <hr />
          <b>File format to transfer tracks to computer:</b>
          <b-form-group>
            <b-form-radio v-model="downloadFormat" name="download-wav" value="WAV">WAV</b-form-radio>
            <b-form-radio v-model="downloadFormat" name="download-flac" value="FLAC">FLAC</b-form-radio>
            <b-form-radio v-model="downloadFormat" name="download-mp3" value="MP3">MP3 (320kbs)</b-form-radio>
            <b-form-radio v-model="downloadFormat" name="download-raw" value="RAW">AEA/AT3 (Do not convert audio)</b-form-radio>
          </b-form-group>
          <hr />
          <b-form-checkbox type="checkbox" name="use-sonicstage-nos" id="use-sonicstage-nos" v-model="useSonicStageNos">Save tracks with SonicStage style track numbers (e.g 001-Title)</b-form-checkbox>
          <b-alert variant="info" show class="mt-3">
            Some functionality for downloading tracks back to your computer will only work with an MZ-RH1. Original self-recorded material should work on other Hi-MD devices.
          </b-alert>
        </b-tab>
        <b-tab title="Track Titling">
          <b>Title Format</b>
          <p>Options: <b-badge>%title%</b-badge> <b-badge>%artist%</b-badge> <b-badge>%trackno%</b-badge></p>
          <b-form-input v-model="titleFormat"></b-form-input>
          <hr />
          <b-form-checkbox type="checkbox" name="sonicstage-titles" id="sonicstage-titles" v-model="sonicStageNosStrip">Strip SonicStage track numbers from titles (e.g 001-Title)</b-form-checkbox>
        </b-tab>
        <b-tab title="Help">
          <div>
            <b-card no-body>
              <b-tabs pills card>
                <b-tab title="Troubleshooter" active v-if="osPlatform === 'darwin'">
                  <b-card-text>
                    <b-row>
                      <b-col cols="12">
                        <b-table striped small :items="requiredPackages">
                          <template #cell(name)="data">
                            <b>{{ data.value }}</b>
                          </template>
                          <template #cell(installed)="data">
                            <b class="text-success" v-if="data.value==='Installed'">{{ data.value }}</b>
                            <b class="text-danger" v-if="data.value!=='Installed'">{{ data.value }}</b>
                          </template>
                        </b-table>
                        <b-button variant="outline-success" @click="runTroubleshooter" class="mb-2">Re-Run Troubleshooter <font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
                      </b-col>
                    </b-row>
                    <b-alert variant="info" show class="mt-3" v-if="packageError">
                      <b>IMPORTANT: You do not have all of the required libraries installed.</b><br />
                      <b-button variant="success" @click="installPackages" class="my-2" small>Click Here to Install Now <font-awesome-icon icon="cog"></font-awesome-icon></b-button><br />
                      <b>* Please wait for the terminal window to appear.
                      You may be asked to enter your password.</b>
                    </b-alert>
                  </b-card-text>
                </b-tab>
                <b-tab title="Troubleshooter" active v-if="osPlatform === 'win32'">
                  <b-alert variant="info" show class="mt-3">
                    If your device is not detected, ensure you have downloaded and used the <a href="#" @click="openExternalLink('https://zadig.akeo.ie/')">Zadig Tool</a> to swap USB drivers.
                  </b-alert>
                </b-tab>
                <b-tab title="Connected USB Devices">
                  <b-card-text>
                      <b-table
                        striped
                        small
                        :items="devices"
                        :fields="fields"
                        responsive="sm"
                      >
                        <div slot="table-busy" class="text-center text-danger my-2">
                          <b-spinner class="align-middle"></b-spinner>
                          <strong>Loading...</strong>
                        </div>
                      </b-table>
                      <template v-slot:overlay>
                        <b-spinner varient="success" label="Spinner" variant="success"></b-spinner>
                      </template>
                    <b-button variant="outline-success" @click="findUSBDevices" class="mb-2">Refresh Device List <font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
                  </b-card-text>
                </b-tab>
              </b-tabs>
            </b-card>
          </div>
          <hr />
          <b-button variant="primary" @click="showDebugConsole">Show Debug Window</b-button>
        </b-tab>
      </b-tabs>
    </b-modal>

    <b-container fluid>
      <b-row>
        <b-col><img id="logo" src="~@/assets/logo.svg" alt="Platinum MD" class="px-3 mt-3"></b-col>
        <b-col class="text-center mt-1" cols="7">
          <div id="unified-controls" class="py-2 px-3">
            <b-row>
              <b-col cols="auto">
                <b-button-toolbar key-nav aria-label="Toolbar for selecting modes">
                  <b-button-group class="mx-1">
                    <b-form-radio-group
                    id="btn-radios-3"
                    v-model="mode"
                    :options="modeOptions"
                    name="radio-btn-stacked"
                    button-variant="dark"
                    buttons
                  ></b-form-radio-group>
                  </b-button-group>
                  <b-button-group class="mx-1" v-if="mode === 'md'">
                    <b-form-radio-group
                    v-model="conversionMode"
                    :options="conversionModeOptions"
                    name="radio-btn-stacked"
                    button-variant="dark"
                    buttons
                  ></b-form-radio-group>
                  </b-button-group>
                  <b-button-group class="mx-1" v-if="mode === 'himd'">
                    <b-form-radio-group
                    v-model="conversionModeHimd"
                    :options="conversionModeHimdOptions"
                    name="radio-btn-stacked"
                    button-variant="dark"
                    buttons
                  ></b-form-radio-group>
                  </b-button-group>
                </b-button-toolbar>
              </b-col>
              <b-col class="text-left no-linewrap">
                <b-badge variant="dark" class="text-uppercase">Status:</b-badge><br />
                <div class="status-msg">{{ progress }}</div>
              </b-col>
              <b-col cols="auto">
                <control-bar v-if="mode === 'md'"></control-bar>
              </b-col>
            </b-row>
            <b-progress :value="progress" :animated="isBusy" variant="success" show-progress class="mt-2">
              <b-progress-bar :value="progressPercent" v-if="progress != 'Idle' && progress != 'Disc Full'">
                <span>{{ progressPercent }}</span>
              </b-progress-bar>
            </b-progress>
          </div>
        </b-col>
        <b-col class="text-right p-3">
          <b-button variant="outline-light" @click="showSettingsModal(0)">Settings <font-awesome-icon icon="cog"></font-awesome-icon></b-button>
        </b-col>
      </b-row>
    </b-container>

    <b-container fluid class="p-3">
      <b-row>
        <b-col class="white-bg full-height mx-3 p-0 overflow-auto">
          <directory-listing></directory-listing>
        </b-col>
        <b-col class="white-bg full-height mx-3 p-0 overflow-auto">
          <net-md-listing></net-md-listing>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import bus from '@/bus'
  import DirectoryListing from './LandingPage/DirectoryListing'
  import NetMdListing from './LandingPage/NetMdListing'
  import ControlBar from './LandingPage/ControlBar'
  import path from 'path'
  import os from 'os'
  import { sonyVid, sonyHiMDPids, sonyMDPids } from '@/deviceIDs'
  import { shell } from 'electron'
  const { remote } = require('electron')
  const homedir = require('os').homedir()
  const usbDetect = require('usb-detection')
  const Store = require('electron-store')
  const store = new Store()
  const fixPath = require('fix-path')
  export default {
    name: 'landing-page',
    components: { DirectoryListing, NetMdListing, ControlBar },
    data () {
      return {
        isBusy: false,
        conversionMode: 'SP',
        conversionModeHimd: 'MP3',
        titleFormat: '%title% - %artist%',
        sonicStageNosStrip: true,
        useSonicStageNos: true,
        rh1: false,
        mode: 'md',
        downloadFormat: 'WAV',
        downloadDir: homedir + '/pmd-music/',
        himdPath: '/Volumes/NO NAME/',
        progress: 'Idle',
        progressPercent: 100,
        modeOptions: [
          { text: 'MD', value: 'md' },
          { text: 'Hi-MD', value: 'himd' }
        ],
        conversionModeOptions: [
          { text: 'SP', value: 'SP' },
          { text: 'LP2', value: 'LP2' },
          { text: 'LP4', value: 'LP4' }
        ],
        conversionModeHimdOptions: [
          { text: 'MP3', value: 'MP3' }
        ],
        showOverlay: false,
        devices: [],
        fields: [
          { key: 'deviceAddress', sortable: true },
          { key: 'manufacturer', sortable: true },
          { key: 'deviceName', sortable: true },
          { key: 'vendorId', sortable: true },
          { key: 'productId', sortable: true },
          { key: 'mdType', sortable: true }
        ],
        requiredPackages: [
          { name: 'brew', installed: '' },
          { name: 'libid3tag', installed: '' },
          { name: 'libtag', installed: '' },
          { name: 'glib', installed: '' },
          { name: 'libusb', installed: '' },
          { name: 'libusb-compat', installed: '' },
          { name: 'libgcrypt', installed: '' },
          { name: 'json-c', installed: '' }
        ],
        packageError: false,
        osPlatform: '',
        settingsTabIndex: 0
      }
    },
    created () {
      this.readConfig()
      this.osPlatform = os.platform()
    },
    mounted () {
      bus.$on('netmd-status', (data) => {
        if ('deviceName' in data) {
          this.rh1 = ((data.deviceName === 'Sony MZ-RH1 MD') || (this.mode === 'himd'))
        }
        if ('progress' in data) {
          this.progress = data.progress
        }
        if ('progressPercent' in data) {
          this.progressPercent = data.progressPercent
        }
        if ('isBusy' in data) {
          this.isBusy = data.isBusy
        }
      })
      // run a sanity check on first start
      fixPath()
      this.runTroubleshooter()
      bus.$on('show-troubleshooter', (data) => {
        this.showSettingsModal(4)
      })
    },
    methods: {
      /**
        * Rename track modal
        */
      showSettingsModal: function (tabIndex = 0) {
        this.$refs['settings-modal'].show()
        this.settingsTabIndex = tabIndex
        this.findUSBDevices()
        this.runTroubleshooter()
      },
      /**
        * Save settings to store
        */
      saveSettings: function () {
        store.set('mode', this.mode)
        if (this.mode === 'himd') {
          store.set('conversionMode', 'MP3')
        } else {
          store.set('conversionMode', this.conversionMode)
        }
        store.set('titleFormat', this.titleFormat)
        store.set('sonicStageNosStrip', this.sonicStageNosStrip)
        store.set('useSonicStageNos', this.useSonicStageNos)
        store.set('downloadFormat', this.downloadFormat)
        store.set('downloadDir', this.downloadDir)
        store.set('himdPath', this.himdPath)
        bus.$emit('config-update')
      },
      /**
        * Read-in config file
        */
      readConfig: function () {
        if (store.has('conversionMode')) {
          this.conversionMode = store.get('conversionMode')
        }
        if (store.has('titleFormat')) {
          this.titleFormat = store.get('titleFormat')
        }
        if (store.has('sonicStageNosStrip')) {
          this.sonicStageNosStrip = store.get('sonicStageNosStrip')
        }
        if (store.has('useSonicStageNos')) {
          this.useSonicStageNos = store.get('useSonicStageNos')
        }
        if (store.has('downloadFormat')) {
          this.downloadFormat = store.get('downloadFormat')
        }
        if (store.has('downloadDir')) {
          this.downloadDir = store.get('downloadDir')
        }
        if (store.has('mode')) {
          this.mode = store.get('mode')
        }
        if (store.has('himdPath')) {
          this.himdPath = store.get('himdPath')
        }
      },
      /**
        * Show debug console
        */
      showDebugConsole: function () {
        remote.getCurrentWindow().webContents.openDevTools()
      },
      chooseDownloadDir: function () {
        remote.dialog.showOpenDialog({
          properties: ['openDirectory'],
          defaultPath: this.downloadDir
        }, names => {
          if (names != null) {
            console.log('selected download directory:' + names[0])
            store.set('downloadDir', names[0] + path.sep)
            this.downloadDir = store.get('downloadDir')
          }
        })
      },
      /**
      * Choose the path of the HiMD device
      */
      chooseHiMDPath: function () {
        remote.dialog.showOpenDialog({
          properties: ['openDirectory'],
          defaultPath: this.himdPath
        }, names => {
          if (names != null) {
            console.log('selected download directory:' + names[0])
            store.set('downloadDir', names[0] + path.sep)
            this.himdPath = store.get('downloadDir')
          }
        })
      },
      /**
      * Finds all USB devices and shows their mode for troubleshooting
      */
      findUSBDevices: async function () {
        this.devices = []
        this.showOverlay = true
        usbDetect.startMonitoring()
        let device = await usbDetect.find(function (err, device) {
          if (err) {
            console.log(err)
            throw err
          }
          return device
        })
        if (device.length) {
          this.devices = device
        }
        var sonyHiMDPidsKeys = Object.keys(sonyHiMDPids)
        var sonyMDPidsKeys = Object.keys(sonyMDPids)
        for (const device of this.devices) {
          if (device.vendorId === sonyVid) {
            if (sonyHiMDPidsKeys.includes(device.productId.toString())) {
              device.mdType = 'HiMD'
              device.deviceName = sonyHiMDPids[device.productId]
              device._rowVariant = 'success'
            } else if (sonyMDPidsKeys.includes(device.productId.toString())) {
              device.mdType = 'MD'
              device.deviceName = sonyMDPids[device.productId]
              device._rowVariant = 'success'
            }
          }
        }
        this.showOverlay = false
      },
      /**
      * Runs the troubleshooter, to figure out any dependancies that may be missing
      * Note: OSX only
      * TODO: Create functionality to detect the currently installed MD driver on Windows.
      */
      runTroubleshooter: function () {
        if (os.platform() === 'darwin') {
          var depCheck
          this.packageError = false
          bus.$emit('package-error', false)
          for (const dependancy of this.requiredPackages) {
            console.log('Checking: ' + dependancy.name)
            if (dependancy.name === 'brew') {
              depCheck = require('child_process').exec('which brew')
              depCheck.stdout.on('data', data => {
                if (data.toString() === '' || data.toString().includes('brew not found')) {
                  console.log('Did not find: ' + dependancy.name)
                  dependancy.installed = '!! Not Found'
                  this.packageError = true
                  bus.$emit('package-error', true)
                } else {
                  dependancy.installed = 'Installed'
                }
              })
            } else {
              depCheck = require('child_process').exec('brew list ' + dependancy.name + ' | grep "No such keg"')
              depCheck.stderr.on('data', data => {
                console.log('stderr: ' + data.toString())
                dependancy.installed = '!! Not Found'
                this.packageError = true
                bus.$emit('package-error', true)
              })
              depCheck.on('exit', function () {
                if (dependancy.installed === '') {
                  dependancy.installed = 'Installed'
                }
              })
            }
          }
        }
        if (os.platform() === 'win32') {
          // TODO: check which USB driver is installed
        }
      },
      /**
      * Function to spawn the terminal and install homebrew, then all other dependancies on OSX
      */
      installPackages: function () {
        // if homebrew not found, install everything
        var command
        if (this.requiredPackages[0].installed === '!! Not Found') {
          command = [
            `osascript -e 'tell application "Terminal" to activate'`,
            /* eslint-disable-next-line */
            `-e 'tell application "Terminal" to do script "/bin/bash -c \\"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\\" && brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg json-c"'`
          ].join(' ')
        // if we do have homebrew, it must just be packages we need
        } else {
          command = [
            `osascript -e 'tell application "Terminal" to activate'`,
            /* eslint-disable-next-line */
           `-e 'tell application "Terminal" to do script "brew install --force pkg-config qt5 mad libid3tag libtag glib libusb libusb-compat libgcrypt ffmpeg json-c"'`
          ].join(' ')
        }
        const child = require('child_process').exec(command, (error, stdout, stderr) => {
          if (error) {
            console.error(error)
            alert('Unable to open Terminal window, see dev console for error.')
          }
        })
        child.on('exit', (code) => console.log('Open terminal exit'))
      },
      /**
      * Function to open browser window
      */
      openExternalLink: function (link) {
        shell.openExternal(link)
      }
    },
    watch: {
      mode: function () {
        this.saveSettings()
        bus.$emit('config-update')
      },
      conversionMode: function () {
        this.saveSettings()
        bus.$emit('config-update')
      }
    }
  }
</script>
