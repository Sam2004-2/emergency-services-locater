/**
 * Emergency Services Locator - Incidents Module
 * Handles incident display, filtering, and real-time updates
 */

const PRIORITY_COLORS = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#ffc107',
  low: '#28a745',
};

const STATUS_LABELS = {
  pending: 'Pending',
  dispatched: 'Dispatched',
  en_route: 'En Route',
  on_scene: 'On Scene',
  resolved: 'Resolved',
};

const INCIDENT_TYPE_ICONS = {
  medical: 'bi-heart-pulse',
  fire: 'bi-fire',
  traffic: 'bi-car-front',
  crime: 'bi-shield-exclamation',
  rescue: 'bi-life-preserver',
  hazmat: 'bi-radioactive',
  other: 'bi-exclamation-triangle',
};

class IncidentManager {
  constructor(map) {
    this.map = map;
    this.incidentLayer = L.layerGroup().addTo(map);
    this.routeLayer = L.layerGroup().addTo(map);
    this.incidents = [];
    this.markers = new Map();
    this.selectedIncident = null;
    this.currentRoute = null;
    this.filters = {
      status: '',
      priority: '',
    };
    
    // Route styling
    this.routeStyles = {
      default: { color: '#2196F3', weight: 5, opacity: 0.8 },
      emergency: { color: '#f44336', weight: 6, opacity: 0.9, dashArray: '10, 10' },
    };
    
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.loadIncidents();
    
    // Auto-refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.loadIncidents();
    }, 30000);
  }
  
  bindEvents() {
    // Filter change handlers
    const statusFilter = document.getElementById('incidentStatusFilter');
    const priorityFilter = document.getElementById('incidentPriorityFilter');
    const refreshBtn = document.getElementById('refreshIncidents');
    
    statusFilter?.addEventListener('change', (e) => {
      this.filters.status = e.target.value;
      this.applyFilters();
    });
    
    priorityFilter?.addEventListener('change', (e) => {
      this.filters.priority = e.target.value;
      this.applyFilters();
    });
    
    refreshBtn?.addEventListener('click', () => {
      this.loadIncidents();
    });
    
    // Zoom to incident button in modal
    document.getElementById('zoomToIncident')?.addEventListener('click', () => {
      if (this.selectedIncident) {
        this.zoomToIncident(this.selectedIncident);
        this.hideModal();
      }
    });
  }
  
  async loadIncidents() {
    const incidentList = document.getElementById('incidentList');
    
    try {
      // Build query params
      const params = new URLSearchParams();
      if (this.filters.status) {
        params.append('status', this.filters.status);
      } else {
        // Default to active incidents only
        params.append('status__in', 'pending,dispatched,en_route,on_scene');
      }
      if (this.filters.priority) {
        params.append('priority', this.filters.priority);
      }
      
      const response = await fetch(`/api/incidents/?${params.toString()}`);
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          incidentList.innerHTML = `
            <div class="es-info-box">
              <i class="bi bi-lock"></i>
              <div><a href="/accounts/login/">Login</a> to view incidents</div>
            </div>
          `;
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      this.incidents = data.results || data;
      
      this.renderIncidentList();
      this.renderIncidentsOnMap();
      this.updateKPIs();
      
    } catch (error) {
      console.error('Failed to load incidents:', error);
      incidentList.innerHTML = `
        <div class="es-info-box" style="color: var(--es-danger);">
          <i class="bi bi-exclamation-triangle"></i>
          <div>Failed to load incidents</div>
        </div>
      `;
    }
  }
  
  renderIncidentList() {
    const incidentList = document.getElementById('incidentList');
    const countBadge = document.getElementById('incidentCount');
    
    if (!this.incidents.length) {
      incidentList.innerHTML = `
        <div class="es-info-box">
          <i class="bi bi-check-circle"></i>
          <div>No active incidents</div>
        </div>
      `;
      if (countBadge) countBadge.textContent = '0';
      return;
    }
    
    // Sort by priority (critical first) then by created_at (newest first)
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    const sorted = [...this.incidents].sort((a, b) => {
      const pDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (pDiff !== 0) return pDiff;
      return new Date(b.created_at) - new Date(a.created_at);
    });
    
    incidentList.innerHTML = sorted.map(incident => this.renderIncidentItem(incident)).join('');
    if (countBadge) countBadge.textContent = this.incidents.length.toString();
    
    // Bind click events
    incidentList.querySelectorAll('.incident-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = item.dataset.incidentId;
        const incident = this.incidents.find(i => i.id.toString() === id);
        if (incident) {
          this.showIncidentDetails(incident);
        }
      });
    });
  }
  
  renderIncidentItem(incident) {
    const icon = INCIDENT_TYPE_ICONS[incident.incident_type] || INCIDENT_TYPE_ICONS.other;
    const timeAgo = this.formatTimeAgo(incident.created_at);
    
    return `
      <div class="incident-item priority-${incident.priority}" data-incident-id="${incident.id}">
        <div class="incident-item-header">
          <span class="incident-badge priority-${incident.priority}">
            ${incident.priority.toUpperCase()}
          </span>
          <span class="incident-badge status-${incident.status}">
            ${STATUS_LABELS[incident.status] || incident.status}
          </span>
        </div>
        <div class="incident-item-body">
          <div class="incident-item-title">
            <i class="bi ${icon}"></i>
            ${incident.title || `Incident #${incident.id}`}
          </div>
          <div class="incident-item-meta">
            <span><i class="bi bi-clock"></i> ${timeAgo}</span>
            ${incident.address ? `<span><i class="bi bi-geo-alt"></i> ${this.truncate(incident.address, 30)}</span>` : ''}
          </div>
        </div>
      </div>
    `;
  }
  
  renderIncidentsOnMap() {
    this.incidentLayer.clearLayers();
    this.markers.clear();
    
    this.incidents.forEach(incident => {
      if (incident.location) {
        const marker = this.createIncidentMarker(incident);
        this.markers.set(incident.id, marker);
        marker.addTo(this.incidentLayer);
      }
    });
  }
  
  createIncidentMarker(incident) {
    const coords = incident.location.coordinates;
    const color = PRIORITY_COLORS[incident.priority] || PRIORITY_COLORS.medium;
    const icon = INCIDENT_TYPE_ICONS[incident.incident_type] || INCIDENT_TYPE_ICONS.other;
    
    // Custom div icon with pulsing effect for critical
    const pulseClass = incident.priority === 'critical' ? 'pulse' : '';
    
    const divIcon = L.divIcon({
      html: `
        <div class="incident-marker ${pulseClass}" style="--marker-color: ${color}">
          <div class="incident-marker-inner">
            <i class="bi ${icon}"></i>
          </div>
        </div>
      `,
      className: 'incident-marker-container',
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
    
    const marker = L.marker([coords[1], coords[0]], { icon: divIcon });
    
    // Popup with incident info
    const popupContent = `
      <div class="es-popup incident-popup">
        <div class="es-popup-header">
          <span class="incident-badge priority-${incident.priority}">${incident.priority}</span>
          <strong>${incident.title || `Incident #${incident.id}`}</strong>
        </div>
        <div class="es-popup-body">
          <div class="es-popup-row">
            <i class="bi bi-info-circle"></i>
            <span>${incident.description || 'No description'}</span>
          </div>
          <div class="es-popup-row">
            <i class="bi bi-flag"></i>
            <span>Status: ${STATUS_LABELS[incident.status] || incident.status}</span>
          </div>
          ${incident.address ? `
            <div class="es-popup-row">
              <i class="bi bi-geo-alt"></i>
              <span>${incident.address}</span>
            </div>
          ` : ''}
        </div>
        <div class="es-popup-footer">
          <button class="es-btn es-btn-sm es-btn-primary" onclick="window.incidentManager?.showIncidentDetails(${incident.id})">
            View Details
          </button>
        </div>
      </div>
    `;
    
    marker.bindPopup(popupContent, {
      maxWidth: 300,
      className: 'incident-popup-container',
    });
    
    return marker;
  }
  
  showIncidentDetails(incidentOrId) {
    const incident = typeof incidentOrId === 'object' 
      ? incidentOrId 
      : this.incidents.find(i => i.id === incidentOrId);
    
    if (!incident) return;
    
    this.selectedIncident = incident;
    const modal = document.getElementById('incidentModal');
    const body = document.getElementById('incidentModalBody');
    
    if (!modal || !body) return;
    
    body.innerHTML = `
      <div class="incident-detail">
        <div class="incident-detail-header">
          <span class="incident-badge priority-${incident.priority}">${incident.priority.toUpperCase()}</span>
          <span class="incident-badge status-${incident.status}">${STATUS_LABELS[incident.status]}</span>
        </div>
        
        <h4>${incident.title || `Incident #${incident.id}`}</h4>
        
        <div class="incident-detail-section">
          <label>Description</label>
          <p>${incident.description || 'No description provided'}</p>
        </div>
        
        <div class="incident-detail-section">
          <label>Type</label>
          <p><i class="bi ${INCIDENT_TYPE_ICONS[incident.incident_type] || 'bi-question'}"></i> ${incident.incident_type || 'Unknown'}</p>
        </div>
        
        ${incident.address ? `
          <div class="incident-detail-section">
            <label>Location</label>
            <p><i class="bi bi-geo-alt"></i> ${incident.address}</p>
          </div>
        ` : ''}
        
        <div class="incident-detail-section">
          <label>Reported</label>
          <p><i class="bi bi-clock"></i> ${new Date(incident.created_at).toLocaleString()}</p>
        </div>
        
        ${incident.reporter_name ? `
          <div class="incident-detail-section">
            <label>Reporter</label>
            <p><i class="bi bi-person"></i> ${incident.reporter_name}</p>
          </div>
        ` : ''}
        
        ${incident.reporter_phone ? `
          <div class="incident-detail-section">
            <label>Contact</label>
            <p><i class="bi bi-telephone"></i> <a href="tel:${incident.reporter_phone}">${incident.reporter_phone}</a></p>
          </div>
        ` : ''}
        
        ${incident.notes ? `
          <div class="incident-detail-section">
            <label>Notes</label>
            <p>${incident.notes}</p>
          </div>
        ` : ''}
        
        <hr style="border-color: var(--es-border, #e0e0e0); margin: 16px 0;">
        
        <div class="incident-detail-section">
          <label>Routing & Response</label>
          <div class="incident-action-buttons">
            <button class="es-btn es-btn-primary" id="showRouteBtn">
              <i class="bi bi-signpost-split"></i> Show Route
            </button>
            <button class="es-btn es-btn-secondary" id="findVehiclesBtn">
              <i class="bi bi-truck"></i> Find Vehicles
            </button>
          </div>
          <div id="nearbyVehiclesList" class="nearby-vehicles-list"></div>
        </div>
      </div>
    `;
    
    // Bind routing button events
    document.getElementById('showRouteBtn')?.addEventListener('click', () => {
      this.showRouteToIncident(incident);
      this.hideModal();
    });
    
    document.getElementById('findVehiclesBtn')?.addEventListener('click', async () => {
      await this.loadNearbyVehicles(incident.id);
    });
    
    modal.classList.add('active');
  }
  
  /**
   * Load and display nearby vehicles for an incident
   */
  async loadNearbyVehicles(incidentId) {
    const listEl = document.getElementById('nearbyVehiclesList');
    if (!listEl) return;
    
    listEl.innerHTML = '<div class="loading-spinner"><i class="bi bi-hourglass-split"></i> Finding vehicles...</div>';
    
    const data = await this.findNearbyVehicles(incidentId);
    
    if (!data || !data.available_vehicles || data.available_vehicles.length === 0) {
      listEl.innerHTML = '<p class="text-muted">No available vehicles found nearby</p>';
      return;
    }
    
    listEl.innerHTML = data.available_vehicles.map(v => `
      <div class="nearby-vehicle-item" data-vehicle-id="${v.vehicle_id}">
        <div class="vehicle-info">
          <strong>${v.call_sign}</strong>
          <span class="vehicle-type">${v.vehicle_type}</span>
        </div>
        <div class="vehicle-eta">
          <span class="eta-distance">${(v.distance_m / 1000).toFixed(1)} km</span>
          <span class="eta-time">${Math.ceil(v.eta_minutes)} min</span>
        </div>
        <button class="es-btn es-btn-sm es-btn-secondary show-vehicle-route" data-vehicle-id="${v.vehicle_id}">
          <i class="bi bi-signpost"></i>
        </button>
      </div>
    `).join('');
    
    // Bind show route buttons
    listEl.querySelectorAll('.show-vehicle-route').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const vehicleId = e.currentTarget.dataset.vehicleId;
        this.showVehicleRoute(parseInt(vehicleId), incidentId);
        this.hideModal();
      });
    });
  }
  
  hideModal() {
    const modal = document.getElementById('incidentModal');
    modal?.classList.remove('active');
    this.selectedIncident = null;
  }
  
  zoomToIncident(incident) {
    if (incident.location) {
      const coords = incident.location.coordinates;
      this.map.setView([coords[1], coords[0]], 15);
      
      // Open the popup
      const marker = this.markers.get(incident.id);
      if (marker) {
        marker.openPopup();
      }
    }
  }
  
  applyFilters() {
    this.loadIncidents();
  }
  
  updateKPIs() {
    const incidentsKpi = document.getElementById('kpiIncidents');
    const vehiclesKpi = document.getElementById('kpiVehicles');
    
    if (incidentsKpi) {
      const activeCount = this.incidents.filter(i => 
        ['pending', 'dispatched', 'en_route', 'on_scene'].includes(i.status)
      ).length;
      incidentsKpi.textContent = activeCount.toString();
    }
    
    // Load vehicle count
    this.loadVehicleCount();
  }
  
  async loadVehicleCount() {
    try {
      const response = await fetch('/api/vehicles/?status=available');
      if (response.ok) {
        const data = await response.json();
        const count = (data.results || data).length;
        const vehiclesKpi = document.getElementById('kpiVehicles');
        if (vehiclesKpi) {
          vehiclesKpi.textContent = count.toString();
        }
      }
    } catch (error) {
      console.error('Failed to load vehicle count:', error);
    }
  }
  
  formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  }
  
  truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
  }
  
  // ============================================
  // Routing Methods
  // ============================================
  
  /**
   * Calculate route between two points using the server API
   */
  async calculateRoute(origin, destination) {
    try {
      const response = await fetch('/api/routing/calculate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
        body: JSON.stringify({
          origin: { latitude: origin.lat, longitude: origin.lng },
          destination: { latitude: destination.lat, longitude: destination.lng },
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Route calculation failed: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error calculating route:', error);
      // Fallback to OSRM public server
      return this.calculateRouteOSRM(origin, destination);
    }
  }
  
  /**
   * Calculate route using public OSRM server (fallback)
   */
  async calculateRouteOSRM(origin, destination) {
    const coords = `${origin.lng},${origin.lat};${destination.lng},${destination.lat}`;
    const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson&steps=true`;
    
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`OSRM request failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
        throw new Error('No route found');
      }
      
      const route = data.routes[0];
      return {
        distance_m: route.distance,
        duration_s: route.duration,
        geometry: route.geometry,
        instructions: route.legs?.[0]?.steps?.map(s => ({
          instruction: s.maneuver?.instruction || '',
          distance_m: s.distance,
          duration_s: s.duration,
          name: s.name,
        })) || [],
      };
    } catch (error) {
      console.error('OSRM route calculation failed:', error);
      return null;
    }
  }
  
  /**
   * Display a route on the map
   */
  displayRoute(routeData, options = {}) {
    this.clearRoute();
    
    if (!routeData || !routeData.geometry) {
      console.error('Invalid route data');
      return null;
    }
    
    const style = options.style || 'emergency';
    const routeStyle = this.routeStyles[style] || this.routeStyles.emergency;
    
    // Create route line
    const routeLine = L.geoJSON(routeData.geometry, {
      style: () => routeStyle,
    }).addTo(this.routeLayer);
    
    this.currentRoute = {
      data: routeData,
      layer: routeLine,
    };
    
    // Fit map to route bounds
    if (options.fitBounds !== false) {
      this.map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
    }
    
    // Show route info popup
    if (options.showInfo !== false) {
      this.showRouteInfo(routeData);
    }
    
    return routeLine;
  }
  
  /**
   * Clear current route from map
   */
  clearRoute() {
    this.routeLayer.clearLayers();
    this.currentRoute = null;
    this.hideRouteInfo();
  }
  
  /**
   * Show route info panel
   */
  showRouteInfo(routeData) {
    const distance = (routeData.distance_m / 1000).toFixed(1);
    const duration = Math.ceil(routeData.duration_s / 60);
    
    // Create or update route info element
    let infoEl = document.getElementById('routeInfo');
    if (!infoEl) {
      infoEl = document.createElement('div');
      infoEl.id = 'routeInfo';
      infoEl.className = 'route-info-panel';
      document.querySelector('.es-map-panel')?.appendChild(infoEl);
    }
    
    infoEl.innerHTML = `
      <div class="route-info-header">
        <i class="bi bi-signpost-split"></i>
        <span>Route to Incident</span>
        <button class="route-info-close" onclick="window.incidentManager?.clearRoute()">
          <i class="bi bi-x"></i>
        </button>
      </div>
      <div class="route-info-body">
        <div class="route-stat">
          <i class="bi bi-speedometer2"></i>
          <span>${distance} km</span>
        </div>
        <div class="route-stat">
          <i class="bi bi-clock"></i>
          <span>${duration} min</span>
        </div>
      </div>
    `;
    
    infoEl.classList.add('active');
  }
  
  /**
   * Hide route info panel
   */
  hideRouteInfo() {
    const infoEl = document.getElementById('routeInfo');
    if (infoEl) {
      infoEl.classList.remove('active');
    }
  }
  
  /**
   * Show route from user's current location to an incident
   */
  async showRouteToIncident(incident) {
    if (!incident || !incident.location) {
      console.error('Invalid incident or missing location');
      return;
    }
    
    const incidentCoords = incident.location.coordinates;
    const destination = { lat: incidentCoords[1], lng: incidentCoords[0] };
    
    // Try to get user's location
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
        });
      });
      
      const origin = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      
      // Calculate and display route
      const routeData = await this.calculateRoute(origin, destination);
      
      if (routeData) {
        this.displayRoute(routeData, { style: 'emergency' });
        
        // Add origin marker
        const originMarker = L.marker([origin.lat, origin.lng], {
          icon: L.divIcon({
            className: 'route-origin-marker',
            html: '<div class="route-marker origin"><i class="bi bi-geo-alt-fill"></i></div>',
            iconSize: [30, 30],
            iconAnchor: [15, 30],
          }),
        }).addTo(this.routeLayer);
        
        originMarker.bindPopup('Your Location');
      } else {
        alert('Could not calculate route');
      }
    } catch (error) {
      console.error('Geolocation error:', error);
      alert('Could not get your location. Please enable location services.');
    }
  }
  
  /**
   * Show route from a vehicle to an incident
   */
  async showVehicleRoute(vehicleId, incidentId) {
    try {
      // Get vehicle data
      const vehicleResponse = await fetch(`/api/vehicles/${vehicleId}/`);
      if (!vehicleResponse.ok) throw new Error('Vehicle not found');
      const vehicle = await vehicleResponse.json();
      
      if (!vehicle.current_location) {
        alert('Vehicle location not available');
        return;
      }
      
      // Get incident data
      const incident = this.incidents.find(i => i.id === incidentId) ||
        await this.fetchIncident(incidentId);
      
      if (!incident || !incident.location) {
        alert('Incident location not available');
        return;
      }
      
      const vehicleCoords = vehicle.current_location.coordinates;
      const incidentCoords = incident.location.coordinates;
      
      const origin = { lat: vehicleCoords[1], lng: vehicleCoords[0] };
      const destination = { lat: incidentCoords[1], lng: incidentCoords[0] };
      
      const routeData = await this.calculateRoute(origin, destination);
      
      if (routeData) {
        this.displayRoute(routeData, { style: 'emergency' });
        
        // Add vehicle marker
        const vehicleMarker = L.marker([origin.lat, origin.lng], {
          icon: L.divIcon({
            className: 'route-vehicle-marker',
            html: `<div class="route-marker vehicle"><i class="bi bi-truck"></i></div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15],
          }),
        }).addTo(this.routeLayer);
        
        vehicleMarker.bindPopup(`${vehicle.call_sign}`);
      }
    } catch (error) {
      console.error('Error showing vehicle route:', error);
      alert('Could not calculate route');
    }
  }
  
  /**
   * Fetch a single incident by ID
   */
  async fetchIncident(incidentId) {
    try {
      const response = await fetch(`/api/incidents/${incidentId}/`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Error fetching incident:', error);
    }
    return null;
  }
  
  /**
   * Find nearby vehicles for an incident
   */
  async findNearbyVehicles(incidentId) {
    try {
      const response = await fetch(`/api/incidents/${incidentId}/nearby-vehicles/`);
      if (!response.ok) {
        throw new Error(`Failed to find vehicles: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error finding nearby vehicles:', error);
      return null;
    }
  }
  
  /**
   * Get CSRF token for API requests
   */
  getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    this.incidentLayer.clearLayers();
    this.routeLayer.clearLayers();
  }
}

// Export for use in map.js
export { IncidentManager, PRIORITY_COLORS, STATUS_LABELS };
