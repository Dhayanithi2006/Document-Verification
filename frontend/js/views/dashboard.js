// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Dashboard (dashboard.js)
import { icons } from '../icons.js';
import { renderBreadcrumbs, renderStatCard, renderBadge, renderAlert } from '../components.js';
import { syntheticApplications, syntheticAuditEvents } from '../sample-data.js';

export function renderDashboard(state) {
  const user = state.getCurrentUser();
  const app = syntheticApplications[0];

  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Dashboard' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <h1>Institution Pre-Scrutiny Dashboard</h1>
          <p style="color: var(--text-muted); margin-top: 4px;">
            AICTE Extension of Approval (EoA) • Academic Session 2026-2027
          </p>
        </div>
        <div style="display: flex; gap: var(--space-3);">
          <a href="#/applications/app_9812/deficiencies" class="btn btn-danger">
            ${icons.alertTriangle}
            <span>Resolve 2 Deficiencies</span>
          </a>
          <a href="#/applications/new" class="btn btn-secondary">
            ${icons.plus}
            <span>New Application</span>
          </a>
        </div>
      </div>

      <!-- Government Notice Banner -->
      ${renderAlert('warning', 'Action Required: Pre-Scrutiny Identified 2 Discrepancies', 
        'Automated pre-scrutiny identified compliance discrepancies in your Fire Safety Certificate and Land Use Conversion Order. Please submit corrected document versions before the AICTE submission deadline (30th November 2026).'
      )}

      <!-- KPI Summary Cards -->
      <div class="stats-grid">
        ${renderStatCard('Pre-Scrutiny Score', `${app.preScrutinyScore}%`, 'Automated compliance index', 'shieldCheck')}
        ${renderStatCard('Mandatory Documents', `${app.summary.uploadedCount} / ${app.summary.totalDocuments}`, 'All 8 required files uploaded', 'document')}
        ${renderStatCard('Critical Deficiencies', `${app.summary.deficienciesCount}`, 'Blocking items requiring correction', 'alertCircle')}
        ${renderStatCard('Advisory Warnings', `${app.summary.warningsCount}`, 'FSR ratio compliance warning', 'scale')}
      </div>

      <!-- Active Application Banner Card -->
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">
              <span>Application #${app.applicationNumber}</span>
              ${renderBadge(app.status, 'FINDINGS AVAILABLE')}
            </div>
            <div class="card-subtitle">${app.institutionName} • ${app.applicationType}</div>
          </div>
          <div>
            <a href="#/applications/${app.id}" class="btn btn-primary btn-sm">
              <span>Open Document Workspace</span>
              ${icons.chevronRight}
            </a>
          </div>
        </div>
        <div class="card-body">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4); margin-bottom: var(--space-4);">
            <div>
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Sanctioned Intake Applied</div>
              <div style="font-size: var(--text-lg); font-weight: bold; color: var(--text-primary);">${app.totalIntakeApplied} Students</div>
            </div>
            <div>
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Approval Category</div>
              <div style="font-size: var(--text-base); font-weight: 600; color: var(--text-primary);">Under-Graduate Engineering</div>
            </div>
            <div>
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Checklist Readiness</div>
              <div style="font-size: var(--text-base); font-weight: 600; color: var(--color-green-700);">8 / 8 Uploaded (100%)</div>
            </div>
            <div>
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Deficiency Bridge</div>
              <div style="font-size: var(--text-base); font-weight: 600; color: var(--color-red-600);">2 Open Deficiencies</div>
            </div>
          </div>

          <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-4);">
            <div style="display: flex; justify-content: space-between; font-size: var(--text-xs); font-weight: 600; margin-bottom: var(--space-2);">
              <span>AICTE Compliance Readiness Score</span>
              <span>${app.preScrutinyScore}%</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill warning" style="width: ${app.preScrutinyScore}%;"></div>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: var(--space-2);">
              Target: 100% compliant before formal AICTE Scrutiny Committee hearing. Uploading corrected certificates will recalculate this index automatically.
            </div>
          </div>
        </div>
        <div class="card-footer">
          <span style="font-size: var(--text-xs); color: var(--text-muted);">Last automated validation run: 24th Oct 2026, 08:35 AM</span>
          <a href="#/applications/app_9812/deficiencies" class="btn btn-secondary btn-sm">
            <span>View All Deficiencies (${app.summary.deficienciesCount})</span>
          </a>
        </div>
      </div>

      <!-- Recent Audit & System Activity -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            ${icons.history}
            <span>Recent Pre-Scrutiny Activity Log</span>
          </div>
          <a href="#/admin/audit" class="btn btn-ghost btn-sm">View Full Audit Trail</a>
        </div>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Target Document / Entity</th>
                <th>Actor & Role</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              ${syntheticAuditEvents.slice(0, 4).map(evt => `
                <tr>
                  <td style="font-family: var(--font-mono); font-size: 12px;">${evt.timestamp}</td>
                  <td>${renderBadge('INFO', evt.action)}</td>
                  <td style="font-weight: 500;">${evt.entity}</td>
                  <td>${evt.actor}</td>
                  <td style="color: var(--text-muted); font-size: 12px;">${evt.details}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}
