// src/stores/auth.js
import { defineStore } from 'pinia';
export const useAuthStore = defineStore('auth', {
  state: () => ({
    isLoggedIn: false,
    userRole: null
  }),
  actions: {
    login(user) {
      this.isLoggedIn = true;
      this.userRole = user.role;
    },
    logout() {
      this.isLoggedIn = false;
      this.userRole = null;
    }
  }
});