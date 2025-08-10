"""
SQLAlchemy models for St. Louis 311 Service Integration with PostGIS support.
Uses GeoAlchemy2 for spatial data handling.
"""

from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from datetime import datetime
from shapely.geometry import Point
from shapely.wkt import dumps
import logging

logger = logging.getLogger(__name__)

# Create the SQLAlchemy instance
db = SQLAlchemy()

class ServiceRequest(db.Model):
    """
    Service Request model for St. Louis 311 data with PostGIS spatial support.
    """
    __tablename__ = 'service_requests'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Service request identifier (from API or auto-generated)
    request_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    
    # Source tracking - NEW FIELD
    source = db.Column(db.String(20), default='api', index=True)  # 'api' or 'citizen'
    
    # Basic information
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='New', index=True)
    problem_code = db.Column(db.String(50), index=True)
    submit_to = db.Column(db.String(100))
    
    # Citizen submission fields - NEW FIELDS
    category = db.Column(db.String(50), index=True)  # refuse, traffic, street, etc.
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    is_emergency = db.Column(db.Boolean, default=False)
    
    # Address information
    prob_address = db.Column(db.String(255))
    prob_city = db.Column(db.String(100))
    prob_zip = db.Column(db.Integer)
    prob_add_type = db.Column(db.String(50))
    
    # Location information
    neighborhood = db.Column(db.String(100))
    ward = db.Column(db.Integer)
    
    # Citizen contact information - NEW FIELDS
    citizen_name = db.Column(db.String(200))
    citizen_phone = db.Column(db.String(20))
    citizen_email = db.Column(db.String(200), index=True)
    contact_method_preference = db.Column(db.String(20))  # email, phone, none
    
    # Dates
    datetime_init = db.Column(db.DateTime, index=True)
    datetime_closed = db.Column(db.DateTime)
    date_cancelled = db.Column(db.DateTime)
    date_inv_done = db.Column(db.DateTime)
    prj_complete_date = db.Column(db.DateTime)
    
    # Staff workflow fields - NEW FIELDS
    assigned_to = db.Column(db.String(100))
    estimated_completion = db.Column(db.DateTime)
    internal_notes = db.Column(db.Text)
    citizen_updates = db.Column(db.Text)  # Updates visible to citizen
    
    # Additional fields
    caller_type = db.Column(db.String(50))
    explanation = db.Column(db.Text)
    plain_english_name = db.Column(db.String(255))
    group_name = db.Column(db.String(100))
    
    # Validation and quality assurance - NEW FIELDS
    is_validated = db.Column(db.Boolean, default=False)
    validation_notes = db.Column(db.Text)
    duplicate_of = db.Column(db.Integer, db.ForeignKey('service_requests.id'))
    
    # Spatial data (PostGIS Point geometry in EPSG:3857)
    geometry = db.Column(Geometry('POINT', srid=3857, spatial_index=True))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - NEW FIELDS
    attachments = db.relationship('ServiceRequestAttachment', backref='service_request', lazy=True, cascade='all, delete-orphan')
    status_updates = db.relationship('ServiceRequestUpdate', backref='service_request', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(ServiceRequest, self).__init__(**kwargs)
        if not self.datetime_init:
            self.datetime_init = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Auto-generate request_id for citizen submissions
        if self.source == 'citizen' and not self.request_id:
            self.request_id = self._generate_request_id()
    
    def _generate_request_id(self):
        """Generate a unique request ID for citizen submissions."""
        import random
        # Use timestamp + random number to ensure uniqueness
        timestamp = int(datetime.utcnow().timestamp())
        random_num = random.randint(1000, 9999)
        return int(f"{timestamp}{random_num}")
    
    def update_from_dict(self, data):
        """
        Update the service request from a dictionary.
        Handles coordinate conversion to PostGIS geometry.
        """
        # Update basic fields
        self.request_id = data.get('request_id')
        self.description = data.get('description')
        self.status = data.get('status')
        self.problem_code = data.get('problem_code')
        self.submit_to = data.get('submit_to')
        self.prob_address = data.get('prob_address')
        self.prob_city = data.get('prob_city')
        self.prob_zip = data.get('prob_zip')
        self.prob_add_type = data.get('prob_add_type')
        self.neighborhood = data.get('neighborhood')
        self.ward = data.get('ward')
        self.caller_type = data.get('caller_type')
        self.explanation = data.get('explanation')
        self.plain_english_name = data.get('plain_english_name')
        self.group_name = data.get('group_name')
        
        # Update dates
        self.datetime_init = data.get('datetime_init')
        self.datetime_closed = data.get('datetime_closed')
        self.date_cancelled = data.get('date_cancelled')
        self.date_inv_done = data.get('date_inv_done')
        self.prj_complete_date = data.get('prj_complete_date')
        
        # Update geometry
        self._set_geometry_from_coordinates(data.get('srx'), data.get('sry'))
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
    
    def _set_geometry_from_coordinates(self, x, y):
        """
        Set the geometry from coordinates.
        Converts to EPSG:3857 (Web Mercator) for web mapping.
        """
        if x is not None and y is not None:
            try:
                # Create a Point geometry
                point = Point(float(x), float(y))
                # Convert to WKT format for PostGIS
                self.geometry = dumps(point)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid coordinates: {x}, {y}. Error: {e}")
                self.geometry = None
        else:
            self.geometry = None
    
    def update_status(self, new_status, update_message=None, internal_note=None, created_by='system'):
        """Update status with automatic logging."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Create status update record (avoid circular import by creating directly)
        update = ServiceRequestUpdate(
            service_request_id=self.id,
            old_status=old_status,
            new_status=new_status,
            update_message=update_message,
            internal_note=internal_note,
            created_by=created_by
        )
        self.status_updates.append(update)
        
        # Close dates
        if new_status.lower() in ['closed', 'resolved', 'completed']:
            self.datetime_closed = datetime.utcnow()
    
    def to_dict(self):
        """
        Convert the service request to a dictionary.
        """
        return {
            'id': self.id,
            'request_id': self.request_id,
            'source': self.source,
            'description': self.description,
            'status': self.status,
            'problem_code': self.problem_code,
            'submit_to': self.submit_to,
            'category': self.category,
            'priority': self.priority,
            'is_emergency': self.is_emergency,
            'prob_address': self.prob_address,
            'prob_city': self.prob_city,
            'prob_zip': self.prob_zip,
            'prob_add_type': self.prob_add_type,
            'neighborhood': self.neighborhood,
            'ward': self.ward,
            'citizen_name': self.citizen_name,
            'citizen_email': self.citizen_email,
            'citizen_phone': self.citizen_phone,
            'contact_method_preference': self.contact_method_preference,
            'datetime_init': self.datetime_init.isoformat() if self.datetime_init else None,
            'datetime_closed': self.datetime_closed.isoformat() if self.datetime_closed else None,
            'date_cancelled': self.date_cancelled.isoformat() if self.date_cancelled else None,
            'date_inv_done': self.date_inv_done.isoformat() if self.date_inv_done else None,
            'prj_complete_date': self.prj_complete_date.isoformat() if self.prj_complete_date else None,
            'assigned_to': self.assigned_to,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'internal_notes': self.internal_notes,
            'citizen_updates': self.citizen_updates,
            'caller_type': self.caller_type,
            'explanation': self.explanation,
            'plain_english_name': self.plain_english_name,
            'group_name': self.group_name,
            'is_validated': self.is_validated,
            'validation_notes': self.validation_notes,
            'duplicate_of': self.duplicate_of,
            'geometry': str(self.geometry) if self.geometry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ServiceRequest {self.request_id}: {self.description[:50]}...>'


class ServiceRequestAttachment(db.Model):
    """
    File attachments for service requests (photos, documents, etc.)
    """
    __tablename__ = 'service_request_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Metadata
    uploaded_by = db.Column(db.String(20), default='citizen')  # citizen, staff, api
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)  # Visible to citizen
    description = db.Column(db.String(500))


class ServiceRequestUpdate(db.Model):
    """
    Status update history for service requests
    """
    __tablename__ = 'service_request_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    
    # Status change
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    
    # Update content
    update_message = db.Column(db.Text)  # Message visible to citizen
    internal_note = db.Column(db.Text)   # Internal staff note
    
    # Metadata
    created_by = db.Column(db.String(100), nullable=False)  # staff username or 'system'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_citizen_visible = db.Column(db.Boolean, default=True)


class ServiceCategory(db.Model):
    """
    Predefined service categories for citizen form
    """
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))  # Which city department handles this
    problem_codes = db.Column(db.Text)      # JSON array of applicable problem codes
    is_emergency_eligible = db.Column(db.Boolean, default=False)
    estimated_response_time = db.Column(db.String(100))  # "1-2 business days"
    instructions = db.Column(db.Text)       # Help text for citizens
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


# Default categories data
DEFAULT_CATEGORIES = [
    {
        'name': 'Street & Sidewalk Issues',
        'description': 'Potholes, street repairs, sidewalk damage, street cleaning',
        'department': 'Streets Division',
        'is_emergency_eligible': False,
        'estimated_response_time': '3-5 business days',
        'instructions': 'Please provide the exact address and describe the issue clearly.'
    },
    {
        'name': 'Refuse & Recycling',
        'description': 'Missed pickup, illegal dumping, dead animals, litter',
        'department': 'Refuse Division',
        'is_emergency_eligible': False,
        'estimated_response_time': '1-3 business days',
        'instructions': 'For missed pickups, please report within 24 hours of scheduled pickup.'
    },
    {
        'name': 'Traffic & Signs',
        'description': 'Traffic signals, street signs, parking issues, traffic safety',
        'department': 'Traffic Division',
        'is_emergency_eligible': True,
        'estimated_response_time': '1-2 business days',
        'instructions': 'For urgent traffic safety issues, please call 911.'
    },
    {
        'name': 'Parks & Recreation',
        'description': 'Park maintenance, playground issues, recreational facilities',
        'department': 'Parks Division',
        'is_emergency_eligible': False,
        'estimated_response_time': '5-7 business days',
        'instructions': 'Please specify which park and the exact location of the issue.'
    },
    {
        'name': 'Building & Property Issues',
        'description': 'Code violations, vacant buildings, property maintenance',
        'department': 'Building Division',
        'is_emergency_eligible': False,
        'estimated_response_time': '10-15 business days',
        'instructions': 'Please provide the complete property address and detailed description.'
    },
    {
        'name': 'Trees & Forestry',
        'description': 'Tree removal, trimming, fallen trees, tree planting requests',
        'department': 'Forestry Division',
        'is_emergency_eligible': True,
        'estimated_response_time': '2-5 business days',
        'instructions': 'For emergency tree issues blocking roads, please call 911.'
    }
] 