// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Reusable Shared UI Component Renderers (components.js)
import { icons } from './icons.js';

export function renderHeader(currentUser, activeRole, isAuthenticated = false) {
  const userName = currentUser?.name || currentUser?.full_name || currentUser?.email || 'Guest User';
  const userInitial = userName.charAt(0).toUpperCase();
  const userTitle = currentUser?.title || (activeRole === 'INSTITUTION' ? 'Institution Applicant' : activeRole === 'REVIEWER' ? 'Authorised Reviewer' : 'Administrator');
  const institutionText = currentUser?.institution?.name || currentUser?.institution || '';

  const authActionsHtml = isAuthenticated
    ? `
        <!-- Authenticated Profile Badge -->
        <div class="user-profile-badge">
          <div class="user-avatar" aria-hidden="true">${userInitial}</div>
          <div>
            <div style="font-weight: 600; color: #FFFFFF;">${escapeHtml(userName)}</div>
            <div style="font-size: 11px; color: #94A3B8;">${escapeHtml(userTitle)}</div>
            ${institutionText && activeRole === 'INSTITUTION' ? `<div style="font-size: 10px; color: #CBD5E1; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(institutionText)}</div>` : ''}
          </div>
        </div>

        <!-- Working Sign Out Action -->
        <button type="button" id="btn-header-logout" class="btn-header-logout" aria-label="Sign out of your account" title="Sign out of AICTE Platform">
          <span>Sign Out</span>
        </button>
      `
    : `
        <a href="#/login" class="btn btn-primary" style="padding: 4px 14px; font-size: 12px; font-weight: 600;">
          Sign In
        </a>
      `;

  return `
    <header class="app-header" role="banner">
      <a href="${isAuthenticated ? '#/dashboard' : '#/login'}" class="header-brand" aria-label="AICTE Pre-Scrutiny Platform Home">
        <div class="brand-emblem" aria-hidden="true">
          ${icons.scale}
        </div>
        <div class="brand-text">
          <div class="brand-title">
            AICTE Pre-Scrutiny & Deficiency Platform
          </div>
          <div class="brand-subtitle">
            Ministry of Education, Govt. of India | SIH Prototype
          </div>
        </div>
      </a>

      <div class="header-actions">
        ${isAuthenticated ? `
          <!-- Verified Authenticated Role Badge -->
          <div class="role-preview-container" title="Current authenticated role">
            <span class="role-preview-label">Role:</span>
            <span class="badge ${activeRole === 'ADMIN' ? 'badge-danger' : activeRole === 'REVIEWER' ? 'badge-info' : 'badge-success'}" style="font-size: 11px; padding: 3px 8px;">
              ${escapeHtml(activeRole === 'INSTITUTION' ? 'Institution Applicant' : activeRole === 'REVIEWER' ? 'Authorised Reviewer' : 'System Administrator')}
            </span>
            <button type="button" id="btn-switch-account" class="btn btn-ghost btn-sm" style="color: #94A3B8; font-size: 11px; padding: 2px 6px; text-decoration: underline;" title="Sign out to switch to another role or account">
              Switch
            </button>
          </div>
        ` : `
          <!-- Role Preview Selector for Testing & Demo -->
          <div class="role-preview-container" title="Switch role preview for evaluation">
            <label for="role-preview-select" class="role-preview-label">Role:</label>
            <select id="role-preview-select" class="role-select" aria-label="Select User Role">
              <option value="INSTITUTION" ${activeRole === 'INSTITUTION' ? 'selected' : ''}>Institution Applicant</option>
              <option value="REVIEWER" ${activeRole === 'REVIEWER' ? 'selected' : ''}>Authorised Reviewer</option>
              <option value="ADMIN" ${activeRole === 'ADMIN' ? 'selected' : ''}>System Administrator</option>
            </select>
          </div>
        `}

        ${authActionsHtml}
      </div>
    </header>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function renderSidebar(activeRole, currentRoute) {
  let navItems = [];

  if (activeRole === 'INSTITUTION') {
    navItems = [
      { section: 'Institution Workspace' },
      { route: '#/dashboard', label: 'Dashboard', icon: icons.dashboard },
      { route: '#/applications', label: 'My Applications', icon: icons.clipboardList },
      { route: '#/applications/new', label: 'Start New EoA', icon: icons.plus },
      { route: '#/applications/app_9812', label: 'Document Checklist', icon: icons.document, badge: '8 Docs' },
      { route: '#/applications/app_9812/deficiencies', label: 'Deficiency Bridge', icon: icons.alertTriangle, badge: '2 Alerts', badgeType: 'alert' },
      { section: 'Regulatory & Guidance' },
      { route: '#/admin/rules', label: 'AICTE APH Rules', icon: icons.scale },
      { route: '#/admin/audit', label: 'Activity Audit Log', icon: icons.history }
    ];
  } else if (activeRole === 'REVIEWER') {
    navItems = [
      { section: 'Scrutiny Committee' },
      { route: '#/reviewer/queue', label: 'Scrutiny Queue', icon: icons.clipboardList, badge: '2 Pending', badgeType: 'info' },
      { route: '#/reviewer/scrutiny/app_9812', label: 'Scrutiny Console', icon: icons.shieldCheck },
      { route: '#/applications/app_9812/evidence/find_0042', label: 'Evidence Inspector', icon: icons.eye },
      { section: 'Governance' },
      { route: '#/admin/rules', label: 'AICTE APH Catalog', icon: icons.scale },
      { route: '#/admin/audit', label: 'Scrutiny Audit Log', icon: icons.history }
    ];
  } else if (activeRole === 'ADMIN') {
    navItems = [
      { section: 'System Administration' },
      { route: '#/dashboard', label: 'System Overview', icon: icons.dashboard },
      { route: '#/admin/users', label: 'User Governance', icon: icons.users },
      { route: '#/admin/rules', label: 'Rule Catalog Manager', icon: icons.scale },
      { route: '#/admin/audit', label: 'Immutable Audit Trail', icon: icons.history },
      { route: '#/applications', label: 'All Institutions', icon: icons.document }
    ];
  }

  const navHtml = navItems.map(item => {
    if (item.section) {
      return `<li class="nav-section-title">${item.section}</li>`;
    }
    const isActive = currentRoute === item.route || currentRoute.startsWith(item.route + '/');
    const badgeHtml = item.badge 
      ? `<span class="nav-badge ${item.badgeType === 'alert' ? 'nav-badge-alert' : 'nav-badge-info'}">${item.badge}</span>` 
      : '';
    return `
      <li class="nav-item">
        <a href="${item.route}" class="nav-link ${isActive ? 'active' : ''}">
          ${item.icon}
          <span>${item.label}</span>
          ${badgeHtml}
        </a>
      </li>
    `;
  }).join('');

  return `
    <aside class="app-sidebar" role="navigation" aria-label="Main Navigation">
      <div class="sidebar-nav">
        <ul class="nav-list">
          ${navHtml}
        </ul>
      </div>
      <div class="sidebar-footer">
        <div class="session-badge">
          ${icons.shieldCheck}
          <span>AICTE Session 2026-27</span>
        </div>
        <div style="margin-top: 4px; font-size: 11px;">APH Norms Version 1.0.0</div>
      </div>
    </aside>
  `;
}

export function renderBreadcrumbs(items) {
  const crumbs = items.map((item, idx) => {
    const isLast = idx === items.length - 1;
    if (isLast) {
      return `<li class="breadcrumb-item active" aria-current="page">${item.label}</li>`;
    }
    return `
      <li class="breadcrumb-item">
        <a href="${item.href}">${item.label}</a>
        <span class="breadcrumb-separator" aria-hidden="true">/</span>
      </li>
    `;
  }).join('');

  return `
    <nav aria-label="Breadcrumb" class="page-breadcrumb-bar">
      <ol class="breadcrumb">
        ${crumbs}
      </ol>
      <div style="font-size: 11px; color: #64748B;">
        Prototype Mode: Local Simulation
      </div>
    </nav>
  `;
}

export function renderBadge(type, text) {
  let cssClass = 'badge-pending';
  const upper = String(type || '').toUpperCase();
  if (upper === 'DEFICIENCY' || upper === 'CRITICAL' || upper === 'DEFICIENCY_DETECTED') cssClass = 'badge-deficiency';
  else if (upper === 'WARNING' || upper === 'WARNING_DETECTED') cssClass = 'badge-warning';
  else if (upper === 'COMPLIANT' || upper === 'PROCESSED' || upper === 'RESOLVED' || upper === 'REVALIDATED' || upper === 'UPLOADED') cssClass = 'badge-compliant';
  else if (upper === 'PROCESSING') cssClass = 'badge-processing';
  else if (upper === 'INFO' || upper === 'SUBMITTED') cssClass = 'badge-info';
  else if (upper === 'DRAFT' || upper === 'PENDING') cssClass = 'badge-draft';

  return `<span class="badge ${cssClass}">${text || type}</span>`;
}

export function renderStatCard(title, value, description, iconName = 'clipboardList') {
  return `
    <div class="stat-card">
      <div class="stat-header">
        <span>${title}</span>
        ${icons[iconName] || icons.clipboardList}
      </div>
      <div class="stat-value">${value}</div>
      <div class="stat-desc">${description}</div>
    </div>
  `;
}

export function renderAlert(type, title, message) {
  const iconMap = {
    warning: icons.alertTriangle,
    danger: icons.alertCircle,
    success: icons.checkCircle,
    info: icons.shieldCheck
  };

  return `
    <div class="alert alert-${type}" role="alert">
      <div class="alert-icon" aria-hidden="true">${iconMap[type] || icons.alertCircle}</div>
      <div class="alert-content">
        ${title ? `<div class="alert-title">${title}</div>` : ''}
        <div>${message}</div>
      </div>
    </div>
  `;
}

export function renderEmptyState(iconName, title, message, actionBtnHtml = '') {
  return `
    <div class="empty-state">
      <div class="empty-state-icon" aria-hidden="true">${icons[iconName] || icons.document}</div>
      <div class="empty-state-title">${title}</div>
      <div class="empty-state-text">${message}</div>
      ${actionBtnHtml}
    </div>
  `;
}

// -------------------------------------------------------------------------
// Scrutiny Readiness Index & Health Gauge
// -------------------------------------------------------------------------
export function renderReadinessGauge(deficienciesCount = 0, warningsCount = 0, missingCount = 0, uploadedSlots = 8, totalSlots = 8, validationRun = null, unresolvedCount = 0) {
  let score = 0;
  let colorClass = 'gauge-amber';
  let statusText = 'Pre-Scrutiny Pending';
  let badgeClass = 'badge-secondary';
  let statusDescription = 'Upload statutory documents and trigger pre-scrutiny checks to evaluate compliance.';

  if (!validationRun && uploadedSlots === 0) {
    score = 0;
    statusText = 'Pre-Scrutiny Pending';
    badgeClass = 'badge-secondary';
    colorClass = 'gauge-amber';
    statusDescription = 'No documents uploaded or pre-scrutiny checks evaluated yet. Upload mandatory documents to begin preparation.';
  } else if (!validationRun && uploadedSlots > 0) {
    score = Math.round((uploadedSlots / totalSlots) * 50);
    statusText = 'Pre-Scrutiny Not Run';
    badgeClass = 'badge-warning';
    colorClass = 'gauge-amber';
    statusDescription = `${uploadedSlots}/${totalSlots} document(s) uploaded, but pre-scrutiny evaluation has not been executed. Run Pre-Scrutiny Checks to evaluate regulatory compliance.`;
  } else {
    // Validation run exists
    if (deficienciesCount > 0) {
      score = Math.max(0, Math.min(100, Math.round(100 - (35 * deficienciesCount) - (12 * warningsCount) - (10 * missingCount) - (10 * unresolvedCount))));
      colorClass = 'gauge-red';
      statusText = 'High Scrutiny Deficiency Risk';
      badgeClass = 'badge-deficiency';
      statusDescription = `${deficienciesCount} blocking statutory deficiency detected. AICTE Scrutiny Committee will issue a query or return for correction.`;
    } else if (warningsCount > 0 || missingCount > 0 || unresolvedCount > 0) {
      score = Math.max(0, Math.min(100, Math.round(100 - (12 * warningsCount) - (10 * missingCount) - (10 * unresolvedCount))));
      colorClass = 'gauge-amber';
      statusText = 'Advisory Review Recommended';
      badgeClass = 'badge-warning';
      statusDescription = `${warningsCount} advisory warning, ${missingCount} missing document(s), or ${unresolvedCount} unresolved item(s) require review before formal submission.`;
    } else {
      score = 100;
      colorClass = 'gauge-green';
      statusText = 'Scrutiny Ready';
      badgeClass = 'badge-compliant';
      statusDescription = 'Application demonstrates strong alignment with AICTE APH 2024–27 norms with low query risk.';
    }
  }

  return `
    <div class="readiness-gauge-card card" style="border: 1px solid var(--border-light); margin-bottom: var(--space-6); background: linear-gradient(to right, #FFFFFF, #F8FAFC);">
      <div class="card-body" style="padding: var(--space-5) var(--space-6);">
        <div style="font-size: 10px; color: var(--color-blue-800); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: var(--space-3);">
          Internal Pre-Scrutiny Readiness Estimate • Not an official AICTE score, certification or prediction of approval
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-4);">
          <div style="display: flex; align-items: center; gap: var(--space-5);">
            <div class="readiness-score-circle ${colorClass}" style="width: 72px; height: 72px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 800; border: 4px solid currentColor; flex-shrink: 0;">
              <span style="font-size: 22px; line-height: 1;">${score}%</span>
              <span style="font-size: 9px; text-transform: uppercase; font-weight: 600; opacity: 0.85;">Readiness</span>
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;">
                <h3 style="margin: 0; font-size: var(--text-base); font-weight: 700;">Pre-Submission Scrutiny Readiness Index</h3>
                <span class="badge ${badgeClass}" style="font-size: 11px;">${statusText}</span>
              </div>
              <p style="margin: 4px 0 0 0; font-size: var(--text-xs); color: var(--text-muted); max-width: 580px;">
                ${statusDescription}
              </p>
            </div>
          </div>
          <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
            <div class="readiness-chip" style="background: ${deficienciesCount > 0 ? '#FEF2F2' : '#F1F5F9'}; border: 1px solid ${deficienciesCount > 0 ? '#FCA5A5' : '#E2E8F0'}; padding: 6px 12px; border-radius: var(--radius-sm); text-align: center;">
              <div style="font-size: 14px; font-weight: 700; color: ${deficienciesCount > 0 ? 'var(--color-red-700)' : 'var(--text-primary)'};">${deficienciesCount}</div>
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Deficiencies</div>
            </div>
            <div class="readiness-chip" style="background: ${warningsCount > 0 ? '#FFFBEB' : '#F1F5F9'}; border: 1px solid ${warningsCount > 0 ? '#FCD34D' : '#E2E8F0'}; padding: 6px 12px; border-radius: var(--radius-sm); text-align: center;">
              <div style="font-size: 14px; font-weight: 700; color: ${warningsCount > 0 ? 'var(--color-amber-700)' : 'var(--text-primary)'};">${warningsCount}</div>
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Warnings</div>
            </div>
            <div class="readiness-chip" style="background: ${unresolvedCount > 0 ? '#FFF7ED' : '#F1F5F9'}; border: 1px solid ${unresolvedCount > 0 ? '#FDBA74' : '#E2E8F0'}; padding: 6px 12px; border-radius: var(--radius-sm); text-align: center;">
              <div style="font-size: 14px; font-weight: 700; color: ${unresolvedCount > 0 ? 'var(--color-amber-700)' : 'var(--text-primary)'};">${unresolvedCount}</div>
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Unresolved</div>
            </div>
            <div class="readiness-chip" style="background: #F0FDF4; border: 1px solid #86EFAC; padding: 6px 12px; border-radius: var(--radius-sm); text-align: center;">
              <div style="font-size: 14px; font-weight: 700; color: var(--color-green-700);">${uploadedSlots}/${totalSlots}</div>
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Docs Uploaded</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// -------------------------------------------------------------------------
// Statutory Clause Grounding Repository & Modal Drawer
// -------------------------------------------------------------------------
export const STATUTORY_CLAUSES = {
  'RULE-EOA-STRUCT-004': {
    title: 'Structural Stability Certificate Requirement',
    source: 'AICTE Approval Process Handbook (APH 2024–27), Chapter II, Clause 2.14.6',
    authority: 'All India Council for Technical Education (AICTE)',
    excerpt: 'The institution shall submit a Structural Stability Certificate from an empanelled structural engineer after the expiry of thirty (30) years from the date of issue of the Completion Certificate. The certificate is valid for five (5) years. In the event of any major structural modification, stability assessment and building plan revalidation are mandatory.',
    notes: 'Calendar arithmetic applies. At the exact 30-year anniversary, the period has not expired. Occupancy Certificates cannot be substituted for Completion Certificates without municipal completion date verification.',
    isVerbatim: true
  },
  'RULE-EOA-FSR-005': {
    title: 'Faculty-Student Ratio (FSR) & Cadre Norms',
    source: 'AICTE Approval Process Handbook (APH 2024–27), Annexure-5, Section 5.1–5.3 & Tables 5.1–5.3',
    authority: 'AICTE Statutory Regulations / PCI / CoA',
    excerpt: 'Institutions shall maintain the minimum Faculty to Student Ratio according to programme and level: Under-Graduate Engineering & Technology: 1:20 (Section 5.2); Diploma Engineering: 1:25 (Section 5.1, Table 5.1); Post-Graduate Engineering (M.Tech): 1:15 (Section 5.3, Table 5.3); Management (MBA/PGDM): 1:20 / 1:25 (Section 5.2 & Table 5.2); Computer Applications (MCA): 1:20 / 1:25 (Section 5.2 & Table 5.2); Pharmacy: 1:15 (PCI Regulations); Architecture: 1:10 (CoA Minimum Standards).',
    notes: 'Denominator is computed against Total Approved Sanctioned Intake across all years (S / Ratio). Fractions are rounded up. Applicability is strictly determined by supported programme category.',
    isVerbatim: true
  },
  'RULE-EOA-FIRE-003': {
    title: 'Fire Safety Certificate (NOC) Validity',
    source: 'AICTE APH 2024–27 Chapter II Clause 2.3.4 & National Building Code (NBC Part IV)',
    authority: 'State Directorate of Fire & Rescue Services / Municipal Fire Authority',
    excerpt: 'Institutions must possess a valid Fire Safety No Objection Certificate (NOC) issued by the competent government fire authority, remaining unexpired and valid through the commencement date of the upcoming academic session.',
    notes: 'Expired or missing NOC is a non-waivable statutory deficiency under Chapter II.',
    isVerbatim: true
  },
  'RULE-EOA-BCC-002': {
    title: 'Building Completion Evidence Check',
    source: 'AICTE APH 2024–27 Chapter II Clause 2.14.3',
    authority: 'Competent Town Planning / Municipal Authority',
    excerpt: 'The institution must submit an Occupancy Certificate, Completion Certificate, Building License, or Form D from the competent local authority. Provisional Occupancy Certificates are restricted to a strict maximum limit of two (2) consecutive academic years.',
    notes: 'Provisional occupancy beyond 2 consecutive years constitutes a deficiency requiring final occupancy submission.',
    isVerbatim: true
  },
  'RULE-EOA-LAND-001': {
    title: 'Land Area & Sanctioned Floor Area Ratio (FAR)',
    source: 'AICTE APH 2024–27 Appendix 4 & Chapter II',
    authority: 'Local Town Planning Authority & AICTE',
    excerpt: 'Land requirement shall be governed by the permissible FSI/FAR as notified by the local competent town planning authority. Vertical campus expansion is permissible subject to local authority FAR sanction.',
    notes: 'Institutions lacking explicit FAR declarations require municipal endorsement confirmation. Local FAR values are governed by municipal bye-laws.',
    isVerbatim: true
  },
  'RULE-EOA-CROSS-006': {
    title: 'Survey Number Cross-Document Consistency',
    source: 'AICTE APH 2024–27 Chapter II Clause 2.14.1',
    authority: 'Revenue Department & AICTE Land Verification',
    excerpt: 'Survey and Khasra numbers listed in the registered Land Title Deed must identically match the Non-Agricultural (NA) Land Use Conversion Certificate.',
    notes: 'Mismatched survey numbers indicate unverified parcels or split titles requiring revenue compounding.',
    isVerbatim: true
  },
  'RULE-EOA-CROSS-007': {
    title: 'Sanctioned vs Completed Built-up Area Reconciliation',
    source: 'AICTE APH 2024–27 Chapter II Clause 2.14.4',
    authority: 'Municipal Planning Authority',
    excerpt: 'Total completed instructional and administrative built-up area certified in the Completion Certificate must not exceed the sanctioned built-up area approved in the official Building Plan without authorized compounding.',
    notes: 'Excess completed area constitutes unauthorized development unless sanctioned by compounding endorsement.',
    isVerbatim: true
  }
};

export function renderStatutoryGroundingModal(ruleCode) {
  const clause = STATUTORY_CLAUSES[ruleCode] || {
    title: 'AICTE Regulatory Norm',
    source: 'AICTE Approval Process Handbook (APH 2024–27)',
    authority: 'All India Council for Technical Education',
    excerpt: 'Statutory compliance norm verified under official AICTE EoA approval regulations.',
    notes: 'Applicability Limitation: Specific clause text subject to authoritative gazette publication for the effective academic year. Evaluation is advisory.',
    isVerbatim: false
  };

  const isVerbatim = clause.isVerbatim !== false;

  return `
    <div id="statutory-grounding-modal" class="modal-backdrop" style="position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: var(--space-4);">
      <div class="card" style="max-width: 620px; width: 100%; max-height: 90vh; overflow-y: auto; box-shadow: var(--shadow-lg);">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; background: var(--color-slate-100); border-bottom: 2px solid var(--color-blue-600);">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            ${icons.scale}
            <span style="font-weight: 700; font-size: var(--text-sm); color: var(--color-blue-900);">AICTE Regulatory Grounding (SIH Prototype)</span>
          </div>
          <button type="button" id="btn-close-grounding-modal" class="btn btn-ghost btn-sm" aria-label="Close modal">✕</button>
        </div>
        <div class="card-body" style="padding: var(--space-5);">
          <div style="margin-bottom: var(--space-3);">
            <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--color-blue-700);">${ruleCode}</span>
            <h3 style="margin: 2px 0 6px 0; font-size: var(--text-base);">${clause.title}</h3>
          </div>
          <div style="background: var(--color-blue-50); border-left: 3px solid var(--color-blue-600); padding: var(--space-3); border-radius: var(--radius-xs); margin-bottom: var(--space-4);">
            <div style="font-size: 11px; font-weight: 700; color: var(--color-blue-900); text-transform: uppercase;">Official Source Reference</div>
            <div style="font-size: var(--text-xs); color: var(--color-blue-800); font-weight: 600; margin-top: 2px;">${clause.source}</div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Enforcing Authority: ${clause.authority}</div>
          </div>
          <div style="margin-bottom: var(--space-4);">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">
              ${isVerbatim ? 'Verbatim Statutory Excerpt (APH 2024–27)' : 'Plain-Language Regulatory Summary'}
            </div>
            <p style="font-size: var(--text-sm); line-height: 1.5; color: var(--text-primary); ${isVerbatim ? 'font-style: italic;' : ''} background: #FAF5FF; padding: var(--space-3); border-radius: var(--radius-sm); border: 1px solid #E9D5FF;">
              ${isVerbatim ? `"${clause.excerpt}"` : clause.excerpt}
            </p>
            ${!isVerbatim ? `<div style="font-size: 11px; color: var(--color-amber-700); margin-top: 4px;"><em>Notice: Summary represents plain-language decision-support guidance. Refer to official AICTE gazette notification for legal enforcement.</em></div>` : ''}
          </div>
          <div style="background: #F8FAFC; padding: var(--space-3); border-radius: var(--radius-sm); border: 1px solid var(--border-light); font-size: var(--text-xs); color: var(--text-secondary);">
            <strong>Regulatory Engine Notes & Applicability Limits:</strong> ${clause.notes}
          </div>
        </div>
        <div class="card-footer" style="display: flex; justify-content: flex-end; padding: var(--space-3) var(--space-5); background: var(--color-slate-50);">
          <button type="button" id="btn-dismiss-grounding-modal" class="btn btn-primary btn-sm">Understood & Close</button>
        </div>
      </div>
    </div>
  `;
}
