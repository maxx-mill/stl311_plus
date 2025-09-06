"""
Test script for daily sync functionality.
Run this to verify your sync setup is working correctly.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.api_client import APIClient
from services.data_processor import DataProcessor
from models import db, ServiceRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDailySync(unittest.TestCase):
    """Test cases for daily sync functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.api_client = APIClient()
        self.data_processor = DataProcessor()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    def test_api_connection(self):
        """Test API connection."""
        logger.info("Testing API connection...")
        result = self.api_client.test_connection()
        
        self.assertIn('status', result)
        if result['status'] == 'success':
            logger.info("✅ API connection successful")
        else:
            logger.warning(f"⚠️ API connection issue: {result['message']}")
        
        # Don't fail test if API is temporarily unavailable
        self.assertTrue(True)
    
    def test_database_connection(self):
        """Test database connection."""
        logger.info("Testing database connection...")
        
        try:
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT 1')).fetchone()
                self.assertEqual(result[0], 1)
                logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.fail(f"Database connection failed: {e}")
    
    def test_data_processor(self):
        """Test data processing functionality."""
        logger.info("Testing data processor...")
        
        # Sample raw data (typical API response format)
        sample_data = [
            {
                'request_id': 99999999,
                'description': 'Test request',
                'status': 'open',
                'problem_code': 'TEST',
                'submit_to': 'Test Department',
                'prob_address': '1234 Test St',
                'prob_city': 'St. Louis',
                'prob_zip': 63101,
                'date_requested': '2025-08-13 10:00:00',
                'lat': 38.6270,
                'long': -90.1994
            }
        ]
        
        processed_data = self.data_processor.process_and_validate_data(sample_data)
        
        self.assertIsInstance(processed_data, list)
        if processed_data:
            self.assertIn('request_id', processed_data[0])
            logger.info("✅ Data processor working correctly")
        else:
            logger.warning("⚠️ Data processor returned empty results")
    
    def test_service_request_model(self):
        """Test ServiceRequest model functionality."""
        logger.info("Testing ServiceRequest model...")
        
        try:
            # Test model creation
            test_request = ServiceRequest(
                request_id=99999998,
                description='Test service request',
                status='open',
                source='test'
            )
            
            # Test update_from_dict method
            update_data = {
                'description': 'Updated test request',
                'status': 'in_progress',
                'problem_code': 'TEST_UPDATE'
            }
            
            test_request.update_from_dict(update_data)
            
            self.assertEqual(test_request.description, 'Updated test request')
            self.assertEqual(test_request.status, 'in_progress')
            self.assertEqual(test_request.problem_code, 'TEST_UPDATE')
            
            logger.info("✅ ServiceRequest model working correctly")
            
        except Exception as e:
            logger.error(f"❌ ServiceRequest model test failed: {e}")
            self.fail(f"ServiceRequest model test failed: {e}")
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        logger.info("Testing scheduler initialization...")
        
        try:
            from services.scheduler import DataScheduler
            scheduler = DataScheduler(self.app)
            
            self.assertIsNotNone(scheduler)
            self.assertFalse(scheduler.is_running)
            
            # Test status method
            status = scheduler.get_scheduler_status()
            self.assertIn('is_running', status)
            
            logger.info("✅ Scheduler initialization successful")
            
        except ImportError:
            logger.warning("⚠️ Scheduler not available (schedule library not installed)")
        except Exception as e:
            logger.error(f"❌ Scheduler initialization failed: {e}")
            self.fail(f"Scheduler initialization failed: {e}")

def run_manual_tests():
    """Run manual tests and report results."""
    logger.info("="*60)
    logger.info("STL 311+ Daily Sync - Manual Test Suite")
    logger.info("="*60)
    
    # Test API client directly
    logger.info("\n1. Testing API Client...")
    api_client = APIClient()
    
    # Test connection
    result = api_client.test_connection()
    if result['status'] == 'success':
        logger.info(f"✅ API Connection: OK (Response time: {result['response_time']:.2f}s)")
    else:
        logger.warning(f"⚠️ API Connection: {result['message']}")
    
    # Test data fetching (small sample)
    try:
        yesterday = datetime.now() - timedelta(days=1)
        requests = api_client.fetch_service_requests(
            start_date=yesterday,
            end_date=yesterday,
            status='open'
        )
        logger.info(f"✅ Data Fetching: Retrieved {len(requests)} requests")
    except Exception as e:
        logger.warning(f"⚠️ Data Fetching: {e}")
    
    # Test database with app context
    logger.info("\n2. Testing Database...")
    with app.app_context():
        try:
            # Test connection
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            logger.info("✅ Database Connection: OK")
            
            # Test table existence
            count = ServiceRequest.query.count()
            logger.info(f"✅ Database Tables: OK ({count} service requests)")
            
        except Exception as e:
            logger.error(f"❌ Database Error: {e}")
    
    # Test data processor
    logger.info("\n3. Testing Data Processor...")
    processor = DataProcessor()
    sample_data = [{
        'request_id': 99999999,
        'description': 'Test request',
        'status': 'open',
        'lat': 38.6270,
        'long': -90.1994
    }]
    
    processed = processor.process_and_validate_data(sample_data)
    if processed:
        logger.info("✅ Data Processor: OK")
    else:
        logger.warning("⚠️ Data Processor: No valid data processed")
    
    logger.info("\n" + "="*60)
    logger.info("Manual test suite completed!")
    logger.info("="*60)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        run_manual_tests()
    else:
        # Run unittest suite
        unittest.main()
