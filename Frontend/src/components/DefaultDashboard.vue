<template>
  <div>
    <slot v-if="!hasError"></slot>
    <div v-else class="error-container">
      <h3>Something went wrong.</h3>
      <p>Please try refreshing the page.</p>
      <button @click="refreshPage">Refresh</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ErrorBoundary',
  data() {
    return {
      hasError: false,
      error: null,
      errorInfo: null
    };
  },
  // errorCaptured hook will catch errors in descendant components.
  errorCaptured(err, vm, info) {
    console.error("ErrorBoundary caught an error:", err, info);
    this.hasError = true;
    this.error = err;
    this.errorInfo = info;
    // Returning false prevents the error from propagating further.
    return false;
  },
  methods: {
    refreshPage() {
      window.location.reload();
    }
  }
};
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
