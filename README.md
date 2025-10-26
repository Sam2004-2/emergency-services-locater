# Emergency Services Locator

> A production-ready web mapping application for discovering and analyzing emergency services across Ireland using interactive spatial queries.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/django-5.0+-green.svg)
![PostGIS](https://img.shields.io/badge/PostGIS-3.4-blue.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development Setup](#local-development-setup)
- [API Documentation](#api-documentation)
- [Data Import](#data-import)
- [Testing](#testing)
- [Deployment](#deployment)
- [Known Issues & Limitations](#known-issues--limitations)
- [Contributing](#contributing)
- [License](#license)

---

## 📖 Overview

The **Emergency Services Locator** is a comprehensive geospatial web application designed to help users locate emergency services (hospitals, fire stations, police stations, ambulance services) across Ireland. Built with Django, PostGIS, and Leaflet, it provides powerful spatial query capabilities through an intuitive map-based interface.

### Key Capabilities

- **Interactive Map Interface**: Drag, zoom, and click to explore emergency services
- **Multiple Search Methods**: Find services by proximity, radius, county boundaries, or custom areas
- **Real-time Spatial Queries**: Optimized PostGIS queries for sub-second response times
- **RESTful API**: Complete API for integration with other systems
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Production Ready**: Dockerized deployment with nginx, PostgreSQL, and monitoring tools

---

## ✨ Features

### Core Functionality

- ✅ **Geolocation Support**: Find your current location and nearby services
- ✅ **Drop Pin Mode**: Place custom pins anywhere on the map to search from that location
- ✅ **Proximity Search**: Find the 5 nearest emergency services to any point
- ✅ **Radius Search**: Discover all services within a customizable radius (1-50km)
- ✅ **County Filtering**: View and search services within specific Irish counties
- ✅ **Service Type Filtering**: Filter by hospital, fire station, police, or ambulance
- ✅ **Interactive Popups**: Detailed information cards for each service location
- ✅ **Distance Calculations**: Real-time distance measurements from your location

### Advanced Features

- 🎯 **Draggable Pins**: Reposition search locations by dragging markers
- 🗺️ **County Boundary Overlays**: Toggle visibility of administrative boundaries
- 📊 **Dynamic Radius Visualization**: Visual circle overlays showing search areas
- 🔄 **Live Updates**: Results update dynamically as you adjust parameters
- 📱 **Fully Responsive**: Mobile-first design with touch-friendly controls
- 🚀 **High Performance**: Spatial indexes and query optimization for fast results

### Technical Features

- 🔒 **Secure API**: Token-based authentication for write operations
- 📦 **Docker Deployment**: Complete containerized stack with health checks
- 🗄️ **Spatial Database**: PostGIS for advanced geospatial operations
- 🔍 **RESTful API**: GeoJSON endpoints following REST best practices
- 📈 **Scalable Architecture**: Nginx reverse proxy with Gunicorn workers
- 🛠️ **Admin Interface**: Django admin panel for data management

---

## 📸 Screenshots

### Main Map Interface
![Main Interface](docs/screenshots/main-interface.png)
*Interactive map with service markers, county boundaries, and control panel*

### Proximity Search
![Proximity Search](docs/screenshots/proximity-search.png)
*Find the 5 nearest emergency services to any location*

### Radius Search
![Radius Search](docs/screenshots/radius-search.png)
*Discover all services within a customizable radius*

### Drop Pin Mode
![Drop Pin Mode](docs/screenshots/drop-pin-mode.png)
*Place custom pins anywhere on the map*

### Mobile View
![Mobile Responsive](docs/screenshots/mobile-view.png)
*Fully responsive design for mobile devices*

> **Note**: Screenshots should be added to `docs/screenshots/` directory. The application is live at `http://localhost/` when running.

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Core programming language |
| **Django** | 5.0+ | Web framework and ORM |
| **Django REST Framework** | 3.15+ | RESTful API framework |
| **PostgreSQL** | 16 | Relational database |
| **PostGIS** | 3.4 | Spatial database extension |
| **GeoDjango** | Built-in | Django's geographic framework |
| **psycopg2** | 2.9+ | PostgreSQL adapter |
| **Gunicorn** | 21.0+ | WSGI HTTP server |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Leaflet.js** | 1.9.x | Interactive mapping library |
| **Bootstrap** | 5.3.x | Responsive UI framework |
| **JavaScript (ES6+)** | Modern | Client-side interactivity |
| **HTML5** | - | Semantic markup |
| **CSS3** | - | Styling and animations |

### DevOps & Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| **Docker** | 20.10+ | Containerization |
| **Docker Compose** | 3.9+ | Multi-container orchestration |
| **Nginx** | Alpine | Reverse proxy & static files |
| **pgAdmin** | 8 | Database administration |

### Data & APIs

- **OpenStreetMap**: Base map tiles (Nominatim API)
- **GeoJSON**: Spatial data interchange format
- **Overpass API**: OpenStreetMap data queries (optional)

---

## 📋 Prerequisites

### For Docker Deployment (Recommended)

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Disk Space**: 2GB minimum
- **RAM**: 4GB minimum recommended

### For Local Development

- **Python**: 3.10 or higher
- **PostgreSQL**: 14+ with PostGIS extension
- **Git**: For version control
- **pip**: Python package manager
- **virtualenv**: Python virtual environment tool

---

## 🚀 Quick Start (Docker)

The fastest way to get the application running is using Docker Compose:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/emergency-services-locator.git
cd emergency-services-locator
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred settings (optional)
# Default values work out of the box
nano .env
```

**Example `.env` file:**

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=es_locator

# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Gunicorn Configuration
WORKERS=3
TIMEOUT=60

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin123
```

### 3. Start the Application

```bash
# Build and start all containers
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### 4. Initialize the Database

```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Import sample data
docker-compose exec web python manage.py import_counties
docker-compose exec web python manage.py import_facilities

# Create admin user
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application

Open your browser and navigate to:

- **Main Application**: http://localhost/
- **Django Admin**: http://localhost/admin/
- **pgAdmin**: http://localhost:5050/

**That's it!** You're now running a full production-ready stack.

### Stopping the Application

```bash
# Stop containers (preserves data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## 💻 Local Development Setup

For local development without Docker:

### 1. Install PostgreSQL with PostGIS

**macOS (using Homebrew):**
```bash
brew install postgresql@16 postgis
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-16 postgresql-16-postgis-3 postgis
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Create database
createdb es_locator

# Enable PostGIS extension
psql -d es_locator -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d es_locator -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit with your database credentials
nano .env
```

**Example local `.env`:**
```env
DB_NAME=es_locator
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Initialize Django

```bash
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Create superuser
python manage.py createsuperuser

# Import sample data
python manage.py import_counties
python manage.py import_facilities
```

### 6. Run Development Server

```bash
python manage.py runserver

# Application available at http://127.0.0.1:8000/
```

---

## 📚 API Documentation

The application provides a comprehensive RESTful API with GeoJSON support.

### Base URL

- **Development**: `http://localhost:8000/api/`
- **Docker**: `http://localhost/api/`

### Authentication

- **Read Operations**: Public (no authentication required)
- **Write Operations**: Requires authentication token
- **Format**: `Authorization: Token <your-token>`

### Endpoints

#### 1. List All Services

```http
GET /api/services/
```

**Query Parameters:**
- `type` (optional): Filter by service type (`hospital`, `fire`, `police`, `ambulance`)
- `limit` (optional): Number of results per page (default: 20)
- `offset` (optional): Pagination offset

**Example Request:**
```bash
curl "http://localhost/api/services/?type=hospital&limit=10"
```

**Example Response:**
```json
{
  "type": "FeatureCollection",
  "count": 45,
  "next": "http://localhost/api/services/?limit=10&offset=10",
  "previous": null,
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "Point",
        "coordinates": [-6.2603, 53.3498]
      },
      "properties": {
        "name": "St. James's Hospital",
        "type": "hospital",
        "address": "James's Street, Dublin 8",
        "phone": "+353 1 410 3000",
        "email": "info@stjames.ie",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    }
  ]
}
```

#### 2. Get Service Detail

```http
GET /api/services/{id}/
```

**Example:**
```bash
curl "http://localhost/api/services/1/"
```

#### 3. Find Nearest Services

```http
GET /api/services/nearest/
```

**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lng` (required): Longitude (-180 to 180)
- `limit` (optional): Number of results (default: 5, max: 50)
- `type` (optional): Filter by service type

**Example Request:**
```bash
curl "http://localhost/api/services/nearest/?lat=53.3498&lng=-6.2603&limit=5&type=hospital"
```

**Example Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "Point",
        "coordinates": [-6.2603, 53.3498]
      },
      "properties": {
        "name": "St. James's Hospital",
        "type": "hospital",
        "distance": 123.45,
        "address": "James's Street, Dublin 8"
      }
    }
  ]
}
```

**Distance Units**: Meters

#### 4. Find Services Within Radius

```http
GET /api/services/within-radius/
```

**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lng` (required): Longitude (-180 to 180)
- `radius` (required): Search radius in meters (max: 100,000m = 100km)
- `type` (optional): Filter by service type

**Example Request:**
```bash
curl "http://localhost/api/services/within-radius/?lat=53.3498&lng=-6.2603&radius=5000&type=hospital"
```

#### 5. Find Services in County

```http
GET /api/services/within-county/
```

**Query Parameters:**
- `county_id` (required): County ID
- `type` (optional): Filter by service type

**Example Request:**
```bash
curl "http://localhost/api/services/within-county/?county_id=1&type=fire"
```

#### 6. Find Services in Polygon

```http
POST /api/services/within-polygon/
```

**Request Body:**
```json
{
  "polygon": {
    "type": "Polygon",
    "coordinates": [
      [
        [-6.3, 53.4],
        [-6.2, 53.4],
        [-6.2, 53.3],
        [-6.3, 53.3],
        [-6.3, 53.4]
      ]
    ]
  },
  "type": "hospital"
}
```

#### 7. Get Coverage Buffers

```http
GET /api/services/coverage-buffers/
```

**Query Parameters:**
- `lat` (required): Latitude
- `lng` (required): Longitude
- `radius` (optional): Coverage radius in meters (default: 10,000m)

**Returns**: All services within radius with distance metadata.

---

### County Endpoints

#### 1. List All Counties

```http
GET /api/counties/
```

**Example Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [...]
      },
      "properties": {
        "name": "Dublin",
        "code": "D",
        "area_km2": 921.0,
        "population": 1345402
      }
    }
  ]
}
```

#### 2. Get County Detail

```http
GET /api/counties/{id}/
```

#### 3. Get Services in County

```http
GET /api/counties/{id}/services/
```

---

### Error Responses

All endpoints return standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

**Example Error Response:**
```json
{
  "error": "Invalid latitude. Must be between -90 and 90.",
  "code": "invalid_parameter"
}
```

---

## 📥 Data Import

The application includes management commands for importing spatial data:

### Import Counties

```bash
# Docker
docker-compose exec web python manage.py import_counties

# Local
python manage.py import_counties
```

This command imports all 26 Irish counties with their administrative boundaries.

### Import Emergency Facilities

```bash
# Docker
docker-compose exec web python manage.py import_facilities

# Local
python manage.py import_facilities
```

This command imports emergency services from OpenStreetMap data.

### Custom Data Import

You can import custom GeoJSON or Shapefile data using Django's management commands or the admin interface.

**Using the Admin Interface:**
1. Navigate to http://localhost/admin/
2. Log in with your superuser credentials
3. Go to "Emergency Facilities" or "Counties"
4. Click "Add" to create new entries manually

**Using ogr2ogr (for bulk imports):**
```bash
ogr2ogr -f "PostgreSQL" \
  PG:"dbname=es_locator user=postgres password=postgres" \
  your_data.shp \
  -nln services_emergencyfacility \
  -append
```

---

## 🧪 Testing

### Run All Tests

```bash
# Docker
docker-compose exec web python manage.py test

# Local
python manage.py test
```

### Run Specific App Tests

```bash
# Test services app
python manage.py test services

# Test boundaries app
python manage.py test boundaries

# Test frontend app
python manage.py test frontend
```

### Test Coverage

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Manual Testing Checklist

- [ ] Map loads correctly with OpenStreetMap tiles
- [ ] Geolocation button finds current location
- [ ] Drop pin mode places markers on map click
- [ ] Nearest services query returns results with distances
- [ ] Radius search shows circle overlay and correct results
- [ ] County dropdown populates from database
- [ ] Service type filter works for all types
- [ ] Radius slider updates dynamically (1-50km)
- [ ] Markers show correct popup information
- [ ] Mobile responsive design works on small screens
- [ ] API endpoints return valid GeoJSON
- [ ] Admin interface allows CRUD operations

---

## 🌐 Deployment

### Docker Production Deployment

#### 1. Cloud Hosting Setup

**For AWS EC2:**
```bash
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**For DigitalOcean Droplet:**
```bash
# Use Docker pre-installed droplet or install manually
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
```

#### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/emergency-services-locator.git
cd emergency-services-locator

# Set production environment variables
nano .env
```

**Production `.env` example:**
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=es_locator
DJANGO_SECRET_KEY=GENERATE_STRONG_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
WORKERS=4
TIMEOUT=120
```

#### 3. Deploy

```bash
# Build and start
docker-compose up -d --build

# Initialize database
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --no-input
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py import_counties
docker-compose exec web python manage.py import_facilities
```

#### 4. Configure Domain (Optional)

**nginx configuration** (`docker/nginx/nginx.conf`):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS (after SSL setup)
    # return 301 https://$server_name$request_uri;
    
    location /static/ {
        alias /staticfiles/;
    }
    
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 5. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Platform-as-a-Service Deployment

The application can also be deployed to:

- **Heroku**: With Heroku Postgres and PostGIS buildpack
- **Railway**: Native Docker support
- **Render**: Supports Docker Compose
- **Google Cloud Run**: Containerized deployment
- **Azure App Service**: Container instances

---

## ⚠️ Known Issues & Limitations

### Current Limitations

1. **Data Coverage**: Sample data includes Irish counties only. Extend to other regions by importing custom data.

2. **Scalability**: Current configuration optimized for up to 10,000 facilities. For larger datasets:
   - Increase Gunicorn workers
   - Add Redis caching layer
   - Implement database connection pooling

3. **Offline Mode**: Application requires internet connection for:
   - OpenStreetMap tiles
   - Geolocation services
   - Consider offline tile caching for production

4. **Browser Compatibility**: 
   - Optimized for modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
   - IE11 not supported

### Known Issues

1. **Mobile Keyboard**: On some mobile devices, the radius slider may not update smoothly when keyboard is visible. **Workaround**: Close keyboard before adjusting slider.

2. **County Boundaries**: Very detailed boundary polygons may cause rendering lag on older devices. **Workaround**: Simplify geometries using `ST_Simplify()`.

3. **API Rate Limits**: OpenStreetMap Nominatim has usage limits. For production, consider:
   - Self-hosted Nominatim instance
   - Commercial geocoding service
   - Local tile server

### Planned Improvements

- [ ] Add routing between user location and selected service
- [ ] Implement real-time facility status updates
- [ ] Add user authentication for saving favorite locations
- [ ] Export search results to CSV/GeoJSON
- [ ] Add heat map visualization
- [ ] Implement advanced search filters (opening hours, ratings)
- [ ] Add multi-language support
- [ ] Offline map caching
- [ ] Progressive Web App (PWA) support
- [ ] Real-time updates via WebSockets

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write comprehensive docstrings
- Add tests for new features
- Update documentation

### Commit Message Format

```
type(scope): subject

body

footer
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Example**:
```
feat(api): add polygon search endpoint

Implement POST /api/services/within-polygon/ endpoint
to find services within custom drawn polygons.

Closes #123
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- **OpenStreetMap** contributors for map data
- **Leaflet** team for the excellent mapping library
- **Django** and **Django REST Framework** communities
- **PostGIS** developers for spatial database capabilities
- All open-source contributors

---

## 📞 Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/emergency-services-locator/issues)
- **Email**: your.email@example.com
- **Documentation**: [Wiki](https://github.com/yourusername/emergency-services-locator/wiki)

---

## 📊 Project Statistics

![GitHub Stars](https://img.shields.io/github/stars/yourusername/emergency-services-locator)
![GitHub Forks](https://img.shields.io/github/forks/yourusername/emergency-services-locator)
![GitHub Issues](https://img.shields.io/github/issues/yourusername/emergency-services-locator)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/yourusername/emergency-services-locator)

---

**Built with ❤️ using Django, PostGIS, and Leaflet**
