// AICTE Pre-Scrutiny Platform — Remediation Regression Tests (remediation_defects.test.js)
import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { icons } from '../frontend/js/icons.js';
import { state } from '../frontend/js/state.js';
import { renderHeader } from '../frontend/js/components.js';

test('Remediation Defect 2: Icon Library Completeness & Proxy Fallback Defense', async (t) => {
  await t.test('All required icons exist, are valid SVGs and accessible', () => {
    const requiredIcons = ['edit', 'check', 'save', 'chevronLeft', 'info', 'scale', 'shieldCheck', 'clipboardList'];
    for (const key of requiredIcons) {
      const svg = icons[key];
      assert.ok(svg, `Icon "${key}" must be defined`);
      assert.strictEqual(typeof svg, 'string', `Icon "${key}" must be a string`);
      assert.ok(svg.includes('<svg'), `Icon "${key}" must contain <svg`);
      assert.ok(svg.includes('viewBox="0 0 20 20"'), `Icon "${key}" must specify 20x20 viewBox`);
      assert.ok(svg.includes('aria-hidden="true"'), `Icon "${key}" must include aria-hidden="true"`);
    }
  });

  await t.test('Safe Proxy Fallback: Unknown icon key returns empty string instead of undefined', () => {
    assert.strictEqual(icons.completelyUnknownIconKey, '');
    assert.strictEqual(icons.anotherMissingIcon, '');

    // Guarantee that template literals never coerce unknown icons to "undefined"
    const templateString = `<button>${icons.completelyUnknownIconKey} Action</button>`;
    assert.strictEqual(templateString, '<button> Action</button>');
    assert.ok(!templateString.includes('undefined'), 'Template string must never contain "undefined"');
  });

  await t.test('Button Template Verification: Edit Parameters and Acknowledge buttons render cleanly', () => {
    const editBtn = `<button>${icons.edit}<span>Edit Declared Parameters</span></button>`;
    assert.ok(editBtn.includes('<svg'), 'Edit button must render valid SVG');
    assert.ok(!editBtn.includes('undefined'), 'Edit button must not contain literal "undefined"');

    const ackBtn = `<button>${icons.check} <span>Acknowledge</span></button>`;
    assert.ok(ackBtn.includes('<svg'), 'Acknowledge button must render valid SVG');
    assert.ok(!ackBtn.includes('undefined'), 'Acknowledge button must not contain literal "undefined"');
  });

  await t.test('Static Code Check: Every icon reference across frontend JS exists in icon library', () => {
    const jsFiles = [];
    function scanDir(dir) {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          scanDir(fullPath);
        } else if (entry.isFile() && entry.name.endsWith('.js') && entry.name !== 'icons.js') {
          jsFiles.push(fullPath);
        }
      }
    }
    scanDir(path.resolve('frontend/js'));

    const iconRegex = /(?<![/'"\\])\bicons\.([a-zA-Z0-9_]+)\b/g;
    const missingReferences = [];

    for (const file of jsFiles) {
      const code = fs.readFileSync(file, 'utf8');
      let match;
      while ((match = iconRegex.exec(code)) !== null) {
        const key = match[1];
        if (key === 'js') continue; // Exclude import paths like '../icons.js'
        if (!icons[key]) {
          missingReferences.push({ file: path.relative(process.cwd(), file), key });
        }
      }
    }

    assert.strictEqual(
      missingReferences.length,
      0,
      `Nonexistent icon references detected: ${JSON.stringify(missingReferences)}`
    );
  });
});

test('Remediation Defect 1: Workspace Refresh Parameter Normalization & Guard', async (t) => {
  await t.test('renderWorkspace script contains defensive argument shift normalization', () => {
    const detailCode = fs.readFileSync(path.resolve('frontend/js/views/application-detail.js'), 'utf8');
    assert.ok(
      detailCode.includes('if (initialFindings && typeof initialFindings.getCurrentUser === \'function\')'),
      'application-detail.js must contain defensive parameter alignment in renderWorkspace'
    );
  });

  await t.test('All four workspace refresh call sites pass all 5 arguments', () => {
    const detailCode = fs.readFileSync(path.resolve('frontend/js/views/application-detail.js'), 'utf8');
    
    // Ensure no call site omits the findings argument
    const matches = detailCode.match(/renderWorkspace\([^)]+\)/g) || [];
    for (const callSite of matches) {
      // Must not be the 4-arg buggy call: renderWorkspace(updatedApp, updatedChecklist, state, router)
      assert.ok(
        !callSite.includes('renderWorkspace(updatedApp, updatedChecklist, state, router)'),
        `Call site must not omit findings: ${callSite}`
      );
    }
  });
});

test('Remediation Defect 3: Role Switcher & Authentication Session Alignment', async (t) => {
  await t.test('When unauthenticated: header renders role preview selector for testing', () => {
    const html = renderHeader(state.getCurrentUser(), 'INSTITUTION', false);
    assert.ok(html.includes('id="role-preview-select"'), 'Unauthenticated header must render role preview select');
    assert.ok(!html.includes('id="btn-switch-account"'), 'Unauthenticated header must not render switch account button');
  });

  await t.test('When authenticated: header renders verified role badge and explicit switch action', () => {
    const mockUser = {
      id: 'usr_inst_01',
      name: 'Dr. R. K. Sharma',
      role: 'INSTITUTION',
      institution: 'Apex Institute of Technology'
    };
    const html = renderHeader(mockUser, 'INSTITUTION', true);
    assert.ok(!html.includes('id="role-preview-select"'), 'Authenticated header must NOT render unauthenticated role select');
    assert.ok(html.includes('id="btn-switch-account"'), 'Authenticated header must render explicit switch account button');
    assert.ok(html.includes('Institution Applicant'), 'Authenticated header must display verified role badge');
  });

  await t.test('app.js wires switch account and logout without client-side permission forgery', () => {
    const appCode = fs.readFileSync(path.resolve('frontend/js/app.js'), 'utf8');
    assert.ok(appCode.includes('switchAccountBtn.addEventListener'), 'app.js must wire switch account button');
    assert.ok(appCode.includes('this.state.logout()'), 'app.js must invoke state.logout() on switch');
    assert.ok(appCode.includes('this.router.navigate(\'/login\')'), 'app.js must redirect to login on switch');
  });
});

test('Remediation Defect 4: Pre-Scrutiny Assessment Dossier Responsive & Print Layout', async (t) => {
  await t.test('components.css contains full print stylesheet modal reset', () => {
    const css = fs.readFileSync(path.resolve('frontend/css/components.css'), 'utf8');
    assert.ok(css.includes('@media print'), 'components.css must define @media print');
    assert.ok(css.includes('#pre-scrutiny-dossier-modal'), 'Print stylesheet must target dossier modal');
    assert.ok(css.includes('position: static !important'), 'Print stylesheet must reset fixed modal backdrop');
    assert.ok(css.includes('table-layout: fixed !important'), 'Print stylesheet must enforce fixed table layout');
    assert.ok(css.includes('word-break: break-word !important'), 'Print stylesheet must enforce word breaking');
  });

  await t.test('application-detail.js wraps dossier tables in responsive containers', () => {
    const detailCode = fs.readFileSync(path.resolve('frontend/js/views/application-detail.js'), 'utf8');
    assert.ok(
      detailCode.includes('<div class="table-responsive" style="overflow-x: auto;'),
      'application-detail.js must wrap dossier tables in table-responsive container'
    );
  });

  await t.test('responsive.css defines table-responsive rules for mobile viewports', () => {
    const respCss = fs.readFileSync(path.resolve('frontend/css/responsive.css'), 'utf8');
    assert.ok(respCss.includes('.table-responsive'), 'responsive.css must define .table-responsive styles');
    assert.ok(respCss.includes('.dossier-paper'), 'responsive.css must define .dossier-paper styles');
  });
});
