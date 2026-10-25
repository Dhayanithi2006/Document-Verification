// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// P7 Regulatory Engine & Pre-Scrutiny Findings Frontend Integration Tests (tests/regulatory_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert';
import { api } from '../frontend/js/api.js';

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

test('P7 Regulatory Engine & Pre-Scrutiny Findings Frontend Integration', async (t) => {
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  let inst1Token = null;
  let testAppId = null;
  let sampleFindingId = null;

  // 1. Authenticate as Institution 1 Applicant
  await t.test('1. Authenticate as Institution 1 Applicant', async () => {
    const loginRes = await api.login('applicant@institution.test', 'Password123!');
    assert.ok(loginRes.access_token, 'Login must yield access token');
    inst1Token = loginRes.access_token;
    assert.strictEqual(api.getToken(), inst1Token);
  });

  // 2. Query Regulatory Rule Catalog via getRules
  await t.test('2. Query Regulatory Rule Catalog via api.getRules', async () => {
    const rules = await api.getRules();
    assert.ok(Array.isArray(rules), 'Rules must be returned as an array');
    assert.ok(rules.length >= 8, 'Catalogue must contain at least 8 seeded rules');

    const landRule = rules.find(r => r.rule_code === 'RULE-EOA-LAND-001');
    assert.ok(landRule, 'RULE-EOA-LAND-001 must exist in catalog');
    assert.strictEqual(landRule.is_active, true);
    assert.strictEqual(landRule.status, 'APPROVED_FOR_PROTOTYPE_USE');
    assert.ok(landRule.official_source.includes('APH') || landRule.official_source.includes('AICTE'));

    // Check draft rule (PARK-010 remains inactive draft)
    const draftRule = rules.find(r => r.rule_code === 'RULE-DRAFT-PARK-010');
    assert.ok(draftRule, 'RULE-DRAFT-PARK-010 must exist in catalog');
    assert.strictEqual(draftRule.is_active, false);
    assert.strictEqual(draftRule.status, 'DRAFT_MISSING_OFFICIAL_SOURCE');
  });

  // 3. Query Specific Rule via api.getRule
  await t.test('3. Query Specific Rule via api.getRule', async () => {
    const rule = await api.getRule('RULE-EOA-FIRE-003');
    assert.ok(rule, 'Rule details must be returned');
    assert.strictEqual(rule.rule_code, 'RULE-EOA-FIRE-003');
    assert.strictEqual(rule.category, 'MANDATORY_SAFETY_CERTIFICATE');
    assert.ok(rule.versions && rule.versions.length >= 1, 'Rule versions list must be present');
  });

  // 4. Retrieve or Create Application for Pre-Scrutiny Validation
  await t.test('4. Retrieve Application for Pre-Scrutiny Validation', async () => {
    const apps = await api.getApplications();
    assert.ok(apps.length >= 1, 'Institution must have at least one application');
    testAppId = apps[0].id;
  });

  // 5. Trigger Deterministic Pre-Scrutiny Validation Run
  await t.test('5. Trigger Validation Run via api.validateApplication', async () => {
    const valRun = await api.validateApplication(testAppId);
    assert.ok(valRun, 'Validation run record must be returned');
    assert.strictEqual(valRun.application_id, testAppId);
    assert.ok(valRun.run_number >= 1, 'Run number must be positive');
    assert.strictEqual(valRun.status, 'COMPLETED');
    assert.ok(valRun.total_checks >= 8, 'Must execute at least 8 active checks');
    assert.ok(typeof valRun.findings_summary.deficiencies === 'number');
    assert.ok(typeof valRun.findings_summary.warnings === 'number');
  });

  // 6. Retrieve Persisted Explainable Findings
  await t.test('6. Retrieve Findings via api.getApplicationFindings', async () => {
    const findingsResp = await api.getApplicationFindings(testAppId);
    assert.ok(findingsResp, 'Findings response must be returned');
    assert.strictEqual(findingsResp.application_id, testAppId);
    assert.ok(Array.isArray(findingsResp.findings), 'findings must be an array');
    assert.ok(findingsResp.findings.length >= 1, 'Must have at least 1 finding');

    const firstFinding = findingsResp.findings[0];
    sampleFindingId = firstFinding.id;
    assert.ok(firstFinding.rule_code, 'Finding must specify rule_code');
    assert.ok(firstFinding.outcome, 'Finding must specify outcome');
    assert.ok(firstFinding.explanation, 'Finding must specify explanation');
    assert.ok(firstFinding.official_source, 'Finding must cite official regulatory source');
  });

  // 7. Retrieve Individual Finding by ID
  await t.test('7. Retrieve Finding by ID via api.getFinding', async () => {
    assert.ok(sampleFindingId, 'Sample finding ID must be present');
    const finding = await api.getFinding(sampleFindingId);
    assert.strictEqual(finding.id, sampleFindingId);
    assert.strictEqual(finding.application_id, testAppId);
    assert.ok(finding.evidence, 'Evidence metadata must be included');
  });

  // 8. IDOR Isolation: Cross-Tenant Access to Findings Denied
  await t.test('8. IDOR Isolation: Cross-tenant finding access denied', async () => {
    // Switch login to Institution 2
    const inst2Login = await api.login('applicant2@institution2.test', 'Password123!');
    assert.ok(inst2Login.access_token);

    // Attempt to access Institution 1's findings
    await assert.rejects(
      async () => {
        await api.getApplicationFindings(testAppId);
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to isolate cross-institution findings');
        return true;
      }
    );

    // Attempt to trigger validation on Institution 1's application
    await assert.rejects(
      async () => {
        await api.validateApplication(testAppId);
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to prevent unauthorized foreign validation');
        return true;
      }
    );

    // Attempt to access Institution 1's finding by ID
    await assert.rejects(
      async () => {
        await api.getFinding(sampleFindingId);
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to prevent IDOR on finding IDs');
        return true;
      }
    );
  });

  // 9. RBAC: Institution User Cannot Activate Regulatory Rules
  await t.test('9. RBAC: Institution applicant cannot activate regulatory rules', async () => {
    // Institution applicant token
    await api.login('applicant@institution.test', 'Password123!');

    await assert.rejects(
      async () => {
        await api.activateRule('RULE-DRAFT-BANK-009');
      },
      (err) => {
        assert.strictEqual(err.status, 403, 'Must return 403 Forbidden for applicant attempting rule activation');
        return true;
      }
    );
  });

  // 10. Admin Can Activate Verified Regulatory Rule
  await t.test('10. RBAC: Administrator can activate draft regulatory rule', async () => {
    // Admin login
    await api.login('admin@platform.test', 'AdminPass123!');

    const actResp = await api.activateRule('RULE-DRAFT-BANK-009');
    assert.ok(actResp, 'Activation response returned');
    assert.strictEqual(actResp.is_active, true);
    assert.strictEqual(actResp.rule_code, 'RULE-DRAFT-BANK-009');
  });
});
