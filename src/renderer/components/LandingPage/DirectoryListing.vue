<template>
  <div>
    <b-container class="toolbar py-2">
      <b-row align-v="center">
        <b-col>
          <b>{{ selected.length }}</b> tracks selected / <span v-if="progress">{{ progress }}</span>
        </b-col>
        <b-col class="text-right">
          <b-button variant="outline-light" @click="readDirectory">Rescan <font-awesome-icon icon="sync-alt"></font-awesome-icon></b-button>
          <b-button variant="success" @click="upload">Transfer <font-awesome-icon icon="angle-double-right"></font-awesome-icon></b-button>
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
      :busy="isBusy"
    >
      <div slot="table-busy" class="text-center text-danger my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>
      
      <template slot="bitrate" slot-scope="row">
        <div class="text-right">
          <b-badge variant="success" class="text-uppercase">{{ row.item.bitrate }}</b-badge>
        </div>
      </template>
      
    </b-table>
 
  </div>
</template>

<script>
const fs = require('fs-extra')
const readChunk = require('read-chunk')
const fileType = require('file-type')
const mm = require('music-metadata')
export default {
  data () {
    return {
      dir: '/Users/gavinbenda/Deezloader Music/Client Liaison - Client Liaison/',
      files: [],
      file: '',
      progress: 'Idle',
      isBusy: true,
      fields: [
        { key: 'title', sortable: true },
        { key: 'artist', sortable: true },
        'bitrate'
      ],
      selected: []
    }
  },
  created () {
    this.readDirectory()
  },
  methods: {
    /**
      * Reads the selected directory and displays all compatable files
      * At this stage it's simply MP3's that contain metadata
      * TODO: this can support direct WAV and FLAC input quite easily...
      * TODO: there should be more promises used here
      */
    readDirectory: function () {
      this.isBusy = true
      this.files = []
      // read the target directory
      fs.readdir(this.dir, (err, dir) => {
        // loop through results
        for (let filePath of dir) {
          let buffer = readChunk.sync(this.dir + filePath, 0, fileType.minimumBytes)
          let fileTypeInfo = fileType(buffer)
          // only interestedin MP3 files at the moment, ignore all others
          if (fileTypeInfo != null) {
            if (fileTypeInfo.ext === 'mp3') {
              // read metadata
              mm.parseFile(this.dir + filePath, {native: true})
                .then(metadata => {
                  // write the relevent data to the files array
                  this.files.push({
                    fileName: filePath,
                    artist: metadata.common.artist,
                    title: metadata.common.title,
                    format: fileTypeInfo.ext,
                    bitrate: metadata.format.bitrate / 1000 + 'kbps'
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
      this.isBusy = false
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
        var filepath = this.dir + this.selected[i].fileName
        console.log(filepath)
        var sourceFile = filepath
        var destFile = filepath.replace('.mp3', '-raw.wav')
        var atracFile = filepath.replace('.mp3', '.at3')
        var finalFile = this.selected[i].title + ' - ' + this.selected[i].artist // filepath.replace('.mp3', '.wav')
        let self = this
        await self.convertToWav(sourceFile, destFile)
          .then(await function () {
            return self.convertToAtrac(destFile, atracFile)
          })
          .then(await function () {
            return self.convertToWavWrapper(atracFile, finalFile)
          })
          .then(await function () {
            return self.sendToPlayer(finalFile)
          })
      }
    },
    /**
      * Convert input MP3 to WAV file using ffmpeg
      * This MUST be 44100 and 16bit for the atrac encoder to work
      */
    convertToWav: function (source, dest) {
      this.progress = 'Converting to Wav'
      return new Promise((resolve, reject) => {
        // spawn this task and resolve promise on close
        let ffmpeg = require('child_process').spawn('ffmpeg', ['-y', '-i', source, '-acodec', 'pcm_u8', '-ar', '44100', dest])
        ffmpeg.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          resolve()
        })
        ffmpeg.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
      })
    },
    /**
      * Pass WAV file to atracdenc
      * TODO: this is the longest part of the process, some user progress % feedback would be nice...
      */
    convertToAtrac: function (source, dest) {
      this.progress = 'Converting to Atrac'
      return new Promise((resolve, reject) => {
        // spawn this task and resolve promise on close
        let atracdenc = require('child_process').spawn('/Users/gavinbenda/webdev/atracdenc/src/build/atracdenc', ['-e', 'atrac3', '-i', source, '-o', dest, '--bitrate', '128'])
        console.log(atracdenc)
        atracdenc.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          resolve()
        })
        atracdenc.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
        // we get a fair bit of useful progress data returned here for debugging
        atracdenc.stdout.on('data', function (data) {
          console.log('stdout: ' + data)
        })
      })
    },
    /**
      * Apply the WAV wrapper around the converted file
      * This is required to be able to send using netmdcli
      */
    convertToWavWrapper: function (source, dest) {
      this.progress = 'Adding Wav Wrapper'
      return new Promise((resolve, reject) => {
        let ffmpeg2 = require('child_process').spawn('ffmpeg', ['-y', '-i', source, '-c', 'copy', dest])
        // console.log(ffmpeg2)
        ffmpeg2.on('close', (code) => {
          console.log(`child process exited with code ${code}`)
          resolve()
        })
        ffmpeg2.on('error', (error) => {
          console.log(`child process creating error with error ${error}`)
          reject(error)
        })
      })
    },
    /**
      * Send final file using netmdcli
      * The filename is named {title} - {artist}
      */
    sendToPlayer: function (file) {
      this.progress = 'Sending to Player'
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn('/Users/gavinbenda/webdev/linux-minidisc/netmdcli/netmdcli', ['send', file])
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
