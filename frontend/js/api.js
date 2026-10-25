// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Centralized API Client & Authentication Transport (api.js)

const TOKEN_KEY = 'aicte_auth_token';

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export class SessionExpiredError extends ApiError {
  constructor(message = 'Your session has expired or is invalid. Please sign in again.') {
    super(message, 401);
    this.name = 'SessionExpiredError';
  }
}

class ApiClient {
  constructor() {
    this.baseUrl = (typeof window !== 'undefined' && window.__API_BASE__) || '/api/v1';
    this.sessionExpiryListeners = [];
  }

  // Token storage helpers (sessionStorage preserves session across tab refreshes without persistent disk exposure)
  getToken() {
    if (typeof window === 'undefined' || !window.sessionStorage) return null;
    try {
      return window.sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  setToken(token) {
    if (typeof window === 'undefined' || !window.sessionStorage) return;
    try {
      if (token) {
        window.sessionStorage.setItem(TOKEN_KEY, token);
      } else {
        window.sessionStorage.removeItem(TOKEN_KEY);
      }
    } catch (e) {
      console.warn('Unable to persist token to sessionStorage:', e);
    }
  }

  clearToken() {
    this.setToken(null);
  }

  onSessionExpired(listener) {
    this.sessionExpiryListeners.push(listener);
    return () => {
      this.sessionExpiryListeners = this.sessionExpiryListeners.filter(l => l !== listener);
    };
  }

  notifySessionExpired() {
    this.clearToken();
    this.sessionExpiryListeners.forEach(fn => {
      try {
        fn();
      } catch (err) {
        console.error('Error in session expiry listener:', err);
      }
    });
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    const headers = {
      ...(options.headers || {})
    };

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
      response = await fetch(url, {
        ...options,
        headers
      });
    } catch (networkError) {
      throw new ApiError(
        'Unable to connect to the verification server. Please verify the backend service is running.',
        0,
        networkError.message
      );
    }

    // Handle Session Expiry / Revocation
    if (response.status === 401) {
      // Do not trigger loop if the request was itself a login attempt
      if (!endpoint.includes('/auth/login')) {
        this.notifySessionExpired();
        throw new SessionExpiredError();
      }
    }

    let data;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = null;
      }
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let detailMsg = 'An unexpected error occurred.';
      if (data && typeof data === 'object') {
        if (typeof data.detail === 'string') {
          detailMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
          detailMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
        }
      }

      // Contextual status codes
      if (response.status === 429) {
        detailMsg = detailMsg || 'Too many authentication attempts. Please wait 5 minutes before trying again.';
      } else if (response.status === 403) {
        detailMsg = detailMsg || 'Access restricted: account is inactive or lacks necessary permissions.';
      } else if (response.status === 401) {
        detailMsg = detailMsg || 'Invalid email or password.';
      }

      throw new ApiError(detailMsg, response.status, data);
    }

    return data;
  }

  // Auth Operations
  async login(email, password) {
    const payload = {
      email: String(email || '').trim().toLowerCase(),
      password: String(password || '')
    };

    const result = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (result && result.access_token) {
      this.setToken(result.access_token);
    }

    return result;
  }

  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      throw new ApiError('No active session token found.', 401);
    }

    return await this.request('/auth/me', {
      method: 'GET'
    });
  }

  async logout() {
    const token = this.getToken();
    let remoteSuccess = false;
    if (token) {
      try {
        await this.request('/auth/logout', {
          method: 'POST'
        });
        remoteSuccess = true;
      } catch (err) {
        console.warn('Remote logout failed, proceeding with local cleanup:', err);
      }
    }
    this.clearToken();
    return { success: true, remoteRevoked: remoteSuccess };
  }

  // Application Operations
  async getApplications() {
    return await this.request('/applications', { method: 'GET' });
  }

  async getApplication(id) {
    return await this.request(`/applications/${id}`, { method: 'GET' });
  }

  async createApplication(data) {
    return await this.request('/applications', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateApplication(id, data) {
    return await this.request(`/applications/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async getChecklist(id) {
    return await this.request(`/applications/${id}/checklist`, { method: 'GET' });
  }

  // Document Operations
  async uploadDocument(applicationId, documentType, file) {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);

    return await this.request(`/applications/${applicationId}/documents`, {
      method: 'POST',
      body: formData
    });
  }

  async deleteDocument(applicationId, documentType) {
    return await this.request(`/applications/${applicationId}/documents/${documentType}`, {
      method: 'DELETE'
    });
  }

  async getDocumentBlobUrl(documentId, version = 1) {
    const token = this.getToken();
    const url = `${this.baseUrl}/documents/${documentId}/versions/${version}/file`;
    const resp = await fetch(url, {
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    });

    if (!resp.ok) {
      let errorMsg = 'Failed to load document binary.';
      try {
        const errJson = await resp.json();
        if (errJson && errJson.detail) errorMsg = errJson.detail;
      } catch {
        // default message
      }
      throw new ApiError(errorMsg, resp.status);
    }

    const blob = await resp.blob();
    return URL.createObjectURL(blob);
  }

  // IDP Extraction & Evidence Operations
  async processDocument(documentId, version = null, force = false) {
    const params = new URLSearchParams();
    if (version !== null) params.append('version', version);
    if (force) params.append('force', 'true');
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/documents/${documentId}/process${query}`, {
      method: 'POST'
    });
  }

  async getDocumentProcessingStatus(documentId, version = null) {
    const params = new URLSearchParams();
    if (version !== null) params.append('version', version);
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/documents/${documentId}/processing-status${query}`, {
      method: 'GET'
    });
  }

  async getDocumentExtractedFields(documentId, version = null) {
    const params = new URLSearchParams();
    if (version !== null) params.append('version', version);
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/documents/${documentId}/extracted-fields${query}`, {
      method: 'GET'
    });
  }

  async getDocumentPages(documentId, version = null) {
    const params = new URLSearchParams();
    if (version !== null) params.append('version', version);
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/documents/${documentId}/pages${query}`, {
      method: 'GET'
    });
  }

  // Regulatory Engine & Pre-Scrutiny Findings
  async validateApplication(applicationId) {
    return await this.request(`/applications/${applicationId}/validate`, {
      method: 'POST'
    });
  }

  async getApplicationFindings(applicationId) {
    return await this.request(`/applications/${applicationId}/findings`, {
      method: 'GET'
    });
  }

  async getApplicationValidationStatus(applicationId) {
    return await this.request(`/applications/${applicationId}/validation-status`, {
      method: 'GET'
    });
  }

  async getFinding(findingId) {
    return await this.request(`/findings/${findingId}`, {
      method: 'GET'
    });
  }

  async getRules(category = null) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/rules${query}`, {
      method: 'GET'
    });
  }

  async getRule(ruleCode) {
    return await this.request(`/rules/${ruleCode}`, {
      method: 'GET'
    });
  }

  async activateRule(ruleCode) {
    return await this.request(`/rules/${ruleCode}/activate`, {
      method: 'POST'
    });
  }

  // Deficiency Resolution, Corrective Actions & Controlled Revalidation (Phase P8)
  async getApplicationDeficiencies(applicationId) {
    return await this.request(`/applications/${applicationId}/deficiencies`, {
      method: 'GET'
    });
  }

  async acknowledgeFinding(findingId) {
    return await this.request(`/findings/${findingId}/acknowledge`, {
      method: 'POST'
    });
  }

  async getFindingResponse(findingId) {
    return await this.request(`/findings/${findingId}/response`, {
      method: 'GET'
    });
  }

  async saveDraftResponse(findingId, data) {
    return await this.request(`/findings/${findingId}/response`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async submitCorrection(findingId, data) {
    return await this.request(`/findings/${findingId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async revalidateApplication(applicationId) {
    return await this.request(`/applications/${applicationId}/revalidate`, {
      method: 'POST'
    });
  }

  async getFindingHistory(findingId) {
    return await this.request(`/findings/${findingId}/history`, {
      method: 'GET'
    });
  }

  async resolveFindingWithDocument(findingId, formData) {
    return await this.request(`/findings/${findingId}/resolve`, {
      method: 'POST',
      body: formData
    });
  }

  // Phase P9: Reviewer Scrutiny Workspace
  async getReviewerQueue(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.review_status) query.append('review_status', params.review_status);
    if (params.assigned) query.append('assigned', params.assigned);
    if (params.academic_year) query.append('academic_year', params.academic_year);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return await this.request(`/reviewer/queue${qs ? '?' + qs : ''}`, { method: 'GET' });
  }

  async getScrutinyDetails(applicationId) {
    return await this.request(`/reviewer/applications/${applicationId}/scrutiny`, {
      method: 'GET'
    });
  }

  async assignReviewer(applicationId, targetReviewerId, remarks = null) {
    return await this.request(`/reviewer/applications/${applicationId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_reviewer_id: targetReviewerId, remarks })
    });
  }

  async recordReviewerObservation(applicationId, data) {
    return await this.request(`/reviewer/applications/${applicationId}/observations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async completePrescrutinyDecision(applicationId, data) {
    return await this.request(`/reviewer/applications/${applicationId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  // Phase P9: Administrator Workspace
  async getAdminOverview() {
    return await this.request('/admin/overview', { method: 'GET' });
  }

  async getAdminUsers(params = {}) {
    const query = new URLSearchParams();
    if (params.role) query.append('role', params.role);
    if (params.is_active !== undefined) query.append('is_active', params.is_active);
    if (params.search) query.append('search', params.search);
    if (params.skip) query.append('skip', params.skip);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return await this.request(`/admin/users${qs ? '?' + qs : ''}`, { method: 'GET' });
  }

  async createAdminUser(data) {
    return await this.request('/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async updateAdminUser(userId, data) {
    return await this.request(`/admin/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async getAdminInstitutions(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.skip) query.append('skip', params.skip);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return await this.request(`/admin/institutions${qs ? '?' + qs : ''}`, { method: 'GET' });
  }

  async updateAdminInstitution(institutionId, data) {
    return await this.request(`/admin/institutions/${institutionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  async getAdminAuditEvents(params = {}) {
    const query = new URLSearchParams();
    if (params.action) query.append('action', params.action);
    if (params.actor_role) query.append('actor_role', params.actor_role);
    if (params.entity_type) query.append('entity_type', params.entity_type);
    if (params.skip) query.append('skip', params.skip);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return await this.request(`/admin/audit-events${qs ? '?' + qs : ''}`, { method: 'GET' });
  }
}

export const api = new ApiClient();
