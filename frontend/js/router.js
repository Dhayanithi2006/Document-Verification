// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Client-Side SPA Hash Router with Role Guards (router.js)
import { renderDashboard } from './views/dashboard.js';
import { renderApplicationsList, initApplicationsListView } from './views/applications-list.js';
import { renderApplicationNew, initApplicationNewView } from './views/application-new.js';
import { renderApplicationDetail, initApplicationDetailView } from './views/application-detail.js';
import { renderEvidenceInspector } from './views/evidence-inspector.js';
import { renderDeficiencyBridge, initDeficiencyBridgeView } from './views/deficiency-bridge.js';
import { renderReviewerQueue, initReviewerQueueView } from './views/reviewer-queue.js';
import { renderReviewerScrutiny, initReviewerScrutinyView } from './views/reviewer-scrutiny.js';
import { renderAdminRules, initAdminRulesView } from './views/admin-rules.js';
import { renderAdminAudit, initAdminAuditView } from './views/admin-audit.js';
import { renderAdminUsers, initAdminUsersView } from './views/admin-users.js';
import { renderLogin, initLoginView } from './views/login.js';
import { renderNotFound } from './views/not-found.js';
import { renderAccessDenied } from './views/access-denied.js';

export class Router {
  constructor(state, contentTargetId = 'main-content') {
    this.state = state;
    this.contentTargetId = contentTargetId;

    // Route Definitions with Role Permissions & Public access flags
    this.routes = [
      { 
        pattern: /^\/?$/, 
        view: renderDashboard, 
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/dashboard$/, 
        view: renderDashboard, 
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/applications$/, 
        view: renderApplicationsList, 
        init: initApplicationsListView,
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/applications\/new$/, 
        view: renderApplicationNew, 
        init: initApplicationNewView,
        isPublic: false, 
        allowedRoles: ['INSTITUTION'] 
      },
      { 
        pattern: /^\/applications\/([^/]+)$/, 
        view: renderApplicationDetail, 
        init: initApplicationDetailView,
        paramNames: ['id'], 
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/applications\/([^/]+)\/evidence\/([^/]+)$/, 
        view: renderEvidenceInspector, 
        paramNames: ['id', 'finding_id'], 
        isPublic: false, 
        allowedRoles: ['REVIEWER', 'ADMIN', 'INSTITUTION'] 
      },
      { 
        pattern: /^\/applications\/([^/]+)\/deficiencies$/, 
        view: renderDeficiencyBridge, 
        init: initDeficiencyBridgeView,
        paramNames: ['id'], 
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/applications\/([^/]+)\/deficiency-bridge$/, 
        view: renderDeficiencyBridge, 
        init: initDeficiencyBridgeView,
        paramNames: ['id'], 
        isPublic: false, 
        allowedRoles: ['INSTITUTION', 'REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/reviewer\/queue$/, 
        view: renderReviewerQueue, 
        init: initReviewerQueueView,
        isPublic: false, 
        allowedRoles: ['REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/reviewer\/scrutiny\/([^/]+)$/, 
        view: renderReviewerScrutiny, 
        init: initReviewerScrutinyView,
        paramNames: ['id'], 
        isPublic: false, 
        allowedRoles: ['REVIEWER', 'ADMIN'] 
      },
      { 
        pattern: /^\/admin\/rules$/, 
        view: renderAdminRules, 
        init: initAdminRulesView,
        isPublic: false, 
        allowedRoles: ['ADMIN', 'REVIEWER', 'INSTITUTION'] 
      },
      { 
        pattern: /^\/admin\/audit$/, 
        view: renderAdminAudit, 
        init: initAdminAuditView,
        isPublic: false, 
        allowedRoles: ['ADMIN', 'REVIEWER'] 
      },
      { 
        pattern: /^\/admin\/users$/, 
        view: renderAdminUsers, 
        init: initAdminUsersView,
        isPublic: false, 
        allowedRoles: ['ADMIN'] 
      },
      { 
        pattern: /^\/login$/, 
        view: renderLogin, 
        init: initLoginView,
        isPublic: true 
      }
    ];

    this.currentHash = '';
    if (typeof window !== 'undefined') {
      window.addEventListener('hashchange', () => this.handleRoute());
    }
  }

  getCurrentRoute() {
    if (typeof window === 'undefined') return '/dashboard';
    let hash = window.location.hash.slice(1) || '/dashboard';
    if (!hash.startsWith('/')) hash = '/' + hash;
    return hash;
  }

  getDefaultRouteForRole(role) {
    if (role === 'INSTITUTION') return '/dashboard';
    if (role === 'REVIEWER') return '/reviewer/queue';
    if (role === 'ADMIN') return '/admin/rules';
    return '/dashboard';
  }

  updateShellLayout(pathOnly) {
    if (typeof document === 'undefined') return;
    const workspaceShell = document.querySelector('.workspace-shell');
    if (workspaceShell) {
      if (pathOnly === '/login') {
        workspaceShell.classList.add('hide-sidebar');
      } else {
        workspaceShell.classList.remove('hide-sidebar');
      }
    }
  }

  handleRoute() {
    if (typeof window === 'undefined') return;

    const rawHash = window.location.hash.slice(1);
    if (!rawHash) {
      // If user is authenticated, redirect to default role home, else login
      if (this.state.isAuthenticated()) {
        window.location.hash = '#' + this.getDefaultRouteForRole(this.state.activeRole);
      } else {
        window.location.hash = '#/dashboard';
      }
      return;
    }

    let fullPath = rawHash;
    if (!fullPath.startsWith('/')) fullPath = '/' + fullPath;
    this.currentHash = '#' + fullPath;

    // Parse path and query parameters
    const [pathOnly, queryString] = fullPath.split('?');
    const queryParams = {};
    if (queryString) {
      const searchParams = new URLSearchParams(queryString);
      for (const [key, val] of searchParams.entries()) {
        queryParams[key] = val;
      }
    }

    const targetEl = document.getElementById(this.contentTargetId);
    if (!targetEl) return;

    // 1. Auth Initializing Guard
    if (this.state.authStatus === 'initializing') {
      targetEl.innerHTML = `
        <div class="auth-loading-state" role="status" aria-live="polite">
          <div class="auth-spinner-large" aria-hidden="true"></div>
          <div><strong style="color: var(--color-navy-900);">Verifying Session Credentials...</strong></div>
          <div style="font-size: 11px; color: var(--text-muted);">Secure Government Gateway Verification</div>
        </div>
      `;
      this.updateShellLayout(pathOnly);
      return;
    }

    // Match Route
    let matchedRoute = null;
    let extractedParams = {};

    for (const r of this.routes) {
      const match = pathOnly.match(r.pattern);
      if (match) {
        matchedRoute = r;
        if (r.paramNames) {
          r.paramNames.forEach((name, i) => {
            extractedParams[name] = match[i + 1];
          });
        }
        break;
      }
    }

    // 2. 404 Route handling
    if (!matchedRoute) {
      targetEl.innerHTML = renderNotFound(this.state);
      this.updateShellLayout(pathOnly);
      window.scrollTo(0, 0);
      this.state.notifyListeners('ROUTE_CHANGED', { route: this.currentHash });
      return;
    }

    // 3. Unauthenticated Guard on Protected Routes
    if (!this.state.isAuthenticated() && !matchedRoute.isPublic) {
      // Validate and preserve internal return destination
      const returnParam = encodeURIComponent(fullPath);
      this.updateShellLayout('/login');
      window.location.hash = `#/login?returnTo=${returnParam}`;
      return;
    }

    // 4. Authenticated User on /login: Redirect to Role Home
    if (this.state.isAuthenticated() && pathOnly === '/login') {
      const dest = this.getDefaultRouteForRole(this.state.activeRole);
      this.updateShellLayout(dest);
      window.location.hash = '#' + dest;
      return;
    }

    // 5. Role Authorization Guard (403 Access Denied)
    if (this.state.isAuthenticated() && matchedRoute.allowedRoles) {
      if (!matchedRoute.allowedRoles.includes(this.state.activeRole)) {
        targetEl.innerHTML = renderAccessDenied(this.state, { targetSection: pathOnly });
        this.updateShellLayout(pathOnly);
        window.scrollTo(0, 0);
        this.state.notifyListeners('ROUTE_CHANGED', { route: this.currentHash });
        return;
      }
    }

    // Combine route params and query params
    const mergedParams = { ...extractedParams, ...queryParams };

    // Render View
    targetEl.innerHTML = matchedRoute.view(this.state, mergedParams);
    this.updateShellLayout(pathOnly);
    window.scrollTo(0, 0);

    // Initialize View Hooks (e.g., event listeners, async backend loading)
    if (matchedRoute.init) {
      matchedRoute.init(this.state, this, mergedParams);
    } else if (pathOnly === '/login') {
      initLoginView(this.state, this);
    }

    // Trigger route update event (for updating sidebar active states)
    this.state.notifyListeners('ROUTE_CHANGED', { route: this.currentHash });
  }

  navigate(path) {
    if (typeof window === 'undefined') return;
    window.location.hash = path.startsWith('#') ? path : '#' + path;
  }
}
