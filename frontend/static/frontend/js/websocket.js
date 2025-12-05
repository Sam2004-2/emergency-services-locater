/**
 * WebSocket Manager for Real-time Incident Updates
 * 
 * Manages WebSocket connections for incidents, vehicles, and dispatch updates.
 */

class WebSocketManager {
    constructor() {
        this.connections = {};
        this.reconnectAttempts = {};
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = {
            incidents: [],
            vehicles: [],
            dispatch: []
        };
    }

    /**
     * Get WebSocket URL for a given channel
     */
    getWebSocketUrl(channel) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/${channel}/`;
    }

    /**
     * Connect to incidents WebSocket channel
     */
    connectIncidents() {
        return this.connect('incidents');
    }

    /**
     * Connect to vehicles WebSocket channel
     */
    connectVehicles() {
        return this.connect('vehicles');
    }

    /**
     * Connect to dispatch WebSocket channel
     */
    connectDispatch() {
        return this.connect('dispatch');
    }

    /**
     * Generic connect method for any channel
     */
    connect(channel) {
        if (this.connections[channel]) {
            console.log(`Already connected to ${channel}`);
            return this.connections[channel];
        }

        const url = this.getWebSocketUrl(channel);
        console.log(`Connecting to WebSocket: ${url}`);

        try {
            const ws = new WebSocket(url);
            this.connections[channel] = ws;
            this.reconnectAttempts[channel] = 0;

            ws.onopen = () => {
                console.log(`WebSocket ${channel} connected`);
                this.reconnectAttempts[channel] = 0;
                this.notifyHandlers(channel, { type: 'connected' });
            };

            ws.onclose = (event) => {
                console.log(`WebSocket ${channel} closed:`, event);
                delete this.connections[channel];
                this.notifyHandlers(channel, { type: 'disconnected' });
                
                // Attempt reconnection
                if (this.reconnectAttempts[channel] < this.maxReconnectAttempts) {
                    this.reconnectAttempts[channel]++;
                    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts[channel] - 1);
                    console.log(`Reconnecting ${channel} in ${delay}ms (attempt ${this.reconnectAttempts[channel]})`);
                    setTimeout(() => this.connect(channel), delay);
                }
            };

            ws.onerror = (error) => {
                console.error(`WebSocket ${channel} error:`, error);
                this.notifyHandlers(channel, { type: 'error', error });
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log(`WebSocket ${channel} message:`, data);
                    this.notifyHandlers(channel, data);
                } catch (e) {
                    console.error(`Error parsing WebSocket message:`, e);
                }
            };

            return ws;
        } catch (error) {
            console.error(`Failed to connect to WebSocket ${channel}:`, error);
            return null;
        }
    }

    /**
     * Disconnect from a channel
     */
    disconnect(channel) {
        if (this.connections[channel]) {
            this.connections[channel].close();
            delete this.connections[channel];
        }
    }

    /**
     * Disconnect from all channels
     */
    disconnectAll() {
        Object.keys(this.connections).forEach(channel => this.disconnect(channel));
    }

    /**
     * Send a message to a channel
     */
    send(channel, message) {
        const ws = this.connections[channel];
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
            return true;
        }
        console.warn(`Cannot send to ${channel}: not connected`);
        return false;
    }

    /**
     * Subscribe an incident for updates
     */
    subscribeIncident(incidentId) {
        return this.send('incidents', {
            action: 'subscribe',
            incident_id: incidentId
        });
    }

    /**
     * Unsubscribe from incident updates
     */
    unsubscribeIncident(incidentId) {
        return this.send('incidents', {
            action: 'unsubscribe',
            incident_id: incidentId
        });
    }

    /**
     * Subscribe a vehicle for tracking
     */
    subscribeVehicle(vehicleId) {
        return this.send('vehicles', {
            action: 'subscribe',
            vehicle_id: vehicleId
        });
    }

    /**
     * Update vehicle location
     */
    updateVehicleLocation(vehicleId, lat, lng) {
        return this.send('vehicles', {
            action: 'update_location',
            vehicle_id: vehicleId,
            lat: lat,
            lng: lng
        });
    }

    /**
     * Join dispatch room for area monitoring
     */
    joinDispatchRoom(areaCode = 'national') {
        return this.send('dispatch', {
            action: 'join_room',
            area: areaCode
        });
    }

    /**
     * Send dispatch command
     */
    dispatch(incidentId, vehicleId) {
        return this.send('dispatch', {
            action: 'dispatch',
            incident_id: incidentId,
            vehicle_id: vehicleId
        });
    }

    /**
     * Add a message handler for a channel
     */
    onMessage(channel, handler) {
        if (!this.messageHandlers[channel]) {
            this.messageHandlers[channel] = [];
        }
        this.messageHandlers[channel].push(handler);
        return () => this.removeHandler(channel, handler);
    }

    /**
     * Remove a message handler
     */
    removeHandler(channel, handler) {
        if (this.messageHandlers[channel]) {
            this.messageHandlers[channel] = this.messageHandlers[channel]
                .filter(h => h !== handler);
        }
    }

    /**
     * Notify all handlers for a channel
     */
    notifyHandlers(channel, data) {
        if (this.messageHandlers[channel]) {
            this.messageHandlers[channel].forEach(handler => {
                try {
                    handler(data);
                } catch (e) {
                    console.error(`Error in handler for ${channel}:`, e);
                }
            });
        }
    }

    /**
     * Check if connected to a channel
     */
    isConnected(channel) {
        return this.connections[channel]?.readyState === WebSocket.OPEN;
    }

    /**
     * Get connection status for all channels
     */
    getStatus() {
        return {
            incidents: this.isConnected('incidents'),
            vehicles: this.isConnected('vehicles'),
            dispatch: this.isConnected('dispatch')
        };
    }
}

// Create global instance
window.wsManager = new WebSocketManager();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
}
