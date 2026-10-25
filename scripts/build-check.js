import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');

console.log('Running frontend production build readiness check...');

const requiredFiles = [
  'index.html',
  'css/variables.css',
  'css/reset.css',
  'css/layout.css',
  'css/components.css',
  'css/views.css',
  'css/responsive.css',
  'js/icons.js',
  'js/sample-data.js',
  'js/state.js',
  'js/components.js',
  'js/router.js',
  'js/app.js',
  'js/views/dashboard.js',
  'js/views/applications-list.js',
  'js/views/application-new.js',
  'js/views/application-detail.js',
  'js/views/evidence-inspector.js',
  'js/views/deficiency-bridge.js',
  'js/views/reviewer-queue.js',
  'js/views/reviewer-scrutiny.js',
  'js/views/admin-rules.js',
  'js/views/admin-audit.js',
  'js/views/admin-users.js',
  'js/views/login.js',
  'js/views/not-found.js'
];

let missingCount = 0;
for (const relPath of requiredFiles) {
  const fullPath = path.join(frontendDir, relPath);
  if (!fs.existsSync(fullPath)) {
    console.error(`❌ Missing required file: frontend/${relPath}`);
    missingCount++;
  } else {
    const stat = fs.statSync(fullPath);
    if (stat.size === 0) {
      console.error(`❌ Empty file detected: frontend/${relPath}`);
      missingCount++;
    }
  }
}

// Verify index.html references existing stylesheets
const indexHtml = fs.readFileSync(path.join(frontendDir, 'index.html'), 'utf8');
const linkMatches = indexHtml.matchAll(/href="([^"]+\.css)"/g);
for (const match of linkMatches) {
  const cssRelPath = match[1];
  const cssFullPath = path.join(frontendDir, cssRelPath);
  if (!fs.existsSync(cssFullPath)) {
    console.error(`❌ index.html links to missing stylesheet: ${cssRelPath}`);
    missingCount++;
  }
}

// Verify index.html references existing entry script
const scriptMatches = indexHtml.matchAll(/src="([^"]+\.js)"/g);
for (const match of scriptMatches) {
  const jsRelPath = match[1];
  const jsFullPath = path.join(frontendDir, jsRelPath);
  if (!fs.existsSync(jsFullPath)) {
    console.error(`❌ index.html links to missing script: ${jsRelPath}`);
    missingCount++;
  }
}

if (missingCount === 0) {
  console.log(`✅ Production build check passed: All ${requiredFiles.length} files exist, are non-empty, and linked.`);
  process.exit(0);
} else {
  console.error(`❌ Build check failed: ${missingCount} issues found.`);
  process.exit(1);
}
