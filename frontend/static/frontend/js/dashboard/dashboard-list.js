/**
 * Dashboard List Module
 *
 * Renders incident list in the sidebar
 */

import { DashboardState } from './dashboard-state.js';

/**
 * Check if we're on a mobile/tablet viewport where the right panel is hidden
 */
function isMobileView() {
  return window.innerWidth < 992;
}

const SEVERITY_BADGE = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'success'
};

const STATUS_BADGE = {
  pending: 'secondary',
  dispatched: 'primary',
  en_route: 'info',
  on_scene: 'warning',
  resolved: 'success',
  cancelled: 'dark'
};

/**
 * Render incidents list
 */
export function renderIncidentsList() {
  const listContainer = document.getElementById('incidentsList');
  if (!listContainer) return;

  const incidents = DashboardState.getFilteredIncidents();

  if (incidents.length === 0) {
    const hasFilters = DashboardState.filters.status ||
                       DashboardState.filters.severity ||
                       DashboardState.filters.incident_type;
    listContainer.innerHTML = `
      <div class="text-center text-muted p-4">
        <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48" class="mb-3 opacity-50">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <p class="mb-2"><strong>No incidents found</strong></p>
        <p class="small mb-0">
          ${hasFilters
            ? 'Try adjusting your filters to see more results.'
            : 'There are no active incidents at this time.'}
        </p>
      </div>
    `;
    return;
  }

  // Sort by created_at descending (newest first)
  const sorted = [...incidents].sort((a, b) => {
    return new Date(b.properties.created_at) - new Date(a.properties.created_at);
  });

  const html = sorted.map(incident => renderIncidentCard(incident)).join('');
  listContainer.innerHTML = html;

  // Add click handlers
  sorted.forEach(incident => {
    const card = document.getElementById(`incident-${incident.id}`);
    if (card) {
      card.addEventListener('click', () => {
        DashboardState.selectIncident(incident);

        if (isMobileView()) {
          // On mobile, show the modal instead of switching tabs
          showMobileDetailModal(incident);
        } else {
          // On desktop, switch to detail tab
          const detailTab = document.getElementById('detail-tab');
          if (detailTab) {
            detailTab.click();
          }
        }
      });
    }
  });
}

/**
 * Render single incident card
 */
function renderIncidentCard(incident) {
  const props = incident.properties;
  const incidentId = incident.id;
  const isSelected = DashboardState.selectedIncident?.id === incidentId;
  
  const timeAgo = getTimeAgo(new Date(props.created_at));

  return `
    <div 
      id="incident-${incidentId}"
      class="incident-card ${isSelected ? 'selected' : ''}"
      role="button"
      tabindex="0"
    >
      <div class="d-flex justify-content-between align-items-start mb-2">
        <h6 class="mb-0 flex-grow-1">${escapeHtml(props.title)}</h6>
        <span class="badge bg-${SEVERITY_BADGE[props.severity]}">${props.severity_display}</span>
      </div>
      <div class="mb-2">
        <span class="badge bg-${STATUS_BADGE[props.status]} me-1">${props.status_display}</span>
        <span class="badge bg-light text-dark">${props.incident_type_display}</span>
      </div>
      <p class="small text-muted mb-1">
        <i class="bi bi-geo-alt"></i> ${escapeHtml(props.address || 'No address')}
      </p>
      <p class="small text-muted mb-0">
        <i class="bi bi-clock"></i> ${timeAgo}
      </p>
    </div>
  `;
}

/**
 * Render incident detail panel
 */
export function renderIncidentDetail() {
  const detailContainer = document.getElementById('incidentDetail');
  if (!detailContainer) return;

  const incident = DashboardState.selectedIncident;
  
  if (!incident) {
    detailContainer.innerHTML = `
      <div class="text-center text-muted p-4">
        <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48" class="mb-3 opacity-50">
          <path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/>
        </svg>
        <p class="mb-2"><strong>No incident selected</strong></p>
        <p class="small mb-0">Click on an incident from the list or map to view its details.</p>
      </div>
    `;
    return;
  }

  const props = incident.properties;
  const currentUser = DashboardState.currentUser;
  const canDispatch = currentUser?.is_dispatcher;
  const canUpdateStatus = currentUser?.is_dispatcher || 
                          currentUser?.is_responder;

  detailContainer.innerHTML = `
    <div class="incident-detail-content">
      <div class="d-flex justify-content-between align-items-start mb-3">
        <h5>${escapeHtml(props.title)}</h5>
        <div>
          <span class="badge bg-${SEVERITY_BADGE[props.severity]} me-1">${props.severity_display}</span>
          <span class="badge bg-${STATUS_BADGE[props.status]}">${props.status_display}</span>
        </div>
      </div>

      <div class="mb-3">
        <strong>Type:</strong> ${props.incident_type_display}
      </div>

      ${props.description ? `
        <div class="mb-3">
          <strong>Description:</strong>
          <p class="mb-0">${escapeHtml(props.description)}</p>
        </div>
      ` : ''}

      <div class="mb-3">
        <strong>Address:</strong>
        <p class="mb-0">${escapeHtml(props.address || 'Not specified')}</p>
      </div>

      <div class="mb-3">
        <strong>Reported by:</strong> ${props.reported_by_name || 'Unknown'}
      </div>

      ${props.assigned_responder_name ? `
        <div class="mb-3">
          <strong>Assigned to:</strong> ${props.assigned_responder_name}
        </div>
      ` : ''}

      ${props.nearest_facility_name ? `
        <div class="mb-3">
          <strong>Nearest Facility:</strong> ${props.nearest_facility_name}
        </div>
      ` : ''}

      <div class="mb-3">
        <strong>Created:</strong> ${formatDateTime(props.created_at)}
      </div>

      ${props.dispatched_at ? `
        <div class="mb-3">
          <strong>Dispatched:</strong> ${formatDateTime(props.dispatched_at)}
        </div>
      ` : ''}

      ${props.route_distance_m ? `
        <div class="mb-3">
          <strong>Route Distance:</strong> ${(props.route_distance_m / 1000).toFixed(2)} km<br>
          <strong>Estimated Duration:</strong> ${Math.round(props.route_duration_s / 60)} minutes
        </div>
      ` : ''}

      <div class="mt-4">
        ${canDispatch && props.status === 'pending' ? `
          <button 
            class="btn btn-primary w-100 mb-2" 
            onclick="window.dashboardActions.openDispatchModal(${incident.id})"
          >
            <i class="bi bi-send"></i> Dispatch Vehicle
          </button>
        ` : ''}
        
        ${canUpdateStatus && props.is_active ? `
          <div class="btn-group w-100 mb-2" role="group">
            ${props.status !== 'en_route' ? `
              <button 
                class="btn btn-sm btn-outline-primary" 
                onclick="window.dashboardActions.updateStatus(${incident.id}, 'en_route')"
              >
                En Route
              </button>
            ` : ''}
            ${props.status !== 'on_scene' ? `
              <button 
                class="btn btn-sm btn-outline-warning" 
                onclick="window.dashboardActions.updateStatus(${incident.id}, 'on_scene')"
              >
                On Scene
              </button>
            ` : ''}
            <button 
              class="btn btn-sm btn-outline-success" 
              onclick="window.dashboardActions.updateStatus(${incident.id}, 'resolved')"
            >
              Resolve
            </button>
          </div>
        ` : ''}

        <button 
          class="btn btn-outline-secondary btn-sm w-100" 
          onclick="window.dashboardActions.focusOnMap(${incident.id})"
        >
          <i class="bi bi-geo-alt"></i> Show on Map
        </button>
      </div>
    </div>
  `;
}

/**
 * Show incident detail in mobile modal
 */
function showMobileDetailModal(incident) {
  const modalContent = document.getElementById('mobileDetailContent');
  const modalTitle = document.getElementById('mobileDetailModalLabel');
  const modal = document.getElementById('mobileDetailModal');

  if (!modalContent || !modal) return;

  const props = incident.properties;
  const currentUser = DashboardState.currentUser;
  const canDispatch = currentUser?.is_dispatcher;
  const canUpdateStatus = currentUser?.is_dispatcher || currentUser?.is_responder;

  // Update modal title
  if (modalTitle) {
    modalTitle.textContent = props.title;
  }

  // Render content (similar to renderIncidentDetail but without the title)
  modalContent.innerHTML = `
    <div class="mb-3">
      <span class="badge bg-${SEVERITY_BADGE[props.severity]} me-1">${props.severity_display}</span>
      <span class="badge bg-${STATUS_BADGE[props.status]}">${props.status_display}</span>
      <span class="badge bg-light text-dark">${props.incident_type_display}</span>
    </div>

    ${props.description ? `
      <div class="mb-3">
        <strong>Description:</strong>
        <p class="mb-0">${escapeHtml(props.description)}</p>
      </div>
    ` : ''}

    <div class="mb-3">
      <strong>Address:</strong>
      <p class="mb-0">${escapeHtml(props.address || 'Not specified')}</p>
    </div>

    <div class="mb-3">
      <strong>Reported by:</strong> ${props.reported_by_name || 'Unknown'}
    </div>

    ${props.assigned_responder_name ? `
      <div class="mb-3">
        <strong>Assigned to:</strong> ${props.assigned_responder_name}
      </div>
    ` : ''}

    ${props.nearest_facility_name ? `
      <div class="mb-3">
        <strong>Nearest Facility:</strong> ${props.nearest_facility_name}
      </div>
    ` : ''}

    <div class="mb-3">
      <strong>Created:</strong> ${formatDateTime(props.created_at)}
    </div>

    ${props.route_distance_m ? `
      <div class="mb-3">
        <strong>Route:</strong> ${(props.route_distance_m / 1000).toFixed(2)} km (~${Math.round(props.route_duration_s / 60)} min)
      </div>
    ` : ''}

    <div class="mt-4">
      ${canDispatch && props.status === 'pending' ? `
        <button
          class="btn btn-primary w-100 mb-2"
          onclick="window.dashboardActions.openDispatchModal(${incident.id})"
        >
          Dispatch Vehicle
        </button>
      ` : ''}

      ${canUpdateStatus && props.is_active ? `
        <div class="btn-group w-100 mb-2" role="group">
          ${props.status !== 'en_route' ? `
            <button
              class="btn btn-sm btn-outline-primary"
              onclick="window.dashboardActions.updateStatus(${incident.id}, 'en_route')"
            >
              En Route
            </button>
          ` : ''}
          ${props.status !== 'on_scene' ? `
            <button
              class="btn btn-sm btn-outline-warning"
              onclick="window.dashboardActions.updateStatus(${incident.id}, 'on_scene')"
            >
              On Scene
            </button>
          ` : ''}
          <button
            class="btn btn-sm btn-outline-success"
            onclick="window.dashboardActions.updateStatus(${incident.id}, 'resolved')"
          >
            Resolve
          </button>
        </div>
      ` : ''}

      <button
        class="btn btn-outline-secondary btn-sm w-100"
        onclick="window.dashboardActions.focusOnMap(${incident.id})"
      >
        Show on Map
      </button>
    </div>
  `;

  // Show the modal using Bootstrap
  const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
  bsModal.show();
}

/**
 * Update statistics
 */
export function updateStats() {
  const stats = DashboardState.getStats();
  
  const activeEl = document.getElementById('activeCount');
  const vehicleEl = document.getElementById('vehicleCount');
  const onSceneEl = document.getElementById('onSceneCount');

  if (activeEl) activeEl.textContent = stats.active;
  if (vehicleEl) vehicleEl.textContent = stats.available;
  if (onSceneEl) onSceneEl.textContent = stats.onScene;
}

/**
 * Utility: Get time ago string
 */
function getTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

/**
 * Utility: Format date time
 */
function formatDateTime(dateStr) {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  return date.toLocaleString();
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
