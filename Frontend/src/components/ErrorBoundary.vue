<template>
  <div>
    <div v-if="hasError" class="error-container">
      <h3>Something went wrong.</h3>
      <p>Please try refreshing the page.</p>
      <button @click="refreshPage">Refresh</button>
    </div>
    <slot v-else></slot>
  </div>
</template>

<script>
import { ref, defineComponent } from 'vue';

export default defineComponent({
  name: 'ErrorBoundary',
  setup() {
    const hasError = ref(false);
    const errorDetails = ref(null);

    const refreshPage = () => {
      window.location.reload();
    };

    // In Vue 3, we use an error handler at the app level
    // This is a simplified version for component-level errors
    const handleError = (error) => {
      console.error("ErrorBoundary caught error:", error);
      hasError.value = true;
      errorDetails.value = error;
    };

    return {
      hasError,
      errorDetails,
      refreshPage,
      handleError
    };
  },
  errorCaptured(err, instance, info) {
    // This lifecycle hook captures errors from descendant components
    console.error("ErrorBoundary captured error:", err, instance, info);
    this.hasError = true;
    this.errorDetails = { err, info };
    // Return false to prevent the error from propagating further
    return false;
  }
});
</script>

<style scoped>
.error-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #e0e0e0;
  background: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  margin-top: 10px;
  cursor: pointer;
}
</style>