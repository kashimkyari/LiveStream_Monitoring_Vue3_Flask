<template>
  <div class="mobile-forgot-password-container" :data-theme="theme">
    <button 
      class="theme-toggle" 
      @click="toggleTheme" 
      :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      role="switch"
      :aria-checked="theme === 'dark'"
    >
      <font-awesome-icon :icon="theme === 'dark' ? 'sun' : 'moon'" />
    </button>
    
    <form @submit.prevent="handleSubmit" class="mobile-forgot-form" ref="forgotForm">
      <div class="back-button" @click="$emit('back')" ref="backButton">
        <font-awesome-icon icon="arrow-left" />
      </div>
      
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="key" class="logo-icon" />
      </div>
      <h2 class="title-text" ref="titleText">Password Recovery</h2>
      <p class="subtitle" ref="subtitle">Recover your account access</p>
      
      <div class="form-content" ref="formContent">
        <div v-if="currentStep === 1">
          <div class="input-group" ref="emailGroup">
            <div class="input-container">
              <font-awesome-icon icon="envelope" class="input-icon" />
              <input
                type="email"
                id="email"
                v-model="email"
                :disabled="loading"
                class="input-field"
                autocomplete="email"
                placeholder="Email Address"
                required
                ref="emailInput"
              />
            </div>
            <p class="input-hint">Enter your registered email address</p>
          </div>
          
          <button type="button" class="action-button" :disabled="loading || !email" @click="requestPasswordReset" ref="requestButton">
            <template v-if="loading">
              <font-awesome-icon icon="spinner" spin class="mr-2" />
              Sending...
            </template>
            <template v-else>
              <font-awesome-icon icon="paper-plane" class="mr-2" />
              Send Reset Code
            </template>
          </button>
        </div>
        
        <div v-if="currentStep === 2">
          <div class="input-group" ref="tokenGroup">
            <div class="input-container">
              <font-awesome-icon icon="fingerprint" class="input-icon" />
              <input
                type="text"
                inputmode="numeric"
                pattern="[0-9]{6}"
                id="token"
                v-model="token"
                :disabled="loading"
                class="input-field"
                placeholder="Reset Code"
                required
                ref="tokenInput"
                aria-describedby="token-hint"
              />
            </div>
            <p id="token-hint" class="input-hint error" v-if="tokenError">
              Token must be a 6-digit number
            </p>
            <p id="token-hint" class="input-hint" v-else>
              Enter the 6-digit code from the email
            </p>
          </div>
          
          <div class="input-group" ref="passwordGroup">
            <div class="input-container">
              <font-awesome-icon icon="lock" class="input-icon" />
              <input
                type="password"
                id="newPassword"
                v-model="newPassword"
                :disabled="loading"
                class="input-field"
                placeholder="New Password"
                required
                ref="passwordInput"
              />
            </div>
            <p class="password-strength" :class="passwordStrengthClass">
              <font-awesome-icon :icon="passwordStrengthIcon" class="mr-1" />
              {{ passwordStrengthText }}
            </p>
          </div>
          
          <div class="input-group" ref="confirmGroup">
            <div class="input-container">
              <font-awesome-icon icon="check-double" class="input-icon" />
              <input
                type="password"
                id="confirmPassword"
                v-model="confirmPassword"
                :disabled="loading"
                class="input-field"
                placeholder="Confirm Password"
                required
                ref="confirmInput"
              />
            </div>
            <p class="input-hint error" v-if="passwordMismatch">
              <font-awesome-icon icon="exclamation-circle" class="mr-1" />
              Passwords don't match
            </p>
          </div>
          
          <div class="button-group">
            <button type="submit" class="action-button" :disabled="loading || !canResetPassword">
              <template v-if="loading">
                <font-awesome-icon icon="spinner" spin class="mr-2" />
                Resetting...
              </template>
              <template v-else>
                <font-awesome-icon icon="key" class="mr-2" />
                Reset Password
              </template>
            </button>
          </div>
        </div>
        
        <div v-if="resetCompleted" class="success-container" ref="successContainer">
          <div class="success-icon">
            <font-awesome-icon icon="check-circle" />
          </div>
          <h3 class="success-title">Password Reset Successfully</h3>
          <p class="success-message">You can now log in with your new password</p>
          <button type="button" class="action-button" @click="$emit('back')">
            <font-awesome-icon icon="sign-in-alt" class="mr-2" />
            Return to Login
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification'
import { ref, onMounted } from 'vue'
import "vue-toastification/dist/index.css"
import { requestPasswordReset, verifyResetToken, resetPassword } from '@/services/api'

export default {
  name: 'MobileForgotPasswordComponent',
  components: { FontAwesomeIcon },
  emits: ['back'],
  setup() {
    const toast = useToast()
    const theme = ref('light')
    
    onMounted(() => {
      const savedTheme = localStorage.getItem('preferred-theme')
      if (savedTheme) {
        theme.value = savedTheme
        return
      }
      
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        theme.value = 'dark'
      }
      
      localStorage.setItem('preferred-theme', theme.value)
    })
    
    const toggleTheme = () => {
      theme.value = theme.value === 'dark' ? 'light' : 'dark'
      localStorage.setItem('preferred-theme', theme.value)
    }
    
    return { toast, theme, toggleTheme }
  },
  data() {
    return {
      currentStep: 1,
      email: '',
      token: '',
      newPassword: '',
      confirmPassword: '',
      loading: false,
      resetCompleted: false,
      tokenVerified: false,
      tokenError: false
    }
  },
  computed: {
    passwordStrength() {
      let strength = 0;
      const password = this.newPassword;
      
      if (password.length >= 8) strength += 1;
      if (password.match(/[A-Z]/)) strength += 1;
      if (password.match(/[0-9]/)) strength += 1;
      if (password.match(/[^A-Za-z0-9]/)) strength += 1;
      
      return strength;
    },
    passwordStrengthText() {
      const strength = this.passwordStrength;
      if (strength === 0) return 'Too weak';
      if (strength === 1) return 'Weak';
      if (strength === 2) return 'Medium';
      if (strength === 3) return 'Strong';
      if (strength === 4) return 'Very strong';
      return '';
    },
    passwordStrengthClass() {
      const strength = this.passwordStrength;
      if (strength === 0) return 'pw-very-weak';
      if (strength === 1) return 'pw-weak';
      if (strength === 2) return 'pw-medium';
      if (strength === 3) return 'pw-strong';
      if (strength === 4) return 'pw-very-strong';
      return '';
    },
    passwordStrengthIcon() {
      const strength = this.passwordStrength;
      if (strength <= 1) return 'times-circle';
      if (strength === 2) return 'exclamation-circle';
      return 'check-circle';
    },
    passwordMismatch() {
      return this.confirmPassword && this.newPassword !== this.confirmPassword;
    },
    canResetPassword() {
      return (
        this.token &&
        /^\d{6}$/.test(this.token) &&
        this.newPassword.length >= 8 &&
        this.confirmPassword.length >= 8 &&
        this.newPassword === this.confirmPassword &&
        this.passwordStrength >= 3
      );
    }
  },
  mounted() {
    // No token extraction from URL
  },
  methods: {
    async requestPasswordReset() {
      if (this.loading) return;
      
      if (!this.email.trim() || !this.email.includes('@') || !this.email.includes('.')) {
        this.toast.error("Please enter a valid email address", {
          position: "top-center"
        });
        return;
      }
      
      this.loading = true;
      
      try {
        const response = await requestPasswordReset(this.email);
        
        if (response.status === 200) {
          this.toast.success("Reset code sent to your email. Please check your inbox.", {
            position: "top-center"
          });
          this.currentStep = 2;
          
          setTimeout(() => {
            if (this.$refs.tokenInput) {
              this.$refs.tokenInput.focus();
            }
          }, 500);
        } else {
          this.toast.error(response.data.message || "Failed to send reset code", {
            position: "top-center"
          });
        }
      } catch (error) {
        console.error('Request reset code error:', error);
        this.toast.error(
          error.response?.data?.message || 
          "An error occurred while sending the reset code", 
          { position: "top-center" }
        );
      } finally {
        this.loading = false;
      }
    },
    async verifyToken() {
      if (!this.token) return;
      
      if (!/^\d{6}$/.test(this.token)) {
        this.tokenError = true;
        this.toast.error("Token must be a 6-digit number", {
          position: "top-center"
        });
        return;
      }
      
      this.tokenError = false;
      this.loading = true;
      
      try {
        const response = await verifyResetToken(this.token);
        
        if (response.status === 200 && response.data.valid) {
          this.tokenVerified = true;
          if (this.$refs.passwordInput) {
            this.$refs.passwordInput.focus();
          }
        } else {
          this.tokenError = true;
          this.toast.error("Invalid or expired reset code. Please request a new code.", {
            position: "top-center"
          });
          this.token = '';
          this.currentStep = 1;
        }
      } catch (error) {
        console.error('Verify token error:', error);
        this.tokenError = true;
        this.toast.error(
          error.response?.data?.message || 
          "Invalid or expired reset code", 
          { position: "top-center" }
        );
        this.token = '';
        this.currentStep = 1;
      } finally {
        this.loading = false;
      }
    },
    async handleSubmit() {
      if (this.loading || !this.canResetPassword) return;
      
      if (!this.tokenVerified) {
        if (!/^\d{6}$/.test(this.token)) {
          this.tokenError = true;
          this.toast.error("Token must be a 6-digit number", {
            position: "top-center"
          });
          return;
        }
        
        try {
          this.loading = true;
          const verifyResponse = await verifyResetToken(this.token);
          
          if (!verifyResponse.data.valid) {
            this.tokenError = true;
            this.toast.error("Invalid or expired reset code. Please request a new code.", {
              position: "top-center"
            });
            this.loading = false;
            return;
          }
          
          this.tokenVerified = true;
        } catch (error) {
          console.error('Token verification error:', error);
          this.tokenError = true;
          this.toast.error(
            error.response?.data?.message || 
            "Invalid or expired reset code", 
            { position: "top-center" }
          );
          this.loading = false;
          return;
        }
      }
      
      this.loading = true;
      
      try {
        const response = await resetPassword(this.token, this.newPassword);
        
        if (response.status === 200) {
          this.resetCompleted = true;
          this.toast.success("Password reset successfully", {
            position: "top-center"
          });
        } else {
          this.toast.error(
            response.data.message || 
            "Failed to reset password", 
            { position: "top-center" }
          );
        }
      } catch (error) {
        console.error('Reset password error:', error);
        this.toast.error(
          error.response?.data?.message || 
          "An error occurred while resetting the password", 
          { position: "top-center" }
        );
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
:root {
  --color-background: #f8f9fa;
  --color-form-bg: #ffffff;
  --color-primary: #0d6efd;
  --color-primary-hover: #0b5ed7;
  --color-secondary: #6c757d;
  --color-success: #198754;
  --color-danger: #dc3545;
  --color-warning: #ffc107;
  --color-info: #0dcaf0;
  --color-info-light: rgba(13, 202, 240, 0.1);
  --color-text: #212529;
  --color-text-muted: #6c757d;
  --color-text-light: #adb5bd;
  --color-border: #dee2e6;
  --color-border-dark: #ced4da;
  --color-input-bg: #f8f9fa;
  --color-input-border: #ced4da;
  --color-input-text: #212529;
  --color-input-placeholder: #6c757d;
  --color-input-icon: #6c757d;
  --shadow-sm: 0 .125rem .25rem rgba(0,0,0,.075);
  --shadow-md: 0 .5rem 1rem rgba(0,0,0,.15);
  --shadow-lg: 0 1rem 3rem rgba(0,0,0,.175);
  --color-focus-ring: rgba(13, 110, 253, 0.25);
}

[data-theme="dark"] {
  --color-background: #121212;
  --color-form-bg: #343a40;
  --color-primary: #0dcaf0;
  --color-primary-hover: #0bb8da;
  --color-secondary: #6c757d;
  --color-success: #20c997;
  --color-danger: #dc3545;
  --color-warning: #ffc107;
  --color-info: #0dcaf0; 
  --color-info-light: rgba(13, 202, 240, 0.1);
  --color-text: #f8f9fa;
  --color-text-muted: #adb5bd;
  --color-text-light: #ced4da;
  --color-border: #495057;
  --color-border-dark: #6c757d;
  --color-input-bg: #212529;
  --color-input-border: #495057;
  --color-input-text: #f8f9fa;
  --color-input-placeholder: #adb5bd;
  --color-input-icon: #adb5bd;
  --shadow-sm: 0 .125rem .25rem rgba(0,0,0,.2);
  --shadow-md: 0 .5rem 1rem rgba(0,0,0,.3);
  --shadow-lg: 0 1rem 3rem rgba(0,0,0,.4);
  --color-focus-ring: rgba(13, 202, 240, 0.4);
}

.mobile-forgot-password-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 1rem;
  background-color: var(--color-background);
  position: relative;
}

.theme-toggle {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  background-color: var(--color-form-bg);
  border: 1px solid var(--color-border);
  color: var(--color-primary);
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  z-index: 100;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  transform: scale(1.05);
}

.theme-toggle:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.theme-toggle:active {
  transform: translateY(1px);
}

.mobile-forgot-form {
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  background: var(--color-form-bg);
  border-radius: 1rem;
  box-shadow: var(--shadow-md);
  position: relative;
}

.back-button {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.2s ease;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
}

.back-button:hover,
.back-button:focus {
  color: var(--color-primary);
}

.back-button:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.logo-container {
  text-align: center;
  margin-top: 2rem;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 2.5rem;
  color: var(--color-primary);
  padding: 1.25rem;
  border-radius: 50%;
  background: var(--color-info-light);
}

.title-text {
  color: var(--color-text);
  font-size: 1.75rem;
  text-align: center;
  margin: 0 0 0.75rem 0;
  font-weight: 600;
}

.subtitle {
  color: var(--color-text-muted);
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 1rem;
}

.form-content {
  margin-top: 1.5rem;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-container {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-input-icon);
  font-size: 1rem;
}

.input-field {
  width: 100%;
  height: 3rem;
  padding: 0.8rem 0.8rem 0.8rem 3rem;
  border: 1px solid var(--color-input-border);
  border-radius: 0.5rem;
  color: var(--color-input-text);
  font-size: 1rem;
  background: var(--color-input-bg);
}

.input-field::placeholder {
  color: var(--color-input-placeholder);
}

.input-field:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.input-hint {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.input-hint.error {
  color: var(--color-danger);
}

.action-button {
  width: 100%;
  min-height: 3rem;
  padding: 0.8rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.action-button:hover,
.action-button:focus {
  background: var(--color-primary-hover);
}

.action-button:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1.5rem;
}

.password-strength {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
}

.pw-very-weak, .pw-weak {
  color: var(--color-danger);
}

.pw-medium {
  color: var(--color-warning);
}

.pw-strong, .pw-very-strong {
  color: var(--color-success);
}

.success-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 1.5rem;
}

.success-icon {
  font-size: 3.5rem;
  color: var(--color-success);
  margin-bottom: 1.5rem;
}

.success-title {
  color: var(--color-text);
  font-size: 1.75rem;
  margin-bottom: 0.75rem;
}

.success-message {
  color: var(--color-text-muted);
  margin-bottom: 1.75rem;
  font-size: 1rem;
}

@media (max-width: 480px) {
  .mobile-forgot-password-container {
    padding: 0.75rem;
  }
  
  .mobile-forgot-form {
    padding: 1.25rem;
  }
  
  .button-group {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .action-button {
    width: 100%;
  }
}

@media (max-width: 320px) {
  .logo-icon {
    font-size: 2rem;
    padding: 1rem;
  }
  
  .title-text {
    font-size: 1.5rem;
  }
  
  .subtitle {
    font-size: 0.9rem;
  }
}

:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.mr-1 {
  margin-right: 0.25rem;
}

.mr-2 {
  margin-right: 0.5rem;
}
</style>