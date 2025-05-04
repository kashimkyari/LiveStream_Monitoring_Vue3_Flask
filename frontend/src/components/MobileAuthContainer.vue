<template>
  <div class="mobile-auth-container">
    <transition name="slide-fade" mode="out-in">
      <MobileLogin
        v-if="currentView === 'login'"
        @login-success="handleLoginSuccess"
        @goto-forgot-password="currentView = 'forgot-password'"
        @goto-register="currentView = 'register'"
        key="login"
      />
      <MobileCreateAccount
        v-else-if="currentView === 'register'"
        @back="currentView = 'login'"
        @account-created="handleAccountCreated"
        key="register"
      />
      <MobileForgotPassword
        v-else-if="currentView === 'forgot-password'"
        @back="currentView = 'login'"
        key="forgot-password"
      />
    </transition>
  </div>
</template>

<script>
import MobileLogin from './MobileLogin.vue';
import MobileCreateAccount from './MobileCreateAccount.vue';
import MobileForgotPassword from './MobileForgotPassword.vue';
import { useToast } from 'vue-toastification';

export default {
  name: 'MobileAuthContainer',
  components: {
    MobileLogin,
    MobileCreateAccount,
    MobileForgotPassword
  },
  data() {
    return {
      currentView: 'login',
      user: null
    };
  },
  setup() {
    const toast = useToast();
    return { toast };
  },
  methods: {
    handleLoginSuccess(user) {
      this.user = user;
      this.toast.success('Login successful! Redirecting...');
      // Handle successful login (redirect to dashboard, etc.)
    },
    handleAccountCreated(/* username */) {
      this.toast.success('Account created successfully!');
      this.currentView = 'login';
      // Optionally pre-fill the username field in login
      // This would require emitting an event to the login component
    }
  }
};
</script>

<style>
@import url('../styles/theme.css');

/* Retain component-specific styles while leveraging theme variables */
.mobile-auth-container {
  min-height: 100vh;
  width: 100%;
  background-color: var(--dark-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Animation styles */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* Shared form styling */
.input-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.input-container:focus-within {
  transform: scale(1.01);
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.input-field {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-color);
  font-size: 0.95rem;
  background: var(--input-bg);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.input-field:focus {
  border-color: var(--primary-color);
  outline: none;
  box-shadow: 0 0 0 3px rgba(13, 202, 240, 0.2);
}

.input-container:focus-within .input-icon {
  color: var(--primary-color);
}

.input-hint {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.action-button {
  width: 100%;
  padding: 0.8rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.action-button:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-2px);
}

.action-button:active:not(:disabled) {
  transform: translateY(0);
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-button {
  padding: 0.8rem;
  background: var(--border-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.secondary-button:hover:not(:disabled) {
  background: color-mix(in srgb, var(--border-color) 85%, white);
  transform: translateY(-2px);
}

.secondary-button:active:not(:disabled) {
  transform: translateY(0);
}

/* Add focus styles for accessibility */
button:focus, input:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.success-icon {
  animation: pulse 1.5s ease-in-out infinite;
}
</style>