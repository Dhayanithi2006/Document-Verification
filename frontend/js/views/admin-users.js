// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Administrator User & Account Management (frontend/js/views/admin-users.js)

import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge, renderAlert } from '../components.js';
import { api } from '../api.js';

let userFilters = {
  role: '',
  is_active: undefined,
  search: '',
  skip: 0,
  limit: 50,
};

let institutionsCache = [];

export function renderAdminUsers(state) {
  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'System Administration' },
    { label: 'User & Role Provisioning' }
  ]);

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6); flex-wrap: wrap; gap: var(--space-4);">
        <div>
          <h1>User Accounts & Reviewer Role Governance</h1>
          <p style="color: var(--text-muted); margin-top: 4px;">
            Provision institutional applicants, assign scrutiny committee reviewers, and manage RBAC access states.
          </p>
        </div>
        <div style="display: flex; gap: var(--space-3); align-items: center;">
          <button id="btn-open-create-user" class="btn btn-primary btn-sm">
            ${icons.plus}
            <span>Provision New User</span>
          </button>
          <button id="btn-refresh-users" class="btn btn-secondary btn-sm">
            ${icons.refresh}
            <span>Refresh</span>
          </button>
        </div>
      </div>

      ${renderAlert('info', 'Role-Based Access Control (RBAC) Policy',
        'Users are strictly partitioned into INSTITUTION, REVIEWER, and ADMIN roles. Deactivated users are blocked instantaneously from accessing protected APIs. Passwords are encrypted with bcrypt (cost factor 12) and never stored or returned in plaintext.'
      )}

      <!-- Filter Controls -->
      <div class="card" style="margin-bottom: var(--space-6);">
        <div class="card-body" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-4); padding: var(--space-4);">
          <div style="display: flex; gap: var(--space-3); flex-wrap: wrap; align-items: center;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);" for="user-filter-role">Role:</label>
              <select id="user-filter-role" class="form-control form-control-sm">
                <option value="">All Roles</option>
                <option value="INSTITUTION">INSTITUTION</option>
                <option value="REVIEWER">REVIEWER</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            <div style="display: flex; align-items: center; gap: 8px;">
              <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);" for="user-filter-status">Status:</label>
              <select id="user-filter-status" class="form-control form-control-sm">
                <option value="">All Statuses</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive / Suspended</option>
              </select>
            </div>
          </div>

          <!-- Search Input -->
          <div style="position: relative; min-width: 260px;">
            <input type="text" id="user-search-input" class="form-control form-control-sm" placeholder="Search Email, Name, or Institution..." style="padding-left: 32px;" value="${userFilters.search}">
            <span style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${icons.search}
            </span>
          </div>
        </div>
      </div>

      <!-- Users Table Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            ${icons.users}
            <span id="users-table-title">System User Directory</span>
          </div>
        </div>
        <div id="users-table-container">
          <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
            <span class="spinner" aria-hidden="true"></span>
            <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Loading accounts from database...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Provision User Modal -->
    <div id="modal-create-user" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center;">
      <div style="background: white; border-radius: var(--radius-md); max-width: 520px; width: 90%; padding: var(--space-6); box-shadow: var(--shadow-xl);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);">
          <h2 style="margin: 0; font-size: 18px;">Provision New Account</h2>
          <button id="btn-close-create-modal" style="background: none; border: none; font-size: 20px; cursor: pointer;">&times;</button>
        </div>

        <form id="form-create-user">
          <div class="form-group" style="margin-bottom: var(--space-3);">
            <label class="form-label" for="new-email">Email Address <span class="required-star">*</span></label>
            <input type="email" id="new-email" class="form-control" required placeholder="user@platform.test">
          </div>

          <div class="form-group" style="margin-bottom: var(--space-3);">
            <label class="form-label" for="new-fullname">Full Name <span class="required-star">*</span></label>
            <input type="text" id="new-fullname" class="form-control" required placeholder="Dr. S. Ramanujan">
          </div>

          <div class="form-group" style="margin-bottom: var(--space-3);">
            <label class="form-label" for="new-password">Password <span class="required-star">*</span></label>
            <input type="password" id="new-password" class="form-control" required minlength="8" placeholder="Minimum 8 characters">
          </div>

          <div class="form-group" style="margin-bottom: var(--space-3);">
            <label class="form-label" for="new-role">Role <span class="required-star">*</span></label>
            <select id="new-role" class="form-control" required>
              <option value="REVIEWER">REVIEWER (Scrutiny Committee Member)</option>
              <option value="INSTITUTION">INSTITUTION (Applicant Principal / Director)</option>
              <option value="ADMIN">ADMIN (System Administrator)</option>
            </select>
          </div>

          <div class="form-group" id="group-institution-select" style="margin-bottom: var(--space-4); display: none;">
            <label class="form-label" for="new-institution">Linked Institution <span class="required-star">*</span></label>
            <select id="new-institution" class="form-control">
              <option value="">Select Institution...</option>
            </select>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-4);">
            <button type="button" id="btn-cancel-create" class="btn btn-secondary">Cancel</button>
            <button type="submit" id="btn-submit-create" class="btn btn-primary">Create Account</button>
          </div>
        </form>
      </div>
    </div>
  `;
}

export async function initAdminUsersView(state) {
  const container = document.getElementById('users-table-container');
  if (!container) return;

  // Load institutions for modal dropdown
  try {
    institutionsCache = await api.getAdminInstitutions();
    const instSelect = document.getElementById('new-institution');
    if (instSelect) {
      instSelect.innerHTML = `<option value="">Select Institution...</option>` +
        institutionsCache.map(i => `<option value="${i.id}">${i.name} (${i.aicte_permanent_id})</option>`).join('');
    }
  } catch (err) {
    console.error('Failed to pre-fetch institutions:', err);
  }

  async function loadUserData() {
    container.innerHTML = `
      <div style="text-align: center; padding: var(--space-8); color: var(--text-muted);">
        <span class="spinner" aria-hidden="true"></span>
        <p style="margin-top: var(--space-2); font-size: var(--text-sm);">Querying user accounts...</p>
      </div>
    `;

    try {
      const params = {
        role: userFilters.role || undefined,
        is_active: userFilters.is_active,
        search: userFilters.search || undefined,
        skip: userFilters.skip,
        limit: userFilters.limit,
      };

      const users = await api.getAdminUsers(params);
      renderUsersTable(users);
    } catch (err) {
      container.innerHTML = `
        <div style="padding: var(--space-6); text-align: center; color: var(--color-red-600);">
          <p style="font-weight: 600;">Failed to load user list: ${err.message}</p>
          <button class="btn btn-secondary btn-sm" id="btn-retry-users" style="margin-top: var(--space-3);">Retry</button>
        </div>
      `;
      document.getElementById('btn-retry-users')?.addEventListener('click', loadUserData);
    }
  }

  function renderUsersTable(users) {
    const titleEl = document.getElementById('users-table-title');
    if (titleEl) {
      titleEl.textContent = `System User Directory (${users.length} Accounts)`;
    }

    if (!users || users.length === 0) {
      container.innerHTML = `
        <div style="padding: var(--space-8); text-align: center; color: var(--text-muted);">
          <p style="font-weight: 600;">No accounts found matching filter.</p>
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
              <th>Full Name & Email</th>
              <th>Role</th>
              <th>Linked Institution</th>
              <th>Status</th>
              <th>Created Date</th>
              <th>Account Actions</th>
            </tr>
          </thead>
          <tbody>
            ${users.map(u => {
              const isSelf = u.id === currentUser.id;
              return `
                <tr>
                  <td>
                    <div style="font-weight: 700; color: var(--color-blue-900); font-size: 13px;">${u.full_name}</div>
                    <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${u.email}</div>
                  </td>
                  <td>
                    <span class="badge ${u.role === 'ADMIN' ? 'badge-deficiency' : u.role === 'REVIEWER' ? 'badge-info' : 'badge-compliant'}">
                      ${u.role}
                    </span>
                  </td>
                  <td>
                    <div style="font-size: 12px; font-weight: 500;">
                      ${u.institution_name ? u.institution_name : '<span style="color: var(--text-muted); font-style: italic;">None (AICTE Official)</span>'}
                    </div>
                  </td>
                  <td>
                    <span class="badge ${u.is_active ? 'badge-compliant' : 'badge-secondary'}">
                      ${u.is_active ? 'Active' : 'Deactivated'}
                    </span>
                  </td>
                  <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); white-space: nowrap;">
                    ${new Date(u.created_at).toISOString().slice(0, 10)}
                  </td>
                  <td>
                    ${isSelf ? `
                      <span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Current Session</span>
                    ` : `
                      <button class="btn btn-sm ${u.is_active ? 'btn-secondary' : 'btn-primary'} btn-toggle-active" data-user-id="${u.id}" data-current-active="${u.is_active}">
                        ${u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    `}
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Bind Toggle Active buttons
    container.querySelectorAll('.btn-toggle-active').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const uId = e.currentTarget.dataset.userId;
        const curActive = e.currentTarget.dataset.currentActive === 'true';
        const targetActive = !curActive;

        const conf = confirm(`Are you sure you want to ${targetActive ? 'activate' : 'deactivate'} this user account?`);
        if (!conf) return;

        try {
          btn.disabled = true;
          await api.updateAdminUser(uId, { is_active: targetActive });
          await loadUserData();
        } catch (err) {
          alert('Failed to update account status: ' + err.message);
          btn.disabled = false;
        }
      });
    });
  }

  // Filter Event Listeners
  document.getElementById('user-filter-role')?.addEventListener('change', (e) => {
    userFilters.role = e.target.value;
    loadUserData();
  });

  document.getElementById('user-filter-status')?.addEventListener('change', (e) => {
    const val = e.target.value;
    userFilters.is_active = val === '' ? undefined : (val === 'true');
    loadUserData();
  });

  let searchTimeout = null;
  document.getElementById('user-search-input')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      userFilters.search = e.target.value.trim();
      loadUserData();
    }, 300);
  });

  document.getElementById('btn-refresh-users')?.addEventListener('click', loadUserData);

  // Modal Controls
  const modal = document.getElementById('modal-create-user');
  const roleSelect = document.getElementById('new-role');
  const instGroup = document.getElementById('group-institution-select');

  roleSelect?.addEventListener('change', (e) => {
    if (e.target.value === 'INSTITUTION') {
      instGroup.style.display = 'block';
    } else {
      instGroup.style.display = 'none';
    }
  });

  const openModal = () => {
    modal.style.display = 'flex';
  };
  const closeModal = () => {
    modal.style.display = 'none';
    document.getElementById('form-create-user')?.reset();
    instGroup.style.display = 'none';
  };

  document.getElementById('btn-open-create-user')?.addEventListener('click', openModal);
  document.getElementById('btn-close-create-modal')?.addEventListener('click', closeModal);
  document.getElementById('btn-cancel-create')?.addEventListener('click', closeModal);

  // Form Submit
  document.getElementById('form-create-user')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('new-email').value.trim();
    const fullName = document.getElementById('new-fullname').value.trim();
    const password = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;
    const institutionId = role === 'INSTITUTION' ? document.getElementById('new-institution').value : null;

    if (role === 'INSTITUTION' && !institutionId) {
      alert('Please select an institution for an institution applicant account.');
      return;
    }

    const submitBtn = document.getElementById('btn-submit-create');
    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating...';

      await api.createAdminUser({
        email,
        full_name: fullName,
        password,
        role,
        institution_id: institutionId,
      });

      alert(`Account for ${fullName} (${role}) successfully created.`);
      closeModal();
      await loadUserData();
    } catch (err) {
      alert('Failed to provision account: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
    }
  });

  // Initial Data Load
  await loadUserData();
}
