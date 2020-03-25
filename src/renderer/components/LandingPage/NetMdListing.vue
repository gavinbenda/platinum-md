<template>
  <div>
    
    <b-modal @ok="renameTrack" ref="rename-track" title="Rename Track">
      <b-form-input v-model="renameTrackName" placeholder="Track Name"></b-form-input>
    </b-modal>
    
    <b-modal @ok="renameDisc" ref="rename-disc" title="Rename Disc">
      <b-form-input v-model="info.title" placeholder="Disc Name"></b-form-input>
    </b-modal>
    
    <b-modal @ok="moveTrack" ref="move-track" title="Move Track">
      <b-form-input v-model="newTrackPosition" placeholder="Move to position (number):"></b-form-input>
    </b-modal>
    
    <b-overlay :show="showOverlay" rounded="md" class="full-height">
      <b-container class="toolbar py-2">
        <b-row align-v="center">
          <b-col>
            <span v-if="info.device === ''">No Device Detected</span> <span v-else><b>{{ tracks.length }}</b> tracks on <i>{{ info.device }}</i></span><br />
            <b-badge class="text-uppercase" v-if="info.title !== ''"><a @click="showRenameDiscModal">{{ info.title }}</a></b-badge> 
            <b-badge class="text-uppercase" v-if="info.title !== ''">{{ info.availableTime }} Availible</b-badge>
          </b-col>
          <b-col class="text-right">
            <b-button variant="outline-light" @click="readNetMd" :disabled="isBusy">Rescan <font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
            <b-button variant="danger" @click="deleteTracks" :disabled="isBusy">Delete <font-awesome-icon icon="times"></font-awesome-icon></b-button>
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
      >
        <div slot="table-busy" class="text-center text-danger my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
        
        <template v-slot:cell(no)="data">
          <h5 class="mb-0"><b-badge>{{ data.item.no + 1 }}</b-badge></h5>
        </template>
        
        <template v-slot:cell(name)="data">
          {{ data.item.name }}
        </template>
        
        <template v-slot:cell(time)="data">
          <i>{{ data.item.time }}</i>
        </template>
        
        <template v-slot:cell(name)="data">
          <span v-if="data.item.name == ' '">Untitled</span><span v-else>{{ data.item.name }}</span>
          <a @click="showRenameModal(data.item.no, data.item.name)" title="Edit Track"><font-awesome-icon icon="edit"></font-awesome-icon></a>
          <a @click="showMoveTrackModal(data.item.no)" title="Move Track"><font-awesome-icon icon="random"></font-awesome-icon></a>
          <a @click="runAction('play', data.item.no)" title="Play Track"><font-awesome-icon icon="play"></font-awesome-icon></a>
        </template>
        
        <template v-slot:cell(formatted)="data">
          <div class="text-right" v-if="!isBusy">
            <b-badge variant="primary" class="text-uppercase">{{ data.item.format }}</b-badge> <b-badge variant="secondary" class="text-uppercase"><span v-if="data.item.bitrate != 'LP2' && data.item.bitrate != 'LP4'">SP / </span> -</b-badge>
            <span v-if="data.item.format == 'TrPROT'"><font-awesome-icon icon="lock"></font-awesome-icon></span><span v-else><font-awesome-icon icon="lock-open"></font-awesome-icon></span>
          </div>
        </template>
  
      </b-table>

      <template v-slot:overlay>
                
        <div class="text-center">
          <div v-if="communicating">
            <b-spinner varient="success" label="Spinner" variant="success"></b-spinner>
            <p id="cancel-label" class="mt-2">Negotiating with device...</p>
          </div>
          <div v-else>
          <font-awesome-icon icon="headphones" size="5x"></font-awesome-icon>
            <p id="cancel-label" class="mt-2">Device not detected.<br />Please connect/reconnect device to continue.</p>
          </div>
          <b-button
            ref="cancel"
            variant="outline-success"
            size="md"
            aria-describedby="cancel-label"
            @click="readNetMd"
          >
            Retry <font-awesome-icon icon="sync-alt"></font-awesome-icon>
          </b-button>
        </div>
      </template>
      
    </b-overlay>
    
  </div>
</template>

<script>
import bus from '@/bus'
import { netmdcliPath } from '@/binaries'
const usbDetect = require('usb-detection')
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
      renameTrackId: 0,
      oldTrackPosition: 0,
      newTrackPosition: 0,
      showOverlay: true,
      communicating: false
    }
  },
  mounted () {
    this.readNetMd()
    bus.$on('track-sent', () => {
      this.readNetMd()
    })
    bus.$on('netmd-status', (data) => {
      console.log(data.eventType)
      if (data.eventType === 'no-connection') {
        this.showOverlay = true
      } else {
        this.showOverlay = false
      }
      if (data.eventType === 'busy' || data.eventType === 'no-connection') {
        this.isBusy = true
      } else {
        this.isBusy = false
      }
    })
    bus.$on('track-action', (data) => {
      this.runAction(data.action, data.trackNo)
    })
    this.readNetMd()
    // USB auto-detection
    usbDetect.startMonitoring()
    usbDetect.on('add', async (device) => {
      // Device is not always immediately ready, retry until ready
      // This is not ideal.
      this.communicating = true
      let retries = 10
      for (let i = 0, len = retries; i < len; i++) {
        try {
          await this.readNetMd()
          break
        } catch (err) {
          console.log(err)
          await new Promise(async (resolve, reject) => setTimeout(resolve, 1500))
        }
      }
      this.communicating = false
    })
    usbDetect.on('remove', (device) => { this.readNetMd() })
    usbDetect.on('change', (device) => { this.readNetMd() })
  },
  methods: {
    /**
      * Use the netmdcli binary to read in info
      * The python output is actually easier to work with but can't include that in the app easily
      */
    readNetMd: function () {
      bus.$emit('netmd-status', { eventType: 'no-connection' })
      console.log('Attempting to read from NetMD')
      this.tracks = []
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn(netmdcliPath, ['-v'])
        /* netmdcli.on('close', (code) => {
          if (code === 0) {
            console.log('netmdcli returned Success code ' + code)
            resolve()
          }
        }) */
        netmdcli.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
        netmdcli.stdout.on('data', data => {
          // get JSON response from netmdcli, store full response for later
          let stringData = data.toString()
          console.log(stringData)
          if (this.IsJsonString(stringData)) {
            let jsonData = JSON.parse(stringData)
            this.info = jsonData
            // parse track data into array format for table display
            let results = Object.keys(jsonData.tracks).map((key) => {
              return jsonData.tracks[key]
            })
            this.tracks = results
            // This is an awful check, that I hate.
            // Ensure 'sane' data comes back before resolving
            if ((this.info.recordedTime !== '00:00:00.00' && this.tracks.length === 0) || (this.info.recordedTime === '00:00:00.00' && this.info.availableTime === '00:00:00.00')) {
              let errorMessage = { message: 'Device not ready, recordedTime: ' + this.info.recordedTime + ' availableTime: ' + this.info.availableTime + ' Tracks: ' + this.tracks.length }
              reject(errorMessage)
            } else {
              // Getting a response was successful, resolve and notify
              bus.$emit('netmd-status', { eventType: 'ready' })
              this.communicating = false
              resolve()
            }
          }
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
        console.log(title)
        let netmdcli = require('child_process').spawn(netmdcliPath, ['settitle', title])
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
      * Move track modal
      */
    showMoveTrackModal: function (trackNo) {
      this.oldTrackPosition = trackNo
      this.$refs['move-track'].show()
    },
    /**
      * Move track using netmdcli
      */
    moveTrack: function () {
      return new Promise((resolve, reject) => {
        let moveFrom = this.oldTrackPosition
        let moveTo = this.newTrackPosition - 1
        console.log('Moving track # ' + moveFrom + ' to #' + moveTo)
        console.log(moveFrom + ' --> ' + moveTo)
        let netmdcli = require('child_process').spawn(netmdcliPath, ['move', moveFrom, moveTo])
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
      * Run an action on a track (play/pause/stop/skip)
      */
    runAction: function (action, trackNo = 0) {
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn(netmdcliPath, [action, trackNo])
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
    onShown () {
      // Focus the cancel button when the overlay is showing
      this.$refs.cancel.focus()
    },
    onHidden () {
      // Focus the show button when the overlay is removed
      this.$refs.show.focus()
    },
    IsJsonString: function (str) {
      try {
        JSON.parse(str)
      } catch (e) {
        return false
      }
      return true
    }
  }
}
</script>
