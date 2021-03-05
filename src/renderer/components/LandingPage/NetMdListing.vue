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
      <b-container class="toolbar py-2 sticky-top">
        <b-row align-v="center">
          <b-col cols="1">
            <b-button variant="outline-light" @click="readNetMd" :disabled="isBusy"><font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
          </b-col>
          <b-col>
            <span v-if="info.device === ''">No Device Detected</span> <span v-else><b>{{ tracks.length }}</b> tracks on <i>{{ info.device }}</i></span><br />
            <b-button variant="link" class="p-0 m-0" @click="showRenameDiscModal"><b-badge class="text-uppercase" variant="primary" v-if="info.title !== ''">{{ info.title }} <font-awesome-icon icon="edit"></font-awesome-icon></b-badge></b-button>
            <b-badge class="text-uppercase" v-if="info.title !== ''">{{ info.availableTime }} Available</b-badge>
          </b-col>
          <b-col class="text-right" cols="auto">
            <b-button variant="success" @click="downloadTracks" v-show=download :disabled="isBusy"><font-awesome-icon icon="angle-double-left"></font-awesome-icon> Transfer</b-button>
            <b-button v-if="mode === 'md'" variant="danger" @click="deleteSelectedTracks" :disabled="isBusy"><font-awesome-icon icon="times"></font-awesome-icon></b-button>
            <b-dropdown v-if="mode === 'md'" class="danger my-0 py-0">
                <b-dropdown-item>
                  <b-button variant="danger" @click="eraseDisc" :disabled="isBusy" block>Erase Disc <font-awesome-icon icon="times"></font-awesome-icon></b-button>
                </b-dropdown-item>
            </b-dropdown>
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
          <a v-if="mode === 'md'" @click="showRenameModal(data.item.no, data.item.name)" title="Edit Track"><font-awesome-icon icon="edit"></font-awesome-icon></a>
          <a v-if="mode === 'md'" @click="showMoveTrackModal(data.item.no)" title="Move Track"><font-awesome-icon icon="random"></font-awesome-icon></a>
          <a v-if="mode === 'md'" @click="runAction('play', data.item.no)" title="Play Track"><font-awesome-icon icon="play"></font-awesome-icon></a>
        </template>

        <template v-slot:cell(formatted)="data">
          <div class="text-right" v-if="!isBusy">
            <b-badge variant="primary" class="text-uppercase">{{ data.item.format }}</b-badge> <b-badge variant="secondary" class="text-uppercase">{{ data.item.bitrate }}</b-badge>
            <span v-if="data.item.format == 'TrPROT'"><font-awesome-icon icon="lock"></font-awesome-icon></span><span v-else><font-awesome-icon icon="lock-open"></font-awesome-icon></span>
          </div>
        </template>

      </b-table>

      <template v-slot:overlay>
        <div class="text-center">
          <div v-if="(communicating && deviceMode == 'himd' && mode == 'himd') || (communicating && deviceMode == 'md' && mode == 'md')">
            <b-spinner varient="success" label="Spinner" variant="success"></b-spinner>
            <span v-if="deviceName"><p id="cancel-label" class="mt-2">Negotiating with {{ deviceName }}...</p></span><span v-else="deviceName"><p id="cancel-label" class="mt-2">Negotiating with device...</p></span>
          </div>
          <div v-if="communicating == false && mode == 'md'">
          <font-awesome-icon icon="headphones" size="5x"></font-awesome-icon>
            <p id="cancel-label" class="mt-2"><b>NetMD device not detected.</b><br />Please connect/reconnect device to continue.</p>
          </div>
          <div v-if="communicating == false && mode == 'himd'">
          <font-awesome-icon icon="headphones" size="5x"></font-awesome-icon>
            <p id="cancel-label" class="mt-2"><b>HiMD Device not detected, or cannot open path: {{ himdPath }} </b><br />Please connect/reconnect device to continue.</p>
          </div>
          <div v-if="deviceMode == 'himd' && mode == 'md'">
            <p id="cancel-label" class="mt-2"><b>HiMD device detected</b></p>
            <p id="cancel-label" class="mt-2">To use netmd, change device mode to MD/reformat disc to MD. </p>
            <p id="cancel-label" class="mt-2">To use HiMD, select 'Hi-MD' mode in platinum-md Settings menu.</p>
            <p id="cancel-label" class="mt-2">Sometimes this can appear if swapping between MD/HiMD discs without unplugging/replugging device - if you belive this to be incorrect, try unplugging/replugging</p>
          </div>
          <div v-if="deviceMode == 'md' && mode == 'himd'">
            <p id="cancel-label" class="mt-2"><b>NetMD device detected</b></p>
            <p id="cancel-label" class="mt-2">To use NetMD, select 'MD' mode in platinum-md Settings menu.</p>
            <p id="cancel-label" class="mt-2">Sometimes this can appear if swapping between MD/HiMD discs without unplugging/replugging device - if you belive this to be incorrect, try unplugging/replugging</p>
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
import { netmdcliPath, himdcliPath } from '@/binaries'
import { convertAudio, ensureDirSync } from '@/common'
import { sonyVid, sharpVid, sonyMDPids, sonyHiMDPids, sharpPids } from '@/deviceIDs'
const checkDiskSpace = require('check-disk-space')
const usbDetect = require('usb-detection')
const homedir = require('os').homedir()
const del = require('del')
const Store = require('electron-store')
const store = new Store()
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
      communicating: false,
      downloadDir: homedir + '/pmd-music/',
      downloadFormat: 'FLAC',
      download: false,
      useSonicStageNos: true,
      progress: 'Idle',
      himdPath: '',
      mode: 'md',
      deviceMode: 'md',
      deviceName: null
    }
  },
  mounted () {
    this.readNetMd()
    bus.$on('track-sent', () => {
      this.readNetMd()
    })
    bus.$on('netmd-status', (data) => {
      if ('eventType' in data) {
        console.log(data)
        if (data.eventType === 'no-connection') {
          this.showOverlay = true
        } else {
          this.showOverlay = false
        }
      }
      if ('isBusy' in data) {
        this.isBusy = data.isBusy
      }
      if ('deviceName' in data) {
        this.download = (data.deviceName === 'Sony MZ-RH1') || (this.mode === 'himd')
      }
      if ('progress' in data) {
        this.progress = data.progress
        console.log('progress ' + this.progress)
      }
    })
    bus.$on('track-action', (data) => {
      this.runAction(data.action, data.trackNo)
    })
    bus.$on('config-update', () => {
      this.readConfig()
      this.readNetMd()
    })

    this.readNetMd()
    // USB auto-detection
    usbDetect.startMonitoring()
    usbDetect.on('add', async (device) => {
      console.log(device)
      let retries = 10
      let mdTimeout = 1500
      let himdTimeout = 3000
      switch (device.vendorId) {
        case sonyVid:
          if (device.productId in sonyMDPids) {
            // Sony NetMD
            this.deviceMode = 'md'
            this.deviceName = sonyMDPids[device.productId]
            console.log('Sony MD: ' + this.deviceName)

            // Device is not always immediately ready, retry until ready
            // This is not ideal.
            this.communicating = true
            await new Promise(async (resolve, reject) => setTimeout(resolve, 1500))
            this.connectToDevice(retries, mdTimeout)
          } else if (device.productId in sonyHiMDPids) {
            // Sony HiMD
            this.deviceMode = 'himd'
            this.deviceName = sonyHiMDPids[device.productId]
            console.log('Sony HiMD: ' + this.deviceName)

            // Device is not always immediately ready, retry until ready
            // This is not ideal.
            this.communicating = true
            await new Promise(async (resolve, reject) => setTimeout(resolve, 4000))
            this.connectToDevice(retries, himdTimeout)
          } else {
            console.log('Unknown Sony product')
          }
          break

        case sharpVid:
          // Sharp NetMD
          if (device.productId in sharpPids) {
            this.deviceMode = 'md'
            this.deviceName = sharpPids[device.productId]
            console.log('SharpMD: ' + this.deviceName)

            // Device is not always immediately ready, retry until ready
            // This is not ideal.
            this.communicating = true
            await new Promise(async (resolve, reject) => setTimeout(resolve, 1500))
            this.connectToDevice(retries, mdTimeout)
          } else {
            console.log('Unknown Sharp product')
          }
          break
      }
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
      bus.$emit('netmd-status', { eventType: 'no-connection', deviceName: '' })
      this.communicating = true
      if (this.mode === 'himd') {
        console.log('Attempting to read from HiMD')
      } else {
        console.log('Attempting to read from NetMD')
      }
      this.tracks = []
      return new Promise((resolve, reject) => {
        let netmdcli
        let stringData = ''
        if (this.mode === 'himd') {
          netmdcli = require('child_process').spawn(himdcliPath, [this.himdPath, 'tracks', 'json'])
        } else {
          netmdcli = require('child_process').spawn(netmdcliPath, ['-v'])
        }
        netmdcli.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
        netmdcli.stdout.on('data', data => {
          // buffer output from netmdcli
          stringData += data.toString()
        })
        netmdcli.on('close', (code) => {
          // on exit, process the output data
          // get JSON response from netmdcli, store full response for later
          console.log(stringData)
          if (this.IsJsonString(stringData)) {
            let jsonData = JSON.parse(stringData)
            this.info = jsonData
            if (this.mode === 'himd') {
              checkDiskSpace(this.himdPath).then((discspace) => {
                this.info.device = 'Hi-MD: ' + this.himdPath
                bus.$emit('netmd-status', { 'freeSpace': discspace.free })
                this.info.availableTime = this.formatBytes(discspace.free)
              })
            }
            // parse track data into array format for table display
            let results = Object.keys(jsonData.tracks).map((key) => {
              return jsonData.tracks[key]
            })
            this.tracks = results
            console.log(results)
            console.log(this.info.recordedTime !== '00:00:00.00' && this.tracks.length === 0)

            // if in netmd mode, check that valid data comes back - sometimes this can return placeholder data if quieried shortly after device connection
            if (this.mode === 'md') {
              // This is an awful check, that I hate.
              // Ensure 'sane' data comes back from netmdcli before resolving
              if ((this.info.recordedTime !== '00:00:00.00' && this.tracks.length === 0) || (this.info.recordedTime === '00:00:00.00' && this.info.availableTime === '00:00:00.00')) {
                let errorMessage = { message: 'Device not ready, recordedTime: ' + this.info.recordedTime + ' availableTime: ' + this.info.availableTime + ' Tracks: ' + this.tracks.length }
                reject(errorMessage)
              } else if (this.tracks.length > 0) {
                if ((this.tracks[0]['protect'] === 'UNKNOWN') && (this.tracks[0]['bitrate'] === 'UNKNOWN') && (this.tracks[0]['name'] === '')) {
                  let errorMessage = { message: 'Device not ready, recordedTime: ' + this.info.recordedTime + ' availableTime: ' + this.info.availableTime + ' Tracks: ' + this.tracks.length }
                  reject(errorMessage)
                }
              }
            }
            // Getting a response was successful, resolve and notify
            bus.$emit('netmd-status', { eventType: 'ready' })
            bus.$emit('netmd-status', { progress: 'Idle' })
            this.communicating = false
            resolve()
          } else if (stringData.includes('no NetMD device')) {
            // netmd cli cannot connect to a device
            this.info.device = ''
            this.info.availableTime = ''
            this.info.title = ''
            this.communicating = false
            console.log('no devices found')
            let errorMessage = { message: 'No NetMD devices found' }
            reject(errorMessage)
          } else if (stringData.includes('Error opening directory')) {
            this.info.device = ''
            this.info.availableTime = ''
            this.info.title = ''
            this.communicating = false
            let errorMessage = { message: 'Cannot open himd directory' }
            reject(errorMessage)
          } else {
            console.error('CLI did not return valid json data')
          }
        })
        // if RH1, show button. VID/PID taken from libnetmd/netmd_dev.c {0x54c, 0x286}
        usbDetect.find(0x54c, 0x286, function (err, devices) {
          if (err) {
            console.log(err)
            throw err
          }
          if (devices.length) bus.$emit('netmd-status', { deviceName: 'Sony MZ-RH1' })
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
      * Erase All
      * This deletes all tracks, I'd prefer this to do a proper "erase" command later.
      */
    eraseDisc: async function () {
      let self = this
      await this.deleteTrack(0, this.tracks.length)
        .then(await function () {
          self.readNetMd()
        })
    },
    /**
      * Delete a selected track
      * This will allow to select a range of tracks in the future
      */
    deleteSelectedTracks: async function () {
      if (this.selected[0] !== undefined) {
        for (const track of this.selected.reverse()) {
          console.log('Deleting: ' + track.no)
          await this.deleteTrack(track.no, track.no)
        }
        this.readNetMd()
      }
    },
    /**
      * Delete track using netmdcli
      */
    deleteTrack: async function (trackFrom, trackTo) {
      // this.progress = 'Deleting Track: ' + trackNo
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn(netmdcliPath, ['delete', trackFrom, trackTo])
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
    },
    /**
      * Download selected track from player and convert.
      */
    downloadTracks: async function () {
      // if button is clicked but nothing is selected, do nothing
      if (this.selected.length < 1) return
      bus.$emit('netmd-status', { isBusy: true })
      // local copy of selected, otherwise this is undefined by the second iteration of the loop
      var selectedTracks
      var downloadPath = this.downloadDir
      await new Promise(async (resolve, reject) => {
        selectedTracks = JSON.parse(JSON.stringify(this.selected))
        resolve()
      })
      // Check or Create temp directory
      try {
        if (this.info.title !== '<Untitled>') {
          downloadPath = this.downloadDir + this.info.title
        }
        ensureDirSync(downloadPath)
        console.log('Download directory created')
      } catch (err) {
        // TODO: notify user could not create download dir
        console.log('Could not create download directory')
        console.error(err)
      }

      for (var i = 0, len = selectedTracks.length; i < len; i++) {
        var trackno = selectedTracks[i].no + 1
        console.log('Downloading track from device: ' + trackno)
        if (selectedTracks.length === 1) {
          bus.$emit('netmd-status', { progress: 'Downloading track ' + trackno })
        } else {
          bus.$emit('netmd-status', { progress: 'Downloading track ' + trackno + ' of ' + selectedTracks.length })
        }
        const downloadFile = await this.fetchTrack(downloadPath, trackno, selectedTracks[i].name, selectedTracks[i].bitrate.trim())
        // timeout to avoid python errors when pulling multiple tracks
        await new Promise(async (resolve, reject) => setTimeout(resolve, 3000))

        // convert to selected audio format
        let promise = new Promise(async (resolve, reject) => {
          if (downloadFile !== '' && this.downloadFormat !== 'RAW') {
            let outputFile = downloadFile.toString().replace(downloadFile.split('.').pop(), this.downloadFormat.toLowerCase())
            console.log('Converting downloadFile: ' + downloadFile + ' to ' + outputFile)
            await convertAudio(downloadFile, outputFile, this.downloadFormat)
            resolve((
              del.sync([downloadFile], {force: true})))
          }
        })
        promise.finally()
      }

      this.readNetMd()
      bus.$emit('netmd-status', { progress: 'Idle' })
    },
    /**
      * Fetch track from rh1
      */
    fetchTrack: async function (downloadPath, trackNo, trackName, trackFormat) {
      return new Promise(async (resolve, reject) => {
        let extensions = {
          'AT3': '.at3',
          'AT3+': '.oma',
          'LP2': '.at3',
          'LP4': '.at3',
          'LPCM': '.pcm',
          'MP3': '.mp3',
          'SP': '.aea'
        }
        let extension = extensions[trackFormat]
        let downloadFile = downloadPath + '/'
        if (this.useSonicStageNos) {
          downloadFile += `00${trackNo}`.slice(-3) + '-' + trackName + extension
        } else {
          downloadFile += trackName + extension
        }
        console.log('download file ' + downloadFile + ' track format: ' + trackFormat)
        let mdcli
        if (this.mode === 'himd') {
          let dumpcmd = (trackFormat === 'MP3') ? 'dumpmp3' : 'dumpnonmp3'
          mdcli = require('child_process').spawn(himdcliPath, [this.himdPath, dumpcmd, trackNo, downloadFile])
        } else {
          mdcli = require('child_process').spawn(netmdcliPath, ['-v', 'recv', trackNo, downloadFile])
        }

        mdcli.on('close', (code) => {
          if (code === 0) {
            console.log('Finished fetchtrack download of track ' + trackNo)
            resolve(downloadFile)
          } else {
            console.log('cli error, returned ' + code)
            reject(code)
          }
        })
        mdcli.stdout.on('data', data => {
          var message = data.toString()
          if (message.match(/\d\d\.\d/)) {
            bus.$emit('netmd-status', { progress: 'Downloading track ' + trackNo + ' - ' + message })
          }
        })
      })
    },
    /*
     * Format free space into something human readable
     * from: https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
     */
    formatBytes: function (bytes, decimals = 2) {
      if (bytes === 0) return '0 Bytes'

      const k = 1024
      const dm = decimals < 0 ? 0 : decimals
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

      const i = Math.floor(Math.log(bytes) / Math.log(k))

      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    },
    /*
     * retry wrapper for connecting to MD devices
     */
    connectToDevice: async function (retries, timeout) {
      for (var i = 0; i < retries; i++) {
        this.progress = 'Connecting to ' + this.deviceName
        this.communicating = true
        try {
          console.log('Connect to device, Try ' + (i + 1))
          await this.readNetMd()
          this.progress = 'Idle'
          break
        } catch (err) {
          console.log(err)
          await new Promise(async (resolve, reject) => setTimeout(resolve, timeout))
        }
      }
      if (i === retries) {
        // Feels like there should be a nicer way of resetting status if you roll off the end of the loop
        this.deviceName = null
        this.progress = 'Idle'
      }
      this.communicating = false
    },
    /**
      * Read-in config file
      */
    readConfig: function () {
      if (store.has('downloadDir')) {
        this.downloadDir = store.get('downloadDir')
      }
      if (store.has('downloadFormat')) {
        this.downloadFormat = store.get('downloadFormat')
        console.log('this.downloadFormat ' + this.downloadFormat)
      }
      if (store.has('useSonicStageNos')) {
        this.useSonicStageNos = store.get('useSonicStageNos')
      }
      if (store.has('mode')) {
        this.mode = store.get('mode')
      }
      if (store.has('himdPath')) {
        this.himdPath = store.get('himdPath')
      }
    }
  }
}
</script>
