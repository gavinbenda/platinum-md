<template>
  <div class="p-3">
  
    <b-button pill variant="primary" @click="runAction('play')"><font-awesome-icon icon="play"></font-awesome-icon></b-button>
    <b-button pill variant="dark" @click="runAction('pause')"><font-awesome-icon icon="pause"></font-awesome-icon></b-button>
    <b-button pill variant="dark" @click="runAction('stop')"><font-awesome-icon icon="stop"></font-awesome-icon></b-button>
    <b-button pill variant="dark" @click="runAction('previous')"><font-awesome-icon icon="backward"></font-awesome-icon></b-button>
    <b-button pill variant="dark" @click="runAction('next')"><font-awesome-icon icon="forward"></font-awesome-icon></b-button>
 
  </div>
</template>

<script>
import bus from '@/bus'
export default {
  methods: {
    /**
      * Run an action on a track (play/pause/stop/skip)
      */
    runAction: function (action, trackNo = 0) {
      bus.$emit('track-action', { action: action, trackNo: trackNo })
    }
  }
}
</script>
next - starts next track
previous - starts previous track
restart - restarts current track
pause - pause the unit
stop - stop the unit