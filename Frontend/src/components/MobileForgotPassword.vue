<template>
  <div class="mobile-forgot-password-container">
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
        <!-- Step 1: Email Entry -->
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
              Send Reset Link
            </template>
          </button>
        </div>
        
        <!-- Step 2: Reset Password with Token -->
        <div v-if="currentStep === 2">
          <div class="input-group" ref="tokenGroup">
            <div class="input-container">
              <font-awesome-icon icon="fingerprint" class="input-icon" />
              <input
                type="text"
                id="token"
                v-model="token"
                :disabled="loading"
                class="input-field"
                placeholder="Reset Token"
                required
                ref="tokenInput"
              />
            </div>
            <p class="input-hint">Enter the token from the email we sent you</p>
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
            <button type="button" class="secondary-button" @click="currentStep = 1" :disabled="loading">
              <font-awesome-icon icon="arrow-left" class="mr-2" />
              Back
            </button>
            
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
        
        <!-- Success State -->
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
import "vue-toastification/dist/index.css"
import { requestPasswordReset, verifyResetToken, resetPassword } from '@/services/api'

export default {
  name: 'MobileForgotPasswordComponent',
  components: { FontAwesomeIcon },
  emits: ['back'],
  setup() {
    const toast = useToast()
    return { toast }
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
      tokenVerified: false
    }
  },
  computed: {
    passwordStrength() {
      // Simple password strength calculation
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
        this.newPassword.length >= 8 &&
        this.confirmPassword.length >= 8 &&
        this.newPassword === this.confirmPassword &&
        this.passwordStrength >= 3 // Require at least Strong password
      );
    }
  },
  mounted() {
    // Check if token is provided in URL (for direct access from email)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    
    if (tokenFromUrl) {
      this.token = tokenFromUrl;
      this.currentStep = 2;
      this.verifyToken();
    }
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
          this.toast.success("Reset link sent to your email. Please check your inbox.", {
            position: "top-center"
          });
          this.currentStep = 2;
          
          // Focus on token input field
          setTimeout(() => {
            if (this.$refs.tokenInput) {
              this.$refs.tokenInput.focus();
            }
          }, 500);
        } else {
          this.toast.error(response.data.message || "Failed to send reset link", {
            position: "top-center"
          });
        }
      } catch (error) {
        console.error('Request reset link error:', error);
        this.toast.error(
          error.response?.data?.message || 
          "An error occurred while sending the reset link", 
          { position: "top-center" }
        );
      } finally {
        this.loading = false;
      }
    },
    
    async verifyToken() {
      if (!this.token) return;
      
      this.loading = true;
      
      try {
        const response = await verifyResetToken(this.token);
        
        if (response.status === 200 && response.data.valid) {
          this.tokenVerified = true;
          if (this.$refs.passwordInput) {
            this.$refs.passwordInput.focus();
          }
        } else {
          this.toast.error("Invalid or expired reset token. Please request a new reset link.", {
            position: "top-center"
          });
          this.token = '';
          this.currentStep = 1;
        }
      } catch (error) {
        console.error('Verify token error:', error);
        this.toast.error(
          error.response?.data?.message || 
          "Invalid or expired reset token", 
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
      
      // Verify token first if not already verified
      if (!this.tokenVerified) {
        try {
          this.loading = true;
          const verifyResponse = await verifyResetToken(this.token);
          
          if (!verifyResponse.data.valid) {
            this.toast.error("Invalid or expired reset token. Please request a new reset link.", {
              position: "top-center"
            });
            this.loading = false;
            return;
          }
          
          this.tokenVerified = true;
        } catch (error) {
          console.error('Token verification error:', error);
          this.toast.error(
            error.response?.data?.message || 
            "Invalid or expired reset token", 
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
.mobile-forgot-password-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 1rem;
  background-color: var(--bs-dark);
}

.mobile-forgot-form {
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  background: var(--bs-gray-800);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  position: relative;
}

.back-button {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: transparent;
  border: none;
  color: var(--bs-gray-400);
  cursor: pointer;
  transition: color 0.2s ease;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.back-button:hover {
  color: var(--bs-info);
}

.logo-container {
  text-align: center;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 2rem;
  color: var(--bs-info);
  padding: 1rem;
  border-radius: 50%;
  background: rgba(13, 202, 240, 0.1);
}

.title-text {
  color: white;
  font-size: 1.5rem;
  text-align: center;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.subtitle {
  color: var(--bs-gray-400);
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.form-content {
  margin-top: 1rem;
}

.input-group {
  margin-bottom: 1rem;
}

.input-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--bs-gray-500);
  font-size: 0.9rem;
}

.input-field {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid var(--bs-gray-700);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  background: var(--bs-gray-900);
}

.input-field:focus {
  border-color: var(--bs-info);
  outline: none;
}

.input-hint {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--bs-gray-500);
}

.input-hint.error {
  color: var(--bs-danger);
}

.action-button {
  width: 100%;
  padding: 0.8rem;
  background: var(--bs-info);
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
}

.action-button:disabled {
  opacity: 0.7;
}

.secondary-button {
  width: 45%;
  padding: 0.8rem;
  background: var(--bs-gray-700);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.button-group {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 1rem;
}

.password-strength {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
}

.pw-very-weak, .pw-weak {
  color: var(--bs-danger);
}

.pw-medium {
  color: var(--bs-warning);
}

.pw-strong {
  color: var(--bs-success);
}

.pw-very-strong {
  color: var(--bs-success);
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
  font-size: 3rem;
  color: var(--bs-success);
  margin-bottom: 1rem;
}

.success-title {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.success-message {
  color: var(--bs-gray-400);
  margin-bottom: 1.5rem;
}

@media (max-width: 480px) {
  .mobile-forgot-password-container {
    padding: 0.5rem;
  }
  
  .mobile-forgot-form {
    padding: 1.25rem;
  }
}
</style>