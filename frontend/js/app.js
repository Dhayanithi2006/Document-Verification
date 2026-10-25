// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Application Bootstrap & Controller (app.js)
import { state } from './state.js';
import { Router } from './router.js';
import { renderHeader, renderSidebar } from './components.js';

class App {
  constructor() {
    this.state = state;
    this.router = null;
  }

  async init() {
    this.renderShell();
    this.router = new Router(this.state, 'main-content');
    
    // Subscribe to state events
    this.state.subscribe((event, data) => {
      if (event === 'ROLE_CHANGED' || event === 'AUTH_STATE_CHANGED') {
        this.updateHeaderAndSidebar();
        this.router.handleRoute();
      } else if (event === 'ROUTE_CHANGED') {
        this.updateSidebarActiveLink(data.route);
      } else if (event === 'SESSION_EXPIRED') {
        this.updateHeaderAndSidebar();
        this.router.navigate('/login');
      } else if (event === 'USER_LOGGED_OUT') {
        this.updateHeaderAndSidebar();
        this.router.navigate('/login');
      }
    });

    this.bindGlobalEvents();

    // Restore real session asynchronously from backend
    await this.state.initSession();
    this.router.handleRoute();
  }

  renderShell() {
    const rootEl = document.getElementById('app');
    if (!rootEl) return;

    const user = this.state.getCurrentUser();
    const role = this.state.activeRole;
    const isAuth = this.state.isAuthenticated();

    rootEl.innerHTML = `
      <!-- Accessibility: Skip to Main Content Link -->
      <a href="#main-content" class="skip-link">Skip to main government content</a>

      <!-- Mandatory Persistent Disclaimer Notice -->
      <aside class="disclaimer-banner" role="note" aria-label="Official Prototype Notice">
        <span class="disclaimer-badge">SIH PROTOTYPE</span>
        <span>Not an official AICTE portal. Created for Smart India Hackathon decision-support demonstration.</span>
      </aside>

      <!-- Government Top Header -->
      <div id="header-container">
        ${renderHeader(user, role, isAuth)}
      </div>

      <!-- Main Workspace Shell -->
      <div class="workspace-shell">
        <div id="sidebar-container">
          ${renderSidebar(role, window.location.hash || '#/dashboard')}
        </div>

        <main id="main-content" class="main-wrapper" tabindex="-1">
          <!-- Active Page View dynamically mounted here by Router -->
        </main>
      </div>

      <!-- Government Minimal Footer -->
      <footer class="app-footer" role="contentinfo">
        <div class="footer-meta">
          <strong>AICTE Pre-Scrutiny Platform</strong>
          <span>•</span>
          <span>SIH AICTE Problem Statement Prototype</span>
          <span>•</span>
          <span>Approval Process Handbook (APH 2024-2027) Norms</span>
        </div>
        <div style="font-size: 11px; color: #64748B;">
          GIGW 3.0 Accessible Interface Baseline
        </div>
      </footer>
      <div class="footer-tricolor-bar" aria-hidden="true"></div>

      <!-- Global Accessible Modal Container -->
      <div id="modal-container"></div>
    `;
  }

  updateHeaderAndSidebar() {
    const user = this.state.getCurrentUser();
    const role = this.state.activeRole;
    const isAuth = this.state.isAuthenticated();
    
    const headerContainer = document.getElementById('header-container');
    if (headerContainer) {
      headerContainer.innerHTML = renderHeader(user, role, isAuth);
    }

    const sidebarContainer = document.getElementById('sidebar-container');
    if (sidebarContainer) {
      sidebarContainer.innerHTML = renderSidebar(role, window.location.hash || '#/dashboard');
    }

    this.bindHeaderEvents();
  }

  updateSidebarActiveLink(currentRoute) {
    const links = document.querySelectorAll('.app-sidebar .nav-link');
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (href === currentRoute || (href !== '#/dashboard' && currentRoute.startsWith(href))) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  bindHeaderEvents() {
    // Role switcher (preview mode when unauthenticated)
    const roleSelect = document.getElementById('role-preview-select');
    if (roleSelect) {
      roleSelect.addEventListener('change', async (e) => {
        if (this.state.isAuthenticated()) {
          try {
            await this.state.logout();
          } catch (err) {
            console.warn('Logout error:', err);
          }
          this.router.navigate('/login');
        } else {
          this.state.setRole(e.target.value);
        }
      });
    }

    // Explicit switch account action (logs out and navigates to login)
    const switchAccountBtn = document.getElementById('btn-switch-account');
    if (switchAccountBtn) {
      switchAccountBtn.addEventListener('click', async () => {
        try {
          await this.state.logout();
        } catch (err) {
          console.warn('Logout error during account switch:', err);
        }
        this.router.navigate('/login');
      });
    }

    // Sign out button
    const logoutBtn = document.getElementById('btn-header-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        try {
          await this.state.logout();
        } catch (err) {
          console.warn('Logout error:', err);
        }
        this.router.navigate('/login');
      });
    }
  }

  bindGlobalEvents() {
    this.bindHeaderEvents();

    // Modal resolution helper attached to window for prototype demo
    window.openResolutionModal = (findingId, docTitle) => {
      const modalContainer = document.getElementById('modal-container');
      if (!modalContainer) return;

      modalContainer.innerHTML = `
        <div class="modal-backdrop open" id="resolution-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div class="modal-dialog">
            <div class="modal-header">
              <div class="modal-title" id="modal-title">Resolve Deficiency: ${findingId}</div>
              <button class="modal-close" onclick="window.closeResolutionModal();" aria-label="Close dialog">✕</button>
            </div>
            <div class="modal-body">
              <p style="font-size: 13px; color: var(--text-muted); margin-bottom: var(--space-4);">
                Target Document: <strong>${docTitle}</strong>
              </p>
              
              <div style="background-color: var(--color-blue-50); border: 1px solid var(--color-blue-100); padding: var(--space-3); border-radius: var(--radius-sm); margin-bottom: var(--space-4); font-size: 12px; color: var(--color-blue-800);">
                <strong>Prototype Action:</strong> Uploading document version v2 will be processed by Core Engine A (OCR & Extraction) and Core Engine B (Delta-Revalidation) in subsequent phases.
              </div>

              <div class="form-group">
                <label class="form-label">Upload Corrected Document Version (v2 PDF)</label>
                <input type="file" class="form-control" accept=".pdf">
                <div class="form-help">Max 15MB. Must be valid PDF format.</div>
              </div>

              <div class="form-group">
                <label class="form-label">Institutional Remarks / Explanation</label>
                <textarea class="form-control" rows="3" placeholder="Explain the rectification made in this corrected version..."></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" onclick="window.closeResolutionModal();">Cancel</button>
              <button class="btn btn-primary" onclick="alert('Document v2 queued for automated delta-revalidation. (Simulated prototype action)'); window.closeResolutionModal();">
                Submit Version 2 for Revalidation
              </button>
            </div>
          </div>
        </div>
      `;
    };

    window.closeResolutionModal = () => {
      const modalContainer = document.getElementById('modal-container');
      if (modalContainer) modalContainer.innerHTML = '';
    };
  }
}

// Bootstrap on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
