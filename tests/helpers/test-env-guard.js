// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Environment Isolation & Database Pollution Safety Guard (tests/helpers/test-env-guard.js)

/**
 * Asserts that the target API backend is running in an isolated test environment
 * backed by a dedicated test database (e.g. test_frontend.db) and NOT the live demonstration database.
 * Throws a fatal safety error if the connected backend is pointed at a demo database.
 * 
 * @param {string} baseUrl - Target API base URL (e.g., 'http://127.0.0.1:3000/api/v1')
 * @returns {Promise<Object>} Readiness diagnostics
 */
export async function assertIsolatedTestEnvironment(baseUrl) {
  const rootUrl = baseUrl.replace(/\/api\/v1\/?$/, '');
  const healthUrl = `${rootUrl}/api/v1/health/readiness`;

  try {
    const res = await fetch(healthUrl);
    if (!res.ok) {
      throw new Error(`Health probe returned HTTP ${res.status}`);
    }
    const data = await res.json();

    const dbName = (data.database_name || '').toLowerCase();
    const isLiveDemo = dbName.includes('aicte.db') || dbName.includes('demo.db');

    if (data.is_isolated_test_db === false || isLiveDemo) {
      throw new Error(
        `\n================================================================================\n` +
        `[CRITICAL SAFETY GUARD ACTIVATED: ENVIRONMENT ISOLATION ENFORCEMENT]\n` +
        `Integration tests are strictly forbidden from running against demonstration database '${data.database_name}'!\n` +
        `Running tests against demo databases causes state pollution, uncheckpointed WAL bloat, and test artifact corruption.\n` +
        `RESOLUTION:\n` +
        `  1. Start the isolated test backend: python scripts/run-backend-test.py (runs on port 8001 with data/test_frontend.db)\n` +
        `  2. Or run tests with: TEST_API_URL=http://127.0.0.1:8001/api/v1 npm test\n` +
        `================================================================================\n`
      );
    }

    return data;
  } catch (err) {
    if (err.message.includes('CRITICAL SAFETY GUARD ACTIVATED')) {
      throw err;
    }
    throw new Error(`Failed to verify test environment isolation at ${healthUrl}: ${err.message}`);
  }
}
