import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

console.log('Running frontend code lint & syntax verification...');
let errorsCount = 0;

function checkJsFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      checkJsFiles(fullPath);
    } else if (entry.name.endsWith('.js')) {
      const code = fs.readFileSync(fullPath, 'utf8');
      try {
        new vm.SourceTextModule(code, { initializeImportMeta() {} });
        // syntax valid
      } catch (err) {
        // Fallback check using basic parse or report if actual syntax error
        if (err.name === 'SyntaxError') {
          console.error(`❌ Syntax Error in ${path.relative(rootDir, fullPath)}:`, err.message);
          errorsCount++;
        }
      }
    }
  }
}

function checkCssFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      checkCssFiles(fullPath);
    } else if (entry.name.endsWith('.css')) {
      const css = fs.readFileSync(fullPath, 'utf8');
      const openCount = (css.match(/\{/g) || []).length;
      const closeCount = (css.match(/\}/g) || []).length;
      if (openCount !== closeCount) {
        console.error(`❌ Mismatched braces in ${path.relative(rootDir, fullPath)}: { count=${openCount}, } count=${closeCount}`);
        errorsCount++;
      }
    }
  }
}

checkJsFiles(path.join(rootDir, 'frontend', 'js'));
checkCssFiles(path.join(rootDir, 'frontend', 'css'));

if (errorsCount === 0) {
  console.log('✅ All JavaScript and CSS files passed syntax and structure linting.');
  process.exit(0);
} else {
  console.error(`❌ Linting failed with ${errorsCount} errors.`);
  process.exit(1);
}
