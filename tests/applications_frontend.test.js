// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// P5 EoA Applications Workflow & Upload Frontend Integration Tests (tests/applications_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert';
import { api } from '../frontend/js/api.js';
import { state } from '../frontend/js/state.js';
import { renderApplicationsList, initApplicationsListView } from '../frontend/js/views/applications-list.js';
import { renderApplicationNew } from '../frontend/js/views/application-new.js';
import { renderApplicationDetail, initApplicationDetailView } from '../frontend/js/views/application-detail.js';

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

test('P5 Applications & Secure Document Upload Frontend Integration', async (t) => {
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  // 1. Authenticate as Institution Applicant
  await t.test('1. Authenticate as Institution Applicant', async () => {
    const loginRes = await api.login('applicant@institution.test', 'Password123!');
    assert.ok(loginRes.access_token, 'Login must yield access token');
    assert.strictEqual(api.getToken(), loginRes.access_token);
  });

  let createdAppId = null;

  // 2. Fetch Applications List
  await t.test('2. List Applications for Authenticated Institution', async () => {
    const apps = await api.getApplications();
    assert.ok(Array.isArray(apps), 'getApplications must return an array');
    assert.ok(apps.length >= 1, 'Should return at least the seeded demo application');
    const firstApp = apps[0];
    assert.strictEqual(firstApp.institution_id, 'inst_01');
    assert.ok(firstApp.application_number.startsWith('AICTE-EOA-'));
  });

  // 3. Create a New EoA Application
  await t.test('3. Create New EoA Application with Statutory Checklist Initialization', async () => {
    const payload = {
      application_type: 'EOA',
      academic_year: '2026-2027',
      total_intake_applied: 480,
      declared_land_acres: 6.5,
      declared_faculty_count: 42,
      declared_builtup_sqm: 9500,
      program_category: 'ENGINEERING_TECHNOLOGY'
    };

    const newApp = await api.createApplication(payload);
    assert.ok(newApp.id, 'New application must have an id');
    assert.strictEqual(newApp.status, 'DRAFT');
    assert.strictEqual(newApp.academic_year, '2026-2027');
    assert.strictEqual(newApp.total_intake_applied, 480);
    assert.strictEqual(newApp.institution_id, 'inst_01');
    createdAppId = newApp.id;

    // Verify 8 document slots initialized
    const checklist = await api.getChecklist(createdAppId);
    assert.strictEqual(checklist.total_slots, 8, 'Must initialize exactly 8 statutory slots');
    assert.strictEqual(checklist.uploaded_slots, 0, 'Initial uploaded slots must be 0');
    assert.strictEqual(checklist.pending_slots, 8, 'Initial pending slots must be 8');
    assert.strictEqual(checklist.checklist.length, 8);
  });

  // 4. Update Declared Parameters (Draft state editing)
  await t.test('4. Update Declared Parameters in Draft Application', async () => {
    assert.ok(createdAppId);
    const updated = await api.updateApplication(createdAppId, {
      total_intake_applied: 540
    });
    assert.strictEqual(updated.total_intake_applied, 540);
  });

  // 5. Upload Valid PDF Document to Checklist Slot
  await t.test('5. Upload Valid PDF Document with Magic-Byte Validation', async () => {
    assert.ok(createdAppId);

    // Create synthetic valid PDF file
    const pdfContent = '%PDF-1.4\n%âãÏÓ\n1 0 obj\n<< /Title (Land Title Deed) >>\nendobj\ntrailer\n<< >>\n%%EOF';
    const blob = new Blob([pdfContent], { type: 'application/pdf' });
    const file = new File([blob], 'Land_Title_Registered_Deed.pdf', { type: 'application/pdf' });

    const uploadRes = await api.uploadDocument(createdAppId, 'LAND_TITLE_DEED', file);
    assert.strictEqual(uploadRes.document_type, 'LAND_TITLE_DEED');
    assert.strictEqual(uploadRes.status, 'UPLOADED');
    assert.strictEqual(uploadRes.version_number, 1);
    assert.strictEqual(uploadRes.file_name, 'Land_Title_Registered_Deed.pdf');
    assert.ok(uploadRes.file_hash_sha256, 'Should compute SHA-256 hash');

    // Verify checklist reflects 1 uploaded slot
    const checklist = await api.getChecklist(createdAppId);
    assert.strictEqual(checklist.uploaded_slots, 1);
    assert.strictEqual(checklist.pending_slots, 7);

    const landDoc = checklist.checklist.find(d => d.document_type === 'LAND_TITLE_DEED');
    assert.ok(landDoc);
    assert.strictEqual(landDoc.status, 'UPLOADED');
    assert.strictEqual(landDoc.current_version.version_number, 1);
  });

  // 6. Reject Invalid Non-PDF Upload
  await t.test('6. Reject Invalid File Type (Non-PDF magic bytes)', async () => {
    assert.ok(createdAppId);

    // Malicious text file disguised as .pdf
    const fakeContent = 'This is NOT a PDF document binary.';
    const blob = new Blob([fakeContent], { type: 'application/pdf' });
    const fakeFile = new File([blob], 'fake_safety_noc.pdf', { type: 'application/pdf' });

    await assert.rejects(
      async () => {
        await api.uploadDocument(createdAppId, 'FIRE_SAFETY_NOC', fakeFile);
      },
      (err) => {
        assert.ok(err.status === 422 || err.status === 400);
        return true;
      },
      'Uploading non-PDF content must be rejected with 422'
    );
  });

  // 7. Remove Document & Reset Slot
  await t.test('7. Remove Uploaded Document and Reset Slot to PENDING', async () => {
    assert.ok(createdAppId);
    const deleteRes = await api.deleteDocument(createdAppId, 'LAND_TITLE_DEED');
    assert.strictEqual(deleteRes.status, 'PENDING');

    const checklist = await api.getChecklist(createdAppId);
    assert.strictEqual(checklist.uploaded_slots, 0);
    assert.strictEqual(checklist.pending_slots, 8);
  });

  // 8. Strict Tenant Isolation (Cross-Institution IDOR Defense)
  await t.test('8. Strict IDOR Defense: Cross-Institution Access Denied with 404', async () => {
    // Attempting to access app_9813 belonging to inst_02 while authenticated as inst_01
    await assert.rejects(
      async () => {
        await api.getApplication('app_9813');
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to mask cross-institution application existence');
        return true;
      }
    );

    await assert.rejects(
      async () => {
        await api.getChecklist('app_9813');
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 on checklist access');
        return true;
      }
    );
  });

  // 9. Semantic View Render Verification
  await t.test('9. Verify View Render Functions', () => {
    const listHtml = renderApplicationsList(state);
    assert.ok(listHtml.includes('Extension of Approval (EoA) Applications'));
    assert.ok(listHtml.includes('Start New EoA Application'));

    const newHtml = renderApplicationNew(state);
    assert.ok(newHtml.includes('Initiate Extension of Approval (EoA) Draft'));
    assert.ok(newHtml.includes('Institutional Baseline Information'));

    const detailHtml = renderApplicationDetail(state, { id: 'app_9812' });
    assert.ok(detailHtml.includes('Mandatory Statutory Document Checklist'));
    assert.ok(detailHtml.includes('1. Land Title Deed / Registered Lease Deed'));
    assert.ok(detailHtml.includes('8. Faculty Cadre & Student Roster Summary'));
  });

  // 10. Clean up session
  await api.logout();
});
