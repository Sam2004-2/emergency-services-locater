"""
WebSocket consumers for real-time incident and vehicle updates.

Uses Django Channels for WebSocket support.
"""
import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


logger = logging.getLogger(__name__)


class IncidentConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time incident updates.
    
    Connect: ws://host/ws/incidents/
    
    Messages received:
        - incident_created: New incident created
        - incident_updated: Incident status/details changed
        - incident_assigned: Vehicle assigned to incident
        - incident_completed: Incident marked complete
    
    Messages sent:
        - subscribe: Subscribe to specific incident(s)
        - unsubscribe: Unsubscribe from incident(s)
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Check authentication
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Join the incidents broadcast group
        self.group_name = 'incidents_all'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Track subscribed incidents
        self.subscribed_incidents = set()
        
        await self.accept()
        
        # Send current active incidents
        incidents = await self.get_active_incidents()
        await self.send_json({
            'type': 'initial_state',
            'incidents': incidents,
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the broadcast group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
        # Leave any specific incident groups
        for incident_id in self.subscribed_incidents:
            await self.channel_layer.group_discard(
                f'incident_{incident_id}',
                self.channel_name
            )
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if message_type == 'subscribe':
            incident_id = content.get('incident_id')
            if incident_id:
                await self.channel_layer.group_add(
                    f'incident_{incident_id}',
                    self.channel_name
                )
                self.subscribed_incidents.add(incident_id)
                await self.send_json({
                    'type': 'subscribed',
                    'incident_id': incident_id,
                })
        
        elif message_type == 'unsubscribe':
            incident_id = content.get('incident_id')
            if incident_id and incident_id in self.subscribed_incidents:
                await self.channel_layer.group_discard(
                    f'incident_{incident_id}',
                    self.channel_name
                )
                self.subscribed_incidents.discard(incident_id)
                await self.send_json({
                    'type': 'unsubscribed',
                    'incident_id': incident_id,
                })
    
    # Event handlers for channel layer messages
    async def incident_created(self, event):
        """Handle incident created event."""
        await self.send_json({
            'type': 'incident_created',
            'incident': event['incident'],
        })
    
    async def incident_updated(self, event):
        """Handle incident updated event."""
        await self.send_json({
            'type': 'incident_updated',
            'incident': event['incident'],
        })
    
    async def incident_assigned(self, event):
        """Handle incident assigned event."""
        await self.send_json({
            'type': 'incident_assigned',
            'incident': event['incident'],
            'vehicle': event.get('vehicle'),
            'route': event.get('route'),
        })
    
    async def incident_completed(self, event):
        """Handle incident completed event."""
        await self.send_json({
            'type': 'incident_completed',
            'incident_id': event['incident_id'],
        })
    
    @database_sync_to_async
    def get_active_incidents(self):
        """Get all active incidents."""
        from .models import Incident
        from .serializers import IncidentSerializer
        
        active_statuses = ['pending', 'dispatched', 'en_route', 'on_scene']
        incidents = Incident.objects.filter(
            status__in=active_statuses
        ).select_related('dispatcher')
        
        return IncidentSerializer(incidents, many=True).data


class VehicleConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time vehicle location updates.
    
    Connect: ws://host/ws/vehicles/
    
    Messages received:
        - vehicle_location: Vehicle location updated
        - vehicle_status: Vehicle status changed
    
    Messages sent:
        - update_location: Update vehicle location (for mobile units)
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        self.group_name = 'vehicles_all'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current vehicle positions
        vehicles = await self.get_available_vehicles()
        await self.send_json({
            'type': 'initial_state',
            'vehicles': vehicles,
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if message_type == 'update_location':
            vehicle_id = content.get('vehicle_id')
            latitude = content.get('latitude')
            longitude = content.get('longitude')
            
            if vehicle_id and latitude and longitude:
                await self.update_vehicle_location(vehicle_id, latitude, longitude)
                
                # Broadcast to all clients
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'vehicle_location',
                        'vehicle_id': vehicle_id,
                        'latitude': latitude,
                        'longitude': longitude,
                    }
                )
    
    async def vehicle_location(self, event):
        """Handle vehicle location event."""
        await self.send_json({
            'type': 'vehicle_location',
            'vehicle_id': event['vehicle_id'],
            'latitude': event['latitude'],
            'longitude': event['longitude'],
        })
    
    async def vehicle_status(self, event):
        """Handle vehicle status change event."""
        await self.send_json({
            'type': 'vehicle_status',
            'vehicle_id': event['vehicle_id'],
            'status': event['status'],
        })
    
    @database_sync_to_async
    def get_available_vehicles(self):
        """Get all vehicles with their current locations."""
        from .models import Vehicle
        from .serializers import VehicleSerializer
        
        vehicles = Vehicle.objects.filter(
            current_location__isnull=False
        )
        return VehicleSerializer(vehicles, many=True).data
    
    @database_sync_to_async
    def update_vehicle_location(self, vehicle_id, latitude, longitude):
        """Update vehicle location in database."""
        from .models import Vehicle
        from django.contrib.gis.geos import Point
        from django.utils import timezone
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle.current_location = Point(longitude, latitude, srid=4326)
            vehicle.location_updated_at = timezone.now()
            vehicle.save()
        except Vehicle.DoesNotExist:
            logger.warning(f"Vehicle {vehicle_id} not found for location update")


class DispatchConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for dispatcher dashboard.
    
    Connect: ws://host/ws/dispatch/
    
    Combines incidents and vehicles for unified dispatch view.
    Provides enhanced features for dispatchers.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        user = self.scope['user']
        if user == AnonymousUser():
            await self.close()
            return
        
        # Check if user is a dispatcher
        if not await self.is_dispatcher(user):
            await self.close()
            return
        
        # Join dispatch groups
        self.incidents_group = 'incidents_all'
        self.vehicles_group = 'vehicles_all'
        
        await self.channel_layer.group_add(
            self.incidents_group,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.vehicles_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard state
        dashboard_state = await self.get_dashboard_state()
        await self.send_json({
            'type': 'initial_state',
            **dashboard_state,
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.incidents_group,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.vehicles_group,
            self.channel_name
        )
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if message_type == 'request_assignment':
            # Dispatcher requests vehicle assignment
            incident_id = content.get('incident_id')
            vehicle_id = content.get('vehicle_id')
            
            if incident_id and vehicle_id:
                result = await self.process_assignment(incident_id, vehicle_id)
                await self.send_json({
                    'type': 'assignment_result',
                    **result,
                })
    
    # Forward incident and vehicle events
    async def incident_created(self, event):
        await self.send_json(event)
    
    async def incident_updated(self, event):
        await self.send_json(event)
    
    async def incident_assigned(self, event):
        await self.send_json(event)
    
    async def incident_completed(self, event):
        await self.send_json(event)
    
    async def vehicle_location(self, event):
        await self.send_json(event)
    
    async def vehicle_status(self, event):
        await self.send_json(event)
    
    @database_sync_to_async
    def is_dispatcher(self, user):
        """Check if user has dispatcher role."""
        return (
            user.is_staff or 
            user.groups.filter(name='Dispatchers').exists() or
            hasattr(user, 'dispatcher_profile')
        )
    
    @database_sync_to_async
    def get_dashboard_state(self):
        """Get full dashboard state."""
        from .models import Incident, Vehicle
        from .serializers import IncidentSerializer, VehicleSerializer
        
        active_statuses = ['pending', 'dispatched', 'en_route', 'on_scene']
        
        incidents = Incident.objects.filter(
            status__in=active_statuses
        ).select_related('assigned_vehicle', 'county')
        
        vehicles = Vehicle.objects.filter(
            is_active=True
        )
        
        # Summary stats
        pending_count = incidents.filter(status='pending').count()
        dispatched_count = incidents.filter(status='dispatched').count()
        available_vehicles = vehicles.filter(status='available').count()
        
        return {
            'incidents': IncidentSerializer(incidents, many=True).data,
            'vehicles': VehicleSerializer(vehicles, many=True).data,
            'stats': {
                'pending_incidents': pending_count,
                'dispatched_incidents': dispatched_count,
                'available_vehicles': available_vehicles,
                'total_vehicles': vehicles.count(),
            }
        }
    
    @database_sync_to_async
    def process_assignment(self, incident_id, vehicle_id):
        """Process a vehicle assignment request."""
        from .models import Incident, Vehicle, VehicleAssignment
        from .routing import routing_service
        from django.utils import timezone
        
        try:
            incident = Incident.objects.get(id=incident_id)
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except (Incident.DoesNotExist, Vehicle.DoesNotExist) as e:
            return {'success': False, 'error': str(e)}
        
        if vehicle.status != 'available':
            return {'success': False, 'error': 'Vehicle not available'}
        
        # Calculate route
        route_info = None
        if vehicle.current_location and incident.location:
            vehicle_loc = (vehicle.current_location.y, vehicle.current_location.x)
            incident_loc = (incident.location.y, incident.location.x)
            route = routing_service.calculate_route(vehicle_loc, incident_loc)
            if route:
                route_info = route.to_dict()
        
        # Create assignment
        user = self.scope['user']
        VehicleAssignment.objects.create(
            incident=incident,
            vehicle=vehicle,
            assigned_by=user,
            route_info=route_info,
        )
        
        # Update statuses
        incident.status = 'dispatched'
        incident.assigned_vehicle = vehicle
        incident.assigned_by = user
        incident.assigned_at = timezone.now()
        incident.save()
        
        vehicle.status = 'dispatched'
        vehicle.save()
        
        return {
            'success': True,
            'incident_id': incident_id,
            'vehicle_id': vehicle_id,
            'route': route_info,
        }


# Helper function to broadcast events from views/signals
async def broadcast_incident_event(event_type: str, incident_data: dict, **kwargs):
    """
    Broadcast an incident event to all connected clients.
    
    Call this from views or signals when incidents change.
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        'incidents_all',
        {
            'type': event_type,
            'incident': incident_data,
            **kwargs,
        }
    )


async def broadcast_vehicle_event(event_type: str, vehicle_id: int, **kwargs):
    """
    Broadcast a vehicle event to all connected clients.
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        'vehicles_all',
        {
            'type': event_type,
            'vehicle_id': vehicle_id,
            **kwargs,
        }
    )
