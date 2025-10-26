import API from './api.js';
import { icons } from './icons.js';

const state = {
  map: null,
  cluster: null,
  countyLayer: null,
  userLatLng: null,
  userMarker: null,
  radiusOverlay: null,
  dropPinMode: false,
};

const $ = (selector) => document.querySelector(selector);
const statusEl = () => $('#statusMsg');
const status = (message) => {
  const el = statusEl();
  if (el) el.textContent = message;
};

const kmToM = (km) => Math.round(Number(km) * 1000);

function popupHtml(feature) {
  const props = feature.properties || {};
  const meta = props.properties || {};
  const phone = props.phone ? `<div>☎ ${props.phone}</div>` : '';
  const website = props.website
    ? `<div>🔗 <a href="${props.website}" target="_blank" rel="noopener">Website</a></div>`
    : '';
  return `
    <div class="fw-semibold">${props.name}</div>
    <div class="text-muted small mb-1">${(props.type || '').replace('_', ' ')}</div>
    <div class="small">${props.address || ''}</div>
    ${phone}${website}
    ${meta.ae ? '<span class="badge bg-success mt-1">A&amp;E</span>' : ''}
  `;
}

function featureToMarker(feature, latlng) {
  const type = feature.properties?.type || 'default';
  return L.marker(latlng, { icon: icons[type] || icons.default }).bindPopup(popupHtml(feature));
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
  state.cluster = L.markerClusterGroup({ chunkedLoading: true });
  state.map.addLayer(state.cluster);
}

function renderFacilities(payload, { fit = false } = {}) {
  const collection = unwrapCollection(payload);
  clearMarkers();
  const layer = L.geoJSON(collection, { pointToLayer: featureToMarker });
  state.cluster.addLayer(layer);
  if (fit && layer.getLayers().length) {
    state.map.fitBounds(layer.getBounds(), { padding: [20, 20] });
  }
  return collection.features.length;
}

async function loadCounties() {
  try {
    const data = await API.counties();
    const collection = unwrapCollection(data);
    const select = $('#countySelect');
    
    // Store county features for click handling
    state.countyFeatures = collection.features;
    
    // Optionally populate dropdown if it exists
    if (select) {
      collection.features.forEach((feature) => {
        const opt = document.createElement('option');
        const id = feature.id ?? feature.properties?.id;
        opt.value = id ?? '';
        opt.textContent = feature.properties?.name_en || `County ${opt.value}`;
        select.appendChild(opt);
      });
    }
    
    if (state.countyLayer) {
      state.map.removeLayer(state.countyLayer);
    }
    
    // Make counties interactive and clickable
    state.countyLayer = L.geoJSON(collection, {
      style: function(feature) {
        return {
          color: '#6c757d',
          weight: 2,
          fillColor: '#e9ecef',
          fillOpacity: 0.25,
          interactive: true,
          className: 'county-boundary',
        };
      },
      onEachFeature: function(feature, layer) {
        const countyName = feature.properties?.name_en || 'County';
        const countyId = feature.id ?? feature.properties?.id;
        
        // Add hover effect
        layer.on('mouseover', function(e) {
          if (state.dropPinMode) return; // Don't highlight counties in drop pin mode
          const layer = e.target;
          layer.setStyle({
            fillColor: '#0d6efd',
            fillOpacity: 0.4,
            weight: 3,
            color: '#0d6efd',
          });
          layer.bringToFront();
          status(`Click to view facilities in ${countyName}`);
        });
        
        layer.on('mouseout', function(e) {
          if (state.dropPinMode) return;
          const layer = e.target;
          layer.setStyle({
            fillColor: '#e9ecef',
            fillOpacity: 0.25,
            weight: 2,
            color: '#6c757d',
          });
        });
        
        // Add click handler
        layer.on('click', async function(e) {
          // If in drop pin mode, let the map handle it
          if (state.dropPinMode) {
            return;
          }
          
          try {
            status(`Loading ${countyName} facilities...`);
            const type = $('#type')?.value || undefined;
            const data = await API.withinCounty({ id: countyId, type });
            const count = renderFacilities(data, { fit: true });
            resetRadiusOverlay();
            
            // Highlight selected county
            state.countyLayer.eachLayer(l => {
              l.setStyle({
                fillColor: '#e9ecef',
                fillOpacity: 0.25,
                weight: 2,
                color: '#6c757d',
              });
            });
            layer.setStyle({
              fillColor: '#0d6efd',
              fillOpacity: 0.25,
              weight: 3,
              color: '#0d6efd',
            });
            layer.bringToFront();
            
            status(count ? `Showing ${count} facilities in ${countyName}` : `No facilities found in ${countyName}`);
          } catch (error) {
            console.error(error);
            status(`Failed to load ${countyName} facilities.`);
          }
        });
        
        // Add tooltip that shows county name on hover
        layer.bindTooltip(countyName, {
          permanent: false,
          direction: 'center',
          className: 'county-tooltip',
          opacity: 0.9,
        });
        
        // Also bind popup for additional info
        layer.bindPopup(`<strong>${countyName}</strong><br><small>Click to view facilities</small>`, {
          closeButton: false,
          className: 'county-popup',
        });
      }
    }).addTo(state.map);
  } catch (error) {
    console.error(error);
    status('Failed to load counties.');
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
    status('Finding nearest facilities…');
    const data = await API.nearest({ lat, lon: lng, limit: 5, type });
    const count = renderFacilities(data, { fit: true });
    status(count ? `Found ${count} nearest facilities.` : 'No facilities found.');
    resetRadiusOverlay();
  } catch (error) {
    console.error(error);
    status('Nearest query failed.');
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
    status(`Searching within ${radiusKm} km…`);
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
      color: '#0d6efd',
      weight: 1,
    }).addTo(state.map);
    status(count ? `Showing ${count} facilities within ${radiusKm} km.` : 'No facilities found within radius.');
  } catch (error) {
    console.error(error);
    status('Radius query failed.');
  }
}

async function queryWithinCounty() {
  const id = $('#countySelect')?.value;
  const type = $('#type')?.value || undefined;
  if (!id) {
    status('Select a county to filter.');
    return;
  }
  try {
    status('Filtering by county…');
    const data = await API.withinCounty({ id, type });
    const count = renderFacilities(data, { fit: true });
    resetRadiusOverlay();
    status(count ? 'Showing facilities within county.' : 'No facilities found in selected county.');
  } catch (error) {
    console.error(error);
    status('County query failed.');
  }
}

async function locateUser(fly = false) {
  status('Locating…');
  return new Promise((resolve) => {
    const onFound = (event) => {
      setUserLocation(event.latlng, fly);
      status('Location set.');
      resolve(event.latlng);
    };
    const onError = () => {
      status('Unable to get location. Click the map to drop a pin instead.');
      resolve(null);
    };
    state.map.once('locationfound', onFound);
    state.map.once('locationerror', onError);
    state.map.locate({ setView: false, maxZoom: 12, enableHighAccuracy: true });
  });
}

function setUserLocation(latlng, fly = false) {
  state.userLatLng = latlng;
  if (state.userMarker) {
    state.map.removeLayer(state.userMarker);
  }
  
  // Create custom pin icon
  const pinIcon = L.divIcon({
    className: 'custom-pin-icon',
    html: '<div style="background-color: #dc3545; width: 24px; height: 24px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"><div style="width: 8px; height: 8px; background: white; border-radius: 50%; margin: 5px;"></div></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 24],
  });
  
  state.userMarker = L.marker(latlng, { 
    icon: pinIcon,
    title: 'Your location',
    draggable: true
  }).addTo(state.map);
  
  // Allow dragging the pin
  state.userMarker.on('dragend', function(event) {
    const marker = event.target;
    const position = marker.getLatLng();
    state.userLatLng = position;
    status(`Pin moved to ${position.lat.toFixed(4)}, ${position.lng.toFixed(4)}`);
  });
  
  state.userMarker.bindPopup(
    `<strong>Your Pin</strong><br>` +
    `<small>Lat: ${latlng.lat.toFixed(4)}<br>Lng: ${latlng.lng.toFixed(4)}</small><br>` +
    `<small class="text-muted">Drag to reposition</small>`
  );
  
  if (fly) state.map.flyTo(latlng, 12);
}

function toggleDropPinMode() {
  console.log('toggleDropPinMode called, current mode:', state.dropPinMode);
  state.dropPinMode = !state.dropPinMode;
  const btn = $('#dropPinBtn');
  
  console.log('Button found:', btn);
  if (!btn) {
    console.error('Drop pin button not found!');
    return;
  }
  
  if (state.dropPinMode) {
    console.log('Entering drop pin mode');
    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-secondary', 'active');
    state.map.getContainer().style.cursor = 'crosshair';
    
    // Disable county layer interactivity completely
    if (state.countyLayer) {
      state.countyLayer.eachLayer(layer => {
        layer.setStyle({
          fillOpacity: 0.1,
          weight: 1,
        });
        // Disable all interactions
        layer.off('click');
        layer.off('mouseover');
        layer.off('mouseout');
        layer.closePopup();
        layer.closeTooltip();
      });
      // Remove from map temporarily and re-add to change z-index
      state.map.removeLayer(state.countyLayer);
      state.countyLayer.addTo(state.map);
      state.countyLayer.bringToBack();
    }
    
    status('Click anywhere on the map to drop a pin.');
  } else {
    console.log('Exiting drop pin mode');
    btn.classList.remove('btn-secondary', 'active');
    btn.classList.add('btn-outline-secondary');
    state.map.getContainer().style.cursor = '';
    
    // Re-enable county layer interactivity by reloading counties
    if (state.countyLayer) {
      state.map.removeLayer(state.countyLayer);
      state.countyLayer = null;
      loadCounties(); // Reload to restore event handlers
    }
    
    status('Drop pin mode disabled.');
  }
}

function handleMapClick(event) {
  console.log('Map clicked! dropPinMode:', state.dropPinMode, 'event:', event);
  if (state.dropPinMode) {
    console.log('Dropping pin at:', event.latlng);
    setUserLocation(event.latlng, false);
    state.dropPinMode = false;
    const btn = $('#dropPinBtn');
    if (btn) {
      btn.classList.remove('btn-secondary', 'active');
      btn.classList.add('btn-outline-secondary');
    }
    state.map.getContainer().style.cursor = '';
    status('Pin dropped. Use "Nearest" or "Within radius" to find facilities.');
  }
}

function setupDrawTools() {
  const drawnItems = new L.FeatureGroup().addTo(state.map);
  const drawControl = new L.Control.Draw({
    draw: {
      marker: false,
      rectangle: true,
      polygon: true,
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
    status('Polygon drawn — querying…');
    try {
      const type = $('#type')?.value || undefined;
      const data = await API.withinPolygon(layer.toGeoJSON(), type);
      const count = renderFacilities(data, { fit: true });
      status(count ? 'Results filtered by drawn area.' : 'No facilities inside drawn area.');
    } catch (error) {
      console.error(error);
      status('Polygon query failed.');
    }
  });
}

function setupEvents() {
  console.log('Setting up event listeners');
  $('#radius')?.addEventListener('input', (event) => {
    const output = $('#radiusOut');
    if (output) output.value = event.target.value;
  });
  
  const locateBtn = $('#locateBtn');
  const dropPinBtn = $('#dropPinBtn');
  const nearestBtn = $('#nearestBtn');
  const radiusBtn = $('#radiusBtn');
  
  console.log('Buttons found:', { locateBtn, dropPinBtn, nearestBtn, radiusBtn });
  
  locateBtn?.addEventListener('click', () => locateUser(true));
  dropPinBtn?.addEventListener('click', () => {
    console.log('Drop pin button clicked!');
    toggleDropPinMode();
  });
  nearestBtn?.addEventListener('click', () => queryNearest());
  radiusBtn?.addEventListener('click', () => queryWithinRadius());
  // County selection now handled by clicking on map, not dropdown
  
  // Handle map clicks for dropping pins
  state.map.on('click', handleMapClick);
}

function initMap() {
  state.map = L.map('map', { zoomControl: true }).setView([53.3498, -6.2603], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(state.map);
  clearMarkers();
  setupDrawTools();
  setupEvents();
  loadCounties();
  status('Map ready. Click any county or use filters above.');
}

document.addEventListener('DOMContentLoaded', initMap);
