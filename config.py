"""
Configuration settings for St. Louis 311 Flask Application.
Centralized configuration management for the Flask/PostGIS/GeoServer stack.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask Configuration
class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:Javabean318?@localhost:5432/stl311_db'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Javabean318?@localhost:5432/stl311_test_db'

# API Configuration
API_KEY = os.environ.get("STL311_API_KEY")
if not API_KEY:
    print("Warning: STL311_API_KEY environment variable is not set. API requests may fail.")

API_BASE_URL = "https://www.stlouis-mo.gov/powernap/stlouis/api.cfm"

# Date Range Configuration
START_DATE = datetime.now() - timedelta(days=1)  # Yesterday
END_DATE = datetime.now()                        # Today (inclusive)

# API Request Configuration
DEFAULT_DAYS_BACK = 30
PAGE_SIZE = 1000
MAX_PAGES = 10
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0

# Status Configuration
DEFAULT_STATUS = "open"

# Coordinate System Configuration
COORDINATE_SYSTEM = "EPSG:3857"  # Web Mercator

# Coordinate Validation Ranges (St. Louis area in EPSG:3857)
COORDINATE_RANGES = {
    'min_x': -10060000,  # West boundary in EPSG:3857
    'max_x': -10020000,  # East boundary in EPSG:3857
    'min_y': 4600000,    # South boundary in EPSG:3857
    'max_y': 4700000     # North boundary in EPSG:3857
}

# Date Fields for Processing
DATE_FIELDS = ['datetime_init', 'datetime_closed', 'prj_complete_date', 'date_inv_done', 'date_cancelled']

# Date Formats for Parsing
DATE_FORMATS = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']

# GeoServer Configuration
GEOSERVER_CONFIG = {
    'base_url': os.environ.get('GEOSERVER_URL', 'http://localhost:8080/geoserver'),
    'username': os.environ.get('GEOSERVER_USERNAME', 'admin'),
    'password': os.environ.get('GEOSERVER_PASSWORD', 'geoserver'),
    'workspace': os.environ.get('GEOSERVER_WORKSPACE', 'stl311'),
    'namespace': os.environ.get('GEOSERVER_NAMESPACE', 'http://stl311.org'),
    
    # Default service settings
    'default_layer_name': 'stl311_service_requests',
    'default_datastore_name': 'stl311_db',
    
    # Service properties
    'service_properties': {
        'title': 'St. Louis 311 Service Requests',
        'description': 'Real-time 311 service requests for the City of St. Louis. Auto-updated from the St. Louis Open311 API.',
        'tags': ['311', 'St. Louis', 'service requests', 'government', 'open data', 'public services'],
        'snippet': 'Current 311 service requests for the City of St. Louis',
        'accessInformation': 'City of St. Louis Open Data Portal',
        'licenseInfo': 'Public Domain - City of St. Louis',
        'type': 'Feature Service'
    },
    
    # Publishing parameters
    'publish_parameters': {
        'hasStaticData': False,
        'maxRecordCount': 10000,
        'allowGeometryUpdates': True,
        'capabilities': 'Query,Create,Update,Delete,Uploads,Editing',
        'units': 'esriMeters',
        'xssPreventionEnabled': True,
        'enableZDefaults': False,
        'allowUpdateWithoutMValues': True
    }
}

# Database Configuration
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME', 'stl311_db'),
    'username': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'schema': 'public'
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': os.environ.get('LOG_LEVEL', 'INFO'),
    'file': os.environ.get('LOG_FILE', 'stl311_flask.log'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
