// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Reviewer Scrutiny Console (frontend/js/views/reviewer-scrutiny.js)

import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert } from '../components.js';
import { api } from '../api.js';

export function renderReviewerScrutiny(state, params) {
  const appId = params.id || 'app_9812';
  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Scrutiny Queue', href: '#/reviewer/queue' },
    { label: `Scrutiny Console (${appId.slice(0, 8)})` }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div id="scrutiny-console-root">
        <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
          <span class="spinner" aria-hidden="true"></span>
          <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading case records, findings, and applicant submissions from backend...</p>
        </div>
      </div>
    </div>
  `;
}

export async function initReviewerScrutinyView(state, router, params) {
  const root = document.getElementById('scrutiny-console-root');
  if (!root) return;

  // Resolve application ID from router-invoked (state, router, params) or direct (state, params)
  const resolvedParams = (params && params.id) ? params : (router && router.id ? router : {});
  const appId = resolvedParams.id;
  if (!appId) {
    root.innerHTML = `<div class="alert alert-danger">Error: Missing Application ID.</div>`;
    return;
  }

  async function loadCaseData() {
    try {
      const data = await api.getScrutinyDetails(appId);
      renderCaseConsole(data);
    } catch (err) {
      root.innerHTML = `
        <div style="padding: var(--space-8); text-align: center; color: var(--color-red-600);">
          <p style="font-weight: 700; font-size: 16px;">Failed to load scrutiny case details</p>
          <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">${err.message}</p>
          <div style="margin-top: var(--space-4);">
            <a href="#/reviewer/queue" class="btn btn-secondary btn-sm" style="margin-right: 8px;">Back to Queue</a>
            <button id="btn-retry-case" class="btn btn-primary btn-sm">Retry</button>
          </div>
        </div>
      `;
      document.getElementById('btn-retry-case')?.addEventListener('click', loadCaseData);
    }
  }

  function renderCaseConsole(data) {
    const app = data.application;
    const currentUser = state.getCurrentUser() || {};
    const findings = data.findings || [];
    const submissions = data.correction_submissions || [];
    const observations = data.observations || [];
    const checklist = data.checklist || [];

    const isAssignedToMe = app.assigned_reviewer_id === currentUser.id;

    root.innerHTML = `
      <!-- Case Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <div style="display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap;">
            <h1 style="margin: 0;">Case Assessment: ${app.application_number}</h1>
            ${renderBadge(app.review_status, app.review_status.replace(/_/g, ' '))}
            ${renderBadge(app.status, app.status.replace(/_/g, ' '))}
          </div>
          <p style="color: var(--text-muted); margin-top: 6px; font-size: 14px;">
            <strong>${app.institution_name}</strong> • AICTE Permanent ID: <code>${app.aicte_permanent_id}</code> • ${app.district}, ${app.state}
          </p>
        </div>
        <div style="display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap;">
          <button id="btn-export-scrutiny-dossier" class="btn btn-secondary btn-sm" title="Generate printable Official Scrutiny Assessment Dossier">
            ${icons.clipboardList}
            <span>Print Scrutiny Dossier</span>
          </button>
          <a href="#/reviewer/queue" class="btn btn-secondary">
            ${icons.chevronRight}
            <span>Back to Queue</span>
          </a>
        </div>
      </div>

      <!-- Scrutiny Meta Bar -->
      <div class="card" style="margin-bottom: var(--space-6); background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);">
        <div class="card-body" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-4); padding: var(--space-4);">
          <div style="display: flex; gap: var(--space-6); align-items: center; flex-wrap: wrap;">
            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Assigned Reviewer</div>
              <div style="font-weight: 700; color: var(--color-blue-800); margin-top: 2px;">
                ${app.assigned_reviewer_name ? app.assigned_reviewer_name : '<span style="color: var(--color-amber-700);">Unassigned</span>'}
              </div>
            </div>
            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Pre-Scrutiny Score</div>
              <div style="font-weight: 700; font-size: 16px; color: ${app.pre_scrutiny_score >= 80 ? 'var(--color-green-700)' : 'var(--color-amber-600)'}; margin-top: 2px;">
                ${app.pre_scrutiny_score}%
              </div>
            </div>
            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Active Deficiencies</div>
              <div style="font-weight: 700; color: var(--color-red-600); margin-top: 2px;">
                ${app.deficiencies_count} Blocking / ${app.warnings_count} Warnings
              </div>
            </div>
          </div>

          <!-- Quick Assignment Action -->
          <div style="display: flex; gap: var(--space-2); align-items: center;">
            ${!isAssignedToMe ? `
              <button id="btn-self-assign-case" class="btn btn-secondary btn-sm">
                ${icons.shieldCheck}
                <span>Assign Case to Me</span>
              </button>
            ` : `
              <span class="badge badge-compliant" style="padding: 6px 12px; font-size: 11px;">
                ✓ Assigned to You
              </span>
            `}
          </div>
        </div>
      </div>

      <!-- Main Layout -->
      <div class="scrutiny-console-layout" style="display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--space-6);">
        
        <!-- LEFT COLUMN: Findings, Submissions, & Documents -->
        <div>
          <!-- P7 Discrepancies Card -->
          <div class="card" style="margin-bottom: var(--space-6);">
            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
              <div class="card-title">
                ${icons.alertTriangle}
                <span>Discrepancies Flagged by Regulatory Engine (${findings.length})</span>
              </div>
              <span class="badge badge-deficiency">Pre-Scrutiny Baseline</span>
            </div>
            <div class="card-body">
              ${findings.length === 0 ? `
                <div style="padding: var(--space-4); text-align: center; color: var(--text-muted);">
                  🎉 Zero regulatory findings identified for this application package.
                </div>
              ` : findings.map(f => {
                const isResolved = f.status === 'RESOLVED';
                const isAwaitingReview = f.status === 'AWAITING_REVIEW';
                
                return `
                  <div style="border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-4); margin-bottom: var(--space-4); background-color: ${isResolved ? '#f0fdf4' : isAwaitingReview ? '#fffbeb' : '#fafafa'}; border-left: 4px solid ${isResolved ? 'var(--color-green-600)' : isAwaitingReview ? 'var(--color-amber-500)' : 'var(--color-red-600)'};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
                      <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: var(--color-blue-800);">
                        ${f.rule_code}
                      </span>
                      <div style="display: flex; gap: var(--space-2); align-items: center;">
                        ${renderBadge(f.severity, f.severity)}
                        ${renderBadge(f.status, f.status.replace(/_/g, ' '))}
                      </div>
                    </div>
                    <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">${f.rule_title}</div>
                    <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: var(--space-3);">
                      ${f.explanation}
                    </p>

                    <!-- Statutory Norm Comparison -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); background: white; border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-3); margin-bottom: var(--space-3); font-size: 12px;">
                      <div>
                        <span style="color: var(--text-muted); font-size: 10px; text-transform: uppercase; font-weight: 600;">Expected Statutory Value</span>
                        <div style="font-family: var(--font-mono); font-weight: 600; color: var(--color-green-700);">${f.expected_value || 'Mandatory Compliance'}</div>
                      </div>
                      <div>
                        <span style="color: var(--text-muted); font-size: 10px; text-transform: uppercase; font-weight: 600;">Observed Value in Document</span>
                        <div style="font-family: var(--font-mono); font-weight: 600; color: var(--color-red-700);">${f.observed_value || 'Deficient'}</div>
                      </div>
                    </div>

                    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: var(--space-3);">
                      <strong>Source Clause:</strong> ${f.official_source}
                    </div>

                    <!-- Action Bar -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-light); padding-top: var(--space-2);">
                      <span style="font-size: 11px; color: var(--text-muted);">
                        Document: Page ${f.evidence_page_number || 1}
                      </span>
                      <a href="#/applications/${app.id}/evidence/${f.id}" class="btn btn-secondary btn-sm" target="_blank" title="Open split-screen viewer with bounding box overlay">
                        ${icons.eye}
                        <span>Inspect Evidence (PDF)</span>
                      </a>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>

          <!-- P8 Applicant Corrections & Revalidation Submissions -->
          <div class="card" style="margin-bottom: var(--space-6);">
            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
              <div class="card-title">
                ${icons.refresh}
                <span>Applicant Corrective Submissions & Revalidations (${submissions.length})</span>
              </div>
              <span class="badge badge-info">P8 Resolution Bridge</span>
            </div>
            <div class="card-body">
              ${submissions.length === 0 ? `
                <div style="padding: var(--space-4); text-align: center; color: var(--text-muted);">
                  No corrective submissions have been submitted by the institutional applicant yet.
                </div>
              ` : submissions.map(s => {
                const matchingFinding = findings.find(f => f.id === s.finding_id);
                const isCleared = s.resolution_outcome === 'CONDITION_CLEARED';
                return `
                <div style="border: 1px solid var(--border-light); border-left: 4px solid ${isCleared ? 'var(--color-green-600)' : 'var(--color-amber-500)'}; border-radius: var(--radius-sm); padding: var(--space-4); margin-bottom: var(--space-4); background: white;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2); flex-wrap: wrap; gap: var(--space-2);">
                    <div style="display: flex; align-items: center; gap: var(--space-2);">
                      <span style="font-weight: 700; font-size: 13px; color: var(--color-blue-800);">
                        Cycle #${s.cycle_number} Remediation Delta
                      </span>
                      ${matchingFinding ? `<span class="badge badge-secondary" style="font-family: var(--font-mono); font-size: 11px;">${matchingFinding.rule_code}</span>` : ''}
                    </div>
                    <span class="badge ${s.status === 'SUBMITTED' ? 'badge-info' : 'badge-secondary'}">${s.status}</span>
                  </div>

                  <!-- Remediation Delta Side-by-Side Comparison -->
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); margin-bottom: var(--space-3); font-size: 12px;">
                    <!-- Left: Original Finding -->
                    <div style="background: #FFF1F2; border: 1px solid #FECDD3; border-radius: var(--radius-xs); padding: var(--space-3);">
                      <div style="font-size: 10px; font-weight: 700; color: #9F1239; text-transform: uppercase; margin-bottom: 2px;">Original Discrepancy (v1)</div>
                      <div style="font-weight: 600; color: #881337;">${matchingFinding ? matchingFinding.rule_title : 'Regulatory Finding'}</div>
                      <div style="color: #4C0519; font-size: 11px; margin-top: 2px;">Observed: <strong>${matchingFinding ? matchingFinding.observed_value : 'Deficient'}</strong></div>
                      <div style="color: #4C0519; font-size: 11px;">Expected: <strong>${matchingFinding ? matchingFinding.expected_value : 'Statutory Standard'}</strong></div>
                    </div>

                    <!-- Right: Institutional Remedy -->
                    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: var(--radius-xs); padding: var(--space-3);">
                      <div style="font-size: 10px; font-weight: 700; color: #166534; text-transform: uppercase; margin-bottom: 2px;">Institutional Remedy (v2)</div>
                      <div style="color: #14532D; font-size: 11px; max-height: 80px; overflow-y: auto; line-height: 1.4;">
                        "${s.response_text}"
                      </div>
                      ${s.document_version_id ? `<div style="font-size: 10px; color: #15803D; margin-top: 4px; font-weight: 600;">✓ Replacement Document Uploaded</div>` : ''}
                    </div>
                  </div>

                  <!-- Engine Revalidation Outcome -->
                  ${s.resolution_outcome ? `
                    <div style="display: flex; justify-content: space-between; align-items: center; background: ${isCleared ? '#f0fdf4' : '#fef2f2'}; border: 1px solid ${isCleared ? '#86EFAC' : '#FCA5A5'}; padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); margin-bottom: var(--space-3); font-size: 12px;">
                      <div>
                        <strong>Engine Revalidation Outcome:</strong> 
                        <span style="font-weight: 700; color: ${isCleared ? 'var(--color-green-700)' : 'var(--color-red-700)'};">
                          ${s.resolution_outcome.replace(/_/g, ' ')}
                        </span>
                      </div>
                      ${s.comparison_notes ? `<span style="color: var(--text-muted); font-size: 11px;">${s.comparison_notes}</span>` : ''}
                    </div>
                  ` : ''}

                  <!-- Reviewer Quick Disposition Bar -->
                  <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted); border-top: 1px solid var(--border-light); padding-top: var(--space-2); margin-top: var(--space-2); flex-wrap: wrap; gap: var(--space-2);">
                    <div>
                      Disposition: <strong>${s.reviewer_disposition || 'PENDING_REVIEW'}</strong>
                      • Submitted: ${s.submitted_at ? new Date(s.submitted_at).toLocaleString() : 'N/A'}
                    </div>
                    <div style="display: flex; gap: var(--space-2);">
                      <button type="button" class="btn btn-secondary btn-sm btn-quick-accept" data-finding-id="${s.finding_id || ''}" data-cycle="${s.cycle_number}" style="color: var(--color-green-700); font-size: 11px; padding: 2px 8px;">
                        ✓ Accept Correction
                      </button>
                      <button type="button" class="btn btn-secondary btn-sm btn-quick-query" data-finding-id="${s.finding_id || ''}" data-cycle="${s.cycle_number}" style="color: var(--color-amber-700); font-size: 11px; padding: 2px 8px;">
                        ? Require Evidence
                      </button>
                      <button type="button" class="btn btn-secondary btn-sm btn-quick-concur" data-finding-id="${s.finding_id || ''}" data-cycle="${s.cycle_number}" style="color: var(--color-red-700); font-size: 11px; padding: 2px 8px;">
                        ✕ Concur Deficiency
                      </button>
                    </div>
                  </div>
                </div>
                `;
              }).join('')}
            </div>
          </div>

          <!-- Document Checklist Card -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                ${icons.clipboardList}
                <span>Statutory Ingestion Checklist (${checklist.length} Documents)</span>
              </div>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Doc #</th>
                    <th>Document Name</th>
                    <th>Version</th>
                    <th>Extraction Mode</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${checklist.map((doc, idx) => `
                    <tr>
                      <td class="tabular-nums">${idx + 1}</td>
                      <td style="font-weight: 600;">${doc.title}</td>
                      <td><span class="badge badge-secondary">v${doc.version_number}</span></td>
                      <td style="font-size: 11px;">${doc.is_scanned ? 'PaddleOCR' : 'Digital Text'}</td>
                      <td>${renderBadge(doc.status, doc.status.replace(/_/g, ' '))}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: Reviewer Action Console & Decision Forms -->
        <div>
          <!-- Record Observation Card -->
          <div class="card" style="margin-bottom: var(--space-6);">
            <div class="card-header" style="background: var(--color-slate-50);">
              <div class="card-title">
                ${icons.shieldCheck}
                <span>Record Scrutiny Observation</span>
              </div>
            </div>
            <div class="card-body">
              <form id="form-record-observation">
                <div class="form-group" style="margin-bottom: var(--space-3);">
                  <label class="form-label" for="obs-target-finding">Target Discrepancy</label>
                  <select id="obs-target-finding" class="form-control">
                    <option value="">General Application Observation</option>
                    ${findings.map(f => `
                      <option value="${f.id}">${f.rule_code} — ${f.rule_title.slice(0, 35)}...</option>
                    `).join('')}
                  </select>
                </div>

                <div class="form-group" style="margin-bottom: var(--space-3);">
                  <label class="form-label" for="obs-decision">Committee Action / Disposition <span class="required-star">*</span></label>
                  <select id="obs-decision" class="form-control" required>
                    <option value="CONCUR_DEFICIENCY">Concur with Discrepancy (Issue Deficiency Notice)</option>
                    <option value="ACCEPT_CORRECTION">Accept Institutional Correction (Mark Resolved)</option>
                    <option value="OVERRULE_DEFICIENCY">Overrule Discrepancy (Formal APH Justification)</option>
                    <option value="REQUIRE_ADDITIONAL_EVIDENCE">Require Additional Physical Verification</option>
                    <option value="GENERAL_OBSERVATION">General Scrutiny Note</option>
                  </select>
                </div>

                <div class="form-group" style="margin-bottom: var(--space-3);">
                  <label class="form-label" for="obs-justification">Justification & Legal Observations <span class="required-star">*</span></label>
                  <textarea id="obs-justification" class="form-control" rows="4" placeholder="Enter formal observations citing AICTE Approval Process Handbook (APH 2024-2027) clauses..." required></textarea>
                </div>

                <div class="form-group" style="margin-bottom: var(--space-4);">
                  <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
                    <input type="checkbox" id="obs-internal-note">
                    <span>Internal Scrutiny Committee Note (Hidden from institutional applicant)</span>
                  </label>
                </div>

                <button type="submit" id="btn-submit-obs" class="btn btn-primary" style="width: 100%;">
                  ${icons.shieldCheck}
                  <span>Submit Scrutiny Observation</span>
                </button>
              </form>
            </div>
          </div>

          <!-- Final Pre-Scrutiny Stage Recommendation Box -->
          <div class="card" style="margin-bottom: var(--space-6); border: 2px solid var(--color-blue-200);">
            <div class="card-header" style="background: var(--color-blue-50);">
              <div class="card-title" style="color: var(--color-blue-900);">
                ${icons.scale}
                <span>Pre-Scrutiny Stage Signoff</span>
              </div>
            </div>
            <div class="card-body">
              <p style="font-size: 12px; color: var(--text-muted); margin-bottom: var(--space-3);">
                Record the committee's pre-scrutiny recommendation. Advisory pre-scrutiny recommendations do not grant official AICTE statutory approval.
              </p>

              <form id="form-stage-decision">
                <div class="form-group" style="margin-bottom: var(--space-3);">
                  <label class="form-label" for="stage-decision">Pre-Scrutiny Recommendation <span class="required-star">*</span></label>
                  <select id="stage-decision" class="form-control" required>
                    <option value="PRE_SCRUTINY_RECOMMENDED_CLEAR">Recommend Pre-Scrutiny Clearance</option>
                    <option value="RETURNED_FOR_CORRECTION">Return Application for Institutional Correction</option>
                    <option value="FURTHER_REVIEW_REQUIRED">Escalate for Supervisory / Appellate Committee Hearing</option>
                  </select>
                </div>

                <div class="form-group" style="margin-bottom: var(--space-4);">
                  <label class="form-label" for="stage-remarks">Committee Stage Summary Remarks <span class="required-star">*</span></label>
                  <textarea id="stage-remarks" class="form-control" rows="4" placeholder="Enter comprehensive committee assessment summary..." required></textarea>
                </div>

                <button type="submit" id="btn-submit-stage" class="btn btn-success" style="width: 100%;">
                  ${icons.checkCircle}
                  <span>Record Formal Pre-Scrutiny Signoff</span>
                </button>
              </form>
            </div>
          </div>

          <!-- Chronological Scrutiny History Stream -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                ${icons.history}
                <span>Recorded Scrutiny History (${observations.length})</span>
              </div>
            </div>
            <div class="card-body" style="max-height: 400px; overflow-y: auto; padding: var(--space-3);">
              ${observations.length === 0 ? `
                <div style="padding: var(--space-4); text-align: center; color: var(--text-muted); font-size: 12px;">
                  No observations recorded on this case yet.
                </div>
              ` : observations.map(o => `
                <div style="border-bottom: 1px solid var(--border-light); padding: var(--space-3) 0;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 700; font-size: 12px; color: var(--color-blue-800);">
                      ${o.reviewer_name || 'Reviewer'}
                    </span>
                    <span class="badge ${o.decision === 'ACCEPT_CORRECTION' ? 'badge-compliant' : o.decision === 'CONCUR_DEFICIENCY' ? 'badge-deficiency' : 'badge-info'}" style="font-size: 10px;">
                      ${o.decision.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p style="font-size: 12px; color: var(--text-secondary); margin: 0;">
                    ${o.justification}
                  </p>
                  <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${o.is_internal_note ? '🔒 Internal Note' : 'Applicant Visible'}</span>
                    <span>${new Date(o.created_at).toLocaleString()}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;

    // Bind Export Scrutiny Dossier Button
    document.getElementById('btn-export-scrutiny-dossier')?.addEventListener('click', () => {
      openReviewerDossierModal(app, findings, submissions, observations, checklist);
    });

    // Bind Quick Disposition Accelerators
    document.querySelectorAll('.btn-quick-accept').forEach(btn => {
      btn.addEventListener('click', () => {
        const fId = btn.getAttribute('data-finding-id');
        const cycle = btn.getAttribute('data-cycle');
        const selectF = document.getElementById('obs-target-finding');
        const selectD = document.getElementById('obs-decision');
        const textJ = document.getElementById('obs-justification');
        if (selectF && fId) selectF.value = fId;
        if (selectD) selectD.value = 'ACCEPT_CORRECTION';
        if (textJ) textJ.value = `[Cycle #${cycle} Remediation Verified]: Evaluated institutional corrective response and supporting replacement evidence against AICTE APH norms. Condition verified compliant. Deficiency resolved.`;
        textJ?.focus();
      });
    });

    document.querySelectorAll('.btn-quick-query').forEach(btn => {
      btn.addEventListener('click', () => {
        const fId = btn.getAttribute('data-finding-id');
        const cycle = btn.getAttribute('data-cycle');
        const selectF = document.getElementById('obs-target-finding');
        const selectD = document.getElementById('obs-decision');
        const textJ = document.getElementById('obs-justification');
        if (selectF && fId) selectF.value = fId;
        if (selectD) selectD.value = 'REQUIRE_ADDITIONAL_EVIDENCE';
        if (textJ) textJ.value = `[Cycle #${cycle} Additional Verification Required]: Clarification or physical endorsement from the competent authority required before deficiency can be cleared.`;
        textJ?.focus();
      });
    });

    document.querySelectorAll('.btn-quick-concur').forEach(btn => {
      btn.addEventListener('click', () => {
        const fId = btn.getAttribute('data-finding-id');
        const cycle = btn.getAttribute('data-cycle');
        const selectF = document.getElementById('obs-target-finding');
        const selectD = document.getElementById('obs-decision');
        const textJ = document.getElementById('obs-justification');
        if (selectF && fId) selectF.value = fId;
        if (selectD) selectD.value = 'CONCUR_DEFICIENCY';
        if (textJ) textJ.value = `[Cycle #${cycle} Deficiency Confirmed]: Remediation provided fails to satisfy AICTE Approval Process Handbook (APH 2024–27) statutory requirements. Discrepancy upheld.`;
        textJ?.focus();
      });
    });

    // Bind Self-Assign Button
    document.getElementById('btn-self-assign-case')?.addEventListener('click', async () => {
      try {
        await api.assignReviewer(app.id, currentUser.id, 'Self-assigned from Case Console');
        alert('Case successfully assigned to you.');
        await loadCaseData();
      } catch (err) {
        alert('Assignment failed: ' + err.message);
      }
    });

    // Bind Scrutiny Observation Form
    const obsForm = document.getElementById('form-record-observation');
    obsForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const findingId = document.getElementById('obs-target-finding').value || null;
      const decision = document.getElementById('obs-decision').value;
      const justification = document.getElementById('obs-justification').value.trim();
      const isInternal = document.getElementById('obs-internal-note').checked;

      const submitBtn = document.getElementById('btn-submit-obs');
      try {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Recording observation...';

        await api.recordReviewerObservation(app.id, {
          finding_id: findingId,
          decision: decision,
          justification: justification,
          is_internal_note: isInternal,
        });

        alert('Scrutiny observation successfully recorded in audit log.');
        await loadCaseData();
      } catch (err) {
        alert('Failed to record observation: ' + err.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Scrutiny Observation';
      }
    });

    // Bind Stage Decision Form
    const stageForm = document.getElementById('form-stage-decision');
    stageForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const decision = document.getElementById('stage-decision').value;
      const remarks = document.getElementById('stage-remarks').value.trim();

      const conf = confirm(`Are you sure you want to record the following pre-scrutiny recommendation?\n\nDecision: ${decision}\nRemarks: ${remarks}`);
      if (!conf) return;

      const stageBtn = document.getElementById('btn-submit-stage');
      try {
        stageBtn.disabled = true;
        stageBtn.textContent = 'Submitting stage signoff...';

        await api.completePrescrutinyDecision(app.id, {
          decision: decision,
          remarks: remarks,
        });

        alert(`Pre-scrutiny recommendation successfully recorded.`);
        await loadCaseData();
      } catch (err) {
        alert('Signoff failed: ' + err.message);
        stageBtn.disabled = false;
        stageBtn.textContent = 'Record Formal Pre-Scrutiny Signoff';
      }
    });
  }

  // Initial Case Load
  await loadCaseData();
}

// -------------------------------------------------------------------------
// Official Reviewer Scrutiny Assessment Dossier Generator
// -------------------------------------------------------------------------
function openReviewerDossierModal(app, findings, submissions, observations, checklist) {
  const existing = document.getElementById('reviewer-dossier-modal');
  if (existing) existing.remove();

  const modalHtml = `
    <div id="reviewer-dossier-modal" class="modal-backdrop dossier-print-container" style="position: fixed; inset: 0; background: rgba(15, 23, 42, 0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: var(--space-4); overflow-y: auto;">
      <div class="card dossier-paper" style="max-width: 840px; width: 100%; max-height: 95vh; overflow-y: auto; box-shadow: var(--shadow-lg); background: #FFFFFF; border-radius: var(--radius-md);">
        
        <!-- Dossier Header -->
        <div style="padding: var(--space-6); border-bottom: 2px solid var(--color-blue-800); background: #F8FAFC;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-4);">
            <div style="display: flex; align-items: center; gap: var(--space-3);">
              <div style="width: 48px; height: 48px; border-radius: 8px; background: var(--color-blue-900); color: white; display: flex; align-items: center; justify-content: center;">
                ${icons.scale}
              </div>
              <div>
                <div style="font-size: 11px; font-weight: 700; color: var(--color-blue-900); text-transform: uppercase; letter-spacing: 0.5px;">AICTE Pre-Scrutiny &amp; Deficiency Platform (SIH Prototype)</div>
                <h2 style="margin: 2px 0 0 0; font-size: 18px; color: #0F172A;">Scrutiny Committee Assessment Working Dossier</h2>
                <div style="font-size: 12px; color: var(--text-muted);">
                  Case: <strong>${escapeHtml(app.application_number)}</strong> • Scrutiny Working Date: ${new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                </div>
              </div>
            </div>
            <div class="no-print" style="display: flex; gap: var(--space-2);">
              <button type="button" id="btn-print-reviewer-dossier" class="btn btn-primary btn-sm">
                ${icons.clipboardList}
                <span>Print Dossier</span>
              </button>
              <button type="button" id="btn-close-reviewer-dossier" class="btn btn-ghost btn-sm" aria-label="Close">✕</button>
            </div>
          </div>
        </div>

        <!-- Dossier Body -->
        <div style="padding: var(--space-6);">
          
          <!-- Neutral Prototype Advisory Disclaimer -->
          <div style="background-color: var(--color-amber-50, #FFFBEB); border: 1px solid var(--color-amber-300, #FCD34D); border-left: 4px solid var(--color-amber-600, #D97706); padding: var(--space-3) var(--space-4); border-radius: var(--radius-xs); margin-bottom: var(--space-4); font-size: 11px; color: var(--color-amber-950, #451A03); line-height: 1.5;">
            <strong>SIH Prototype — Not an official AICTE portal.</strong> This generated report is a decision-support aid, not an official AICTE assessment, approval or certificate. Final regulatory authority rests exclusively with the authorized AICTE Scrutiny Committee.
          </div>

          <!-- Formal Committee Sign-off Status -->
          <div style="margin-bottom: var(--space-4); display: flex; align-items: center; justify-content: space-between; background: #F8FAFC; border: 1px solid var(--border-light); padding: var(--space-3); border-radius: var(--radius-xs);">
            <span style="font-size: 12px; font-weight: 600; color: var(--text-secondary);">Formal Sign-off Determination:</span>
            <span class="badge ${app.review_status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}" style="font-size: 11px; font-weight: 700;">
              ${app.review_status === 'COMPLETED' ? 'COMMITTEE REVIEW RECORDED' : 'PENDING FORMAL COMMITTEE REVIEW (No final regulatory determination made)'}
            </span>
          </div>

          <!-- Case Assessment Overview -->
          <div style="background: #F1F5F9; border-radius: var(--radius-sm); padding: var(--space-4); margin-bottom: var(--space-5);">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-3); font-size: 12px;">
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Institution</span>
                <div style="font-weight: 700; color: #0F172A;">${escapeHtml(app.institution_name)}</div>
                <div style="font-size: 11px; color: var(--text-muted);">Permanent ID: ${escapeHtml(app.aicte_permanent_id)}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Assigned Scrutinizer</span>
                <div style="font-weight: 700; color: var(--color-blue-900);">${escapeHtml(app.assigned_reviewer_name || 'Authorised Reviewer')}</div>
                <div style="font-size: 11px; color: var(--text-muted);">Status: ${escapeHtml(app.review_status)}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Location</span>
                <div style="font-weight: 600;">${escapeHtml(app.district)}, ${escapeHtml(app.state)}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Pre-Scrutiny Score</span>
                <div style="font-weight: 800; font-size: 15px; color: ${app.pre_scrutiny_score >= 80 ? 'var(--color-green-700)' : 'var(--color-amber-700)'};">
                  ${app.pre_scrutiny_score}% (Deficiencies: ${app.deficiencies_count})
                </div>
              </div>
            </div>
          </div>

          <!-- Discrepancies Table -->
          <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: var(--space-2); color: var(--color-blue-900);">Evaluated Discrepancies (${findings.length})</h4>
          <table class="data-table" style="width: 100%; margin-bottom: var(--space-5); font-size: 11px;">
            <thead>
              <tr style="background: #F8FAFC;">
                <th>Rule Code</th>
                <th>Discrepancy Title</th>
                <th>Severity</th>
                <th>Expected Statutory Value</th>
                <th>Observed Evidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${findings.map(f => `
                <tr>
                  <td style="font-family: var(--font-mono); font-weight: 700;">${escapeHtml(f.rule_code)}</td>
                  <td style="font-weight: 600;">${escapeHtml(f.rule_title)}</td>
                  <td><span class="badge ${f.severity === 'DEFICIENCY' ? 'badge-danger' : 'badge-warning'}">${f.severity}</span></td>
                  <td style="color: var(--color-green-800);">${escapeHtml(f.expected_value || 'Compliant')}</td>
                  <td style="color: var(--color-red-700);">${escapeHtml(f.observed_value || 'Deficient')}</td>
                  <td><span class="badge ${f.status === 'RESOLVED' ? 'badge-success' : 'badge-secondary'}">${escapeHtml(f.status)}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <!-- Recorded Committee Observations -->
          <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: var(--space-2); color: var(--color-blue-900);">Committee Scrutiny Observations & Dispositions (${observations.length})</h4>
          ${observations.length === 0 ? `
            <div style="padding: var(--space-3); background: #F8FAFC; border: 1px solid var(--border-light); font-size: 12px; color: var(--text-muted); margin-bottom: var(--space-5);">
              No scrutiny observations formally submitted yet.
            </div>
          ` : `
            <div style="display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-5);">
              ${observations.map(o => `
                <div style="border: 1px solid var(--border-light); border-left: 3px solid var(--color-blue-700); padding: var(--space-3); border-radius: var(--radius-xs); font-size: 11px; background: #FAFAFA;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="font-weight: 700; color: var(--color-blue-900);">${escapeHtml(o.reviewer_name || 'Reviewer')} — Disposition: ${escapeHtml(o.decision.replace(/_/g, ' '))}</span>
                    <span style="color: var(--text-muted); font-size: 10px;">${new Date(o.created_at).toLocaleString()}</span>
                  </div>
                  <div style="color: var(--text-secondary); line-height: 1.4;">${escapeHtml(o.justification)}</div>
                </div>
              `).join('')}
            </div>
          `}

          <!-- Statutory Boundary Statement -->
          <div style="border-top: 1px solid var(--border-light); padding-top: var(--space-4); font-size: 10px; color: var(--text-muted); line-height: 1.4;">
            <strong>Statutory Scrutiny Declaration:</strong> This Scrutiny Assessment Dossier is prepared under the provisions of the AICTE Approval Process Handbook (APH 2024–27). Algorithmic evaluations generated by the Intelligent Document Processing and regulatory engines serve as advisory decision-support. All regulatory findings, queries, returns, and recommendations are exercised under the statutory discretion and human authority of the authorised Scrutiny Committee.
          </div>

        </div>

        <!-- Footer -->
        <div class="card-footer no-print" style="display: flex; justify-content: flex-end; gap: var(--space-3); padding: var(--space-3) var(--space-6); background: #F8FAFC; border-top: 1px solid var(--border-light);">
          <button type="button" id="btn-reviewer-dossier-dismiss" class="btn btn-secondary btn-sm">Close</button>
          <button type="button" id="btn-reviewer-dossier-print" class="btn btn-primary btn-sm">
            ${icons.clipboardList}
            <span>Print Dossier</span>
          </button>
        </div>

      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const modalEl = document.getElementById('reviewer-dossier-modal');
  const closeDossier = () => modalEl?.remove();

  document.getElementById('btn-close-reviewer-dossier')?.addEventListener('click', closeDossier);
  document.getElementById('btn-reviewer-dossier-dismiss')?.addEventListener('click', closeDossier);
  document.getElementById('btn-print-reviewer-dossier')?.addEventListener('click', () => window.print());
  document.getElementById('btn-reviewer-dossier-print')?.addEventListener('click', () => window.print());
}
