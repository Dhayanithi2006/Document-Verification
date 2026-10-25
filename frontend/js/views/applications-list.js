// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Applications List (applications-list.js)
import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert } from '../components.js';
import { api } from '../api.js';

export function renderApplicationsList(state) {
  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Applications' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <h1>Extension of Approval (EoA) Applications</h1>
          <p style="color: var(--text-muted); margin-top: 4px;">
            Manage and track automated pre-scrutiny submissions across academic sessions.
          </p>
        </div>
        <div>
          <a href="#/applications/new" class="btn btn-primary" id="btn-start-new-application">
            ${icons.plus}
            <span>Start New EoA Application</span>
          </a>
        </div>
      </div>

      <!-- Application Registry Card -->
      <div class="card" id="applications-card">
        <div class="card-header">
          <div class="card-title">
            ${icons.clipboardList}
            <span id="applications-table-title">Application Registry</span>
          </div>
          <div style="font-size: var(--text-xs); color: var(--text-muted);" id="applications-status-badge">
            Connecting to verification server...
          </div>
        </div>

        <div id="applications-content-area">
          <div style="padding: var(--space-12); text-align: center;" role="status">
            <div class="spinner" style="margin: 0 auto var(--space-3);" aria-hidden="true"></div>
            <p style="color: var(--text-muted); font-size: var(--text-sm);">Loading application records from backend...</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

export async function initApplicationsListView(state, router) {
  const contentArea = document.getElementById('applications-content-area');
  const tableTitle = document.getElementById('applications-table-title');
  const statusBadge = document.getElementById('applications-status-badge');
  if (!contentArea) return;

  try {
    const applications = await api.getApplications();

    if (statusBadge) {
      statusBadge.textContent = 'Active Institution Registry';
    }

    if (!applications || applications.length === 0) {
      if (tableTitle) tableTitle.textContent = 'Application Registry (0)';
      contentArea.innerHTML = `
        <div style="padding: var(--space-12); text-align: center; max-width: 500px; margin: 0 auto;">
          <div style="font-size: 40px; color: var(--color-slate-400); margin-bottom: var(--space-3);" aria-hidden="true">
            ${icons.clipboardList}
          </div>
          <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">No EoA Applications Found</h2>
          <p style="color: var(--text-muted); font-size: var(--text-sm); margin-bottom: var(--space-6);">
            Your institution does not have any active or drafted Extension of Approval applications. Initiate a new application to upload the 8 statutory documents.
          </p>
          <a href="#/applications/new" class="btn btn-primary">
            ${icons.plus}
            <span>Create First EoA Application</span>
          </a>
        </div>
      `;
      return;
    }

    if (tableTitle) {
      tableTitle.textContent = `Application Registry (${applications.length})`;
    }

    contentArea.innerHTML = `
      <div class="table-responsive">
        <table class="data-table" id="applications-data-table">
          <thead>
            <tr>
              <th>Application No.</th>
              <th>Academic Session</th>
              <th>Status</th>
              <th>Intake Applied</th>
              <th>Created Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${applications.map(app => {
              const createdDate = app.created_at ? new Date(app.created_at).toLocaleDateString() : '—';
              const appNum = escapeHtml(app.application_number || 'AICTE-EOA-DRAFT');
              const academicYear = escapeHtml(app.academic_year || '2026-2027');
              const status = app.status || 'DRAFT';
              const intake = app.total_intake_applied || 0;

              return `
                <tr>
                  <td style="font-family: var(--font-mono); font-weight: 600;">
                    <a href="#/applications/${app.id}" class="app-link" data-id="${app.id}">${appNum}</a>
                  </td>
                  <td>${academicYear}</td>
                  <td>${renderBadge(status, status.replace(/_/g, ' '))}</td>
                  <td class="tabular-nums">${intake}</td>
                  <td>${createdDate}</td>
                  <td>
                    <a href="#/applications/${app.id}" class="btn btn-secondary btn-sm" aria-label="Open Workspace for ${appNum}">
                      <span>Open Workspace</span>
                      ${icons.chevronRight}
                    </a>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error fetching applications:', err);
    contentArea.innerHTML = `
      <div style="padding: var(--space-6);">
        ${renderAlert('danger', 'Unable to Load Applications', err.message || 'Server communication error.')}
        <div style="margin-top: var(--space-4); text-align: center;">
          <button id="btn-retry-applications" class="btn btn-secondary">
            ${icons.refresh}
            <span>Retry Loading</span>
          </button>
        </div>
      </div>
    `;

    const retryBtn = document.getElementById('btn-retry-applications');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => initApplicationsListView(state, router));
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
