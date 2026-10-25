// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Tamper-Evident Audit Trail (frontend/js/views/admin-audit.js)

import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert } from '../components.js';
import { api } from '../api.js';

let auditFilters = {
  action: '',
  actor_role: '',
  entity_type: '',
  skip: 0,
  limit: 50,
};

export function renderAdminAudit(state) {
  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Governance' },
    { label: 'Activity Audit Trail' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <h1>Tamper-Evident System Audit Trail</h1>
          <p style="color: var(--text-muted); margin-top: 4px;">
            Immutable forensic event logging: Document uploads, SHA-256 hashes, validation triggers, submissions, and reviewer observations.
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2); align-items: center;">
          <span class="badge badge-info" style="font-size: 11px;">
            ${icons.shieldCheck}
            <span>Forensic Tamper-Evident Log</span>
          </span>
          <button id="btn-refresh-audit" class="btn btn-secondary btn-sm">
            ${icons.refresh}
            <span>Refresh</span>
          </button>
        </div>
      </div>

      ${renderAlert('info', 'Legal Auditability & Non-Repudiation Policy',
        'Every document upload, IDP extraction run, rule evaluation, corrective resubmission, and committee observation is permanently recorded in the relational audit trail with actor ID, role, IP address, and payload parameters. Historical audit rows are strictly append-only and cannot be altered or deleted.'
      )}

      <!-- Audit Filters -->
      <div class="card" style="margin-bottom: var(--space-6);">
        <div class="card-body" style="display: flex; gap: var(--space-4); flex-wrap: wrap; align-items: center; padding: var(--space-4);">
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);" for="audit-filter-action">Action:</label>
            <select id="audit-filter-action" class="form-control form-control-sm" style="min-width: 180px;">
              <option value="">All Actions</option>
              <option value="USER_LOGIN_SUCCESS">USER_LOGIN_SUCCESS</option>
              <option value="APPLICATION_CREATED">APPLICATION_CREATED</option>
              <option value="DOCUMENT_UPLOADED">DOCUMENT_UPLOADED</option>
              <option value="VALIDATION_RUN_COMPLETED">VALIDATION_RUN_COMPLETED</option>
              <option value="DEFICIENCY_ACKNOWLEDGED">DEFICIENCY_ACKNOWLEDGED</option>
              <option value="DEFICIENCY_CORRECTION_SUBMITTED">DEFICIENCY_CORRECTION_SUBMITTED</option>
              <option value="APPLICATION_REVIEWER_ASSIGNED">APPLICATION_REVIEWER_ASSIGNED</option>
              <option value="REVIEWER_OBSERVATION_RECORDED">REVIEWER_OBSERVATION_RECORDED</option>
              <option value="PRE_SCRUTINY_REVIEW_COMPLETED">PRE_SCRUTINY_REVIEW_COMPLETED</option>
            </select>
          </div>

          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);" for="audit-filter-role">Actor Role:</label>
            <select id="audit-filter-role" class="form-control form-control-sm" style="min-width: 140px;">
              <option value="">All Roles</option>
              <option value="INSTITUTION">INSTITUTION</option>
              <option value="REVIEWER">REVIEWER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>

          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);" for="audit-filter-entity">Entity Type:</label>
            <select id="audit-filter-entity" class="form-control form-control-sm" style="min-width: 140px;">
              <option value="">All Entities</option>
              <option value="APPLICATION">APPLICATION</option>
              <option value="DOCUMENT">DOCUMENT</option>
              <option value="FINDING">FINDING</option>
              <option value="USER">USER</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Audit Events Table Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            ${icons.history}
            <span id="audit-events-title">Audit Event Stream</span>
          </div>
        </div>
        <div id="audit-table-container">
          <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
            <span class="spinner" aria-hidden="true"></span>
            <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading forensic audit log from database...</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

export async function initAdminAuditView(state) {
  const container = document.getElementById('audit-table-container');
  if (!container) return;

  async function loadAuditData() {
    container.innerHTML = `
      <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
        <span class="spinner" aria-hidden="true"></span>
        <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Querying audit log...</p>
      </div>
    `;

    try {
      const params = {
        action: auditFilters.action || undefined,
        actor_role: auditFilters.actor_role || undefined,
        entity_type: auditFilters.entity_type || undefined,
        skip: auditFilters.skip,
        limit: auditFilters.limit,
      };

      const events = await api.getAdminAuditEvents(params);
      renderAuditTable(events);
    } catch (err) {
      container.innerHTML = `
        <div style="padding: var(--space-6); text-align: center; color: var(--color-red-600);">
          <p style="font-weight: 600;">Failed to load audit events: ${err.message}</p>
          <button class="btn btn-secondary btn-sm" id="btn-retry-audit" style="margin-top: var(--space-3);">Retry</button>
        </div>
      `;
      document.getElementById('btn-retry-audit')?.addEventListener('click', loadAuditData);
    }
  }

  function renderAuditTable(events) {
    const titleEl = document.getElementById('audit-events-title');
    if (titleEl) {
      titleEl.textContent = `Audit Event Stream (${events.length} Events Logged)`;
    }

    if (!events || events.length === 0) {
      container.innerHTML = `
        <div style="padding: var(--space-8); text-align: center; color: var(--text-muted);">
          <p style="font-weight: 600;">No audit events match the selected criteria.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Actor</th>
              <th>Action Type</th>
              <th>Entity</th>
              <th>IP Address</th>
              <th>Forensic Payload Details</th>
            </tr>
          </thead>
          <tbody>
            ${events.map(evt => {
              let cleanPayload = evt.payload_json;
              try {
                const parsed = JSON.parse(evt.payload_json);
                cleanPayload = JSON.stringify(parsed, null, 2);
              } catch {
                // leave as is
              }

              return `
                <tr>
                  <td style="font-family: var(--font-mono); font-size: 11px; white-space: nowrap;">
                    ${new Date(evt.created_at).toISOString().replace('T', ' ').slice(0, 19)}
                  </td>
                  <td>
                    <div style="font-weight: 600; font-size: 12px;">${evt.actor_email || evt.actor_user_id.slice(0, 10)}</div>
                    <span class="badge ${evt.actor_role === 'ADMIN' ? 'badge-deficiency' : evt.actor_role === 'REVIEWER' ? 'badge-info' : 'badge-secondary'}" style="font-size: 9px; padding: 1px 5px;">
                      ${evt.actor_role}
                    </span>
                  </td>
                  <td>
                    <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--color-blue-800);">
                      ${evt.action}
                    </span>
                  </td>
                  <td style="font-family: var(--font-mono); font-size: 11px;">
                    <div>${evt.entity_type}</div>
                    <span style="color: var(--text-muted); font-size: 10px;">${evt.entity_id ? evt.entity_id.slice(0, 8) : 'N/A'}</span>
                  </td>
                  <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">
                    ${evt.ip_address}
                  </td>
                  <td style="font-size: 11px; max-width: 340px;">
                    <details>
                      <summary style="cursor: pointer; color: var(--color-blue-600); font-weight: 500;">View Payload JSON</summary>
                      <pre style="background: #f8fafc; border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: 6px; font-size: 10px; max-height: 120px; overflow-y: auto; margin-top: 4px;">${cleanPayload}</pre>
                    </details>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  // Filter Bindings
  document.getElementById('audit-filter-action')?.addEventListener('change', (e) => {
    auditFilters.action = e.target.value;
    loadAuditData();
  });
  document.getElementById('audit-filter-role')?.addEventListener('change', (e) => {
    auditFilters.actor_role = e.target.value;
    loadAuditData();
  });
  document.getElementById('audit-filter-entity')?.addEventListener('change', (e) => {
    auditFilters.entity_type = e.target.value;
    loadAuditData();
  });
  document.getElementById('btn-refresh-audit')?.addEventListener('click', loadAuditData);

  // Initial load
  await loadAuditData();
}
