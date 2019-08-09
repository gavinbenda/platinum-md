<template>
  <div>

    <button @click="readNetMd">Scan Files</button>
    
    <div v-for="track in tracks" :key="track">
      {{track}}
    </div>
    
  </div>
</template>

<script>
export default {
  data () {
    return {
      lsmd: [],
      tracks: []
    }
  },
  methods: {
    readNetMd () {
      let py = require('child_process').spawn('python', ['/Users/gavinbenda/webdev/linux-minidisc/netmd/lsmd.py'])
      py.stdout.on('data', data => {
        // consume track listing
        // probably would be nicer to modify the python scripts to provide an API
        let response = data.toString()
        // console.log(response)
        this.lsmd = response.split(/\r\n|\r|\n/)
        // now store only tracks
        for (var i = 0, len = this.lsmd.length; i < len; i++) {
          let line = this.lsmd[i]
          if (/^\d+$/.test(line.substr(0, 2)) && line.substr(3, 4)) {
            console.log(line)
            this.tracks.push(line)
          }
        }
      })
      py.on('close', () => {
        console.log('script ended.')
      })
    }
  }
}
</script>

<style scoped>
  .title {
    color: #888;
    font-size: 18px;
    font-weight: initial;
    letter-spacing: .25px;
    margin-top: 10px;
  }

  .items { margin-top: 8px; }

  .item {
    display: flex;
    margin-bottom: 6px;
  }

  .item .name {
    color: #6a6a6a;
    margin-right: 6px;
  }

  .item .value {
    color: #35495e;
    font-weight: bold;
  }
</style>
