// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// P8 Deficiency Resolution, Revalidation & History Frontend Integration Tests (tests/deficiency_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert';
import { api } from '../frontend/js/api.js';
import { renderDeficiencyBridge } from '../frontend/js/views/deficiency-bridge.js';

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
      hash: '#/applications',
      origin: 'http://localhost:3000'
    },
    scrollTo: () => {},
    addEventListener: () => {},
    confirm: () => true
  };
}

test('P8 Deficiency Resolution, Corrective Actions & Revalidation Frontend Integration', async (t) => {
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  let inst1Token = null;
  let testAppId = null;
  let actionableFindingId = null;

  // 1. Authenticate as Institution 1 Applicant
  await t.test('1. Authenticate as Institution 1 Applicant', async () => {
    const loginRes = await api.login('applicant@institution.test', 'Password123!');
    assert.ok(loginRes.access_token, 'Login must yield access token');
    inst1Token = loginRes.access_token;
    assert.strictEqual(api.getToken(), inst1Token);
  });

  // 2. Initialize Application & Pre-Scrutiny Findings
  await t.test('2. Create Application and Trigger Initial Pre-Scrutiny', async () => {
    const appRes = await api.createApplication({
      academic_year: '2026-2027',
      total_intake_applied: 540
    });
    assert.ok(appRes.id, 'Application must be created');
    testAppId = appRes.id;

    // Run initial pre-scrutiny checks to generate actionable findings
    const valRes = await api.validateApplication(testAppId);
    assert.strictEqual(valRes.status, 'COMPLETED');
    assert.ok(valRes.findings_summary.deficiencies > 0, 'Must identify deficiencies for empty checklist');
  });

  // 3. Query Application Deficiencies Workspace
  await t.test('3. Query Deficiency Workspace via api.getApplicationDeficiencies', async () => {
    const defData = await api.getApplicationDeficiencies(testAppId);
    assert.strictEqual(defData.application_id, testAppId);
    assert.ok(defData.total_deficiencies > 0, 'Total deficiencies must be > 0');
    assert.ok(defData.actionable_count > 0, 'Actionable count must be > 0');
    assert.ok(Array.isArray(defData.deficiencies), 'Deficiencies must be an array');

    const first = defData.deficiencies[0];
    assert.ok(first.id, 'Finding ID must exist');
    assert.ok(first.rule_code, 'Rule code must exist');
    assert.strictEqual(first.resolution_status, 'OPEN');
    actionableFindingId = first.id;
  });

  // 4. Acknowledge Finding
  await t.test('4. Acknowledge Actionable Finding via api.acknowledgeFinding', async () => {
    assert.ok(actionableFindingId, 'Actionable finding ID must be present');
    const ackRes = await api.acknowledgeFinding(actionableFindingId);
    assert.strictEqual(ackRes.id, actionableFindingId);
    assert.ok(ackRes.acknowledged_at, 'Acknowledged timestamp must be populated');
    assert.strictEqual(ackRes.resolution_status, 'ACKNOWLEDGED');

    // Re-verify in workspace
    const refreshed = await api.getApplicationDeficiencies(testAppId);
    assert.ok(refreshed.acknowledged_count >= 1, 'Acknowledged count must increment');
  });

  // 5. Save and Retrieve Draft Corrective Response
  await t.test('5. Save and Retrieve Draft Response via api.saveDraftResponse', async () => {
    const draftPayload = {
      response_text: 'Institution has initiated expedited renewal of missing statutory certificate.',
      response_category: 'CLARIFICATION_JUSTIFICATION'
    };

    const draftRes = await api.saveDraftResponse(actionableFindingId, draftPayload);
    assert.strictEqual(draftRes.status, 'DRAFT');
    assert.strictEqual(draftRes.cycle_number, 1);
    assert.strictEqual(draftRes.response_text, draftPayload.response_text);

    // Fetch via getFindingResponse
    const retrievedDraft = await api.getFindingResponse(actionableFindingId);
    assert.ok(retrievedDraft, 'Draft response must be retrievable');
    assert.strictEqual(retrievedDraft.id, draftRes.id);
    assert.strictEqual(retrievedDraft.status, 'DRAFT');
  });

  // 6. Submit Formal Corrective Response
  await t.test('6. Submit Formal Correction via api.submitCorrection', async () => {
    const submitPayload = {
      response_text: 'Inspection completed by competent authority; provisional clearance certificate issued.',
      response_category: 'CLARIFICATION_JUSTIFICATION'
    };

    const subRes = await api.submitCorrection(actionableFindingId, submitPayload);
    assert.strictEqual(subRes.status, 'SUBMITTED');
    assert.ok(subRes.submitted_at, 'Submitted timestamp must be recorded');
    assert.strictEqual(subRes.revalidation_status, 'PENDING');

    // Verify workspace status transitions to CORRECTION_SUBMITTED
    const refreshed = await api.getApplicationDeficiencies(testAppId);
    const target = refreshed.deficiencies.find(d => d.id === actionableFindingId);
    assert.ok(target, 'Target deficiency must be found');
    assert.strictEqual(target.resolution_status, 'CORRECTION_SUBMITTED');
  });

  // 7. Execute Controlled Revalidation
  await t.test('7. Controlled Revalidation via api.revalidateApplication', async () => {
    const revalRes = await api.revalidateApplication(testAppId);
    assert.strictEqual(revalRes.application_id, testAppId);
    assert.strictEqual(revalRes.status, 'COMPLETED');
    assert.ok(revalRes.run_number >= 2, 'Validation run number must be incremented');
    assert.ok(Array.isArray(revalRes.comparison), 'Delta comparison items must be returned');
  });

  // 8. Query Full Chronological Finding History
  await t.test('8. Chronological Timeline via api.getFindingHistory', async () => {
    const histRes = await api.getFindingHistory(actionableFindingId);
    assert.strictEqual(histRes.finding_id, actionableFindingId);
    assert.strictEqual(histRes.application_id, testAppId);
    assert.ok(Array.isArray(histRes.history), 'History must be an array');
    assert.ok(histRes.history.length >= 4, 'Must contain detection, acknowledgement, draft, and submission events');

    const eventTypes = histRes.history.map(e => e.event_type);
    assert.ok(eventTypes.includes('FINDING_IDENTIFIED'));
    assert.ok(eventTypes.includes('ACKNOWLEDGED'));
    assert.ok(eventTypes.includes('DRAFT_SAVED'));
    assert.ok(eventTypes.includes('CORRECTION_SUBMITTED'));
    assert.ok(eventTypes.includes('REVALIDATION_RUN'));

    // Check chronological order
    for (let i = 0; i < histRes.history.length - 1; i++) {
      const t1 = new Date(histRes.history[i].timestamp).getTime();
      const t2 = new Date(histRes.history[i + 1].timestamp).getTime();
      assert.ok(t1 <= t2, 'Events must be in non-decreasing chronological order');
    }
  });

  // 9. Multi-Tenant Cross-Institution Defense
  await t.test('9. Strict Multi-Tenant Isolation (IDOR Defense)', async () => {
    // Authenticate as Institution 2
    await api.login('applicant2@institution2.test', 'Password123!');

    // Institution 2 attempting to view Institution 1 deficiencies -> HTTP 404
    await assert.rejects(
      async () => await api.getApplicationDeficiencies(testAppId),
      (err) => err.status === 404,
      'Must deny cross-institution deficiency access with 404 Not Found'
    );

    // Institution 2 attempting to acknowledge Institution 1 finding -> HTTP 404
    await assert.rejects(
      async () => await api.acknowledgeFinding(actionableFindingId),
      (err) => err.status === 404,
      'Must deny cross-institution finding acknowledgement with 404 Not Found'
    );

    // Re-authenticate as Institution 1
    await api.login('applicant@institution.test', 'Password123!');
  });

  // 10. Frontend Template Rendering
  await t.test('10. renderDeficiencyBridge Template Rendering', async () => {
    const mockState = {
      getCurrentUser: () => ({ role: 'INSTITUTION', email: 'applicant@institution.test' })
    };
    const html = renderDeficiencyBridge(mockState, { id: testAppId });
    assert.ok(html.includes('Deficiency Resolution Bridge'), 'Must contain view title');
    assert.ok(html.includes('btn-revalidate-application'), 'Must contain revalidation button');
    assert.ok(html.includes('deficiency-filter-tabs'), 'Must contain filter tabs');
    assert.ok(html.includes('deficiencies-list-container'), 'Must contain findings container');
    assert.ok(html.includes('deficiency-modals-container'), 'Must contain modals container');
  });
});
