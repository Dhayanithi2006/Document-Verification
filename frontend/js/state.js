// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Client State & Authentication Session Manager (state.js)
import { api, SessionExpiredError } from './api.js';

class StateManager {
  constructor() {
    // Explicit Auth Lifecycle States: 'initializing' | 'authenticated' | 'unauthenticated' | 'error'
    this.authStatus = 'initializing';
    this.currentUser = null;
    this.activeRole = 'INSTITUTION'; // default fallback for preview/testing
    this.currentAppId = 'app_9812';
    this.errorMessage = null;
    this.listeners = [];

    // Fallback dictionary for testing and preview modes
    this.usersByRole = {
      INSTITUTION: {
        id: 'usr_inst_01',
        name: 'Dr. R. K. Sharma',
        full_name: 'Dr. R. K. Sharma',
        title: 'Principal / Authorized Representative',
        institution: 'Apex Institute of Technology & Management (Synthetic Demo)',
        institutionId: 'inst_01',
        institution_id: 'inst_01',
        role: 'INSTITUTION',
        email: 'applicant@institution.test'
      },
      REVIEWER: {
        id: 'usr_rev_104',
        name: 'Prof. K. S. Krishnan',
        full_name: 'Prof. K. S. Krishnan',
        title: 'Scrutiny Committee Reviewer',
        institution: 'Regional Scrutiny Panel (Synthetic Demo)',
        institutionId: null,
        institution_id: null,
        role: 'REVIEWER',
        email: 'reviewer@reviewer.test'
      },
      ADMIN: {
        id: 'usr_adm_001',
        name: 'Platform Administrator',
        full_name: 'Platform Administrator',
        title: 'Platform Operations & Rule Governance',
        institution: 'Platform Operations (Synthetic Demo)',
        institutionId: null,
        institution_id: null,
        role: 'ADMIN',
        email: 'admin@platform.test'
      }
    };

    // Auto-handle session expiration emitted from API client
    api.onSessionExpired(() => {
      this.handleSessionExpired();
    });
  }

  isAuthenticated() {
    return this.authStatus === 'authenticated' && !!this.currentUser;
  }

  getCurrentUser() {
    if (this.currentUser) {
      return {
        ...this.currentUser,
        name: this.currentUser.full_name || this.currentUser.name || this.currentUser.email,
        title: this.getRoleTitle(this.currentUser.role),
        institution: this.currentUser.institution?.name || (this.currentUser.role === 'INSTITUTION' ? 'Linked Institution' : 'AICTE Central Authority')
      };
    }
    return this.usersByRole[this.activeRole];
  }

  getRoleTitle(role) {
    if (role === 'INSTITUTION') return 'Authorized Institution Representative';
    if (role === 'REVIEWER') return 'AICTE Scrutiny Committee Member';
    if (role === 'ADMIN') return 'System Administrator';
    return 'Authorized User';
  }

  // Session Restoration Lifecycle
  async initSession() {
    this.authStatus = 'initializing';
    this.errorMessage = null;
    this.notifyListeners('AUTH_STATE_CHANGED', { status: this.authStatus });

    const token = api.getToken();
    if (!token) {
      this.authStatus = 'unauthenticated';
      this.currentUser = null;
      this.notifyListeners('AUTH_STATE_CHANGED', { status: this.authStatus });
      return false;
    }

    try {
      const user = await api.getCurrentUser();
      this.currentUser = user;
      this.activeRole = user.role;
      this.authStatus = 'authenticated';
      this.notifyListeners('AUTH_STATE_CHANGED', { status: this.authStatus, user: this.currentUser });
      return true;
    } catch (err) {
      api.clearToken();
      this.currentUser = null;
      this.authStatus = 'unauthenticated';
      if (!(err instanceof SessionExpiredError)) {
        this.errorMessage = err.message;
      }
      this.notifyListeners('AUTH_STATE_CHANGED', { status: this.authStatus, error: this.errorMessage });
      return false;
    }
  }

  // Login action
  async login(email, password) {
    this.errorMessage = null;
    try {
      const result = await api.login(email, password);
      this.currentUser = result.user;
      this.activeRole = result.user.role;
      this.authStatus = 'authenticated';
      this.notifyListeners('AUTH_STATE_CHANGED', { status: 'authenticated', user: this.currentUser });
      return result.user;
    } catch (err) {
      this.authStatus = 'unauthenticated';
      this.currentUser = null;
      this.errorMessage = err.message;
      this.notifyListeners('AUTH_STATE_CHANGED', { status: 'unauthenticated', error: err.message });
      throw err;
    }
  }

  // Logout action
  async logout() {
    const prevUser = this.currentUser;
    await api.logout();
    this.currentUser = null;
    this.authStatus = 'unauthenticated';
    this.notifyListeners('AUTH_STATE_CHANGED', { status: 'unauthenticated', user: null });
    this.notifyListeners('USER_LOGGED_OUT', { prevUser });
  }

  handleSessionExpired() {
    this.currentUser = null;
    this.authStatus = 'unauthenticated';
    this.errorMessage = 'Your session has expired. Please sign in again.';
    this.notifyListeners('SESSION_EXPIRED', { message: this.errorMessage });
  }

  // Preview & Testing helper
  setRole(newRole) {
    if (this.usersByRole[newRole]) {
      this.activeRole = newRole;
      if (!this.currentUser) {
        this.notifyListeners('ROLE_CHANGED', { role: newRole, user: this.getCurrentUser() });
      }
    }
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notifyListeners(eventType, data) {
    this.listeners.forEach(fn => {
      try {
        fn(eventType, data);
      } catch (err) {
        console.error(`Error in state listener for ${eventType}:`, err);
      }
    });
  }
}

export const state = new StateManager();
