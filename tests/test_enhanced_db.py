"""
Test script for creating enhanced database tables.
"""

from flask import Flask
from models import db, ServiceRequest, ServiceRequestAttachment, ServiceRequestUpdate, ServiceCategory, DEFAULT_CATEGORIES
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5433/stl311')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

def create_enhanced_tables():
    """Create enhanced database tables with citizen submission support."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Enhanced database tables created successfully!")
        
        # Initialize default categories if none exist
        try:
            existing_count = ServiceCategory.query.count()
            if existing_count == 0:
                for cat_data in DEFAULT_CATEGORIES:
                    category = ServiceCategory(**cat_data)
                    db.session.add(category)
                db.session.commit()
                print(f"✅ Initialized {len(DEFAULT_CATEGORIES)} default service categories")
            else:
                print(f"ℹ️ Found {existing_count} existing service categories")
                
        except Exception as e:
            print(f"⚠️ Error initializing categories: {e}")
            db.session.rollback()
        
        # Print table information
        print("\n📊 Enhanced Database Schema:")
        print("- service_requests (main table with citizen fields)")
        print("- service_request_attachments (file uploads)")
        print("- service_request_updates (status history)")
        print("- service_categories (predefined categories)")
        
        print("\n🆕 New Fields Added to service_requests:")
        print("- source: Tracks 'api' vs 'citizen' submissions")
        print("- category: User-friendly category names")
        print("- priority: User-selected priority level")
        print("- is_emergency: Emergency flag")
        print("- citizen_name: Contact name")
        print("- citizen_email: Contact email")
        print("- citizen_phone: Contact phone")
        print("- contact_method_preference: How to reach citizen")
        print("- assigned_to: Staff assignment")
        print("- estimated_completion: SLA tracking")
        print("- internal_notes: Staff-only notes")
        print("- citizen_updates: Public updates")
        print("- is_validated: Quality assurance")
        print("- validation_notes: QA notes")
        print("- duplicate_of: Duplicate tracking")

if __name__ == '__main__':
    create_enhanced_tables()
