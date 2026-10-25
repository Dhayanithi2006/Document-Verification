// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Reviewer Scrutiny Queue (frontend/js/views/reviewer-queue.js)

import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert } from '../components.js';
import { api } from '../api.js';

let currentQueueState = {
  filter: 'all',
  search: '',
  page: 1,
  limit: 20,
};

export function renderReviewerQueue(state) {
  const currentUser = state.getCurrentUser() || { name: 'Authorised Reviewer' };
  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Scrutiny Committee' },
    { label: 'Review Queue' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <h1>AICTE Scrutiny Committee Queue</h1>
          <p style="color: var(--text-muted); margin-top: 4px;">
            Authorised Scrutiny Workspace: Inspect evidence-backed pre-scrutiny findings and record official observations.
          </p>
        </div>
        <div style="display: flex; align-items: center; gap: var(--space-3);">
          <span class="badge badge-info" style="padding: 6px 14px; font-size: 12px; font-weight: 600;">
            ${icons.shieldCheck}
            <span>Reviewer: ${currentUser.name || currentUser.full_name || 'Prof. K. S. Krishnan'}</span>
          </span>
          <button id="btn-refresh-queue" class="btn btn-secondary btn-sm" title="Refresh Queue">
            ${icons.refresh}
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <!-- Decision-Support Scrutiny Notice Banner -->
      ${renderAlert('info', 'Decision-Support Scrutiny Mode — SIH Prototype',
        'Pre-scrutiny flags discrepancies automatically using versioned AICTE Approval Process Handbook (APH 2024-2027) rules. As an authorised committee member, you inspect source document coordinates, review applicant corrective submissions, and record advisory recommendations. This decision-support system does not grant official AICTE approval.'
      )}

      <!-- Queue Metrics Strip -->
      <div id="reviewer-metrics-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--space-3); margin-bottom: var(--space-6);">
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Total Cases</div>
          <div id="metric-total-apps" style="font-size: 24px; font-weight: 700; color: var(--color-blue-800); margin-top: 4px;">--</div>
        </div>
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Assigned To Me</div>
          <div id="metric-assigned-me" style="font-size: 24px; font-weight: 700; color: var(--color-blue-600); margin-top: 4px;">--</div>
        </div>
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Unassigned</div>
          <div id="metric-unassigned" style="font-size: 24px; font-weight: 700; color: var(--color-amber-600); margin-top: 4px;">--</div>
        </div>
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Under Scrutiny</div>
          <div id="metric-under-scrutiny" style="font-size: 24px; font-weight: 700; color: var(--color-blue-700); margin-top: 4px;">--</div>
        </div>
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Awaiting Review</div>
          <div id="metric-awaiting-review" style="font-size: 24px; font-weight: 700; color: var(--color-amber-700); margin-top: 4px;">--</div>
        </div>
        <div class="stat-card" style="padding: var(--space-4); border-radius: var(--radius-md); background: white; border: 1px solid var(--border-light); text-align: center;">
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Rec. Clear</div>
          <div id="metric-recommended-clear" style="font-size: 24px; font-weight: 700; color: var(--color-green-700); margin-top: 4px;">--</div>
        </div>
      </div>

      <!-- Queue Controls & Filters -->
      <div class="card" style="margin-bottom: var(--space-6);">
        <div class="card-body" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-4); padding: var(--space-4);">
          <!-- Filter Chips -->
          <div id="reviewer-filter-chips" style="display: flex; flex-wrap: wrap; gap: var(--space-2);">
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'all' ? 'btn-primary' : 'btn-secondary'}" data-filter="all">All Applications</button>
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'me' ? 'btn-primary' : 'btn-secondary'}" data-filter="me">Assigned to Me</button>
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'unassigned' ? 'btn-primary' : 'btn-secondary'}" data-filter="unassigned">Unassigned</button>
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'under_scrutiny' ? 'btn-primary' : 'btn-secondary'}" data-filter="under_scrutiny">Under Scrutiny</button>
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'recommended_clear' ? 'btn-primary' : 'btn-secondary'}" data-filter="recommended_clear">Recommended Clear</button>
            <button class="btn btn-sm btn-filter ${currentQueueState.filter === 'returned_for_correction' ? 'btn-primary' : 'btn-secondary'}" data-filter="returned_for_correction">Returned</button>
          </div>

          <!-- Search Box -->
          <div style="position: relative; min-width: 260px;">
            <input type="text" id="reviewer-search-input" class="form-control form-control-sm" placeholder="Search App No. or Institution..." style="padding-left: 32px;" value="${currentQueueState.search}">
            <span style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${icons.search}
            </span>
          </div>
        </div>
      </div>

      <!-- Queue Table Card -->
      <div class="card">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <div class="card-title">
            ${icons.clipboardList}
            <span id="queue-table-title">Scrutiny Queue</span>
          </div>
          <div style="font-size: var(--text-xs); color: var(--text-muted);">
            Session: 2026-2027 • AICTE Western & Southern Regions
          </div>
        </div>
        <div id="reviewer-table-container">
          <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
            <span class="spinner" aria-hidden="true"></span>
            <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading scrutiny cases from backend...</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

export async function initReviewerQueueView(state) {
  const container = document.getElementById('reviewer-table-container');
  if (!container) return;

  async function loadQueueData() {
    container.innerHTML = `
      <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
        <span class="spinner" aria-hidden="true"></span>
        <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Fetching applications for scrutiny...</p>
      </div>
    `;

    try {
      const params = {
        search: currentQueueState.search || undefined,
        page: currentQueueState.page,
        limit: currentQueueState.limit,
      };

      if (currentQueueState.filter === 'me') {
        params.assigned = 'me';
      } else if (currentQueueState.filter === 'unassigned') {
        params.assigned = 'unassigned';
      } else if (currentQueueState.filter === 'under_scrutiny') {
        params.review_status = 'UNDER_SCRUTINY';
      } else if (currentQueueState.filter === 'recommended_clear') {
        params.review_status = 'PRE_SCRUTINY_RECOMMENDED_CLEAR';
      } else if (currentQueueState.filter === 'returned_for_correction') {
        params.review_status = 'RETURNED_FOR_CORRECTION';
      }

      const res = await api.getReviewerQueue(params);
      renderQueueContent(res);
    } catch (err) {
      container.innerHTML = `
        <div style="padding: var(--space-6); text-align: center; color: var(--color-red-600);">
          <p style="font-weight: 600;">Failed to load scrutiny queue: ${err.message}</p>
          <button class="btn btn-secondary btn-sm" id="btn-retry-queue" style="margin-top: var(--space-3);">Retry</button>
        </div>
      `;
      document.getElementById('btn-retry-queue')?.addEventListener('click', loadQueueData);
    }
  }

  function renderQueueContent(data) {
    // 1. Update Metrics
    if (data.metrics) {
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val !== undefined ? val : 0;
      };
      setVal('metric-total-apps', data.metrics.total_applications);
      setVal('metric-assigned-me', data.metrics.assigned_to_me);
      setVal('metric-unassigned', data.metrics.unassigned);
      setVal('metric-under-scrutiny', data.metrics.under_scrutiny);
      setVal('metric-awaiting-review', data.metrics.awaiting_review);
      setVal('metric-recommended-clear', data.metrics.recommended_clear);
    }

    const titleEl = document.getElementById('queue-table-title');
    if (titleEl) {
      titleEl.textContent = `Applications Available for Scrutiny (${data.total || 0})`;
    }

    if (!data.items || data.items.length === 0) {
      container.innerHTML = `
        <div style="padding: var(--space-8); text-align: center; color: var(--text-muted);">
          <div style="font-size: 32px; margin-bottom: var(--space-2);">${icons.clipboardList}</div>
          <p style="font-weight: 600; font-size: var(--text-md);">No applications match the selected scrutiny filter.</p>
          <p style="font-size: var(--text-xs); margin-top: 4px;">Try selecting "All Applications" or adjusting your search keyword.</p>
        </div>
      `;
      return;
    }

    const currentUser = state.getCurrentUser() || {};

    container.innerHTML = `
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>App Number</th>
              <th>Institution & Location</th>
              <th>Pre-Scrutiny Findings</th>
              <th>Score</th>
              <th>Review Status</th>
              <th>Assigned Reviewer</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${data.items.map(app => {
              const isAssignedToMe = app.assigned_reviewer_id === currentUser.id;
              const hasDeficiencies = app.deficiencies_count > 0;
              const hasAwaitingReview = app.awaiting_review_count > 0;

              return `
                <tr>
                  <td>
                    <div style="font-family: var(--font-mono); font-weight: 700; color: var(--color-blue-800);">
                      <a href="#/reviewer/scrutiny/${app.id}">${app.application_number}</a>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted);">${app.application_type} • ${app.academic_year}</div>
                  </td>
                  <td>
                    <div style="font-weight: 600; color: var(--text-primary);">${app.institution_name}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">
                      PID: ${app.aicte_permanent_id} • ${app.district}, ${app.state}
                    </div>
                  </td>
                  <td>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      ${hasDeficiencies 
                        ? `<span class="badge badge-deficiency">${app.deficiencies_count} Deficiencies</span>`
                        : `<span class="badge badge-compliant">0 Deficiencies</span>`
                      }
                      ${hasAwaitingReview 
                        ? `<span class="badge badge-warning" style="font-size: 10px;">${app.awaiting_review_count} Awaiting Signoff</span>` 
                        : ''}
                    </div>
                  </td>
                  <td>
                    <div class="tabular-nums" style="font-weight: 700; font-size: 14px; color: ${app.pre_scrutiny_score >= 80 ? 'var(--color-green-700)' : app.pre_scrutiny_score >= 50 ? 'var(--color-amber-600)' : 'var(--color-red-600)'};">
                      ${app.pre_scrutiny_score}%
                    </div>
                  </td>
                  <td>
                    ${renderBadge(app.review_status, app.review_status.replace(/_/g, ' '))}
                  </td>
                  <td>
                    <div style="font-size: 12px; font-weight: 500;">
                      ${app.assigned_reviewer_name ? app.assigned_reviewer_name : '<span style="color: var(--text-muted); font-style: italic;">Unassigned</span>'}
                    </div>
                    ${!app.assigned_reviewer_id ? `
                      <button class="btn btn-secondary btn-sm btn-self-assign" data-app-id="${app.id}" style="font-size: 10px; padding: 2px 6px; margin-top: 4px;">
                        Assign to Me
                      </button>
                    ` : ''}
                  </td>
                  <td>
                    <a href="#/reviewer/scrutiny/${app.id}" class="btn btn-primary btn-sm" style="display: inline-flex; align-items: center; gap: 4px; white-space: nowrap;">
                      ${icons.shieldCheck}
                      <span>Open Console</span>
                    </a>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Bind Quick Self-Assign buttons
    container.querySelectorAll('.btn-self-assign').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const appId = e.currentTarget.dataset.appId;
        if (!appId || !currentUser.id) return;
        try {
          btn.disabled = true;
          btn.textContent = 'Assigning...';
          await api.assignReviewer(appId, currentUser.id, 'Self-assigned from Scrutiny Queue');
          await loadQueueData();
        } catch (err) {
          alert('Assignment failed: ' + err.message);
          btn.disabled = false;
          btn.textContent = 'Assign to Me';
        }
      });
    });
  }

  // Bind Filter Chips
  document.querySelectorAll('#reviewer-filter-chips .btn-filter').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('#reviewer-filter-chips .btn-filter').forEach(b => {
        b.classList.remove('btn-primary');
        b.classList.add('btn-secondary');
      });
      e.currentTarget.classList.remove('btn-secondary');
      e.currentTarget.classList.add('btn-primary');
      currentQueueState.filter = e.currentTarget.dataset.filter;
      currentQueueState.page = 1;
      loadQueueData();
    });
  });

  // Bind Search with debounce
  let searchTimeout = null;
  const searchInput = document.getElementById('reviewer-search-input');
  searchInput?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      currentQueueState.search = e.target.value.trim();
      currentQueueState.page = 1;
      loadQueueData();
    }, 300);
  });

  // Bind Refresh Button
  document.getElementById('btn-refresh-queue')?.addEventListener('click', loadQueueData);

  // Initial Load
  await loadQueueData();
}
