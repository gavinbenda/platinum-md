'use strict'

import path from 'path'
import getPlatform from './get-platform'

const IS_PROD = process.env.NODE_ENV === 'production'
const root = process.cwd()

export const platform = getPlatform()

const binariesPath =
  IS_PROD
    ? path.join(path.dirname(__dirname), '..', './Resources', './bin')
    : path.join(root, './resources', platform, './bin')

export const atracdencPath = path.resolve(path.join(binariesPath, './atracdenc'))
export const ffmpegPath = path.resolve(path.join(binariesPath, './ffmpeg'))
export const netmdcliPath = path.resolve(path.join(binariesPath, './netmdcli'))
export const himdcliPath = path.resolve(path.join(binariesPath, './himdcli'))
