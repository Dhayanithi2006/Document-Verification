// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Government-Grade Authentication Portal (login.js)
import { icons } from '../icons.js';
import { renderAlert } from '../components.js';

export function renderLogin(state, params = {}) {
  const returnTo = params?.returnTo || '';

  return `
    <div class="login-page-container">
      <div class="card login-card">
        <!-- Official Government Header Band -->
        <div class="card-header login-header">
          <div class="brand-emblem login-emblem" aria-hidden="true">
            ${icons.scale}
          </div>
          <div>
            <h1 class="login-title">Sign In to Your Account</h1>
            <p class="login-subtitle">
              AICTE Pre-Scrutiny & Deficiency Resolution Platform
            </p>
            <div class="login-department">
              Department of Higher Education | Ministry of Education, Govt. of India
            </div>
          </div>
        </div>

        <div class="card-body login-body">
          <!-- Dynamic Alert Container -->
          <div id="login-error-container" style="display: none; margin-bottom: var(--space-4);" role="alert" aria-live="polite"></div>

          <!-- Login Form -->
          <form id="login-form" novalidate>
            <input type="hidden" id="login-return-to" value="${escapeHtml(returnTo)}">

            <div class="form-group">
              <label class="form-label" for="login-email">
                Registered Email ID / Institute Login ID <span style="color: var(--color-red-600);" aria-hidden="true">*</span>
              </label>
              <div class="input-icon-wrapper">
                <input 
                  type="email" 
                  id="login-email" 
                  name="email" 
                  class="form-control" 
                  placeholder="name@institution.edu.in" 
                  required 
                  autocomplete="username" 
                  spellcheck="false"
                  value=""
                  aria-required="true"
                >
              </div>
              <div class="form-help">Enter the registered email associated with your AICTE approval profile.</div>
            </div>

            <div class="form-group">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-1);">
                <label class="form-label" for="login-password" style="margin-bottom: 0;">
                  Password <span style="color: var(--color-red-600);" aria-hidden="true">*</span>
                </label>
              </div>
              <div class="password-input-group">
                <input 
                  type="password" 
                  id="login-password" 
                  name="password" 
                  class="form-control" 
                  placeholder="Enter your security password" 
                  required 
                  autocomplete="current-password"
                  aria-required="true"
                >
                <button 
                  type="button" 
                  id="btn-toggle-password" 
                  class="btn-toggle-password" 
                  aria-label="Show password as plain text"
                  title="Toggle password visibility"
                >
                  <span id="eye-icon-visible" aria-hidden="true">${icons.eye}</span>
                  <span id="eye-icon-hidden" style="display: none;" aria-hidden="true">${icons.shieldCheck}</span>
                </button>
              </div>
            </div>

            <button type="submit" id="btn-login-submit" class="btn btn-primary login-submit-btn">
              <span id="login-submit-text">Sign In to Platform</span>
              <span id="login-submit-spinner" class="spinner" style="display: none;" aria-hidden="true"></span>
              <span aria-hidden="true">${icons.chevronRight}</span>
            </button>
          </form>

          <!-- Safe Synthetic Demo Credentials Selector -->
          <div class="demo-credentials-box">
            <div class="demo-credentials-header">
              <span class="badge badge-info">SYNTHETIC DEMO CREDENTIALS</span>
              <span style="font-size: 11px; color: var(--text-muted);">Quick-fill for evaluation</span>
            </div>
            <div class="demo-accounts-grid">
              <button type="button" class="btn-demo-account" data-email="applicant@institution.test" data-pass="Password123!">
                <strong>Institution Applicant</strong>
                <span>applicant@institution.test</span>
              </button>
              <button type="button" class="btn-demo-account" data-email="reviewer@reviewer.test" data-pass="ReviewerPass123!">
                <strong>Authorised Reviewer</strong>
                <span>reviewer@reviewer.test</span>
              </button>
              <button type="button" class="btn-demo-account" data-email="admin@platform.test" data-pass="AdminPass123!">
                <strong>System Administrator</strong>
                <span>admin@platform.test</span>
              </button>
            </div>
          </div>
        </div>

        <div class="card-footer login-footer">
          <div>SIH Prototype — Not an official AICTE portal.</div>
          <div style="font-size: 10px; color: #94A3B8; margin-top: 2px;">
            Secure Encrypted Session • AICTE APH 2024-2027 Baseline
          </div>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function initLoginView(state, router) {
  const form = document.getElementById('login-form');
  if (!form) return;

  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  const togglePassBtn = document.getElementById('btn-toggle-password');
  const eyeVisible = document.getElementById('eye-icon-visible');
  const eyeHidden = document.getElementById('eye-icon-hidden');
  const submitBtn = document.getElementById('btn-login-submit');
  const submitText = document.getElementById('login-submit-text');
  const submitSpinner = document.getElementById('login-submit-spinner');
  const errorContainer = document.getElementById('login-error-container');
  const returnToInput = document.getElementById('login-return-to');

  // Password visibility toggle
  if (togglePassBtn && passwordInput) {
    togglePassBtn.addEventListener('click', () => {
      const isPassword = passwordInput.type === 'password';
      passwordInput.type = isPassword ? 'text' : 'password';
      togglePassBtn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password as plain text');
      if (eyeVisible && eyeHidden) {
        eyeVisible.style.display = isPassword ? 'none' : 'inline-block';
        eyeHidden.style.display = isPassword ? 'inline-block' : 'none';
      }
    });
  }

  // Quick fill buttons
  const demoButtons = document.querySelectorAll('.btn-demo-account');
  demoButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const email = btn.getAttribute('data-email');
      const pass = btn.getAttribute('data-pass');
      if (emailInput && passwordInput) {
        emailInput.value = email;
        passwordInput.value = pass;
        emailInput.focus();
        if (errorContainer) errorContainer.style.display = 'none';
      }
    });
  });

  // Form submit handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';

    // Client-side validation
    if (!email) {
      showError('Please enter your registered email address.');
      if (emailInput) emailInput.focus();
      return;
    }

    if (!password) {
      showError('Please enter your password.');
      if (passwordInput) passwordInput.focus();
      return;
    }

    // Set Loading State
    setLoading(true);
    if (errorContainer) errorContainer.style.display = 'none';

    try {
      const user = await state.login(email, password);
      setLoading(false);

      // Determine post-login redirect
      let dest = '';
      if (returnToInput && returnToInput.value) {
        const rawReturn = decodeURIComponent(returnToInput.value);
        // Validate internal relative route only (prevent open redirects)
        if (rawReturn.startsWith('/') && !rawReturn.startsWith('//') && !rawReturn.includes(':') && rawReturn !== '/login') {
          dest = rawReturn;
        }
      }

      if (!dest) {
        // Role-appropriate default home
        if (user.role === 'INSTITUTION') dest = '/dashboard';
        else if (user.role === 'REVIEWER') dest = '/reviewer/queue';
        else if (user.role === 'ADMIN') dest = '/admin/rules';
        else dest = '/dashboard';
      }

      router.navigate(dest);
    } catch (err) {
      setLoading(false);
      showError(err.message || 'Authentication failed. Please verify your credentials.');
      if (passwordInput) {
        passwordInput.value = '';
        passwordInput.focus();
      }
    }
  });

  function showError(msg) {
    if (!errorContainer) return;
    errorContainer.innerHTML = renderAlert('error', 'Sign In Failed', msg);
    errorContainer.style.display = 'block';
  }

  function setLoading(isLoading) {
    if (submitBtn) submitBtn.disabled = isLoading;
    if (submitSpinner) submitSpinner.style.display = isLoading ? 'inline-block' : 'none';
    if (submitText) submitText.textContent = isLoading ? 'Authenticating...' : 'Sign In to Platform';
  }
}
