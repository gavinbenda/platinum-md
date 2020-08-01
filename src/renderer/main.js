import Vue from 'vue'
import axios from 'axios'

import App from './App'
import router from './router'
import store from './store'

import BootstrapVue from 'bootstrap-vue'

import './scss/styles.scss'

import { library } from '@fortawesome/fontawesome-svg-core'
import { faAngleDoubleRight, faSyncAlt, faLock, faLockOpen, faEdit, faTimes, faFolderOpen, faCog, faRandom, faHeadphones, faPlay, faPause, faStop, faForward, faBackward } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

library.add(faAngleDoubleRight, faSyncAlt, faLock, faLockOpen, faEdit, faTimes, faFolderOpen, faCog, faRandom, faHeadphones, faPlay, faPause, faStop, faForward, faBackward)

Vue.component('font-awesome-icon', FontAwesomeIcon)

/* eslint-disable no-unused-vars */
Vue.use(BootstrapVue)

if (!process.env.IS_WEB) Vue.use(require('vue-electron'))
Vue.http = Vue.prototype.$http = axios
Vue.config.productionTip = false

// register global filter
Vue.filter('timeFormat', function (duration) {
  // Hours, minutes and seconds
  var hrs = ~~(duration / 3600)
  var mins = ~~((duration % 3600) / 60)
  var secs = ~~duration % 60
  // Output like "1:01" or "4:03:59" or "123:03:59"
  var ret = ''
  if (hrs > 0) {
    ret += '' + hrs + ':' + (mins < 10 ? '0' : '')
  }
  ret += '' + mins + ':' + (secs < 10 ? '0' : '')
  ret += '' + secs
  return ret
})

/* eslint-disable no-new */
new Vue({
  components: { App },
  router,
  store,
  template: '<App/>'
}).$mount('#app')
