// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: New Application Draft (application-new.js)
import { icons } from '../icons.js';
import { renderBreadcrumbs, renderAlert } from '../components.js';
import { api } from '../api.js';

export function renderApplicationNew(state) {
  const user = state.getCurrentUser() || {};
  const institutionName = user.institution?.name || user.institution || 'Authorised Institution';

  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Applications', href: '#/applications' },
    { label: 'New EoA Draft' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="margin-bottom: var(--space-6);">
        <h1>Initiate Extension of Approval (EoA) Draft</h1>
        <p style="color: var(--text-muted); margin-top: 4px;">
          Create a new pre-scrutiny package for Academic Session 2026-2027 under AICTE Approval Process Handbook guidelines.
        </p>
      </div>

      <div id="new-app-error-container" style="display: none; margin-bottom: var(--space-4);" role="alert" aria-live="polite"></div>

      ${renderAlert('info', 'Prototype Mode: Document Checklist Initialization', 
        'Creating this application will initialize the 8 mandatory AICTE statutory document slots (Land Title, Land Use, Building Plan, Occupancy Certificate, Fire NOC, Stability Certificate, Previous Approval, Faculty Roster) for pre-scrutiny upload.'
      )}

      <div class="card" style="max-width: 800px;">
        <div class="card-header">
          <div class="card-title">
            ${icons.clipboardList}
            <span>Institutional Baseline Information</span>
          </div>
          <span class="badge badge-info">AICTE APH 2026-27</span>
        </div>
        <div class="card-body">
          <form id="new-application-form" novalidate>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
              <div class="form-group">
                <label class="form-label" for="inst-name">Institution Name</label>
                <input type="text" id="inst-name" class="form-control" value="${escapeHtml(institutionName)}" readonly>
                <div class="form-help">Locked to authenticated institutional profile</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="academic-year">Academic Session <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <select id="academic-year" class="form-control" required>
                  <option value="2026-2027" selected>2026-2027 (Upcoming Session)</option>
                  <option value="2025-2026">2025-2026</option>
                </select>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
              <div class="form-group">
                <label class="form-label" for="program-category">Programme Category <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <select id="program-category" class="form-control" required>
                  <option value="ENGINEERING_TECHNOLOGY" selected>Engineering & Technology (UG/PG)</option>
                  <option value="MANAGEMENT">Management (MBA/PGDM)</option>
                  <option value="POLYTECHNIC">Polytechnic / Diploma</option>
                  <option value="PHARMACY">Pharmacy</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label" for="applied-intake">Total Applied Sanctioned Intake <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <input type="number" id="applied-intake" class="form-control" value="720" min="30" step="30" required>
                <div class="form-help">Total seats across all approved academic branches</div>
              </div>
            </div>

            <h3 style="font-size: var(--text-base); margin: var(--space-6) 0 var(--space-3); padding-top: var(--space-4); border-top: 1px solid var(--border-light);">
              Declared Physical & Academic Parameters
            </h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--space-4);">
              <div class="form-group">
                <label class="form-label" for="declared-land">Declared Land (Acres) <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <input type="number" id="declared-land" class="form-control" value="5.2" step="0.1" min="0.5" required>
                <div class="form-help">Contiguous land holding</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="declared-faculty">Total Full-Time Faculty <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <input type="number" id="declared-faculty" class="form-control" value="35" min="1" required>
                <div class="form-help">Regular faculty in cadre roster</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="declared-carpet">Built-up Carpet Area (Sq.m) <span style="color: var(--color-red-600);" aria-hidden="true">*</span></label>
                <input type="number" id="declared-carpet" class="form-control" value="8420" min="500" required>
                <div class="form-help">Instructional + administrative area</div>
              </div>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-6); padding-top: var(--space-4); border-top: 1px solid var(--border-light);">
              <a href="#/applications" class="btn btn-secondary">Cancel</a>
              <button type="submit" id="btn-create-application-submit" class="btn btn-primary">
                <span id="create-app-spinner" class="spinner" style="display: none;" aria-hidden="true"></span>
                <span id="create-app-icon">${icons.plus}</span>
                <span id="create-app-btn-text">Create Application & Open Checklist</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
}

export function initApplicationNewView(state, router) {
  const form = document.getElementById('new-application-form');
  if (!form) return;

  const errorContainer = document.getElementById('new-app-error-container');
  const submitBtn = document.getElementById('btn-create-application-submit');
  const spinner = document.getElementById('create-app-spinner');
  const icon = document.getElementById('create-app-icon');
  const btnText = document.getElementById('create-app-btn-text');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const academicYear = document.getElementById('academic-year')?.value;
    const programCategory = document.getElementById('program-category')?.value;
    const appliedIntake = parseInt(document.getElementById('applied-intake')?.value, 10);
    const declaredLand = parseFloat(document.getElementById('declared-land')?.value);
    const declaredFaculty = parseInt(document.getElementById('declared-faculty')?.value, 10);
    const declaredCarpet = parseFloat(document.getElementById('declared-carpet')?.value);

    // Validation
    if (!academicYear) {
      showError('Please select a valid academic session.');
      return;
    }

    if (isNaN(appliedIntake) || appliedIntake <= 0) {
      showError('Please enter a valid sanctioned intake (greater than 0).');
      return;
    }

    setLoading(true);
    if (errorContainer) errorContainer.style.display = 'none';

    try {
      const payload = {
        application_type: 'EOA',
        academic_year: academicYear,
        total_intake_applied: appliedIntake,
        declared_land_acres: !isNaN(declaredLand) ? declaredLand : undefined,
        declared_faculty_count: !isNaN(declaredFaculty) ? declaredFaculty : undefined,
        declared_builtup_sqm: !isNaN(declaredCarpet) ? declaredCarpet : undefined,
        program_category: programCategory
      };

      const result = await api.createApplication(payload);
      setLoading(false);

      if (result && result.id) {
        router.navigate(`/applications/${result.id}`);
      } else {
        router.navigate('/applications');
      }
    } catch (err) {
      setLoading(false);
      console.error('Failed to create application:', err);
      showError(err.message || 'Failed to create application. Please verify details and try again.');
    }
  });

  function showError(msg) {
    if (!errorContainer) return;
    errorContainer.innerHTML = renderAlert('danger', 'Application Creation Failed', msg);
    errorContainer.style.display = 'block';
    window.scrollTo(0, 0);
  }

  function setLoading(isLoading) {
    if (submitBtn) submitBtn.disabled = isLoading;
    if (spinner) spinner.style.display = isLoading ? 'inline-block' : 'none';
    if (icon) icon.style.display = isLoading ? 'none' : 'inline-block';
    if (btnText) btnText.textContent = isLoading ? 'Creating & Initializing Checklist...' : 'Create Application & Open Checklist';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
