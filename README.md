# STL 311+ Enhanced Citizen Portal

A modern, comprehensive citizen engagement platform for St. Louis 311 service requests, featuring an interactive web interface, citizen submission portal, real-time tracking, and integrated GIS mapping capabilities.

## 🌟 Overview

STL 311+ transforms the traditional 311 system into a full-featured citizen engagement portal that allows residents to:
- **Submit detailed service requests** with photos, precise locations, and priority levels
- **Track requests in real-time** with status updates and timeline visualization  
- **View interactive maps** of all service requests with spatial filtering
- **Access emergency contact information** when needed

The system integrates with the St. Louis Open311 API while providing enhanced citizen-facing features through a modern web interface built with Flask, PostGIS, and GeoServer.

## 🚀 Key Features

### 🏛️ **Citizen Portal**
- **Multi-step submission wizard** with category selection, interactive mapping, and file uploads
- **Real-time request tracking** with status timeline and location visualization
- **Emergency detection** with appropriate routing to emergency services
- **Mobile-responsive design** optimized for all devices
- **Professional UI/UX** with Bootstrap styling and intuitive navigation

### 🗺️ **Interactive Mapping**
- **Live service request visualization** with color-coded status markers
- **Spatial filtering** with bounding box queries and neighborhood selection
- **Location selection** with geocoding and precise coordinate capture
- **Map integration** using Leaflet.js with OpenStreetMap tiles

### 📊 **Data Management** 
- **Enhanced database schema** with 15+ citizen-specific fields
- **File attachment support** for photos and documents
- **Status update system** with citizen and staff visibility controls
- **Data validation** and quality assurance workflows
- **Backward compatibility** with existing 311 data

### 🔧 **Technical Infrastructure**
- **RESTful API** with comprehensive endpoints for all operations
- **PostGIS spatial database** with EPSG:3857 coordinate system
- **GeoServer integration** for professional GIS services
- **Docker containerization** for easy deployment and scaling
- **Automated testing** suite with comprehensive coverage

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, GeoAlchemy2, PostGIS
- **Frontend**: Bootstrap 5, Leaflet.js, Font Awesome
- **Database**: PostgreSQL 13 with PostGIS 3.1 
- **GIS Server**: GeoServer 2.22.2 (Kartoza Docker image)
- **Deployment**: Docker Compose
- **APIs**: St. Louis Open311 API integration
- **Mapping**: OpenStreetMap, Nominatim geocoding

## 📋 System Requirements

**For Docker Setup (Recommended)**:
- **Docker** and **Docker Compose** installed
- **4GB+ RAM** for optimal performance
- **Modern web browser** with JavaScript enabled

**For Manual Setup (Advanced)**:
- **Python 3.9+** 
- **PostgreSQL 13+** with PostGIS 3.1+ extension
- **GeoServer 2.22.2+**

## 🚀 Easy Setup with Docker Compose

**STL 311+ includes a complete `docker-compose.yml` configuration** that sets up all services automatically:
- **Flask Application** (Port 5000)
- **PostgreSQL + PostGIS** Database (Port 5433)
- **GeoServer** GIS Server (Port 8080)

### 1. Clone the Repository
```bash
git clone https://github.com/maxx-mill/stl311_plus.git
cd stl311_plus
```

### 2. Start All Services
```bash
# Start all services in detached mode
docker-compose up -d
```

### 3. Initialize the Database (First Time Only)
```bash
# Run database migration to create tables and sample data
docker exec stl311_flask python migrate_database.py
```

### 4. Access the Application
🎉 **That's it!** Your STL 311+ portal is now running:

- **🏛️ Citizen Portal**: http://localhost:5000
- **📝 Submit Requests**: http://localhost:5000/submit  
- **🔍 Track Requests**: http://localhost:5000/track
- **🗺️ GeoServer Admin**: http://localhost:8080/geoserver (admin/geoserver)
- **🗄️ Database**: localhost:5433 (postgres/password)

### 5. Stopping Services
```bash
# Stop all services when done
docker-compose down
```

That's it! The Docker Compose setup handles all the complexity of service coordination and networking.

## 🛠️ Development Commands

### Managing Docker Services
```bash
# Start all services (detached)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart services (after code changes)
docker-compose down && docker-compose up -d --build

# Check service health
docker-compose ps
```

### Database Operations
```bash
# Run database migration
docker exec stl311_flask python migrate_database.py

# Connect to PostgreSQL
docker exec -it stl311_postgres psql -U postgres -d stl311

# Backup database
docker exec stl311_postgres pg_dump -U postgres stl311 > backup.sql

# Restore database
docker exec -i stl311_postgres psql -U postgres -d stl311 < backup.sql
```

### Testing
```bash
# Run all tests
docker exec stl311_flask python -m pytest tests/

# Run specific test file
docker exec stl311_flask python -m pytest tests/test_api.py -v

# Run enhanced database tests
docker exec stl311_flask python tests/test_enhanced_db.py
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask App     │    │   PostgreSQL     │    │   GeoServer     │
│   (Port 5000)   │◄──►│   + PostGIS      │◄──►│   (Port 8080)   │
│                 │    │   (Port 5433)    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   Spatial Data   │    │   Map Services  │
│   • Submit      │    │   • Coordinates  │    │   • WMS/WFS     │
│   • Track       │    │   • Geometry     │    │   • Styling     │
│   • Visualize   │    │   • Attachments  │    │   • Publishing  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
stl311_plus/
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models  
├── config.py              # Configuration settings
├── migrate_database.py    # Database migration script
├── validation.py          # Data validation utilities
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker orchestration
├── Dockerfile            # Flask app container
├── init-db.sql           # Database initialization
├── services/             # Service layer modules
│   ├── api_client.py     # Open311 API integration
│   ├── data_processor.py # Data processing utilities  
│   └── geoserver_client.py # GeoServer integration
├── templates/            # HTML templates
│   ├── index.html        # Main mapping interface
│   ├── submit.html       # Citizen submission form
│   └── track.html        # Request tracking interface
├── tests/                # Test suite
│   ├── test_api.py       # API endpoint tests
│   ├── test_enhanced_db.py # Database tests
│   └── test_docker_schema.py # Schema validation tests
└── logs/                 # Application logs
```

## 🔧 Manual Installation (Advanced Users)

For developers who prefer manual setup or need custom configurations:

### Prerequisites
- **Python 3.9+** with pip
- **PostgreSQL 13+** with PostGIS 3.1+ extension
- **GeoServer 2.22.2+** (optional, for advanced GIS features)

### 1. Clone and Setup Environment
```bash
git clone https://github.com/maxx-mill/stl311_plus.git
cd stl311_plus

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Database Configuration
```bash
# Create PostgreSQL database with PostGIS
createdb stl311
psql -d stl311 -c "CREATE EXTENSION postgis;"

# Set environment variables
export DATABASE_URL="postgresql://username:password@localhost/stl311"
export FLASK_ENV=development
export FLASK_DEBUG=True
export GEOSERVER_URL="http://localhost:8080/geoserver"
```

### 3. Initialize and Run
```bash
# Initialize database with tables and sample data
python migrate_database.py

# Start Flask development server
python app.py
```

The application will be available at http://localhost:5000

> **💡 Note**: Manual installation requires significant configuration of PostgreSQL, PostGIS, and optionally GeoServer. The Docker Compose approach is strongly recommended for most users.

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Main mapping interface
- `GET /submit` - Citizen submission form  
- `GET /track` - Request tracking interface
- `GET /api/health` - System health check

### Service Request Management
- `GET /api/service-requests` - List service requests (paginated)
- `GET /api/service-requests/{id}` - Get specific request
- `POST /api/submit-request` - Submit new citizen request
- `GET /api/track-request/{id}` - Track request by ID

### Data Integration  
- `GET /api/categories` - Service categories
- `POST /api/sync` - Sync with Open311 API
- `GET /api/stats` - System statistics
- `POST /api/geoserver/publish` - Publish to GeoServer

## 💾 Database Schema

The enhanced database includes all original 311 fields plus:

### Citizen Engagement Fields
- `source` - Request origin (api/citizen)
- `category` - Service category  
- `priority` - Priority level (low/normal/high/urgent)
- `is_emergency` - Emergency flag
- `citizen_name`, `citizen_email`, `citizen_phone` - Contact info
- `contact_method_preference` - Preferred contact method

### Staff Workflow Fields  
- `assigned_to` - Staff assignment
- `estimated_completion` - Completion estimate
- `internal_notes` - Staff notes
- `citizen_updates` - Public status updates

### Quality Assurance
- `is_validated` - Validation status
- `validation_notes` - QA notes
- `duplicate_of` - Duplicate detection

### Related Tables
- `service_request_attachments` - File uploads
- `service_request_updates` - Status timeline
- `service_categories` - Category definitions

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test files  
python tests/test_api.py
python tests/test_enhanced_db.py
python tests/test_docker_schema.py

# Test with Docker
docker exec stl311_flask python -m pytest tests/
```

## 🔐 Environment Variables

Key configuration options in `.env`:

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=stl311_db  
DB_USER=postgres
DB_PASSWORD=password

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key

# API Configuration  
STL311_API_KEY=your-api-key
STL311_API_URL=https://www.stlouis-mo.gov/data/service-requests-311.cfm

# GeoServer Configuration
GEOSERVER_URL=http://geoserver:8080/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=geoserver
```

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```sql
-- Create database
CREATE DATABASE stl311_db;

-- Enable PostGIS extension
CREATE EXTENSION postgis;

-- Create user (optional)
CREATE USER stl311_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE stl311_db TO stl311_user;
```

### 5. Configure Environment Variables

Copy the example environment file and update it with your settings:

```bash
cp env.example .env
```

Edit `.env` with your actual configuration:

```env
# St. Louis 311 API Configuration
STL311_API_KEY=your_actual_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/stl311_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stl311_db
DB_USER=postgres
DB_PASSWORD=your_password

# GeoServer Configuration
GEOSERVER_URL=http://localhost:8080/geoserver
GEOSERVER_USERNAME=admin
GEOSERVER_PASSWORD=geoserver
GEOSERVER_WORKSPACE=stl311
## 🚀 Development

### Local Development Setup

If you prefer to run without Docker:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set up PostgreSQL with PostGIS
createdb stl311_db
psql stl311_db -c "CREATE EXTENSION postgis;"

# 3. Configure environment
cp env.example .env
# Edit .env with your local settings

# 4. Run migrations
python migrate_database.py

# 5. Start the application  
python app.py
```

### Making Changes

1. **Frontend Changes**: Edit templates in `templates/` directory
2. **Backend Changes**: Modify `app.py` or service modules in `services/`
3. **Database Changes**: Update models in `models.py` and create migrations
4. **Styling**: CSS is embedded in templates (consider extracting for larger projects)

### Rebuilding Docker Images

```bash
# Rebuild after changes
docker-compose down
docker-compose build --no-cache flask_app
docker-compose up -d
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `python -m pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to new functions and classes
- Include tests for new functionality
- Update documentation for user-facing changes
- Test with both Docker and local development setups

## 📈 Performance & Scaling

### Database Optimization
- PostGIS spatial indexes on geometry columns
- B-tree indexes on frequently queried fields
- Connection pooling configured in SQLAlchemy
- Pagination for large result sets

### Caching Strategies
- Browser caching for static assets
- Database query caching for frequently accessed data
- GeoServer tile caching for map services

### Monitoring
- Application logs in `logs/` directory
- Health check endpoint for monitoring
- Database performance metrics available
- GeoServer admin interface for service monitoring

## 🔧 Troubleshooting

### Common Issues

**Port conflicts**: Ensure ports 5000, 5433, and 8080 are available
```bash
# Check port usage
netstat -an | findstr "5000"
```

**Database connection errors**: Verify PostgreSQL is running and accessible
```bash
# Test database connection
docker exec stl311_flask python -c "from app import db; print('DB OK' if db.engine.connect() else 'DB ERROR')"
```

**GeoServer publishing issues**: Check GeoServer admin interface
- Login: http://localhost:8080/geoserver (admin/geoserver)  
- Verify workspace and datastore configuration
- Check layer publishing status

**Template/Static file changes not showing**: Clear browser cache or rebuild Docker container

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **City of St. Louis** - Open311 API and open data initiative
- **PostGIS Project** - Spatial database capabilities
- **GeoServer Project** - Open source GIS server
- **OpenStreetMap** - Map tile data
- **Bootstrap** - UI framework
- **Leaflet** - Interactive mapping library

## 📞 Support

For support and questions:
- **Issues**: Create a GitHub issue for bugs and feature requests
- **Documentation**: Check the Wiki for detailed guides
- **Community**: Join our discussions in GitHub Discussions

---

**STL 311+** - Empowering St. Louis citizens with modern 311 services 🏛️✨

### Get Specific Service Request

```http
GET /api/service-requests/{id}
```

### Sync Data from API

```http
POST /api/sync
Content-Type: application/json

{
  "days_back": 1,
  "status": "open",
  "force_sync": false
}
```

### Publish to GeoServer

```http
POST /api/geoserver/publish
Content-Type: application/json

{
  "layer_name": "stl311_service_requests"
}
```

### Get Statistics

```http
GET /api/stats
```

Returns statistics about service requests including total count, coordinate percentage, and status breakdown.

## 🗄️ Database Schema

The application creates a `service_requests` table with the following structure:

```sql
CREATE TABLE service_requests (
    id SERIAL PRIMARY KEY,
    request_id BIGINT UNIQUE NOT NULL,
    description TEXT,
    status VARCHAR(50),
    problem_code VARCHAR(50),
    submit_to VARCHAR(100),
    prob_address VARCHAR(255),
    prob_city VARCHAR(100),
    prob_zip INTEGER,
    prob_add_type VARCHAR(50),
    neighborhood VARCHAR(100),
    ward INTEGER,
    datetime_init TIMESTAMP,
    datetime_closed TIMESTAMP,
    date_cancelled TIMESTAMP,
    date_inv_done TIMESTAMP,
    prj_complete_date TIMESTAMP,
    caller_type VARCHAR(50),
    explanation TEXT,
    plain_english_name VARCHAR(255),
    group_name VARCHAR(100),
    geometry GEOMETRY(POINT, 3857),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🗺️ GeoServer Integration

The application automatically:

1. Creates a workspace named `stl311`
2. Creates a PostGIS datastore connection
3. Publishes the `service_requests` table as a feature layer
4. Provides WMS and WFS endpoints

### GeoServer URLs

- **WMS Service**: `http://localhost:8080/geoserver/stl311/wms`
- **WFS Service**: `http://localhost:8080/geoserver/stl311/wfs`
- **Layer Preview**: `http://localhost:8080/geoserver/stl311/wms?service=WMS&version=1.1.0&request=GetMap&layers=stl311:stl311_service_requests&bbox=-10060000,4600000,-10020000,4700000&width=768&height=768&srs=EPSG:3857&format=application/openlayers`

## 🔧 Configuration

### Coordinate System

The application uses **EPSG:3857 (Web Mercator)** for all spatial data:

- **Input**: Coordinates from St. Louis 311 API (SRX/SRY fields)
- **Storage**: PostGIS geometry in EPSG:3857
- **Output**: GeoServer services in EPSG:3857
- **Validation**: St. Louis area bounds checking

### Data Validation

The system validates:

- Coordinate ranges (St. Louis area bounds)
- Date formats (multiple format support)
- Required fields
- Data types and constraints

## 📊 Monitoring and Logging

### Log Files

- Application logs: `stl311_flask.log`
- Log level: Configurable via `LOG_LEVEL` environment variable

### Health Monitoring

- Database connection status
- API connectivity
- GeoServer publishing status
- System statistics

## 🔄 Data Flow

1. **Fetch**: Retrieve data from St. Louis Open311 API
2. **Process**: Validate and clean data
3. **Store**: Save to PostGIS database with spatial indexing
4. **Publish**: Automatically publish to GeoServer
5. **Serve**: Provide REST API and web mapping services

## 🚀 Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Production Considerations

1. **Database**: Use managed PostgreSQL service (AWS RDS, Google Cloud SQL, etc.)
2. **GeoServer**: Deploy on separate server or use managed service
3. **Load Balancing**: Use nginx or cloud load balancer
4. **Monitoring**: Implement application monitoring (Prometheus, Grafana)
5. **Backup**: Regular database backups
6. **SSL**: Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the logs for error messages
2. Verify database and GeoServer connectivity
3. Ensure all environment variables are set correctly
4. Check API key validity

## 🔗 Related Projects

- Original ArcPy version: [stlouis311](https://github.com/maxx-mill/stlouis311)
- St. Louis Open Data Portal: [https://www.stlouis-mo.gov/data/](https://www.stlouis-mo.gov/data/)
- GeoServer Documentation: [https://docs.geoserver.org/](https://docs.geoserver.org/) 