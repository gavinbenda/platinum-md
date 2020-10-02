'use strict'

import path from 'path'
import { remote } from 'electron'
import getPlatform from './get-platform'

const IS_PROD = process.env.NODE_ENV === 'production'
const root = process.cwd()
const { getAppPath } = remote.app

export const platform = getPlatform()

const binariesPath =
  IS_PROD
    ? path.join(path.dirname(getAppPath()), '..', './Resources', './bin')
    : path.join(root, './resources', platform, './bin')

export const atracdencPath = path.resolve(path.join(binariesPath, './atracdenc'))
export const ffmpegPath = path.resolve(path.join(binariesPath, './ffmpeg'))
export const netmdcliPath = path.resolve(path.join(binariesPath, './netmdcli'))

export const uploadPyPath =
  IS_PROD
    ? path.join(path.dirname(getAppPath()), '..', './Resources', './netmd-py')
    : path.join(root, './resources', './netmd-py')
