// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: 404 Not Found (not-found.js)
import { icons } from '../icons.js';
import { renderEmptyState } from '../components.js';

export function renderNotFound(state) {
  return `
    <div class="content-container" style="display: flex; align-items: center; justify-content: center; min-height: 480px;">
      <div style="max-width: 500px; width: 100%;">
        ${renderEmptyState(
          'alertTriangle',
          '404 — Page Not Found',
          'The requested e-governance route does not exist or has been moved. Please verify the URL or return to the main dashboard.',
          '<a href="#/dashboard" class="btn btn-primary">Return to Dashboard</a>'
        )}
      </div>
    </div>
  `;
}
