<template>
  <div id="wrapper" class="p-3">

    <b-modal @ok="saveSettings" ref="settings-modal" title="Settings" size="lg">
      <b-tabs content-class="mt-3" card>
        <b-tab title="Device Mode" active>
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
          <b-alert variant="danger" show class="mt-3">
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
          <b-button variant="outline-light" @click="showSettingsModal">Settings <font-awesome-icon icon="cog"></font-awesome-icon></b-button>
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
  const { remote } = require('electron')
  const homedir = require('os').homedir()
  const Store = require('electron-store')
  const store = new Store()
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
        ]
      }
    },
    created () {
      this.readConfig()
    },
    mounted () {
      bus.$on('netmd-status', (data) => {
        if ('deviceName' in data) {
          this.rh1 = ((data.deviceName === 'Sony MZ-RH1') || (this.mode === 'himd'))
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
    },
    methods: {
      /**
        * Rename track modal
        */
      showSettingsModal: function () {
        this.$refs['settings-modal'].show()
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
          this.downloadFormat = store.get('downloadDir')
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
