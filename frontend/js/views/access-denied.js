// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: 403 Role-Based Access Denied (access-denied.js)
import { icons } from '../icons.js';

export function renderAccessDenied(state, params = {}) {
  const user = state.getCurrentUser();
  const currentRole = state.activeRole;
  const targetSection = params?.targetSection || 'this restricted section';

  // Determine safe home route for current role
  let homeRoute = '#/dashboard';
  if (currentRole === 'REVIEWER') homeRoute = '#/reviewer/queue';
  else if (currentRole === 'ADMIN') homeRoute = '#/admin/rules';

  return `
    <div class="access-denied-container">
      <div class="card access-denied-card">
        <div style="width: 64px; height: 64px; margin: 0 auto var(--space-4); background-color: var(--color-red-50); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--color-red-600);">
          ${icons.shieldCheck}
        </div>

        <h1 style="font-size: var(--text-2xl); font-weight: var(--font-bold); color: var(--color-navy-900); margin-bottom: var(--space-2);">
          403 — Access Denied
        </h1>

        <p style="font-size: var(--text-base); color: var(--text-secondary); margin-bottom: var(--space-4);">
          You do not have administrative or committee authorization to access ${escapeHtml(targetSection)}.
        </p>

        <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-6); text-align: left; font-size: var(--text-xs);">
          <div style="margin-bottom: var(--space-2);">
            <strong>Authenticated Account:</strong> ${escapeHtml(user?.name || user?.email || 'Authenticated User')}
          </div>
          <div style="margin-bottom: var(--space-2);">
            <strong>Assigned Role:</strong> <span class="badge badge-info">${escapeHtml(currentRole)}</span>
          </div>
          <div style="color: var(--text-muted);">
            Access control policies are strictly enforced server-side. Institutional applicants, scrutiny committee reviewers, and administrators are isolated to their permitted workspaces.
          </div>
        </div>

        <div style="display: flex; justify-content: center; gap: var(--space-4);">
          <a href="${homeRoute}" class="btn btn-primary">
            ${icons.chevronRight}
            <span>Return to Permitted Workspace</span>
          </a>
          <button type="button" class="btn btn-secondary" onclick="window.history.back();">
            Go Back
          </button>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
