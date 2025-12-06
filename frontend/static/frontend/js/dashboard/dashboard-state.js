/**
 * Dashboard State Management
 * 
 * Centralized state for incidents, vehicles, and selections
 */

export const DashboardState = {
  incidents: [],
  vehicles: [],
  activeRoutes: [],
  selectedIncident: null,
  currentUser: null,
  filters: {
    status: '',
    severity: '',
    type: ''
  },

  /**
   * Update incidents
   */
  setIncidents(incidents) {
    this.incidents = incidents;
    this.notifyListeners('incidents');
  },

  /**
   * Update vehicles
   */
  setVehicles(vehicles) {
    this.vehicles = vehicles;
    this.notifyListeners('vehicles');
  },

  /**
   * Update active routes
   */
  setActiveRoutes(routes) {
    this.activeRoutes = routes;
    this.notifyListeners('activeRoutes');
  },

  /**
   * Set selected incident
   */
  selectIncident(incident) {
    this.selectedIncident = incident;
    this.notifyListeners('selectedIncident');
  },

  /**
   * Set current user
   */
  setCurrentUser(user) {
    this.currentUser = user;
    this.notifyListeners('currentUser');
  },

  /**
   * Update filters
   */
  setFilters(filters) {
    this.filters = { ...this.filters, ...filters };
    this.notifyListeners('filters');
  },

  /**
   * Get filtered incidents
   */
  getFilteredIncidents() {
    return this.incidents.filter(incident => {
      const statusMatch = !this.filters.status || incident.properties.status === this.filters.status;
      const severityMatch = !this.filters.severity || incident.properties.severity === this.filters.severity;
      const typeMatch = !this.filters.type || incident.properties.incident_type === this.filters.type;
      return statusMatch && severityMatch && typeMatch;
    });
  },

  /**
   * Get incident by ID
   */
  getIncidentById(id) {
    // GeoJSON features have id at top level, not in properties
    return this.incidents.find(inc => inc.id === id || inc.id === parseInt(id));
  },

  /**
   * Get vehicle by ID
   */
  getVehicleById(id) {
    // GeoJSON features have id at top level, not in properties
    return this.vehicles.find(veh => veh.id === id || veh.id === parseInt(id));
  },

  /**
   * Get statistics
   */
  getStats() {
    const activeIncidents = this.incidents.filter(inc => 
      inc.properties.status !== 'resolved' && inc.properties.status !== 'cancelled'
    );
    const availableVehicles = this.vehicles.filter(veh => 
      veh.properties.status === 'available'
    );
    const onScene = this.incidents.filter(inc => 
      inc.properties.status === 'on_scene'
    );

    return {
      active: activeIncidents.length,
      available: availableVehicles.length,
      onScene: onScene.length
    };
  },

  // Listener management
  listeners: {},

  addListener(key, callback) {
    if (!this.listeners[key]) {
      this.listeners[key] = [];
    }
    this.listeners[key].push(callback);
  },

  notifyListeners(key) {
    if (this.listeners[key]) {
      this.listeners[key].forEach(callback => callback(this));
    }
    // Also notify 'all' listeners
    if (this.listeners.all) {
      this.listeners.all.forEach(callback => callback(this, key));
    }
  }
};
