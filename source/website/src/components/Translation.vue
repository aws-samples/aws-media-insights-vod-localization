<template>
  <div>
    <div v-if="noTranslation === true">
      No translation found for this asset
    </div>
    <b-alert
      v-model="showTerminologyNotification"
      :variant="terminologyNotificationStatus"
      dismissible
      fade
    >
      {{ terminologyNotificationMessage }}
    </b-alert>
    <!-- show spinner while busy loading -->
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <!-- show table if not busy loading and translation data exists -->
    <div
      v-else-if="noTranslation === false"
      class="wrapper"
    >
      <!-- show radio buttons for each available translation language -->
      <b-form-group>
        <b-form-radio-group
          v-model="selected_lang_code"
          :options="translationsCollection"
          @change="getWebCaptions"
        ></b-form-radio-group>
      </b-form-group>
      <!-- show translation text when language has been selected -->
      <div v-if="selected_lang_code !== ''" id="event-line-editor" class="event-line-editor">
        <b-table
          ref="selectableTable"
          selectable
          select-mode="single"
          thead-class="hidden_header"
          fixed responsive="sm"
          :items="webCaptions"
          :fields="webCaptions_fields"
        >
          <!-- adjust column width for captions -->
          <template v-slot:table-colgroup="scope">
            <col
              v-for="field in scope.fields"
              :key="field.key"
              :style="{ width: field.key === 'caption' ? '80%' : '20%' }"
            >
          </template>
          <!-- reformat timestamp to hh:mm:ss and -->
          <!-- disable timestamp edits if workflow status is not Complete -->
          <template v-slot:cell(timeslot)="data">
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height start-time-field " :value="toHHMMSS(data.item.start)" @change="new_time => changeStartTime(new_time, data.index)" />
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height stop-time-field " :value="toHHMMSS(data.item.end)" @change="new_time => changeEndTime(new_time, data.index)" />
          </template>
          <template v-slot:cell(caption)="data">
            <b-container class="p-0">
              <b-row no-gutters>
                <b-col cols="10">
                  <!-- The state on this text area will show a red alert icon if the user forgets to enter any text. Otherwise we set the state to null so no validity indicator is shown. -->
                  <b-form-textarea
                    :id="'caption' + data.index"
                    :ref="'caption' + data.index"
                    class="custom-text-field .form-control-sm"
                    rows="2"
                    placeholder="Type translation here"
                    :value="data.item.caption"
                    :dir="text_direction"
                    :disabled="workflow_status !== 'Complete'"
                    :state="(data.item.caption.length > 0) ? null : false"
                    @change="new_caption => changeCaption(new_caption, data.index)"
                    @click="captionClickHandler(data.index)"
                  />
                </b-col>
                <b-col>
                  <span style="position:absolute; top: 0px">
                    <b-button v-if="workflow_status === 'Complete'" size="sm" variant="link" @click="delete_row(data.index)">
                      <b-icon icon="x-circle" color="lightgrey"></b-icon>
                    </b-button>
                  </span>
                  <span style="position:absolute; bottom: 0px">
                    <b-button v-if="workflow_status === 'Complete'" size="sm" variant="link" @click="add_row(data.index)">
                      <b-icon icon="plus-square" color="lightgrey"></b-icon>
                    </b-button>
                  </span>
                </b-col>
              </b-row>
            </b-container>
          </template>
        </b-table>
      </div>
      <br>
      <!-- this is the download button -->
      <b-dropdown id="download-dropdown" text="Download VTT/SRT" class="mb-2" size="sm" dropup no-caret>
        <template slot="button-content">
          <b-icon icon="download" color="white"></b-icon> Download
        </template>
        <b-dropdown-item :href="vtt_url">
          Download VTT
        </b-dropdown-item>
        <b-dropdown-item :href="srt_url">
          Download SRT
        </b-dropdown-item>
        <b-dropdown-item v-if="pollyaudio_url" :href="pollyaudio_url" target="_blank" download>
          Download Audio
        </b-dropdown-item>
        <b-dropdown-item v-else disabled>
          Download Audio (language not supported)
        </b-dropdown-item>
      </b-dropdown>&nbsp;
      <!-- this is the save vocabulary button -->
      <b-button id="saveTerminology" v-b-tooltip.hover title="Save terminology will open a window where you can create or modify custom terminologies for AWS Translate" size="sm" class="mb-2" @click="showTerminologyConfirmation()">
        <b-icon icon="card-text" color="white"></b-icon>
        Save terminology
      </b-button>&nbsp;
      <!-- this is the save edits button for when workflow complete -->
      <b-button v-if="workflow_status === 'Complete' || workflow_status === 'Error'" id="editCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow running -->
      <b-button v-else id="editCaptionsDisabled" size="sm" disabled class="mb-2">
        <b-icon icon="arrow-clockwise" animation="spin" color="white"></b-icon>
        Saving edits
      </b-button>
      <br>
      <b-modal ref="delete-terminology-modal" ok-title="Confirm" ok-variant="danger" title="Delete Terminology?" @ok="deleteTerminologyRequest(customTerminologySelected=customTerminologySelected)">
        <p>Are you sure you want to permanently delete the custom terminology <b>{{ customTerminologySelected }}</b>?</p>
      </b-modal>
      <b-modal
          ref="terminology-modal"
          size="lg"
          title="Custom Terminology Editor"
          :ok-disabled="validTerminologyName === false || (customTerminologyCreateNew === '') || customTerminologyUnion.length === 0 || validCSV === false" ok-title="Save" @ok="saveTerminology()"
          @cancel="customTerminologySelected=[]; customTerminologySaved=[];">
        <div v-if="customTerminologyList.length > 0">
          Load an existing terminology:
        </div>
        <b-form-group v-if="customTerminologyList.length > 0">
          <b-form-checkbox-group
            id="custom-terminology-selection"
            v-model="customTerminologySelected"
            name="custom-terminology-list"
            :options="customTerminologyList"
            text-field="name_and_status"
            value-field="name"
            disabled-field="notEnabled"
            stacked
          >
          </b-form-checkbox-group>
        </b-form-group>
        <div v-if="customTerminologySelected.length > 0">
          <div v-if="customTerminologySelected.length === 1">
            Delete terminology? <b>{{ customTerminologySelected }}</b>&nbsp;
            <b-button v-b-tooltip.hover.right size="sm" title="Delete selected terminology" variant="danger" @click="deleteTerminology">
              Delete
            </b-button>
          </div>
          <div v-if="customTerminologySelected.length > 1">
            Delete terminologies? <b>{{ customTerminologySelected }}</b>&nbsp;
            <b-button v-b-tooltip.hover.right size="sm" title="Delete selected terminologies" variant="danger" @click="deleteTerminology">
              Delete
            </b-button>
          </div>
        </div>

        <!-- Only show the option to save a new terminology if the user has
        made edits to translated words or they have selected a previously
        saved custom terminology. -->
        <div v-if="customTerminologyUnsaved.length !== 0 || customTerminologySaved.length !== 0">
          New terminology name:
          <!-- The state on this text area will show a red alert icon if
          the user enters an invalid custom terminology name. Otherwise we
          set the state to null so no validity indicator is shown. -->
          <b-form-input v-model="customTerminologyCreateNew" size="sm" :state="validTerminologyName ? null : false"></b-form-input>
        </div>
        <div v-if="customTerminologyUnsaved.length !== 0">
          New terminology content (click to edit):
          <div v-if="customTerminologySelected.length > 0" class="text-info" style="font-size: 80%">
            Rows shown in blue were loaded from <b>{{ customTerminologySelected }}.</b>
          </div>
        </div>
        <b-table
          :items="customTerminologyUnion"
          :fields="customTerminologyFields"
          selectable
          select-mode="single"
          fixed responsive="sm"
          bordered
          small
          show-empty
        >
          <template #empty="scope">
            No data
          </template>
          <!-- Here we define the cell contents for the terminology table: -->
          <template v-slot:cell()="{ item, index, field: { key } }">
            <!-- The v-if/else here is used to show the add / delete row buttons
            only in the right-most column. -->
            <div v-if="key === customTerminologyLastTableField">
              <!-- In this div we're controlling the right most column. -->
              <b-row no-gutters>
                <b-col cols="9">
                  <div v-if="index < customTerminologyUnsaved.length">
                    <!-- We use null in state to avoid showing a green check mark when field is valid -->
                    <b-form-input v-model="item[key]" class="custom-text-field" placeholder="(required)" :state="item[key] !== '' && item[key] !== undefined ? null : false" />
                  </div>
                  <div v-else>
                    <b-form-input v-model="item[key]" class="custom-text-field text-info" />
                  </div>
                </b-col>
                <b-col nopadding cols="1">
                  <span style="position:absolute; top: 0px">
                    <b-button v-b-tooltip.hover.right size="sm" style="display: flex;" variant="link" title="Remove row" @click="delete_terminology_row(index)">
                      <b-icon font-scale=".9" icon="x-circle" color="lightgrey"></b-icon>
                    </b-button>
                  </span>
                  <span style="position:absolute; bottom: 0px">
                    <b-button v-b-tooltip.hover.right size="sm" style="display: flex;" variant="link" title="Add row" @click="add_terminology_row(index)">
                      <b-icon font-scale=".9" icon="plus-square" color="lightgrey"></b-icon>
                    </b-button>
                  </span>
                </b-col>
              </b-row>
            </div>
            <div v-else>
              <!-- In this div we're controlling every column except the right most column. -->
              <div v-if="index < customTerminologyUnsaved.length">
                <!-- We use null in state to avoid showing a green check mark when field is valid -->
                <b-form-input v-model="item[key]" class="custom-text-field" placeholder="(required)" :state="item[key] !== '' && item[key] !== undefined ? null : false" />
              </div>
              <div v-else>
                <b-form-input v-model="item[key]" class="custom-text-field text-info" placeholder="(required)" :state="item[key] !== '' && item[key] !== undefined ? null : false" />
              </div>
            </div>
          </template>
          <!-- Here we show buttons to add / remove languages from custom terminology: -->
          <template v-slot:table-caption>
            <span style="position:absolute; right: 10px">
<!--
Uncomment the following buttons to get options for adding or removing languages to the terminology table:
-->
              <b-button v-if="customTerminologySelected !== ''" v-b-tooltip.hover.top title="Add a new language" variant="outline-secondary" class="btn-xs" @click="add_language()">Add Language</b-button>&nbsp;
              <b-button v-if="customTerminologySelected !== ''" v-b-tooltip.hover.top title="Remove a language" variant="outline-secondary" class="btn-xs" @click="remove_language()">Remove Language</b-button>
            </span>
          </template>
        </b-table>
        <div v-if="validTerminologyName === false" style="color:red">
          Invalid terminology name. Valid characters are a-z, A-Z, and 0-9. Max length is 200.
        </div>
        <div v-else-if="(customTerminologyUnsaved.length !== 0 || customTerminologySaved.length !== 0)  && customTerminologyCreateNew === ''" style="color:red">
          Specify a terminology name to save as.<br>
        </div>
        <div v-else-if="validCSV === false" style="color:red">
          Custom terminology must not contain any empty fields.<br>
        </div>
      </b-modal>
      <b-modal ref="save-modal" title="Save Confirmation" ok-title="Confirm" @ok="saveCaptions()">
        <p>Saving will overwrite the existing {{ selected_lang }} translation. Are you sure?</p>
      </b-modal>
      <b-modal ref="add-language-modal" title="Add Language" ok-title="Save" :ok-disabled="newLanguageCode === ''" @ok="add_language_request()">
        <p>Select language to add:</p>
        <b-form-select
            v-model="newLanguageCode"
            placeholder="language code"
            :options="translateLanguages"
            size="sm"
        />
      </b-modal>
      <b-modal ref="remove-language-modal" title="Remove Language" ok-title="Remove" :ok-disabled="removeLanguageCode === ''" @ok="remove_language_request()">
        <p>Select language to remove:</p>
        <b-form-group>
          <b-form-radio-group
            v-model="removeLanguageCode"
            :options="alphabetized_language_collection.map(x => x.value)"
          ></b-form-radio-group>
        </b-form-group>
      </b-modal>
      <div v-if="webCaptions.length > 0 && workflow_status !== 'Complete' && workflow_status !== 'Error' && workflow_status !== 'Waiting'" style="color:red">
        Editing is disabled until workflow completes.
      </div>
    </div>
  </div>
</template>

<script>
import {mapState} from "vuex";

export default {
  name: "Translation",
  data() {
    return {
      text: "",
      vttcaptions: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      srtcaptions: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      pollyaudiotranscripts: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      isBusy: false,
      operator: "translation",
      noTranslation: false,
      translationsCollection: [],
      addedLanguages: [],
      removedLanguages: [],
      selected_lang: "",
      selected_lang_code: "",
      translatedText: "",
      translateLanguages: [
        {text: 'Afrikaans', value: 'af'},
        {text: 'Albanian', value: 'sq'},
        {text: 'Amharic', value: 'am'},
        {text: 'Arabic', value: 'ar'},
        {text: 'Azerbaijani', value: 'az'},
        {text: 'Bengali', value: 'bn'},
        {text: 'Bosnian', value: 'bs'},
        {text: 'Bulgarian', value: 'bg'},
        {text: 'Chinese (Simplified)', value: 'zh'},
        // AWS Translate does not support translating from zh to zh-TW
        // {text: 'Chinese (Traditional)', value: 'zh-TW'},
        {text: 'Croatian', value: 'hr'},
        {text: 'Czech', value: 'cs'},
        {text: 'Danish', value: 'da'},
        {text: 'Dari', value: 'fa-AF'},
        {text: 'Dutch', value: 'nl'},
        {text: 'English', value: 'en'},
        {text: 'Estonian', value: 'et'},
        {text: 'Finnish', value: 'fi'},
        {text: 'French', value: 'fr'},
        {text: 'French (Canadian)', value: 'fr-CA'},
        {text: 'Georgian', value: 'ka'},
        {text: 'German', value: 'de'},
        {text: 'Greek', value: 'el'},
        {text: 'Hausa', value: 'ha'},
        {text: 'Hebrew', value: 'he'},
        {text: 'Hindi', value: 'hi'},
        {text: 'Hungarian', value: 'hu'},
        {text: 'Indonesian', value: 'id'},
        {text: 'Italian', value: 'it'},
        {text: 'Japanese', value: 'ja'},
        {text: 'Korean', value: 'ko'},
        {text: 'Latvian', value: 'lv'},
        {text: 'Malay', value: 'ms'},
        {text: 'Norwegian', value: 'no'},
        {text: 'Persian', value: 'fa'},
        {text: 'Pashto', value: 'ps'},
        {text: 'Polish', value: 'pl'},
        {text: 'Portuguese', value: 'pt'},
        {text: 'Romanian', value: 'ro'},
        {text: 'Russian', value: 'ru'},
        {text: 'Serbian', value: 'sr'},
        {text: 'Slovak', value: 'sk'},
        {text: 'Slovenian', value: 'sl'},
        {text: 'Somali', value: 'so'},
        {text: 'Spanish', value: 'es'},
        {text: 'Swahili', value: 'sw'},
        {text: 'Swedish', value: 'sv'},
        {text: 'Tagalog', value: 'tl'},
        {text: 'Tamil', value: 'ta'},
        {text: 'Thai', value: 'th'},
        {text: 'Turkish', value: 'tr'},
        {text: 'Ukrainian', value: 'uk'},
        {text: 'Urdu', value: 'ur'},
        {text: 'Vietnamese', value: 'vi'},
      ],
      asset_id: this.$route.params.asset_id,
      workflow_id: "",
      workflow_status: "",
      waiting_stage: "",
      sourceLanguageCode: "",
      workflow_config: {},
      workflow_definition: {},
      results: [],
      newLanguageCode: "",
      removeLanguageCode: "",
      customTerminologyCSV: "",
      customTerminologyUnsaved: [],
      customTerminologySaved: [],
      customTerminologyList: [],
      customTerminologySelected: [],
      customTerminologyCreateNew: "",
      showTerminologyNotification: 0,
      terminologyNotificationStatus: "success",
      terminologyNotificationMessage: "",
      webCaptions: [],
      webCaptions_vtt: '',
      webCaptions_fields: [
        {key: 'timeslot', label: 'timeslot', tdClass: this.tdClassFunc},
        {key: 'caption', label: 'caption'}
      ],
      uploaded_captions_file: '',
      id: 0,
      transcript: "",
      isSaving: false,
      noTranscript: false
    }
  },
  computed: {
    customTerminologyFields: function () {
      return [this.sourceLanguageCode].concat(this.alphabetized_language_collection.map(x => x.value).filter(y => this.removedLanguages.includes(y) === false))
    },
    customTerminologyLastTableField: function() {
      // if there's no custom terminology selected, then the terminology table only include 2 columns, the source language and the language selected in the web captions table, so we can just return selected_lang_code as the name of the last column.
      if (this.alphabetized_language_collection.length > 0) {
        return this.alphabetized_language_collection[this.alphabetized_language_collection.length-1].value
      } else {
        return ''
      }
    },
    customTerminologyUnion: function() {
      return this.customTerminologyUnsaved.concat(this.customTerminologySaved)
    },
    validCSV: function() {
      for (let key in this.customTerminologyUnion) {
        for (let term in this.customTerminologyUnion[key]) {
          if (this.customTerminologyUnion[key][term] === null || this.customTerminologyUnion[key][term] === "")
            return false;
        }
      }
      return true;
    },
    validTerminologyName: function() {
      const letterNumber = /^([A-Za-z0-9-]_?)+$/;
      // The name can be up to 256 characters long. Valid characters are a-z, A-Z, 0-9, -, and _.
      if (this.customTerminologyCreateNew === "" || (this.customTerminologyCreateNew.match(letterNumber) && this.customTerminologyCreateNew.length<256)) {
        return true;
      }
      else
      {
        return false;
      }
    },
    customTerminologyName: function () {
      if (this.customTerminologyCreateNew !== "")
        return this.customTerminologyCreateNew
    },
    inputListeners: function () {
      var vm = this
      // `Object.assign` merges objects together to form a new object
      return Object.assign({},
        // We add all the listeners from the parent
        this.$listeners,
        // Then we can add custom listeners or override the
        // behavior of some listeners.
        {
          // This ensures that the component works with v-model
          input: function (event) {
            vm.$emit('input', event.target.value)
          }
        }
      )
    },
    ...mapState(['player', 'waveform_seek_position']),
    alphabetized_language_collection: function() {
      // This function sorts the columns in the terminology table by alphabetical order.
      let translations_collection = []
      // If the user has not yet selected an existing terminology then
      // order the columns by the translation languages specified
      // in the workflow, which is in this.translationsCollection.
      if (this.customTerminologySelected.length === 0)
        translations_collection = this.translationsCollection
      // If the user has selected an existing terminology then union the columns in that
      // terminology with the columns in the languages specified in the workflow, which
      // is in this.translations.Collection, and sort by the languages in that union.
      else {
        const custom_terminology_union = this.customTerminologyUnion
        custom_terminology_union.forEach(terminology_row => {
          for (const language_code in terminology_row) {
            const language_label = this.translateLanguages.filter(x => (x.value === language_code))[0].text;
            // avoid adding duplicates
            if (translations_collection.filter(x => x["text"] === language_label).length === 0)
              translations_collection.push({"text": language_label, "value": language_code})
          }
        })
      }
      translations_collection = translations_collection.filter(x => this.removedLanguages.includes(x.value) === false)
      return translations_collection.filter(x => x.text.length > 0)
          .sort(function(a, b) {
            const textA = a.text.toUpperCase();
            const textB = b.text.toUpperCase();
            return (textA < textB) ? -1 : (textA > textB) ? 1 : 0;
          });
    },
    vtt_url: function() {
      if (this.selected_lang_code !== '') {
        let vttcaption = this.vttcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (vttcaption) {
          return vttcaption.src
        }
      }
      return null
    },
    srt_url: function() {
      if (this.selected_lang_code !== '') {
        let srtcaption = this.srtcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (srtcaption) {
          return srtcaption.src
        }
      }
      return null
    },
    pollyaudio_url: function() {
      if (this.selected_lang_code !== '') {
        let pollyaudiotranscript = this.pollyaudiotranscripts.filter(x => (x.lang === this.selected_lang_code))[0];
        if (pollyaudiotranscript) {
          return pollyaudiotranscript.src
        } else {
        return null
        }
      } else {
        return null
      }
    },
    text_direction: function() {
      // This function is used to change text direction for right-to-left languages
      if (this.selected_lang_code === "ar" || this.selected_lang_code === "fa" || this.selected_lang_code === "he" || this.selected_lang_code === "ur" ) return "rtl"
      else return "ltr"
    }
  },
  watch: {
    // When user moves the cursor on the waveform
    // then focus the corresponding row in the caption table.
    waveform_seek_position: function () {
      this.handleWaveformSeek();
    },
    customTerminologySelected: async function() {
      // Now add phrases from the selected terminologies:
      await this.downloadTerminology()
    }
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
    this.selected_lang_code = ""
    clearInterval(this.workflow_status_polling)
  },
  activated: function () {
    console.log('activated component:', this.operator);
    this.getVttCaptions();
    this.getSrtCaptions();
    this.getPollyAudioTranscripts()
    this.isBusy = true;
    this.handleVideoPlay();
    this.handleVideoSeek();
    this.getWorkflowId();
    this.pollWorkflowStatus();
  },
  beforeDestroy: function () {
    clearInterval(this.workflow_status_polling)
  },
  methods: {
    getEmptyTerminologyRecord: function() {
      /* This function creates an empty terminology record.
         This is used when the user adds terminology rows in the terminology editor
         and when the user initially opens the custom terminology editor.
      */
      const emptyTerminologyRecord = {}
      emptyTerminologyRecord[this.sourceLanguageCode] = ""
      emptyTerminologyRecord[this.selected_lang_code] = ""
      return emptyTerminologyRecord
    },
    listTerminologiesRequest: async function () {
      let apiName = 'mieWorkflowApi'
      let path = 'service/translate/list_terminologies'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);
        this.customTerminologyList = response.data['TerminologyPropertiesList'].map(x => x.Name)
      } catch (error) {
        console.log(
          "ERROR: Failed to get vocabularies."
        );
        console.log(error)
      }
    },
    getLanguageList: async function () {
      // This function gets the list of languages that we'll show as columns
      // in the terminology table before the user selects an existing custom
      // terminology.
      this.translationsCollection = [];
      const asset_id = this.$route.params.asset_id;

      // Get the all the output for the TranslateWebCaptions operator.
      // We do this simply so we can get the list of languages that have been translated.
      let apiName = 'mieDataplaneApi'
      let path = 'metadata/' + asset_id + '/TranslateWebCaptions'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        let vm = this
        response.data.results.CaptionsCollection.forEach( (item) => {
            let languageLabel = vm.translateLanguages.filter(x => (x.value === item.TargetLanguageCode))[0].text;
            // save the language code to the translationsCollection
            this.translationsCollection.push(
              {text: languageLabel, value: item.TargetLanguageCode}
            );
          })
          console.log("got the collection")
          console.log(this.translationsCollection)
          // Got all the languages now.
          // Set the default language to the first one in the alphabetized list.
          if (this.alphabetized_language_collection.length > 0) {
            this.selected_lang = this.alphabetized_language_collection[0].text
            this.selected_lang_code = this.alphabetized_language_collection[0].value
            await this.getWebCaptions()
            console.log("got the captions")
            console.log(this.translationsCollection)
          }
          this.isBusy = false
      } catch (error) {
        console.log(
          "ERROR: Failed to get languages."
        );
        console.log(error)
      }

    },
    asyncForEach: async function(array, callback) {
      // This async function allows us to wait for all vtt files to be
      // downloaded.
      for (let index = 0; index < array.length; index++) {
        await callback(array[index]);
      }
    },
    getVttCaptions: async function () {

      let asset_id = this.$route.params.asset_id;

      let apiName = 'mieDataplaneApi'
      let path = 'metadata/' + asset_id + '/WebToVTTCaptions'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true
      };

      console.log("Getting VTT captions")

      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        if (response.status !== 200) {
            this.isBusy = false
            this.noTranslation = true
            console.log("ERROR: Could not retrieve Translation data.");
            console.log(response.data.Code);
            console.log(response.data.Message);
            console.log("Data:");
            console.log((response.data));
            console.log("Response: " + response.status);
          }

        console.log("Got VTT captions collection info")
        this.vttcaptions = [];
        this.num_caption_tracks = response.data.results.CaptionsCollection.length;
        console.log(this.num_caption_tracks)
        console.log("Got VTT captions files")
        let vm = this;
        // now get signed urls that can be used to download the vtt files from s3
        this.asyncForEach(response.data.results.CaptionsCollection, async(item) => {
          const bucket = item.Results.S3Bucket;
          const key = item.Results.S3Key;

          let apiName = 'mieDataplaneApi'
          let path = 'download'
          let requestOpts = {
              headers: {
                'Content-Type': 'application/json'
              },
              body: {
                "S3Bucket": bucket,
                "S3Key": key
                },
              response: true,
              responseType: 'text'
          }

          try {

            let res = await vm.$Amplify.API.post(apiName, path, requestOpts);
            // record the signed urls in an array

            vm.vttcaptions.push({'src': res.data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
            console.log("pushed vtt captions "+item.LanguageCode)
          } catch  (error){
            console.error(error)
          }
          console.log("vm.vvtcaptions")
          console.log(vm.vttcaptions)
          // now that we have all the signed urls to download vtt files,
          // update the captions in the video player for the currently selected
          // language. This will make sure the video player reflects any edits
          // that the user may have saved by clicking the Save Edits button.
          if (vm.selected_lang_code !== "") {
            // hide all the captions in the video player
            for (let i = 0; i < vm.player.textTracks().length; i++) {
              console.log("in the loop")
              let track = vm.player.textTracks()[i];
              track.mode = "disabled";
            }
            console.log("getting old tracks")
            // get the src for that language's vtt file
            let old_track = vm.player.textTracks()["tracks_"].filter(x => (x.language == vm.selected_lang_code))[0]
            // create properties for a new track
            let new_track = {}
            if (vm.player.textTracks().length > 0) {
              new_track.label = old_track.label
              new_track.language = old_track.language
              new_track.kind = old_track.kind
              // remove the old track for that vtt
              console.log("remove old tracks")
              vm.player.removeRemoteTextTrack(old_track)
            }
            new_track.src = vm.vtt_url
            // show the new caption in the video player
            new_track.mode = "showing"

            // add a new text track for that vtt
            const manualCleanup = false
            // manualCleanup is needed in order to avoid a warning
            console.log("add new tracks")
            vm.player.addRemoteTextTrack(new_track, manualCleanup)
          }
        });

      } catch (error) {
        console.log(error)
      }
    },
    getSrtCaptions: async function () {
      const asset_id = this.$route.params.asset_id;
      let apiName = 'mieDataplaneApi'
      let path = 'metadata/' + asset_id + '/WebToSRTCaptions'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        let captions_collection = [];
        this.num_caption_tracks = response.data.results.CaptionsCollection.length;

        this.asyncForEach(response.data.results.CaptionsCollection, async(item) => {
          // TODO: map the language code to a language label
          const bucket = item.Results.S3Bucket;
          const key = item.Results.S3Key;
          // get URL to captions file in S3

          let apiName = 'mieDataplaneApi'
          let path = 'download'
          let requestOpts = {
              headers: {
                'Content-Type': 'application/json'
              },
              body: {
                "S3Bucket": bucket,
                "S3Key": key
                },
              response: true,
              responseType: 'text'
          };

          try {

            let res = await this.$Amplify.API.post(apiName, path, requestOpts);
            // record the signed urls in an array
            captions_collection.push({'src': res.data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
          } catch  (error){
            console.error(error)
          }
        });
        this.srtcaptions = captions_collection

      } catch (error) {
        console.log(error)
      }
    },
    getPollyAudioTranscripts: async function () {

      const asset_id = this.$route.params.asset_id;
      let apiName = 'mieDataplaneApi'
      let path = 'metadata/' + asset_id + '/PollyWebCaptions'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        let captions_collection = [];
        this.asyncForEach(response.data.results.CaptionsCollection, async(item) => {
          // TODO: map the language code to a language label
          if (item.PollyStatus != "not supported") {
            const bucket = item.PollyAudio.S3Bucket;
            const key = item.PollyAudio.S3Key;
            // get URL to captions file in S3
            let apiName = 'mieDataplaneApi'
            let path = 'download'
            let requestOpts = {
                headers: {
                },
                body: {"S3Bucket": bucket, "S3Key": key},
                response: true,
                responseType: 'text'
            };

            try {

              let res = await this.$Amplify.API.post(apiName, path, requestOpts);
              captions_collection.push({'src': res.data, 'lang': item.TargetLanguageCode, 'label': item.TargetLanguageCode});

            }
            catch {
              this.pollyaudiotranscripts = captions_collection
            }
          }
        });
        this.pollyaudiotranscripts = captions_collection
      }
      catch(error) {
        console.log(error)
      }
    },
    downloadAudioFile() {
      const blob = new Blob([this.pollyaudio_url], {type: 'audio/mpeg', autoplay:'0', autostart:'false', endings:'native'});
      const e = document.createEvent('MouseEvents'),
        a = document.createElement('a');
      a.download = "audiofile.mp3";
      a.href = window.URL.createObjectURL(blob);
      a.dataset.downloadurl = ['audio/mpeg', a.download, a.href].join(':');
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
      a.dispatchEvent(e);
    },
    toHHMMSS(secs) {
      var sec_num = parseInt(secs, 10)
      var hours   = Math.floor(sec_num / 3600)
      var minutes = Math.floor(sec_num / 60) % 60
      var seconds = sec_num % 60

      return [hours,minutes,seconds]
        .map(v => v < 10 ? "0" + v : v)
        .filter((v,i) => v !== "00" || i > 0)
        .join(":")
    },
    sortWebCaptions(item) {
      // Keep the webCaptions table sorted on caption start time
      this.webCaptions.sort((a,b) => {
        a=parseFloat(a["start"])
        b=parseFloat(b["start"])
        return a<b?-1:1
      });
      if (item) {
        // Since table has mutated, regain focus on the row that the user is editing
        const new_index = this.webCaptions.findIndex(element => {
          return (element.start === item.start)
        })
        this.$refs["caption" + (new_index)].focus();
      }
    },
    changeStartTime(hms, index) {
      // input time must be in hh:mm:ss or mm:ss format
      let new_time = hms.split(':').reduce((acc,time) => (60 * acc) + +time);
      this.webCaptions[index].start = new_time
      this.sortWebCaptions(this.webCaptions[index])
    },
    changeEndTime(hms, index) {
      // input time must be in hh:mm:ss or mm:ss format
      let new_time = hms.split(':').reduce((acc,time) => (60 * acc) + +time);
      this.webCaptions[index].end = new_time
    },
    changeCaption(new_caption, index) {
      const Diff = require('diff');
      const diff = Diff.diffWords(this.webCaptions[index].caption, new_caption);
      // if no words were removed (i.e. only new words were added)...
      console.log("Translation edit:")
      console.log(diff)
      let old_phrase = ''
      let new_phrase = ''
      for (let i=0; i<=(diff.length-1); i++) {
        // if element contains key removed
        if ("removed" in diff[i] && diff[i].removed !== undefined) {
          old_phrase += diff[i].value+' '
        }
        // if element contains key added
        else if ("added" in diff[i] && diff[i].added !== undefined) {
          new_phrase += diff[i].value+' '
        }
        // otherwise if element is just words, or if it's the last element,
        // then save word change to custom terminology
        if (i === (diff.length-1) || !("added" in diff[i] || "removed" in diff[i])) {
          // if this value is a space and next value contains key 'added',
          // then break so that we can add that value to the new_phrase
          if (i !== (diff.length-1) && diff[i].value === ' ' && "added" in diff[i+1] && diff[i+1].added !== 'undefined') {
            continue
          } else {
            // or if this is the last element
            // or if this value is anything other than a space
            // then save to custom terminology
            if (old_phrase != '' && new_phrase != '') {
              // replace multiple spaces with a single space
              // and remove spaces at beginning or end of word
              old_phrase = old_phrase.replace(/ +(?= )/g, '').trim();
              new_phrase = new_phrase.replace(/ +(?= )/g, '').trim();
              // remove old_phrase from custom terminology, if it already exists
              this.customTerminologyUnsaved = this.customTerminologyUnsaved.filter(item => {return item.original_phrase !== old_phrase;});
              // add old_phrase to custom terminology
              this.customTerminologyUnsaved.push({[this.sourceLanguageCode]: "", [this.selected_lang_code]: new_phrase})
              console.log("CUSTOM TERMINOLOGY: " + JSON.stringify(this.customTerminologyUnsaved))
            }
            old_phrase = ''
            new_phrase = ''
          }
        }
      }
      this.webCaptions[index].caption = new_caption
    },
    captionClickHandler(index) {
      // pause video player and jump to the time for the selected caption
      this.player.currentTime(this.webCaptions[index].start)
      this.player.pause()
    },
    handleWaveformSeek() {
      // When user moves the cursor on the waveform
      // then focus the corresponding row in the caption table.
      let timeline_position = this.webCaptions.findIndex(function (item) {
        return (parseInt(item.start) <= this.waveform_seek_position && parseInt(item.end) >= this.waveform_seek_position)
      }.bind(this));
      if (timeline_position === -1) {
        // There is no caption at that seek position
        // so just seek to the beginning.
        timeline_position = 0
      }
      if (this.$refs.selectableTable) {
        var element = document.getElementById("caption" + timeline_position);
        element.scrollIntoView();
      }
    },
    handleVideoSeek() {
      // When user moves the cursor on the video player
      // then focus the corresponding row in the caption table.
      if (this.player) {
        this.player.controlBar.progressControl.on('mouseup', function () {
          const current_position = Math.round(this.player.currentTime());
          let timeline_position = this.webCaptions.findIndex(function (item) {
            return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)
          })
          if (timeline_position === -1) {
            // There is no caption at that seek position
            // so just seek to the beginning.
            timeline_position = 0
          }
          if (this.$refs.selectableTable) {
            var element = document.getElementById("caption" + (timeline_position));
            element.scrollIntoView();
          }
        }.bind(this));
      }
    },
    handleVideoPlay() {
      var last_position = 0;
      // Advance the selected row in the caption table when the video is playing
      this.player.on('timeupdate', function () {
        const current_position = Math.round(this.player.currentTime());
        if (current_position !== last_position) {
          let timeline_position = this.webCaptions.findIndex(function(item){return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)})
          if (this.$refs.selectableTable) {
            this.$refs.selectableTable.selectRow(timeline_position)
          }
          last_position = current_position;
        }
      }.bind(this));
    },
    getWorkflowId: async function() {

      const asset_id = this.asset_id
      let apiName = 'mieWorkflowApi'
      let path = 'workflow/execution/asset/' + asset_id
      let requestOpts = {
        response: true,
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        this.workflow_id = response.data[0].Id
        this.workflow_status = response.data[0].Status
        if ("CurrentStage" in response.data[0])
          this.waiting_stage = response.data[0].CurrentStage
        // get the list of languages to show the user
        this.getLanguageList();
        // get workflow config, needed for edit captions button
        this.getWorkflowConfig();
      } catch (error) {
        console.log(error)
      }
    },
    getWorkflowStatus: async function() {
      // This function gets the workflow status. If its in a running state
      // then we temporarily disable the ability for users to edit
      // translations in the GUI.
      let apiName = 'mieWorkflowApi'
      let path =  "workflow/execution/asset/" + this.asset_id
      let requestOpts = {
        headers: {},
        response: true,
        queryStringParameters: {} // optional
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);
        const new_workflow_status = response.data[0].Status
        if (this.workflow_status !== 'Complete'
          && new_workflow_status === 'Complete') {
          this.getVttCaptions()
        }
        this.workflow_status = new_workflow_status
      } catch (error) {
        console.log("ERROR: Failed to get workflow status");
        console.log(error)
      }
    },
    getWorkflowConfig: async function() {
      // This function gets the workflow configuration that is used
      // to update the saved vtt and srt caption files after a user saves
      // translation edits.

      let apiName = 'mieWorkflowApi'
      let path = 'workflow/execution/' + this.workflow_id
      let requestOpts = {
        response: true,
      };
      try {
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);
        this.workflow_config = response.data.Configuration
        this.sourceLanguageCode = response.data.Configuration.WebCaptionsStage2.WebCaptions.SourceLanguageCode
        this.terminology_used = response.data.Configuration.Translate.TranslateWebCaptions.TerminologyNames.map(x => x.Name)
        this.parallel_data_used = response.data.Configuration.Translate.TranslateWebCaptions.ParallelDataNames.map(x => x.Name)
        this.workflow_definition = response.data.Workflow
        const operator_info = []
        const sourceLanguage = this.translateLanguages.filter(x => (x.value === this.sourceLanguageCode))[0].text;
        operator_info.push({"name": "Source Language", "value": sourceLanguage})
        if (this.terminology_used) {
          if (this.terminology_used.length === 1)
            operator_info.push({"name": "Custom Terminology", "value": this.terminology_used[0]})
          else
            operator_info.push({"name": "Custom Terminologies", "value": this.terminology_used.join().replace(/,/g, ', ')})

        }
        if (this.parallel_data_used) {
          if (this.parallel_data_used.length === 1)
            operator_info.push({"name": "Parallel Data", "value": this.parallel_data_used[0]})
          else
            operator_info.push({"name": "Parallel Data", "value": this.parallel_data_used.join().replace(/,/g, ', ')})

        }
        this.$store.commit('updateOperatorInfo', operator_info)
      } catch (error) {
        console.log(error)
      }
    },
    disableUpstreamStages()  {
      // This function disables all the operators in stages above Translate,
      // so all that's left are the operators that update vtt and srt files.
      let data = {
        "Name": "ContentLocalizationWorkflow",
        "Configuration": this.workflow_config
      }
      data["Input"] = {
        "AssetId": this.asset_id
      };
      let workflow = this.workflow_definition
      let stage_name = workflow.StartAt
      let stage = workflow["Stages"][stage_name]
      let end = false
      // This loop starts at the first stage and
      // goes until the staged named "End"
      while (end == false) {
        // If the current stage is End then end the loop.
        if ("End" in stage && stage["End"] == true){
          end = true
        }
        // If the current stage is TransformText then end the loop.
        else if (stage_name == "TransformText") {
          end = true
        }
        // For all other stages disable all the operators in the stage
        else {
          // Disable all the operators in the stage
          for (const operator in data["Configuration"][stage_name]){
            data["Configuration"][stage_name][operator]["Enabled"] = false
          }
          // Now look at the next stage in the workflow
          stage_name = stage["Next"]
          stage = workflow["Stages"][stage_name]
        }
      }

      return data

    },
    rerunWorkflow: async function () {
      // This function reruns TransformText in order to
      // regenerate VTT and SRT files.
      let data = this.disableUpstreamStages();
      data["Configuration"]["Translate"]["TranslateWebCaptions"].MediaType = "MetadataOnly";
      let apiName = 'mieWorkflowApi'
      let path = 'workflow/execution'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true,
          body: data,
          queryStringParameters: {} // optional
      };
      try {
        let response = await this.$Amplify.API.post(apiName, path, requestOpts);
        let asset_id = response.data.AssetId;
        let wf_id = response.data.Id;
        console.log("Media assigned asset id and workflow id: " + asset_id + "workflow id:" + wf_id);
        this.pollWorkflowStatus()
        if (response.status !== 200) {
          console.log("ERROR: Failed to start workflow.");
          console.log(response.data.Code);
          console.log(response.data.Message);
          console.log("URL: " + this.WORKFLOW_API_ENDPOINT + 'workflow/execution');
          console.log("Data:");
          console.log(JSON.stringify(data));
          console.log((data));
          console.log("Response: " + response.status);
        } else {
          this.saveNotificationMessage += " and workflow resumed"
          console.log("workflow executing");
          console.log(response);
        }
      } catch (error) {
        alert(
          "ERROR: Failed to start workflow. Check Workflow API logs."
        );
        console.log(error)
      }
    },
    saveCaptions: async function () {
      this.workflow_status = "Started"
      // This function saves translation edits to the dataplane
      this.$refs['save-modal'].hide()
      this.isSaving=true;
      const operator_name = "WebCaptions_"+this.selected_lang_code
      const web_captions = {"WebCaptions": this.webCaptions}
      let body={
        "OperatorName": operator_name ,
        "Results": web_captions,
        "WorkflowId": this.workflow_id
      }
      let apiName = 'mieDataplaneApi'
      let path = 'metadata/' + this.asset_id
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true,
          body: body,
          queryStringParameters: {} // optional
      };



      try {
        let response = await this.$Amplify.API.post(apiName, path, requestOpts);
        if (response.status === 200) {
            this.isSaving=true;
            console.log("Saving translation for " + this.selected_lang_code)
            this.rerunWorkflow();
          }
         else {
            console.log("ERROR: Failed to upload captions.");
            console.log(response.data.Code);
            console.log(response.data.Message);
            console.log("Response: " + response.status);
          }
      } catch (error) {
        alert(
          "ERROR: Failed to start workflow. Check Workflow API logs."
        );
        console.log(error)
      }
    },
    showTerminologyConfirmation: async function() {
      // When we open the custom terminology modal, then we'll initialize the
      // terminology table to include a single empty terminology so the table shows
      // at least one row.
      if (this.customTerminologyUnsaved.length === 0) {
        this.customTerminologyUnsaved = [this.getEmptyTerminologyRecord()]
      }
      await this.listTerminologiesRequest()
      this.$refs['terminology-modal'].show()
    },
    convertToCSV: function(objArray) {
      var array = typeof objArray != 'object' ? JSON.parse(objArray) : objArray;
      var str = '';
      for (var i = 0; i < array.length; i++) {
        var line = '';
        for (var index in array[i]) {
          if (line != '') line += ','
          line += array[i][index];
        }
        str += line + '\r\n';
      }
      return str;
    },
    saveTerminology: async function () {
      const csv_header = Object.keys(this.customTerminologyUnion[0]).toString()
      this.customTerminologyCSV = csv_header+'\n'+this.convertToCSV(this.customTerminologyUnion)
      this.customTerminologyUnsaved = []
      this.customTerminologySaved = []
      await this.saveTerminologyRequest()
    },
    saveTerminologyRequest: async function () {
      const csv = this.customTerminologyCSV
      let apiName = 'mieWorkflowApi'
      let path = 'service/translate/create_terminology'
      let requestOpts = {
          headers: {
            'Content-Type': 'application/json'
          },
          response: true,
          body: {"terminology_name": this.customTerminologyName, "terminology_csv": csv},
          queryStringParameters: {} // optional
      };

      try {
        let response = await this.$Amplify.API.post(apiName, path, requestOpts);
        if (response.status === 200) {
            console.log("Success! Custom terminology saved.")
            this.terminologyNotificationMessage = "Saved terminology: " + this.customTerminologyName
            this.terminologyNotificationStatus = "success"
            this.showTerminologyNotification = 5
          } else {
            console.log("Failed to save vocabulary")
            this.vocabularyNotificationMessage = "Failed to save terminology: " + this.customTerminologyName
            this.terminologyNotificationStatus = "danger"
            this.showTerminologyNotification = 5
          }
          // clear the custom terminology name used in the save terminology modal form
          this.customTerminologyCreateNew = ""
          this.customTerminologySelected = []
          this.customTerminologySaved = []
      } catch (error) {
        alert(
          "ERROR: Failed to save terminology."
        );
        console.log(error)
      }
    },
    deleteTerminology: async function () {
      this.$refs['delete-terminology-modal'].show()
    },
    deleteTerminologyRequest: async function (customTerminologySelected) {
      if (customTerminologySelected.length === 1)
        this.terminologyNotificationMessage = "Deleted terminology: " + customTerminologySelected
      if (customTerminologySelected.length > 1)
        this.terminologyNotificationMessage = "Deleted terminologies: " + customTerminologySelected

      for (const i in customTerminologySelected) {
        this.$refs['delete-terminology-modal'].hide()
        this.$refs['terminology-modal'].hide()
        console.log("Delete terminology request:")
        let apiName = 'mieWorkflowApi'
        let path = 'service/translate/delete_terminology'
        let requestOpts = {
            headers: {
              'Content-Type': 'application/json'
            },
            response: true,
            body: {"terminology_name":customTerminologySelected[i]},
            queryStringParameters: {} // optional
        };

        try {
          let response = await this.$Amplify.API.post(apiName, path, requestOpts);
          if (response.status === 200) {
              console.log("Success! Terminology deleted.")
              this.terminologyNotificationStatus = "success"
              this.showTerminologyNotification = 5
              // reset the radio button selection
              this.customTerminologySelected = ""
              this.customTerminologySaved = []
              this.listTerminologiesRequest()
            } else {
              console.log("Failed to delete vocabulary")
              this.terminologyNotificationMessage = "Failed to delete vocabulary: " + customTerminologySelected[i]
              this.terminologyNotificationStatus = "danger"
              this.showTerminologyNotification = 5
            }
            // clear the custom terminology name used in the save terminology modal form
            this.customTerminologyCreateNew = ""
            this.customTerminologySelected = ""
            this.customTerminologySaved = []
        } catch (error) {
          alert(
            "ERROR: Failed to delete terminology."
          );
          console.log(error)
        }
      }
    },
    downloadTerminology: async function() {
      this.customTerminologySaved = []
      let apiName = 'mieWorkflowApi'
      let path = 'service/translate/download_terminology'
      for (const i in this.customTerminologySelected) {
        let requestOpts = {
            headers: {
              'Content-Type': 'application/json'
            },
            response: true,
            body: {"terminology_name":this.customTerminologySelected[i]},
            queryStringParameters: {} // optional
        };
        try {
          let response = await this.$Amplify.API.post(apiName, path, requestOpts);
          const csv = response.data.terminology.replace(/"/g, '')
            const json = this.csvJSON(csv)
            this.customTerminologySaved = this.customTerminologySaved.concat(json)
        } catch (error) {
          alert(
              "ERROR: Failed to delete terminology."
          );
          console.log(error)
        }
      }
    },
    csvJSON: function(csv) {
      var lines=csv.split("\n");
      var json = [];
      var headers=lines[0].split(",");
      for(let i=1;i<lines.length;i++){
        let obj = {};
        let currentline = lines[i].split(",");
        for(let j = 0; j<headers.length; j++){
          obj[headers[j]] = currentline[j];
        }
        json.push(obj);
      }
      return json;
    },
    getWebCaptions: async function () {
      // This functions gets paginated web caption data

      const operator_name = "WebCaptions_"+this.selected_lang_code
      let cursor=''
      this.webCaptions = []
      console.log("call getWebCaptionPages")
      this.getWebCaptionPages(this.asset_id, operator_name, cursor)
      console.log("after call getWebCaptionPages")
      console.log(this.webCaptions)

      // switch the video player to show the selected language
      // by first disabling all the text tracks, like this:
      for (let i = 0; i < this.player.textTracks().length; i++) {
        let track = this.player.textTracks()[i];
        track.mode = "disabled";
      }
      console.log("before player")
      // then showing the text track for the selected language
      if (this.player.textTracks().length > 0) {
        this.player.textTracks()["tracks_"].filter(x => (x.language == this.selected_lang_code))[0].mode = "showing"
      }
      console.log("after player")
    },
    getWebCaptionPages: async function (asset_id, operator_name, cursor) {

      let apiName = 'mieDataplaneApi'
      console.log("getWebCaptionPages")
      let path = 'metadata/' + this.asset_id + '/' + operator_name
      console.log("getWebCaptionPages asset__id "+this.asset_id)
      console.log("path "+path)
      let qs = {}
      console.log("getWebCaptionPages")
      if (cursor.length != 0) {
        //path = path + '?cursor=' + cursor
        qs = {"cursor":cursor}
        console.log("cursr getWebCaptionPages")
      }
      console.log("getWebCaptionPages")
      let requestOpts = {
        response: true,
        headers: {'Content-Type': 'application/json'},
        queryStringParameters: qs
      };

      console.log("before try getWebCaptionPages")
      console.log(requestOpts)

      try {
        console.log("try getWebCaptionPages")
        let response = await this.$Amplify.API.get(apiName, path, requestOpts);

        console.log("getWebCaptiosPages reponse")
        console.log(response)
        if (response.status !== 200) {
            console.log("ERROR: Failed to download captions.");
            console.log(response.data.Code);
            console.log(response.data.Message);
            console.log("Response: " + response.status);
            this.isBusy = false
            this.noTranscript = true
          }
          if (response.data.results) {
            cursor = response.data.cursor;
            this.webCaptions = response.data.results["WebCaptions"]
            this.sortWebCaptions()
            this.isBusy = false
            if (cursor)
              this.getWebCaptionPages(token,url,cursor)
          } else {
            this.videoOptions.captions = []
          }
      } catch (error) {
        this.showDataplaneAlert = true
        console.log(error)
      }
    },
    add_row(index) {
      this.webCaptions.splice(index+1, 0, {"start":this.webCaptions[index].end,"caption":"","end":this.webCaptions[index+1].start})
      this.$refs["caption"+(index+1)].focus();
      this.player.currentTime(this.webCaptions[index+1].start)
      this.player.pause()
    },
    delete_row(index) {
      this.webCaptions.splice(index, 1)
    },
    add_language() {
      this.$refs['add-language-modal'].show()
    },
    add_language_request() {
      console.log("adding language " + this.newLanguageCode)
      // if language was previously removed, then undo the prior remove by removing this language from the list of removed languages
      this.removedLanguages = this.removedLanguages.filter(x => x !== this.newLanguageCode)
      // add the new language as a new column in the terminology table
      const language_label = this.translateLanguages.filter(x => (x.value === this.newLanguageCode))[0].value;
      this.addedLanguages = this.addedLanguages.concat({"text":language_label, "value": this.newLanguageCode})
      // add the new language as a column in the terminology table data
      const terminology_row = this.customTerminologyUnsaved.pop()
      terminology_row[this.newLanguageCode] = ""
      this.customTerminologyUnsaved = this.customTerminologyUnsaved.concat(terminology_row)

      // reset the language code used in the add-language-modal form
      this.newLanguageCode=""
    },
    remove_language() {
      this.$refs['remove-language-modal'].show()
    },
    remove_language_request() {
      console.log("removing language " + this.removeLanguageCode)
      this.addedLanguages = this.addedLanguages.filter(x => x.value !== this.removeLanguageCode)
      this.removedLanguages = [this.removeLanguageCode].concat(this.removedLanguages)
      // reset the language code used in the form on remove-language-modal
      console.log("this.customTerminologyUnsaved")
      this.customTerminologyUnsaved.map(x => delete x[this.removeLanguageCode])
      this.customTerminologySaved.map(x => delete x[this.removeLanguageCode])
      console.log(this.customTerminologyUnsaved)
      console.log(this.customTerminologySaved)
      this.removeLanguageCode=""
    },
    add_terminology_row(index) {
      // The index provided is the index into the concatenated unsaved and saved terminologies.
      // Unsaved vocab will always be listed first, so we're converting the index here so that
      // we can splice appropriately in the unsaved or saved terminology.
      if (index < this.customTerminologyUnsaved.length) {
        this.customTerminologyUnsaved.splice(index+1, 0, this.getEmptyTerminologyRecord())
      } else {
        this.customTerminologyUnsaved.splice(index-this.customTerminologyUnsaved.length, 0, this.getEmptyTerminologyRecord())
      }
      console.log("added " + JSON.stringify(this.getEmptyTerminologyRecord()))
    },
    delete_terminology_row(index) {
      // The index provided is the index into the concatenated unsaved and saved terminologies
      // Unsaved terminologies will always be listed first, so we convert the index as follows so that
      // we can splice appropriately in the unsaved or saved terminology.
      if (index < this.customTerminologyUnsaved.length) {
        this.customTerminologyUnsaved.splice(index, 1)
      } else {
        const index_into_saved_terminology = index - this.customTerminologyUnsaved.length
        this.customTerminologySaved.splice(index_into_saved_terminology, 1)
      }
      // if (this.customTerminologyUnion.length === 0){
      //   this.customTerminologyUnsaved.push(this.emptyTerminologyRecord)
      // }
    },
    pollWorkflowStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 5000;
      clearInterval(this.workflow_status_polling)
      this.workflow_status_polling = setInterval(() => {
        this.getWorkflowStatus();
      }, poll_frequency)
    },
  }
}
</script>

<style>
  .start-time-field {
    padding: 0 !important;
    margin: 0 !important;
    margin-bottom: 4px !important;
    border: 0 !important;
    height: auto;
    background-color: white !important;
  }
  .stop-time-field {
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    height: auto;
    background-color: white !important;
  }
  .hidden_header {
    display: none;
  }
  .event-line-editor {
    overflow: scroll;
    height: 500px;
    border-top: 1px solid #e2e2e2;
    border-bottom: 1px solid #e2e2e2;
  }
  /* these options needed for MacOS to make scrollbar visible when not in use */
  .event-line-editor::-webkit-scrollbar {
    -webkit-appearance: none;
    width: 7px;
  }
  /* these options needed for MacOS to make scrollbar visible when not in use */
  .event-line-editor::-webkit-scrollbar-thumb {
    border-radius: 4px;
    background-color: rgba(0, 0, 0, .5);
    -webkit-box-shadow: 0 0 1px rgba(255, 255, 255, .5);
  }
  .custom-text-field {
    background-color: white !important;
    border: 0;
  }
  .highlightedBorder {
    border-left: 1px solid #cc181e;
    background-color: green;
  }
  tr.b-table-row-selected {
    border-left: 1px solid #cc181e !important;
  }
  table.b-table-selectable > tbody > tr.b-table-row-selected > td {
    background-color: white !important;
  }
  .btn-group-xs > .btn, .btn-xs {
    padding: .25rem .4rem;
    font-size: .875rem;
    line-height: .5;
    border-radius: .2rem;
  }
</style>

