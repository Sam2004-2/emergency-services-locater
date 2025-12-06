/**
 * Dashboard Map Module
 * 
 * Handles Leaflet map, markers, and routes
 */

import { DashboardState } from './dashboard-state.js';

let map;
let incidentMarkers;
let vehicleMarkers;
let routeLayer;

const SEVERITY_COLORS = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#ffc107',
  low: '#28a745'
};

const INCIDENT_ICONS = {
  fire: '🔥',
  medical: '🚑',
  crime: '🚔',
  accident: '🚗'
};

const VEHICLE_ICONS = {
  ambulance: '🚑',
  fire_engine: '🚒',
  police_car: '🚔',
  helicopter: '🚁'
};

/**
 * Initialize the map
 */
export function initMap() {
  map = L.map('map', {
    center: [53.349, -6.260], // Dublin
    zoom: 12
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);

  // Initialize marker layers
  incidentMarkers = L.layerGroup().addTo(map);
  vehicleMarkers = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);

  // Add click handler for creating incidents
  map.on('click', handleMapClick);

  return map;
}

/**
 * Render incident markers
 */
export function renderIncidents(incidents) {
  incidentMarkers.clearLayers();

  incidents.forEach(incident => {
    const props = incident.properties;
    const coords = incident.geometry.coordinates;
    const [lng, lat] = coords;

    const icon = INCIDENT_ICONS[props.incident_type] || '⚠️';
    const color = SEVERITY_COLORS[props.severity] || '#6c757d';

    const markerHtml = `
      <div style="
        background: ${color};
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        cursor: pointer;
        ${props.status === 'pending' ? 'animation: pulse 2s infinite;' : ''}
      ">
        ${icon}
      </div>
    `;

    const marker = L.marker([lat, lng], {
      icon: L.divIcon({
        html: markerHtml,
        className: 'incident-marker',
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      })
    });

    marker.bindPopup(`
      <strong>${props.title}</strong><br>
      <span class="badge bg-${getSeverityBadgeColor(props.severity)}">${props.severity_display}</span>
      <span class="badge bg-secondary">${props.status_display}</span><br>
      <small>${props.address || 'No address'}</small>
    `);

    marker.on('click', () => {
      const fullIncident = DashboardState.getIncidentById(props.id);
      DashboardState.selectIncident(fullIncident);
    });

    marker.addTo(incidentMarkers);
  });
}

/**
 * Render vehicle markers
 */
export function renderVehicles(vehicles) {
  vehicleMarkers.clearLayers();

  vehicles.forEach(vehicle => {
    const props = vehicle.properties;
    const coords = vehicle.geometry.coordinates;
    const [lng, lat] = coords;

    const icon = VEHICLE_ICONS[props.vehicle_type] || '🚗';
    const isActive = props.status !== 'available' && props.status !== 'maintenance';

    const markerHtml = `
      <div style="
        background: ${isActive ? '#0d6efd' : '#28a745'};
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        border: 2px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        cursor: pointer;
        ${props.status === 'en_route' ? 'animation: pulse 1.5s infinite;' : ''}
      ">
        ${icon}
      </div>
    `;

    const marker = L.marker([lat, lng], {
      icon: L.divIcon({
        html: markerHtml,
        className: 'vehicle-marker',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      })
    });

    marker.bindPopup(`
      <strong>${props.callsign}</strong><br>
      <span class="badge bg-info">${props.vehicle_type_display}</span>
      <span class="badge bg-${getStatusBadgeColor(props.status)}">${props.status_display}</span><br>
      <small>Speed: ${props.speed_kmh.toFixed(1)} km/h</small>
    `);

    marker.addTo(vehicleMarkers);
  });
}

/**
 * Draw route on map
 */
export function drawRoute(routeGeometry, color = '#0d6efd') {
  routeLayer.clearLayers();

  if (!routeGeometry || !routeGeometry.coordinates) return;

  const coords = routeGeometry.coordinates.map(([lng, lat]) => [lat, lng]);
  
  const polyline = L.polyline(coords, {
    color: color,
    weight: 4,
    opacity: 0.7,
    dashArray: '10, 5'
  });

  polyline.addTo(routeLayer);
  map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
}

/**
 * Clear route
 */
export function clearRoute() {
  routeLayer.clearLayers();
}

/**
 * Focus on incident
 */
export function focusIncident(incident) {
  if (!incident || !incident.geometry) return;
  
  const coords = incident.geometry.coordinates;
  const [lng, lat] = coords;
  map.setView([lat, lng], 15);
}

/**
 * Handle map click for creating incidents
 */
function handleMapClick(e) {
  const createModal = document.getElementById('createIncidentModal');
  if (createModal && createModal.classList.contains('show')) {
    document.getElementById('incidentLat').value = e.latlng.lat.toFixed(6);
    document.getElementById('incidentLng').value = e.latlng.lng.toFixed(6);
  }
}

/**
 * Get severity badge color
 */
function getSeverityBadgeColor(severity) {
  const colors = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'success'
  };
  return colors[severity] || 'secondary';
}

/**
 * Get status badge color
 */
function getStatusBadgeColor(status) {
  const colors = {
    available: 'success',
    dispatched: 'primary',
    en_route: 'info',
    on_scene: 'warning',
    returning: 'secondary',
    maintenance: 'danger'
  };
  return colors[status] || 'secondary';
}

// Add CSS animation for pulsing markers
const style = document.createElement('style');
style.textContent = `
  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.8; }
  }
`;
document.head.appendChild(style);

export { map };
