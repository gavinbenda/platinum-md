<template>
  <div>

    <button @click="readDirectory">Scan Files</button>
    
    <div v-for="file in files" :key="file.id">
      {{file}}
      <button @click="upload(file)">Upload</button>
    </div>
    
  </div>
</template>

<script>
const fs = require('fs-extra')
export default {
  data () {
    return {
      dir: '/Users/gavinbenda/Deezloader Music/',
      files: [],
      file: ''
    }
  },
  methods: {
    readDirectory () {
      fs.readdir(this.dir, (err, dir) => {
        console.log(dir)
        for (let filePath of dir) { console.log(filePath) }
        this.files = dir
        if (err) { console.log(err) }
      })
    },
    upload (file) {
      let filepath = this.dir + file
      let sourceFile = filepath
      let destFile = filepath.replace('.mp3', '.wav')
      console.log(filepath)
      let ffmpeg = require('child_process').spawn('ffmpeg', ['-i', `${sourceFile}`, '-acodec', 'pcm_u8', '-ar', '44100', `${destFile}`])
      ffmpeg.on('exit', (statusCode) => {
        if (statusCode === 0) {
          console.log('conversion successful')
        }
      })
      ffmpeg
        .stderr
        .on('data', (err) => {
          console.log('err:', String(err))
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
