// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Frontend Environment Isolation Safety Guard Test (tests/isolation_guard_frontend.test.js)

import test from 'node:test';
import assert from 'node:assert/strict';
import { assertIsolatedTestEnvironment } from './helpers/test-env-guard.js';

test('Environment Isolation Safety Guard', async (t) => {
  await t.test('1. Blocks execution if connected backend targets live demo database (aicte.db)', async () => {
    // Port 8000 is currently running live dev backend backed by data/aicte.db
    await assert.rejects(
      async () => {
        await assertIsolatedTestEnvironment('http://127.0.0.1:8000/api/v1');
      },
      (err) => {
        assert.ok(
          err.message.includes('CRITICAL SAFETY GUARD ACTIVATED'),
          `Error must be the critical safety guard, got: ${err.message}`
        );
        assert.ok(
          err.message.includes('aicte.db'),
          `Error must identify aicte.db, got: ${err.message}`
        );
        return true;
      }
    );
  });
});
