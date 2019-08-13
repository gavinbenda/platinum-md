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
    readDirectory () {
      this.isBusy = true
      this.files = []
      fs.readdir(this.dir, (err, dir) => {
        console.log(dir)
        for (let filePath of dir) {
          console.log(filePath)
          let buffer = readChunk.sync(this.dir + filePath, 0, fileType.minimumBytes)
          let fileTypeInfo = fileType(buffer)
          // only interestedin MP3 files at the moment
          console.log(fileTypeInfo)
          if (fileTypeInfo != null) {
            if (fileTypeInfo.ext === 'mp3') {
              console.log(fileTypeInfo.mime)
              // read metadata
              mm.parseFile(this.dir + filePath, {native: true})
                .then(metadata => {
                  console.log(metadata)
                  // write the relevent data
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
    rowSelected (items) {
      this.selected = items
    },
    upload () {
      for (var i = 0, len = this.selected.length; i < len; i++) {
        var filepath = this.dir + this.selected[i].fileName
        console.log(filepath)
        var sourceFile = filepath
        var destFile = filepath.replace('.mp3', '.wav')
        var atracFile = filepath.replace('.mp3', '.at3')
        var finalFile = filepath.replace('.mp3', '-final.wav')
        let self = this
        self.convertToWav(sourceFile, destFile)
          .then(function () {
            return self.convertToAtrac(destFile, atracFile)
          })
          .then(function () {
            return self.convertToWavWrapper(atracFile, finalFile)
          })
          .then(function () {
            return self.sendToPlayer(finalFile)
          })
        // this should only proceed once all files have been created
      }
    },
    convertToWav (source, dest) {
      console.log('stage 1')
      this.progress = 'Converting to Wav'
      return new Promise((resolve, reject) => {
        // let ffmpeg = require('child_process').execSync('ffmpeg -y -i "' + source + '" -acodec pcm_u8 -ar 44100 "' + dest + '"')
        let ffmpeg = require('child_process').spawn('ffmpeg', ['-y', '-i', source, '-acodec', 'pcm_u8', '-ar', '44100', dest])
        // console.log(ffmpeg)
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
    convertToAtrac (source, dest) {
      console.log('stage 2')
      this.progress = 'Converting to Atrac'
      let self = this
      return new Promise((resolve, reject) => {
        // let atracdenc = require('child_process').execSync('/Users/gavinbenda/webdev/atracdenc/src/build/atracdenc -e atrac3 -i"' + source + '" -o "' + dest + '" --bitrate 128')
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
        atracdenc.stdout.on('data', function (data) {
          console.log('stdout: ' + data)
          self.progress = data
        })
      })
    },
    convertToWavWrapper (source, dest) {
      console.log('stage 3')
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
    sendToPlayer (file) {
      console.log('stage 4')
      this.progress = 'Sending to Player'
      return new Promise((resolve, reject) => {
        let netmdcli = require('child_process').spawn('/Users/gavinbenda/webdev/linux-minidisc/netmdcli/netmdcli', ['send', file])
        // console.log(netmdcli)
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
