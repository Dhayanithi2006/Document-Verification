import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');

// Import modules to test
import { state } from '../frontend/js/state.js';
import { Router } from '../frontend/js/router.js';
import { syntheticApplications, syntheticChecklist, syntheticFindings, syntheticRules } from '../frontend/js/sample-data.js';
import { renderDashboard } from '../frontend/js/views/dashboard.js';
import { renderApplicationsList } from '../frontend/js/views/applications-list.js';
import { renderApplicationNew } from '../frontend/js/views/application-new.js';
import { renderApplicationDetail } from '../frontend/js/views/application-detail.js';
import { renderEvidenceInspector } from '../frontend/js/views/evidence-inspector.js';
import { renderDeficiencyBridge } from '../frontend/js/views/deficiency-bridge.js';
import { renderReviewerQueue } from '../frontend/js/views/reviewer-queue.js';
import { renderReviewerScrutiny } from '../frontend/js/views/reviewer-scrutiny.js';
import { renderAdminRules } from '../frontend/js/views/admin-rules.js';
import { renderAdminAudit } from '../frontend/js/views/admin-audit.js';
import { renderLogin } from '../frontend/js/views/login.js';
import { renderNotFound } from '../frontend/js/views/not-found.js';

test('1. Design Tokens: variables.css defines all required design tokens', () => {
  const css = fs.readFileSync(path.join(frontendDir, 'css', 'variables.css'), 'utf8');
  const requiredTokens = [
    '--color-navy-900',
    '--color-blue-600',
    '--color-saffron-500',
    '--color-green-600',
    '--color-red-600',
    '--color-slate-900',
    '--font-sans',
    '--font-mono',
    '--focus-ring',
    '--radius-md',
    '--shadow-sm',
    '--space-4'
  ];

  for (const token of requiredTokens) {
    assert.ok(css.includes(token), `Missing design token in variables.css: ${token}`);
  }
});

test('2. Layout: Mandatory disclaimer banner and accessibility elements exist in app.js and CSS', () => {
  const layoutCss = fs.readFileSync(path.join(frontendDir, 'css', 'layout.css'), 'utf8');
  assert.ok(layoutCss.includes('.disclaimer-banner'), 'Missing .disclaimer-banner in layout.css');
  assert.ok(layoutCss.includes('.app-header'), 'Missing .app-header in layout.css');
  assert.ok(layoutCss.includes('.app-sidebar'), 'Missing .app-sidebar in layout.css');

  const appJs = fs.readFileSync(path.join(frontendDir, 'js', 'app.js'), 'utf8');
  assert.ok(appJs.includes('SIH PROTOTYPE'), 'Missing SIH Prototype badge in app.js');
  assert.ok(appJs.includes('Skip to main government content'), 'Missing accessibility skip-link in app.js');
});

test('3. Router Pattern Matching: All 11 routes resolve and parse parameters correctly', () => {
  // Mock DOM environment for Router test
  const router = new Router(state, 'dummy-id');

  const testCases = [
    { path: '/dashboard', expectedView: renderDashboard },
    { path: '/applications', expectedView: renderApplicationsList },
    { path: '/applications/new', expectedView: renderApplicationNew },
    { path: '/applications/app_9812', expectedView: renderApplicationDetail, expectedParams: { id: 'app_9812' } },
    { path: '/applications/app_9812/evidence/find_0042', expectedView: renderEvidenceInspector, expectedParams: { id: 'app_9812', finding_id: 'find_0042' } },
    { path: '/applications/app_9812/deficiencies', expectedView: renderDeficiencyBridge, expectedParams: { id: 'app_9812' } },
    { path: '/reviewer/queue', expectedView: renderReviewerQueue },
    { path: '/reviewer/scrutiny/app_9812', expectedView: renderReviewerScrutiny, expectedParams: { id: 'app_9812' } },
    { path: '/admin/rules', expectedView: renderAdminRules },
    { path: '/admin/audit', expectedView: renderAdminAudit },
    { path: '/login', expectedView: renderLogin }
  ];

  for (const tc of testCases) {
    let matched = false;
    for (const r of router.routes) {
      const match = tc.path.match(r.pattern);
      if (match) {
        matched = true;
        assert.strictEqual(r.view, tc.expectedView, `Route ${tc.path} mapped to unexpected view`);
        if (tc.expectedParams) {
          const params = {};
          r.paramNames.forEach((name, i) => {
            params[name] = match[i + 1];
          });
          assert.deepStrictEqual(params, tc.expectedParams, `Route ${tc.path} extracted incorrect params`);
        }
        break;
      }
    }
    assert.ok(matched, `Route ${tc.path} failed to match any router pattern`);
  }
});

test('4. Primary USP: Evidence Inspector renders split-screen layout with visual bounding box', () => {
  const html = renderEvidenceInspector(state, { id: 'app_9812', finding_id: 'find_0042' });
  assert.ok(html.includes('Split-Screen Regulatory Evidence Inspector'), 'Missing evidence inspector title');
  assert.ok(html.includes('bounding-box-highlight'), 'Missing bounding-box-highlight element');
  assert.ok(html.includes('find_0042'), 'Missing finding ID');
  assert.ok(html.includes('RULE-EOA-CROSS-006'), 'Missing rule code');
  assert.ok(html.includes('mock-pdf-page'), 'Missing mock PDF page container');
});

test('5. Statutory Checklist: 8 mandatory documents are present in sample data and detail view', () => {
  assert.strictEqual(syntheticChecklist.length, 8, 'Checklist must contain exactly 8 mandatory documents');
  
  const docTypes = syntheticChecklist.map(d => d.documentType);
  const expectedTypes = [
    'LAND_TITLE_DEED',
    'LAND_USE_CERTIFICATE',
    'APPROVED_BUILDING_PLAN',
    'BUILDING_COMPLETION',
    'FIRE_SAFETY_NOC',
    'STRUCTURAL_STABILITY',
    'PREV_AICTE_APPROVAL',
    'FACULTY_ROSTER'
  ];
  assert.deepStrictEqual(docTypes, expectedTypes, 'Checklist documents do not match the 8 mandatory EoA types');

  const html = renderApplicationDetail(state, { id: 'app_9812' });
  for (const doc of syntheticChecklist) {
    assert.ok(html.includes(doc.title), `Application detail view missing document: ${doc.title}`);
  }
});

test('6. State & Role Preview Management: Switching role updates active profile', () => {
  state.setRole('INSTITUTION');
  assert.strictEqual(state.activeRole, 'INSTITUTION');
  assert.strictEqual(state.getCurrentUser().name, 'Dr. R. K. Sharma');

  state.setRole('REVIEWER');
  assert.strictEqual(state.activeRole, 'REVIEWER');
  assert.strictEqual(state.getCurrentUser().name, 'Prof. K. S. Krishnan');

  state.setRole('ADMIN');
  assert.strictEqual(state.activeRole, 'ADMIN');
  assert.strictEqual(state.getCurrentUser().name, 'Platform Administrator');

  // Reset back to INSTITUTION
  state.setRole('INSTITUTION');
});

test('7. View Controllers: All 12 views return non-empty valid HTML', () => {
  const views = [
    renderDashboard(state),
    renderApplicationsList(state),
    renderApplicationNew(state),
    renderApplicationDetail(state, { id: 'app_9812' }),
    renderEvidenceInspector(state, { id: 'app_9812', finding_id: 'find_0042' }),
    renderDeficiencyBridge(state, { id: 'app_9812' }),
    renderReviewerQueue(state),
    renderReviewerScrutiny(state, { id: 'app_9812' }),
    renderAdminRules(state),
    renderAdminAudit(state),
    renderLogin(state),
    renderNotFound(state)
  ];

  for (let i = 0; i < views.length; i++) {
    const v = views[i];
    assert.ok(typeof v === 'string' && v.length > 50, `View #${i} returned empty or invalid string`);
  }
});
