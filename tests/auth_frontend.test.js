// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// P4 Authentication & Protected Routes Test Suite (tests/auth_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert';
import { api, ApiError, SessionExpiredError } from '../frontend/js/api.js';
import { state } from '../frontend/js/state.js';
import { Router } from '../frontend/js/router.js';
import { renderLogin } from '../frontend/js/views/login.js';
import { renderAccessDenied } from '../frontend/js/views/access-denied.js';
import { renderHeader } from '../frontend/js/components.js';

// Setup Mock Browser Environment for Node.js
if (typeof globalThis.window === 'undefined') {
  const storage = new Map();
  globalThis.window = {
    sessionStorage: {
      getItem: (k) => storage.get(k) || null,
      setItem: (k, v) => storage.set(k, String(v)),
      removeItem: (k) => storage.delete(k),
      clear: () => storage.clear()
    },
    location: {
      hash: '#/dashboard',
      origin: 'http://localhost:3000'
    },
    scrollTo: () => {},
    addEventListener: () => {}
  };
  globalThis.document = {
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => []
  };
}

test('1. API Client: Token Storage, Headers and Error Classification', () => {
  api.clearToken();
  assert.strictEqual(api.getToken(), null, 'Token must initially be null');

  api.setToken('test_jwt_token_123');
  assert.strictEqual(api.getToken(), 'test_jwt_token_123', 'Token must be stored in sessionStorage');

  api.clearToken();
  assert.strictEqual(api.getToken(), null, 'clearToken must remove the token');

  const err401 = new SessionExpiredError();
  assert.strictEqual(err401.status, 401);
  assert.strictEqual(err401.name, 'SessionExpiredError');

  const customErr = new ApiError('Forbidden role', 403);
  assert.strictEqual(customErr.status, 403);
  assert.strictEqual(customErr.message, 'Forbidden role');
});

test('2. State Manager: Session Lifecycle State Transitions', async () => {
  // Test Initializing State
  state.authStatus = 'initializing';
  state.currentUser = null;
  assert.strictEqual(state.isAuthenticated(), false);

  // Without token, initSession should transition to unauthenticated
  api.clearToken();
  const restored = await state.initSession();
  assert.strictEqual(restored, false);
  assert.strictEqual(state.authStatus, 'unauthenticated');
  assert.strictEqual(state.currentUser, null);

  // Fake an authenticated state
  state.currentUser = {
    id: 'usr_inst_01',
    email: 'applicant@institution.test',
    full_name: 'Dr. R. K. Sharma',
    role: 'INSTITUTION',
    institution_id: 'inst_01',
    institution: { name: 'Apex Institute of Technology' }
  };
  state.authStatus = 'authenticated';
  state.activeRole = 'INSTITUTION';
  assert.strictEqual(state.isAuthenticated(), true);

  const currentUser = state.getCurrentUser();
  assert.strictEqual(currentUser.name, 'Dr. R. K. Sharma');
  assert.strictEqual(currentUser.role, 'INSTITUTION');

  // Test Logout Transition
  await state.logout();
  assert.strictEqual(state.isAuthenticated(), false);
  assert.strictEqual(state.authStatus, 'unauthenticated');
  assert.strictEqual(state.currentUser, null);
});

test('3. Login View: Semantic Structure, Prototype Disclosure, and Password Toggle', () => {
  const html = renderLogin(state, { returnTo: '/applications/app_9812' });

  // Semantic Controls
  assert.ok(html.includes('id="login-form"'), 'Missing login form element');
  assert.ok(html.includes('id="login-email"'), 'Missing email input');
  assert.ok(html.includes('id="login-password"'), 'Missing password input');
  assert.ok(html.includes('id="btn-toggle-password"'), 'Missing password visibility toggle');
  assert.ok(html.includes('id="btn-login-submit"'), 'Missing submit button');
  assert.ok(html.includes('id="login-error-container"'), 'Missing inline error container');

  // Government Identification & Prototype Disclosure
  assert.ok(html.includes('Sign In to Your Account'), 'Missing sign in heading');
  assert.ok(html.includes('SIH Prototype — Not an official AICTE portal.'), 'Missing mandatory prototype notice');
  assert.ok(html.includes('Ministry of Education, Govt. of India'), 'Missing ministry attribution');

  // Synthetic Demo Accounts Drawer
  assert.ok(html.includes('SYNTHETIC DEMO CREDENTIALS'), 'Missing demo accounts helper section');
  assert.ok(html.includes('applicant@institution.test'), 'Missing institution demo account button');
  assert.ok(html.includes('reviewer@reviewer.test'), 'Missing reviewer demo account button');
  assert.ok(html.includes('admin@platform.test'), 'Missing admin demo account button');

  // Safe Return Destination Preservation
  assert.ok(html.includes('value="/applications/app_9812"'), 'Missing encoded return-to destination');
});

test('4. Route Protection: Role Permissions and Metadata', () => {
  const router = new Router(state, 'dummy-content');

  // Verify public routes
  const loginRoute = router.routes.find(r => r.pattern.test('/login'));
  assert.ok(loginRoute, 'Login route must be defined');
  assert.strictEqual(loginRoute.isPublic, true, 'Login route must be public');

  // Verify role restrictions on protected routes
  const newAppRoute = router.routes.find(r => r.pattern.test('/applications/new'));
  assert.strictEqual(newAppRoute.isPublic, false, 'Applications/new must be protected');
  assert.deepStrictEqual(newAppRoute.allowedRoles, ['INSTITUTION'], 'Only INSTITUTION role can create new EoA');

  const reviewerQueueRoute = router.routes.find(r => r.pattern.test('/reviewer/queue'));
  assert.strictEqual(reviewerQueueRoute.isPublic, false, 'Reviewer queue must be protected');
  assert.ok(reviewerQueueRoute.allowedRoles.includes('REVIEWER'), 'REVIEWER must have access to queue');
  assert.ok(!reviewerQueueRoute.allowedRoles.includes('INSTITUTION'), 'INSTITUTION must NOT have access to reviewer queue');

  const adminAuditRoute = router.routes.find(r => r.pattern.test('/admin/audit'));
  assert.strictEqual(adminAuditRoute.isPublic, false, 'Admin audit must be protected');
  assert.ok(adminAuditRoute.allowedRoles.includes('ADMIN'), 'ADMIN must have access to audit trail');
  assert.ok(!adminAuditRoute.allowedRoles.includes('INSTITUTION'), 'INSTITUTION must NOT have access to admin audit');
});

test('5. Access Denied (403) View: Informative and Safe Explanation', () => {
  state.activeRole = 'INSTITUTION';
  state.currentUser = {
    id: 'usr_inst_01',
    email: 'applicant@institution.test',
    name: 'Dr. R. K. Sharma',
    role: 'INSTITUTION'
  };

  const html = renderAccessDenied(state, { targetSection: '/reviewer/queue' });
  assert.ok(html.includes('403 — Access Denied'), 'Missing 403 header');
  assert.ok(html.includes('/reviewer/queue'), 'Missing target section reference');
  assert.ok(html.includes('INSTITUTION'), 'Missing active role indicator');
  assert.ok(html.includes('Return to Permitted Workspace'), 'Missing return button');
  assert.ok(html.includes('#/dashboard'), 'Safe return link must point to institutional dashboard');
});

test('6. Application Shell: Role-Aware Header & Logout Control', () => {
  // Test Unauthenticated Header
  const unauthHtml = renderHeader(null, 'INSTITUTION', false);
  assert.ok(unauthHtml.includes('Sign In'), 'Unauthenticated header must show Sign In link');
  assert.ok(!unauthHtml.includes('id="btn-header-logout"'), 'Unauthenticated header must not show Logout button');

  // Test Authenticated Header
  const authUser = {
    id: 'usr_inst_01',
    name: 'Dr. R. K. Sharma',
    title: 'Principal',
    role: 'INSTITUTION',
    institution: { name: 'Apex Institute of Technology' }
  };
  const authHtml = renderHeader(authUser, 'INSTITUTION', true);
  assert.ok(authHtml.includes('Dr. R. K. Sharma'), 'Authenticated header must display user name');
  assert.ok(authHtml.includes('id="btn-header-logout"'), 'Authenticated header must render Sign Out button');
  assert.ok(authHtml.includes('Sign Out'), 'Logout button must have accessible text');
});

test('7. End-to-End Real Backend Integration: Login, Profile, and Revocation', async () => {
  // Test against live FastAPI backend via proxy on port 3000
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  // 1. Invalid credentials
  await assert.rejects(
    async () => {
      await api.login('invalid.user@reviewer.test', 'WrongPassword123!');
    },
    (err) => {
      assert.strictEqual(err.status, 401);
      assert.ok(err.message.includes('Invalid') || err.message.includes('password'));
      return true;
    },
    'Invalid credentials must be rejected with 401'
  );

  // 2. Inactive account
  await assert.rejects(
    async () => {
      await api.login('inactive@institution.test', 'Password123!');
    },
    (err) => {
      assert.strictEqual(err.status, 403);
      assert.ok(err.message.includes('deactivated') || err.message.includes('inactive'));
      return true;
    },
    'Inactive accounts must be rejected with 403'
  );

  // 3. Valid Login as Institution Applicant
  const loginResult = await api.login('applicant@institution.test', 'Password123!');
  assert.ok(loginResult.access_token, 'Login must return access_token');
  assert.strictEqual(loginResult.user.email, 'applicant@institution.test');
  assert.strictEqual(loginResult.user.role, 'INSTITUTION');
  assert.strictEqual(loginResult.token_type, 'bearer');

  // Verify token was saved
  assert.strictEqual(api.getToken(), loginResult.access_token);

  // 4. Retrieve Current User Profile via /auth/me
  const profile = await api.getCurrentUser();
  assert.strictEqual(profile.id, 'usr_inst_01');
  assert.strictEqual(profile.email, 'applicant@institution.test');
  assert.strictEqual(profile.role, 'INSTITUTION');
  assert.ok(profile.institution, 'Institution user profile must include institution details');

  // 5. Logout & Remote Token Revocation
  const logoutResult = await api.logout();
  assert.strictEqual(logoutResult.success, true);
  assert.strictEqual(logoutResult.remoteRevoked, true, 'Remote revocation should succeed on backend');
  assert.strictEqual(api.getToken(), null, 'Local token must be cleared after logout');

  // 6. Verify Revoked Token Rejected on Backend
  api.setToken(loginResult.access_token); // Try reusing the revoked token
  await assert.rejects(
    async () => {
      await api.getCurrentUser();
    },
    (err) => {
      assert.strictEqual(err.status, 401);
      return true;
    },
    'Reusing revoked token must fail with 401'
  );

  api.clearToken();
});
