<template>
  <div>

    <b-modal @ok="editTrack" ref="edit-track" title="Edit Track">
      <b-row class="my-1">
        <b-col sm="2">
          <label for="input-small">No:</label>
        </b-col>
        <b-col sm="10">
          <b-form-input v-model="selectedTrack.trackNo" placeholder="Track Number:"></b-form-input>
        </b-col>
      </b-row>
      <b-row class="my-1">
        <b-col sm="2">
          <label for="input-small">Title:</label>
        </b-col>
        <b-col sm="10">
          <b-form-input v-model="selectedTrack.title" placeholder="Title"></b-form-input>
        </b-col>
      </b-row>
      <b-row class="my-1">
        <b-col sm="2">
          <label for="input-small">Artist:</label>
        </b-col>
        <b-col sm="10">
          <b-form-input v-model="selectedTrack.artist" placeholder="Artist"></b-form-input>
        </b-col>
      </b-row>
    </b-modal>

    <b-container class="toolbar py-2 m-0 sticky-top">
      <b-row align-v="center">
        <b-col cols="1">
          <b-button variant="outline-light" @click="readDirectory" :disabled="isBusy"><font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
        </b-col>
        <b-col class="no-linewrap">
          <b>{{ selected.length }}</b> tracks selected ({{ selectedTrackTime | timeFormat }}).<br />
          <b-button variant="link" class="p-0 m-0" @click="chooseDir"><b-badge class="text-uppercase">{{ dir }}</b-badge></b-button>
        </b-col>
        <b-col class="text-right" cols="auto">
          <b-button variant="primary" @click="chooseDir">Folder <font-awesome-icon icon="folder-open"></font-awesome-icon></b-button>
          <b-button variant="success" @click="upload" :disabled="isBusy">Transfer <font-awesome-icon icon="angle-double-right"></font-awesome-icon></b-button>
        </b-col>
      </b-row>
    </b-container>

    <b-table
      selectable
      striped
      select-mode="range"
      selectedVariant="success"
      :items="files"
      :fields="fields"
      @row-selected="rowSelected"
      responsive="sm"
      sortable="true"
      sortBy="trackNo"
    >
      <div slot="table-busy" class="text-center text-danger my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>

      <template v-slot:cell(trackNo)="data">
        <div>
          <h5 class="mb-0"><b-badge>{{ data.item.trackNo }}</b-badge></h5>
        </div>
      </template>

      <template v-slot:cell(bitrate)="data">
        <div class="text-right">
          <b-badge variant="success" class="text-uppercase">{{ data.item.bitrate }} {{ data.item.codec }}</b-badge>
        </div>
      </template>

      <template v-slot:cell(time)="data">
        <div class="text-right">
          {{ data.item.time | timeFormat }}
        </div>
      </template>

      <template v-slot:cell(options)="data">
        <div class="text-right">
          <a @click="showEditModal(data.item)"><font-awesome-icon icon="edit"></font-awesome-icon></a>
        </div>
      </template>

    </b-table>

  </div>
</template>

<script>
import bus from '@/bus'
import { atracdencPath, netmdcliPath, himdcliPath } from '@/binaries'
import { convertAudio, ensureDirSync, stripID3, sanitizeName } from '@/common'
import clone from 'lodash/clone'
import os from 'os'
import path from 'path'
const fs = require('fs-extra')
const del = require('del')
const readChunk = require('read-chunk')
const fileType = require('file-type')
const mm = require('music-metadata')
const { remote } = require('electron')
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path.replace('app.asar', 'app.asar.unpacked')
const ffmpeg = require('fluent-ffmpeg')
ffmpeg.setFfmpegPath(ffmpegPath)
const Store = require('electron-store')
const store = new Store()
export default {
  data () {
    return {
      dir: '',
      files: [],
      file: '',
      progress: 'Idle',
      progressPercent: 0,
      isBusy: false,
      fields: [
        { key: 'trackNo', sortable: true, label: 'No' },
        { key: 'title', sortable: true },
        { key: 'artist', sortable: true },
        { key: 'time', sortable: true },
        // { key: 'album', sortable: true },
        'bitrate',
        { key: 'options', label: '' }
      ],
      selected: [],
      processing: 0,
      config: {},
      conversionMode: 'SP',
      titleFormat: '%title% - %artist%',
      sonicStageNosStrip: 'true',
      bitrate: 128,
      selectedTrack: {
        trackNo: 0
      },
      selectedTrackSource: {},
      tempDirectory: 'pmd-temp',
      mode: 'md',
      himdPath: ''
    }
  },
  created () {
    this.readConfig()
  },
  mounted () {
    this.readDirectory()
    // check temp directory has trailing slash on linux
    if (os.platform() === 'linux') {
      let tmpdir = os.tmpdir()
      if (!tmpdir.endsWith('/')) {
        this.tempDirectory = '/' + tmpdir
      }
    }
    bus.$on('config-update', () => {
      console.log('config-update recieved.')
      this.readConfig()
    })
    bus.$on('netmd-status', (data) => {
      if ('eventType' in data) {
        console.log(data.eventType)
      }
      if ('isBusy' in data) {
        this.isBusy = data.isBusy
      }
      if ('freeSpace' in data) {
        this.freeSpace = data.freeSpace
      }
    })
  },
  methods: {
    chooseDir: function () {
      remote.dialog.showOpenDialog({
        properties: ['openDirectory'],
        defaultPath: this.dir
      }, names => {
        if (names != null) {
          console.log('selected directory:' + names[0])
          store.set('baseDirectory', names[0] + path.sep)
          this.dir = store.get('baseDirectory')
          this.readDirectory()
        }
      })
    },
    /**
      * Reads the selected directory and displays all compatable files
      * At this stage it's simply any file that contain valid metadata
      * TODO: there should be more promises used here
      */
    readDirectory: function () {
      bus.$emit('netmd-status', { isBusy: true })
      this.files = []
      // read the target directory
      console.log(this.dir)
      fs.readdir(this.dir, (err, dir) => {
        // loop through results
        for (let filePath of dir) {
          // ensure that we're only working with files
          if (fs.statSync(this.dir + filePath).isFile()) {
            let buffer = readChunk.sync(this.dir + filePath, 0, fileType.minimumBytes)
            let fileTypeInfo = fileType(buffer)
            if (fileTypeInfo != null) {
              // read metadata
              mm.parseFile(this.dir + filePath, {native: true})
                .then(metadata => {
                  // console.log(metadata)
                  // Get data for file object
                  let title = (metadata.common.title !== undefined) ? metadata.common.title : (this.sonicStageNosStrip === true) ? path.parse(filePath).name.replace(RegExp(/^\d\d\d-/), '') : path.parse(filePath).name
                  let artist = (metadata.common.artist !== undefined) ? metadata.common.artist : 'No Artist'
                  let album = (metadata.common.album !== undefined) ? metadata.common.album : '-'
                  let bitrate = (metadata.format.bitrate !== undefined) ? metadata.format.bitrate : ''
                  let codec = (metadata.format.codec !== undefined) ? metadata.format.codec.replace(/^MPEG [12] Layer 3$/, 'MP3') : ''
                  let trackNo = (metadata.common.track.no !== undefined) ? metadata.common.track.no : ''
                  let time = (metadata.format.duration !== undefined) ? metadata.format.duration : 0
                  // filter forbidden filesystem characters
                  // Windows list from: https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
                  if (os.platform() === 'win32') {
                    artist = (artist !== null) ? artist.substring(0, 255).replace(/[<>:"/\\|?*]/g, '_') : ''
                    title = (title !== null) ? title.substring(0, 255).replace(/[<>:"/\\|?*]/g, '_') : ''
                  } else {
                    artist = (artist !== null) ? artist.substring(0, 255).replace('/', '_') : ''
                    title = (title !== null) ? title.substring(0, 255).replace('/', '_') : ''
                  }
                  // write the relevent data to the files array
                  this.files.push({
                    fileName: filePath,
                    artist,
                    title,
                    album: (album !== null) ? album : '',
                    trackNo: (trackNo !== null) ? trackNo : 0,
                    format: fileTypeInfo.ext,
                    bitrate: (bitrate !== null) ? Math.round(bitrate / 1000) + 'kbps' : '-',
                    codec: (codec !== null) ? codec : '',
                    time: time,
                    no_metadata: metadata.common.title
                  })
                })
                .catch(err => {
                  console.error(err.message)
                })
            }
          }
        }
        // this.files = dir
        if (err) { console.log(err) }
      })
      bus.$emit('netmd-status', { isBusy: false })
    },
    /**
      * Track which rows are selected
      */
    rowSelected: function (items) {
      this.selected = items
    },
    /**
      * Upload (and convert) selected tracks to player
      * This is async so it happens in order and awaits each upload to finish
      */
    upload: async function () {
      // loop through each selected track one-by-one
      for (var i = 0, len = this.selected.length; i < len; i++) {
        console.log('Processing track: ' + i)
        bus.$emit('netmd-status', { isBusy: true })
        // create a temp directory for working files
        // TODO: maybe some automated cleanup?
        this.processing = i + 1
        var fileName = this.selected[i].fileName
        // Check or Create temp directory
        try {
          ensureDirSync(path.join(os.tmpdir(), this.tempDirectory))
          console.log('Directory created' + path.join(os.tmpdir(), this.tempDirectory))
        } catch (err) {
          console.error(err)
        }
        // Convert to desired format, strip 'No Artist' rather than writing to disc
        var artistName = (this.selected[i].artist !== 'No Artist') ? this.selected[i].artist : ''
        let finalFile = await this.convert(fileName, this.selected[i])
        let trackTitle = sanitizeName(this.titleFormat.replace(/%title%/g, this.selected[i].title).replace(/%artist%/g, artistName).replace(/%trackno%/g, this.selected[i].trackNo))
        console.log('Title: ' + trackTitle)
        console.log('Conversion Complete: ' + finalFile)
        await this.sendToPlayer(finalFile, trackTitle)
        bus.$emit('netmd-status', { eventType: 'transfer-completed', isBusy: false })
      }
      // Clean up
      const deletedPaths = await del.sync([path.join(os.tmpdir(), this.tempDirectory)], {force: true})
      console.log('Deleting:\n', deletedPaths.join('\n'))
    },
    /**
      * Convert input audio file to WAV file using ffmpeg
      * This MUST be 44100 and 16bit for the atrac encoder to work
      */
    convert: async function (fileName, selectedFile) {
      return new Promise(async (resolve, reject) => {
        var filePath = this.dir + fileName
        console.log(filePath)
        var sourceFile = filePath
        let fileExtension = '.' + sourceFile.split('.').pop()
        var destFile = path.join(os.tmpdir(), this.tempDirectory, fileName.replace(fileExtension, '.raw.wav'))
        var atracFile = path.join(os.tmpdir(), this.tempDirectory, fileName.replace(fileExtension, '.at3'))
        var finalFile = path.join(os.tmpdir(), this.tempDirectory, selectedFile.title + ' - ' + selectedFile.artist + '.wav')
        let self = this
        // If sending in SP mode
        // Convert to Wav and send to NetMD Device
        // The encoding process is handled by the NetMD device
        console.log('Starting conversion in <' + this.conversionMode + '> mode')
        if (this.conversionMode === 'SP') {
          bus.$emit('netmd-status', { progress: 'Converting to Wav' })
          await convertAudio(sourceFile, finalFile, fileExtension)
        // uploading as LP2
        // This uses an experimental ATRAC3 encoder
        // The files are converted into ATRAC locally, and then sent to the NetMD device
        } else if (this.conversionMode === 'LP2' || this.conversionMode === 'LP4') {
          // check the filetype, and choose the output
          switch (this.conversionMode) {
            case 'LP2':
              this.bitrate = 128
              break
            case 'LP4':
              this.bitrate = 64
              break
          }
          await convertAudio(sourceFile, destFile)
          await self.convertToAtrac(destFile, atracFile)
          await self.convertToWavWrapper(atracFile, finalFile)
        } else {
          // !SP and !LP, so must be hi-md - Convert to MP3
          finalFile = path.join(os.tmpdir(), this.tempDirectory, fileName.replace(fileExtension, '.mp3'))
          if (fileExtension.toLowerCase() === '.mp3') {
            // file is already a mp3, no need to convert
            // Strip id3v2 tag because it can cause tracks to be unplayable on device
            await stripID3(sourceFile, finalFile)
          } else {
            // file is not mp3
            bus.$emit('netmd-status', { progress: 'Converting to MP3' })
            let title = (selectedFile.no_metadata === undefined) ? selectedFile.title : null
            await convertAudio(sourceFile, finalFile, 'MP3', title)
          }
        }
        resolve(finalFile)
      })
    },
    /**
      * Pass WAV file to atracdenc
      * TODO: this is the longest part of the process, some user progress % feedback would be nice...
      */
    convertToAtrac: async function (source, dest) {
      bus.$emit('netmd-status', { progress: 'Converting to ATRAC', progressPercent: 0 })
      console.log('Converting to atrac')
      return new Promise(async (resolve, reject) => {
        // spawn this task and resolve promise on close
        let atracdenc = require('child_process').spawn(atracdencPath, ['-e', 'atrac3', '-i', source, '-o', dest, '--bitrate', this.bitrate])
        // console.log(atracdenc)
        atracdenc.on('close', (code) => {
          if (code === 0) {
            console.log('atracdenc returned Success code ' + code)
            resolve()
          }
        })
        atracdenc.on('error', (error) => {
          console.log(`atracdenc errored with error ${error}`)
          reject(error)
        })
        // we get a fair bit of useful progress data returned here for debugging
        atracdenc.stdout.on('data', data => {
          var output = data.toString()
          console.log(data.toString())
          bus.$emit('netmd-status', { progress: 'Converting to ATRAC', progressPercent: output.substr(3, 3) })
        })
      })
    },
    /**
      * Apply the WAV wrapper around the converted file
      * This is required to be able to send using netmdcli
      */
    convertToWavWrapper: async function (source, dest) {
      bus.$emit('netmd-status', { progress: 'Adding Wav Wrapper' })
      return new Promise(async (resolve, reject) => {
        ffmpeg(source)
          .output(dest)
          .audioCodec('copy')
          .on('progress', function (progress) {
            console.log('Processing: ' + progress.timemark + ' done ' + progress.targetSize + ' kilobytes')
          })
          // If successful, resolve
          .on('end', function () {
            console.log('ffmpeg completed successfully')
            resolve()
          })
          // Reject if we get any errors
          .on('error', function (err) {
            console.log('ffmpeg error: ' + err.message)
            reject(err.message)
          })
          .run()
      })
    },
    /**
      * Send final file using netmdcli
      * The filename is named {title} - {artist}
      */
    sendToPlayer: async function (file, trackTitle) {
      bus.$emit('netmd-status', { progress: 'Sending to Player' })
      if (this.mode === 'md') {
        console.log('Attempting to send to NetMD device')
      } else {
        console.log('Attempting to send to HiMD device')
      }
      // send off command, we wrap this so it can be retryed
      // not 100% on this method, may refactor in the future
      let retries = 5
      for (let i = 0, len = retries; i < len; i++) {
        try {
          await this.sendCommand(file, trackTitle)
          break
        } catch (err) {
          console.log(err.message)
          if (err.message === 'Disc Full') {
            return
          }
          console.log('Attempt to send file failed, retrying...')
          await new Promise(async (resolve, reject) => setTimeout(resolve, 2000))
        }
      }
    },
    sendCommand: async function (file, trackTitle) {
      return new Promise(async (resolve, reject) => {
        let netmdcli
        let cliname
        if (this.mode === 'himd') {
          cliname = 'himdcli'
          // check that disc is not full
          let size = fs.statSync(file).size
          if (size > this.freeSpace) {
            console.log('ERROR: track ' + file + ' larger than free space on himd device')
            bus.$emit('netmd-status', { progress: 'Disc Full' })
            return (Error('Disc Full'))
          } else {
            // transfer track  to himd
            console.log(himdcliPath + ' ' + this.himdPath + ' writemp3 ' + file)
            netmdcli = require('child_process').spawn(himdcliPath, [this.himdPath, 'writemp3', file])
            // himdcli doesnt provide status updates, so set status instead of waiting on output
            bus.$emit('netmd-status', { progress: 'Transferring: ' + trackTitle, progressPercent: '50' })
          }
        } else {
          cliname = 'netmdcli'
          // transfer track to netmd
          netmdcli = require('child_process').spawn(netmdcliPath, ['-v', 'send', file, trackTitle])
        }
        netmdcli.on('close', (code) => {
          if (code === 0) {
            console.log(cliname + ' send returned Success code ' + code)
            bus.$emit('track-sent')
            // timeout to let readnetmd complete before starting next transfer
            resolve(new Promise(async (resolve, reject) => setTimeout(resolve, 1500)))
          } else {
            console.log(cliname + ' error, returned ' + code)
            reject(code)
          }
          bus.$emit('netmd-status', { progress: 'Idle' })
        })
        netmdcli.on('error', (error) => {
          console.log(cliname + ` send errored with error ${error}`)
          reject(error)
        })
        // we get a fair bit of useful progress data returned here for debugging
        netmdcli.stdout.on('data', data => {
          var output = data.toString()
          console.log(output)
          if (output.includes('%) transferred')) {
            bus.$emit('netmd-status', { progress: 'Transferring: ' + trackTitle, progressPercent: output.split('bytes (').pop().split(') transferred')[0] })
          }
        })
      })
    },
    /**
      * Move track modal
      */
    showEditModal: function (track) {
      console.log(track)
      this.selectedTrack = clone(track, true)
      this.selectedTrackSource = track
      this.$refs['edit-track'].show()
    },
    /**
    * Edit track
    */
    editTrack: function () {
      this.selectedTrackSource.trackNo = this.selectedTrack.trackNo
      this.selectedTrackSource.title = this.selectedTrack.title
      this.selectedTrackSource.artist = this.selectedTrack.artist
    },
    /**
      * Read-in config file
      */
    readConfig: function () {
      if (store.has('baseDirectory')) {
        this.dir = store.get('baseDirectory')
      }
      if (store.has('conversionMode')) {
        this.conversionMode = store.get('conversionMode')
      }
      if (store.has('titleFormat')) {
        this.titleFormat = store.get('titleFormat')
      }
      if (store.has('sonicStageNosStrip')) {
        this.sonicStageNosStrip = store.get('sonicStageNosStrip')
      }
      if (store.has('mode')) {
        this.mode = store.get('mode')
      }
      if (store.has('himdPath')) {
        this.himdPath = store.get('himdPath')
      }
    },
    /**
    * Calculate selected track time total
    */
    getSelectedTrackTime: function () {
      return this.selected.reduce((acc, data) => {
        console.log(data.time)
        return acc + data.time
      }, 0)
    }
  },
  /**
  * Computed property to return total time
  */
  computed: {
    selectedTrackTime: function () {
      return this.getSelectedTrackTime()
    }
  }
}
</script>
