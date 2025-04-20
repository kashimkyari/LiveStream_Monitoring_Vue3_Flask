<template>
  <div class="notification-badge">{{ displayCount }}</div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'MobileNotificationBadge',
  props: {
    count: {
      type: Number,
      required: true
    },
    maxDisplay: {
      type: Number,
      default: 99
    }
  },
  setup(props) {
    // Format the count as "99+" if it exceeds the maxDisplay
    const displayCount = computed(() => {
      return props.count > props.maxDisplay 
        ? `${props.maxDisplay}+` 
        : props.count;
    });
    
    return {
      displayCount
    };
  }
};
</script>

<style scoped>
/* Badge styling is in App.vue to ensure consistent styling across the app */
</style>