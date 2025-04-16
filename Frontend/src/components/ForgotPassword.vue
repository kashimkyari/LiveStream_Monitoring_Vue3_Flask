<template>
  <div class="forgot-password-container">
    <form @submit.prevent="handleSubmit" class="forgot-password-form" ref="forgotForm">
      <div class="back-button" @click="$emit('back')" ref="backButton">
        <font-awesome-icon icon="arrow-left" />
      </div>
      
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="key" class="logo-icon" />
      </div>
      <h2 class="title-text" ref="titleText">Password Recovery</h2>
      <p class="subtitle" ref="subtitle">For agent accounts only</p>
      
      <div class="form-content" ref="formContent">
        <div class="step-indicator" v-if="!codeVerified" ref="stepIndicator">
          <div class="step" :class="{ active: currentStep === 1 }">1</div>
          <div class="step-line"></div>
          <div class="step" :class="{ active: currentStep === 2 }">2</div>
          <div class="step-line"></div>
          <div class="step" :class="{ active: currentStep === 3 }">3</div>
        </div>
        
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
                placeholder=" "
                required
                ref="emailInput"
              />
              <label for="email" class="input-label">Agency Email</label>
            </div>
            <p class="input-hint">Enter your registered agency email address</p>
          </div>
          
          <button type="button" class="action-button" :disabled="loading || !email" @click="requestCode" ref="requestButton">
            <template v-if="loading">
              <font-awesome-icon icon="spinner" spin class="mr-2" />
              Sending...
            </template>
            <template v-else>
              <font-awesome-icon icon="paper-plane" class="mr-2" />
              Send Verification Code
            </template>
          </button>
        </div>
        
        <!-- Step 2: Code Verification -->
        <div v-if="currentStep === 2">
          <div class="input-group" ref="codeGroup">
            <div class="code-container">
              <input
                v-for="(_, index) in 6"
                :key="index"
                :ref="el => { if(el) codeInputs[index] = el }"
                type="text"
                class="code-input"
                maxlength="1"
                pattern="[0-9]"
                inputmode="numeric"
                v-model="verificationCode[index]"
                @input="handleCodeInput(index)"
                @keydown="handleKeyDown($event, index)"
                @paste="handlePaste"
                :disabled="loading"
              />
            </div>
            <p class="input-hint">Enter the 6-digit code sent to {{ maskEmail(email) }}</p>
            <div class="resend-container">
              <span v-if="cooldown > 0">Resend code in {{ cooldown }}s</span>
              <a href="#" v-else class="resend-link" @click.prevent="requestCode">Resend code</a>
            </div>
          </div>
          
          <button type="button" class="action-button" :disabled="loading || !isCodeComplete" @click="verifyCode" ref="verifyButton">
            <template v-if="loading">
              <font-awesome-icon icon="spinner" spin class="mr-2" />
              Verifying...
            </template>
            <template v-else>
              <font-awesome-icon icon="check-circle" class="mr-2" />
              Verify Code
            </template>
          </button>
        </div>
        
        <!-- Step 3: New Password -->
        <div v-if="currentStep === 3">
          <div class="input-group" ref="passwordGroup">
            <div class="input-container">
              <font-awesome-icon icon="lock" class="input-icon" />
              <input
                type="password"
                id="newPassword"
                v-model="newPassword"
                :disabled="loading"
                class="input-field"
                placeholder=" "
                required
                ref="passwordInput"
              />
              <label for="newPassword" class="input-label">New Password</label>
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
                placeholder=" "
                required
                ref="confirmInput"
              />
              <label for="confirmPassword" class="input-label">Confirm Password</label>
            </div>
            <p class="input-hint" v-if="passwordMismatch" style="color: var(--error-color);">
              <font-awesome-icon icon="exclamation-circle" class="mr-1" />
              Passwords don't match
            </p>
          </div>
          
          <button type="submit" class="action-button" :disabled="loading || !canResetPassword" ref="resetButton">
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
        
        <!-- Success State -->
        <div v-if="codeVerified && resetCompleted" class="success-container" ref="successContainer">
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
      
      <div class="decorative-circles">
        <div class="circle circle-1" ref="circle1"></div>
        <div class="circle circle-2" ref="circle2"></div>
        <div class="circle circle-3" ref="circle3"></div>
      </div>
    </form>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification'
import "vue-toastification/dist/index.css"
import anime from 'animejs/lib/anime.es.js'
import api from '@/services/api'

export default {
  name: 'ForgotPasswordComponent',
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
      verificationCode: Array(6).fill(''),
      codeInputs: [],
      newPassword: '',
      confirmPassword: '',
      loading: false,
      cooldown: 0,
      cooldownInterval: null,
      codeVerified: false,
      resetCompleted: false,
      agentVerified: false
    }
  },
  computed: {
    isCodeComplete() {
      return this.verificationCode.every(digit => digit !== '');
    },
    fullVerificationCode() {
      return this.verificationCode.join('');
    },
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
        this.newPassword.length >= 8 &&
        this.confirmPassword.length >= 8 &&
        this.newPassword === this.confirmPassword &&
        this.passwordStrength >= 2
      );
    }
  },
  mounted() {
    this.initializeAnimations();
  },
  methods: {
    initializeAnimations() {
      // Initial animations when component mounts
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: this.$refs.forgotForm,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
      })
      .add({
        targets: this.$refs.backButton,
        opacity: [0, 1],
        translateX: [-10, 0],
        duration: 500,
      }, '-=600')
      .add({
        targets: this.$refs.logoContainer,
        scale: [0.5, 1],
        opacity: [0, 1],
        duration: 700,
      }, '-=500')
      .add({
        targets: [this.$refs.titleText, this.$refs.subtitle],
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(150),
        duration: 700,
      }, '-=500')
      .add({
        targets: this.$refs.formContent,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 700,
      }, '-=400')
      .add({
        targets: [this.$refs.circle1, this.$refs.circle2, this.$refs.circle3],
        scale: [0, 1],
        opacity: [0, 0.7],
        delay: anime.stagger(150),
        duration: 1000,
      }, '-=700');
      
      // Animate decorative circles continuously
      this.animateDecorations();
    },
    
    animateStepChange() {
      anime.timeline({
        easing: 'easeOutExpo'
      })
      .add({
        targets: this.$refs.formContent,
        opacity: [1, 0],
        translateY: [0, -10],
        duration: 300,
        complete: () => {
          // Animation completed
        }
      })
      .add({
        targets: this.$refs.formContent,
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 500,
      });
    },
    
    animateDecorations() {
      // Continuous animations for decorative elements
      anime({
        targets: this.$refs.circle1,
        translateX: '10px',
        translateY: '15px',
        duration: 8000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
      
      anime({
        targets: this.$refs.circle2,
        translateX: '-15px',
        translateY: '-10px',
        duration: 9000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
      
      anime({
        targets: this.$refs.circle3,
        translateX: '8px',
        translateY: '-12px',
        duration: 7000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
    },
    
    maskEmail(email) {
      if (!email) return '';
      const parts = email.split('@');
      if (parts.length !== 2) return email;
      
      const name = parts[0];
      const domain = parts[1];
      
      let masked = '';
      if (name.length <= 2) {
        masked = name[0] + '*';
      } else {
        masked = name[0] + '*'.repeat(name.length - 2) + name[name.length - 1];
      }
      
      return masked + '@' + domain;
    },
    
    startCooldown() {
      this.cooldown = 60;
      if (this.cooldownInterval) {
        clearInterval(this.cooldownInterval);
      }
      this.cooldownInterval = setInterval(() => {
        this.cooldown--;
        if (this.cooldown <= 0) {
          clearInterval(this.cooldownInterval);
        }
      }, 1000);
    },
    
    async requestCode() {
      if (this.loading || this.cooldown > 0) return;
      
      if (!this.email.trim() || !this.email.includes('@') || !this.email.includes('.')) {
        this.toast.error("Please enter a valid email address", {
          position: "top-center"
        });
        this.shakeElement(this.$refs.emailGroup);
        return;
      }
      
      this.loading = true;
      
      try {
        // Check if email belongs to an agent
        const agentCheckResponse = await api.post('/api/check-agent-email', {
          email: this.email
        });
        
        if (agentCheckResponse.status !== 200 || !agentCheckResponse.data.isAgent) {
          this.toast.error("Recovery is only available for verified agent accounts", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.emailGroup);
          this.loading = false;
          return;
        }
        
        this.agentVerified = true;
        
        // If it's an agent, send verification code
        const response = await api.post('/api/request-password-reset', {
          email: this.email
        });
        
        if (response.status === 200) {
          this.toast.success("Verification code sent to your email", {
            position: "top-center"
          });
          this.startCooldown();
          this.currentStep = 2;
          this.animateStepChange();
          
          // Focus on first code input field
          setTimeout(() => {
            if (this.codeInputs[0]) {
              this.codeInputs[0].focus();
            }
          }, 500);
        } else {
          this.toast.error(response.data.message || "Failed to send verification code", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.emailGroup);
        }
      } catch (error) {
        console.error('Request code error:', error);
        this.toast.error(error.response?.data?.message || "An error occurred while sending the code", {
          position: "top-center"
        });
        this.shakeElement(this.$refs.emailGroup);
      } finally {
        this.loading = false;
      }
    },
    
    async verifyCode() {
      if (this.loading || !this.isCodeComplete) return;
      
      this.loading = true;
      
      try {
        const response = await api.post('/api/verify-reset-code', {
          email: this.email,
          code: this.fullVerificationCode
        });
        
        if (response.status === 200) {
          this.toast.success("Code verified successfully", {
            position: "top-center"
          });
          this.codeVerified = true;
          this.currentStep = 3;
          this.animateStepChange();
          
          // Focus on password field
          setTimeout(() => {
            if (this.$refs.passwordInput) {
              this.$refs.passwordInput.focus();
            }
          }, 500);
        } else {
          this.toast.error(response.data.message || "Invalid verification code", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.codeGroup);
          
          // Clear code inputs
          this.verificationCode = Array(6).fill('');
          if (this.codeInputs[0]) {
            this.codeInputs[0].focus();
          }
        }
      } catch (error) {
        console.error('Verify code error:', error);
        this.toast.error(error.response?.data?.message || "Failed to verify code", {
          position: "top-center"
        });
        this.shakeElement(this.$refs.codeGroup);
      } finally {
        this.loading = false;
      }
    },
    
    async handleSubmit() {
      if (this.loading || !this.canResetPassword) return;
      
      this.loading = true;
      
      try {
        const response = await api.post('/api/reset-password', {
          email: this.email,
          code: this.fullVerificationCode,
          password: this.newPassword
        });
        
        if (response.status === 200) {
          this.resetCompleted = true;
          this.toast.success("Password reset successfully", {
            position: "top-center"
          });
          
          // Animate success
          anime.timeline({
            easing: 'easeOutExpo'
          })
          .add({
            targets: this.$refs.successContainer,
            scale: [0.9, 1],
            opacity: [0, 1],
            duration: 800,
          });
        } else {
          this.toast.error(response.data.message || "Failed to reset password", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.passwordGroup);
        }
      } catch (error) {
        console.error('Reset password error:', error);
        this.toast.error(error.response?.data?.message || "An error occurred while resetting the password", {
          position: "top-center"
        });
        this.shakeElement(this.$refs.passwordGroup);
      } finally {
        this.loading = false;
      }
    },
    
    handleCodeInput(index) {
      // Format to ensure only numbers
      this.verificationCode[index] = this.verificationCode[index].replace(/[^0-9]/g, '');
      
      // Auto move to next input
      if (this.verificationCode[index] && index < 5 && this.codeInputs[index + 1]) {
        this.codeInputs[index + 1].focus();
      }
    },
    
    handleKeyDown(event, index) {
      // Handle backspace
      if (event.key === 'Backspace') {
        if (!this.verificationCode[index] && index > 0 && this.codeInputs[index - 1]) {
          this.codeInputs[index - 1].focus();
        }
      }
    },
    
    handlePaste(event) {
      event.preventDefault();
      const pastedData = (event.clipboardData || window.clipboardData).getData('text');
      
      // Extract only numbers and limit to 6 digits
      const digits = pastedData.replace(/[^0-9]/g, '').slice(0, 6);
      
      // Fill each input with pasted digits
      for (let i = 0; i < digits.length; i++) {
        if (i < 6) {
          this.verificationCode[i] = digits[i];
        }
      }
      
      // Focus last filled input or next empty input
      const focusIndex = Math.min(digits.length, 5);
      if (this.codeInputs[focusIndex]) {
        this.codeInputs[focusIndex].focus();
      }
    },
    
    shakeElement(element) {
      if (!element) return;
      
      anime({
        targets: element,
        translateX: [
          { value: -10, duration: 100, delay: 0 },
          { value: 10, duration: 100, delay: 0 },
          { value: -8, duration: 100, delay: 0 },
          { value: 8, duration: 100, delay: 0 },
          { value: -5, duration: 100, delay: 0 },
          { value: 0, duration: 100, delay: 0 }
        ],
        easing: 'easeInOutSine'
      });
    }
  },
  beforeUnmount() {
    if (this.cooldownInterval) {
      clearInterval(this.cooldownInterval);
    }
  }
}
</script>

<style scoped>
.forgot-password-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
  background-color: var(--bg-color);
  overflow: hidden;
}

.forgot-password-form {
  width: 100%;
  max-width: 450px;
  padding: 2.5rem;
  background: var(--input-bg);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  position: relative;
  margin-top: 1rem;
  overflow: hidden;
  opacity: 0; /* Initial state for animation */
}

.back-button {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-color);
  opacity: 0.7;
  transition: all 0.3s ease;
  box-shadow: 0 3px 8px rgba(0,0,0,0.1);
  z-index: 10;
}

.back-button:hover {
  transform: translateX(-3px);
  opacity: 1;
  color: var(--primary-color);
}

.form-content {
  position: relative;
  z-index: 2;
}

.logo-container {
  text-align: center;
  margin-bottom: 2rem;
  position: relative;
  z-index: 2;
}

.logo-icon {
  font-size: 2.5rem;
  color: var(--primary-color);
  padding: 1.2rem;
  border-radius: 50%;
  background: rgba(var(--primary-color-rgb), 0.1);
  box-shadow: 0 5px 15px rgba(var(--primary-color-rgb), 0.2);
}

.title-text {
  color: var(--text-color);
  font-size: 1.85rem;
  text-align: center;
  margin: 0 0 0.8rem 0;
  font-weight: 700;
  position: relative;
  z-index: 2;
}

.subtitle {
  color: var(--text-color);
  opacity: 0.8;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1rem;
  position: relative;
  z-index: 2;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: 2px solid rgba(var(--primary-color-rgb), 0.3);
  color: var(--text-color);
  opacity: 0.7;
  transition: all 0.3s ease;
}

.step.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  opacity: 1;
  box-shadow: 0 0 0 5px rgba(var(--primary-color-rgb), 0.15);
}

.step-line {
  height: 2px;
  width: 60px;
  background: rgba(var(--primary-color-rgb), 0.3);
}

.input-group {
  margin-bottom: 1.5rem;
  position: relative;
  z-index: 2;
}

.input-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.input-icon {
  position: absolute;
  left: 1.2rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color);
  opacity: 0.6;
  z-index: 1;
}

.input-field {
  width: 100%;
  padding: 1.2rem 1.2rem 1.2rem 3.2rem;
  border: 2px solid var(--input-border);
  border-radius: 12px;
  color: var(--text-color);
  font-size: 1rem;
  background: var(--bg-color);
  transition: all 0.3s ease;
}

.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.15);
}

.input-label {
  position: absolute;
  left: 3.2rem;
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-color);
  padding: 0 0.5rem;
  color: var(--text-color);
  opacity: 0.6;
  transition: all 0.3s ease;
  pointer-events: none;
}

.input-field:focus + .input-label,
.input-field:not(:placeholder-shown) + .input-label {
  transform: translateY(-2rem) scale(0.85);
  opacity: 1;
  color: var(--primary-color);
  font-weight: 600;
  left: 2.5rem;
}

.input-hint {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  color: var(--text-color);
  opacity: 0.7;
  padding-left: 0.5rem;
}

.code-container {
  display: flex;
  justify-content: space-between;
  margin: 1rem 0;
}

.code-input {
  width: 50px;
  height: 60px;
  border: 2px solid var(--input-border);
  border-radius: 10px;
  background: var(--bg-color);
  font-size: 1.5rem;
  font-weight: 700;
  text-align: center;
  color: var(--text-color);
  transition: all 0.3s ease;
}

.code-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.15);
}

.resend-container {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.8;
}

.resend-link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.resend-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.password-strength {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  font-weight: 600;
  padding-left: 0.5rem;
  display: flex;
  align-items: center;
}

.pw-very-weak, .pw-weak {
  color: var(--error-color);
}

.pw-medium {
  color: var(--warning-color);
}

.pw-strong, .pw-very-strong {
  color: var(--success-color);
}

.action-button {
  width: 100%;
  padding: 1.1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  position: relative;
  z-index: 2;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.25);
  margin-top: 1.5rem;
}

.action-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(var(--primary-color-rgb), 0.3);
}

.action-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(var(--primary-color-rgb), 0.2);
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.success-container {
  text-align: center;
  padding: 1rem 0;
  animation: fadeIn 0.5s ease;
}

.success-icon {
  font-size: 3.5rem;
  color: var(--success-color);
  margin-bottom: 1.5rem;
}

.success-title {
  font-size: 1.5rem;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.success-message {
  color: var(--text-color);
  opacity: 0.8;
  margin-bottom: 2rem;
}

.decorative-circles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0;
}

.circle-1 {
  width: 180px;
  height: 180px;
  bottom: -60px;
  right: -60px;
  background: linear-gradient(135deg, rgba(var(--primary-color-rgb), 0.4), rgba(var(--primary-color-rgb), 0.1));
}

.circle-2 {
  width: 120px;
  height: 120px;
  top: -30px;
  left: -30px;
  background: linear-gradient(135deg, rgba(var(--primary-color-rgb), 0.3), rgba(var(--primary-color-rgb), 0.05));
}

.circle-3 {
  width: 80px;
  height: 80px;
  top: 40%;
  right: -20px;
  background: linear-gradient(135deg, rgba(var(--primary-color-rgb), 0.2), rgba(var(--primary-color-rgb), 0.03));
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 480px) {
  .forgot-password-form {
    padding: 2rem 1.5rem;
  }
  
  .code-input {
    width: 40px;
    height: 50px;
    font-size: 1.2rem;
  }
  
  .step-line {
    width: 40px;
  }
  
  .title-text {
    font-size: 1.6rem;
  }
  
  .back-button {
    top: 1rem;
    left: 1rem;
    width: 32px;
    height: 32px;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #121212;
    --input-bg: #1e1e1e;
    --input-border: #333;
    --text-color: #e0e0e0;
  }
  
  .input-field:focus {
    background: #252525;
  }
  
  .input-field:focus + .input-label,
  .input-field:not(:placeholder-shown) + .input-label {
    background: #252525;
  }
}

/* Animations */
@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.85;
  }
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
}

/* Accessibility improvements */
.input-field:focus, 
.code-input:focus, 
.action-button:focus, 
.back-button:focus,
.resend-link:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.5);
}

/* Focus visible */
.input-field:focus-visible, 
.code-input:focus-visible, 
.action-button:focus-visible, 
.back-button:focus-visible,
.resend-link:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
</style>