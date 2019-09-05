<template>
  <div id="wrapper" class="p-3">
    
    <b-modal @ok="saveSettings" ref="settings-modal" title="Settings">
      <b-form-group label="Transfer Mode:">
        <b-form-radio v-model="conversionMode" name="mode-sp" value="SP">SP (Best quality)</b-form-radio>
        <b-form-radio v-model="conversionMode" name="mode-lp2" value="LP2">LP2 (Fit more tracks)</b-form-radio>
      </b-form-group>
      <b-alert variant="success" show><b>Please note:</b> LP2 is implemented using an experimental encoder.<br />LP4 is currently not possible.</b-alert>
    </b-modal>
    
    <b-container fluid class="px-3">
      <b-row>
        <b-col class="p-3">
          <img id="logo" src="~@/assets/logo.svg" alt="Platinum MD">
        </b-col>
        <b-col class="p-3 text-right">
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
  import DirectoryListing from './LandingPage/DirectoryListing'
  import NetMdListing from './LandingPage/NetMdListing'
  const Store = require('electron-store')
  const store = new Store()
  export default {
    name: 'landing-page',
    components: { DirectoryListing, NetMdListing },
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
      }
    }
  }
</script>
