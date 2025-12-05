/**
 * Incidents Dashboard Controller
 * 
 * Main controller for the Emergency Services Dispatch Dashboard.
 */

class DashboardController {
    constructor(options = {}) {
        this.map = null;
        this.routing = null;
        this.apiUrl = options.apiUrl || '/api';
        
        // Layers
        this.incidentLayer = null;
        this.vehicleLayer = null;
        this.coverageLayer = null;
        
        // Data
        this.incidents = new Map();
        this.vehicles = new Map();
        this.selectedIncident = null;
        this.selectedVehicle = null;
        
        // Icons
        this.incidentIcons = {};
        this.vehicleIcons = {};
        
        // Update intervals
        this.updateIntervals = [];
        
        // Initialize icons
        this.initializeIcons();
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        // Initialize map
        this.initMap();
        
        // Initialize routing service
        this.routing = new RoutingService(this.map);
        
        // Initialize layers
        this.initLayers();
        
        // Load initial data
        await this.loadData();
        
        // Setup WebSocket connections
        this.setupWebSockets();
        
        // Setup event handlers
        this.setupEventHandlers();
        
        // Start periodic updates (fallback if WebSockets fail)
        this.startPeriodicUpdates();
        
        console.log('Dashboard initialized');
    }

    /**
     * Initialize the Leaflet map
     */
    initMap() {
        // Default to Ireland center
        const defaultCenter = [53.5, -7.5];
        const defaultZoom = 7;
        
        this.map = L.map('dispatch-map', {
            center: defaultCenter,
            zoom: defaultZoom,
            zoomControl: true
        });
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
    }

    /**
     * Initialize map layers
     */
    initLayers() {
        this.incidentLayer = L.layerGroup().addTo(this.map);
        this.vehicleLayer = L.layerGroup().addTo(this.map);
        this.coverageLayer = L.layerGroup(); // Not added by default
        this.coverageLoaded = false;
        
        // Add layer control
        const overlays = {
            'Incidents': this.incidentLayer,
            'Vehicles': this.vehicleLayer,
            'Coverage Zones': this.coverageLayer
        };
        
        L.control.layers(null, overlays, { position: 'topright' }).addTo(this.map);
        
        // Load coverage data when layer is first enabled
        this.map.on('overlayadd', (e) => {
            if (e.name === 'Coverage Zones' && !this.coverageLoaded) {
                this.loadCoverageAnalysis()
                    .then(() => { this.coverageLoaded = true; })
                    .catch(err => console.error('Coverage load failed:', err));
            }
        });
    }

    /**
     * Initialize marker icons
     */
    initializeIcons() {
        // Incident icons by type
        const incidentColors = {
            fire: '#f44336',
            medical: '#4CAF50',
            crime: '#9C27B0',
            traffic: '#FF9800',
            hazmat: '#795548',
            rescue: '#2196F3',
            other: '#607D8B'
        };
        
        // Priority indicators
        const priorityIcons = {
            critical: '🔴',
            high: '🟠',
            medium: '🟡',
            low: '🟢'
        };
        
        Object.keys(incidentColors).forEach(type => {
            this.incidentIcons[type] = (priority) => L.divIcon({
                className: 'incident-marker',
                html: `<div style="
                    background-color: ${incidentColors[type]};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                ">${priorityIcons[priority] || '❓'}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
        });
        
        // Vehicle icons by type
        const vehicleEmojis = {
            fire: '🚒',
            ambulance: '🚑',
            police: '🚔',
            rescue: '🚐'
        };
        
        Object.keys(vehicleEmojis).forEach(type => {
            this.vehicleIcons[type] = (status) => L.divIcon({
                className: 'vehicle-marker',
                html: `<div style="
                    background-color: ${status === 'available' ? '#4CAF50' : '#FF9800'};
                    width: 28px;
                    height: 28px;
                    border-radius: 6px;
                    border: 2px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                ">${vehicleEmojis[type] || '🚗'}</div>`,
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });
        });
    }

    /**
     * Load initial data from API
     */
    async loadData() {
        try {
            await Promise.all([
                this.loadIncidents(),
                this.loadVehicles()
            ]);
            this.updateDashboardStats();
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please refresh the page.');
        }
    }

    /**
     * Load coverage analysis and display on map
     */
    async loadCoverageAnalysis() {
        try {
            const response = await fetch(`${this.apiUrl}/coverage/analyze/`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load coverage: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayCoverageZones(data);
            
            console.log(`Loaded coverage analysis: ${data.summary.total_facilities} facilities, ${data.summary.total_counties} counties`);
            return data;
        } catch (error) {
            console.error('Error loading coverage:', error);
            throw error;
        }
    }

    /**
     * Display coverage zones on the map
     */
    displayCoverageZones(coverageData) {
        this.coverageLayer.clearLayers();
        
        // Define colors for different response time zones
        const zoneColors = {
            5: { fillColor: '#22c55e', color: '#16a34a', label: '5 min' },   // Green
            10: { fillColor: '#eab308', color: '#ca8a04', label: '10 min' }, // Yellow
            15: { fillColor: '#f97316', color: '#ea580c', label: '15 min' }  // Orange
        };
        
        // Add coverage zones (add in reverse order so 5-min is on top)
        const sortedZones = [...(coverageData.coverage_zones || [])].sort((a, b) => b.response_time - a.response_time);
        
        sortedZones.forEach(zone => {
            if (zone.geometry && zone.geometry.coordinates) {
                const colorScheme = zoneColors[zone.response_time] || { fillColor: '#94a3b8', color: '#64748b' };
                
                const layer = L.geoJSON(zone.geometry, {
                    style: {
                        fillColor: colorScheme.fillColor,
                        fillOpacity: 0.25,
                        color: colorScheme.color,
                        weight: 1,
                        opacity: 0.5
                    }
                }).bindPopup(`
                    <strong>${zone.response_time} Minute Coverage Zone</strong><br>
                    <small>Based on emergency facility locations</small>
                `);
                
                layer.addTo(this.coverageLayer);
            }
        });
        
        // Highlight gaps/underserved areas
        if (coverageData.gaps) {
            coverageData.gaps.forEach(gap => {
                if (gap.geometry && gap.severity === 'high') {
                    L.geoJSON(gap.geometry, {
                        style: {
                            fillColor: '#ef4444',
                            fillOpacity: 0.35,
                            color: '#dc2626',
                            weight: 2,
                            dashArray: '5, 5'
                        }
                    }).bindPopup(`
                        <strong>Coverage Gap</strong><br>
                        ${gap.description || 'Area with limited emergency service coverage'}
                    `).addTo(this.coverageLayer);
                }
            });
        }
    }

    /**
     * Toggle coverage layer visibility
     */
    toggleCoverageLayer(show) {
        if (show) {
            this.map.addLayer(this.coverageLayer);
        } else {
            this.map.removeLayer(this.coverageLayer);
        }
    }

    /**
     * Load incidents from API
     */
    async loadIncidents() {
        const response = await fetch(`${this.apiUrl}/incidents/geojson/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load incidents: ${response.status}`);
        }
        
        const data = await response.json();
        this.incidentLayer.clearLayers();
        this.incidents.clear();
        
        // Handle nested FeatureCollection
        const features = data.features?.features || data.features || [];
        
        features.forEach(feature => {
            const incident = {
                id: feature.id,
                ...feature.properties,
                coordinates: feature.geometry.coordinates
            };
            
            this.incidents.set(incident.id, incident);
            this.addIncidentMarker(incident);
        });
        
        console.log(`Loaded ${this.incidents.size} incidents`);
    }

    /**
     * Load vehicles from API
     */
    async loadVehicles() {
        const response = await fetch(`${this.apiUrl}/vehicles/geojson/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load vehicles: ${response.status}`);
        }
        
        const data = await response.json();
        this.vehicleLayer.clearLayers();
        this.vehicles.clear();
        
        // Handle nested FeatureCollection
        const features = data.features?.features || data.features || [];
        
        features.forEach(feature => {
            const vehicle = {
                id: feature.id,
                ...feature.properties,
                coordinates: feature.geometry.coordinates
            };
            
            this.vehicles.set(vehicle.id, vehicle);
            this.addVehicleMarker(vehicle);
        });
        
        console.log(`Loaded ${this.vehicles.size} vehicles`);
    }

    /**
     * Add incident marker to map
     */
    addIncidentMarker(incident) {
        if (!incident.coordinates) return;
        
        const [lng, lat] = incident.coordinates;
        const iconFn = this.incidentIcons[incident.incident_type] || this.incidentIcons.other;
        const icon = iconFn(incident.priority);
        
        const marker = L.marker([lat, lng], { icon })
            .bindPopup(this.createIncidentPopup(incident))
            .addTo(this.incidentLayer);
        
        marker.on('click', () => this.selectIncident(incident));
        marker.incidentId = incident.id;
    }

    /**
     * Add vehicle marker to map
     */
    addVehicleMarker(vehicle) {
        if (!vehicle.coordinates) return;
        
        const [lng, lat] = vehicle.coordinates;
        const iconFn = this.vehicleIcons[vehicle.vehicle_type] || this.vehicleIcons.rescue;
        const icon = iconFn(vehicle.status);
        
        const marker = L.marker([lat, lng], { icon })
            .bindPopup(this.createVehiclePopup(vehicle))
            .addTo(this.vehicleLayer);
        
        marker.on('click', () => this.selectVehicle(vehicle));
        marker.vehicleId = vehicle.id;
    }

    /**
     * Create incident popup content
     */
    createIncidentPopup(incident) {
        return `
            <div class="incident-popup">
                <h4>${incident.title || incident.incident_number}</h4>
                <p><strong>Type:</strong> ${incident.incident_type}</p>
                <p><strong>Priority:</strong> ${incident.priority}</p>
                <p><strong>Status:</strong> ${incident.status}</p>
                <p><strong>Reported:</strong> ${new Date(incident.reported_at).toLocaleString()}</p>
                ${incident.description ? `<p>${incident.description}</p>` : ''}
                <button class="btn btn-primary btn-sm" onclick="dashboard.showIncidentDetails(${incident.id})">
                    View Details
                </button>
            </div>
        `;
    }

    /**
     * Create vehicle popup content
     */
    createVehiclePopup(vehicle) {
        return `
            <div class="vehicle-popup">
                <h4>${vehicle.call_sign}</h4>
                <p><strong>Type:</strong> ${vehicle.vehicle_type}</p>
                <p><strong>Status:</strong> ${vehicle.status}</p>
                ${vehicle.home_station_name ? `<p><strong>Station:</strong> ${vehicle.home_station_name}</p>` : ''}
                <button class="btn btn-primary btn-sm" onclick="dashboard.showVehicleDetails(${vehicle.id})">
                    View Details
                </button>
            </div>
        `;
    }

    /**
     * Select an incident
     */
    selectIncident(incident) {
        this.selectedIncident = incident;
        this.updateIncidentPanel(incident);
        
        // Highlight on map
        this.highlightIncident(incident.id);
    }

    /**
     * Select a vehicle
     */
    selectVehicle(vehicle) {
        this.selectedVehicle = vehicle;
        this.updateVehiclePanel(vehicle);
        
        // If an incident is selected, show route
        if (this.selectedIncident) {
            this.showRouteToIncident(vehicle, this.selectedIncident);
        }
    }

    /**
     * Show route from vehicle to incident
     */
    async showRouteToIncident(vehicle, incident) {
        try {
            const vehicleLocation = {
                lat: vehicle.coordinates[1],
                lng: vehicle.coordinates[0]
            };
            const incidentLocation = {
                lat: incident.coordinates[1],
                lng: incident.coordinates[0]
            };
            
            await this.routing.showVehicleToIncident(
                [vehicleLocation.lat, vehicleLocation.lng],
                [incidentLocation.lat, incidentLocation.lng],
                {
                    originLabel: `Vehicle: ${vehicle.call_sign}`,
                    destinationLabel: `Incident: ${incident.incident_number}`
                }
            );
            
            // Show route stats
            const stats = this.routing.getRouteStats();
            if (stats) {
                this.showRouteInfo(stats);
            }
        } catch (error) {
            console.error('Error showing route:', error);
            this.showError('Could not calculate route');
        }
    }

    /**
     * Setup WebSocket connections
     */
    setupWebSockets() {
        if (!window.wsManager) {
            console.warn('WebSocket manager not available');
            return;
        }
        
        // Connect to channels
        wsManager.connectIncidents();
        wsManager.connectVehicles();
        wsManager.connectDispatch();
        
        // Handle incident updates
        wsManager.onMessage('incidents', (data) => {
            if (data.type === 'incident_update') {
                this.handleIncidentUpdate(data.incident);
            }
        });
        
        // Handle vehicle updates
        wsManager.onMessage('vehicles', (data) => {
            if (data.type === 'location_update') {
                this.handleVehicleLocationUpdate(data.vehicle_id, data.location);
            }
        });
        
        // Handle dispatch updates
        wsManager.onMessage('dispatch', (data) => {
            if (data.type === 'new_incident') {
                this.handleNewIncident(data.incident);
            } else if (data.type === 'dispatch_update') {
                this.handleDispatchUpdate(data);
            }
        });
    }

    /**
     * Handle incident update from WebSocket
     */
    handleIncidentUpdate(incidentData) {
        const incident = this.incidents.get(incidentData.id);
        if (incident) {
            Object.assign(incident, incidentData);
            this.updateIncidentMarker(incident);
        } else {
            this.incidents.set(incidentData.id, incidentData);
            this.addIncidentMarker(incidentData);
        }
        this.updateDashboardStats();
    }

    /**
     * Handle new incident from WebSocket
     */
    handleNewIncident(incidentData) {
        this.incidents.set(incidentData.id, incidentData);
        this.addIncidentMarker(incidentData);
        this.updateDashboardStats();
        
        // Show notification
        this.showNotification('New Incident', incidentData.title, 'warning');
    }

    /**
     * Handle vehicle location update from WebSocket
     */
    handleVehicleLocationUpdate(vehicleId, location) {
        const vehicle = this.vehicles.get(vehicleId);
        if (vehicle) {
            vehicle.coordinates = [location.lng, location.lat];
            this.updateVehicleMarker(vehicle);
        }
    }

    /**
     * Update incident marker on map
     */
    updateIncidentMarker(incident) {
        // Remove old marker
        this.incidentLayer.eachLayer(layer => {
            if (layer.incidentId === incident.id) {
                this.incidentLayer.removeLayer(layer);
            }
        });
        
        // Add updated marker
        this.addIncidentMarker(incident);
    }

    /**
     * Update vehicle marker on map
     */
    updateVehicleMarker(vehicle) {
        // Remove old marker
        this.vehicleLayer.eachLayer(layer => {
            if (layer.vehicleId === vehicle.id) {
                this.vehicleLayer.removeLayer(layer);
            }
        });
        
        // Add updated marker
        this.addVehicleMarker(vehicle);
    }

    /**
     * Highlight an incident on the map
     */
    highlightIncident(incidentId) {
        this.incidentLayer.eachLayer(layer => {
            if (layer.incidentId === incidentId) {
                layer.openPopup();
            }
        });
    }

    /**
     * Update dashboard statistics panel
     */
    updateDashboardStats() {
        // Count incidents by status
        const activeIncidents = Array.from(this.incidents.values())
            .filter(i => !['resolved', 'cancelled'].includes(i.status));
        const pendingIncidents = activeIncidents.filter(i => i.status === 'pending');
        const criticalIncidents = activeIncidents.filter(i => i.priority === 'critical');
        
        // Count vehicles by status
        const availableVehicles = Array.from(this.vehicles.values())
            .filter(v => v.status === 'available');
        
        // Update UI elements
        this.updateStatElement('active-incidents-count', activeIncidents.length);
        this.updateStatElement('pending-incidents-count', pendingIncidents.length);
        this.updateStatElement('critical-incidents-count', criticalIncidents.length);
        this.updateStatElement('available-vehicles-count', availableVehicles.length);
        this.updateStatElement('total-vehicles-count', this.vehicles.size);
    }

    /**
     * Update a stat element in the UI
     */
    updateStatElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Update incident details panel
     */
    updateIncidentPanel(incident) {
        const panel = document.getElementById('incident-details-panel');
        if (panel) {
            panel.innerHTML = `
                <h5>${incident.incident_number}</h5>
                <p><strong>${incident.title}</strong></p>
                <div class="mb-2">
                    <span class="badge bg-${this.getPriorityColor(incident.priority)}">${incident.priority}</span>
                    <span class="badge bg-${this.getStatusColor(incident.status)}">${incident.status}</span>
                    <span class="badge bg-secondary">${incident.incident_type}</span>
                </div>
                <p class="small">${incident.description || 'No description'}</p>
                <button class="btn btn-primary btn-sm" onclick="dashboard.assignVehicle(${incident.id})">
                    Assign Vehicle
                </button>
                <button class="btn btn-secondary btn-sm" onclick="dashboard.viewIncidentHistory(${incident.id})">
                    View History
                </button>
            `;
            panel.style.display = 'block';
        }
    }

    /**
     * Update vehicle details panel
     */
    updateVehiclePanel(vehicle) {
        const panel = document.getElementById('vehicle-details-panel');
        if (panel) {
            panel.innerHTML = `
                <h5>${vehicle.call_sign}</h5>
                <p><strong>Type:</strong> ${vehicle.vehicle_type}</p>
                <div class="mb-2">
                    <span class="badge bg-${this.getVehicleStatusColor(vehicle.status)}">${vehicle.status}</span>
                </div>
                ${vehicle.home_station_name ? `<p class="small">Station: ${vehicle.home_station_name}</p>` : ''}
                <button class="btn btn-primary btn-sm" onclick="dashboard.trackVehicle(${vehicle.id})">
                    Track Vehicle
                </button>
            `;
            panel.style.display = 'block';
        }
    }

    /**
     * Show route info panel
     */
    showRouteInfo(stats) {
        const panel = document.getElementById('route-info-panel');
        if (panel) {
            panel.innerHTML = `
                <h6>Route Information</h6>
                <p><strong>Distance:</strong> ${stats.formattedDistance}</p>
                <p><strong>ETA:</strong> ${stats.formattedDuration}</p>
                <button class="btn btn-sm btn-outline-secondary" onclick="dashboard.clearRoute()">
                    Clear Route
                </button>
            `;
            panel.style.display = 'block';
        }
    }

    /**
     * Clear current route
     */
    clearRoute() {
        if (this.routing) {
            this.routing.clearRoute();
        }
        const panel = document.getElementById('route-info-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    /**
     * Get priority badge color
     */
    getPriorityColor(priority) {
        const colors = {
            critical: 'danger',
            high: 'warning',
            medium: 'info',
            low: 'secondary'
        };
        return colors[priority] || 'secondary';
    }

    /**
     * Get status badge color
     */
    getStatusColor(status) {
        const colors = {
            pending: 'warning',
            dispatched: 'info',
            en_route: 'primary',
            on_scene: 'success',
            resolved: 'secondary',
            cancelled: 'dark'
        };
        return colors[status] || 'secondary';
    }

    /**
     * Get vehicle status badge color
     */
    getVehicleStatusColor(status) {
        const colors = {
            available: 'success',
            dispatched: 'info',
            en_route: 'primary',
            on_scene: 'warning',
            out_of_service: 'danger'
        };
        return colors[status] || 'secondary';
    }

    /**
     * Setup event handlers
     */
    setupEventHandlers() {
        // Filter controls
        document.querySelectorAll('[data-filter-type]').forEach(el => {
            el.addEventListener('change', () => this.applyFilters());
        });
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        }
    }

    /**
     * Apply filters to displayed data
     */
    applyFilters() {
        const typeFilter = document.getElementById('filter-type')?.value || 'all';
        const statusFilter = document.getElementById('filter-status')?.value || 'all';
        const priorityFilter = document.getElementById('filter-priority')?.value || 'all';
        
        this.incidentLayer.clearLayers();
        
        this.incidents.forEach(incident => {
            const matchesType = typeFilter === 'all' || incident.incident_type === typeFilter;
            const matchesStatus = statusFilter === 'all' || incident.status === statusFilter;
            const matchesPriority = priorityFilter === 'all' || incident.priority === priorityFilter;
            
            if (matchesType && matchesStatus && matchesPriority) {
                this.addIncidentMarker(incident);
            }
        });
    }

    /**
     * Start periodic data updates (fallback)
     */
    startPeriodicUpdates() {
        // Update every 30 seconds as fallback
        this.updateIntervals.push(
            setInterval(() => this.loadData(), 30000)
        );
    }

    /**
     * Stop periodic updates
     */
    stopPeriodicUpdates() {
        this.updateIntervals.forEach(interval => clearInterval(interval));
        this.updateIntervals = [];
    }

    /**
     * Show notification
     */
    showNotification(title, message, type = 'info') {
        console.log(`Notification [${type}]: ${title} - ${message}`);
        
        // If browser supports notifications
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error(message);
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }

    /**
     * Show incident details modal
     */
    showIncidentDetails(incidentId) {
        const incident = this.incidents.get(incidentId);
        if (incident) {
            console.log('Show details for incident:', incident);
            this.selectIncident(incident);
        }
    }

    /**
     * Show vehicle details modal
     */
    showVehicleDetails(vehicleId) {
        const vehicle = this.vehicles.get(vehicleId);
        if (vehicle) {
            console.log('Show details for vehicle:', vehicle);
            this.selectVehicle(vehicle);
        }
    }

    /**
     * Assign vehicle to selected incident
     */
    async assignVehicle(incidentId) {
        if (!this.selectedVehicle) {
            this.showError('Please select a vehicle first');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/incidents/${incidentId}/assign_vehicle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                credentials: 'include',
                body: JSON.stringify({
                    vehicle_id: this.selectedVehicle.id
                })
            });
            
            if (!response.ok) {
                throw new Error(`Assignment failed: ${response.status}`);
            }
            
            this.showNotification('Success', 'Vehicle assigned to incident', 'success');
            await this.loadData();
        } catch (error) {
            console.error('Error assigning vehicle:', error);
            this.showError('Failed to assign vehicle');
        }
    }

    /**
     * Track a vehicle
     */
    trackVehicle(vehicleId) {
        const vehicle = this.vehicles.get(vehicleId);
        if (vehicle && vehicle.coordinates) {
            this.map.setView([vehicle.coordinates[1], vehicle.coordinates[0]], 15);
        }
    }

    /**
     * View incident history
     */
    viewIncidentHistory(incidentId) {
        console.log('View history for incident:', incidentId);
        // TODO: Implement history view
    }

    /**
     * Get CSRF token
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

    /**
     * Cleanup on page unload
     */
    destroy() {
        this.stopPeriodicUpdates();
        if (window.wsManager) {
            wsManager.disconnectAll();
        }
    }
}

// Create global dashboard instance when DOM is ready
let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the dashboard page
    if (document.getElementById('dispatch-map')) {
        dashboard = new DashboardController();
        dashboard.init().catch(error => {
            console.error('Failed to initialize dashboard:', error);
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (dashboard) {
                dashboard.destroy();
            }
        });
    }
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardController;
}
