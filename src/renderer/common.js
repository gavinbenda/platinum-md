import bus from '@/bus'
const fs = require('fs-extra')
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path.replace('app.asar', 'app.asar.unpacked')
const ffmpeg = require('fluent-ffmpeg')
ffmpeg.setFfmpegPath(ffmpegPath)

/**
  * Convert audio file to WAV file using ffmpeg
  * This MUST be 44100 and 16bit for the atrac encoder to work
  */
export async function convertAudio (source, dest, format, title = null) {
  return new Promise(async (resolve, reject) => {
    // Start conversion
    var codec = ['-acodec', 'pcm_s16le']
    console.log('Starting WAV conversion process using ffmpeg: ' + source + ' --> ' + dest)
    switch (format) {
      case ('FLAC'):
        codec = ['-acodec', 'flac']
        break
      case ('MP3'):
        if (title !== null) {
          codec = ['-metadata', 'title=' + title, '-acodec', 'mp3', '-b:a', '256k', '-ar', '44100']
        } else {
          codec = ['-acodec', 'mp3', '-b:a', '256k', '-ar', '44100']
        }
        break
    }
    ffmpeg(source)
      .output(dest)
      .outputOption(codec)
      .audioFrequency(44100)
      .on('start', function (commandLine) {
        console.log('Spawned Ffmpeg with command: ', commandLine)
      })
      .on('progress', function (progress) {
        console.log('Processing: ' + progress.timemark + ' done ' + progress.targetSize + ' kilobytes')
        bus.$emit('netmd-status', { progress: 'Converting Track', progressPercent: Math.round(progress.percent) + '%' })
      })
      // If successful, resolve
      .on('end', function () {
        console.log('ffmpeg completed successfully')
        bus.$emit('netmd-status', { progress: 'Idle', progressPercent: 0 })
        resolve()
      })
      // Reject if we get any errors
      .on('error', function (err) {
        console.log('ffmpeg error: ' + err.message)
        reject(err.message)
      })
      .run()
  })
}

/**
  * Strip ID3v2 tag from mp3 file
  */
export async function stripID3 (source, dest) {
  return new Promise(async (resolve, reject) => {
    // Start conversion
    var codec = ['-acodec', 'pcm_s16le']
    console.log('Starting ID3 strip using ffmpeg: ' + source + ' --> ' + dest)
    codec = ['-codec:a', 'copy', '-map', 'a']
    ffmpeg(source)
      .output(dest)
      .outputOption(codec)
      .on('start', function (commandLine) {
        console.log('Spawned Ffmpeg with command: ', commandLine)
      })
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
}

/**
  * Make sure temp directory actually exists, if not create it
  */
export function ensureDirSync (dirpath) {
  try {
    fs.mkdirSync(dirpath, { recursive: true })
  } catch (err) {
    if (err.code !== 'EEXIST') throw err
  }
}

/**
  *Sanitize titles for half-width slot
  */
export function sanitizeName (name) {
  return name.normalize('NFD').replace(/[^\x20-\x7F]/g, '')
}
