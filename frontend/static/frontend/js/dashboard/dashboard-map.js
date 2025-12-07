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
let activeRoutesLayer;
let previewRouteLayer;
let heatLayer = null;
let heatmapEnabled = false;

const SEVERITY_COLORS = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#ffc107',
  low: '#28a745'
};

// SVG icons for incidents (clean, professional look)
const INCIDENT_ICONS = {
  fire: '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 23c-3.9 0-7-3.1-7-7 0-2.1.9-4.5 2.6-7.2.4-.6.8-1.2 1.3-1.8l.5-.6c.3-.4.7-.4 1 0l.5.6c.4.5.7.9 1 1.4.3-.5.6-1.1 1-1.6l.4-.5c.3-.4.7-.4 1 0l.4.5c.4.5.8 1.1 1.1 1.6.5-.8 1-1.5 1.4-2.1.3-.4.7-.4 1 0C18.1 8.5 19 11.1 19 13.5c0 4.7-3.1 9.5-7 9.5zm0-15.5c-.5.8-1 1.5-1.4 2.2-.3.4-.7.4-1 0-.4-.5-.7-1-1-1.4-.3.4-.6.9-.9 1.3C6.6 11.3 6 13 6 14.5 6 17.5 8.7 21 12 21s6-3.5 6-6.5c0-1.5-.6-3.2-1.7-5-.3-.4-.6-.9-.9-1.3-.3.4-.6.8-.9 1.2-.3.4-.7.4-1 0-.4-.6-.9-1.3-1.5-2.1z"/></svg>',
  medical: '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>',
  crime: '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>',
  accident: '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>',
  traffic: '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>'
};

// SVG icons for vehicles
const VEHICLE_ICONS = {
  ambulance: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>',
  fire_engine: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>',
  fire: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>',
  police_car: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>',
  garda: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>',
  helicopter: '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>'
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
  activeRoutesLayer = L.layerGroup().addTo(map);
  previewRouteLayer = L.layerGroup().addTo(map);

  // Add click handler for creating incidents
  map.on('click', handleMapClick);

  return map;
}

// Default fallback icon (warning triangle)
const DEFAULT_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>';
const DEFAULT_VEHICLE_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>';

/**
 * Render incident markers
 */
export function renderIncidents(incidents) {
  incidentMarkers.clearLayers();

  incidents.forEach(incident => {
    const props = incident.properties;
    const coords = incident.geometry.coordinates;
    const [lng, lat] = coords;

    const icon = INCIDENT_ICONS[props.incident_type] || DEFAULT_ICON;
    const color = SEVERITY_COLORS[props.severity] || '#6c757d';

    const markerHtml = `
      <div class="incident-marker-icon" style="
        background: ${color};
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
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

    const icon = VEHICLE_ICONS[props.vehicle_type] || DEFAULT_VEHICLE_ICON;
    const isActive = props.status !== 'available' && props.status !== 'maintenance';

    const markerHtml = `
      <div class="vehicle-marker-icon" style="
        background: ${isActive ? '#0d6efd' : '#28a745'};
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
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
 * Draw route on map (for selected incident)
 */
export function drawRoute(routeGeometry, color = '#0d6efd') {
  routeLayer.clearLayers();

  if (!routeGeometry || !routeGeometry.coordinates) return;

  const coords = routeGeometry.coordinates.map(([lng, lat]) => [lat, lng]);
  
  const polyline = L.polyline(coords, {
    color: color,
    weight: 5,
    opacity: 0.8,
    lineCap: 'round',
    lineJoin: 'round'
  });

  // Add animated dash effect for active routes
  const animatedPolyline = L.polyline(coords, {
    color: 'white',
    weight: 5,
    opacity: 0.4,
    dashArray: '10, 20',
    lineCap: 'round',
    lineJoin: 'round'
  });

  animatedPolyline.addTo(routeLayer);
  polyline.addTo(routeLayer);
  
  // Add start/end markers
  if (coords.length >= 2) {
    const startPoint = coords[0];
    const endPoint = coords[coords.length - 1];
    
    // Vehicle start marker
    L.circleMarker(startPoint, {
      radius: 8,
      fillColor: '#28a745',
      color: 'white',
      weight: 2,
      fillOpacity: 1
    }).bindPopup('Vehicle Location').addTo(routeLayer);
    
    // Incident end marker
    L.circleMarker(endPoint, {
      radius: 8,
      fillColor: color,
      color: 'white',
      weight: 2,
      fillOpacity: 1
    }).bindPopup('Incident Location').addTo(routeLayer);
  }

  map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
}

/**
 * Clear route
 */
export function clearRoute() {
  routeLayer.clearLayers();
}

/**
 * Draw preview route (when hovering/selecting vehicle for dispatch)
 */
export function drawPreviewRoute(routeGeometry, distanceDisplay, durationDisplay) {
  previewRouteLayer.clearLayers();

  if (!routeGeometry || !routeGeometry.coordinates) return;

  const coords = routeGeometry.coordinates.map(([lng, lat]) => [lat, lng]);
  
  const polyline = L.polyline(coords, {
    color: '#6c757d',
    weight: 4,
    opacity: 0.6,
    dashArray: '5, 10'
  });

  polyline.addTo(previewRouteLayer);
  
  // Add info popup at midpoint
  if (coords.length >= 2) {
    const midIndex = Math.floor(coords.length / 2);
    const midPoint = coords[midIndex];
    
    L.popup()
      .setLatLng(midPoint)
      .setContent(`
        <div class="text-center">
          <strong>Route Preview</strong><br>
          <span class="text-muted">Distance:</span> ${distanceDisplay}<br>
          <span class="text-muted">ETA:</span> ${durationDisplay}
        </div>
      `)
      .openOn(map);
  }

  map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
}

/**
 * Clear preview route
 */
export function clearPreviewRoute() {
  previewRouteLayer.clearLayers();
  map.closePopup();
}

/**
 * Render all active routes (vehicles en route to incidents)
 */
export function renderActiveRoutes(routes) {
  activeRoutesLayer.clearLayers();

  routes.forEach(route => {
    if (!route.route_geometry || !route.route_geometry.coordinates) return;

    const coords = route.route_geometry.coordinates.map(([lng, lat]) => [lat, lng]);
    const color = SEVERITY_COLORS[route.severity] || '#0d6efd';
    
    // Main route line
    const polyline = L.polyline(coords, {
      color: color,
      weight: 4,
      opacity: 0.7,
      lineCap: 'round',
      lineJoin: 'round'
    });

    // Format duration
    const durationMin = Math.round((route.route_duration_s || 0) / 60);
    const distanceKm = ((route.route_distance_m || 0) / 1000).toFixed(1);

    polyline.bindPopup(`
      <strong>${route.incident_title}</strong><br>
      <span class="badge bg-${getSeverityBadgeColor(route.severity)}">${route.severity}</span>
      <span class="badge bg-info">${route.status}</span><br>
      <small>Distance: ${distanceKm} km | ETA: ${durationMin} min</small>
    `);

    polyline.addTo(activeRoutesLayer);
  });
}

/**
 * Clear active routes
 */
export function clearActiveRoutes() {
  activeRoutesLayer.clearLayers();
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

/**
 * Toggle heatmap layer visibility
 * Shows incident density with severity-based intensity
 */
export function toggleHeatmap(enabled) {
  heatmapEnabled = enabled;

  if (!enabled) {
    // Remove heatmap layer if it exists
    if (heatLayer && map.hasLayer(heatLayer)) {
      map.removeLayer(heatLayer);
    }
    heatLayer = null;
    return;
  }

  // Get all incidents from state
  const incidents = DashboardState.incidents || [];

  if (incidents.length === 0) {
    return;
  }

  // Build heatmap data points with severity-based intensity
  const heatData = incidents.map(incident => {
    const coords = incident.geometry.coordinates;
    const [lng, lat] = coords;
    const severity = incident.properties.severity;

    // Intensity based on severity (0.0 to 1.0)
    const intensityMap = {
      critical: 1.0,
      high: 0.75,
      medium: 0.5,
      low: 0.25
    };
    const intensity = intensityMap[severity] || 0.5;

    return [lat, lng, intensity];
  });

  // Remove existing heatmap if any
  if (heatLayer && map.hasLayer(heatLayer)) {
    map.removeLayer(heatLayer);
  }

  // Create new heatmap layer
  heatLayer = L.heatLayer(heatData, {
    radius: 30,
    blur: 20,
    maxZoom: 15,
    max: 1.0,
    gradient: {
      0.2: '#28a745',  // low - green
      0.4: '#ffc107',  // medium - yellow
      0.6: '#fd7e14',  // high - orange
      0.8: '#dc3545',  // critical - red
      1.0: '#7b0000'   // very hot - dark red
    }
  }).addTo(map);
}

/**
 * Update heatmap when incidents change (if enabled)
 */
export function updateHeatmap() {
  if (heatmapEnabled) {
    toggleHeatmap(true);
  }
}

export { map };
