<template>
  <div class="stat-card">
    <div class="stat-icon">
      <font-awesome-icon :icon="icon" />
    </div>
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script>
export default {
  name: 'StatCard',
  props: {
    value: [Number, String],
    label: String,
    icon: String
  }
}
</script>

<style scoped>
.stat-card {
  background-color: var(--input-bg);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 2rem;
  color: var(--primary-color);
  opacity: 0.2;
  position: absolute;
  top: 10px;
  right: 10px;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.8;
}
</style>