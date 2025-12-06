// User location, drop pin, and county interaction functions

import API from './api.js';
import { $, status, state } from './map-state.js';
import { renderFacilities, unwrapCollection, resetRadiusOverlay } from './map-rendering.js';
import { themeColors } from './theme-config.js';

export async function locateUser(fly = false) {
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

export function setUserLocation(latlng, fly = false) {
  state.userLatLng = latlng;
  if (state.userMarker) {
    state.map.removeLayer(state.userMarker);
  }
  
  const pinIcon = L.divIcon({
    className: 'custom-pin-icon',
    html: `<div style="background-color: ${themeColors.emergencyLight}; width: 24px; height: 24px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"><div style="width: 8px; height: 8px; background: white; border-radius: 50%; margin: 5px;"></div></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
  });
  
  state.userMarker = L.marker(latlng, { 
    icon: pinIcon,
    title: 'Your location',
    draggable: true
  }).addTo(state.map);
  
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

export function toggleDropPinMode() {
  state.dropPinMode = !state.dropPinMode;
  const btn = $('#dropPinBtn');
  
  if (!btn) {
    console.error('Drop pin button not found!');
    return;
  }
  
  if (state.dropPinMode) {
    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-secondary', 'active');
    state.map.getContainer().style.cursor = 'crosshair';
    
    if (state.countyLayer) {
      state.countyLayer.eachLayer(layer => {
        layer.setStyle({
          fillOpacity: 0.1,
          weight: 1,
        });
        layer.off('click');
        layer.off('mouseover');
        layer.off('mouseout');
        layer.closePopup();
        layer.closeTooltip();
      });
      state.map.removeLayer(state.countyLayer);
      state.countyLayer.addTo(state.map);
      state.countyLayer.bringToBack();
    }
    
    status('Click anywhere on the map to drop a pin.');
  } else {
    btn.classList.remove('btn-secondary', 'active');
    btn.classList.add('btn-outline-secondary');
    state.map.getContainer().style.cursor = '';
    
    if (state.countyLayer) {
      state.map.removeLayer(state.countyLayer);
      state.countyLayer = null;
      loadCounties();
    }
    
    status('Drop pin mode disabled.');
  }
}

export function handleMapClick(event) {
  if (state.dropPinMode) {
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

export async function loadCounties() {
  try {
    const data = await API.counties();
    const collection = unwrapCollection(data);
    const select = $('#countySelect');
    
    state.countyFeatures = collection.features;
    
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
    
    state.countyLayer = L.geoJSON(collection, {
      style: function(feature) {
        return {
          color: themeColors.mapCountyBorder,
          weight: 2,
          fillColor: themeColors.mapCountyFill,
          fillOpacity: 0.25,
          interactive: true,
          className: 'county-boundary',
        };
      },
      onEachFeature: function(feature, layer) {
        const countyName = feature.properties?.name_en || 'County';
        const countyId = feature.id ?? feature.properties?.id;
        
        layer.on('mouseover', function(e) {
          if (state.dropPinMode) return;
          const layer = e.target;
          layer.setStyle({
            fillColor: themeColors.mapCountyHover,
            fillOpacity: 0.4,
            weight: 3,
            color: themeColors.mapCountyHover,
          });
          layer.bringToFront();
          status(`Click to view facilities in ${countyName}`);
        });
        
        layer.on('mouseout', function(e) {
          if (state.dropPinMode) return;
          const layer = e.target;
          layer.setStyle({
            fillColor: themeColors.mapCountyFill,
            fillOpacity: 0.25,
            weight: 2,
            color: themeColors.mapCountyBorder,
          });
        });
        
        layer.on('click', async function(e) {
          if (state.dropPinMode) {
            return;
          }
          
          try {
            status(`Loading ${countyName} facilities...`);
            const type = $('#type')?.value || undefined;
            const data = await API.withinCounty({ id: countyId, type });
            const count = renderFacilities(data, { fit: true });
            resetRadiusOverlay();
            
            state.countyLayer.eachLayer(l => {
              l.setStyle({
                fillColor: themeColors.mapCountyFill,
                fillOpacity: 0.25,
                weight: 2,
                color: themeColors.mapCountyBorder,
              });
            });
            layer.setStyle({
              fillColor: themeColors.mapCountyActive,
              fillOpacity: 0.25,
              weight: 3,
              color: themeColors.mapCountyActive,
            });
            layer.bringToFront();
            
            status(count ? `Showing ${count} facilities in ${countyName}` : `No facilities found in ${countyName}`);
          } catch (error) {
            console.error(error);
            status(`Failed to load ${countyName} facilities.`);
          }
        });
        
        layer.bindTooltip(countyName, {
          permanent: false,
          direction: 'center',
          className: 'county-tooltip',
          opacity: 0.9,
        });
        
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
