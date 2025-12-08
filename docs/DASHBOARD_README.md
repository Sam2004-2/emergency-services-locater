# Emergency Services Locator - Enhanced Dashboard

A Django/PostGIS-based emergency services locator for Ireland with real-time incident management, routing, and PWA support.

## 🚀 New Features (Phase 1-5 Complete)

### ✅ Phase 1: User Authentication
- Role-based access control (Admin, Dispatcher, Responder, Viewer)
- Custom login/logout views
- User profile with role badges

### ✅ Phase 2: Incidents Backend
- **Models**: Incident, Vehicle, Dispatch with PostGIS spatial support
- **API**: Full CRUD operations for incidents, vehicles, and dispatches
- **OSRM Routing**: Real-time route calculation between points
- **Spatial Queries**: Nearest facility, within radius, active incidents

### ✅ Phase 3: Dashboard Frontend
- Real-time incident dashboard with live updates every 15 seconds
- Interactive Leaflet map with incident and vehicle markers
- Filterable incident list (status, severity, type)
- Dispatch workflow: Create incidents → Assign vehicles → Track progress
- Status updates: Pending → Dispatched → En Route → On Scene → Resolved

### ✅ Phase 4: PWA Implementation
- Full Progressive Web App support
- Offline-capable with service worker
- Installable on desktop and mobile
- App shortcuts to Map and Dashboard
- Manifest with custom icons

### ✅ Phase 5: Docker Improvements
- Redis integration for caching
- Health checks for all services
- docker-compose.override.yml for development
- PgAdmin on debug profile only

## 📁 Project Structure

```
webmapping_ass/
├── accounts/              # User authentication & profiles
│   ├── models.py         # UserProfile with roles
│   ├── views.py          # Login/logout, CurrentUserAPIView
│   └── permissions.py    # DRF permission classes
├── incidents/            # Incident management
│   ├── models.py         # Incident, Vehicle, Dispatch
│   ├── api.py            # ViewSets & custom actions
│   ├── serializers.py    # DRF serializers
│   ├── routing.py        # OSRM routing service
│   └── management/       # Simulation commands
│       └── commands/
│           ├── generate_incidents.py
│           └── simulate_vehicles.py
├── frontend/
│   ├── templates/
│   │   └── frontend/
│   │       ├── base.html       # Shared layout with nav & PWA
│   │       ├── login.html      # Login page
│   │       ├── map.html        # Facilities map
│   │       └── dashboard.html  # Incident dashboard
│   └── static/frontend/
│       ├── css/
│       │   ├── dashboard.css   # Dashboard styles
│       │   └── map.css         # Map styles
│       ├── js/
│       │   ├── dashboard/      # Dashboard modules (7 files)
│       │   │   ├── dashboard.js          # Main entry point
│       │   │   ├── dashboard-api.js      # API client
│       │   │   ├── dashboard-state.js    # State management
│       │   │   ├── dashboard-map.js      # Map rendering
│       │   │   ├── dashboard-list.js     # Incident list
│       │   │   ├── dashboard-forms.js    # Modals & forms
│       │   │   └── dashboard-polling.js  # Live updates
│       │   └── sw.js           # Service worker
│       ├── manifest.json       # PWA manifest
│       └── icons/              # PWA icons (to be generated)
├── docker-compose.yml          # Production configuration
├── docker-compose.override.yml # Development overrides
└── requirements.txt            # Python dependencies
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ with PostGIS 3.4
- Docker & Docker Compose (optional but recommended)

### Local Development (without Docker)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up database:**
```bash
createdb es_locator
psql es_locator -c "CREATE EXTENSION postgis;"
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run migrations:**
```bash
python3 manage.py migrate
```

5. **Create superuser:**
```bash
python3 manage.py createsuperuser
```

6. **Load sample data:**
```bash
python3 manage.py import_counties
python3 manage.py import_facilities
python3 manage.py generate_incidents --count 20
python3 manage.py simulate_vehicles --create-vehicles
```

7. **Generate PWA icons:**
```bash
cd frontend/static/frontend
python3 generate_icons.py
```

8. **Collect static files:**
```bash
python3 manage.py collectstatic --noinput
```

9. **Run development server:**
```bash
python3 manage.py runserver
```

### Docker Development

1. **Start services:**
```bash
docker-compose up
```

2. **Run migrations (in another terminal):**
```bash
docker-compose exec web python manage.py migrate
```

3. **Create superuser:**
```bash
docker-compose exec web python manage.py createsuperuser
```

4. **Load sample data:**
```bash
docker-compose exec web python manage.py import_counties
docker-compose exec web python manage.py import_facilities
docker-compose exec web python manage.py generate_incidents --count 20
docker-compose exec web python manage.py simulate_vehicles --create-vehicles
```

5. **Access the app:**
- Main app: http://localhost
- Dashboard: http://localhost/dashboard/
- Admin: http://localhost/admin/
- API: http://localhost/api/

### Production Docker

```bash
# Start without debug services
docker-compose -f docker-compose.yml up -d

# Or with PgAdmin for debugging
docker-compose --profile debug up -d
```

## 🎮 Usage

### Dashboard Features

#### For Dispatchers:
1. **Create Incidents:**
   - Click "Create Incident" button
   - Fill in details (type, severity, location)
   - Click on map to set coordinates
   - Submit to create

2. **Dispatch Vehicles:**
   - Select an incident from the list
   - Click "Dispatch Vehicle"
   - Choose available vehicle
   - Optionally assign responder
   - Vehicle will route to incident

3. **Monitor Progress:**
   - Watch real-time updates every 15 seconds
   - Track vehicle positions on map
   - View incident status changes
   - See route polylines

#### For Responders:
1. **View Assigned Incidents:**
   - See incidents assigned to you
   - Update status: En Route → On Scene → Resolved
   - View route and distance

#### For Viewers:
1. **Monitor Incidents:**
   - View all active incidents
   - Filter by status, severity, type
   - See live vehicle positions
   - Read-only access

### Simulation Commands

#### Generate Demo Incidents:
```bash
python3 manage.py generate_incidents --count 20 --clear
```

Options:
- `--count N`: Number of incidents to generate
- `--clear`: Delete existing incidents first

#### Simulate Vehicle Movement:
```bash
python3 manage.py simulate_vehicles --duration 120 --interval 5 --create-vehicles
```

Options:
- `--duration N`: Simulation duration in seconds
- `--interval N`: Update interval in seconds
- `--create-vehicles`: Create demo vehicles first

## 🔌 API Endpoints

### Incidents
- `GET /api/incidents/` - List all incidents
- `POST /api/incidents/` - Create incident (Dispatcher only)
- `GET /api/incidents/{id}/` - Get incident details
- `PATCH /api/incidents/{id}/` - Update incident
- `GET /api/incidents/active/` - List active incidents
- `POST /api/incidents/{id}/dispatch/` - Dispatch vehicle (Dispatcher)
- `POST /api/incidents/{id}/update-status/` - Update status (Responder/Dispatcher)
- `GET /api/incidents/{id}/route/` - Get OSRM route

### Vehicles
- `GET /api/vehicles/` - List all vehicles
- `GET /api/vehicles/available/` - List available vehicles
- `GET /api/vehicles/available/?type=ambulance` - Filter by type

### Dispatches
- `GET /api/dispatches/` - List dispatch records
- `POST /api/dispatches/{id}/acknowledge/` - Acknowledge dispatch (Responder)
- `POST /api/dispatches/{id}/arrive/` - Mark arrival (Responder)
- `POST /api/dispatches/{id}/complete/` - Complete dispatch (Responder/Dispatcher)

### Authentication
- `GET /api/auth/me/` - Get current user info
- `POST /accounts/login/` - Login
- `POST /accounts/logout/` - Logout

## 🎨 Key Technologies

- **Backend:** Django 5.0, Django REST Framework, PostGIS
- **Frontend:** Vanilla JavaScript (ES6 modules), Bootstrap 5, Leaflet.js
- **Database:** PostgreSQL 16 + PostGIS 3.4
- **Caching:** Redis 7
- **Routing:** OSRM (Open Source Routing Machine)
- **Deployment:** Docker, Nginx, Gunicorn
- **PWA:** Service Worker, Web App Manifest

## 🧪 Testing

Run tests:
```bash
python3 manage.py test
```

Run specific app tests:
```bash
python3 manage.py test incidents
python3 manage.py test accounts
```

## 🔒 Security Notes

1. **Change default secrets** in production
2. **Set strong passwords** for superuser and database
3. **Configure ALLOWED_HOSTS** properly
4. **Enable HTTPS** in production
5. **Review CORS settings** if needed

## 📱 PWA Installation

### Desktop (Chrome/Edge):
1. Visit the site
2. Look for install icon in address bar
3. Click "Install ES Locator"

### Mobile:
1. Open in browser
2. Tap "Add to Home Screen"
3. Confirm installation

### Features When Installed:
- Standalone app window
- Offline map tile caching
- Background sync
- Push notifications (future)

## 🐛 Troubleshooting

### Static files not loading:
```bash
python3 manage.py collectstatic --clear --noinput
```

### PostGIS not found:
```bash
# Install PostGIS extension
psql es_locator -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Icons not showing:
```bash
cd frontend/static/frontend
pip install Pillow
python3 generate_icons.py
```

### Service worker not updating:
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Update CACHE_VERSION in sw.js

## 📝 License

MIT License - See LICENSE file for details

## 👥 Credits

Developed for Advanced Web Mapping Assignment
- OpenStreetMap contributors for map tiles
- OSRM project for routing
- Leaflet.js for mapping library
- Bootstrap for UI components
