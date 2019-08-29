<template>
  <div>
    
    <b-modal @ok="renameTrack" ref="rename-track" title="Rename Track">
      <b-form-input v-model="renameTrackName" placeholder="Track Name"></b-form-input>
    </b-modal>
    
    <b-modal @ok="renameDisc" ref="rename-disc" title="Rename Disc">
      <b-form-input v-model="info.title" placeholder="Disc Name"></b-form-input>
    </b-modal>
    
    <b-container class="toolbar py-2">
      <b-row align-v="center">
        <b-col>
          <span v-if="info.device === ''">No Device Detected</span> <span v-else><b>{{ tracks.length }}</b> tracks on <i>{{ info.device }}</i></span><br />
          <b-badge class="text-uppercase" v-if="info.title !== ''"><a @click="showRenameDiscModal">{{ info.title }}</a></b-badge> 
          <b-badge class="text-uppercase" v-if="info.title !== ''">{{ info.availableTime }} Availible</b-badge>
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
      select-mode="single"
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
        <span v-if="row.item.name == ' '">Untitled</span><span v-else>{{ row.item.name }}</span> <a @click="showRenameModal(row.item.no, row.item.name)"><font-awesome-icon icon="edit"></font-awesome-icon></a>
      </template>
      
      <template slot="formatted" slot-scope="row">
        <div class="text-right">
          <b-badge variant="primary" class="text-uppercase">{{ row.item.format }}</b-badge> <b-badge variant="secondary" class="text-uppercase"><span v-if="row.item.bitrate != 'LP2' && row.item.bitrate != 'LP4'">SP / </span>{{ row.item.bitrate }}</b-badge>
          <span v-if="row.item.format == 'TrPROT'"><font-awesome-icon icon="lock"></font-awesome-icon></span><span v-else><font-awesome-icon icon="lock-open"></font-awesome-icon></span>
        </div>
      </template>

    </b-table>
    
  </div>
</template>

<script>
import bus from '@/bus'
import { netmdcliPath } from '@/binaries'
export default {
  data () {
    return {
      lsmd: [],
      info: { title: '', device: '' },
      tracks: [],
      isBusy: false,
      fields: [
        { key: 'no', sortable: true },
        { key: 'name', sortable: true },
        { key: 'time', sortable: true },
        { key: 'formatted', label: '' }
      ],
      selected: [],
      renameTrackName: '',
      renameTrackId: 0
    }
  },
  mounted () {
    this.readNetMd()
    bus.$on('track-sent', () => {
      this.readNetMd()
    })
  },
  methods: {
    /**
      * Read track listingi n using lsmd.py
      */
    readNetMd2: function () {
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
      * Use the netmdcli binary to read in info
      * The python output is actually easier to work with but can't include that in the app easily
      */
    readNetMd: function () {
      this.tracks = []
      this.isBusy = true
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn(netmdcliPath, ['-v'])
        netmdcli.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          this.isBusy = false
          resolve()
        })
        netmdcli.stdout.on('data', data => {
          // get JSON response from netmdcli, store full response for later
          let response = JSON.parse(data.toString())
          this.info = response
          // parse track data into array format for table display
          let results = Object.keys(response.tracks).map((key) => {
            return response.tracks[key]
          })
          this.tracks = results
        })
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
        let netmdcli = require('child_process').spawn(netmdcliPath, ['delete', trackNo])
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
      * Rename track modal
      */
    showRenameModal: function (trackNo, title) {
      this.renameTrackName = title
      this.renameTrackId = trackNo
      this.$refs['rename-track'].show()
    },
    /**
      * Rename track using netmdcli
      */
    renameTrack: function (trackNo, title) {
      // this.progress = 'Renaming Track: ' + trackNo
      return new Promise((resolve, reject) => {
        trackNo = parseInt(this.renameTrackId, 10)
        console.log(trackNo + ':' + this.renameTrackName)
        let netmdcli = require('child_process').spawn(netmdcliPath, ['rename', trackNo, this.renameTrackName])
        netmdcli.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          this.readNetMd()
          resolve()
        })
        netmdcli.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
      })
    },
    /**
      * Rename track modal
      */
    showRenameDiscModal: function () {
      this.$refs['rename-disc'].show()
    },
    /**
      * Rename disc using netmdcli
      */
    renameDisc: function () {
      return new Promise((resolve, reject) => {
        let title = this.info.title
        let netmdcli = require('child_process').spawn(netmdcliPath, ['retitle', title])
        netmdcli.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          this.readNetMd()
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