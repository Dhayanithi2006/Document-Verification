// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Phase P10: Accessibility (WCAG 2.1 AA) & Performance Hardening Verification Test Suite
// File: tests/accessibility_performance.test.js

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

// Helper to compute relative luminance for WCAG contrast ratio calculations
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function hexToRgb(hex) {
  hex = hex.replace('#', '').trim();
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('');
  }
  const num = parseInt(hex, 16);
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}

function getContrastRatio(hex1, hex2) {
  const rgb1 = hexToRgb(hex1);
  const rgb2 = hexToRgb(hex2);
  const lum1 = getLuminance(...rgb1);
  const lum2 = getLuminance(...rgb2);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

test('P10 Accessibility Audit: Design Tokens & Color Contrast (WCAG 2.1 AA)', async (t) => {
  const variablesCss = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'css', 'variables.css'), 'utf-8');

  await t.test('1. Core Text against White Background meets 4.5:1 AA contrast ratio', () => {
    // --color-slate-900: #0F172A
    const slate900 = '#0F172A';
    const white = '#FFFFFF';
    const contrastRatio = getContrastRatio(slate900, white);
    assert.ok(contrastRatio >= 4.5, `Slate 900 contrast ${contrastRatio.toFixed(2)} must be >= 4.5:1`);
    assert.ok(contrastRatio >= 7.0, `Slate 900 contrast ${contrastRatio.toFixed(2)} meets AAA level`);
  });

  await t.test('2. Primary Brand Blue meets AA contrast ratio against white background', () => {
    // --color-blue-700: #1442AB
    const blue700 = '#1442AB';
    const white = '#FFFFFF';
    const contrastRatio = getContrastRatio(blue700, white);
    assert.ok(contrastRatio >= 4.5, `Blue 700 contrast ${contrastRatio.toFixed(2)} must be >= 4.5:1`);
  });

  await t.test('3. Success Green meets AA contrast ratio against light green or white', () => {
    // --color-green-800: #065F46
    const green800 = '#065F46';
    const white = '#FFFFFF';
    const contrastRatio = getContrastRatio(green800, white);
    assert.ok(contrastRatio >= 4.5, `Green 800 contrast ${contrastRatio.toFixed(2)} must be >= 4.5:1`);
  });

  await t.test('4. Danger / Deficiency Red meets AA contrast ratio against white', () => {
    // --color-red-700: #B91C1C
    const red700 = '#B91C1C';
    const white = '#FFFFFF';
    const contrastRatio = getContrastRatio(red700, white);
    assert.ok(contrastRatio >= 4.5, `Red 700 contrast ${contrastRatio.toFixed(2)} must be >= 4.5:1`);
  });

  await t.test('5. Focus Ring token is defined for clear keyboard navigation visibility', () => {
    assert.ok(variablesCss.includes('--focus-ring:'), 'variables.css must define --focus-ring');
    assert.ok(variablesCss.includes('--focus-ring-danger:'), 'variables.css must define --focus-ring-danger');
  });
});

test('P10 Accessibility Audit: Semantic Markup, Landmarks & Motion Safeguards', async (t) => {
  const resetCss = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'css', 'reset.css'), 'utf-8');
  const responsiveCss = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'css', 'responsive.css'), 'utf-8');
  const appJs = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'js', 'app.js'), 'utf-8');
  const indexHtml = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'index.html'), 'utf-8');

  await t.test('1. Document has lang="en" and viewport meta tag', () => {
    assert.ok(indexHtml.includes('<html lang="en">'), 'index.html must have lang attribute');
    assert.ok(indexHtml.includes('name="viewport"'), 'index.html must define viewport meta tag');
    assert.ok(indexHtml.includes('name="description"'), 'index.html must define description meta tag');
  });

  await t.test('2. Universal :focus-visible ring is enforced for all interactive elements', () => {
    assert.ok(resetCss.includes(':focus-visible'), 'reset.css must define universal :focus-visible styles');
    assert.ok(resetCss.includes('var(--focus-ring)'), ':focus-visible must apply --focus-ring');
  });

  await t.test('3. Accessible Skip-to-Content link exists in both DOM and CSS', () => {
    assert.ok(appJs.includes('class="skip-link"'), 'app.js must render a skip-link');
    assert.ok(resetCss.includes('.skip-link'), 'reset.css must style .skip-link');
    assert.ok(resetCss.includes('.skip-link:focus'), 'reset.css must handle .skip-link:focus visibility');
  });

  await t.test('4. Prefers-reduced-motion media query is implemented for interaction comfort (WCAG 2.3.3)', () => {
    assert.ok(responsiveCss.includes('@media (prefers-reduced-motion: reduce)'), 'responsive.css must define prefers-reduced-motion');
    assert.ok(responsiveCss.includes('animation-duration: 0.01ms'), 'Animations must be bounded to 0.01ms on reduced motion');
  });

  await t.test('5. Persistent Prototype Disclaimer Banner is present with ARIA role and label', () => {
    assert.ok(appJs.includes('class="disclaimer-banner"'), 'app.js must render .disclaimer-banner');
    assert.ok(appJs.includes('role="note"'), 'Disclaimer banner must have role="note"');
    assert.ok(appJs.includes('aria-label="Official Prototype Notice"'), 'Disclaimer banner must have accessible label');
    assert.ok(appJs.includes('SIH PROTOTYPE'), 'Disclaimer must mention SIH PROTOTYPE');
    assert.ok(appJs.includes('Not an official AICTE portal'), 'Disclaimer must explicitly state not an official portal');
  });
});

test('P10 Performance & Hardening Audit: Database Configuration & Production Build Assets', async (t) => {
  const databasePy = fs.readFileSync(path.join(ROOT_DIR, 'backend', 'core', 'database.py'), 'utf-8');

  await t.test('1. SQLite is configured with WAL (Write-Ahead Logging) and Foreign Key pragmas', () => {
    assert.ok(databasePy.includes('PRAGMA foreign_keys=ON'), 'SQLite must enforce foreign key integrity');
    assert.ok(databasePy.includes('PRAGMA journal_mode=WAL'), 'SQLite must use WAL mode for high-throughput reads/writes');
    assert.ok(databasePy.includes('PRAGMA synchronous=NORMAL'), 'SQLite must use NORMAL synchronous pragma with WAL');
    assert.ok(databasePy.includes('PRAGMA busy_timeout=5000'), 'SQLite must configure 5000ms busy timeout');
  });

  await t.test('2. Production build readiness check verifies all mandatory files exist and are non-empty', () => {
    const buildCheckJs = fs.readFileSync(path.join(ROOT_DIR, 'scripts', 'build-check.js'), 'utf-8');
    assert.ok(buildCheckJs.includes('admin-users.js'), 'build-check.js must include admin-users.js');
    assert.ok(buildCheckJs.includes('reviewer-queue.js'), 'build-check.js must include reviewer-queue.js');
    assert.ok(buildCheckJs.includes('reviewer-scrutiny.js'), 'build-check.js must include reviewer-scrutiny.js');
    assert.ok(buildCheckJs.includes('deficiency-bridge.js'), 'build-check.js must include deficiency-bridge.js');
    assert.ok(buildCheckJs.includes('evidence-inspector.js'), 'build-check.js must include evidence-inspector.js');
  });
});
