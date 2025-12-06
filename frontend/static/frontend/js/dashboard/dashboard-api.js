/**
 * Dashboard API Client
 * 
 * Handles all API requests for incidents, vehicles, and dispatches
 */

const API_BASE = '/api';

// Get CSRF token from meta tag
function getCSRFToken() {
  return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

export const DashboardAPI = {
  /**
   * Fetch all active incidents
   */
  async getActiveIncidents() {
    const response = await fetch(`${API_BASE}/incidents/active/`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch incidents');
    return response.json();
  },

  /**
   * Fetch incidents with filters
   */
  async getIncidents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.incident_type) params.append('incident_type', filters.incident_type);
    
    const response = await fetch(`${API_BASE}/incidents/?${params}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch incidents');
    return response.json();
  },

  /**
   * Fetch single incident
   */
  async getIncident(id) {
    const response = await fetch(`${API_BASE}/incidents/${id}/`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch incident');
    return response.json();
  },

  /**
   * Create new incident
   */
  async createIncident(data) {
    const response = await fetch(`${API_BASE}/incidents/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create incident');
    }
    return response.json();
  },

  /**
   * Update incident status
   */
  async updateIncidentStatus(id, status) {
    const response = await fetch(`${API_BASE}/incidents/${id}/update_status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ status })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update status');
    }
    return response.json();
  },

  /**
   * Dispatch vehicle to incident
   */
  async dispatchIncident(incidentId, vehicleId, responderId = null) {
    const data = { vehicle_id: vehicleId };
    if (responderId) data.responder_id = responderId;

    const response = await fetch(`${API_BASE}/incidents/${incidentId}/dispatch/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to dispatch');
    }
    return response.json();
  },

  /**
   * Get route to incident
   */
  async getRoute(incidentId, fromLat, fromLng) {
    const params = new URLSearchParams({ from_lat: fromLat, from_lng: fromLng });
    const response = await fetch(`${API_BASE}/incidents/${incidentId}/route/?${params}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to get route');
    return response.json();
  },

  /**
   * Fetch all vehicles
   */
  async getVehicles(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.vehicle_type) params.append('vehicle_type', filters.vehicle_type);
    
    const response = await fetch(`${API_BASE}/vehicles/?${params}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch vehicles');
    return response.json();
  },

  /**
   * Fetch available vehicles
   */
  async getAvailableVehicles(type = null) {
    const params = type ? `?type=${type}` : '';
    const response = await fetch(`${API_BASE}/vehicles/available/${params}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch vehicles');
    return response.json();
  },

  /**
   * Fetch dispatch records
   */
  async getDispatches(filters = {}) {
    const params = new URLSearchParams();
    if (filters.incident) params.append('incident', filters.incident);
    if (filters.vehicle) params.append('vehicle', filters.vehicle);
    
    const response = await fetch(`${API_BASE}/dispatches/?${params}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch dispatches');
    return response.json();
  },

  /**
   * Acknowledge dispatch
   */
  async acknowledgeDispatch(dispatchId) {
    const response = await fetch(`${API_BASE}/dispatches/${dispatchId}/acknowledge/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to acknowledge');
    }
    return response.json();
  },

  /**
   * Get current user info
   */
  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/auth/me/`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    if (!response.ok) throw new Error('Failed to fetch user');
    return response.json();
  }
};
