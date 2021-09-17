<template>
  <b-container>
    <div id="waveform">
      <!-- Here be waveform -->
    </div>
    <div id="wave-timeline"></div>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  import WaveSurfer from 'wavesurfer.js';
  import Timeline from 'wavesurfer.js/dist/plugin/wavesurfer.timeline.js';

  export default {
    name: "Waveform",
    data() {
      return {
        wavesurfer: Object,
        wavesurfer_ready: false,
        old_position: 0
      }
    },
    computed: {
      ...mapState(['player']),
    },
    mounted() {
      this.getWorkflowId();
      this.getTimeUpdate()
    },
    beforeDestroy: function () {
    },
    methods: {
      async getAssetAudio(bucket, s3Key) {
        const body = { "S3Bucket": bucket, "S3Key": s3Key };

        let apiName = 'mieDataplaneApi'
        let path = 'download'
        let requestOpts = {
          body: body,
          response: true,
          responseType: 'text'
        };
        try {
          let response = await this.$Amplify.API.post(apiName, path, requestOpts);
          await response.text().then(url => {
            this.renderWaveform(url)
          });   
        } catch (error) {
          this.showDataplaneAlert = true
          console.log(error)
        }
      },
      async getWorkflowId() {
        let asset_id = this.$route.params.asset_id
        let path = 'workflow/execution/asset/' + asset_id
        let apiName = 'mieWorkflowApi'
        let requestOpts = {
          headers: {'Content-Type': 'application/json'},
          response: true
        };
        console.log(path)
        try {
          let response = await this.$Amplify.API.get(apiName, path, requestOpts);
          console.log("Waveform: getWorkflowId")
          console.log(response)
          const workflow_id = response.data[0].Id
          let path = 'workflow/execution/asset/' + workflow_id

          let res = await this.$Amplify.API.get(apiName, path, requestOpts);
          const bucket = res.data.Globals.Media.Audio.S3Bucket;
          const s3Key = res.data.Globals.Media.Audio.S3Key;
          this.getAssetAudio(bucket, s3Key);
        } catch (error) {
          console.log(error)
        }
      },
      renderWaveform(url) {
        const vm = this;
        let wavesurfer = WaveSurfer.create({
          container: '#waveform',
          removeMediaElementOnDestroy: true,
          closeAudioContext: true,
          cursorColor: "red",
          progressColor: "#999",
          responsive: true,
          height: 64,
          barHeight: 2,
          plugins: [
            Timeline.create({
              container: '#wave-timeline'
            }),
          ]
        });
        wavesurfer.cancelAjax()
        wavesurfer.load(url);
        vm.wavesurfer = wavesurfer
        wavesurfer.on('ready', function () {
          vm.wavesurfer_ready = true;
        });
        wavesurfer.on('seek', function (new_position) {
          // In order to distinguish between interactive user clicks and
          // seeks from the getTimeUpdate() function, we need to do this:
          // Don't seek if new position within 3 seconds from the old position.
          // Hopefully all user clicks will be 3 seconds away from the old position.
          if (Math.abs(new_position*wavesurfer.getDuration() - vm.old_position*wavesurfer.getDuration()) < 3) {
            vm.old_position = new_position;
            return;
          }
          // Seek the video player to the new position
          vm.player.currentTime(new_position*wavesurfer.getDuration())
          vm.old_position = new_position
          // Send a signal to the Transcript component so it can
          // seek the caption table to the new position.
          vm.$store.commit('updateWaveformSeekPosition', new_position*wavesurfer.getDuration());
        });
      },
      getTimeUpdate() {
        const vm = this;
        // Send current time position for the video player to verticalLineCanvas
        var last_position = 0;
        if (this.player) {
          this.player.on('timeupdate', function () {
            const current_position = Math.round(this.player.currentTime() / this.player.duration() * 1000);
            if (current_position !== last_position) {
              if (vm.wavesurfer_ready) {
                vm.wavesurfer.seekTo(current_position/1000);
              }
              last_position = current_position;
            }
          }.bind(this));
        }
      },
    }
  }
</script>

<style scoped>
</style>
