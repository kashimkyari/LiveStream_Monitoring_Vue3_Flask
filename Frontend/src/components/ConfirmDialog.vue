<template>
  <div class="confirm-overlay">
    <div class="confirm-dialog">
      <p class="confirm-message">{{ message }}</p>
      <div class="confirm-actions">
        <button class="confirm-button" @click="$emit('confirm')">Yes</button>
        <button class="cancel-button" @click="$emit('cancel')">No</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    message: {
      type: String,
      required: true
    }
  },
  emits: ['confirm', 'cancel']
};
</script>