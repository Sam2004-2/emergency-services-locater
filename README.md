# Emergency Services Locator

A production-ready geospatial web application for locating and managing emergency services across Ireland. Features interactive mapping, real-time incident management, vehicle dispatch, and emergency response tracking with advanced spatial query capabilities.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
  - [Local Development Setup](#local-development-setup)
- [Usage](#usage)
  - [User Roles](#user-roles)
  - [Map Interface](#map-interface)
  - [Incident Dashboard](#incident-dashboard)
- [API Reference](#api-reference)
- [Mobile App](#mobile-app)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Emergency Services Locator enables emergency services personnel to:

- **Discover facilities** - Locate hospitals, fire stations, police stations, and ambulance bases
- **Manage incidents** - Create, track, and resolve emergency events
- **Dispatch vehicles** - Assign and route emergency vehicles to incidents
- **Track responses** - Monitor real-time vehicle locations and response status

---

## Features

### Interactive Mapping
- Full-screen responsive Leaflet.js map with OpenStreetMap tiles
- Geolocation support (find your current location)
- Drop pin mode for placing custom search points
- Draggable markers for flexible positioning
- County boundary overlays
- Dynamic radius visualization

### Spatial Queries
- **Proximity search** - Find the 5 nearest facilities
- **Radius search** - Search within 1-50 km customizable radius
- **County filtering** - Filter facilities by administrative boundary
- **Service type filtering** - Filter by hospital, fire, police, or ambulance

### Incident Management Dashboard
- Real-time monitoring with 15-second auto-refresh
- Interactive map with incident and vehicle markers
- Filterable incident list (status, severity, type)
- Route visualization using OSRM routing engine
- Multi-user support with role-based access control

### Role-Based Access Control
| Role | Capabilities |
|------|-------------|
| **Admin** | Full access to all operations and user management |
| **Dispatcher** | Create incidents, dispatch vehicles, manage operations |
| **Responder** | View assigned incidents, update status |
| **Viewer** | Read-only access to map and incidents |

### Progressive Web App (PWA)
- Installable on desktop and mobile devices
- Offline-capable with service worker caching
- Native app-like experience

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core language |
| Django | 5.0+ | Web framework |
| Django REST Framework | 3.15+ | REST API |
| GeoDjango | - | Spatial operations |
| PostgreSQL | 16 | Database |
| PostGIS | 3.4 | Spatial database extension |
| Gunicorn | 21.0+ | WSGI server |
| Redis | 5.0 | Caching |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Leaflet.js | 1.9.x | Interactive mapping |
| Bootstrap | 5.3.x | UI framework |
| JavaScript | ES6+ | Client-side logic |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Nginx | Reverse proxy & static files |
| OSRM | Route calculation |

### Mobile
| Technology | Version | Purpose |
|------------|---------|---------|
| Apache Cordova | 12.0+ | Cross-platform mobile |

---

## Project Structure

```
webmapping_ass/
├── accounts/              # User authentication & profiles
├── boundaries/            # Administrative boundaries (counties)
├── incidents/             # Incident management & dispatch
├── services/              # Emergency facility management
├── core/                  # Core utilities & validators
├── frontend/              # Web interface
│   ├── templates/         # Django templates
│   └── static/            # CSS, JS, icons
├── es_locator/            # Django project configuration
├── docker/                # Docker configuration
│   ├── web/               # Django container
│   └── nginx/             # Nginx container
├── spatial_data/          # GIS data files
├── cordova/               # Mobile app wrapper
├── docs/                  # Documentation
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker configuration
├── Makefile               # Build automation
└── .env.example           # Environment template
```

---

## Getting Started

### Prerequisites

#### For Docker Setup
- Docker 20.10+
- Docker Compose 3.9+

#### For Local Development
- Python 3.10+
- PostgreSQL 16 with PostGIS 3.4
- Node.js 18+ (for mobile development)

---

### Docker Setup (Recommended)

```bash
# Clone repository
git clone <repo-url>
cd webmapping_ass

# Configure environment
cp .env.example .env

# Start containers
docker-compose up -d

# Initialize database
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser

# Import sample data
docker-compose exec web python manage.py import_counties
docker-compose exec web python manage.py import_facilities

# Generate demo data (optional)
docker-compose exec web python manage.py generate_incidents --count 20
docker-compose exec web python manage.py simulate_vehicles --create-vehicles
```

**Access Points:**
| Service | URL |
|---------|-----|
| Main Application | http://localhost/ |
| Dashboard | http://localhost/dashboard/ |
| Admin Panel | http://localhost/admin/ |
| API Documentation | http://localhost/api/docs/ |

#### Docker Commands

```bash
make up      # Start containers
make down    # Stop containers
make reset   # Stop and remove all data
```

---

### Local Development Setup

#### 1. Install PostgreSQL with PostGIS

**macOS:**
```bash
brew install postgresql@16 postgis
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-16 postgresql-16-postgis-3
sudo systemctl start postgresql
```

#### 2. Create Database

```bash
createdb es_locator
psql -d es_locator -c "CREATE EXTENSION postgis;"
```

#### 3. Setup Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

#### 5. Initialize Application

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import data
python manage.py import_counties
python manage.py import_facilities

# Generate demo data (optional)
python manage.py generate_incidents --count 20
python manage.py simulate_vehicles --create-vehicles
```

#### 6. Run Development Server

```bash
python manage.py runserver
# Access at http://127.0.0.1:8000/
```

---

## Usage

### User Roles

Create users through the Django admin panel (`/admin/`) and assign appropriate roles:

- **Dispatcher**: Operational control of incidents and vehicles
- **Responder**: Field personnel responding to incidents
- **Viewer**: Read-only access for monitoring

### Map Interface

The main map interface (`/`) provides:

1. **Search Methods**
   - Click "Nearest" to find the 5 closest facilities
   - Click "Radius" and set distance to search within range
   - Use filters to narrow by service type or county

2. **Drop Pin Mode**
   - Click "Drop Pin" button
   - Click anywhere on the map to place a search point
   - Drag the marker to adjust position

3. **Facility Details**
   - Click any facility marker to view details
   - See distance from your location
   - Access contact information and services

### Incident Dashboard

The dashboard (`/dashboard/`) provides real-time incident management:

1. **Viewing Incidents**
   - Left sidebar shows incident list with filters
   - Map displays all active incidents and vehicles
   - Click an incident to view details

2. **Creating Incidents** (Dispatcher)
   - Click "New Incident" button
   - Fill in incident details and location
   - Set severity and type

3. **Dispatching Vehicles** (Dispatcher)
   - Select an incident
   - Click "Dispatch Vehicle"
   - Choose from available vehicles
   - Route is automatically calculated

4. **Updating Status** (Responder)
   - View assigned incidents
   - Update status as you respond
   - Mark incidents as resolved

---

## API Reference

The application provides a comprehensive REST API with full OpenAPI documentation.

### Documentation Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/docs/` | Swagger UI documentation |
| `GET /api/redoc/` | ReDoc documentation |
| `GET /api/schema/` | OpenAPI schema |

### Core Endpoints

#### Facilities
```
GET    /api/facilities/              # List all facilities
POST   /api/facilities/              # Create facility
GET    /api/facilities/{id}/         # Get facility details
GET    /api/facilities/within-radius/ # Find within radius
GET    /api/facilities/nearest/      # Find K-nearest
GET    /api/facilities/within-county/ # Find in county
```

#### Incidents
```
GET    /api/incidents/               # List incidents
POST   /api/incidents/               # Create incident
GET    /api/incidents/{id}/          # Get incident details
POST   /api/incidents/{id}/dispatch/ # Dispatch vehicle
POST   /api/incidents/{id}/update-status/ # Update status
GET    /api/incidents/active/        # List active incidents
GET    /api/incidents/{id}/route/    # Get OSRM route
```

#### Vehicles
```
GET    /api/vehicles/                # List all vehicles
GET    /api/vehicles/available/      # List available vehicles
GET    /api/vehicles/available/?type=ambulance # Filter by type
```

#### Dispatches
```
GET    /api/dispatches/              # List dispatches
POST   /api/dispatches/              # Create dispatch
POST   /api/dispatches/{id}/acknowledge/ # Acknowledge
POST   /api/dispatches/{id}/arrive/  # Mark arrival
POST   /api/dispatches/{id}/complete/ # Complete dispatch
```

#### Authentication
```
POST   /api/token/                   # Get JWT token
POST   /api/token/refresh/           # Refresh JWT token
GET    /api/auth/me/                 # Get current user
POST   /accounts/login/              # Session login
POST   /accounts/logout/             # Session logout
```

#### Counties
```
GET    /api/counties/                # List counties
GET    /api/counties/?name_en=Dublin # Filter by name
```

---

## Mobile App

The project includes an Apache Cordova wrapper for iOS and Android deployment.

### Setup

```bash
cd cordova
npm install
```

### Development

```bash
# Add platforms
cordova platform add ios
cordova platform add android

# Run in emulator
cordova emulate ios
cordova emulate android

# Run on device
cordova run ios --device
cordova run android --device
```

### Build for Release

```bash
# iOS (requires Xcode)
cordova build ios --release

# Android
cordova build android --release
```

See [cordova/README.md](cordova/README.md) for detailed mobile setup instructions.

---

## Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test incidents
python manage.py test services
python manage.py test boundaries

# With Docker
docker-compose exec web python manage.py test
```

---

## Deployment

### Docker Production Deployment

1. Configure production environment variables in `.env`
2. Update `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
3. Set `DJANGO_DEBUG=False`
4. Generate a secure `DJANGO_SECRET_KEY`

```bash
docker-compose -f docker-compose.yml up -d
```

### Cloud Platforms

The application supports deployment on:

- **AWS EC2** - With RDS PostgreSQL
- **Azure** - App Service with Azure Database for PostgreSQL
- **DigitalOcean** - Droplets or App Platform
- **Heroku** - With Heroku Postgres addon
- **Railway/Render** - Container deployment

See [docs/README.md](docs/README.md) for detailed deployment instructions.

### SSL/HTTPS

For production, configure SSL using Let's Encrypt:

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d yourdomain.com
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (required) |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `localhost` |
| `CSRF_TRUSTED_ORIGINS` | Trusted CSRF origins | - |
| `DB_NAME` | Database name | `es_locator` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASS` | Database password | `postgres` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `WORKERS` | Gunicorn workers | `3` |
| `TIMEOUT` | Gunicorn timeout | `60` |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org/) for map tiles
- [Leaflet.js](https://leafletjs.com/) for the mapping library
- [OSRM](http://project-osrm.org/) for routing services
- [Bootstrap](https://getbootstrap.com/) for the UI framework
- [Django](https://www.djangoproject.com/) and [Django REST Framework](https://www.django-rest-framework.org/) for the backend
