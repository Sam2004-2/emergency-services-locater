// Map initialization and event setup

import API from './api.js';
import { $, status, state } from './map-state.js';
import { clearMarkers, renderFacilities, resetRadiusOverlay } from './map-rendering.js';
import { locateUser, toggleDropPinMode, handleMapClick, loadCounties } from './map-interactions.js';
import { queryNearest, queryWithinRadius } from './map-queries.js';

export { loadCounties };

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
  $('#radius')?.addEventListener('input', (event) => {
    const output = $('#radiusOut');
    if (output) output.value = event.target.value;
  });
  
  $('#locateBtn')?.addEventListener('click', () => locateUser(true));
  $('#dropPinBtn')?.addEventListener('click', () => toggleDropPinMode());
  $('#nearestBtn')?.addEventListener('click', () => queryNearest());
  $('#radiusBtn')?.addEventListener('click', () => queryWithinRadius());
  
  state.map.on('click', handleMapClick);
}

export function initMap() {
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
