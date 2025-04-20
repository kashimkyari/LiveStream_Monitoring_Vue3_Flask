<template>
  <div class="mobile-dashboard-tab">
    <div class="tab-header">
      <h2>{{ title }}</h2>
      <div class="refresh-button" @click="$emit('refresh')" v-if="showRefreshButton">
        <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoading }" />
      </div>
    </div>
    
    <div class="tab-content">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>{{ loadingText || 'Loading...' }}</p>
      </div>
      
      <div v-else-if="isEmpty && emptyStateText" class="empty-state">
        <font-awesome-icon :icon="emptyStateIcon" class="empty-state-icon" v-if="emptyStateIcon" />
        <p>{{ emptyStateText }}</p>
      </div>
      
      <div v-else class="tab-content-inner">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
import { inject } from 'vue'

export default {
  name: 'MobileDashboardTab',
  props: {
    title: {
      type: String,
      required: true
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    isEmpty: {
      type: Boolean,
      default: false
    },
    emptyStateText: {
      type: String,
      default: ''
    },
    emptyStateIcon: {
      type: String,
      default: ''
    },
    loadingText: {
      type: String,
      default: ''
    },
    showRefreshButton: {
      type: Boolean,
      default: true
    }
  },
  emits: ['refresh'],
  setup() {
    // Get theme from parent via injection
    const isDarkTheme = inject('theme')
    
    return {
      isDarkTheme
    }
  }
}
</script>

<style scoped>
.mobile-dashboard-tab {
  margin-bottom: 1.5rem;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tab-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
}

.refresh-button {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--hover-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-light);
  transition: background-color 0.2s;
}

.refresh-button:hover {
  background-color: var(--hover-bg-darker);
}

.tab-content {
  position: relative;
  min-height: 100px;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--text-light);
  background-color: var(--input-bg);
  border-radius: 8px;
  border: 1px dashed var(--border-color);
}

.empty-state-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: var(--text-light);
}

.tab-content-inner {
  /* Custom styles for the content area */
}
</style>