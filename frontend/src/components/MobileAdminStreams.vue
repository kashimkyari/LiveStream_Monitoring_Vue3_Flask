<template>
  <div class="streams-tab">
    <div class="tab-header">
      <h2>Active Streams</h2>
      <div class="filter-actions">
        <select 
          v-model="platformFilter" 
          class="platform-filter"
          @change="applyFilters"
        >
          <option value="">All Platforms</option>
          <option value="chaturbate">Chaturbate</option>
          <option value="stripchat">Stripchat</option>
        </select>
        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search streamer..."
            @input="applyFiltersDebounced"
            class="search-input"
          />
          <font-awesome-icon icon="search" class="search-icon" />
        </div>
      </div>
    </div>
    
    <!-- Stream list -->
    <div class="stream-list" v-if="!loading">
      <p v-if="filteredStreams.length === 0" class="empty-message">
        No streams match your filters
      </p>
      <mobile-stream-card
        v-for="stream in filteredStreams"
        :key="stream.id"
        :stream="stream"
        :is-refreshing="refreshingStreams[stream.id]"
        @click="openStreamDetails(stream)"
        @refresh="refreshStream(stream)"
      />
    </div>
    <div v-else class="loading-container">
      <mobile-loading-spinner :size="40" text="Loading streams..." />
    </div>
    
    <!-- Add stream button -->
    <div class="floating-action-button" @click="$emit('add-stream')">
      <font-awesome-icon icon="plus" />
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import MobileStreamCard from './MobileStreamCard.vue'
import MobileLoadingSpinner from './MobileLoadingSpinner.vue'
import debounce from 'lodash/debounce'
import axios from 'axios'
import { useToast } from 'vue-toastification'

export default {
  name: 'MobileAdminStreams',
  components: {
    MobileStreamCard,
    MobileLoadingSpinner
  },
  props: {
    loading: Boolean,
    refreshingStreams: Object,
    allStreams: Array,
    agents: Array
  },
  emits: ['refresh', 'stream-selected', 'add-stream'],
  setup(props, { emit }) {  // Add emit parameter
    const toast = useToast()
    const platformFilter = ref('')
    const searchQuery = ref('')
    
    // Filter streams based on platform and search query
    const filteredStreams = computed(() => {
      let result = props.allStreams
      if (platformFilter.value) {
        result = result.filter(stream => 
          (stream.type || stream.platform || '').toLowerCase() === platformFilter.value.toLowerCase()
        )
      }
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(stream => 
          (stream.streamer_username || '').toLowerCase().includes(query)
        )
      }
      return result
    })

    // Register user activity
    const registerUserActivity = () => {
      axios.post('/api/user-activity')
    }

    // Apply filters with debounce
    const applyFiltersDebounced = debounce(() => {
      registerUserActivity()
    }, 300)

    // Refresh stream
    const refreshStream = async (stream) => {
      try {
        const response = await axios.post(`/api/streams/${stream.id}/refresh`)
        toast.success('Stream refreshed')
        return response.data
      } catch (error) {
        console.error('Error refreshing stream:', error)
        toast.error('Failed to refresh stream')
        return null
      }
    }

    // Open stream details
    const openStreamDetails = (stream) => {
      emit('stream-selected', stream)  // Use emit instead of $emit
      registerUserActivity()
    }

    // Watch for changes and register activity
    watch(platformFilter, () => registerUserActivity())
    watch(searchQuery, () => registerUserActivity())

    return {
      platformFilter,
      searchQuery,
      filteredStreams,
      applyFiltersDebounced,
      refreshStream,
      openStreamDetails
    }
  }
}
</script>
<style scoped>
.mobile-admin-dashboard,
.mobile-admin-dashboard * {
  font-family: var(--font-family);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.mobile-admin-dashboard {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  color: var(--text-color);
  padding-bottom: 70px; /* Space for bottom nav */
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 1rem;
}
</style>