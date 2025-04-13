<template>
  <div class="stream-card" @click="$emit('click', $event)">
    <div class="stream-thumbnail">
      <VideoPlayer
        :platform="stream.platform.toLowerCase()"
        :streamer-uid="stream.streamer_uid"
        :streamer-name="stream.streamer_username"
        :alerts="[]"
        thumbnail-only
      />
      <DetectionBadge v-if="detectionCount > 0" :count="detectionCount" />
    </div>
    <div class="stream-info">
      <h3 class="stream-title">{{ stream.streamer_username }}</h3>
      <div class="stream-meta">
        <span class="platform-tag" :class="stream.platform.toLowerCase()">
          {{ stream.platform }}
        </span>
        <span class="agent-name">
          {{ stream.agent?.username || 'Unassigned' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import VideoPlayer from './VideoPlayer.vue'
import DetectionBadge from './DetectionBadge.vue'

export default {
  name: 'StreamCard',
  components: {
    VideoPlayer,
    DetectionBadge
  },
  props: {
    stream: Object,
    detectionCount: Number
  },
  emits: ['click']
}
</script>

<style scoped>
.stream-card {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid var(--input-border);
  cursor: pointer;
}

.stream-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  border-color: var(--primary-color);
}

.stream-thumbnail {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;
}

.stream-thumbnail::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.5));
  z-index: 1;
}

.stream-info {
  padding: 15px;
}

.stream-title {
  margin: 0 0 5px 0;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stream-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.8;
}

.platform-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.agent-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 50%;
}
</style>