<template>
  <div id="wrapper" class="p-3">

    <b-modal @ok="saveSettings" ref="settings-modal" title="Settings">
      <b-form-group label="Mode:">
        <b-form-radio v-model="mode" name="mode-md" value='md'>MD</b-form-radio>
        <b-form-radio v-model="mode" name="mode-himd" value='himd'>Hi-MD</b-form-radio>
      </b-form-group>
      <hr />
      <b-form-group v-if="mode === 'himd'">
        <p>HiMD Path: {{ himdPath }}</p>
        <b-button variant="outline-primary" @click="chooseHiMDPath">Browse <font-awesome-icon icon="folder-open"></font-awesome-icon></b-button>
      </b-form-group>
      <b-form-group v-else label="Transfer Mode:">
        <b-form-radio v-model="conversionMode" name="mode-sp" value="SP">SP (Best quality)</b-form-radio>
        <b-form-radio v-model="conversionMode" name="mode-lp2" value="LP2">LP2 (Acceptable Quality)</b-form-radio>
        <b-form-radio v-model="conversionMode" name="mode-lp4" value="LP4">LP4 (Lower Quality)</b-form-radio>
      </b-form-group>
      <b-alert variant="success" show><b>Please note:</b> LP2/LP4 is implemented using an experimental encoder.</b-alert>
      <hr />
      <b>Title Format</b>
      <p>Options: <b-badge>%title%</b-badge> <b-badge>%artist%</b-badge> <b-badge>%trackno%</b-badge></p>
      <b-form-input v-model="titleFormat"></b-form-input>
      <hr />
      <b-form-checkbox type="checkbox" name="sonicstage-titles" id="sonicstage-titles" v-model="sonicStageNosStrip">Strip SonicStage track numbers from titles (e.g 001-Title)</b-form-checkbox>
      <hr />
      <template v-if="(mode === 'himd') || rh1">
        <b v-if="mode === 'md'">RH1 Download Options</b>
        <b v-if="mode === 'himd'">Hi-MD Download Options</b>
        <b-form-group label="Save downloaded tracks as:">
          <b-form-radio v-model="downloadFormat" name="WAV" value="WAV">WAV</b-form-radio>
          <b-form-radio v-model="downloadFormat" name="FLAC" value="FLAC">FLAC</b-form-radio>
          <b-form-radio v-model="downloadFormat" name="MP3" value="MP3">MP3 (320kbs)</b-form-radio>
          <b-form-radio v-model="downloadFormat" name="RAW" value="RAW">AEA/AT3 (Do not convert audio)</b-form-radio>
        </b-form-group>
        <b-form-checkbox type="checkbox" name="use-sonicstage-nos" id="use-sonicstage-nos" v-model="useSonicStageNos">Save tracks with SonicStage style track numbers (e.g 001-Title)</b-form-checkbox>
        <br>
        <p>Download directory: {{ downloadDir }}</p>
        <b-button variant="outline-primary" @click="chooseDownloadDir">Browse <font-awesome-icon icon="folder-open"></font-awesome-icon></b-button>
        <hr />
      </template>

      <b-button variant="outline-primary" @click="showDebugConsole">Debug Window</b-button>
    </b-modal>

    <b-container fluid>
      <b-row>
        <b-col cols="6"><img id="logo" src="~@/assets/logo.svg" alt="Platinum MD" class="p-3"></b-col>
        <p><b>Experimental deenine Hi-MD Build 0.0.1</b></p>
        <b-col v-if="mode === 'md'" class="text-center"><control-bar></control-bar></b-col>
        <b-col class="text-right p-3"><b-button variant="outline-light" @click="showSettingsModal">Settings <font-awesome-icon icon="cog"></font-awesome-icon></b-button></b-col>
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
        conversionMode: 'SP',
        titleFormat: '%title% - %artist%',
        sonicStageNosStrip: true,
        useSonicStageNos: true,
        rh1: false,
        mode: 'md',
        downloadFormat: 'FLAC',
        downloadDir: homedir + '/pmd-music/',
        himdPath: '/Users/Doug/workspace/linux-minidisc/testdata/himd/'
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
    }
  }
</script>
