<template>
  <div class="alert-badge">
    {{ count }}
  </div>
</template>

<script>
export default {
  name: 'DetectionBadge',
  props: {
    count: Number
  }
}
</script>

<style scoped>
.alert-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: #dc3545;
  color: white;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  z-index: 2;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>