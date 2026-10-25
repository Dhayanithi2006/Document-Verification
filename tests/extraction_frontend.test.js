// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// P6 IDP Document Extraction & Evidence Frontend Integration Tests (tests/extraction_frontend.test.js)

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

test('P6 Intelligent Document Processing & Evidence Frontend Integration', async (t) => {
  api.baseUrl = 'http://127.0.0.1:3000/api/v1';

  // 1. Authenticate as Institution 1 Applicant
  await t.test('1. Authenticate as Institution Applicant', async () => {
    const loginRes = await api.login('applicant@institution.test', 'Password123!');
    assert.ok(loginRes.access_token, 'Login must yield access token');
    assert.strictEqual(api.getToken(), loginRes.access_token);
  });

  // 2. Fetch or create an application and upload a test document
  let testAppId = null;
  let testDocId = null;

  await t.test('2. Retrieve Application, Upload Document, and Initialize Slot', async () => {
    const apps = await api.getApplications();
    assert.ok(apps.length >= 1, 'Should have at least 1 application');
    testAppId = apps[0].id;

    // Upload a valid PDF file to the slot
    const pdfContent = '%PDF-1.4\n%âãÏÓ\n1 0 obj\n<< /Title (Land Title Deed) >>\nendobj\ntrailer\n<< >>\n%%EOF';
    const blob = new Blob([pdfContent], { type: 'application/pdf' });
    const file = new File([blob], 'Land_Title_Registered_Deed.pdf', { type: 'application/pdf' });
    const uploadRes = await api.uploadDocument(testAppId, 'LAND_TITLE_DEED', file);
    assert.ok(uploadRes.document_id, 'Upload must return document_id');
    testDocId = uploadRes.document_id;
  });

  // 3. Query Processing Status for Document Slot
  await t.test('3. Query Processing Status via getDocumentProcessingStatus', async () => {
    const statusResp = await api.getDocumentProcessingStatus(testDocId);
    assert.ok(statusResp, 'Status response must be returned');
    assert.strictEqual(statusResp.document_id, testDocId);
    assert.ok(typeof statusResp.status === 'string', 'Status must be a string');
  });

  // 4. Query Extracted Fields Endpoint
  await t.test('4. Query Extracted Fields via getDocumentExtractedFields', async () => {
    const fieldsResp = await api.getDocumentExtractedFields(testDocId);
    assert.ok(fieldsResp, 'Extraction result must be returned');
    assert.strictEqual(fieldsResp.document_id, testDocId);
    assert.ok(Array.isArray(fieldsResp.extracted_fields), 'extracted_fields must be an array');
  });

  // 5. Query Document Pages Endpoint
  await t.test('5. Query Document Pages via getDocumentPages', async () => {
    const pagesResp = await api.getDocumentPages(testDocId);
    assert.ok(Array.isArray(pagesResp), 'pages must be an array');
  });

  // 6. Test IDOR Tenant Isolation on Extraction Endpoints
  await t.test('6. IDOR Isolation: Cross-tenant extraction access denied', async () => {
    // Switch token to Institution 2
    const inst2Login = await api.login('applicant2@institution2.test', 'Password123!');
    assert.ok(inst2Login.access_token);

    // Attempt to access Institution 1's document extraction status
    await assert.rejects(
      async () => {
        await api.getDocumentProcessingStatus(testDocId);
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to mask existence of foreign document');
        return true;
      }
    );

    // Attempt to access Institution 1's extracted fields
    await assert.rejects(
      async () => {
        await api.getDocumentExtractedFields(testDocId);
      },
      (err) => {
        assert.strictEqual(err.status, 404, 'Must return 404 to mask existence of foreign document fields');
        return true;
      }
    );
  });
});
