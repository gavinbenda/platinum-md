<template>
  <div id="wrapper" class="p-3">
    
    <b-container fluid class="px-3">
      <b-row>
        <b-col class="p-3">
          <img id="logo" src="~@/assets/logo.svg" alt="Platinum MD">
        </b-col>
        <b-col class="p-3">
          Status
        </b-col>
      </b-row>
    </b-container>

    <b-container fluid class="p-3">
      <b-row>
        <b-col class="white-bg full-height mx-3 p-0">
          <directory-listing></directory-listing>
        </b-col>
        <b-col class="white-bg full-height mx-3 p-0">
          <net-md-listing></net-md-listing>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import DirectoryListing from './LandingPage/DirectoryListing'
  import NetMdListing from './LandingPage/NetMdListing'

  export default {
    name: 'landing-page',
    components: { DirectoryListing, NetMdListing },
    methods: {
      open (link) {
        this.$electron.shell.openExternal(link)
      }
    }
  }
</script>
