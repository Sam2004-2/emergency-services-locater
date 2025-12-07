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

function setupSidebar() {
  const sidebar = $('#mapSidebar');
  const toggleBtn = $('#sidebarToggle');
  const mobileBtn = $('#mobileSidebarBtn');

  if (!sidebar) return;

  // Create overlay for mobile
  let overlay = document.querySelector('.sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.querySelector('.map-page')?.appendChild(overlay);
  }

  function openSidebar() {
    sidebar.classList.add('open');
    mobileBtn?.classList.add('hidden');
    overlay?.classList.add('visible');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    mobileBtn?.classList.remove('hidden');
    overlay?.classList.remove('visible');
  }

  // Toggle button inside sidebar
  toggleBtn?.addEventListener('click', closeSidebar);

  // Mobile floating button
  mobileBtn?.addEventListener('click', openSidebar);

  // Close on overlay click
  overlay?.addEventListener('click', closeSidebar);

  // Close sidebar when clicking on the map (mobile only)
  state.map.on('click', () => {
    if (window.innerWidth < 992 && sidebar.classList.contains('open')) {
      closeSidebar();
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
  setupSidebar();
  loadCounties();
  status('Map ready. Click any county or use filters.');
}
