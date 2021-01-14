<template>
  <b-button-toolbar aria-label="Toolbar for playing tracks">
    <b-button-group class="mx-1">
      <b-button variant="success" @click="runAction('play')"><font-awesome-icon icon="play"></font-awesome-icon></b-button>
      <b-button variant="dark" @click="runAction('pause')"><font-awesome-icon icon="pause"></font-awesome-icon></b-button>
      <b-button variant="dark" @click="runAction('stop')"><font-awesome-icon icon="stop"></font-awesome-icon></b-button>
      <b-button variant="dark" @click="runAction('previous')"><font-awesome-icon icon="backward"></font-awesome-icon></b-button>
      <b-button variant="dark" @click="runAction('next')"><font-awesome-icon icon="forward"></font-awesome-icon></b-button>
    </b-button-group>
  </b-button-toolbar>
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