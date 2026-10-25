// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Deficiency Resolution Bridge & Corrective Workspace (frontend/js/views/deficiency-bridge.js)

import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert, renderStatutoryGroundingModal } from '../components.js';
import { api } from '../api.js';

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function renderDeficiencyBridge(state, params) {
  const appId = params?.id || '';

  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Applications', href: '#/applications' },
    { label: `Application #${appId}`, href: `#/applications/${appId}` },
    { label: 'Deficiency Resolution Bridge' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container" id="deficiency-bridge-view" data-app-id="${escapeHtml(appId)}">
      <!-- Top Action Bar -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <div style="display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap;">
            <h1>Deficiency Resolution Bridge</h1>
            <span id="app-lifecycle-badge" class="badge badge-info" style="font-size: var(--text-xs);">Loading...</span>
          </div>
          <p style="color: var(--text-muted); margin-top: 4px;">
            Targeted remediation console: review evidence, upload updated document versions (v2/v3), submit corrective justifications, and trigger controlled regulatory revalidation.
          </p>
        </div>
        <div style="display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap;">
          <a href="#/applications/${escapeHtml(appId)}" class="btn btn-secondary btn-sm">
            ${icons.clipboardList}
            <span>Back to Checklist</span>
          </a>
          <button id="btn-revalidate-application" class="btn btn-primary btn-sm" title="Re-evaluate application documents against versioned AICTE regulatory rule catalogue">
            <span id="reval-spinner" class="spinner" style="display: none;" aria-hidden="true"></span>
            ${icons.refresh}
            <span id="reval-btn-text">Re-run Regulatory Pre-Scrutiny</span>
          </button>
        </div>
      </div>

      <!-- Advisory Guard Notice -->
      <div style="margin-bottom: var(--space-6);">
        ${renderAlert('info', 'AICTE Decision-Support & Revalidation Policy',
          'This platform provides advisory pre-scrutiny assistance. Corrective responses and document replacements (v2/v3) submitted here are automatically evaluated by the versioned regulatory engine. When an automated check clears a deficiency, the finding transitions to "Awaiting Review" for formal verification by the AICTE Scrutiny Committee. Automated revalidation does not replace authorized human reviewers or constitute official EoA approval.'
        )}
      </div>

      <!-- Revalidation Banner (dynamically populated after revalidation run) -->
      <div id="revalidation-banner-area" style="display: none; margin-bottom: var(--space-6);"></div>

      <!-- Metrics Summary Bar -->
      <div class="stats-grid" id="deficiency-metrics-bar" style="margin-bottom: var(--space-6);">
        <div class="card stat-card">
          <div class="stat-label">Actionable Findings</div>
          <div class="stat-value" id="stat-total-actionable">--</div>
          <div class="stat-subtext">Total discrepancies identified</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Acknowledged</div>
          <div class="stat-value" id="stat-acknowledged" style="color: var(--color-blue-700);">--</div>
          <div class="stat-subtext">Applicant awareness established</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Response In Progress</div>
          <div class="stat-value" id="stat-in-progress" style="color: var(--color-amber-600);">--</div>
          <div class="stat-subtext">Saved draft remediation</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Corrections Submitted</div>
          <div class="stat-value" id="stat-submitted" style="color: var(--color-indigo-600);">--</div>
          <div class="stat-subtext">Responses formally submitted</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Awaiting Review</div>
          <div class="stat-value" id="stat-awaiting-review" style="color: var(--color-teal-600);">--</div>
          <div class="stat-subtext">Condition cleared by engine</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Resolved</div>
          <div class="stat-value" id="stat-resolved" style="color: var(--color-green-600);">--</div>
          <div class="stat-subtext">Formally accepted findings</div>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="tabs-nav" id="deficiency-filter-tabs" style="margin-bottom: var(--space-6);">
        <button class="tab-btn active" data-filter="ALL">All Findings (<span id="tab-count-all">0</span>)</button>
        <button class="tab-btn" data-filter="DEFICIENCY">Critical Deficiencies (<span id="tab-count-def">0</span>)</button>
        <button class="tab-btn" data-filter="WARNING">Advisory Warnings (<span id="tab-count-warn">0</span>)</button>
        <button class="tab-btn" data-filter="IN_PROGRESS">Draft / In Progress (<span id="tab-count-prog">0</span>)</button>
        <button class="tab-btn" data-filter="AWAITING_REVIEW">Awaiting Review (<span id="tab-count-await">0</span>)</button>
      </div>

      <!-- Actionable Findings Cards Container -->
      <div id="deficiencies-list-container">
        <div style="text-align: center; padding: var(--space-12); color: var(--text-muted);">
          <span class="spinner" aria-hidden="true"></span>
          <p style="margin-top: var(--space-3); font-size: var(--text-sm);">Loading actionable findings and corrective responses from backend...</p>
        </div>
      </div>

      <!-- Modals Container (Response Console, History, Revalidation Report) -->
      <div id="deficiency-modals-container"></div>
    </div>
  `;
}

export async function initDeficiencyBridgeView(state, router, params) {
  const container = document.getElementById('deficiency-bridge-view');
  if (!container) return;

  const appId = params?.id || container.getAttribute('data-app-id');
  if (!appId) {
    container.innerHTML = renderAlert('danger', 'Invalid Application', 'Application identifier is missing.');
    return;
  }

  // Bind Revalidate Button
  const revalBtn = document.getElementById('btn-revalidate-application');
  if (revalBtn) {
    revalBtn.addEventListener('click', () => handleRevalidateApplication(appId, state));
  }

  // Load and Render Deficiency Workspace Data
  await loadDeficiencyWorkspace(appId, state);
}

let activeDeficiencies = [];
let currentFilter = 'ALL';

async function loadDeficiencyWorkspace(appId, state) {
  const listContainer = document.getElementById('deficiencies-list-container');
  if (!listContainer) return;

  try {
    const data = await api.getApplicationDeficiencies(appId);
    activeDeficiencies = data.deficiencies || [];

    // Update Status Badge
    const lifecycleBadge = document.getElementById('app-lifecycle-badge');
    if (lifecycleBadge) {
      lifecycleBadge.textContent = data.application_status.replace(/_/g, ' ');
      lifecycleBadge.className = `badge badge-${data.application_status === 'APPROVED' ? 'success' : 'info'}`;
    }

    // Update Statistics Bar
    updateStatsBar(data);

    // Render Cards Grid
    renderDeficiencyCards(activeDeficiencies, currentFilter, appId);

    // Bind Filter Tabs
    bindFilterTabs(appId);

  } catch (err) {
    console.error('Failed to load deficiencies:', err);
    listContainer.innerHTML = `
      <div style="padding: var(--space-8); text-align: center;">
        <div style="color: var(--color-red-600); font-size: 24px; margin-bottom: var(--space-2);">${icons.alertTriangle}</div>
        <h3 style="font-size: var(--text-base); margin-bottom: var(--space-2);">Failed to Load Actionable Deficiencies</h3>
        <p style="color: var(--text-muted); font-size: var(--text-sm); margin-bottom: var(--space-4);">
          ${escapeHtml(err.message || 'Unable to retrieve regulatory evaluation findings.')}
        </p>
        <button class="btn btn-secondary btn-sm" onclick="window.location.reload();">Retry</button>
      </div>
    `;
  }
}

function updateStatsBar(data) {
  const setEl = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  setEl('stat-total-actionable', data.total_deficiencies || 0);
  setEl('stat-acknowledged', data.acknowledged_count || 0);
  setEl('stat-in-progress', data.in_progress_count || 0);
  setEl('stat-submitted', data.submitted_count || 0);
  setEl('stat-awaiting-review', data.awaiting_review_count || 0);
  setEl('stat-resolved', data.resolved_count || 0);

  // Tab counts
  const items = data.deficiencies || [];
  setEl('tab-count-all', items.length);
  setEl('tab-count-def', items.filter(d => d.severity === 'DEFICIENCY').length);
  setEl('tab-count-warn', items.filter(d => d.severity === 'WARNING').length);
  setEl('tab-count-prog', items.filter(d => ['RESPONSE_IN_PROGRESS', 'CORRECTION_SUBMITTED'].includes(d.resolution_status)).length);
  setEl('tab-count-await', items.filter(d => d.resolution_status === 'AWAITING_REVIEW').length);
}

function bindFilterTabs(appId) {
  const tabsContainer = document.getElementById('deficiency-filter-tabs');
  if (!tabsContainer) return;

  tabsContainer.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      const target = e.currentTarget;
      target.classList.add('active');
      currentFilter = target.getAttribute('data-filter') || 'ALL';
      renderDeficiencyCards(activeDeficiencies, currentFilter, appId);
    });
  });
}

function renderDeficiencyCards(items, filter, appId) {
  const container = document.getElementById('deficiencies-list-container');
  if (!container) return;

  let filtered = items;
  if (filter === 'DEFICIENCY') {
    filtered = items.filter(d => d.severity === 'DEFICIENCY');
  } else if (filter === 'WARNING') {
    filtered = items.filter(d => d.severity === 'WARNING');
  } else if (filter === 'IN_PROGRESS') {
    filtered = items.filter(d => ['RESPONSE_IN_PROGRESS', 'CORRECTION_SUBMITTED'].includes(d.resolution_status));
  } else if (filter === 'AWAITING_REVIEW') {
    filtered = items.filter(d => d.resolution_status === 'AWAITING_REVIEW');
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="card" style="padding: var(--space-12); text-align: center; color: var(--text-muted);">
        <div style="font-size: 32px; color: var(--color-green-600); margin-bottom: var(--space-2);">${icons.checkCircle}</div>
        <h3 style="font-size: var(--text-base); color: var(--text-primary); margin-bottom: var(--space-1);">No Actionable Findings Available in this View</h3>
        <p style="font-size: var(--text-sm);">
          ${filter === 'ALL' 
            ? 'No discrepancies detected. If you recently updated evidence, run pre-scrutiny checks to verify compliance.'
            : `No findings currently match the "${filter}" filter criteria.`}
        </p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(d => {
    const isWarning = d.severity === 'WARNING';
    const isResolved = d.resolution_status === 'RESOLVED';
    const isAwaiting = d.resolution_status === 'AWAITING_REVIEW';
    const isSubmitted = d.resolution_status === 'CORRECTION_SUBMITTED';
    const isInProgress = d.resolution_status === 'RESPONSE_IN_PROGRESS';
    const isAcknowledged = d.resolution_status === 'ACKNOWLEDGED';

    let cardBorderClass = isWarning ? 'warning-severity' : '';
    if (isResolved || isAwaiting) cardBorderClass = 'resolved-status';

    // Status Badge Formatting
    let resBadgeColor = 'secondary';
    if (isResolved) resBadgeColor = 'success';
    else if (isAwaiting) resBadgeColor = 'info';
    else if (isSubmitted) resBadgeColor = 'primary';
    else if (isInProgress) resBadgeColor = 'warning';
    else if (isAcknowledged) resBadgeColor = 'secondary';

    const docRef = d.document_title || (d.evidence?.document_title) || 'General Application Record';
    const pageRef = d.evidence?.page_number ? `Page ${d.evidence.page_number}` : '';

    return `
      <div class="deficiency-card ${cardBorderClass}" id="card-finding-${escapeHtml(d.id)}">
        <!-- Card Header -->
        <div class="deficiency-header">
          <div>
            <span style="font-family: var(--font-mono); font-size: var(--text-xs); font-weight: bold; color: var(--color-blue-700);">
              ${escapeHtml(d.rule_code)}
            </span>
            <span style="color: var(--text-muted); font-size: var(--text-xs); margin: 0 var(--space-2);">•</span>
            <span style="font-size: var(--text-xs); font-weight: 600; color: var(--text-secondary);">
              ${escapeHtml(d.category.replace(/_/g, ' '))}
            </span>
            ${d.official_source ? `
              <span style="color: var(--text-muted); font-size: var(--text-xs); margin: 0 var(--space-2);">•</span>
              <span style="font-size: var(--text-xs); font-style: italic; color: var(--text-muted);">
                ${escapeHtml(d.official_source)}
              </span>
            ` : ''}
          </div>
          <div style="display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap;">
            ${renderBadge(d.severity, d.severity)}
            ${renderBadge(resBadgeColor, d.resolution_status.replace(/_/g, ' '))}
          </div>
        </div>

        <!-- Title -->
        <div class="deficiency-title">
          <span>${escapeHtml(d.title || d.rule_title)}</span>
        </div>

        <!-- Plain Language Explanation -->
        <p style="font-size: var(--text-sm); color: var(--text-primary); margin: var(--space-2) 0 var(--space-3) 0; line-height: 1.5;">
          ${escapeHtml(d.explanation)}
        </p>

        <!-- Values Box: Expected vs Observed -->
        <div class="deficiency-values-box">
          <div>
            <div class="val-label">Expected Statutory Norm (APH Requirement)</div>
            <div class="val-data expected">${escapeHtml(d.expected_value || 'Mandatory statutory compliance')}</div>
          </div>
          <div>
            <div class="val-label">Observed Evidence Parameter</div>
            <div class="val-data observed">${escapeHtml(d.observed_value || 'Condition absent / unverified')}</div>
          </div>
        </div>

        <!-- Recommended Remediation Box -->
        <div style="background-color: var(--color-blue-50); border-left: 3px solid var(--color-blue-600); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); margin: var(--space-3) 0; font-size: var(--text-xs); color: var(--color-blue-900);">
          <strong>Recommended Corrective Action:</strong> ${escapeHtml(d.recommended_action)}
        </div>

        <!-- Active Draft or Submission Alert Banner -->
        ${d.latest_submission ? `
          <div style="background-color: var(--color-indigo-50); border: 1px solid var(--color-indigo-200); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); margin: var(--space-2) 0; font-size: var(--text-xs); color: var(--color-indigo-950);">
            <strong>Cycle ${d.latest_submission.cycle_number} Response (${escapeHtml(d.latest_submission.status)}):</strong> 
            "${escapeHtml(d.latest_submission.response_text.substring(0, 140))}${d.latest_submission.response_text.length > 140 ? '...' : ''}"
            ${d.latest_submission.resolution_outcome ? `
              <span style="display: block; margin-top: 4px; font-weight: 600; color: ${d.latest_submission.resolution_outcome === 'CONDITION_CLEARED' ? 'var(--color-green-700)' : 'var(--color-amber-700)'};">
                Revalidation Outcome: ${escapeHtml(d.latest_submission.resolution_outcome.replace(/_/g, ' '))}
              </span>
            ` : ''}
          </div>
        ` : (d.active_draft ? `
          <div style="background-color: var(--color-amber-50); border: 1px solid var(--color-amber-200); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); margin: var(--space-2) 0; font-size: var(--text-xs); color: var(--color-amber-950);">
            <strong>Unsubmitted Draft Remarks (Cycle ${d.active_draft.cycle_number}):</strong>
            "${escapeHtml(d.active_draft.response_text.substring(0, 120))}..."
          </div>
        ` : '')}

        <!-- Card Footer Actions -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: var(--space-3); border-top: 1px solid var(--border-light); padding-top: var(--space-3); flex-wrap: wrap; gap: var(--space-2);">
          <div style="font-size: var(--text-xs); color: var(--text-muted);">
            Evidence: <strong>${escapeHtml(docRef)}</strong> ${pageRef ? `• ${pageRef}` : ''}
          </div>
          <div style="display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap;">
            ${d.resolution_status === 'OPEN' ? `
              <button class="btn btn-secondary btn-sm btn-ack-finding" data-finding-id="${escapeHtml(d.id)}" title="Confirm applicant review and awareness">
                ${icons.check}
                <span>Acknowledge</span>
              </button>
            ` : ''}

            <button class="btn btn-secondary btn-sm btn-view-history" data-finding-id="${escapeHtml(d.id)}" title="View chronological history and audit trail">
              ${icons.history || icons.clipboardList}
              <span>History</span>
            </button>

            <a href="#/applications/${escapeHtml(appId)}/evidence/${escapeHtml(d.id)}" class="btn btn-secondary btn-sm" title="Inspect bounding boxes and extracted text layer">
              ${icons.eye}
              <span>Inspect Evidence</span>
            </a>

            <button class="btn btn-secondary btn-sm btn-open-grounding" data-rule-code="${escapeHtml(d.rule_code)}" title="View official verbatim AICTE APH clause and regulatory grounding">
              ${icons.scale}
              <span>APH Clause</span>
            </button>

            <button class="btn btn-primary btn-sm btn-open-response" data-finding-id="${escapeHtml(d.id)}" title="Provide corrective remarks or upload replacement version">
              ${icons.upload}
              <span>${d.active_draft ? 'Edit Draft Response' : (d.latest_submission ? 'Resubmit Correction' : 'Correct Deficiency')}</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Bind Card Action Listeners
  bindCardActions(appId);
}

function bindCardActions(appId) {
  // Acknowledge Button
  document.querySelectorAll('.btn-ack-finding').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const findingId = e.currentTarget.getAttribute('data-finding-id');
      try {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner" style="width: 12px; height: 12px;" aria-hidden="true"></span> Acknowledging...`;
        await api.acknowledgeFinding(findingId);
        await loadDeficiencyWorkspace(appId);
      } catch (err) {
        alert('Failed to acknowledge finding: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = `${icons.check} <span>Acknowledge</span>`;
      }
    });
  });

  // History Button
  document.querySelectorAll('.btn-view-history').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const findingId = e.currentTarget.getAttribute('data-finding-id');
      openHistoryModal(findingId, appId);
    });
  });

  // Response Console Button
  document.querySelectorAll('.btn-open-response').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const findingId = e.currentTarget.getAttribute('data-finding-id');
      openResponseModal(findingId, appId);
    });
  });

  // Statutory Grounding Button
  document.querySelectorAll('.btn-open-grounding').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const ruleCode = e.currentTarget.getAttribute('data-rule-code');
      const modalsContainer = document.getElementById('deficiency-modals-container');
      if (modalsContainer && ruleCode) {
        modalsContainer.innerHTML = renderStatutoryGroundingModal(ruleCode);
        const closeModal = () => { modalsContainer.innerHTML = ''; };
        document.getElementById('btn-close-grounding-modal')?.addEventListener('click', closeModal);
        document.getElementById('btn-dismiss-grounding-modal')?.addEventListener('click', closeModal);
      }
    });
  });
}

// -------------------------------------------------------------------------
// Interactive Modal 1: Response & Corrective Action Console
// -------------------------------------------------------------------------
async function openResponseModal(findingId, appId) {
  const modalsContainer = document.getElementById('deficiency-modals-container');
  if (!modalsContainer) return;

  const finding = activeDeficiencies.find(d => d.id === findingId);
  if (!finding) return;

  const isFsrRule = finding.rule_code === 'RULE-EOA-FSR-005' || (finding.title && finding.title.toLowerCase().includes('faculty'));
  const isAreaRule = finding.rule_code === 'RULE-EOA-LAND-001' || finding.rule_code === 'RULE-EOA-CROSS-007';

  let calculatorHtml = '';
  if (isFsrRule) {
    calculatorHtml = `
      <!-- Interactive "What-If" FSR Remediation Calculator -->
      <div class="calculator-card" style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: var(--radius-sm); padding: var(--space-3); margin-bottom: var(--space-4);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2);">
          <div style="display: flex; align-items: center; gap: var(--space-2); font-weight: 700; color: #166534; font-size: 12px;">
            ${icons.scale}
            <span>Interactive "What-If" FSR Remediation Calculator</span>
          </div>
          <span class="badge badge-success" style="font-size: 10px;">APH Annexure-5 Norm</span>
        </div>
        <div style="font-size: 11px; color: #14532D; margin-bottom: var(--space-3);">
          Simulate required faculty strength based on programme-specific AICTE statutory ratio norms:
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--space-2); margin-bottom: var(--space-3);">
          <div>
            <label style="font-size: 10px; font-weight: 600; color: #166534; display: block; margin-bottom: 2px;">Programme Category</label>
            <select id="calc-prog-select" class="form-control" style="font-size: 11px; padding: 4px 6px;">
              <option value="20" selected>UG Engineering & Tech (1:20)</option>
              <option value="25">Diploma Engineering (1:25)</option>
              <option value="15">PG Engineering / M.Tech (1:15)</option>
              <option value="20">Management / MBA / PGDM — 1:20 Norm</option>
              <option value="25">Management / MBA / PGDM — 1:25 Norm</option>
              <option value="20">Computer Applications / MCA — 1:20 Norm</option>
              <option value="25">Computer Applications / MCA — 1:25 Norm</option>
              <option value="15">Pharmacy (1:15)</option>
              <option value="10">Architecture (1:10)</option>
              <option value="20">HMCT Hotel Management (1:20)</option>
            </select>
          </div>
          <div>
            <label style="font-size: 10px; font-weight: 600; color: #166534; display: block; margin-bottom: 2px;">Total Approved Intake (All Years)</label>
            <input type="number" id="calc-intake-input" class="form-control" value="720" step="30" min="30" style="font-size: 11px; padding: 4px 6px;">
            <div style="font-size: 9px; color: #166534; margin-top: 2px;">Sum across all active years (S)</div>
          </div>
          <div>
            <label style="font-size: 10px; font-weight: 600; color: #166534; display: block; margin-bottom: 2px;">Current Faculty</label>
            <input type="number" id="calc-current-input" class="form-control" value="30" min="0" style="font-size: 11px; padding: 4px 6px;">
          </div>
        </div>
        <div style="background: white; border: 1px solid #BBF7D0; border-radius: var(--radius-xs); padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
          <div>
            <span style="color: var(--text-muted);">Required: </span>
            <strong id="calc-req-count" style="color: #166534; font-size: 13px;">36</strong>
            <span style="color: var(--text-muted); margin: 0 6px;">|</span>
            <span style="color: var(--text-muted);">Deficit: </span>
            <strong id="calc-deficit-count" style="color: #B91C1C; font-size: 13px;">6 members needed</strong>
          </div>
          <button type="button" id="btn-apply-fsr-calc" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 3px 8px;">
            Copy Math to Remarks
          </button>
        </div>
      </div>
    `;
  } else if (isAreaRule) {
    calculatorHtml = `
      <!-- Interactive Land & Built-up Area Reconciliation Calculator -->
      <div class="calculator-card" style="background: #EFF6FF; border: 1px solid #93C5FD; border-radius: var(--radius-sm); padding: var(--space-3); margin-bottom: var(--space-4);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2);">
          <div style="display: flex; align-items: center; gap: var(--space-2); font-weight: 700; color: #1E40AF; font-size: 12px;">
            ${icons.scale}
            <span>Interactive Land & Built-up Area Reconciliation Calculator</span>
          </div>
          <span class="badge badge-info" style="font-size: 10px;">APH Chapter II</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-bottom: var(--space-2);">
          <div>
            <label style="font-size: 10px; font-weight: 600; color: #1E40AF; display: block; margin-bottom: 2px;">Sanctioned Built-up (Sq.m)</label>
            <input type="number" id="calc-sanctioned-area" class="form-control" value="8500" style="font-size: 11px; padding: 4px 6px;">
          </div>
          <div>
            <label style="font-size: 10px; font-weight: 600; color: #1E40AF; display: block; margin-bottom: 2px;">Completed Built-up (Sq.m)</label>
            <input type="number" id="calc-completed-area" class="form-control" value="8420" style="font-size: 11px; padding: 4px 6px;">
          </div>
        </div>
        <div style="background: white; border: 1px solid #BFDBFE; border-radius: var(--radius-xs); padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
          <div>
            <span style="color: var(--text-muted);">Area Variance: </span>
            <strong id="calc-variance-val" style="color: #1E40AF; font-size: 12px;">-80 Sq.m (Within Sanction)</strong>
          </div>
          <button type="button" id="btn-apply-area-calc" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 3px 8px;">
            Copy Reconciliation
          </button>
        </div>
        <div style="font-size: 10px; color: #1E40AF; margin-top: 4px;">
          <strong>Regulatory Note:</strong> Assumes sanctioned area verified from municipal building plan. Local FSI/FAR permissible limits depend on municipal master plan notifications and are not inferred.
        </div>
      </div>
    `;
  }

  // Render Skeleton Modal
  modalsContainer.innerHTML = `
    <div class="modal-overlay" id="response-modal-overlay">
      <div class="modal-card" style="max-width: 650px; width: 95%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.edit}
            <h3 style="font-size: var(--text-base); margin: 0;">Remediation & Corrective Action Console</h3>
          </div>
          <button class="btn-icon" id="btn-close-response-modal" aria-label="Close dialog">&times;</button>
        </div>

        <div class="modal-body" style="padding: var(--space-5);">
          <!-- Target Summary -->
          <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-3); margin-bottom: var(--space-4);">
            <div style="font-size: var(--text-xs); font-weight: bold; color: var(--color-blue-700); font-family: var(--font-mono);">
              ${escapeHtml(finding.rule_code)} • ${escapeHtml(finding.title || finding.rule_title)}
            </div>
            <div style="font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px;">
              ${escapeHtml(finding.explanation)}
            </div>
          </div>

          ${calculatorHtml}

          <form id="corrective-response-form">
            <div id="response-feedback-area" style="margin-bottom: var(--space-3);"></div>

            <!-- Response Category -->
            <div class="form-group" style="margin-bottom: var(--space-4);">
              <label for="resp-category-select" class="form-label" style="font-weight: 600; font-size: var(--text-xs);">
                Remediation Category <span style="color: var(--color-red-500);">*</span>
              </label>
              <select id="resp-category-select" class="form-control" style="font-size: var(--text-sm);">
                <option value="DOCUMENT_REPLACEMENT" selected>Document Replacement (Upload renewed or corrected certificate / scan)</option>
                <option value="CLARIFICATION_JUSTIFICATION">Statutory Clarification / Legal Exemption Justification</option>
                <option value="CORRECTION_AFFIDAVIT">Notarized Compliance Affidavit / Undertaking</option>
              </select>
            </div>

            <!-- Response Text -->
            <div class="form-group" style="margin-bottom: var(--space-4);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <label for="resp-text-area" class="form-label" style="font-weight: 600; font-size: var(--text-xs);">
                  Corrective Explanation / Justification <span style="color: var(--color-red-500);">*</span>
                </label>
                <span id="resp-char-counter" style="font-size: 11px; color: var(--text-muted);">0 / 5000 chars</span>
              </div>
              <textarea id="resp-text-area" class="form-control" rows="4" placeholder="Detail the corrective actions taken, statutory justification, or specify how the renewed certificate remedies the finding..." style="font-size: var(--text-sm); line-height: 1.4; resize: vertical;"></textarea>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Minimum 10 characters required. Draft updates are automatically traceable.</div>
            </div>

            <!-- Document Upload Replacement -->
            <div class="form-group" style="margin-bottom: var(--space-5);">
              <label class="form-label" style="font-weight: 600; font-size: var(--text-xs);">
                Supporting Replacement Document (Optional .PDF)
              </label>
              <input type="file" id="resp-file-input" accept="application/pdf" class="form-control" style="font-size: var(--text-xs); padding: var(--space-2);" />
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
                Upload replacement PDF version (v2/v3). Document will undergo automated virus scanning, SHA-256 integrity hashing, and IDP extraction.
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-light); padding-top: var(--space-4);">
              <button type="button" class="btn btn-secondary btn-sm" id="btn-cancel-response">Cancel</button>
              <div style="display: flex; gap: var(--space-2);">
                <button type="button" class="btn btn-secondary btn-sm" id="btn-save-draft">
                  ${icons.save || icons.edit}
                  <span>Save Draft</span>
                </button>
                <button type="submit" class="btn btn-primary btn-sm" id="btn-submit-response">
                  ${icons.checkCircle}
                  <span>Submit Correction & Revalidate</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  // Pre-fill existing draft if available
  const existingDraft = finding.active_draft || finding.latest_submission;
  const textarea = document.getElementById('resp-text-area');
  const counter = document.getElementById('resp-char-counter');
  const categorySelect = document.getElementById('resp-category-select');

  if (existingDraft && textarea) {
    textarea.value = existingDraft.response_text || '';
    if (categorySelect && existingDraft.response_category) {
      categorySelect.value = existingDraft.response_category;
    }
    if (counter) counter.textContent = `${textarea.value.length} / 5000 chars`;
  }

  if (textarea && counter) {
    textarea.addEventListener('input', () => {
      counter.textContent = `${textarea.value.length} / 5000 chars`;
    });
  }

  // Bind Calculator Interactions
  if (isFsrRule) {
    const progSelect = document.getElementById('calc-prog-select');
    const intakeInput = document.getElementById('calc-intake-input');
    const currentInput = document.getElementById('calc-current-input');
    const reqEl = document.getElementById('calc-req-count');
    const defEl = document.getElementById('calc-deficit-count');
    const copyBtn = document.getElementById('btn-apply-fsr-calc');

    const recalculateFsr = () => {
      const ratio = parseInt(progSelect?.value || '20', 10);
      const rawIntake = intakeInput?.value?.trim();
      const rawCurrent = currentInput?.value?.trim();
      const intake = parseInt(rawIntake || '0', 10);
      const current = parseInt(rawCurrent || '0', 10);

      if (isNaN(intake) || intake <= 0) {
        if (reqEl) reqEl.textContent = '—';
        if (defEl) {
          defEl.textContent = 'Enter valid intake (> 0)';
          defEl.style.color = '#B91C1C';
        }
        return;
      }

      if (isNaN(current) || current < 0) {
        if (reqEl) reqEl.textContent = '—';
        if (defEl) {
          defEl.textContent = 'Enter non-negative faculty count (>= 0)';
          defEl.style.color = '#B91C1C';
        }
        return;
      }

      const req = Math.ceil(intake / ratio);
      const deficit = Math.max(0, req - current);

      if (reqEl) reqEl.textContent = req;
      if (defEl) {
        if (deficit === 0) {
          defEl.textContent = 'Compliant (Zero Deficit)';
          defEl.style.color = '#166534';
        } else {
          defEl.textContent = `${deficit} member(s) needed`;
          defEl.style.color = '#B91C1C';
        }
      }
    };

    progSelect?.addEventListener('change', recalculateFsr);
    intakeInput?.addEventListener('input', recalculateFsr);
    currentInput?.addEventListener('input', recalculateFsr);
    recalculateFsr();

    copyBtn?.addEventListener('click', () => {
      const ratio = progSelect?.value || '20';
      const intake = intakeInput?.value || '720';
      const current = currentInput?.value || '30';
      const req = Math.ceil(parseInt(intake, 10) / parseInt(ratio, 10));
      const deficit = Math.max(0, req - parseInt(current, 10));
      const textToAppend = `[Statutory FSR Math: Approved Intake ${intake} with 1:${ratio} ratio requires ${req} faculty members. Current roster: ${current}. Deficit of ${deficit} member(s) addressed via appointment orders attached in revised roster.]`;
      if (textarea) {
        textarea.value = (textarea.value ? textarea.value.trim() + '\n' : '') + textToAppend;
        textarea.dispatchEvent(new Event('input'));
      }
    });
  }

  if (isAreaRule) {
    const sancInput = document.getElementById('calc-sanctioned-area');
    const compInput = document.getElementById('calc-completed-area');
    const varEl = document.getElementById('calc-variance-val');
    const copyBtn = document.getElementById('btn-apply-area-calc');

    const recalculateArea = () => {
      const rawSanc = sancInput?.value?.trim();
      const rawComp = compInput?.value?.trim();
      const sanc = parseFloat(rawSanc || '0');
      const comp = parseFloat(rawComp || '0');

      if (isNaN(sanc) || sanc <= 0 || isNaN(comp) || comp <= 0) {
        if (varEl) {
          varEl.textContent = 'Enter positive areas (> 0 Sq.m)';
          varEl.style.color = '#B91C1C';
        }
        return;
      }

      const diff = comp - sanc;
      if (varEl) {
        if (diff > 0) {
          varEl.textContent = `+${diff.toFixed(1)} Sq.m (Exceeds Sanction by ${diff.toFixed(1)} Sq.m — Compounding Required)`;
          varEl.style.color = '#B91C1C';
        } else {
          varEl.textContent = `${diff.toFixed(1)} Sq.m (Within Sanction)`;
          varEl.style.color = '#166534';
        }
      }
    };

    sancInput?.addEventListener('input', recalculateArea);
    compInput?.addEventListener('input', recalculateArea);
    recalculateArea();

    copyBtn?.addEventListener('click', () => {
      const sanc = sancInput?.value || '0';
      const comp = compInput?.value || '0';
      const diff = (parseFloat(comp) - parseFloat(sanc)).toFixed(1);
      const textToAppend = `[Area Reconciliation: Sanctioned Area = ${sanc} Sq.m, Completed Area = ${comp} Sq.m (Variance: ${diff} Sq.m). Fully verified against municipal building plan endorsement.]`;
      if (textarea) {
        textarea.value = (textarea.value ? textarea.value.trim() + '\n' : '') + textToAppend;
        textarea.dispatchEvent(new Event('input'));
      }
    });
  }

  // Close handlers
  const closeModal = () => { modalsContainer.innerHTML = ''; };
  document.getElementById('btn-close-response-modal')?.addEventListener('click', closeModal);
  document.getElementById('btn-cancel-response')?.addEventListener('click', closeModal);

  // Save Draft Handler
  document.getElementById('btn-save-draft')?.addEventListener('click', async () => {
    const text = textarea?.value?.trim() || '';
    if (text.length < 5) {
      alert('Draft remarks must be at least 5 characters.');
      return;
    }
    const saveBtn = document.getElementById('btn-save-draft');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
      await api.saveDraftResponse(findingId, {
        response_text: text,
        response_category: categorySelect.value,
        document_id: finding.document_id || null,
        document_version_id: finding.document_version_id || null,
      });
      closeModal();
      await loadDeficiencyWorkspace(appId);
    } catch (err) {
      alert('Failed to save draft: ' + err.message);
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save Draft';
    }
  });

  // Submit Handler
  document.getElementById('corrective-response-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = textarea?.value?.trim() || '';
    if (text.length < 10) {
      alert('Formal submission remarks must be at least 10 characters.');
      return;
    }

    const fileInput = document.getElementById('resp-file-input');
    const submitBtn = document.getElementById('btn-submit-response');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px;" aria-hidden="true"></span> Submitting...`;

    try {
      if (fileInput?.files?.length > 0) {
        // Multipart Document Resolve Bridge (uploads file v2, extracts, submits, and runs revalidation)
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('remarks', text);
        formData.append('response_category', categorySelect.value);

        const result = await api.resolveFindingWithDocument(findingId, formData);
        closeModal();
        if (result.revalidation) {
          renderRevalidationReportModal(result.revalidation, appId);
        }
      } else {
        // Direct Submit
        await api.submitCorrection(findingId, {
          response_text: text,
          response_category: categorySelect.value,
          document_id: finding.document_id || null,
          document_version_id: finding.document_version_id || null,
        });

        // Trigger Revalidation
        const revalResult = await api.revalidateApplication(appId);
        closeModal();
        renderRevalidationReportModal(revalResult, appId);
      }

      await loadDeficiencyWorkspace(appId);
    } catch (err) {
      alert('Submission failed: ' + err.message);
      submitBtn.disabled = false;
      submitBtn.innerHTML = `${icons.checkCircle} <span>Submit Correction & Revalidate</span>`;
    }
  });
}

// -------------------------------------------------------------------------
// Interactive Modal 2: Full Chronological Timeline & Audit History
// -------------------------------------------------------------------------
async function openHistoryModal(findingId, appId) {
  const modalsContainer = document.getElementById('deficiency-modals-container');
  if (!modalsContainer) return;

  const finding = activeDeficiencies.find(d => d.id === findingId);
  const title = finding ? (finding.title || finding.rule_code) : `Finding #${findingId}`;

  modalsContainer.innerHTML = `
    <div class="modal-overlay" id="history-modal-overlay">
      <div class="modal-card" style="max-width: 600px; width: 95%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.history || icons.clipboardList}
            <h3 style="font-size: var(--text-base); margin: 0;">Traceable Chronological History</h3>
          </div>
          <button class="btn-icon" id="btn-close-history-modal" aria-label="Close dialog">&times;</button>
        </div>

        <div class="modal-body" style="padding: var(--space-5);">
          <div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4);">
            Forensic audit trail for finding: <strong>${escapeHtml(title)}</strong>
          </div>

          <div id="timeline-events-list">
            <div style="text-align: center; padding: var(--space-6); color: var(--text-muted);">
              <span class="spinner" aria-hidden="true"></span>
              <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading forensic timeline...</p>
            </div>
          </div>

          <div style="text-align: right; margin-top: var(--space-5); border-top: 1px solid var(--border-light); padding-top: var(--space-3);">
            <button class="btn btn-secondary btn-sm" id="btn-done-history">Close</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const closeModal = () => { modalsContainer.innerHTML = ''; };
  document.getElementById('btn-close-history-modal')?.addEventListener('click', closeModal);
  document.getElementById('btn-done-history')?.addEventListener('click', closeModal);

  try {
    const data = await api.getFindingHistory(findingId);
    const events = data.history || [];
    const listEl = document.getElementById('timeline-events-list');
    if (!listEl) return;

    if (events.length === 0) {
      listEl.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: var(--space-4);">No events recorded yet.</div>`;
      return;
    }

    listEl.innerHTML = `
      <div style="border-left: 2px solid var(--border-light); margin-left: var(--space-3); padding-left: var(--space-4); display: flex; flex-direction: column; gap: var(--space-4);">
        ${events.map(ev => {
          const dateStr = new Date(ev.timestamp).toLocaleString();
          let dotColor = 'var(--color-blue-600)';
          if (ev.event_type === 'FINDING_IDENTIFIED') dotColor = 'var(--color-red-600)';
          else if (ev.event_type === 'CORRECTION_SUBMITTED') dotColor = 'var(--color-indigo-600)';
          else if (ev.event_type === 'REVALIDATION_RUN') dotColor = 'var(--color-teal-600)';
          else if (ev.event_type === 'ACKNOWLEDGED') dotColor = 'var(--color-green-600)';

          return `
            <div style="position: relative;">
              <span style="position: absolute; left: -25px; top: 3px; width: 10px; height: 10px; border-radius: 50%; background-color: ${dotColor};"></span>
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <span style="font-weight: 600; font-size: var(--text-xs); color: var(--text-primary);">
                  ${escapeHtml(ev.event_type.replace(/_/g, ' '))}
                </span>
                <span style="font-size: 11px; color: var(--text-muted);">${escapeHtml(dateStr)}</span>
              </div>
              <p style="font-size: var(--text-xs); color: var(--text-secondary); margin: 2px 0 0 0;">
                ${escapeHtml(ev.description)}
              </p>
              ${ev.actor ? `
                <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">
                  Actor: ${escapeHtml(ev.actor)} (${escapeHtml(ev.actor_role || 'SYSTEM')})
                </div>
              ` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;

  } catch (err) {
    const listEl = document.getElementById('timeline-events-list');
    if (listEl) {
      listEl.innerHTML = `<div style="color: var(--color-red-600); font-size: var(--text-xs);">Failed to load history: ${escapeHtml(err.message)}</div>`;
    }
  }
}

// -------------------------------------------------------------------------
// Interactive Modal 3: Controlled Revalidation Report (Delta Comparison)
// -------------------------------------------------------------------------
function renderRevalidationReportModal(revalData, appId) {
  const modalsContainer = document.getElementById('deficiency-modals-container');
  if (!modalsContainer) return;

  const comparisons = revalData.comparison || [];
  const clearedCount = revalData.findings_cleared || 0;
  const persistingCount = revalData.findings_persisting || 0;
  const newCount = revalData.new_findings || 0;

  modalsContainer.innerHTML = `
    <div class="modal-overlay" id="revalidation-modal-overlay">
      <div class="modal-card" style="max-width: 720px; width: 95%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.scale}
            <h3 style="font-size: var(--text-base); margin: 0;">Automated Revalidation Outcome (Run #${revalData.run_number})</h3>
          </div>
          <button class="btn-icon" id="btn-close-reval-modal" aria-label="Close dialog">&times;</button>
        </div>

        <div class="modal-body" style="padding: var(--space-5);">
          <!-- Summary Metrics -->
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-3); margin-bottom: var(--space-4);">
            <div style="background-color: var(--color-green-50); border: 1px solid var(--color-green-200); border-radius: var(--radius-sm); padding: var(--space-3); text-align: center;">
              <div style="font-size: var(--text-lg); font-weight: bold; color: var(--color-green-700);">${clearedCount}</div>
              <div style="font-size: var(--text-xs); color: var(--color-green-800);">Conditions Cleared</div>
            </div>
            <div style="background-color: var(--color-amber-50); border: 1px solid var(--color-amber-200); border-radius: var(--radius-sm); padding: var(--space-3); text-align: center;">
              <div style="font-size: var(--text-lg); font-weight: bold; color: var(--color-amber-700);">${persistingCount}</div>
              <div style="font-size: var(--text-xs); color: var(--color-amber-800);">Conditions Persisting</div>
            </div>
            <div style="background-color: var(--color-slate-100); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-3); text-align: center;">
              <div style="font-size: var(--text-lg); font-weight: bold; color: var(--text-primary);">${newCount}</div>
              <div style="font-size: var(--text-xs); color: var(--text-muted);">New Deficiencies</div>
            </div>
          </div>

          <!-- Comparison Table -->
          <div style="font-weight: 600; font-size: var(--text-xs); margin-bottom: var(--space-2); color: var(--text-primary);">
            Before vs After Revalidation Delta Evaluation
          </div>

          <div class="table-responsive" style="max-height: 280px; overflow-y: auto; border: 1px solid var(--border-light); border-radius: var(--radius-sm);">
            <table class="data-table" style="font-size: var(--text-xs);">
              <thead>
                <tr>
                  <th>Rule Code</th>
                  <th>Previous Outcome</th>
                  <th>Revalidation Outcome</th>
                  <th>Delta Status</th>
                  <th>Evaluation Notes</th>
                </tr>
              </thead>
              <tbody>
                ${comparisons.map(c => {
                  let badgeType = 'secondary';
                  if (c.status_change === 'CLEARED') badgeType = 'success';
                  else if (c.status_change === 'PERSISTS') badgeType = 'danger';
                  else if (c.status_change === 'NEW') badgeType = 'warning';

                  return `
                    <tr>
                      <td style="font-family: var(--font-mono); font-weight: bold;">${escapeHtml(c.rule_code)}</td>
                      <td>${escapeHtml(c.previous_outcome.replace(/_/g, ' '))}</td>
                      <td style="font-weight: 600;">${escapeHtml(c.latest_outcome.replace(/_/g, ' '))}</td>
                      <td>${renderBadge(badgeType, c.status_change)}</td>
                      <td style="color: var(--text-secondary); max-width: 220px;">${escapeHtml(c.details)}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>

          <!-- Advisory Governance Disclaimer -->
          <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-3); margin-top: var(--space-4); font-size: 11px; color: var(--text-muted);">
            <strong>Notice:</strong> Cleared findings are designated <em>"Awaiting Review"</em> and forwarded to the assigned AICTE Scrutiny Committee for formal verification. This prototype does not automatically approve or reject applications.
          </div>

          <div style="text-align: right; margin-top: var(--space-5); border-top: 1px solid var(--border-light); padding-top: var(--space-3);">
            <button class="btn btn-primary btn-sm" id="btn-ack-reval-report">Acknowledge & Refresh</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const closeModal = () => {
    modalsContainer.innerHTML = '';
  };
  document.getElementById('btn-close-reval-modal')?.addEventListener('click', closeModal);
  document.getElementById('btn-ack-reval-report')?.addEventListener('click', () => {
    closeModal();
    loadDeficiencyWorkspace(appId);
  });
}

// -------------------------------------------------------------------------
// Global Revalidate Application Action Handler
// -------------------------------------------------------------------------
async function handleRevalidateApplication(appId, state) {
  const btn = document.getElementById('btn-revalidate-application');
  const spinner = document.getElementById('reval-spinner');
  const btnText = document.getElementById('reval-btn-text');

  if (btn) btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (btnText) btnText.textContent = 'Revalidating Against APH Rules...';

  try {
    const result = await api.revalidateApplication(appId);
    renderRevalidationReportModal(result, appId);
    await loadDeficiencyWorkspace(appId, state);
  } catch (err) {
    alert('Revalidation failed: ' + (err.message || 'Error executing regulatory engine.'));
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
    if (btnText) btnText.textContent = 'Re-run Regulatory Pre-Scrutiny';
  }
}
