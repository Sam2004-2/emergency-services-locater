/**
 * Dashboard Forms Module
 * 
 * Handles create incident and dispatch modals
 */

import { DashboardAPI } from './dashboard-api.js';
import { DashboardState } from './dashboard-state.js';
import { pollNow } from './dashboard-polling.js';

/**
 * Initialize form handlers
 */
export function initForms() {
  // Create incident button
  const createBtn = document.getElementById('createIncidentBtn');
  if (createBtn) {
    createBtn.addEventListener('click', showCreateIncidentModal);
  }

  // Submit incident
  const submitBtn = document.getElementById('submitIncident');
  if (submitBtn) {
    submitBtn.addEventListener('click', handleCreateIncident);
  }

  // Submit dispatch
  const submitDispatchBtn = document.getElementById('submitDispatch');
  if (submitDispatchBtn) {
    submitDispatchBtn.addEventListener('click', handleDispatch);
  }

  // Filter handlers
  const filterStatus = document.getElementById('filterStatus');
  const filterSeverity = document.getElementById('filterSeverity');
  const filterType = document.getElementById('filterType');

  if (filterStatus) {
    filterStatus.addEventListener('change', (e) => {
      DashboardState.setFilters({ status: e.target.value });
    });
  }

  if (filterSeverity) {
    filterSeverity.addEventListener('change', (e) => {
      DashboardState.setFilters({ severity: e.target.value });
    });
  }

  if (filterType) {
    filterType.addEventListener('change', (e) => {
      DashboardState.setFilters({ type: e.target.value });
    });
  }

  // Auto-refresh toggle
  const autoRefresh = document.getElementById('autoRefresh');
  if (autoRefresh) {
    autoRefresh.addEventListener('change', (e) => {
      window.dashboardPolling.setAutoRefresh(e.target.checked);
    });
  }
}

/**
 * Show create incident modal
 */
function showCreateIncidentModal() {
  const modal = new bootstrap.Modal(document.getElementById('createIncidentModal'));
  
  // Reset form
  document.getElementById('createIncidentForm').reset();
  
  // Set default coordinates (Dublin center)
  document.getElementById('incidentLat').value = '53.349';
  document.getElementById('incidentLng').value = '-6.260';
  
  modal.show();
}

/**
 * Handle create incident submission
 */
async function handleCreateIncident() {
  const submitBtn = document.getElementById('submitIncident');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Creating...';

  try {
    const data = {
      title: document.getElementById('incidentTitle').value,
      description: document.getElementById('incidentDescription').value,
      incident_type: document.getElementById('incidentType').value,
      severity: document.getElementById('incidentSeverity').value,
      address: document.getElementById('incidentAddress').value,
      location: {
        type: 'Point',
        coordinates: [
          parseFloat(document.getElementById('incidentLng').value),
          parseFloat(document.getElementById('incidentLat').value)
        ]
      }
    };

    await DashboardAPI.createIncident(data);

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('createIncidentModal'));
    modal.hide();

    // Show success message
    showNotification('Incident created successfully', 'success');

    // Refresh data
    await pollNow();

  } catch (error) {
    console.error('Failed to create incident:', error);
    showNotification('Failed to create incident: ' + error.message, 'danger');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Create Incident';
  }
}

/**
 * Open dispatch modal for incident
 */
export async function openDispatchModal(incidentId) {
  const incident = DashboardState.getIncidentById(incidentId);
  if (!incident) return;

  const modal = new bootstrap.Modal(document.getElementById('dispatchModal'));
  
  // Update incident info
  const infoEl = document.getElementById('dispatchIncidentInfo');
  if (infoEl) {
    infoEl.innerHTML = `
      <strong>Incident:</strong> ${incident.properties.title}<br>
      <span class="badge bg-${getSeverityBadge(incident.properties.severity)}">${incident.properties.severity_display}</span>
    `;
  }

  // Clear route preview info
  const routePreviewEl = document.getElementById('routePreviewInfo');
  if (routePreviewEl) {
    routePreviewEl.innerHTML = '';
  }

  // Load available vehicles
  try {
    const vehicleSelect = document.getElementById('dispatchVehicle');
    vehicleSelect.innerHTML = '<option value="">Loading vehicles...</option>';

    const vehicles = await DashboardAPI.getAvailableVehicles();
    
    if (vehicles.features && vehicles.features.length > 0) {
      vehicleSelect.innerHTML = '<option value="">Select a vehicle</option>' +
        vehicles.features.map(v => 
          `<option value="${v.id}">${v.properties.callsign} - ${v.properties.vehicle_type_display}</option>`
        ).join('');
      
      // Add change handler for route preview
      vehicleSelect.onchange = async function() {
        await previewRouteForVehicle(incidentId, this.value);
      };
    } else {
      vehicleSelect.innerHTML = '<option value="">No vehicles available</option>';
    }

    // Store incident ID on modal
    modal._incidentId = incidentId;
    
    // Clean up preview on modal close
    document.getElementById('dispatchModal').addEventListener('hidden.bs.modal', () => {
      if (window.dashboardActions && window.dashboardActions.cancelPreviewRoute) {
        window.dashboardActions.cancelPreviewRoute();
      }
    }, { once: true });
    
    modal.show();
  } catch (error) {
    console.error('Failed to load vehicles:', error);
    showNotification('Failed to load vehicles', 'danger');
  }
}

/**
 * Preview route for selected vehicle
 */
async function previewRouteForVehicle(incidentId, vehicleId) {
  const routePreviewEl = document.getElementById('routePreviewInfo');
  
  if (!vehicleId) {
    if (routePreviewEl) routePreviewEl.innerHTML = '';
    if (window.dashboardActions && window.dashboardActions.cancelPreviewRoute) {
      window.dashboardActions.cancelPreviewRoute();
    }
    return;
  }
  
  if (routePreviewEl) {
    routePreviewEl.innerHTML = '<div class="text-muted small"><i class="bi bi-hourglass-split"></i> Calculating route...</div>';
  }
  
  try {
    const routeData = await DashboardAPI.getRoutePreview(incidentId, vehicleId);
    
    if (routePreviewEl) {
      routePreviewEl.innerHTML = `
        <div class="alert alert-info py-2 mb-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong><i class="bi bi-signpost-2"></i> Route Preview</strong>
            </div>
            <div class="text-end">
              <span class="badge bg-primary">${routeData.distance_display}</span>
              <span class="badge bg-success"><i class="bi bi-clock"></i> ${routeData.duration_display}</span>
            </div>
          </div>
        </div>
      `;
    }
    
    // Draw preview on map
    if (window.dashboardActions && window.dashboardActions.previewRoute) {
      window.dashboardActions.previewRoute(incidentId, vehicleId);
    }
    
  } catch (error) {
    console.error('Failed to get route preview:', error);
    if (routePreviewEl) {
      routePreviewEl.innerHTML = '<div class="text-warning small"><i class="bi bi-exclamation-triangle"></i> Could not calculate route</div>';
    }
  }
}

/**
 * Handle dispatch submission
 */
async function handleDispatch() {
  const submitBtn = document.getElementById('submitDispatch');
  const modal = bootstrap.Modal.getInstance(document.getElementById('dispatchModal'));
  const incidentId = modal._incidentId;

  if (!incidentId) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Dispatching...';

  try {
    const vehicleId = document.getElementById('dispatchVehicle').value;
    const responderId = document.getElementById('dispatchResponder').value || null;

    if (!vehicleId) {
      throw new Error('Please select a vehicle');
    }

    await DashboardAPI.dispatchIncident(incidentId, vehicleId, responderId);

    // Close modal
    modal.hide();

    // Show success message
    showNotification('Vehicle dispatched successfully', 'success');

    // Refresh data
    await pollNow();

  } catch (error) {
    console.error('Failed to dispatch:', error);
    showNotification('Failed to dispatch: ' + error.message, 'danger');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Dispatch';
  }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
  // Create toast element
  const toastHtml = `
    <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  // Get or create toast container
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }

  // Add toast
  const div = document.createElement('div');
  div.innerHTML = toastHtml;
  const toastEl = div.firstElementChild;
  container.appendChild(toastEl);

  // Show toast
  const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
  toast.show();

  // Remove from DOM after hidden
  toastEl.addEventListener('hidden.bs.toast', () => {
    toastEl.remove();
  });
}

/**
 * Get severity badge class
 */
function getSeverityBadge(severity) {
  const badges = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'success'
  };
  return badges[severity] || 'secondary';
}

// Export functions for global access
export { showNotification };
