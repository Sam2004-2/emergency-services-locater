import API from './api.js';
import { icons, getIconForType } from './icons.js';
import { IncidentManager } from './incidents.js';

/**
 * Emergency Services Locator - Map Module
 * Enterprise Edition
 */

const state = {
  map: null,
  cluster: null,
  countyLayer: null,
  selectedCounty: null,
  userLatLng: null,
  userMarker: null,
  radiusOverlay: null,
  performanceMarks: {},
  incidentManager: null,
};

// Performance instrumentation
const perf = {
  mark: (name) => {
    state.performanceMarks[name] = performance.now();
    performance.mark(name);
  },
  measure: (name, startMark) => {
    const duration = performance.now() - (state.performanceMarks[startMark] || 0);
    console.log(`[Perf] ${name}: ${duration.toFixed(2)}ms`);
    return duration;
  },
};

const $ = (selector) => document.querySelector(selector);

// Status management
const status = (message, loading = false) => {
  const statusMsg = $('#statusMsg span:last-child');
  const statusText = $('#statusText');
  const indicator = $('#statusIndicator');
  
  if (statusMsg) statusMsg.textContent = message;
  if (statusText) statusText.textContent = message;
  if (indicator) {
    indicator.classList.toggle('loading', loading);
  }
};

const kmToM = (km) => Math.round(Number(km) * 1000);

// Icon mapping for popups
const typeIcons = {
  hospital: 'bi-hospital',
  fire_station: 'bi-fire',
  police_station: 'bi-shield-shaded',
  ambulance_base: 'bi-truck',
};

const typeLabels = {
  hospital: 'Hospital',
  fire_station: 'Fire Station',
  police_station: 'Garda / Police',
  ambulance_base: 'Ambulance Base',
};

function popupHtml(feature) {
  const props = feature.properties || {};
  const meta = props.properties || {};
  const type = props.type || 'default';
  const icon = typeIcons[type] || 'bi-geo-alt';
  const label = typeLabels[type] || type.replace('_', ' ');
  
  let rows = '';
  
  if (props.address) {
    rows += `
      <div class="es-popup-row">
        <i class="bi bi-geo-alt"></i>
        <span>${props.address}</span>
      </div>
    `;
  }
  
  if (props.phone) {
    rows += `
      <div class="es-popup-row">
        <i class="bi bi-telephone"></i>
        <a href="tel:${props.phone}">${props.phone}</a>
      </div>
    `;
  }
  
  if (props.website) {
    rows += `
      <div class="es-popup-row">
        <i class="bi bi-globe"></i>
        <a href="${props.website}" target="_blank" rel="noopener">Visit Website</a>
      </div>
    `;
  }
  
  const badge = meta.ae ? '<div class="es-popup-badge"><i class="bi bi-check-circle-fill"></i> A&E Department</div>' : '';
  
  return `
    <div class="es-popup">
      <div class="es-popup-header">
        <div class="es-popup-icon ${type}">
          <i class="bi ${icon}"></i>
        </div>
        <div style="flex: 1;">
          <div class="es-popup-title">${props.name || 'Unknown Facility'}</div>
          <div class="es-popup-type">${label}</div>
        </div>
      </div>
      <div class="es-popup-body">
        ${rows}
        ${badge}
      </div>
    </div>
  `;
}

function featureToMarker(feature, latlng) {
  const type = feature.properties?.type || 'default';
  const icon = getIconForType(type);
  return L.marker(latlng, { icon }).bindPopup(popupHtml(feature));
}

function unwrapCollection(data) {
  if (!data) {
    return { type: 'FeatureCollection', features: [] };
  }
  if (data.type === 'FeatureCollection') {
    return data;
  }
  if (Array.isArray(data.features)) {
    return { type: 'FeatureCollection', features: data.features };
  }
  if (data.results && data.results.type === 'FeatureCollection') {
    return data.results;
  }
  return { type: 'FeatureCollection', features: [] };
}

function clearMarkers() {
  if (state.cluster) {
    state.map.removeLayer(state.cluster);
  }
  state.cluster = L.markerClusterGroup({ 
    chunkedLoading: true,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    maxClusterRadius: 50,
  });
  state.map.addLayer(state.cluster);
}

function renderFacilities(payload, { fit = false } = {}) {
  const collection = unwrapCollection(payload);
  clearMarkers();
  const layer = L.geoJSON(collection, { pointToLayer: featureToMarker });
  state.cluster.addLayer(layer);
  if (fit && layer.getLayers().length) {
    state.map.fitBounds(layer.getBounds(), { padding: [40, 40] });
  }
  return collection.features.length;
}

async function loadCounties() {
  try {
    perf.mark('counties-load-start');
    status('Loading county boundaries...', true);
    const data = await API.counties();
    const collection = unwrapCollection(data);
    
    if (state.countyLayer) {
      state.map.removeLayer(state.countyLayer);
    }
    
    // Emergency-focused county styling - Bold and visible borders
    const defaultStyle = {
      color: '#475569',
      weight: 2.5,
      fillColor: '#E2E8F0',
      fillOpacity: 0.4,
      interactive: true,
      dashArray: null,
    };
    
    const hoverStyle = {
      color: '#0066CC',
      weight: 4,
      fillColor: '#BFDBFE',
      fillOpacity: 0.5,
    };
    
    const selectedStyle = {
      color: '#DC143C',
      weight: 5,
      fillColor: '#FEE2E2',
      fillOpacity: 0.5,
    };
    
    state.countyLayer = L.geoJSON(collection, {
      style: () => defaultStyle,
      onEachFeature: (feature, layer) => {
        const countyName = feature.properties?.name_en || 'County';
        const countyId = feature.id ?? feature.properties?.id;
        
        layer.on('mouseover', (e) => {
          if (state.selectedCounty !== layer) {
            e.target.setStyle(hoverStyle);
          }
          e.target.bringToFront();
          status(`Click to view facilities in ${countyName}`);
        });
        
        layer.on('mouseout', (e) => {
          if (state.selectedCounty !== layer) {
            e.target.setStyle(defaultStyle);
          }
        });
        
        layer.on('click', async () => {
          if (state.selectedCounty) {
            state.selectedCounty.setStyle(defaultStyle);
          }
          
          state.selectedCounty = layer;
          layer.setStyle(selectedStyle);
          layer.bringToFront();
          
          try {
            status(`Loading ${countyName} facilities...`, true);
            const type = $('#type')?.value || undefined;
            const data = await API.withinCounty({ id: countyId, type });
            const count = renderFacilities(data, { fit: true });
            resetRadiusOverlay();
            status(count ? `${count} facilities in ${countyName}` : `No facilities in ${countyName}`);
          } catch (error) {
            console.error(error);
            status(`Failed to load ${countyName} facilities`);
          }
        });
        
        layer.bindTooltip(countyName, {
          permanent: false,
          direction: 'center',
          className: 'county-tooltip',
        });
      },
    }).addTo(state.map);
    
    perf.measure('counties-loaded', 'counties-load-start');
    status('Ready');
  } catch (error) {
    console.error(error);
    status('Failed to load counties');
  }
}

function resetRadiusOverlay() {
  if (state.radiusOverlay) {
    state.map.removeLayer(state.radiusOverlay);
    state.radiusOverlay = null;
  }
}

async function queryNearest() {
  try {
    const type = $('#type')?.value || undefined;
    if (!state.userLatLng) {
      await locateUser(true);
    }
    if (!state.userLatLng) return;
    const { lat, lng } = state.userLatLng;
    status('Finding nearest facilities...', true);
    const data = await API.nearest({ lat, lon: lng, limit: 5, type });
    const count = renderFacilities(data, { fit: true });
    status(count ? `Found ${count} nearest facilities` : 'No facilities found');
    resetRadiusOverlay();
  } catch (error) {
    console.error(error);
    status('Nearest query failed');
  }
}

async function queryWithinRadius() {
  try {
    const type = $('#type')?.value || undefined;
    if (!state.userLatLng) {
      await locateUser(true);
    }
    if (!state.userLatLng) return;
    const { lat, lng } = state.userLatLng;
    const radiusKm = $('#radius')?.value || 10;
    status(`Searching within ${radiusKm} km...`, true);
    const data = await API.withinRadius({
      lat,
      lon: lng,
      radius_m: kmToM(radiusKm),
      type,
    });
    const count = renderFacilities(data, { fit: true });
    resetRadiusOverlay();
    state.radiusOverlay = L.circle(state.userLatLng, {
      radius: kmToM(radiusKm),
      color: '#0066CC',
      weight: 3,
      fillColor: '#0066CC',
      fillOpacity: 0.15,
    }).addTo(state.map);
    status(count ? `${count} facilities within ${radiusKm} km` : 'No facilities within radius');
  } catch (error) {
    console.error(error);
    status('Radius query failed');
  }
}

async function locateUser(fly = false) {
  status('Locating...', true);
  return new Promise((resolve) => {
    const onFound = (event) => {
      state.userLatLng = event.latlng;
      if (state.userMarker) {
        state.map.removeLayer(state.userMarker);
      }
      
      // Custom user location marker
      const userIcon = L.divIcon({
        className: 'user-location-marker',
        html: `<div style="
          width: 20px;
          height: 20px;
          background: #0066CC;
          border: 4px solid white;
          border-radius: 50%;
          box-shadow: 0 3px 8px rgba(0,102,204,0.5);
        "></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });
      
      state.userMarker = L.marker(event.latlng, { 
        icon: userIcon,
        title: 'Your location',
        zIndexOffset: 1000,
      }).addTo(state.map);
      
      if (fly) state.map.flyTo(event.latlng, 12);
      status('Location found');
      resolve(event.latlng);
    };
    const onError = () => {
      status('Unable to get location');
      resolve(null);
    };
    state.map.once('locationfound', onFound);
    state.map.once('locationerror', onError);
    state.map.locate({ setView: false, maxZoom: 12, enableHighAccuracy: true });
  });
}

function setupDrawTools() {
  const drawnItems = new L.FeatureGroup().addTo(state.map);
  const drawControl = new L.Control.Draw({
    position: 'topright',
    draw: {
      marker: false,
      rectangle: {
        shapeOptions: {
          color: '#0066CC',
          weight: 3,
          fillOpacity: 0.15,
        },
      },
      polygon: {
        shapeOptions: {
          color: '#0066CC',
          weight: 3,
          fillOpacity: 0.15,
        },
      },
      circle: false,
      circlemarker: false,
      polyline: false,
    },
    edit: {
      featureGroup: drawnItems,
      edit: false,
    },
  });
  state.map.addControl(drawControl);

  state.map.on(L.Draw.Event.CREATED, async (event) => {
    drawnItems.clearLayers();
    const layer = event.layer;
    drawnItems.addLayer(layer);
    resetRadiusOverlay();
    status('Querying drawn area...', true);
    try {
      const type = $('#type')?.value || undefined;
      const data = await API.withinPolygon(layer.toGeoJSON(), type);
      const count = renderFacilities(data, { fit: true });
      status(count ? `${count} facilities in drawn area` : 'No facilities in drawn area');
    } catch (error) {
      console.error(error);
      status('Polygon query failed');
    }
  });
}

function setupEvents() {
  $('#radius')?.addEventListener('input', (event) => {
    const output = $('#radiusOut');
    if (output) output.value = event.target.value;
  });
  $('#locateBtn')?.addEventListener('click', () => locateUser(true));
  $('#nearestBtn')?.addEventListener('click', () => queryNearest());
  $('#radiusBtn')?.addEventListener('click', () => queryWithinRadius());
}

function initMap() {
  perf.mark('map-init-start');
  
  state.map = L.map('map', { 
    zoomControl: true,
    preferCanvas: true,
    attributionControl: true,
  }).setView([53.3498, -6.2603], 7);
  
  // Cleaner map tiles
  const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    updateWhenZooming: false,
    updateWhenIdle: true,
  }).addTo(state.map);
  
  // Move zoom control to top-right
  state.map.zoomControl.setPosition('topright');
  
  // Track tile loading
  let tileLoadStart = null;
  tileLayer.on('loading', () => {
    tileLoadStart = performance.now();
  });
  tileLayer.on('load', () => {
    if (tileLoadStart) {
      const duration = performance.now() - tileLoadStart;
      console.log(`[Perf] Tiles loaded: ${duration.toFixed(2)}ms`);
    }
  });
  
  clearMarkers();
  setupDrawTools();
  setupEvents();
  loadCounties();
  
  // Initialize incident manager
  state.incidentManager = new IncidentManager(state.map);
  window.incidentManager = state.incidentManager;  // Expose for popup buttons
  
  perf.measure('map-initialized', 'map-init-start');
}

document.addEventListener('DOMContentLoaded', initMap);
