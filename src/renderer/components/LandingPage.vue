<template>
  <div id="wrapper">
    <img id="logo" src="~@/assets/logo.svg" alt="Platinum MD">
    <main>
      <div class="left-side">
        <span class="title">
          Local Files:
        </span>
        <directory-listing></directory-listing>
      </div>

      <div class="right-side">
        <span class="title">
          NetMD Files:
        </span>
        <net-md-listing></net-md-listing>
      </div>
    </main>
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

<style>
  @import url('https://fonts.googleapis.com/css?family=Source+Sans+Pro');

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  body { font-family: 'Source Sans Pro', sans-serif; }

  #wrapper {
    background-image: radial-gradient(52% 131%, #00B5A7 48%, #007A9F 100%);
    height: 100vh;
    padding: 60px 80px;
    width: 100vw;
  }

  #logo {
    height: auto;
    margin-bottom: 20px;
    width: 250px;
    box-shadow: 10px 10px 5px -10px rgba(17,82,77,1);
  }

  main {
    display: flex;
    justify-content: space-between;
  }

  main > div { flex-basis: 50%; }

  .left-side {
    display: flex;
    flex-direction: column;
  }

  .welcome {
    color: #555;
    font-size: 23px;
    margin-bottom: 10px;
  }

  .title {
    color: #2c3e50;
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 6px;
  }

  .title.alt {
    font-size: 18px;
    margin-bottom: 10px;
  }

  .doc p {
    color: black;
    margin-bottom: 10px;
  }

  .doc button {
    font-size: .8em;
    cursor: pointer;
    outline: none;
    padding: 0.75em 2em;
    border-radius: 2em;
    display: inline-block;
    color: #fff;
    background-color: #4fc08d;
    transition: all 0.15s ease;
    box-sizing: border-box;
    border: 1px solid #4fc08d;
  }

  .doc button.alt {
    color: #42b983;
    background-color: transparent;
  }
</style>
