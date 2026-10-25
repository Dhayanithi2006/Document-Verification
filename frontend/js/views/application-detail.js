import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert, renderReadinessGauge, renderStatutoryGroundingModal } from '../components.js';
import { syntheticApplications, syntheticChecklist } from '../sample-data.js';
import { api } from '../api.js';

export function renderApplicationDetail(state, params = {}) {
  const appId = params?.id || 'app_9812';
  const initialApp = syntheticApplications.find(a => a.id === appId) || syntheticApplications[0];

  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Applications', href: '#/applications' },
    { label: initialApp.applicationNumber }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div id="application-detail-container">
        <!-- Top Action / Notification Banner -->
        <div id="detail-alert-area" style="margin-bottom: var(--space-4);"></div>

        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
          <div>
            <div style="display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap;">
              <h1>Application #${escapeHtml(initialApp.applicationNumber)}</h1>
              ${renderBadge(initialApp.status, initialApp.status.replace(/_/g, ' '))}
            </div>
            <p style="color: var(--text-muted); margin-top: 4px;">
              ${escapeHtml(initialApp.institutionName)} • ${initialApp.academicYear} • Extension of Approval (EoA)
            </p>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">
              ${icons.clipboardList}
              <span>Mandatory Statutory Document Checklist (8 Items)</span>
            </div>
            <span style="font-size: var(--text-xs); color: var(--text-muted);">
              Connecting to verification server...
            </span>
          </div>
          <div class="card-body">
            <div class="checklist-grid" id="checklist-items-container">
              ${syntheticChecklist.map((doc, idx) => `
                <div class="checklist-item-card" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-4) var(--space-5); border: 1px solid var(--border-light); border-radius: var(--radius-md); margin-bottom: var(--space-3);">
                  <div class="checklist-item-info">
                    <div class="checklist-item-number ${doc.status === 'PROCESSED' || doc.status === 'UPLOADED' ? 'completed' : ''}">
                      ${idx + 1}
                    </div>
                    <div>
                      <div class="checklist-item-title">
                        <span>${doc.title}</span>
                        <span class="badge badge-info" style="font-size: 10px;">Mandatory</span>
                        ${renderBadge(doc.status, doc.status.replace(/_/g, ' '))}
                      </div>
                      <div class="checklist-item-meta">
                        <span>Loading live statutory verification status...</span>
                      </div>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export async function initApplicationDetailView(state, router, params) {
  const container = document.getElementById('application-detail-container');
  if (!container) return;

  const appId = params?.id;
  if (!appId) {
    container.innerHTML = renderAlert('danger', 'Invalid Application Reference', 'No application identifier was specified.');
    return;
  }

  try {
    // Parallel fetch of application metadata, 8-document checklist, and pre-scrutiny findings
    const [app, checklist, findingsData] = await Promise.all([
      api.getApplication(appId),
      api.getChecklist(appId),
      api.getApplicationFindings(appId).catch(() => ({ findings: [] }))
    ]);

    renderWorkspace(app, checklist, findingsData?.findings || [], state, router);
  } catch (err) {
    console.error('Failed to load application workspace:', err);
    if (err.status === 404) {
      container.innerHTML = `
        <div style="padding: var(--space-12); text-align: center; max-width: 500px; margin: 0 auto;">
          <div style="font-size: 40px; color: var(--color-red-500); margin-bottom: var(--space-3);" aria-hidden="true">
            ${icons.shieldCheck}
          </div>
          <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">Application Not Found or Access Restricted</h2>
          <p style="color: var(--text-muted); font-size: var(--text-sm); margin-bottom: var(--space-6);">
            The requested application identifier does not exist or does not belong to your authorised institution.
          </p>
          <a href="#/applications" class="btn btn-secondary">
            ${icons.chevronLeft}
            <span>Return to My Applications</span>
          </a>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div style="padding: var(--space-6);">
          ${renderAlert('danger', 'Unable to Load Application', err.message || 'Server communication error.')}
          <div style="margin-top: var(--space-4); text-align: center;">
            <button id="btn-retry-app-detail" class="btn btn-secondary">
              ${icons.refresh}
              <span>Retry Loading</span>
            </button>
          </div>
        </div>
      `;
      const retryBtn = document.getElementById('btn-retry-app-detail');
      if (retryBtn) {
        retryBtn.addEventListener('click', () => initApplicationDetailView(state, router, params));
      }
    }
  }
}

function renderWorkspace(app, checklist, initialFindings = [], state, router) {
  const container = document.getElementById('application-detail-container');
  if (!container) return;

  // Defensive parameter alignment in case initialFindings was omitted or shifted
  if (initialFindings && typeof initialFindings.getCurrentUser === 'function') {
    router = state;
    state = initialFindings;
    initialFindings = [];
  }

  const user = state?.getCurrentUser ? state.getCurrentUser() : {};
  const institutionName = user.institution?.name || user.institution || 'Authorised Institution';
  const items = checklist.checklist || checklist.items || [];
  const totalSlots = checklist.total_slots || items.length || 8;
  const uploadedSlots = checklist.uploaded_slots !== undefined ? checklist.uploaded_slots : items.filter(d => d.status === 'UPLOADED').length;
  const percentComplete = Math.round((uploadedSlots / totalSlots) * 100);

  const deficienciesCount = initialFindings.filter(f => (f.outcome === 'DEFICIENCY_DETECTED' || f.severity === 'DEFICIENCY') && f.status !== 'RESOLVED').length;
  const warningsCount = initialFindings.filter(f => f.severity === 'WARNING' && f.status !== 'RESOLVED').length;
  const missingCount = Math.max(0, totalSlots - uploadedSlots);

  container.innerHTML = `
    <!-- Top Action / Notification Banner -->
    <div id="detail-alert-area" style="margin-bottom: var(--space-4);"></div>

    <!-- Application Header Banner -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
      <div>
        <div style="display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap;">
          <h1>Application #${escapeHtml(app.application_number)}</h1>
          ${renderBadge(app.status, app.status.replace(/_/g, ' '))}
          <span class="badge badge-info">${escapeHtml(app.academic_year)}</span>
        </div>
        <p style="color: var(--text-muted); margin-top: 4px;">
          ${escapeHtml(institutionName)} • ${escapeHtml(app.program_category || 'Engineering & Technology')} • Extension of Approval (EoA)
        </p>
      </div>

      <div style="display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap;">
        <button id="btn-export-dossier" class="btn btn-secondary btn-sm" title="Generate printable Pre-Scrutiny Assessment Dossier">
          ${icons.clipboardList}
          <span>Pre-Scrutiny Dossier</span>
        </button>
        <a href="#/applications/${app.id}/deficiencies" class="btn btn-secondary btn-sm" id="btn-goto-deficiencies" style="display: flex; align-items: center; gap: 6px;" title="Review and resolve actionable regulatory discrepancies">
          ${icons.alertTriangle}
          <span>Deficiency Resolution Bridge</span>
        </a>
        <button id="btn-run-validation" class="btn btn-primary btn-sm" title="Run AICTE Pre-Scrutiny Checks against active regulatory rules">
          <span id="run-val-spinner" class="spinner" style="display: none;" aria-hidden="true"></span>
          ${icons.checkCircle}
          <span id="run-val-text">Run Pre-Scrutiny Checks</span>
        </button>
        <button id="btn-toggle-edit-params" class="btn btn-secondary btn-sm">
          ${icons.edit}
          <span>Edit Declared Parameters</span>
        </button>
        <button id="btn-refresh-checklist" class="btn btn-secondary btn-sm" title="Refresh checklist status">
          ${icons.refresh}
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Pre-Submission Scrutiny Readiness Gauge & Health Index -->
    ${renderReadinessGauge(deficienciesCount, warningsCount, missingCount, uploadedSlots, totalSlots, (initialFindings && initialFindings.length > 0) ? 'run_active' : null, deficienciesCount)}

    <!-- Declared Parameters Modal/Form Drawer (Collapsible) -->
    <div id="edit-params-drawer" class="card" style="display: none; margin-bottom: var(--space-6); background-color: var(--color-slate-50); border: 1px solid var(--color-blue-200);">
      <div class="card-header" style="background-color: var(--color-slate-100);">
        <div class="card-title">
          ${icons.edit}
          <span>Update Declared Physical & Academic Parameters</span>
        </div>
        <button type="button" id="btn-close-edit-params" class="btn btn-ghost btn-sm">✕ Close</button>
      </div>
      <div class="card-body">
        <form id="edit-params-form">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4);">
            <div class="form-group">
              <label class="form-label" for="edit-intake">Total Applied Intake <span style="color: var(--color-red-600);">*</span></label>
              <input type="number" id="edit-intake" class="form-control" value="${app.total_intake_applied || 720}" min="30" step="30" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="edit-land">Declared Land (Acres)</label>
              <input type="number" id="edit-land" class="form-control" value="${app.declared_land_acres || 5.2}" step="0.1" min="0.5">
            </div>
            <div class="form-group">
              <label class="form-label" for="edit-faculty">Declared Faculty Count</label>
              <input type="number" id="edit-faculty" class="form-control" value="${app.declared_faculty_count || 35}" min="1">
            </div>
            <div class="form-group">
              <label class="form-label" for="edit-carpet">Built-up Carpet Area (Sq.m)</label>
              <input type="number" id="edit-carpet" class="form-control" value="${app.declared_builtup_sqm || 8420}" min="100">
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-4);">
            <button type="button" id="btn-cancel-edit-params" class="btn btn-secondary btn-sm">Cancel</button>
            <button type="submit" id="btn-save-params" class="btn btn-primary btn-sm">
              <span id="save-params-spinner" class="spinner" style="display: none;" aria-hidden="true"></span>
              <span id="save-params-text">Save Declared Parameters</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Mandatory Disclaimer Alert -->
    <div style="margin-bottom: var(--space-6);">
      ${renderAlert('info', 'SIH Prototype Pre-Scrutiny Notice', 
        'Uploading documents initializes the preparation stage for pre-scrutiny. Uploading a document or completing this checklist does not constitute regulatory compliance, verification, or official approval.'
      )}
    </div>

    <!-- Application Progress & Stats Grid -->
    <div class="card" style="margin-bottom: var(--space-6);">
      <div class="card-body" style="padding: var(--space-4) var(--space-6);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4); align-items: center;">
          <div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Checklist Readiness</div>
            <div style="font-size: var(--text-lg); font-weight: bold; color: ${uploadedSlots === totalSlots ? 'var(--color-green-700)' : 'var(--color-blue-700)'};">
              ${uploadedSlots} / ${totalSlots} Documents Uploaded
            </div>
            <div class="progress-bar-container" style="height: 6px; margin-top: 6px;">
              <div class="progress-bar-fill ${uploadedSlots === totalSlots ? 'success' : ''}" style="width: ${percentComplete}%;"></div>
            </div>
          </div>
          <div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Applied Sanctioned Intake</div>
            <div style="font-size: var(--text-lg); font-weight: bold; color: var(--text-primary);">${app.total_intake_applied || 0} Seats</div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Undergraduate Programmes</div>
          </div>
          <div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Declared Infrastructure</div>
            <div style="font-size: var(--text-base); font-weight: 600; color: var(--text-primary);">
              ${app.declared_land_acres || 0} Acres • ${app.declared_builtup_sqm || 0} Sq.m
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Faculty Roster: ${app.declared_faculty_count || 0} Members</div>
          </div>
          <div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Application Lifecycle State</div>
            <div style="font-size: var(--text-base); font-weight: 600;">
              ${renderBadge(app.status, app.status)}
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Preparation & Upload Active</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Statutory 8-Document Checklist -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          ${icons.clipboardList}
          <span>Statutory Document Checklist (${totalSlots} Mandatory Items)</span>
        </div>
        <span style="font-size: var(--text-xs); color: var(--text-muted);">
          AICTE Approval Process Handbook (APH 2024-2027) Norms
        </span>
      </div>
      <div class="card-body">
        <div class="checklist-grid" id="checklist-items-container">
          ${items.map((doc, idx) => renderChecklistItem(doc, idx, app.id)).join('')}
        </div>
      </div>
    </div>

    <!-- Explainable Regulatory Pre-Scrutiny Findings Section -->
    <div id="pre-scrutiny-findings-section" style="margin-top: var(--space-6);">
      <div class="card">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-3);">
          <div class="card-title" style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.shieldCheck}
            <span>Explainable Regulatory Pre-Scrutiny Findings</span>
          </div>
          <div id="findings-summary-chips" style="display: flex; gap: var(--space-2); flex-wrap: wrap; align-items: center;"></div>
        </div>
        <div class="card-body">
          <div id="findings-content-area">
            <div style="text-align: center; padding: var(--space-6); color: var(--text-muted);">
              <span class="spinner" aria-hidden="true"></span>
              <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading pre-scrutiny evaluation records...</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Evidence & Fields Inspection Modal Container -->
    <div id="evidence-modal-target"></div>
    <div id="grounding-modal-target"></div>
  `;

  bindWorkspaceEvents(app, checklist, initialFindings, state, router);
}

function renderChecklistItem(doc, idx, appId) {
  const isUploaded = doc.status === 'UPLOADED' && doc.current_version;
  const version = doc.current_version;
  const docTitle = doc.title || doc.document_title || doc.document_type;

  let fileMetaHtml = '';
  let actionsHtml = '';

  if (isUploaded) {
    const sizeMb = (version.file_size_bytes / (1024 * 1024)).toFixed(2);
    const dateVal = version.upload_timestamp || version.created_at;
    const dateStr = dateVal ? new Date(dateVal).toLocaleDateString() : '—';
    const hashVal = version.file_hash_sha256 || version.sha256_hash || '';
    const hashPreview = hashVal ? hashVal.substring(0, 8) : '';

    fileMetaHtml = `
      <div class="checklist-item-meta" style="flex-wrap: wrap;">
        <span>File: <strong style="color: var(--text-primary);">${escapeHtml(version.file_name)}</strong></span>
        <span>•</span>
        <span>Size: <strong>${sizeMb} MB</strong></span>
        <span>•</span>
        <span><strong>${version.page_count || 1}</strong> ${version.page_count === 1 ? 'Page' : 'Pages'}</span>
        <span>•</span>
        <span title="SHA256: ${hashVal}">Hash: <code>${hashPreview}...</code></span>
        <span>•</span>
        <span>Uploaded: ${dateStr}</span>
      </div>
    `;

    actionsHtml = `
      <button class="btn btn-primary btn-sm btn-inspect-doc" data-doc-id="${doc.id}" data-version="${version.version_number}" data-doc-title="${escapeHtml(docTitle)}" title="Inspect extracted fields and spatial evidence">
        ${icons.search}
        <span>Evidence & Fields</span>
      </button>
      <button class="btn btn-secondary btn-sm btn-reprocess-doc" data-doc-id="${doc.id}" data-version="${version.version_number}" data-doc-title="${escapeHtml(docTitle)}" title="Re-run Intelligent Document Processing pipeline">
        ${icons.refresh}
        <span>Re-Extract</span>
      </button>
      <button class="btn btn-secondary btn-sm btn-view-doc" data-doc-id="${doc.id}" data-version="${version.version_number}" title="View uploaded PDF document">
        ${icons.eye}
        <span>View PDF</span>
      </button>
      <label class="btn btn-secondary btn-sm" title="Upload a revised version (v${version.version_number + 1})" style="cursor: pointer; margin-bottom: 0;">
        ${icons.upload}
        <span>Replace</span>
        <input type="file" class="doc-file-input" data-doc-type="${doc.document_type}" data-app-id="${appId}" accept=".pdf" style="display: none;">
      </label>
      <button class="btn btn-ghost btn-sm btn-remove-doc" data-doc-type="${doc.document_type}" data-app-id="${appId}" data-doc-title="${escapeHtml(docTitle)}" title="Remove uploaded document" style="color: var(--color-red-600);">
        ✕ Remove
      </button>
    `;
  } else {
    fileMetaHtml = `
      <div class="checklist-item-meta" style="color: var(--color-slate-500);">
        <span>Required statutory document: PDF format only, max 15 MB.</span>
      </div>
    `;

    actionsHtml = `
      <div class="upload-action-group" style="display: flex; align-items: center; gap: var(--space-2);">
        <label class="btn btn-primary btn-sm" style="cursor: pointer; margin-bottom: 0;">
          ${icons.upload}
          <span>Upload PDF</span>
          <input type="file" class="doc-file-input" data-doc-type="${doc.document_type}" data-app-id="${appId}" accept=".pdf" style="display: none;">
        </label>
      </div>
    `;
  }

  return `
    <div class="checklist-item-card" id="doc-card-${doc.document_type}" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-4) var(--space-5); border: 1px solid var(--border-light); border-radius: var(--radius-md); margin-bottom: var(--space-3); background-color: ${isUploaded ? 'var(--bg-surface)' : 'var(--color-slate-50)'};">
      <div class="checklist-item-info" style="flex: 1;">
        <div class="checklist-item-number ${isUploaded ? 'completed' : ''}">
          ${idx + 1}
        </div>
        <div style="flex: 1;">
          <div class="checklist-item-title">
            <span>${escapeHtml(docTitle)}</span>
            <span class="badge badge-info" style="font-size: 10px;">Mandatory</span>
            ${isUploaded ? `<span class="badge badge-info" style="font-size: 10px;">v${version.version_number}</span>` : ''}
            ${renderBadge(doc.status, isUploaded ? 'UPLOADED' : 'PENDING')}
          </div>
          ${fileMetaHtml}
          <!-- Inline Upload Progress / Message -->
          <div class="doc-inline-msg" id="inline-msg-${doc.document_type}" style="display: none; margin-top: var(--space-2); font-size: var(--text-xs);"></div>
        </div>
      </div>

      <div class="checklist-item-actions" style="margin-left: var(--space-4); display: flex; flex-wrap: wrap; gap: var(--space-2); justify-content: flex-end;">
        ${actionsHtml}
      </div>
    </div>
  `;
}

function bindWorkspaceEvents(app, checklist, initialFindings = [], state, router) {
  const container = document.getElementById('application-detail-container');
  if (!container) return;

  const alertArea = document.getElementById('detail-alert-area');
  const editDrawer = document.getElementById('edit-params-drawer');
  const toggleEditBtn = document.getElementById('btn-toggle-edit-params');
  const closeEditBtn = document.getElementById('btn-close-edit-params');
  const cancelEditBtn = document.getElementById('btn-cancel-edit-params');
  const editForm = document.getElementById('edit-params-form');
  const refreshBtn = document.getElementById('btn-refresh-checklist');
  const exportDossierBtn = document.getElementById('btn-export-dossier');

  // Dossier Modal Button
  if (exportDossierBtn) {
    exportDossierBtn.addEventListener('click', async () => {
      exportDossierBtn.disabled = true;
      try {
        const findingsData = await api.getApplicationFindings(app.id).catch(() => ({ findings: [] }));
        openDossierModal(app, checklist, findingsData?.findings || initialFindings, state);
      } finally {
        exportDossierBtn.disabled = false;
      }
    });
  }

  // Toggle Edit Drawer
  if (toggleEditBtn && editDrawer) {
    toggleEditBtn.addEventListener('click', () => {
      const isHidden = editDrawer.style.display === 'none';
      editDrawer.style.display = isHidden ? 'block' : 'none';
      if (isHidden) {
        document.getElementById('edit-intake')?.focus();
      }
    });
  }

  if (closeEditBtn && editDrawer) {
    closeEditBtn.addEventListener('click', () => { editDrawer.style.display = 'none'; });
  }

  if (cancelEditBtn && editDrawer) {
    cancelEditBtn.addEventListener('click', () => { editDrawer.style.display = 'none'; });
  }

  // Refresh checklist
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.disabled = true;
      try {
        const [updatedApp, updatedChecklist, updatedFindings] = await Promise.all([
          api.getApplication(app.id),
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindings?.findings || [], state, router);
      } catch (err) {
        showGlobalAlert('danger', 'Refresh Failed', err.message);
      } finally {
        refreshBtn.disabled = false;
      }
    });
  }

  // Edit Parameters Submit
  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const intake = parseInt(document.getElementById('edit-intake')?.value, 10);
      const land = parseFloat(document.getElementById('edit-land')?.value);
      const faculty = parseInt(document.getElementById('edit-faculty')?.value, 10);
      const carpet = parseFloat(document.getElementById('edit-carpet')?.value);

      const saveBtn = document.getElementById('btn-save-params');
      const saveSpinner = document.getElementById('save-params-spinner');
      const saveText = document.getElementById('save-params-text');

      if (saveBtn) saveBtn.disabled = true;
      if (saveSpinner) saveSpinner.style.display = 'inline-block';
      if (saveText) saveText.textContent = 'Saving...';

      try {
        const payload = {
          total_intake_applied: intake,
          declared_land_acres: !isNaN(land) ? land : undefined,
          declared_faculty_count: !isNaN(faculty) ? faculty : undefined,
          declared_builtup_sqm: !isNaN(carpet) ? carpet : undefined
        };

        const updatedApp = await api.updateApplication(app.id, payload);
        showGlobalAlert('success', 'Parameters Saved', 'Application parameters successfully updated.');
        
        // Refresh workspace
        const [updatedChecklist, updatedFindingsData] = await Promise.all([
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindingsData?.findings || initialFindings || [], state, router);
      } catch (err) {
        console.error('Failed to update application:', err);
        showGlobalAlert('danger', 'Update Failed', err.message || 'Unable to update parameters.');
        if (saveBtn) saveBtn.disabled = false;
        if (saveSpinner) saveSpinner.style.display = 'none';
        if (saveText) saveText.textContent = 'Save Declared Parameters';
      }
    });
  }

  // Bind Evidence & Fields Inspection
  const inspectBtns = container.querySelectorAll('.btn-inspect-doc');
  inspectBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const docId = btn.getAttribute('data-doc-id');
      const version = parseInt(btn.getAttribute('data-version') || '1', 10);
      const docTitle = btn.getAttribute('data-doc-title') || 'Document';
      await openEvidenceModal(docId, version, docTitle, app, state, router);
    });
  });

  // Bind Re-Extract IDP Buttons
  const reprocessBtns = container.querySelectorAll('.btn-reprocess-doc');
  reprocessBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const docId = btn.getAttribute('data-doc-id');
      const version = parseInt(btn.getAttribute('data-version') || '1', 10);
      const docTitle = btn.getAttribute('data-doc-title') || 'Document';
      const origHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner" aria-hidden="true"></span> <span>Extracting...</span>`;

      try {
        const run = await api.processDocument(docId, version, true);
        showGlobalAlert(
          'success',
          'Document IDP Complete',
          `Successfully processed "${docTitle}". Extracted ${run.fields_count || 0} fields across ${run.pages_processed || 1} pages using ${run.extraction_method || 'pipeline'}.`
        );
        // Refresh workspace
        const [updatedApp, updatedChecklist, updatedFindingsData] = await Promise.all([
          api.getApplication(app.id),
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindingsData?.findings || initialFindings || [], state, router);
      } catch (err) {
        showGlobalAlert('danger', 'IDP Extraction Failed', err.message || 'Processing error occurred.');
        btn.disabled = false;
        btn.innerHTML = origHtml;
      }
    });
  });

  // Bind View PDF Buttons
  const viewBtns = container.querySelectorAll('.btn-view-doc');
  viewBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const docId = btn.getAttribute('data-doc-id');
      const version = btn.getAttribute('data-version') || 1;
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner" aria-hidden="true"></span> <span>Opening...</span>`;

      try {
        const blobUrl = await api.getDocumentBlobUrl(docId, version);
        window.open(blobUrl, '_blank');
      } catch (err) {
        showGlobalAlert('danger', 'Failed to Open Document', err.message || 'Unable to stream private document.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    });
  });

  // Bind Remove Document Buttons
  const removeBtns = container.querySelectorAll('.btn-remove-doc');
  removeBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const docType = btn.getAttribute('data-doc-type');
      const docTitle = btn.getAttribute('data-doc-title') || docType;
      const confirmRemove = window.confirm(`Are you sure you want to remove the uploaded document for "${docTitle}"?\n\nThis will reset the checklist slot to PENDING.`);
      if (!confirmRemove) return;

      btn.disabled = true;
      btn.textContent = 'Removing...';

      try {
        await api.deleteDocument(app.id, docType);
        showGlobalAlert('success', 'Document Removed', `The document for "${docTitle}" has been removed.`);
        
        // Refresh workspace
        const [updatedApp, updatedChecklist, updatedFindingsData] = await Promise.all([
          api.getApplication(app.id),
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindingsData?.findings || initialFindings || [], state, router);
      } catch (err) {
        showGlobalAlert('danger', 'Remove Failed', err.message || 'Failed to remove document.');
        btn.disabled = false;
        btn.textContent = '✕ Remove';
      }
    });
  });

  // Bind File Upload Inputs
  const fileInputs = container.querySelectorAll('.doc-file-input');
  fileInputs.forEach(input => {
    input.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const docType = input.getAttribute('data-doc-type');
      const inlineMsg = document.getElementById(`inline-msg-${docType}`);

      // Client-side Validation Checks
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        showInlineError(inlineMsg, 'Invalid file format: Only PDF documents (.pdf) are permitted.');
        input.value = '';
        return;
      }

      if (file.size === 0) {
        showInlineError(inlineMsg, 'Invalid file: The selected file is empty (0 bytes).');
        input.value = '';
        return;
      }

      const MAX_SIZE = 15 * 1024 * 1024; // 15MB
      if (file.size > MAX_SIZE) {
        const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
        showInlineError(inlineMsg, `File size limit exceeded: Selected file is ${sizeMb} MB (maximum allowed is 15 MB).`);
        input.value = '';
        return;
      }

      // Show Uploading Spinner
      showInlineLoading(inlineMsg, `Validating and uploading ${escapeHtml(file.name)} (${(file.size / (1024 * 1024)).toFixed(2)} MB)...`);
      input.disabled = true;

      try {
        const result = await api.uploadDocument(app.id, docType, file);
        showGlobalAlert('success', 'Upload Successful', `Successfully uploaded and validated ${escapeHtml(file.name)}. Stored as version v${result.version?.version_number || 1}.`);
        
        // Refresh workspace
        const [updatedApp, updatedChecklist, updatedFindingsData] = await Promise.all([
          api.getApplication(app.id),
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindingsData?.findings || initialFindings || [], state, router);
      } catch (err) {
        console.error('Upload failed:', err);
        showInlineError(inlineMsg, err.message || 'Upload failed. Ensure the file is a valid PDF and meets statutory guidelines.');
        input.disabled = false;
        input.value = '';
      }
    });
  });

  // Wire Run Pre-Scrutiny Validation Button
  const runValBtn = document.getElementById('btn-run-validation');
  if (runValBtn) {
    runValBtn.addEventListener('click', async () => {
      runValBtn.disabled = true;
      const spinner = document.getElementById('run-val-spinner');
      const text = document.getElementById('run-val-text');
      if (spinner) spinner.style.display = 'inline-block';
      if (text) text.textContent = 'Evaluating Regulatory Rules...';

      try {
        const valRun = await api.validateApplication(app.id);
        const [updatedApp, updatedChecklist, updatedFindingsData] = await Promise.all([
          api.getApplication(app.id),
          api.getChecklist(app.id),
          api.getApplicationFindings(app.id).catch(() => ({ findings: [] }))
        ]);
        renderWorkspace(updatedApp, updatedChecklist, updatedFindingsData?.findings || [], state, router);
      } catch (err) {
        console.error('Validation failed:', err);
        showGlobalAlert('danger', 'Pre-Scrutiny Evaluation Failed', err.message || 'Unable to execute regulatory evaluation.');
      } finally {
        runValBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (text) text.textContent = 'Run Pre-Scrutiny Checks';
      }
    });
  }

  // Load Initial Pre-Scrutiny Findings
  loadAndRenderFindings(app, state, router);

  function showGlobalAlert(type, title, msg) {
    if (!alertArea) return;
    alertArea.innerHTML = renderAlert(type, title, msg);
    alertArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function showInlineError(el, msg) {
    if (!el) return;
    el.style.display = 'block';
    el.innerHTML = `<span style="color: var(--color-red-600); font-weight: 500;">⚠ ${escapeHtml(msg)}</span>`;
  }

  function showInlineLoading(el, msg) {
    if (!el) return;
    el.style.display = 'block';
    el.innerHTML = `
      <div style="display: flex; align-items: center; gap: var(--space-2); color: var(--color-blue-700);">
        <span class="spinner" aria-hidden="true"></span>
        <span>${escapeHtml(msg)}</span>
      </div>
    `;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function loadAndRenderFindings(app, state, router) {
  const chipsTarget = document.getElementById('findings-summary-chips');
  const contentTarget = document.getElementById('findings-content-area');
  if (!contentTarget) return;

  try {
    const data = await api.getApplicationFindings(app.id);
    const findings = data.findings || [];

    if (findings.length === 0) {
      if (chipsTarget) chipsTarget.innerHTML = '';
      contentTarget.innerHTML = `
        <div style="text-align: center; padding: var(--space-6); color: var(--text-muted);">
          <div style="font-size: 28px; margin-bottom: var(--space-2); color: var(--color-blue-500);">${icons.info}</div>
          <p style="font-weight: 500;">No pre-scrutiny validation run recorded yet for this application.</p>
          <p style="font-size: var(--text-xs); margin-top: 4px;">Click <strong>"Run Pre-Scrutiny Checks"</strong> in the top header to evaluate uploaded document evidence against active AICTE APH 2024-2027 regulatory rules.</p>
        </div>
      `;
      return;
    }

    // Compute summary metrics
    const deficiencies = findings.filter(f => f.outcome === 'DEFICIENCY_DETECTED' || f.severity === 'DEFICIENCY').length;
    const warnings = findings.filter(f => f.severity === 'WARNING').length;
    const passed = findings.filter(f => f.outcome === 'NO_ISSUE_DETECTED').length;
    const unable = findings.filter(f => f.outcome === 'UNABLE_TO_EVALUATE' || f.outcome === 'RULE_UNAVAILABLE').length;

    if (chipsTarget) {
      chipsTarget.innerHTML = `
        <span class="badge ${deficiencies > 0 ? 'badge-danger' : 'badge-success'}" style="font-weight: 600;">${deficiencies} Deficiencies</span>
        <span class="badge ${warnings > 0 ? 'badge-warning' : 'badge-info'}">${warnings} Warnings</span>
        <span class="badge badge-success">${passed} Passed</span>
        <span class="badge badge-info">${unable} Inconclusive</span>
        <span class="badge badge-secondary">Run #${data.validation_run?.run_number || 1}</span>
      `;
    }

    contentTarget.innerHTML = `
      <!-- Mandatory Advisory Product Boundary Notice -->
      <div style="background-color: var(--color-blue-50); border-left: 4px solid var(--color-blue-600); padding: var(--space-3) var(--space-4); border-radius: var(--radius-xs); margin-bottom: var(--space-5); font-size: var(--text-xs); color: var(--color-blue-900); line-height: 1.5;">
        <strong>Advisory Decision-Support Notice:</strong> These findings represent deterministic regulatory pre-scrutiny evaluations comparing structured extracted parameters against the AICTE Approval Process Handbook (APH 2024-2027) catalogue. They assist institutions and scrutinizing officers by highlighting potential gaps and do not constitute an official statutory approval, rejection, or legal verdict.
      </div>

      <div class="findings-list" style="display: flex; flex-direction: column; gap: var(--space-4);">
        ${findings.map((f, idx) => renderFindingCard(f, idx, app)).join('')}
      </div>
    `;

    // Bind Visual Evidence modal inspection triggers on findings
    contentTarget.querySelectorAll('.btn-inspect-finding-evidence').forEach(btn => {
      btn.addEventListener('click', () => {
        const docId = btn.getAttribute('data-doc-id');
        const verNum = parseInt(btn.getAttribute('data-version') || '1', 10);
        const title = btn.getAttribute('data-title');
        if (docId) {
          openEvidenceModal(docId, verNum, title, app, state, router);
        }
      });
    });

    // Bind Statutory Grounding clause modal triggers
    contentTarget.querySelectorAll('.btn-inspect-aph-clause').forEach(btn => {
      btn.addEventListener('click', () => {
        const ruleCode = btn.getAttribute('data-rule-code');
        const modalHost = document.getElementById('grounding-modal-target');
        if (modalHost && ruleCode) {
          modalHost.innerHTML = renderStatutoryGroundingModal(ruleCode);
          const closeGModal = () => { modalHost.innerHTML = ''; };
          document.getElementById('btn-close-grounding-modal')?.addEventListener('click', closeGModal);
          document.getElementById('btn-dismiss-grounding-modal')?.addEventListener('click', closeGModal);
        }
      });
    });

  } catch (err) {
    console.error('Failed to load findings:', err);
    contentTarget.innerHTML = `
      <div style="padding: var(--space-4); color: var(--color-red-600); font-size: var(--text-sm);">
        ${icons.alertTriangle} Failed to load pre-scrutiny findings: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderFindingCard(f, idx, app) {
  const isDeficiency = f.outcome === 'DEFICIENCY_DETECTED' || f.severity === 'DEFICIENCY';
  const isPass = f.outcome === 'NO_ISSUE_DETECTED';
  const isWarning = f.severity === 'WARNING';

  let outcomeBadgeClass = 'badge-info';
  let outcomeLabel = (f.outcome || '').replace(/_/g, ' ');
  if (isDeficiency) {
    outcomeBadgeClass = 'badge-danger';
    outcomeLabel = 'DEFICIENCY DETECTED';
  } else if (isPass) {
    outcomeBadgeClass = 'badge-success';
    outcomeLabel = 'NO ISSUE DETECTED';
  } else if (isWarning) {
    outcomeBadgeClass = 'badge-warning';
    outcomeLabel = 'NEEDS REVIEW / INCONCLUSIVE';
  }

  const borderLeftColor = isDeficiency ? 'var(--color-red-600)' : isPass ? 'var(--color-green-600)' : 'var(--color-amber-500)';
  const evidence = f.evidence || {};
  const hasDocEvidence = evidence.document_id && evidence.page_number;
  const secondaryEvidence = evidence.secondary_evidence;

  return `
    <div class="finding-card" style="border: 1px solid var(--border-light); border-left: 4px solid ${borderLeftColor}; border-radius: var(--radius-sm); padding: var(--space-4) var(--space-5); background-color: var(--bg-surface);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: var(--space-2); margin-bottom: var(--space-2);">
        <div>
          <div style="display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;">
            <span class="badge badge-secondary" style="font-family: var(--font-mono); font-size: 11px;">${escapeHtml(f.rule_code)}</span>
            <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">${escapeHtml((f.category || '').replace(/_/g, ' '))}</span>
            <span class="badge ${outcomeBadgeClass}">${outcomeLabel}</span>
          </div>
          <h3 style="font-size: var(--text-base); margin-top: var(--space-1); color: var(--text-primary); font-weight: 600;">
            ${escapeHtml(f.title)}
          </h3>
        </div>

        ${hasDocEvidence ? `
          <button class="btn btn-secondary btn-sm btn-inspect-finding-evidence" data-doc-id="${evidence.document_id}" data-version="${evidence.version_number || 1}" data-title="${escapeHtml(f.title)}" title="Inspect grounded visual evidence and token coordinates">
            ${icons.search}
            <span>Inspect Evidence</span>
          </button>
        ` : ''}
      </div>

      <!-- Plain Language Explanation -->
      <p style="font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: var(--space-3);">
        ${escapeHtml(f.explanation)}
      </p>

      <!-- Expected vs Observed Parameters Comparison Box -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-3); background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-xs); padding: var(--space-3); margin-bottom: var(--space-3);">
        <div>
          <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 500;">Expected Condition (APH Norm)</div>
          <div style="font-size: var(--text-sm); font-weight: 600; color: var(--color-green-800); margin-top: 2px;">
            ${escapeHtml(f.expected_value || 'Compliant with statutory standard')}
          </div>
        </div>
        <div>
          <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 500;">Observed Value (Extraction Evidence)</div>
          <div style="font-size: var(--text-sm); font-weight: 600; color: ${isDeficiency ? 'var(--color-red-700)' : 'var(--text-primary)'}; margin-top: 2px;">
            ${escapeHtml(f.observed_value || 'None')}
          </div>
        </div>
      </div>

      <!-- Cross-Document Secondary Evidence (if present) -->
      ${secondaryEvidence ? `
        <div style="background-color: var(--color-blue-50); border: 1px dashed var(--color-blue-300); border-radius: var(--radius-xs); padding: var(--space-3); margin-bottom: var(--space-3); font-size: var(--text-xs);">
          <div style="font-weight: 600; color: var(--color-blue-900); margin-bottom: 2px;">Cross-Document Reconciliation Evidence:</div>
          <div style="color: var(--color-blue-800);">
            Comparing with <strong>${escapeHtml(secondaryEvidence.document_type || 'Secondary Document')}</strong> (Page ${secondaryEvidence.page_number || 1}):
            <span style="font-family: var(--font-mono); background-color: #FFFFFF; padding: 2px 6px; border-radius: 3px; border: 1px solid var(--color-blue-200); margin-left: 4px;">
              "${escapeHtml(secondaryEvidence.raw_text || secondaryEvidence.normalized_value)}"
            </span>
          </div>
        </div>
      ` : ''}

      <!-- Official Regulatory Source & Recommended Remediation Action -->
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-2); font-size: 11px; color: var(--text-muted); border-top: 1px solid var(--border-light); padding-top: var(--space-2); margin-top: var(--space-2);">
        <div style="display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap;">
          <span>Official Authority: <strong style="color: var(--text-secondary);">${escapeHtml(f.official_source || 'AICTE APH 2024-2027')}</strong></span>
          <button type="button" class="btn btn-ghost btn-sm btn-inspect-aph-clause" data-rule-code="${escapeHtml(f.rule_code)}" style="font-size: 11px; color: var(--color-blue-700); padding: 2px 6px;" title="View official verbatim AICTE APH clause and regulatory grounding">
            ${icons.scale}
            <span>APH Clause</span>
          </button>
        </div>
        <div>
          <span>Action: <strong style="color: var(--text-primary);">${escapeHtml(f.recommended_action || 'Review and verify.')}</strong></span>
        </div>
      </div>
    </div>
  `;
}

async function openEvidenceModal(docId, version, docTitle, app, state, router) {
  const modalTarget = document.getElementById('evidence-modal-target');
  if (!modalTarget) return;

  // Show loading modal immediately
  modalTarget.innerHTML = `
    <div class="modal-backdrop open" id="evidence-modal-backdrop">
      <div class="modal-dialog" style="max-width: 900px;">
        <div class="modal-header">
          <div class="modal-title" style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.shieldCheck}
            <span>Loading Evidence & Provenance: ${escapeHtml(docTitle)}</span>
          </div>
          <button type="button" class="modal-close" id="btn-close-evidence-modal">✕</button>
        </div>
        <div class="modal-body" style="text-align: center; padding: var(--space-12);">
          <div class="spinner" style="width: 32px; height: 32px; margin: 0 auto var(--space-4);" aria-hidden="true"></div>
          <p style="color: var(--text-muted); font-size: var(--text-sm);">Fetching structured field extractions and spatial coordinates...</p>
        </div>
      </div>
    </div>
  `;

  document.getElementById('btn-close-evidence-modal')?.addEventListener('click', () => {
    modalTarget.innerHTML = '';
  });

  try {
    const [result, pages] = await Promise.all([
      api.getDocumentExtractedFields(docId, version),
      api.getDocumentPages(docId, version)
    ]);

    const run = result.processing_run || {};
    const fields = result.extracted_fields || [];
    const method = run.extraction_method || 'HYBRID';
    const avgConf = run.average_confidence ? (run.average_confidence * 100).toFixed(1) + '%' : '100.0%';

    let fieldsHtml = '';
    if (fields.length === 0) {
      fieldsHtml = `
        <div style="text-align: center; padding: var(--space-8); background-color: var(--color-slate-50); border-radius: var(--radius-md);">
          <div style="font-size: var(--text-base); font-weight: bold; margin-bottom: var(--space-2); color: var(--text-muted);">No structured fields extracted</div>
          <p style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4);">
            The document text has been indexed, but no specific statutory pattern matches were recognized for this document type.
          </p>
          <button class="btn btn-secondary btn-sm" id="btn-modal-reprocess">
            ${icons.refresh}
            <span>Force Re-Run Pipeline</span>
          </button>
        </div>
      `;
    } else {
      fieldsHtml = `
        <div style="overflow-x: auto;">
          <table class="table" style="width: 100%; font-size: var(--text-xs);">
            <thead>
              <tr style="border-bottom: 2px solid var(--border-light); text-align: left;">
                <th style="padding: var(--space-2) var(--space-3);">Field Label & Key</th>
                <th style="padding: var(--space-2) var(--space-3);">Normalized Value</th>
                <th style="padding: var(--space-2) var(--space-3);">Raw Text Snippet</th>
                <th style="padding: var(--space-2) var(--space-3);">Page & Bounding Box</th>
                <th style="padding: var(--space-2) var(--space-3);">Confidence</th>
                <th style="padding: var(--space-2) var(--space-3);">Method</th>
              </tr>
            </thead>
            <tbody>
              ${fields.map(f => {
                const confPct = (f.confidence * 100).toFixed(1);
                const confColor = f.confidence >= 0.9 ? 'badge-success' : (f.confidence >= 0.7 ? 'badge-warning' : 'badge-danger');
                const boxStr = f.bounding_box 
                  ? `[${f.bounding_box.ymin.toFixed(2)}, ${f.bounding_box.xmin.toFixed(2)}, ${f.bounding_box.ymax.toFixed(2)}, ${f.bounding_box.xmax.toFixed(2)}]`
                  : 'Page-level';
                return `
                  <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: var(--space-2) var(--space-3);">
                      <div style="font-weight: 600; color: var(--text-primary);">${escapeHtml(f.field_label)}</div>
                      <div style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${escapeHtml(f.field_key)}</div>
                    </td>
                    <td style="padding: var(--space-2) var(--space-3);">
                      <span style="font-weight: bold; color: var(--color-blue-800); background-color: var(--color-blue-50); padding: 2px 6px; border-radius: 4px;">
                        ${escapeHtml(f.normalized_value)}
                      </span>
                      <span class="badge badge-info" style="font-size: 9px; margin-left: 4px;">${f.data_type}</span>
                    </td>
                    <td style="padding: var(--space-2) var(--space-3); max-width: 200px;">
                      <div style="font-family: var(--font-mono); font-size: 11px; color: var(--color-slate-700); background-color: var(--color-slate-100); padding: 2px 4px; border-radius: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(f.raw_value)}">
                        "${escapeHtml(f.raw_value)}"
                      </div>
                    </td>
                    <td style="padding: var(--space-2) var(--space-3);">
                      <div><strong>Page ${f.page_number}</strong></div>
                      <div style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${boxStr}</div>
                    </td>
                    <td style="padding: var(--space-2) var(--space-3);">
                      <span class="badge ${confColor}" style="font-size: 10px;">${confPct}%</span>
                    </td>
                    <td style="padding: var(--space-2) var(--space-3);">
                      <span class="badge ${f.extraction_method === 'OCR' ? 'badge-warning' : 'badge-info'}" style="font-size: 9px;">
                        ${f.extraction_method}
                      </span>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    let pagesHtml = '';
    if (pages.length === 0) {
      pagesHtml = `<p style="color: var(--text-muted); font-size: var(--text-xs);">No page-level text recorded.</p>`;
    } else {
      pagesHtml = `
        <div style="display: flex; flex-direction: column; gap: var(--space-4);">
          ${pages.map(p => `
            <div style="border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: var(--space-3); background-color: var(--color-slate-50);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2); flex-wrap: wrap; gap: var(--space-2);">
                <div style="font-weight: 600; font-size: var(--text-xs); color: var(--text-primary);">
                  Page ${p.page_number} (${p.char_count} characters • ${p.word_count} words)
                </div>
                <div style="display: flex; gap: var(--space-2); align-items: center;">
                  <span class="badge ${p.extraction_method === 'OCR' ? 'badge-warning' : 'badge-info'}" style="font-size: 10px;">
                    Method: ${p.extraction_method}
                  </span>
                  <span class="badge badge-success" style="font-size: 10px;">
                    Conf: ${(p.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div style="font-family: var(--font-mono); font-size: 11px; max-height: 180px; overflow-y: auto; background-color: var(--color-white); padding: var(--space-3); border-radius: var(--radius-sm); border: 1px solid var(--border-light); white-space: pre-wrap; line-height: 1.4; color: var(--color-slate-800);">
                ${escapeHtml(p.text_content || 'No text content available on this page.')}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    modalTarget.innerHTML = `
      <div class="modal-backdrop open" id="evidence-modal-backdrop">
        <div class="modal-dialog" style="max-width: 960px; max-height: 90vh;">
          <div class="modal-header">
            <div class="modal-title" style="display: flex; align-items: center; gap: var(--space-3);">
              ${icons.shieldCheck}
              <div>
                <div style="font-size: var(--text-base); font-weight: bold;">
                  ${escapeHtml(docTitle)} (v${version})
                </div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">
                  IDP Pipeline v1.0.0 • Run #${escapeHtml(run.run_id ? run.run_id.substring(0, 8) : 'N/A')}
                </div>
              </div>
            </div>
            <button type="button" class="modal-close" id="btn-close-evidence-modal" aria-label="Close modal">✕</button>
          </div>

          <div class="modal-body" style="padding: var(--space-5);">
            <!-- Metrics Bar -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: var(--space-3); margin-bottom: var(--space-4);">
              <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Run Status</div>
                <div style="font-weight: bold; font-size: var(--text-sm);">${renderBadge(result.status, result.status)}</div>
              </div>
              <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Extraction Method</div>
                <div style="font-weight: bold; font-size: var(--text-sm); color: var(--color-blue-700);">${method}</div>
              </div>
              <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Pages Processed</div>
                <div style="font-weight: bold; font-size: var(--text-sm); color: var(--text-primary);">${run.pages_digital || 0} Digital / ${run.pages_ocr || 0} OCR</div>
              </div>
              <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Avg Confidence</div>
                <div style="font-weight: bold; font-size: var(--text-sm); color: var(--color-green-700);">${avgConf}</div>
              </div>
              <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Fields Grounded</div>
                <div style="font-weight: bold; font-size: var(--text-sm); color: var(--text-primary);">${fields.length} Fields</div>
              </div>
            </div>

            <!-- Mandatory Disclaimer Alert -->
            <div style="margin-bottom: var(--space-4);">
              ${renderAlert('info', 'AICTE Pre-Scrutiny Decision-Support Notice',
                'Extracted parameters are preliminary machine-generated evidence. They do not constitute statutory compliance, proof of document authenticity, or official approval. The regulatory cross-matching engine (Engine B) evaluates these against AICTE norms.'
              )}
            </div>

            <!-- Tabs -->
            <div style="display: flex; gap: var(--space-2); border-bottom: 2px solid var(--border-light); margin-bottom: var(--space-4);">
              <button type="button" id="tab-fields-btn" class="btn btn-ghost btn-sm" style="font-weight: bold; border-bottom: 2px solid var(--color-blue-600); border-radius: 0; margin-bottom: -2px;">
                Structured Extracted Fields (${fields.length})
              </button>
              <button type="button" id="tab-pages-btn" class="btn btn-ghost btn-sm" style="font-weight: normal; border-radius: 0; margin-bottom: -2px; color: var(--text-muted);">
                Extracted Page Text (${pages.length} Pages)
              </button>
            </div>

            <!-- Tab Content -->
            <div id="tab-fields-content">
              ${fieldsHtml}
            </div>
            <div id="tab-pages-content" style="display: none;">
              ${pagesHtml}
            </div>
          </div>

          <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 11px; color: var(--text-muted);">
              Document ID: <code>${docId}</code> (v${version})
            </div>
            <div style="display: flex; gap: var(--space-2);">
              <button type="button" id="btn-modal-reprocess" class="btn btn-secondary btn-sm">
                ${icons.refresh}
                <span>Re-Run Extraction (Force)</span>
              </button>
              <button type="button" id="btn-modal-view-pdf" class="btn btn-secondary btn-sm">
                ${icons.eye}
                <span>View Original PDF</span>
              </button>
              <button type="button" id="btn-modal-close-footer" class="btn btn-primary btn-sm">
                <span>Done</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Tab switcher events
    const tabFieldsBtn = document.getElementById('tab-fields-btn');
    const tabPagesBtn = document.getElementById('tab-pages-btn');
    const tabFieldsContent = document.getElementById('tab-fields-content');
    const tabPagesContent = document.getElementById('tab-pages-content');

    tabFieldsBtn?.addEventListener('click', () => {
      tabFieldsBtn.style.borderBottom = '2px solid var(--color-blue-600)';
      tabFieldsBtn.style.fontWeight = 'bold';
      tabFieldsBtn.style.color = 'var(--text-primary)';
      tabPagesBtn.style.borderBottom = 'none';
      tabPagesBtn.style.fontWeight = 'normal';
      tabPagesBtn.style.color = 'var(--text-muted)';
      tabFieldsContent.style.display = 'block';
      tabPagesContent.style.display = 'none';
    });

    tabPagesBtn?.addEventListener('click', () => {
      tabPagesBtn.style.borderBottom = '2px solid var(--color-blue-600)';
      tabPagesBtn.style.fontWeight = 'bold';
      tabPagesBtn.style.color = 'var(--text-primary)';
      tabFieldsBtn.style.borderBottom = 'none';
      tabFieldsBtn.style.fontWeight = 'normal';
      tabFieldsBtn.style.color = 'var(--text-muted)';
      tabPagesContent.style.display = 'block';
      tabFieldsContent.style.display = 'none';
    });

    // Close actions
    const closeModal = () => { modalTarget.innerHTML = ''; };
    document.getElementById('btn-close-evidence-modal')?.addEventListener('click', closeModal);
    document.getElementById('btn-modal-close-footer')?.addEventListener('click', closeModal);

    // View PDF
    document.getElementById('btn-modal-view-pdf')?.addEventListener('click', async () => {
      try {
        const blobUrl = await api.getDocumentBlobUrl(docId, version);
        window.open(blobUrl, '_blank');
      } catch (err) {
        alert('Failed to stream document: ' + err.message);
      }
    });

    // Force Reprocess
    document.getElementById('btn-modal-reprocess')?.addEventListener('click', async () => {
      const repBtn = document.getElementById('btn-modal-reprocess');
      if (repBtn) {
        repBtn.disabled = true;
        repBtn.innerHTML = `<span class="spinner" aria-hidden="true"></span> <span>Extracting...</span>`;
      }
      try {
        await api.processDocument(docId, version, true);
        await openEvidenceModal(docId, version, docTitle, app, state, router);
      } catch (err) {
        alert('Reprocessing failed: ' + err.message);
        if (repBtn) {
          repBtn.disabled = false;
          repBtn.innerHTML = `${icons.refresh} <span>Re-Run Extraction (Force)</span>`;
        }
      }
    });
  } catch (err) {
    console.error('Failed to load extraction modal:', err);
    modalTarget.innerHTML = `
      <div class="modal-backdrop open" id="evidence-modal-backdrop">
        <div class="modal-dialog" style="max-width: 600px;">
          <div class="modal-header">
            <div class="modal-title">Extraction Results Unavailable</div>
            <button type="button" class="modal-close" id="btn-close-evidence-modal">✕</button>
          </div>
          <div class="modal-body">
            ${renderAlert('danger', 'Unable to Load Extraction Results', err.message || 'Server error.')}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="btn-modal-close-error">Close</button>
          </div>
        </div>
      </div>
    `;
    document.getElementById('btn-close-evidence-modal')?.addEventListener('click', () => { modalTarget.innerHTML = ''; });
    document.getElementById('btn-modal-close-error')?.addEventListener('click', () => { modalTarget.innerHTML = ''; });
  }
}

// -------------------------------------------------------------------------
// Pre-Scrutiny Assessment Dossier Generator & Print View
// -------------------------------------------------------------------------
function openDossierModal(app, checklist, findings, state) {
  const existing = document.getElementById('pre-scrutiny-dossier-modal');
  if (existing) existing.remove();

  const user = state.getCurrentUser() || {};
  const institutionName = user.institution?.name || user.institution || 'Authorised Institution';
  const items = checklist.checklist || checklist.items || [];
  const totalSlots = checklist.total_slots || items.length || 8;
  const uploadedSlots = checklist.uploaded_slots !== undefined ? checklist.uploaded_slots : items.filter(d => d.status === 'UPLOADED').length;

  const deficienciesCount = findings.filter(f => (f.outcome === 'DEFICIENCY_DETECTED' || f.severity === 'DEFICIENCY') && f.status !== 'RESOLVED').length;
  const warningsCount = findings.filter(f => f.severity === 'WARNING' && f.status !== 'RESOLVED').length;

  const readinessScore = Math.max(0, Math.min(100, Math.round(
    ((uploadedSlots / totalSlots) * 50) +
    (deficienciesCount === 0 ? 35 : Math.max(0, 35 - deficienciesCount * 12)) +
    (warningsCount === 0 ? 15 : Math.max(0, 15 - warningsCount * 5))
  )));

  const modalHtml = `
    <div id="pre-scrutiny-dossier-modal" class="modal-backdrop dossier-print-container" style="position: fixed; inset: 0; background: rgba(15, 23, 42, 0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: var(--space-4); overflow-y: auto;">
      <div class="card dossier-paper" style="max-width: 820px; width: 100%; max-height: 95vh; overflow-y: auto; box-shadow: var(--shadow-lg); background: #FFFFFF; border-radius: var(--radius-md);">
        
        <!-- Dossier Header -->
        <div style="padding: var(--space-6); border-bottom: 2px solid var(--color-blue-800); background: #F8FAFC;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-4);">
            <div style="display: flex; align-items: center; gap: var(--space-3);">
              <div style="width: 48px; height: 48px; border-radius: 8px; background: var(--color-blue-800); color: white; display: flex; align-items: center; justify-content: center;">
                ${icons.scale}
              </div>
              <div>
                <div style="font-size: 11px; font-weight: 700; color: var(--color-blue-800); text-transform: uppercase; letter-spacing: 0.5px;">AICTE Pre-Scrutiny &amp; Deficiency Platform (SIH Prototype)</div>
                <h2 style="margin: 2px 0 0 0; font-size: 18px; color: #0F172A;">Institutional Pre-Scrutiny Working Dossier (EoA)</h2>
                <div style="font-size: 12px; color: var(--text-muted);">Academic Year: <strong>${escapeHtml(app.academic_year || '2024-2025')}</strong> • Working Draft: ${new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
              </div>
            </div>
            <div class="no-print" style="display: flex; gap: var(--space-2);">
              <button type="button" id="btn-print-dossier-action" class="btn btn-primary btn-sm" title="Print or save as PDF">
                ${icons.clipboardList}
                <span>Print Dossier</span>
              </button>
              <button type="button" id="btn-close-dossier-modal" class="btn btn-ghost btn-sm" aria-label="Close">✕</button>
            </div>
          </div>
        </div>

        <!-- Dossier Body -->
        <div style="padding: var(--space-6);">
          
          <!-- Neutral Prototype Advisory Disclaimer -->
          <div style="background-color: var(--color-amber-50, #FFFBEB); border: 1px solid var(--color-amber-300, #FCD34D); border-left: 4px solid var(--color-amber-600, #D97706); padding: var(--space-3) var(--space-4); border-radius: var(--radius-xs); margin-bottom: var(--space-4); font-size: 11px; color: var(--color-amber-950, #451A03); line-height: 1.5;">
            <strong>SIH Prototype — Not an official AICTE portal.</strong> This generated report is a decision-support aid, not an official AICTE assessment, approval or certificate. Final regulatory authority rests exclusively with the authorized AICTE Scrutiny Committee.
          </div>
          
          <!-- Institutional Metadata -->
          <div style="background: #F1F5F9; border-radius: var(--radius-sm); padding: var(--space-4); margin-bottom: var(--space-5);">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-3); font-size: 12px;">
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Application Reference</span>
                <div style="font-weight: 700; font-family: var(--font-mono); color: var(--color-blue-900);">${escapeHtml(app.application_number)}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Institution Name</span>
                <div style="font-weight: 700; color: #0F172A;">${escapeHtml(institutionName)}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Programme Category</span>
                <div style="font-weight: 600;">${escapeHtml(app.program_category || 'Engineering & Technology')}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Pre-Scrutiny Readiness</span>
                <div style="font-weight: 800; color: ${readinessScore >= 80 ? 'var(--color-green-700)' : readinessScore >= 60 ? 'var(--color-amber-700)' : 'var(--color-red-700)'};">${readinessScore}% Readiness Index</div>
              </div>
            </div>
          </div>

          <!-- Parameter Summary Table -->
          <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: var(--space-2); color: var(--color-blue-900);">Declared Institutional Parameters</h4>
          <div class="table-responsive" style="overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; margin-bottom: var(--space-5);">
            <table class="data-table" style="width: 100%; font-size: 12px; margin-bottom: 0;">
              <thead>
                <tr style="background: #F8FAFC;">
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Applied Intake</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Declared Land (Acres)</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Declared Faculty Count</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Built-up Area (Sq.m)</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Current Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="font-weight: 700; overflow-wrap: anywhere; word-break: break-word;">${app.total_intake_applied || 720} Seats</td>
                  <td style="overflow-wrap: anywhere; word-break: break-word;">${app.declared_land_acres || 5.2} Acres</td>
                  <td style="overflow-wrap: anywhere; word-break: break-word;">${app.declared_faculty_count || 35} Members</td>
                  <td style="overflow-wrap: anywhere; word-break: break-word;">${app.declared_builtup_sqm || 8420} Sq.m</td>
                  <td style="overflow-wrap: anywhere; word-break: break-word;"><span class="badge badge-info">${app.status}</span></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Statutory 8-Document Ingestion Checklist -->
          <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: var(--space-2); color: var(--color-blue-900);">Statutory Document Checklist Verification (${uploadedSlots}/${totalSlots})</h4>
          <div class="table-responsive" style="overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; margin-bottom: var(--space-5);">
            <table class="data-table" style="width: 100%; font-size: 11px; margin-bottom: 0;">
              <thead>
                <tr style="background: #F8FAFC;">
                  <th style="width: 30px;">#</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Mandatory Statutory Document</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Status</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">Version</th>
                  <th style="overflow-wrap: anywhere; word-break: break-word;">File Integrity SHA-256</th>
                </tr>
              </thead>
              <tbody>
                ${items.map((doc, i) => {
                  const isUp = doc.status === 'UPLOADED' && doc.current_version;
                  const v = doc.current_version;
                  const hash = v?.file_hash_sha256 ? `${v.file_hash_sha256.substring(0, 10)}...` : '—';
                  return `
                    <tr>
                      <td>${i + 1}</td>
                      <td style="font-weight: 600; overflow-wrap: anywhere; word-break: break-word;">${escapeHtml(doc.title || doc.document_type)}</td>
                      <td><span class="badge ${isUp ? 'badge-success' : 'badge-danger'}">${isUp ? 'UPLOADED' : 'PENDING'}</span></td>
                      <td>${isUp ? `v${v.version_number}` : '—'}</td>
                      <td style="font-family: var(--font-mono); overflow-wrap: anywhere; word-break: break-word;">${hash}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>

          <!-- Pre-Scrutiny Discrepancies & Regulatory Findings -->
          <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: var(--space-2); color: var(--color-blue-900);">Pre-Scrutiny Discrepancies & Regulatory Evaluation (${findings.length} Evaluated)</h4>
          ${findings.length === 0 ? `
            <div style="padding: var(--space-3); background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: var(--radius-sm); font-size: 12px; color: #166534; margin-bottom: var(--space-5);">
              ✓ No discrepancies recorded. All active regulatory checks passed successfully.
            </div>
          ` : `
            <div style="display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-5);">
              ${findings.map(f => {
                const isDef = f.severity === 'DEFICIENCY' || f.outcome === 'DEFICIENCY_DETECTED';
                return `
                  <div style="border: 1px solid var(--border-light); border-left: 3px solid ${isDef ? 'var(--color-red-600)' : 'var(--color-amber-500)'}; padding: var(--space-3); border-radius: var(--radius-xs); font-size: 11px; background: #FAFAFA;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                      <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-blue-800);">${escapeHtml(f.rule_code)}: ${escapeHtml(f.title || f.rule_title)}</span>
                      <span class="badge ${isDef ? 'badge-danger' : 'badge-warning'}">${escapeHtml(f.severity || 'WARNING')}</span>
                    </div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">${escapeHtml(f.explanation)}</div>
                    <div style="display: flex; gap: var(--space-4); color: var(--text-muted); font-size: 10px;">
                      <span>Expected: <strong style="color: var(--color-green-700);">${escapeHtml(f.expected_value || 'Compliant')}</strong></span>
                      <span>Observed: <strong style="color: var(--color-red-700);">${escapeHtml(f.observed_value || 'Deficient')}</strong></span>
                      <span>Source: <em>${escapeHtml(f.official_source || 'AICTE APH 2024–27')}</em></span>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          `}

          <!-- Legal Disclaimer Notice -->
          <div style="border-top: 1px solid var(--border-light); padding-top: var(--space-4); font-size: 10px; color: var(--text-muted); line-height: 1.4;">
            <strong>Statutory Boundary & Decision-Support Notice:</strong> This document is generated by the AICTE Pre-Scrutiny & Deficiency Resolution Platform for preparatory pre-scrutiny and deficiency remediation. It is an advisory decision-support instrument and does not constitute official approval, rejection, or formal regulatory clearance by the All India Council for Technical Education. Final regulatory decisions remain strictly under the authority of the designated AICTE Scrutiny Committee, Hearing Committee, and Executive Committee.
          </div>

        </div>

        <!-- Dossier Footer -->
        <div class="card-footer no-print" style="display: flex; justify-content: flex-end; gap: var(--space-3); padding: var(--space-3) var(--space-6); background: #F8FAFC; border-top: 1px solid var(--border-light);">
          <button type="button" id="btn-dossier-dismiss" class="btn btn-secondary btn-sm">Close</button>
          <button type="button" id="btn-dossier-print-trigger" class="btn btn-primary btn-sm">
            ${icons.clipboardList}
            <span>Print / Save PDF</span>
          </button>
        </div>

      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const modalEl = document.getElementById('pre-scrutiny-dossier-modal');
  const closeDossier = () => modalEl?.remove();

  document.getElementById('btn-close-dossier-modal')?.addEventListener('click', closeDossier);
  document.getElementById('btn-dossier-dismiss')?.addEventListener('click', closeDossier);
  document.getElementById('btn-print-dossier-action')?.addEventListener('click', () => window.print());
  document.getElementById('btn-dossier-print-trigger')?.addEventListener('click', () => window.print());
}
