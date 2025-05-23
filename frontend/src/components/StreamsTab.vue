<template>
  <section class="streams-tab">
    <div class="tab-header">
      <h2>Stream Management</h2>
      <div class="controls">
        <div class="search-box">
          <font-awesome-icon icon="search" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search streams..." 
            @input="filterStreams"
          />
        </div>
        <button @click="$emit('create')" class="create-button" v-wave>
          <font-awesome-icon icon="plus" /> Add Stream
        </button>
      </div>
    </div>
    <div class="streams-table-wrapper" ref="tableWrapper">
      <div class="streams-table">
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Streamer</th>
                <th>Platform</th>
                <th>Agent</th>
                <th class="text-center">Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stream in filteredStreams" 
                  :key="stream.id" 
                  class="stream-row"
                  :data-id="stream.id"
                  :ref="`streamRow_${stream.id}`">
                <td>
                  <div class="streamer-info">
                    <div class="avatar">{{ stream.streamer_username.charAt(0).toUpperCase() }}</div>
                    <div>
                      <div class="streamer-name">{{ stream.streamer_username }}</div>
                      <div class="streamer-url">{{ formatUrl(stream.room_url) }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="platform-tag" :class="stream.platform.toLowerCase()">
                    {{ stream.platform }}
                  </span>
                </td>
                <td>
                  <div class="agent-info">
                    <template v-if="getAssignedAgent(stream)">
                      <div class="agent-avatar" v-for="agent in [getAssignedAgent(stream)]" :key="agent.id">
                        {{ agent.username.charAt(0).toUpperCase() }}
                      </div>
                      <div class="agent-name" v-for="agent in [getAssignedAgent(stream)]" :key="agent.id">
                        {{ agent.username }}
                      </div>
                    </template>
                    <div v-else class="unassigned-label">
                      <font-awesome-icon icon="user-slash" />
                      <span>Unassigned</span>
                    </div>
                  </div>
                </td>
                <td class="text-center">
                  <span class="status-badge" :class="stream.status === 'online' ? 'active' : 'inactive'">
                    {{ stream.status === 'online' ? 'Online' : 'Offline' }}
                  </span>
                </td>
                <td class="actions">
                  <div class="action-buttons">
                    <button @click.stop="$emit('view', stream)" class="icon-button view" title="View Stream" v-wave>
                      <font-awesome-icon icon="eye" />
                    </button>
                    <button @click.stop="handleRefresh(stream)" class="icon-button refresh" title="Refresh Stream" v-wave>
                      <font-awesome-icon icon="sync" />
                    </button>
                    <button @click.stop="openEditorModal(stream)" class="icon-button edit" title="Edit Stream" v-wave>
                      <font-awesome-icon icon="edit" />
                    </button>
                    <button @click.stop="confirmDelete(stream)" class="icon-button danger" title="Delete Stream" v-wave>
                      <font-awesome-icon icon="trash" />
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredStreams.length === 0">
                <td colspan="5" class="empty-state">
                  <div class="empty-content">
                    <font-awesome-icon icon="stream" class="empty-icon" />
                    <p>No streams found</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <!-- Mobile Card View -->
    <div class="mobile-cards">
      <div v-for="stream in filteredStreams" 
           :key="stream.id" 
           class="stream-card"
           :data-id="stream.id"
           :ref="`streamCard_${stream.id}`">
        <div class="card-header">
          <div class="streamer-info">
            <div class="avatar">{{ stream.streamer_username.charAt(0).toUpperCase() }}</div>
            <div>
              <div class="streamer-name">{{ stream.streamer_username }}</div>
              <div class="streamer-url">{{ formatUrl(stream.room_url) }}</div>
            </div>
          </div>
          <span class="status-badge" :class="stream.status === 'online' ? 'active' : 'inactive'">
            {{ stream.status === 'online' ? 'Online' : 'Offline' }}
          </span>
        </div>
        <div class="card-details">
          <div class="detail-row">
            <span class="detail-label">Platform:</span>
            <span class="platform-tag" :class="stream.platform.toLowerCase()">
              {{ stream.platform }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Agent:</span>
            <div class="agent-info">
              <template v-if="getAssignedAgent(stream)">
                <div class="agent-avatar">{{ getAssignedAgent(stream).username.charAt(0).toUpperCase() }}</div>
                <div class="agent-name">{{ getAssignedAgent(stream).username }}</div>
              </template>
              <div v-else class="unassigned-label">
                <font-awesome-icon icon="user-slash" />
                <span>Unassigned</span>
              </div>
            </div>
          </div>
        </div>
        <div class="card-actions">
          <button @click.stop="$emit('view', stream)" class="icon-button view" title="View Stream" v-wave>
            <font-awesome-icon icon="eye" />
          </button>
          <button @click.stop="handleRefresh(stream)" class="icon-button refresh" title="Refresh Stream" v-wave>
            <font-awesome-icon icon="sync-alt" />
          </button>
          <button @click.stop="openEditorModal(stream)" class="icon-button edit" title="Edit Stream" v-wave>
            <font-awesome-icon icon="edit" />
          </button>
          <button @click.stop="confirmDelete(stream)" class="icon-button danger" title="Delete Stream" v-wave>
            <font-awesome-icon icon="trash" />
          </button>
        </div>
      </div>
      <div v-if="filteredStreams.length === 0" class="empty-state-mobile">
        <div class="empty-content">
          <font-awesome-icon icon="stream" class="empty-icon" />
          <p>No streams found</p>
        </div>
      </div>
    </div>
    <!-- Confirmation Modal -->
    <confirmation-modal
      v-if="showDeleteModal"
      title="Delete Stream"
      message="Are you sure you want to delete this stream? This action cannot be undone."
      action-text="Delete"
      @close="cancelDelete"
      @confirm="confirmDeleteAction"
    />
    <!-- Stream Editor Modal -->
    <stream-editor-modal
      v-if="showEditorModal"
      :stream="streamToEdit"
      :agents="agents"
      @close="closeEditorModal"
      @created="handleStreamCreated"
      @updated="handleStreamUpdated"
    />
    <!-- Toast Notification -->
    <div class="toast-container" ref="toastContainer">
      <div v-for="(toast, toastIndex) in toasts" 
           :key="toastIndex" 
           class="toast" 
           :class="toast.type"
           :ref="`toast_${toastIndex}`">
        <div class="toast-icon">
          <font-awesome-icon :icon="getToastIcon(toast.type)" />
        </div>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div class="toast-message">{{ toast.message }}</div>
        </div>
        <button class="toast-close" @click="removeToast(toastIndex)">
          <font-awesome-icon icon="times" />
        </button>
      </div>
    </div>
  </section>
</template>

<script>
import axios from 'axios';
import anime from 'animejs';
import ConfirmationModal from './ConfirmationModal.vue';
import StreamEditorModal from './StreamEditorModal.vue';

export default {
  name: 'StreamsTab',
  components: {
    ConfirmationModal,
    StreamEditorModal
  },
  props: {
    streams: {
      type: Array,
      default: () => []
    },
    agents: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      searchQuery: '',
      filteredStreams: [],
      showDeleteModal: false,
      streamToDelete: null,
      showEditorModal: false,
      streamToEdit: null,
      toasts: [],
      lastDeletedStreamId: null
    }
  },
  emits: ['create', 'edit', 'delete', 'view', 'refresh', 'stream-updated', 'stream-created', 'stream-deleted'],
  watch: {
    streams: {
      immediate: true,
      handler(newStreams) {
        this.filteredStreams = [...newStreams];
        this.$nextTick(() => {
          this.animateStreamRows();
        });
      }
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.animateStreamRows();
      this.initScrollbars();
      anime({
        targets: '.tab-header h2',
        translateY: [20, 0],
        opacity: [0, 1],
        easing: 'easeOutQuad',
        duration: 800
      });
      anime({
        targets: '.controls',
        translateY: [15, 0],
        opacity: [0, 1],
        easing: 'easeOutQuad',
        delay: 200,
        duration: 600
      });
      anime({
        targets: '.streams-table',
        scale: [0.98, 1],
        opacity: [0, 1],
        easing: 'easeOutElastic(1, .8)',
        delay: 400,
        duration: 800
      });
    });
  },
  methods: {
    getAssignedAgent(stream) {
      if (stream.assignments && stream.assignments.length > 0) {
        const firstAssignment = stream.assignments[0];
        if (firstAssignment.agent && firstAssignment.agent.username) {
          return firstAssignment.agent;
        }
        const foundAgent = this.agents.find(agent => agent.id === firstAssignment.agent_id);
        return foundAgent || null;
      }
      return null;
    },
    filterStreams() {
      if (!this.searchQuery) {
        this.filteredStreams = [...this.streams];
        return;
      }
      const query = this.searchQuery.toLowerCase();
      this.filteredStreams = this.streams.filter(stream => {
        const agent = this.getAssignedAgent(stream);
        const agentUsername = agent ? agent.username.toLowerCase() : '';
        return stream.streamer_username.toLowerCase().includes(query) || 
               stream.platform.toLowerCase().includes(query) ||
               agentUsername.includes(query);
      });
      this.$nextTick(() => {
        anime({
          targets: '.stream-row, .stream-card',
          opacity: [0, 1],
          translateY: [10, 0],
          easing: 'easeOutQuad',
          delay: anime.stagger(50),
          duration: 400
        });
      });
    },
    initScrollbars() {
      // Custom scrollbar initialization if needed
    },
    animateStreamRows() {
      anime({
        targets: '.stream-row',
        translateX: [-20, 0],
        opacity: [0, 1],
        easing: 'easeOutQuad',
        delay: anime.stagger(100, {start: 500}),
        duration: 600
      });
      anime({
        targets: '.stream-card',
        translateY: [20, 0],
        opacity: [0, 1],
        easing: 'easeOutQuad',
        delay: anime.stagger(150, {start: 500}),
        duration: 600
      });
    },
    formatUrl(url) {
      try {
        const urlObj = new URL(url);
        return urlObj.hostname;
      } catch (e) {
        return url;
      }
    },
    isStreamActive(stream) {
      if (stream.platform === 'Chaturbate') {
        return !!stream.chaturbate_m3u8_url;
      } else if (stream.platform === 'Stripchat') {
        return !!stream.stripchat_m3u8_url;
      }
      return false;
    },
    confirmDelete(stream) {
      this.streamToDelete = stream;
      this.showDeleteModal = true;
      this.$nextTick(() => {
        anime({
          targets: '.modal-container',
          opacity: [0, 1],
          scale: [0.9, 1],
          easing: 'easeOutQuint',
          duration: 300
        });
      });
    },
    cancelDelete() {
      anime({
        targets: '.modal-container',
        opacity: [1, 0],
        scale: [1, 0.9],
        easing: 'easeInQuint',
        duration: 200,
        complete: () => {
          this.showDeleteModal = false;
          this.streamToDelete = null;
        }
      });
    },
    async confirmDeleteAction() {
      if (!this.streamToDelete) return;

      const streamId = this.streamToDelete.id;
      const streamName = this.streamToDelete.streamer_username;
      const rowEl = this.$refs[`streamRow_${streamId}`]?.[0];
      const cardEl = this.$refs[`streamCard_${streamId}`]?.[0];

      if (rowEl) {
        anime({
          targets: rowEl,
          translateX: [0, -50],
          opacity: [1, 0],
          easing: 'easeInCubic',
          duration: 300
        });
      }

      if (cardEl) {
        anime({
          targets: cardEl,
          translateX: [0, -50],
          opacity: [1, 0],
          easing: 'easeInCubic',
          duration: 300
        });
      }

      try {
        await new Promise(resolve => setTimeout(resolve, 300));
        await axios.delete(`/api/streams/${streamId}`);
        this.lastDeletedStreamId = streamId;
        this.filteredStreams = this.filteredStreams.filter(s => s.id !== streamId);
        this.$emit('stream-deleted', streamId);
        this.showToast({
          type: 'success',
          title: 'Stream Deleted',
          message: `${streamName} has been successfully removed.`,
          duration: 5000
        });
      } catch (error) {
        console.error('Error deleting stream:', error);
        this.showToast({
          type: 'error',
          title: 'Deletion Failed',
          message: 'Could not delete the stream. Please try again.',
          duration: 5000
        });
      } finally {
        anime({
          targets: '.modal-container',
          opacity: [1, 0],
          scale: [1, 0.9],
          easing: 'easeInQuint',
          duration: 200,
          complete: () => {
            this.showDeleteModal = false;
            this.streamToDelete = null;
          }
        });
      }
    },
    showToast(options) {
      const toast = {
        id: Date.now(),
        type: options.type || 'info',
        title: options.title || '',
        message: options.message || '',
        duration: options.duration || 3000
      };
      this.toasts.push(toast);
      this.$nextTick(() => {
        const toastIndex = this.toasts.length - 1;
        const toastEl = this.$refs[`toast_${toastIndex}`]?.[0];
        if (toastEl) {
          anime({
            targets: toastEl,
            translateX: [100, 0],
            opacity: [0, 1],
            easing: 'easeOutBack',
            duration: 600
          });
          setTimeout(() => {
            this.removeToast(toastIndex);
          }, toast.duration);
        }
      });
    },
    removeToast(index) {
      const toastEl = this.$refs[`toast_${index}`]?.[0];
      if (toastEl) {
        anime({
          targets: toastEl,
          translateX: [0, 100],
          opacity: [1, 0],
          easing: 'easeInBack',
          duration: 400,
          complete: () => {
            this.toasts.splice(index, 1);
          }
        });
      }
    },
    getToastIcon(type) {
      switch(type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
      }
    },
    openEditorModal(stream = null) {
      this.streamToEdit = stream;
      this.showEditorModal = true;
      this.$nextTick(() => {
        anime({
          targets: '.modal-container',
          opacity: [0, 1],
          scale: [0.9, 1],
          easing: 'easeOutQuint',
          duration: 300
        });
      });
    },
    closeEditorModal() {
      anime({
        targets: '.modal-container',
        opacity: [1, 0],
        scale: [1, 0.9],
        easing: 'easeInQuint',
        duration: 200,
        complete: () => {
          this.showEditorModal = false;
          this.streamToEdit = null;
        }
      });
    },
    handleStreamCreated(streamData) {
      this.$emit('stream-created', streamData);
      this.showToast({
        type: 'success',
        title: 'Stream Created',
        message: `${streamData.streamer_username} has been successfully added.`,
        duration: 5000
      });
      this.$nextTick(() => {
        const newRowEl = this.$refs[`streamRow_${streamData.id}`]?.[0];
        const newCardEl = this.$refs[`streamCard_${streamData.id}`]?.[0];
        if (newRowEl) {
          anime({
            targets: newRowEl,
            translateY: [-20, 0],
            opacity: [0, 1],
            backgroundColor: ['rgba(var(--primary-rgb), 0.1)', 'transparent'],
            easing: 'easeOutQuad',
            duration: 800
          });
        }
        if (newCardEl) {
          anime({
            targets: newCardEl,
            translateY: [-20, 0],
            opacity: [0, 1],
            backgroundColor: ['rgba(var(--primary-rgb), 0.1)', 'transparent'],
            easing: 'easeOutQuad',
            duration: 800
          });
        }
      });
    },
    handleStreamUpdated(updatedStream) {
      this.$emit('stream-updated', updatedStream);
      const index = this.filteredStreams.findIndex(s => s.id === updatedStream.id);
      if (index !== -1) {
        this.filteredStreams.splice(index, 1, updatedStream);
      }
      this.showToast({
        type: 'success',
        title: 'Stream Updated',
        message: `${updatedStream.streamer_username} has been successfully updated.`,
        duration: 5000
      });
      this.$nextTick(() => {
        const updatedRowEl = this.$refs[`streamRow_${updatedStream.id}`]?.[0];
        const updatedCardEl = this.$refs[`streamCard_${updatedStream.id}`]?.[0];
        if (updatedRowEl) {
          anime({
            targets: updatedRowEl,
            backgroundColor: ['rgba(var(--primary-rgb), 0.15)', 'transparent'],
            easing: 'easeOutQuad',
            duration: 1200
          });
        }
        if (updatedCardEl) {
          anime({
            targets: updatedCardEl,
            backgroundColor: ['rgba(var(--primary-rgb), 0.15)', 'transparent'],
            easing: 'easeOutQuad',
            duration: 1200
          });
        }
      });
    },
    async handleRefresh(stream) {
      if (!stream.id) return;

      const rowEl = this.$refs[`streamRow_${stream.id}`]?.[0];
      const cardEl = this.$refs[`streamCard_${stream.id}`]?.[0];

      const animateRefresh = (element) => {
        if (!element) return;
        const btn = element.querySelector('.icon-button.refresh');
        if (btn) {
          anime({
            targets: btn,
            rotate: '360deg',
            easing: 'linear',
            duration: 800,
            loop: true
          });
        }
      };

      animateRefresh(rowEl);
      animateRefresh(cardEl);

      try {
        let response;
        if (stream.platform === 'Chaturbate') {
          response = await axios.post('/api/streams/refresh/chaturbate', {
            room_slug: stream.streamer_username
          });
        } else if (stream.platform === 'Stripchat') {
          response = await axios.post('/api/streams/refresh/stripchat', {
            room_url: stream.room_url
          });
        }

        if (response?.data) {
          this.$emit('refresh');
          this.showToast({
            type: 'success',
            title: 'Stream Refreshed',
            message: `${stream.streamer_username} has been refreshed successfully.`,
            duration: 3000
          });
          this.$nextTick(() => {
            if (rowEl) {
              anime({
                targets: rowEl,
                backgroundColor: ['rgba(33, 150, 243, 0.15)', 'transparent'],
                easing: 'easeOutQuad',
                duration: 1200
              });
            }
            if (cardEl) {
              anime({
                targets: cardEl,
                backgroundColor: ['rgba(33, 150, 243, 0.15)', 'transparent'],
                easing: 'easeOutQuad',
                duration: 1200
              });
            }
          });
        }
      } catch (error) {
        console.error('Error refreshing stream:', error);
        this.showToast({
          type: 'error',
          title: 'Refresh Failed',
          message: `Could not refresh ${stream.streamer_username}. Please try again.`,
          duration: 5000
        });
      } finally {
        const stopAnimation = (element) => {
          if (!element) return;
          const btn = element.querySelector('.icon-button.refresh');
          if (btn) {
            anime.remove(btn);
            btn.style.transform = '';
          }
        };
        stopAnimation(rowEl);
        stopAnimation(cardEl);
      }
    }
  }
}
</script>

<style scoped>
.streams-tab {
  margin: 0 auto;
  box-sizing: border-box;
  animation: fadeIn 0.4s ease;
  position: relative;
  padding-top: 1.5rem;
  width: auto;
  
  
}

.tab-header {
  margin-bottom: 2rem;
}

.tab-header h2 {
  font-size: 1.75rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
}

.controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #6c757d);
  opacity: 0.6;
}

.search-box input {
  width: 100%;
  padding: 10px 15px 10px 35px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.create-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.create-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Table Scrollable Container */
.streams-table-wrapper {
  height: calc(100vh - 250px);
  min-height: 400px;
  max-height: 800px;
  overflow: hidden;
  position: relative;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
}

.streams-table {
  height: 100%;
  background-color: var(--input-bg);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

.table-responsive {
  height: 100%;
  overflow-y: auto;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--primary-rgb), 0.3) transparent;
}

.table-responsive::-webkit-scrollbar {
  width: 8px;
}

.table-responsive::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 10px;
}

.table-responsive::-webkit-scrollbar-thumb {
  background-color: rgba(var(--primary-rgb), 0.3);
  border-radius: 10px;
  border: 2px solid transparent;
}

.table-responsive::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--primary-rgb), 0.5);
}


table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: var(--text-color);
}

thead th {
  position: sticky;
  top: 0;
  background-color: var(--input-bg);
  padding: 1.2rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  z-index: 10;
}

tbody tr {
  transition: background-color 0.2s ease;
}

tbody tr:hover {
  background-color: rgba(var(--primary-rgb), 0.04);
}

tbody td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
}

.text-center {
  text-align: center;
}

.streamer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.streamer-name {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
}

.streamer-url {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.platform-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.platform-tag.chaturbate {
  background-color: rgba(255, 120, 51, 0.1);
  color: #ff7833;
}

.platform-tag.stripchat {
  background-color: rgba(133, 94, 251, 0.1);
  color: #855efb;
}

.agent-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.agent-avatar {
  width: 32px;
  height: 32px;
  background-color: var(--secondary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.agent-name {
  font-weight: 500;
  color: var(--text-color);
  margin-left: 5px;
}

.unassigned-label {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.active {
  background-color: rgba(40, 199, 111, 0.1);
  color: #28c76f;
}

.status-badge.inactive {
  background-color: rgba(234, 84, 85, 0.1);
  color: #ea5455;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.icon-button {
  width: 34px;
  height: 34px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  cursor: pointer;
  background-color: transparent;
  border: none;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.icon-button:hover {
  background-color: rgba(var(--primary-rgb), 0.1);
  color: var(--primary-color);
}

.icon-button.view:hover {
  background-color: rgba(var(--info-rgb), 0.1);
  color: var(--info-color);
}

.icon-button.refresh:hover {
  background-color: rgba(var(--success-rgb), 0.1);
  color: var(--success-color);
}

.icon-button.danger:hover {
  background-color: rgba(var(--danger-rgb), 0.1);
  color: var(--danger-color);
}

.empty-state {
  height: 300px;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.4;
}

/* Mobile Card View */
.mobile-cards {
  display: none;
  flex-direction: column;
  gap: 16px;
  padding: 16px 0;
}

.stream-card {
  background-color: var(--input-bg);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
  border: 1px solid var(--border-color);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stream-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-details {
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.detail-label {
  font-weight: 500;
  color: var(--text-secondary);
  width: 80px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
  margin-top: 10px;
}

.empty-state-mobile {
  padding: 3rem 0;
  text-align: center;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  max-width: 90vw;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background-color: white;
  overflow: hidden;
  position: relative;
  animation: slideInRight 0.3s ease;
}

.toast.success {
  border-left: 4px solid var(--success-color);
}

.toast.error {
  border-left: 4px solid var(--danger-color);
}

.toast.warning {
  border-left: 4px solid var(--warning-color);
}

.toast.info {
  border-left: 4px solid var(--info-color);
}

.toast-icon {
  flex-shrink: 0;
  margin-right: 12px;
  font-size: 1.2rem;
}

.toast.success .toast-icon {
  color: var(--success-color);
}

.toast.error .toast-icon {
  color: var(--danger-color);
}

.toast.warning .toast-icon {
  color: var(--warning-color);
}

.toast.info .toast-icon {
  color: var(--info-color);
}

.toast-content {
  flex: 1;
  padding-right: 15px;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.toast-message {
  font-size: 0.9rem;
  opacity: 0.85;
}

.toast-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  padding: 0;
}

.toast-close:hover {
  opacity: 1;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Media Queries for Responsive Design */
@media (max-width: 992px) {
  .streams-table-wrapper {
    height: auto;
    max-height: none;
  }
}

@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: none;
  }
  
  .create-button {
    width: 100%;
    justify-content: center;
  }
  
  /* Hide table on mobile */
  .streams-table-wrapper {
    display: none;
  }
  
  /* Show card view on mobile */
  .mobile-cards {
    display: flex;
  }
}

/* Dark Mode Adjustments */
@media (prefers-color-scheme: dark) {
  .streams-tab {
    color: var(--text-color);
  }
  
  .streams-table {
    background-color: var(--input-bg);
  }
  
  .tab-header h2 {
    color: var(--text-color);
  }
  
  /* Table styling */
  thead th {
    background-color: var(--input-bg);
    border-bottom-color: var(--border-color);
  }
  
  tbody tr:hover {
    background-color: rgba(var(--primary-rgb), 0.08);
  }
  
  tbody td {
    border-bottom-color: var(--border-color);
  }
  
  /* Stream cards */
  .stream-card {
    background-color: var(--input-bg);
    border-color: var(--border-color);
  }
  
  /* Toast styling for dark mode */
  .toast {
    background-color: var(--input-bg);
    color: var(--text-color);
  }
  
  /* Search box and inputs */
  .search-box input {
    background-color: var(--input-bg);
    color: var(--text-color);
    border-color: var(--input-border);
  }
  
  .search-box input:focus {
    box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.25);
  }
  
  /* Status badges with improved contrast */
  .status-badge.active {
    background-color: rgba(40, 199, 111, 0.15);
    color: #3dd685;
  }
  
  .status-badge.inactive {
    background-color: rgba(234, 84, 85, 0.15);
    color: #ff6b6b;
  }
  
  /* Platform tags with improved contrast */
  .platform-tag.chaturbate {
    background-color: rgba(255, 120, 51, 0.15);
    color: #ff8c48;
  }
  
  .platform-tag.stripchat {
    background-color: rgba(133, 94, 251, 0.15);
    color: #9d7cff;
  }
  
  /* Buttons hover states */
  .icon-button:hover {
    background-color: rgba(var(--primary-rgb), 0.15);
  }
  
  .icon-button.view:hover {
    background-color: rgba(var(--info-rgb), 0.15);
  }
  
  .icon-button.refresh:hover {
    background-color: rgba(var(--success-rgb), 0.15);
  }
  
  .icon-button.danger:hover {
    background-color: rgba(var(--danger-rgb), 0.15);
  }
  
  /* Empty state */
  .empty-content {
    color: var(--text-muted);
  }
}

</style>