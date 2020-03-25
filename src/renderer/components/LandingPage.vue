<template>
  <div id="wrapper" class="p-3">
    
    <b-modal @ok="saveSettings" ref="settings-modal" title="Settings">
      <b-form-group label="Transfer Mode:">
        <b-form-radio v-model="conversionMode" name="mode-sp" value="SP">SP (Best quality)</b-form-radio>
        <b-form-radio v-model="conversionMode" name="mode-lp2" value="LP2">LP2 (Fit more tracks)</b-form-radio>
      </b-form-group>
      <b-alert variant="success" show><b>Please note:</b> LP2 is implemented using an experimental encoder.<br />LP4 is currently not possible.</b-alert>
      <b-button variant="outline-primary" @click="showDebugConsole">Debug Window</b-button>
    </b-modal>
    
    <b-container fluid>
      <b-row>
        <b-col cols="6"><img id="logo" src="~@/assets/logo.svg" alt="Platinum MD" class="p-3"></b-col>
        <b-col class="text-center"><control-bar></control-bar></b-col>
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
  const { remote } = require('electron')
  const Store = require('electron-store')
  const store = new Store()
  export default {
    name: 'landing-page',
    components: { DirectoryListing, NetMdListing, ControlBar },
    data () {
      return {
        conversionMode: 'SP'
      }
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
        store.set('conversionMode', this.conversionMode)
        bus.$emit('config-update')
      },
      /**
        * Show debug console
        */
      showDebugConsole: function () {
        remote.getCurrentWindow().webContents.openDevTools()
      }
    }
  }
</script>
