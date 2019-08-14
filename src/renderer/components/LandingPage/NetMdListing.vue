<template>
  <div>
    
    <b-container class="toolbar py-2">
      <b-row align-v="center">
        <b-col>
          <b>{{ tracks.length }}</b> tracks on NetMD
        </b-col>
        <b-col class="text-right">
          <b-button variant="outline-light" @click="readNetMd">Rescan <font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
          <b-button variant="danger" @click="deleteTracks">Delete <font-awesome-icon icon="times"></font-awesome-icon></b-button>
        </b-col>
      </b-row>
    </b-container>
    
    <b-table
      selectable
      striped
      select-mode="range"
      selectedVariant="success"
      :items="tracks"
      :fields="fields"
      @row-selected="rowSelected"
      responsive="sm"
      :busy="isBusy"
    >
      <div slot="table-busy" class="text-center text-danger my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>
      
      <template slot="name" slot-scope="row">
        <span v-if="row.item.name == ' '">Untitled</span><span v-else>{{ row.item.name }}</span>
      </template>
      
      <template slot="formatted" slot-scope="row">
        <div class="text-right">
          <b-badge variant="primary" class="text-uppercase">{{ row.item.format }}</b-badge> <b-badge variant="secondary" class="text-uppercase">{{ row.item.stereo }}</b-badge>
          <span v-if="row.item.format == 'protected'"><font-awesome-icon icon="lock"></font-awesome-icon></span><span v-else><font-awesome-icon icon="lock-open"></font-awesome-icon></span>
        </div>
      </template>

    </b-table>
    
  </div>
</template>

<script>
export default {
  data () {
    return {
      lsmd: [],
      tracks: [],
      isBusy: false,
      fields: [
        { key: 'no', sortable: true },
        { key: 'name', sortable: true },
        { key: 'formatted', label: '' }
      ],
      selected: []
    }
  },
  created () {
    this.readNetMd()
  },
  methods: {
    readNetMd: function () {
      this.tracks = []
      this.isBusy = true
      let py = require('child_process').spawn('python', ['/Users/gavinbenda/webdev/linux-minidisc/netmd/lsmd.py'])
      py.stdout.on('data', data => {
        // consume track listing
        // probably would be nicer to modify the python scripts to provide an API
        let response = data.toString()
        console.log(response)
        this.lsmd = response.split(/\r\n|\r|\n/)
        // now store only tracks
        for (var i = 0, len = this.lsmd.length; i < len; i++) {
          let line = this.lsmd[i]
          // bit of a dirty way of finding out lines that are track info
          // TODO: grab disc capacity here too
          if (/^\d+$/.test(line.substr(0, 3)) && line.charAt(3) === ':') {
            let parts = line.split(/\s+/)
            let track = {
              no: parts[0],
              format: parts[2],
              stereo: parts[3],
              status: parts[4],
              name: line.split(' ').slice(5).join(' ')
            }
            console.log(track)
            this.tracks.push(track)
          }
        }
      })
      py.on('close', () => {
        this.isBusy = false
      })
    },
    /**
      * Track which rows are selected
      */
    rowSelected: function (items) {
      this.selected = items
    },
    /**
      * Delete selected tracks
      * This is async so it happens in order and awaits each delete action to finish
      */
    deleteTracks: async function () {
      // loop through each selected track one-by-one
      for (var i = 0, len = this.selected.length; i < len; i++) {
        var trackNo = parseInt(this.selected[i].no, 10)
        console.log('deleting: ' + trackNo)
        let self = this
        await self.deleteTrack(trackNo)
          .then(await function () {
            console.log(i + ': deleted' + trackNo)
            // this feels a bit dirty, but works?
            if ((i + 1) === self.selected.length) {
              self.readNetMd()
            }
          })
      }
    },
    /**
      * Delete track using netmdcli
      */
    deleteTrack: function (trackNo) {
      // this.progress = 'Deleting Track: ' + trackNo
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn('/Users/gavinbenda/webdev/linux-minidisc/netmdcli/netmdcli', ['delete', trackNo])
        netmdcli.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          resolve()
        })
        netmdcli.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
      })
    },
    /**
      * Rename track using netmdcli
      */
    renameTrack: function (trackNo, title) {
      // this.progress = 'Renaming Track: ' + trackNo
      return new Promise((resolve, reject) => {
        trackNo = parseInt(trackNo, 10)
        let netmdcli = require('child_process').spawn('/Users/gavinbenda/webdev/linux-minidisc/netmdcli/netmdcli', ['rename', trackNo, title])
        netmdcli.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          resolve()
        })
        netmdcli.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
      })
    }
  }
}
</script>