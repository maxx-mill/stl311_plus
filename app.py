"""
Flask application for St. Louis 311 Service Integration with PostGIS and GeoServer.
Provides REST API endpoints for managing 311 service requests with spatial data support.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from geoalchemy2 import Geometry
from shapely.geometry import Point
from shapely.wkt import dumps
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stl311_flask.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Import and apply configuration
from config import config
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config.get(config_name, config['default']))

# Import models first to get the db instance
from models import db, ServiceRequest

# Initialize database with the app
db.init_app(app)

# Import services after db initialization
from services.api_client import APIClient
from services.data_processor import DataProcessor
from services.geoserver_client import GeoServerClient

# Initialize services
api_client = APIClient()
data_processor = DataProcessor()
geoserver_client = GeoServerClient()

# Initialize scheduler (optional - can be started via API)
scheduler = None

def initialize_scheduler():
    """Initialize the data scheduler."""
    global scheduler
    try:
        from services.scheduler import DataScheduler
        scheduler = DataScheduler(app)
        logger.info("Scheduler initialized (not started)")
        return True
    except ImportError as e:
        logger.warning(f"Scheduler not available - schedule library not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        return False

# Try to initialize scheduler
initialize_scheduler()

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

@app.route('/')
def index():
    """Home page with API documentation."""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_status
    })

@app.route('/api/service-requests', methods=['GET'])
def get_service_requests():
    """Get service requests with optional filtering."""
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 100, type=int), 1000)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        bbox = request.args.get('bbox')  # Format: "x1,y1,x2,y2"
        
        # Build query
        query = ServiceRequest.query
        
        # Apply filters
        if status:
            query = query.filter(ServiceRequest.status == status)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(ServiceRequest.datetime_init >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(ServiceRequest.datetime_init <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        if bbox:
            try:
                x1, y1, x2, y2 = map(float, bbox.split(','))
                # Create bounding box geometry
                bbox_wkt = f'POLYGON(({x1} {y1}, {x2} {y1}, {x2} {y2}, {x1} {y2}, {x1} {y1}))'
                query = query.filter(ServiceRequest.geometry.ST_Intersects(bbox_wkt))
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid bbox format. Use: x1,y1,x2,y2'}), 400
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.order_by(ServiceRequest.datetime_init.desc())
        service_requests = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to JSON
        results = []
        for sr in service_requests:
            result = sr.to_dict()
            if sr.geometry:
                try:
                    # Extract coordinates from PostGIS geometry
                    # Use ST_X and ST_Y functions to get coordinates
                    from sqlalchemy import text
                    coords_query = db.session.execute(
                        text(f"SELECT ST_X(geometry) as x, ST_Y(geometry) as y FROM service_requests WHERE id = {sr.id}")
                    ).fetchone()
                    if coords_query:
                        result['geometry'] = {
                            'type': 'Point',
                            'coordinates': [float(coords_query.x), float(coords_query.y)]
                        }
                    else:
                        result['geometry'] = None
                except Exception as e:
                    logger.warning(f"Error extracting geometry for request {sr.id}: {e}")
                    result['geometry'] = None
            else:
                result['geometry'] = None
            results.append(result)
        
        return jsonify({
            'service_requests': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching service requests: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/service-requests/<int:request_id>', methods=['GET'])
def get_service_request(request_id):
    """Get a specific service request by ID."""
    try:
        service_request = ServiceRequest.query.get(request_id)
        if not service_request:
            return jsonify({'error': 'Service request not found'}), 404
        
        result = service_request.to_dict()
        if service_request.geometry:
            try:
                # Extract coordinates from PostGIS geometry
                from sqlalchemy import text
                coords_query = db.session.execute(
                    text(f"SELECT ST_X(geometry) as x, ST_Y(geometry) as y FROM service_requests WHERE id = {service_request.id}")
                ).fetchone()
                if coords_query:
                    result['geometry'] = {
                        'type': 'Point',
                        'coordinates': [float(coords_query.x), float(coords_query.y)]
                    }
                else:
                    result['geometry'] = None
            except Exception as e:
                logger.warning(f"Error extracting geometry for request {service_request.id}: {e}")
                result['geometry'] = None
        else:
            result['geometry'] = None
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching service request {request_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """Sync data from St. Louis 311 API to PostGIS database."""
    try:
        # Parse request parameters
        data = request.get_json() or {}
        days_back = data.get('days_back', 1)
        status = data.get('status', 'open')
        force_sync = data.get('force_sync', False)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Starting data sync from {start_date} to {end_date}")
        
        # Fetch data from API
        raw_requests = api_client.fetch_service_requests(
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        if not raw_requests:
            return jsonify({
                'status': 'success',
                'message': 'No new data to sync',
                'requests_processed': 0
            })
        
        # Process and validate data
        processed_requests = data_processor.process_and_validate_data(raw_requests)
        
        if not processed_requests:
            return jsonify({
                'status': 'success',
                'message': 'No valid data after processing',
                'requests_processed': 0
            })
        
        # Save to database
        inserted_count = 0
        updated_count = 0
        
        for request_data in processed_requests:
            try:
                # Check if request already exists
                existing = ServiceRequest.query.filter_by(
                    request_id=request_data['request_id']
                ).first()
                
                if existing and not force_sync:
                    # Update existing record
                    existing.update_from_dict(request_data)
                    updated_count += 1
                else:
                    # Create new record
                    service_request = ServiceRequest()
                    service_request.update_from_dict(request_data)
                    db.session.add(service_request)
                    inserted_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving request {request_data.get('request_id')}: {e}")
                continue
        
        # Commit changes
        db.session.commit()
        
        # Publish to GeoServer if configured
        geoserver_result = None
        try:
            geoserver_result = geoserver_client.publish_layer('stl311_service_requests')
        except Exception as e:
            logger.error(f"Error publishing to GeoServer: {e}")
            geoserver_result = {'error': str(e)}
        
        return jsonify({
            'status': 'success',
            'message': 'Data sync completed',
            'requests_processed': len(processed_requests),
            'requests_inserted': inserted_count,
            'requests_updated': updated_count,
            'geoserver_result': geoserver_result
        })
        
    except Exception as e:
        logger.error(f"Error during data sync: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the automatic daily sync scheduler."""
    global scheduler
    try:
        if not scheduler:
            if not initialize_scheduler():
                return jsonify({'error': 'Scheduler not available'}), 500
        
        if scheduler.is_running:
            return jsonify({
                'message': 'Scheduler is already running',
                'status': scheduler.get_scheduler_status()
            })
        
        scheduler.start_scheduler()
        return jsonify({
            'message': 'Scheduler started successfully',
            'status': scheduler.get_scheduler_status()
        })
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({'error': f'Failed to start scheduler: {e}'}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the automatic daily sync scheduler."""
    global scheduler
    try:
        if not scheduler:
            return jsonify({'message': 'Scheduler not initialized'})
        
        if not scheduler.is_running:
            return jsonify({'message': 'Scheduler is not running'})
        
        scheduler.stop_scheduler()
        return jsonify({'message': 'Scheduler stopped successfully'})
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({'error': f'Failed to stop scheduler: {e}'}), 500

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get scheduler status."""
    global scheduler
    try:
        if not scheduler:
            return jsonify({
                'initialized': False,
                'is_running': False,
                'message': 'Scheduler not initialized'
            })
        
        status = scheduler.get_scheduler_status()
        status['initialized'] = True
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({'error': f'Failed to get scheduler status: {e}'}), 500

@app.route('/api/sync/yesterday', methods=['POST'])
def sync_yesterday():
    """Sync yesterday's data immediately."""
    global scheduler
    try:
        if not scheduler:
            if not initialize_scheduler():
                return jsonify({'error': 'Scheduler not available'}), 500
        
        result = scheduler.sync_yesterday_now()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing yesterday's data: {e}")
        return jsonify({'error': f'Failed to sync yesterday: {e}'}), 500

@app.route('/api/sync/date-range', methods=['POST'])
def sync_date_range():
    """Sync a specific date range."""
    global scheduler
    try:
        if not scheduler:
            if not initialize_scheduler():
                return jsonify({'error': 'Scheduler not available'}), 500
        
        data = request.get_json()
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        result = scheduler.sync_date_range(start_date, end_date)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing date range: {e}")
        return jsonify({'error': f'Failed to sync date range: {e}'}), 500

@app.route('/api/geoserver/publish', methods=['POST'])
def publish_to_geoserver():
    """Publish current data to GeoServer."""
    try:
        data = request.get_json() or {}
        layer_name = data.get('layer_name', 'stl311_service_requests')
        
        result = geoserver_client.publish_layer(layer_name)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error publishing to GeoServer: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/submit')
def submit_form():
    """Render the citizen submission form."""
    return render_template('submit.html')

@app.route('/track')
def track_form():
    """Render the request tracking form."""
    return render_template('track.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get service categories for the submission form."""
    try:
        from models import ServiceCategory
        categories = ServiceCategory.query.all()
        
        if not categories:
            # Return default categories if none exist
            default_categories = [
                {'name': 'Streets & Sidewalks', 'description': 'Potholes, street repairs, sidewalk issues', 'estimated_response_time': '3-5 business days'},
                {'name': 'Waste & Recycling', 'description': 'Missed pickups, illegal dumping, bin issues', 'estimated_response_time': '1-2 business days'},
                {'name': 'Traffic & Signs', 'description': 'Traffic lights, stop signs, street signs', 'estimated_response_time': '2-3 business days'},
                {'name': 'Parks & Recreation', 'description': 'Park maintenance, playground issues', 'estimated_response_time': '5-7 business days'},
                {'name': 'Trees & Forestry', 'description': 'Tree removal, trimming, planting requests', 'estimated_response_time': '7-10 business days'},
                {'name': 'Other', 'description': 'General city services and issues', 'estimated_response_time': '3-5 business days'}
            ]
            return jsonify(default_categories)
        
        return jsonify([{
            'name': cat.name,
            'description': cat.description,
            'estimated_response_time': cat.estimated_response_time
        } for cat in categories])
        
    except ImportError:
        # Handle case where ServiceCategory model doesn't exist yet
        default_categories = [
            {'name': 'Streets & Sidewalks', 'description': 'Potholes, street repairs, sidewalk issues', 'estimated_response_time': '3-5 business days'},
            {'name': 'Waste & Recycling', 'description': 'Missed pickups, illegal dumping, bin issues', 'estimated_response_time': '1-2 business days'},
            {'name': 'Traffic & Signs', 'description': 'Traffic lights, stop signs, street signs', 'estimated_response_time': '2-3 business days'},
            {'name': 'Parks & Recreation', 'description': 'Park maintenance, playground issues', 'estimated_response_time': '5-7 business days'},
            {'name': 'Trees & Forestry', 'description': 'Tree removal, trimming, planting requests', 'estimated_response_time': '7-10 business days'},
            {'name': 'Other', 'description': 'General city services and issues', 'estimated_response_time': '3-5 business days'}
        ]
        return jsonify(default_categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/submit-request', methods=['POST'])
def submit_request():
    """Submit a new service request from citizen form."""
    try:
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
            files = None
        else:
            data = request.form.to_dict()
            files = request.files.getlist('attachments')
        
        # Generate request ID
        import random
        request_id = random.randint(100000, 999999)
        while ServiceRequest.query.filter_by(request_id=request_id).first():
            request_id = random.randint(100000, 999999)
        
        # Create geometry if coordinates provided
        geometry = None
        if data.get('latitude') and data.get('longitude'):
            try:
                lat = float(data['latitude'])
                lng = float(data['longitude'])
                
                # Convert to Web Mercator (EPSG:3857)
                import pyproj
                transformer = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
                x, y = transformer.transform(lng, lat)
                
                from geoalchemy2.functions import ST_GeomFromText
                geometry = f'POINT({x} {y})'
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing coordinates: {e}")
        
        # Create service request
        service_request = ServiceRequest(
            request_id=request_id,
            source='citizen',
            category=data.get('category'),
            description=data.get('description', ''),
            priority=data.get('priority', 'normal'),
            is_emergency=data.get('is_emergency') == 'on' or data.get('is_emergency') == True,
            prob_address=data.get('prob_address'),
            prob_zip=int(data.get('prob_zip')) if data.get('prob_zip') and data.get('prob_zip').isdigit() else None,
            citizen_name=data.get('citizen_name'),
            citizen_phone=data.get('citizen_phone'),
            citizen_email=data.get('citizen_email'),
            contact_method_preference=data.get('contact_method_preference', 'email'),
            status='New',
            datetime_init=datetime.utcnow()
        )
        
        # Set geometry if available
        if geometry:
            from geoalchemy2.functions import ST_GeomFromText
            service_request.geometry = ST_GeomFromText(geometry, 3857)
        
        # Save to database
        db.session.add(service_request)
        db.session.commit()
        
        # Handle file attachments if present
        if files:
            from models import ServiceRequestAttachment
            for file in files:
                if file.filename:
                    # In a production system, you'd save files to storage
                    # For now, we'll just record the filename
                    attachment = ServiceRequestAttachment(
                        service_request_id=service_request.id,
                        filename=file.filename,
                        original_filename=file.filename,
                        file_path=f'/uploads/{file.filename}',  # placeholder path
                        file_size=len(file.read()) if hasattr(file, 'read') else 0,
                        mime_type=file.content_type or 'unknown',
                        uploaded_by='citizen',
                        upload_date=datetime.utcnow()
                    )
                    db.session.add(attachment)
            db.session.commit()
        
        # Create initial status update
        from models import ServiceRequestUpdate
        initial_update = ServiceRequestUpdate(
            service_request_id=service_request.id,
            new_status='New',
            update_message=f'Service request submitted by {data.get("citizen_name", "citizen")}',
            created_by='citizen_portal',
            created_at=datetime.utcnow()
        )
        db.session.add(initial_update)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'message': 'Service request submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting service request: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit service request'}), 500

@app.route('/api/track-request/<int:request_id>', methods=['GET'])
def track_request(request_id):
    """Track a service request by ID."""
    try:
        service_request = ServiceRequest.query.filter_by(request_id=request_id).first()
        
        if not service_request:
            return jsonify({'error': 'Service request not found'}), 404
        
        # Get status updates
        from models import ServiceRequestUpdate
        updates = ServiceRequestUpdate.query.filter_by(
            service_request_id=service_request.id,
            is_citizen_visible=True  # Only show public updates
        ).order_by(ServiceRequestUpdate.created_at.desc()).all()
        
        result = service_request.to_dict()
        result['updates'] = [{
            'date': update.created_at.isoformat(),
            'status': update.new_status,
            'update_text': update.update_message
        } for update in updates]
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error tracking request {request_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/service-types', methods=['GET'])
def get_service_types():
    """Get unique service types for filtering."""
    try:
        # Get unique service types from the database using description field
        service_types = db.session.query(ServiceRequest.description)\
            .filter(ServiceRequest.description.isnot(None))\
            .distinct()\
            .all()
        
        # Convert to list
        types = [st[0] for st in service_types if st[0]]
        
        return jsonify({
            'service_types': types
        })
        
    except Exception as e:
        logger.error(f"Error fetching service types: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about service requests."""
    try:
        # Total requests
        total_requests = ServiceRequest.query.count()
        
        # Requests by status
        status_counts = db.session.query(
            ServiceRequest.status,
            db.func.count(ServiceRequest.id)
        ).group_by(ServiceRequest.status).all()
        
        # Requests with coordinates
        requests_with_coords = ServiceRequest.query.filter(
            ServiceRequest.geometry.isnot(None)
        ).count()
        
        # Recent requests (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_requests = ServiceRequest.query.filter(
            ServiceRequest.datetime_init >= yesterday
        ).count()
        
        return jsonify({
            'total_requests': total_requests,
            'requests_with_coordinates': requests_with_coords,
            'coordinate_percentage': (requests_with_coords / total_requests * 100) if total_requests > 0 else 0,
            'recent_requests_24h': recent_requests,
            'status_breakdown': dict(status_counts)
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000) 