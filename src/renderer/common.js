const fs = require('fs-extra')
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path.replace('app.asar', 'app.asar.unpacked')
const ffmpeg = require('fluent-ffmpeg')
ffmpeg.setFfmpegPath(ffmpegPath)

/**
  * Convert audio file to WAV file using ffmpeg
  * This MUST be 44100 and 16bit for the atrac encoder to work
  */
export async function convertToWav (source, dest, format) {
  return new Promise(async (resolve, reject) => {
    // Start conversion
    var codec = ['-acodec', 'pcm_s16le']
    console.log('Starting WAV conversion process using ffmpeg: ' + source + ' --> ' + dest)
    switch (format) {
      case ('FLAC'):
        codec = ['-acodec', 'flac']
        break
      case ('MP3'):
        codec = ['-acodec', 'mp3', '-b:a', '320k']
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
