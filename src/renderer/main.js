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

/* eslint-disable no-new */
new Vue({
  components: { App },
  router,
  store,
  template: '<App/>'
}).$mount('#app')
