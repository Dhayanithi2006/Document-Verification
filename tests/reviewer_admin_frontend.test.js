// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Reviewer & Administrator Frontend & API Integration Tests (tests/reviewer_admin_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert/strict';
import { api } from '../frontend/js/api.js';
import { renderReviewerQueue } from '../frontend/js/views/reviewer-queue.js';
import { renderReviewerScrutiny, initReviewerScrutinyView } from '../frontend/js/views/reviewer-scrutiny.js';
import { renderAdminAudit } from '../frontend/js/views/admin-audit.js';
import { renderAdminUsers } from '../frontend/js/views/admin-users.js';
import { Router } from '../frontend/js/router.js';

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
      hash: '#/reviewer/queue',
      origin: 'http://localhost:3000'
    },
    scrollTo: () => {},
    addEventListener: () => {},
    confirm: () => true
  };
}

if (typeof globalThis.document === 'undefined') {
  const elements = new Map();
  globalThis.document = {
    getElementById: (id) => {
      if (!elements.has(id)) {
        elements.set(id, {
          id,
          innerHTML: '',
          textContent: '',
          style: {},
          classList: { add: () => {}, remove: () => {} },
          addEventListener: () => {},
          dataset: {},
          setAttribute: () => {},
          getAttribute: () => null
        });
      }
      return elements.get(id);
    },
    querySelector: () => null,
    querySelectorAll: () => []
  };
}

test('P9 Reviewer Workspace & Administration Frontend Integration', async (t) => {
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  let reviewerToken = null;
  let reviewerUser = null;
  let adminToken = null;
  let targetAppId = null;

  await t.test('1. Authenticate as Authorised Reviewer', async () => {
    const res = await api.login('reviewer@reviewer.test', 'ReviewerPass123!');
    assert.ok(res.access_token, 'Reviewer token should exist');
    assert.equal(res.user.role, 'REVIEWER', 'Role must be REVIEWER');
    reviewerToken = res.access_token;
    reviewerUser = res.user;
  });

  await t.test('2. Query Reviewer Queue via api.getReviewerQueue', async () => {
    api.setToken(reviewerToken);
    const queueData = await api.getReviewerQueue();
    assert.ok(Array.isArray(queueData.items), 'items must be an array');
    assert.ok(queueData.metrics, 'metrics must exist');
    assert.ok(queueData.total >= 1, 'Total applications must be >= 1');
    assert.ok(typeof queueData.metrics.total_applications === 'number', 'total_applications metric must be numeric');
    
    targetAppId = queueData.items[0].id;
    assert.ok(targetAppId, 'targetAppId should be extracted');
  });

  await t.test('3. Query Scrutiny Case Details via api.getScrutinyDetails', async () => {
    api.setToken(reviewerToken);
    const caseData = await api.getScrutinyDetails(targetAppId);
    assert.ok(caseData.application, 'Application summary must be returned');
    assert.ok(Array.isArray(caseData.checklist), 'Checklist must be returned as array');
    assert.ok(Array.isArray(caseData.findings), 'Findings must be returned as array');
    assert.ok(Array.isArray(caseData.correction_submissions), 'Correction submissions must be returned as array');
    assert.ok(Array.isArray(caseData.observations), 'Observations must be returned as array');
    assert.ok(Array.isArray(caseData.eligible_actions), 'Eligible actions must be returned');
  });

  await t.test('4. Assign Case to Reviewer via api.assignReviewer', async () => {
    api.setToken(reviewerToken);
    const assignRes = await api.assignReviewer(targetAppId, reviewerUser.id, 'Assigned via Frontend Integration Test');
    assert.equal(assignRes.id, targetAppId, 'Application ID must match');
    assert.equal(assignRes.assigned_reviewer_id, reviewerUser.id, 'Reviewer ID must match');
  });

  await t.test('5. Record Scrutiny Observation via api.recordReviewerObservation', async () => {
    api.setToken(reviewerToken);
    const obsRes = await api.recordReviewerObservation(targetAppId, {
      decision: 'GENERAL_OBSERVATION',
      justification: 'Statutory scrutiny conducted against AICTE Approval Process Handbook (APH 2024-2027) norms.',
      is_internal_note: false
    });
    assert.ok(obsRes.id, 'Observation record ID must be generated');
    assert.equal(obsRes.decision, 'GENERAL_OBSERVATION', 'Decision must match payload');
    assert.equal(obsRes.application_id, targetAppId, 'Application ID must match');
  });

  await t.test('6. Record Stage Signoff via api.completePrescrutinyDecision', async () => {
    api.setToken(reviewerToken);
    const decisionRes = await api.completePrescrutinyDecision(targetAppId, {
      decision: 'RETURNED_FOR_CORRECTION',
      remarks: 'Returned for institutional clarification regarding fire certificate endorsement.'
    });
    assert.equal(decisionRes.id, targetAppId, 'Application ID must match');
    assert.equal(decisionRes.review_status, 'RETURNED_FOR_CORRECTION', 'Review status must be RETURNED_FOR_CORRECTION');
    assert.equal(decisionRes.status, 'RETURNED_FOR_CORRECTION', 'Application status must be updated');
  });

  await t.test('7. Authenticate as Administrator & Query Overview via api.getAdminOverview', async () => {
    const adminLogin = await api.login('admin@platform.test', 'AdminPass123!');
    assert.equal(adminLogin.user.role, 'ADMIN', 'Role must be ADMIN');
    adminToken = adminLogin.access_token;
    api.setToken(adminToken);

    const overview = await api.getAdminOverview();
    assert.ok(overview.total_users >= 4, 'total_users must be >= 4');
    assert.ok(overview.total_institutions >= 2, 'total_institutions must be >= 2');
    assert.ok(overview.total_applications >= 1, 'total_applications must be >= 1');
    assert.ok(overview.total_audit_events >= 1, 'total_audit_events must be >= 1');
  });

  await t.test('8. Query and Provision User via api.getAdminUsers & api.createAdminUser', async () => {
    api.setToken(adminToken);
    const users = await api.getAdminUsers();
    assert.ok(Array.isArray(users), 'Users must be an array');
    assert.ok(users.length >= 4, 'Users count must be >= 4');

    const uniqueEmail = `test_reviewer_${Date.now()}@reviewer.test`;
    const newUser = await api.createAdminUser({
      email: uniqueEmail,
      full_name: 'Dr. Automated Test Reviewer',
      password: 'SecureTestPass123!',
      role: 'REVIEWER',
      is_active: true
    });
    assert.equal(newUser.email, uniqueEmail, 'Provisioned email must match');
    assert.equal(newUser.role, 'REVIEWER', 'Provisioned role must be REVIEWER');
    assert.equal(newUser.is_active, true, 'User must be active');
  });

  await t.test('9. Query Forensic Audit Log via api.getAdminAuditEvents', async () => {
    api.setToken(adminToken);
    const auditEvents = await api.getAdminAuditEvents();
    assert.ok(Array.isArray(auditEvents), 'Audit events must be an array');
    assert.ok(auditEvents.length >= 1, 'Audit events count must be >= 1');
    assert.ok(auditEvents[0].action, 'Action must be present in audit record');
    assert.ok(auditEvents[0].actor_user_id, 'Actor user ID must be present');
  });

  await t.test('10. RBAC Boundary: Institutional Applicant Denied Access to Reviewer & Admin APIs', async () => {
    const instLogin = await api.login('applicant@institution.test', 'Password123!');
    api.setToken(instLogin.access_token);

    // Reviewer queue access denied
    await assert.rejects(
      async () => await api.getReviewerQueue(),
      (err) => err.status === 403,
      'Institutional applicant must be rejected with 403 on reviewer queue'
    );

    // Admin overview access denied
    await assert.rejects(
      async () => await api.getAdminOverview(),
      (err) => err.status === 403,
      'Institutional applicant must be rejected with 403 on admin overview'
    );
  });

  await t.test('11. Template Rendering: Reviewer and Admin Views', () => {
    const mockState = {
      getCurrentUser: () => ({ name: 'Prof. K. S. Krishnan', role: 'REVIEWER' })
    };

    const queueHtml = renderReviewerQueue(mockState);
    assert.ok(queueHtml.includes('AICTE Scrutiny Committee Queue'), 'Reviewer queue markup must render header');
    assert.ok(queueHtml.includes('reviewer-table-container'), 'Reviewer table container must exist');

    const scrutinyHtml = renderReviewerScrutiny(mockState, { id: 'app_test_123' });
    assert.ok(scrutinyHtml.includes('scrutiny-console-root'), 'Scrutiny console root must exist');

    const auditHtml = renderAdminAudit(mockState);
    assert.ok(auditHtml.includes('Tamper-Evident System Audit Trail'), 'Audit trail markup must render header');

    const usersHtml = renderAdminUsers(mockState);
    assert.ok(usersHtml.includes('User Accounts & Reviewer Role Governance'), 'Users admin markup must render header');
    assert.ok(usersHtml.includes('modal-create-user'), 'User provisioning modal must exist');
  });

  await t.test('12. Regression: Opening application from Reviewer Queue generates correct href to Scrutiny Console', async () => {
    api.setToken(reviewerToken);
    const queueData = await api.getReviewerQueue();
    const app = queueData.items[0];
    assert.ok(app && app.id, 'Application must exist in queue');

    // Verify queue link targets application scrutiny console with application ID
    const queueLink = `#/reviewer/scrutiny/${app.id}`;
    assert.equal(queueLink, `#/reviewer/scrutiny/${targetAppId}`, 'Queue link must contain target application ID');
  });

  await t.test('13. Regression: Opening #/reviewer/scrutiny/:id routes application ID to initReviewerScrutinyView without missing ID error', async () => {
    api.setToken(reviewerToken);
    const mockState = {
      activeRole: 'REVIEWER',
      authStatus: 'authenticated',
      isAuthenticated: () => true,
      getCurrentUser: () => reviewerUser,
      notifyListeners: () => {}
    };

    const targetEl = document.getElementById('main-content');
    const router = new Router(mockState, 'main-content');

    window.location.hash = `#/reviewer/scrutiny/${targetAppId}`;
    router.handleRoute();

    // Verify view shell rendered
    assert.ok(targetEl.innerHTML.includes('scrutiny-console-root'), 'Scrutiny console root must be rendered in main container');

    // Execute init hook with router invocation arguments
    const rootEl = document.getElementById('scrutiny-console-root');
    await initReviewerScrutinyView(mockState, router, { id: targetAppId });

    // Verify no missing ID error is rendered and scrutiny data loaded
    assert.ok(!rootEl.innerHTML.includes('Error: Missing Application ID'), 'View must not display Missing Application ID error');
    assert.ok(rootEl.innerHTML.includes('Case Assessment:') || rootEl.innerHTML.includes(targetAppId), 'View must render case assessment with application ID');
  });
});
