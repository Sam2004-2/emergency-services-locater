/**
 * Dashboard Main Entry Point
 * 
 * Initializes and orchestrates all dashboard modules
 */

import { DashboardAPI } from './dashboard-api.js';
import { DashboardState } from './dashboard-state.js';
import { initMap, renderIncidents, renderVehicles, focusIncident, drawRoute, clearRoute, renderActiveRoutes, drawPreviewRoute, clearPreviewRoute, toggleHeatmap, updateHeatmap } from './dashboard-map.js';
import { renderIncidentsList, renderIncidentDetail, updateStats, renderPriorityQueue } from './dashboard-list.js';
import { startPolling, stopPolling, pollNow } from './dashboard-polling.js';
import { initForms, openDispatchModal, showNotification } from './dashboard-forms.js';

/**
 * Initialize dashboard
 */
async function init() {
  console.log('Initializing dashboard...');

  try {
    // Initialize map
    initMap();

    // Initialize forms and event handlers
    initForms();

    // Load current user
    const user = await DashboardAPI.getCurrentUser();
    DashboardState.setCurrentUser(user);

    // Set up state listeners
    setupStateListeners();

    // Set up heatmap toggle
    const heatmapToggle = document.getElementById('heatmapToggle');
    if (heatmapToggle) {
      heatmapToggle.addEventListener('change', (e) => {
        toggleHeatmap(e.target.checked);
      });
    }

    // Set up mobile sidebar toggle
    setupMobileSidebar();

    // Start polling
    startPolling();

    console.log('Dashboard initialized successfully');
  } catch (error) {
    console.error('Dashboard initialization failed:', error);
    showNotification('Failed to initialize dashboard', 'danger');
  }
}

/**
 * Set up mobile sidebar toggle functionality
 */
function setupMobileSidebar() {
  const sidebar = document.getElementById('dashboardSidebar');
  const toggleBtn = document.getElementById('mobileSidebarBtn');

  if (!sidebar || !toggleBtn) return;

  // Create overlay for mobile
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
    toggleBtn.classList.add('hidden');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    toggleBtn.classList.remove('hidden');
  }

  toggleBtn.addEventListener('click', openSidebar);
  overlay.addEventListener('click', closeSidebar);

  // Close sidebar when pressing Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });
}

/**
 * Set up state change listeners
 */
function setupStateListeners() {
  // Listen for incidents changes
  DashboardState.addListener('incidents', () => {
    const filtered = DashboardState.getFilteredIncidents();
    renderIncidents(filtered);
    renderIncidentsList();
    renderPriorityQueue();
    updateStats();
    updateHeatmap(); // Refresh heatmap if enabled
  });

  // Listen for vehicles changes
  DashboardState.addListener('vehicles', () => {
    renderVehicles(DashboardState.vehicles);
    updateStats();
  });

  // Listen for active routes changes
  DashboardState.addListener('activeRoutes', () => {
    renderActiveRoutes(DashboardState.activeRoutes);
  });

  // Listen for selected incident changes
  DashboardState.addListener('selectedIncident', () => {
    renderIncidentDetail();
    renderIncidentsList(); // Re-render to update selection
    
    const incident = DashboardState.selectedIncident;
    if (incident) {
      focusIncident(incident);
      
      // Draw route if available
      if (incident.properties && incident.properties.route_geometry) {
        drawRoute(incident.properties.route_geometry);
      } else {
        clearRoute();
      }
    } else {
      clearRoute();
    }
  });

  // Listen for filter changes
  DashboardState.addListener('filters', () => {
    const filtered = DashboardState.getFilteredIncidents();
    renderIncidents(filtered);
    renderIncidentsList();
  });
}

/**
 * Preview route from vehicle to incident
 */
async function previewRoute(incidentId, vehicleId) {
  try {
    const routeData = await DashboardAPI.getRoutePreview(incidentId, vehicleId);
    drawPreviewRoute(routeData.geometry, routeData.distance_display, routeData.duration_display);
    return routeData;
  } catch (error) {
    console.error('Failed to preview route:', error);
    return null;
  }
}

/**
 * Clear route preview
 */
function cancelPreviewRoute() {
  clearPreviewRoute();
}

/**
 * Update incident status
 */
async function updateStatus(incidentId, status) {
  try {
    await DashboardAPI.updateIncidentStatus(incidentId, status);
    showNotification('Status updated successfully', 'success');
    await pollNow();
  } catch (error) {
    console.error('Failed to update status:', error);
    showNotification('Failed to update status: ' + error.message, 'danger');
  }
}

/**
 * Focus incident on map
 */
function focusOnMap(incidentId) {
  const incident = DashboardState.getIncidentById(incidentId);
  if (incident) {
    focusIncident(incident);
  }
}

/**
 * Polling manager
 */
const pollingManager = {
  start: startPolling,
  stop: stopPolling,
  pollNow: pollNow,
  setAutoRefresh(enabled) {
    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }
  }
};

// Expose functions to window for HTML onclick handlers
window.dashboardActions = {
  updateStatus,
  focusOnMap,
  openDispatchModal,
  previewRoute,
  cancelPreviewRoute
};

window.dashboardPolling = pollingManager;

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  stopPolling();
});

export { init, DashboardState, pollingManager };
