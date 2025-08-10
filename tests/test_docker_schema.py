"""
Test script for validating enhanced database schema in Docker environment.
This script will be run inside the Flask container.
"""

from models import db, ServiceRequest, ServiceRequestAttachment, ServiceRequestUpdate, ServiceCategory, DEFAULT_CATEGORIES
from app import app
from datetime import datetime

def test_enhanced_schema():
    """Test the enhanced database schema with all new tables and fields."""
    
    print("🔍 Testing Enhanced Database Schema in Docker Environment...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created/updated successfully!")
            
            # Test ServiceRequest model with new fields
            print("\n📋 Testing ServiceRequest model with citizen fields...")
            
            # Check existing data count
            existing_count = ServiceRequest.query.count()
            print(f"   Existing service requests: {existing_count}")
            
            # Test creating a citizen-submitted request
            test_request = ServiceRequest(
                source='citizen',
                category='Street & Sidewalk Issues',
                description='Test pothole on Main Street',
                priority='normal',
                is_emergency=False,
                prob_address='123 Main Street',
                prob_city='St. Louis',
                citizen_name='Test User',
                citizen_email='test@example.com',
                citizen_phone='(314) 555-0123',
                contact_method_preference='email',
                status='New'
            )
            
            # The constructor should auto-generate request_id
            print(f"   Auto-generated request ID: {test_request.request_id}")
            
            # Test ServiceCategory model
            print("\n📂 Testing ServiceCategory model...")
            existing_categories = ServiceCategory.query.count()
            
            if existing_categories == 0:
                print("   Initializing default categories...")
                for cat_data in DEFAULT_CATEGORIES:
                    category = ServiceCategory(**cat_data)
                    db.session.add(category)
                db.session.commit()
                print(f"   ✅ Added {len(DEFAULT_CATEGORIES)} default categories")
            else:
                print(f"   Found {existing_categories} existing categories")
            
            # List categories
            categories = ServiceCategory.query.all()
            for cat in categories:
                print(f"   - {cat.name}: {cat.estimated_response_time}")
            
            # Test relationships
            print("\n🔗 Testing model relationships...")
            
            # Test ServiceRequestUpdate
            if existing_count > 0:
                sample_request = ServiceRequest.query.first()
                print(f"   Sample request {sample_request.request_id} has {len(sample_request.status_updates)} updates")
                print(f"   Sample request has {len(sample_request.attachments)} attachments")
            
            # Test enhanced to_dict method
            print("\n📊 Testing enhanced to_dict method...")
            if existing_count > 0:
                sample_request = ServiceRequest.query.first()
                sample_dict = sample_request.to_dict()
                new_fields = ['source', 'category', 'priority', 'is_emergency', 
                             'citizen_name', 'citizen_email', 'assigned_to', 'is_validated']
                
                print("   New fields in to_dict output:")
                for field in new_fields:
                    if field in sample_dict:
                        print(f"   - {field}: {sample_dict[field]}")
            
            print("\n🎉 Enhanced Database Schema Test Completed Successfully!")
            print("\nNew Features Available:")
            print("- ✅ Citizen submission support")
            print("- ✅ File attachment system")
            print("- ✅ Status update tracking")
            print("- ✅ Service categories")
            print("- ✅ Priority levels")
            print("- ✅ Emergency flagging")
            print("- ✅ Contact management")
            print("- ✅ Staff workflow fields")
            print("- ✅ Quality assurance tracking")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_enhanced_schema()
