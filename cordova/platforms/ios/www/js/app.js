/**
 * ES Locator - Cordova Mobile App
 * 
 * Main application entry point
 */

import { setApiBaseUrl, isAuthenticated, login, logout, getStoredUser, authFetch, ensureValidToken } from './auth.js';

// =============================================================================
// Configuration
// =============================================================================

// TODO: Update this to your production server URL
const API_BASE_URL = 'http://localhost:8000';  // Change in production

// =============================================================================
// State
// =============================================================================

let map = null;
let markersLayer = null;
let routesLayer = null;
let incidents = [];
let vehicles = [];
let currentUser = null;
let pollingInterval = null;

// =============================================================================
// App Initialization
// =============================================================================

document.addEventListener('deviceready', onDeviceReady, false);

// Fallback for browser testing
if (!window.cordova) {
    document.addEventListener('DOMContentLoaded', onDeviceReady);
}

function onDeviceReady() {
    console.log('ES Locator: Device Ready');
    
    // Set API URL
    setApiBaseUrl(API_BASE_URL);
    
    // Initialize app
    initializeApp();
}

async function initializeApp() {
    // Check if user is already authenticated
    if (isAuthenticated()) {
        const valid = await ensureValidToken();
        if (valid) {
            currentUser = getStoredUser();
            showMainScreen();
            return;
        }
    }
    
    // Show login screen
    showLoginScreen();
}

// =============================================================================
// Screen Management
// =============================================================================

function hideAllScreens() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-screen').style.display = 'none';
}

function showLoginScreen() {
    hideAllScreens();
    document.getElementById('login-screen').style.display = 'flex';
    setupLoginForm();
}

function showMainScreen() {
    hideAllScreens();
    document.getElementById('main-screen').style.display = 'flex';
    updateUserInfo();
    initializeMap();
    startPolling();
    setupMainScreenEvents();
}

// =============================================================================
// Login
// =============================================================================

function setupLoginForm() {
    const form = document.getElementById('login-form');
    const errorDiv = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-btn');
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // Show loading state
        submitBtn.querySelector('.btn-text').textContent = 'Signing in...';
        submitBtn.querySelector('.spinner-border').classList.remove('d-none');
        submitBtn.disabled = true;
        errorDiv.style.display = 'none';
        
        const result = await login(username, password);
        
        // Reset button
        submitBtn.querySelector('.btn-text').textContent = 'Sign In';
        submitBtn.querySelector('.spinner-border').classList.add('d-none');
        submitBtn.disabled = false;
        
        if (result.success) {
            currentUser = result.user;
            showMainScreen();
        } else {
            errorDiv.textContent = result.error;
            errorDiv.style.display = 'block';
        }
    };
}

// =============================================================================
// Map
// =============================================================================

function initializeMap() {
    if (map) return;
    
    // Initialize Leaflet map
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([53.3498, -6.2603], 12); // Dublin center
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);
    
    // Add zoom control to top right
    L.control.zoom({ position: 'topright' }).addTo(map);
    
    // Create layers
    markersLayer = L.layerGroup().addTo(map);
    routesLayer = L.layerGroup().addTo(map);
    
    // Try to get user location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 14);
                
                // Add user location marker
                L.circleMarker([latitude, longitude], {
                    radius: 10,
                    fillColor: '#0077B6',
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map).bindPopup('Your Location');
            },
            (error) => {
                console.warn('Geolocation error:', error);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }
    
    // Load initial data
    loadIncidents();
    loadVehicles();
}

// =============================================================================
// Data Loading
// =============================================================================

async function loadIncidents() {
    try {
        const response = await authFetch('/api/incidents/');
        if (response.ok) {
            const data = await response.json();
            incidents = data.features || data;
            renderIncidentMarkers();
            updateIncidentsList();
        }
    } catch (error) {
        console.error('Error loading incidents:', error);
    }
}

async function loadVehicles() {
    try {
        const response = await authFetch('/api/vehicles/');
        if (response.ok) {
            const data = await response.json();
            vehicles = data.features || data;
            renderVehicleMarkers();
        }
    } catch (error) {
        console.error('Error loading vehicles:', error);
    }
}

// =============================================================================
// Markers
// =============================================================================

const SEVERITY_COLORS = {
    critical: '#dc3545',
    high: '#fd7e14',
    medium: '#ffc107',
    low: '#28a745'
};

const INCIDENT_ICONS = {
    fire: 'bi-fire',
    medical: 'bi-heart-pulse',
    crime: 'bi-shield-exclamation',
    accident: 'bi-car-front',
    default: 'bi-exclamation-triangle'
};

function renderIncidentMarkers() {
    if (!markersLayer) return;
    
    // Clear existing incident markers (keep vehicle markers)
    markersLayer.eachLayer(layer => {
        if (layer.options && layer.options.markerType === 'incident') {
            markersLayer.removeLayer(layer);
        }
    });
    
    incidents.forEach(incident => {
        const props = incident.properties || incident;
        const coords = incident.geometry?.coordinates || [props.longitude, props.latitude];
        
        if (!coords || coords.length < 2) return;
        
        const color = SEVERITY_COLORS[props.severity] || SEVERITY_COLORS.medium;
        const iconClass = INCIDENT_ICONS[props.incident_type] || INCIDENT_ICONS.default;
        
        const icon = L.divIcon({
            html: `<div class="incident-marker" style="background-color: ${color}"><i class="bi ${iconClass}"></i></div>`,
            className: 'custom-marker',
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });
        
        const marker = L.marker([coords[1], coords[0]], { 
            icon,
            markerType: 'incident',
            incidentId: incident.id || props.id
        });
        
        marker.bindPopup(`
            <strong>${props.title || 'Incident'}</strong><br>
            <span class="badge" style="background-color: ${color}; color: white;">${props.severity}</span>
            <span class="badge bg-secondary">${props.status}</span>
        `);
        
        marker.on('click', () => showIncidentDetail(incident));
        marker.addTo(markersLayer);
    });
}

function renderVehicleMarkers() {
    if (!markersLayer) return;
    
    // Clear existing vehicle markers
    markersLayer.eachLayer(layer => {
        if (layer.options && layer.options.markerType === 'vehicle') {
            markersLayer.removeLayer(layer);
        }
    });
    
    vehicles.forEach(vehicle => {
        const props = vehicle.properties || vehicle;
        const coords = vehicle.geometry?.coordinates || [props.longitude, props.latitude];
        
        if (!coords || coords.length < 2) return;
        
        const isAvailable = props.status === 'available';
        const color = isAvailable ? '#28a745' : '#6c757d';
        
        const icon = L.divIcon({
            html: `<div class="vehicle-marker" style="background-color: ${color}"><i class="bi bi-truck"></i></div>`,
            className: 'custom-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        });
        
        const marker = L.marker([coords[1], coords[0]], { 
            icon,
            markerType: 'vehicle',
            vehicleId: vehicle.id || props.id
        });
        
        marker.bindPopup(`
            <strong>${props.call_sign || props.callsign || 'Vehicle'}</strong><br>
            <span class="badge" style="background-color: ${color}; color: white;">${props.status}</span>
        `);
        
        marker.addTo(markersLayer);
    });
}

// =============================================================================
// Incident List & Details
// =============================================================================

function updateIncidentsList() {
    const listEl = document.getElementById('incidents-list');
    if (!listEl) return;
    
    if (incidents.length === 0) {
        listEl.innerHTML = '<div class="empty-state"><i class="bi bi-check-circle"></i><p>No active incidents</p></div>';
        return;
    }
    
    listEl.innerHTML = incidents.map(incident => {
        const props = incident.properties || incident;
        const color = SEVERITY_COLORS[props.severity] || SEVERITY_COLORS.medium;
        
        return `
            <div class="incident-card" data-id="${incident.id || props.id}">
                <div class="incident-header">
                    <span class="incident-severity" style="background-color: ${color}"></span>
                    <h4>${props.title || 'Incident'}</h4>
                </div>
                <div class="incident-meta">
                    <span class="badge bg-secondary">${props.status}</span>
                    <span class="badge" style="background-color: ${color}; color: white;">${props.severity}</span>
                </div>
                <p class="incident-address">${props.address || 'Unknown location'}</p>
            </div>
        `;
    }).join('');
    
    // Add click handlers
    listEl.querySelectorAll('.incident-card').forEach(card => {
        card.onclick = () => {
            const id = parseInt(card.dataset.id);
            const incident = incidents.find(i => (i.id || i.properties?.id) === id);
            if (incident) showIncidentDetail(incident);
        };
    });
}

function showIncidentDetail(incident) {
    const props = incident.properties || incident;
    const modal = document.getElementById('incident-modal');
    const title = document.getElementById('incident-title');
    const details = document.getElementById('incident-details');
    const actions = document.getElementById('incident-actions');
    
    title.textContent = props.title || 'Incident Details';
    
    const color = SEVERITY_COLORS[props.severity] || SEVERITY_COLORS.medium;
    
    details.innerHTML = `
        <div class="detail-row">
            <span class="label">Status:</span>
            <span class="badge bg-secondary">${props.status}</span>
        </div>
        <div class="detail-row">
            <span class="label">Severity:</span>
            <span class="badge" style="background-color: ${color}; color: white;">${props.severity}</span>
        </div>
        <div class="detail-row">
            <span class="label">Type:</span>
            <span>${props.incident_type || 'Unknown'}</span>
        </div>
        <div class="detail-row">
            <span class="label">Address:</span>
            <span>${props.address || 'Unknown'}</span>
        </div>
        ${props.description ? `
        <div class="detail-row full-width">
            <span class="label">Description:</span>
            <p>${props.description}</p>
        </div>
        ` : ''}
        ${props.reported_at ? `
        <div class="detail-row">
            <span class="label">Reported:</span>
            <span>${new Date(props.reported_at).toLocaleString()}</span>
        </div>
        ` : ''}
    `;
    
    // Actions based on user role
    const isDispatcher = currentUser?.is_dispatcher || currentUser?.is_admin;
    
    actions.innerHTML = `
        <button class="btn btn-outline-primary" onclick="zoomToIncident(${incident.id || props.id})">
            <i class="bi bi-geo-alt"></i> Show on Map
        </button>
        ${isDispatcher ? `
        <button class="btn btn-primary" onclick="dispatchToIncident(${incident.id || props.id})">
            <i class="bi bi-truck"></i> Dispatch
        </button>
        ` : ''}
    `;
    
    modal.style.display = 'flex';
}

// Global functions for button handlers
window.zoomToIncident = function(id) {
    const incident = incidents.find(i => (i.id || i.properties?.id) === id);
    if (incident) {
        const coords = incident.geometry?.coordinates;
        if (coords) {
            map.setView([coords[1], coords[0]], 16);
            document.getElementById('incident-modal').style.display = 'none';
        }
    }
};

window.dispatchToIncident = function(id) {
    // TODO: Implement dispatch modal
    alert('Dispatch functionality coming soon!');
};

// =============================================================================
// Main Screen Events
// =============================================================================

function setupMainScreenEvents() {
    // Menu button
    document.getElementById('menu-btn').onclick = () => {
        document.getElementById('side-menu').classList.add('open');
    };
    
    // Close menu on overlay click
    document.querySelector('.side-menu-overlay').onclick = () => {
        document.getElementById('side-menu').classList.remove('open');
    };
    
    // Menu items
    document.querySelectorAll('.side-menu-nav a').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const action = link.dataset.action;
            handleMenuAction(action);
            document.getElementById('side-menu').classList.remove('open');
        };
    });
    
    // Refresh button
    document.getElementById('refresh-btn').onclick = () => {
        loadIncidents();
        loadVehicles();
    };
    
    // Bottom nav
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.onclick = () => {
            const tab = btn.dataset.tab;
            handleTabChange(tab);
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        };
    });
    
    // Close incident modal
    document.getElementById('close-incident-modal').onclick = () => {
        document.getElementById('incident-modal').style.display = 'none';
    };
    
    // Close incidents panel
    document.getElementById('close-incidents-panel').onclick = () => {
        document.getElementById('incidents-panel').style.display = 'none';
    };
}

function handleMenuAction(action) {
    switch (action) {
        case 'logout':
            stopPolling();
            logout(null); // Don't redirect
            currentUser = null;
            showLoginScreen();
            break;
        case 'incidents':
            document.getElementById('incidents-panel').style.display = 'block';
            break;
        case 'settings':
            alert('Settings coming soon!');
            break;
        default:
            console.log('Menu action:', action);
    }
}

function handleTabChange(tab) {
    // Hide all panels first
    document.getElementById('incidents-panel').style.display = 'none';
    
    switch (tab) {
        case 'map':
            // Already showing map
            break;
        case 'incidents':
            document.getElementById('incidents-panel').style.display = 'block';
            break;
        case 'vehicles':
            alert('Vehicles panel coming soon!');
            break;
        case 'profile':
            alert('Profile coming soon!');
            break;
    }
}

function updateUserInfo() {
    if (currentUser) {
        document.getElementById('user-name').textContent = 
            currentUser.first_name ? `${currentUser.first_name} ${currentUser.last_name}` : currentUser.username;
        document.getElementById('user-role').textContent = currentUser.role_display || currentUser.role || 'User';
    }
}

// =============================================================================
// Polling
// =============================================================================

function startPolling() {
    if (pollingInterval) return;
    
    // Poll every 30 seconds
    pollingInterval = setInterval(() => {
        loadIncidents();
        loadVehicles();
    }, 30000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// =============================================================================
// Network Status (Cordova plugin)
// =============================================================================

document.addEventListener('offline', () => {
    console.log('App is offline');
    // Show offline indicator
}, false);

document.addEventListener('online', () => {
    console.log('App is online');
    // Hide offline indicator and refresh data
    loadIncidents();
    loadVehicles();
}, false);
